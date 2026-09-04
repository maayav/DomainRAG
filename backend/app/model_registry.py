"""Runtime model configuration: switch between local Ollama and OpenAI-compatible providers."""
import os
import logging
import threading
from dataclasses import dataclass, field

from llama_index.core import Settings
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI

from app.config import LLM_MODEL, LLM_TEMPERATURE, LLM_TIMEOUT, LLM_CONTEXT_WINDOW

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"

# Providers that expose an OpenAI-compatible API.
# "models" lists are curated free-tier options shown in the UI; models without
# "/" or ":" in the id are additionally validated against the provider's
# live model list when a config is applied. If a model 404s at query time,
# model_registry.enable_fallback() reverts the active config to the local
# default model automatically.
OPENAI_COMPATIBLE_PROVIDERS = {
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1-nano"],
    },
    "groq": {
        "label": "Groq (free tier)",
        "base_url": "https://api.groq.com/openai/v1",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.3-70b-specdec",
            "llama-3.1-8b-instant",
            "deepseek-r1-distill-llama-70b",
            "qwen-qwq-32b",
            "gemma-2-9b-it",
        ],
    },
    "openrouter": {
        "label": "OpenRouter (free models)",
        "base_url": "https://openrouter.ai/api/v1",
        "models": [
            "meta-llama/llama-3.3-70b-instruct:free",
            "llama/llama-3.3-70b-instruct:free",
            "deepseek/deepseek-chat-v3-0324:free",
            "qwen/qwen-2.5-72b-instruct:free",
            "google/gemini-2.0-flash-exp:free",
            "mistralai/mistral-small-3.1-24b-instruct:free",
            "meta-llama/llama-3.1-8b-instruct:free",
            "nousresearch/hermes-3-llama-3.1-405b:free",
        ],
    },
    "zen": {
        "label": "OpenCode Zen (free + OpenAI-compatible)",
        "base_url": "https://opencode.ai/zen/v1",
        "models": [
            "deepseek-v4-flash-free",
            "big-pickle",
            "mimo-v2.5-free",
            "nemotron-3-ultra-free",
            "north-mini-code-free",
            "ling-3.0-tiny-free",
            "deepseek-v4-flash",
        ],
    },
    "custom": {
        "label": "Custom (OpenAI-compatible)",
        "base_url": "",
        "models": [],
    },
}


@dataclass
class ModelConfig:
    provider: str = "ollama"  # "ollama" or an OpenAI-compatible provider key
    model: str = LLM_MODEL
    base_url: str = ""
    api_key: str = ""  # kept in memory only; never returned by the API


def _provider_base_url(provider: str) -> str:
    info = OPENAI_COMPATIBLE_PROVIDERS.get(provider)
    return info["base_url"] if info else ""


_state_lock = threading.Lock()


def _initial_config() -> ModelConfig:
    """Bootstrap the active provider from the environment (for containers/ops).

    Applies raw without network validation; a failing provider automatically
    falls back to the local model on the first query.
    """
    provider = os.environ.get("DOMAINRAG_PROVIDER", "ollama").strip().lower()
    if provider == "ollama":
        return ModelConfig()
    if provider not in OPENAI_COMPATIBLE_PROVIDERS:
        logger.warning("Ignoring unknown DOMAINRAG_PROVIDER '%s'", provider)
        return ModelConfig()
    api_key = os.environ.get("DOMAINRAG_PROVIDER_API_KEY", "").strip()
    if not api_key:
        logger.warning("DOMAINRAG_PROVIDER=%s set without DOMAINRAG_PROVIDER_API_KEY - using local model", provider)
        return ModelConfig()
    model = os.environ.get("DOMAINRAG_MODEL", "deepseek-v4-flash-free").strip()
    base_url = os.environ.get("DOMAINRAG_BASE_URL", "").strip() or _provider_base_url(provider)
    return ModelConfig(provider=provider, model=model, base_url=base_url, api_key=api_key)


_config = _initial_config()
_fallback_active = False


def get_config() -> dict:
    """Return the active model config without the API key."""
    with _state_lock:
        return {
            "provider": _config.provider,
            "model": _config.model,
            "base_url": _config.base_url,
            "using_local": _config.provider == "ollama",
            "fallback_active": _fallback_active,
        }


def update_config(provider: str, model: str, api_key: str = "", base_url: str = "") -> dict:
    """Validate and apply a new model configuration. Raises ValueError on invalid input."""
    global _fallback_active
    provider = provider.strip().lower()
    model = model.strip()
    if not model:
        raise ValueError("Model name is required")

    if provider == "ollama":
        installed = installed_local_models()
        if installed and model not in installed:
            raise ValueError(f"Model '{model}' is not installed locally. Pull it first: ollama pull {model}")
        with _state_lock:
            _fallback_active = False
        _set_config(ModelConfig(provider="ollama", model=model))
        return get_config()

    if provider not in OPENAI_COMPATIBLE_PROVIDERS:
        raise ValueError(f"Unsupported provider '{provider}'")
    if not api_key.strip():
        raise ValueError(f"{provider} requires an API key")

    base_url = base_url.strip() or _provider_base_url(provider)
    _validate_openai_compatible(base_url, model, api_key.strip())

    with _state_lock:
        _fallback_active = False
    _set_config(ModelConfig(provider=provider, model=model, base_url=base_url, api_key=api_key.strip()))
    return get_config()


def reset_config() -> dict:
    """Revert to the local Ollama default model and clear any fallback state."""
    global _fallback_active
    with _state_lock:
        _fallback_active = False
    _set_config(ModelConfig())
    return get_config()


def enable_fallback(reason: str = "") -> bool:
    """Switch the active config back to the default local model after a provider failure.

    Returns True if a failing cloud provider was replaced, False when already
    running on the local model (or when local models are unavailable).
    """
    global _fallback_active, _config
    with _state_lock:
        if _config.provider == "ollama":
            return False
        _fallback_active = True
        _config = ModelConfig(provider="ollama", model=LLM_MODEL)
    logger.warning(f"Provider failed ({reason or 'unknown error'}) - falling back to local {LLM_MODEL}")
    return True


def _set_config(cfg: ModelConfig):
    global _config
    with _state_lock:
        _config = cfg
    logger.info(f"Model config updated: provider={cfg.provider}, model={cfg.model}")


def make_llm():
    """Build the LLM for the active configuration (also updates global Settings)."""
    with _state_lock:
        cfg = _config
    if cfg.provider == "ollama":
        # Qwen3 defaults to a long chain-of-thought thinking phase; disable it
        # for chat use unless explicitly requested.
        thinking = False if cfg.model.startswith("qwen3") else None
        llm = Ollama(
            model=cfg.model,
            temperature=LLM_TEMPERATURE,
            request_timeout=LLM_TIMEOUT,
            thinking=thinking,
            # Default context_window=-1 makes llama-index request the model's
            # full context (128K), overflowing the 8GB GPU and offloading to
            # CPU. Cap it so the KV cache fits on the GPU.
            context_window=LLM_CONTEXT_WINDOW,
        )
    else:
        llm = OpenAI(
            model=cfg.model,
            api_key=cfg.api_key,
            api_base=cfg.base_url,
            temperature=LLM_TEMPERATURE,
            timeout=LLM_TIMEOUT,
            max_retries=2,
            context_window=LLM_CONTEXT_WINDOW,
        )
    Settings.llm = llm
    return llm


def installed_local_models() -> list[str]:
    """List models currently installed in local Ollama (empty list if unreachable)."""
    try:
        import httpx

        resp = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        resp.raise_for_status()
        return [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        logger.warning("Could not reach local Ollama to list models")
        return []


def _validate_openai_compatible(base_url: str, model: str, api_key: str):
    """Verify the provider is reachable and the model exists (no tokens consumed)."""
    try:
        from openai import OpenAI as OpenAIClient

        client = OpenAIClient(base_url=base_url, api_key=api_key)
        names = {m.id for m in client.models.list().data}
        # Some providers (e.g. OpenRouter) use "/" or ":" in model ids that
        # are not queryable via the models endpoint, so only enforce membership
        # for plain model names.
        if model not in names and "/" not in model and ":" not in model:
            raise ValueError(
                f"Model '{model}' not found in provider's model list "
                f"(available: {', '.join(sorted(names)[:5])}{'...' if len(names) > 5 else ''})"
            )
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Could not validate API key or endpoint: {e}") from e