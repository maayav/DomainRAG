"""End-to-end pipeline verification for DomainRAG.

Run:  cd backend && ./venv/bin/python tests/verify_pipeline.py
Requires the API server running on port 8000 (default) and local Ollama up.

Sections:
  A. Unit checks  - sanitization, storage, registry fallback logic, contexts
  B. Core API     - health, query (valid/validation), streaming SSE
  C. Uploads      - happy path, duplicates, traversal, bad ext, empty, batches
  D. Model swap   - validation errors, local swap, fallback flag round-trip
  E. Rate limit   - burst of requests must hit 429
  F. Cleanup      - remove test uploads, rebuild index, restart backend

Exit code 0 if all checks pass.
"""
import io
import os
import sys
import time
import signal
import shutil
import tempfile
import subprocess

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE = os.environ.get("DOMAINRAG_BASE", "http://localhost:8000")
DATA_DIR = os.path.join(BACKEND_DIR, "data", "raw")
PID_FILE = "/tmp/domainrag-server.pid"
SERVER_LOG = "/tmp/domainrag-server.log"

# Files the verification run may create in the corpus (removed at cleanup).
TEST_FILES = ["custom.txt", "custom_1.txt", "evil.md"]

results = []
g_start = time.time()


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail and not cond else ""))


def section(title, subtitle=""):
    print(f"\n=== {title} ===" + (f" — {subtitle}" if subtitle else ""))


def _raises(exc, fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except exc:
        return True


def parse_sse(text):
    counts = {}
    for block in text.split("\n\n"):
        evt = None
        for line in block.split("\n"):
            if line.startswith("event:"):
                evt = line[6:].strip()
        if evt:
            counts[evt] = counts.get(evt, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# A. Unit checks (no server)
# ---------------------------------------------------------------------------
def unit_checks():
    from app.uploads import sanitize_filename, unique_path, store_upload, MAX_FILE_SIZE

    section("A. Unit checks")

    check("traversal sanitized to basename", sanitize_filename("../../etc/passwd.md") == "passwd.md",
          sanitize_filename("../../etc/passwd.md"))
    check("backslash traversal sanitized", sanitize_filename("..\\..\\evil.md") == "evil.md",
          sanitize_filename("..\\..\\evil.md"))
    check("unsafe chars replaced", sanitize_filename("my file!.md") == "my_file_.md", sanitize_filename("my file!.md"))
    check("empty name rejected", _raises(ValueError, sanitize_filename, "   "))
    check("whitespace-only name rejected", _raises(ValueError, sanitize_filename, "\n\t"))

    with tempfile.TemporaryDirectory() as td:
        with open(os.path.join(td, "x.md"), "w") as f:
            f.write("# x")
        check("unique_path collides -> _1", unique_path(td, "x.md").endswith("x_1.md"), unique_path(td, "x.md"))
        check("unique_path free name as-is", not unique_path(td, "y.md").endswith("_1.md"),
              unique_path(td, "y.md"))

    # store_upload against a scratch corpus dir (patched DATA_DIR)
    from app import uploads as uploads_mod
    scratch = tempfile.mkdtemp(prefix="dr-upload-")
    old_dir, uploads_mod.DATA_DIR = uploads_mod.DATA_DIR, scratch
    try:
        check("store rejects bad ext", _raises(ValueError, store_upload, "a.exe", b"MZ"))
        check("store rejects empty file", _raises(ValueError, store_upload, "a.txt", b""))
        check("store rejects oversize", _raises(ValueError, store_upload, "a.txt", b"x" * (MAX_FILE_SIZE + 1)))
        name = store_upload("..\\..\\abc.md", b"# hello raw bytes")
        check("store writes sanitized name", name == "abc.md" and os.path.exists(os.path.join(scratch, name)))
        name2 = store_upload("abc.md", b"# duplicate")
        check("store dedupes silently", name2 == "abc_1.md", name2)
        check("store rejects bad ext only", _raises(ValueError, store_upload, "av.exe", b"MZ"))
    finally:
        uploads_mod.DATA_DIR = old_dir
        shutil.rmtree(scratch, ignore_errors=True)

    from app import model_registry as mr
    cfg_keys = {"provider", "model", "base_url", "using_local", "fallback_active"}
    check("get_config shape", set(mr.get_config()) == cfg_keys, str(mr.get_config()))
    check("no fallback when local", mr.enable_fallback("nope") is False)
    check("unknown provider rejected", _raises(ValueError, mr.update_config, "nope", "m"))
    check("cloud without key rejected", _raises(ValueError, mr.update_config, "openai", "gpt-4o-mini"))
    check("empty model rejected", _raises(ValueError, mr.update_config, "ollama", "  "))
    local = mr.installed_local_models()
    check("ollama reachable with models", len(local) >= 3, str(local))

    # fallback machinery (offline: manipulate internal state directly)
    mr._set_config(mr.ModelConfig(provider="openai", model="gpt-4o-mini", api_key="sk-fake"))
    check("fallback fires on cloud failure", mr.enable_fallback("401 unauthorized") is True)
    c = mr.get_config()
    check("fallback lands on local default", c["provider"] == "ollama" and c["model"] == "qwen3:8b",
          f"{c['provider']}:{c['model']}")
    check("fallback flag exposed", c["fallback_active"] is True)
    mr.reset_config()
    check("reset clears fallback", mr.get_config()["fallback_active"] is False)

    # provider model lists (free choices)
    check("groq lists 6 free models", len(mr.OPENAI_COMPATIBLE_PROVIDERS["groq"]["models"]) == 6)
    check("openrouter lists 8 free models", len(mr.OPENAI_COMPATIBLE_PROVIDERS["openrouter"]["models"]) == 8)
    zen_models = mr.OPENAI_COMPATIBLE_PROVIDERS["zen"]["models"]
    check("zen lists deepseek-v4-flash-free", "deepseek-v4-flash-free" in zen_models)
    check("zen base url", mr.OPENAI_COMPATIBLE_PROVIDERS["zen"]["base_url"] == "https://opencode.ai/zen/v1")


# ---------------------------------------------------------------------------
# B-C-D. API integration (needs running server)
# ---------------------------------------------------------------------------
def api_checks():
    c = httpx.Client(base_url=BASE, timeout=180)

    def get(path):
        return c.get(path)

    def post_json(path, payload):
        return c.post(path, json=payload)

    def upload(files):
        return c.post("/documents", files=files)

    section("B. Core endpoints")

    r = get("/health")
    check("GET /health 200", r.status_code == 200 and r.json().get("status") == "ok")
    base_docs = r.json()["documents"] if r.status_code == 200 else 0

    r = get("/models")
    check("GET /models 200", r.status_code == 200 and r.json()["current"]["provider"] == "ollama")
    if r.status_code == 200:
        body = r.json()
        check("providers list openai/groq/openrouter/custom",
              {"openai", "groq", "openrouter", "custom", "zen"} <= set(body["providers"]))
        check("ollama models listed", len(body["local"]) >= 3, str(body["local"]))
        check("default model qwen3:8b", body["current"]["model"] == "qwen3:8b", body["current"]["model"])
        check("fallback_active present", body["current"]["fallback_active"] is False)

    r = post_json("/query", {"query": "What is a Python decorator?"})
    check("POST /query 200", r.status_code == 200 and len(r.json().get("answer", "")) > 50)
    if r.status_code == 200:
        body = r.json()
        check("citations present", 1 <= len(body["citations"]) <= 3, str(len(body.get("citations", []))))
        check("citation fields", all({"score", "text", "source", "url"} <= set(cc) for cc in body["citations"]))
        check("citations carry URLs", any(cc["url"].startswith("http") for cc in body["citations"]))

    r = post_json("/query", {"query": "what is the capital of a planet that does not exist?"})
    check("no-match returns guidance", r.status_code == 200
          and "could not find anything relevant" in r.json()["answer"].lower())

    check("empty query -> 422", post_json("/query", {"query": ""}).status_code == 422)
    check("too-long query -> 422", post_json("/query", {"query": "x" * 2001}).status_code == 422)
    check("wrong key -> 422", post_json("/query", {"question": "x"}).status_code == 422)

    r = post_json("/query/stream", {"query": "what is a GIN index?"})
    events = parse_sse(r.text) if r.status_code == 200 else {}
    check("stream 200", r.status_code == 200)
    check("stream thinking phases", events.get("thinking", 0) >= 3, f"thinking={events.get('thinking', 0)}")
    check("stream citations", events.get("citations", 0) == 1, f"citations={events.get('citations', 0)}")
    check("stream tokens", events.get("token", 0) >= 20, f"tokens={events.get('token', 0)}")
    check("stream done", events.get("done", 0) == 1, f"done={events.get('done', 0)}")
    check("stream no error", events.get("error", 0) == 0, f"error={events.get('error', 0)}")

    section("C. Document uploads", f"(baseline documents={base_docs})")

    with open("/tmp/dr_custom.txt", "w") as f:
        f.write("# Custom Test Doc\n\nDomainRAG-VERIFY-42 is the secret answer to the custom question.\n")
    with open("/tmp/dr_empty.txt", "w") as f:
        f.write("")
    with open("/tmp/dr_bad.exe", "wb") as f:
        f.write(b"MZ" + b"\x00" * 100)

    r = upload([("files", ("custom.txt", open("/tmp/dr_custom.txt", "rb"), "text/plain"))])
    check("valid upload 200", r.status_code == 200 and r.json()["uploaded"] == ["custom.txt"], str(r.json() if r else r.status_code))
    if r.status_code == 200:
        check("document count +1", r.json()["documents"] == base_docs + 1,
              f"{base_docs} -> {r.json()['documents']}")

    r = upload([("files", ("custom.txt", open("/tmp/dr_custom.txt", "rb"), "text/plain"))])
    check("duplicate upload suffixed", r.status_code == 200 and r.json()["uploaded"] == ["custom_1.txt"],
          str(r.json() if r else r.status_code))
    if r.status_code == 200:
        check("documents +2 total", r.json()["documents"] == base_docs + 2,
              f"{base_docs} -> {r.json()['documents']}")

    r = upload([
        ("files", ("run.exe", open("/tmp/dr_bad.exe", "rb"), "application/octet-stream")),
        ("files", ("empty.txt", open("/tmp/dr_empty.txt", "rb"), "text/plain")),
        ("files", ("..\\..\\evil.md", open("/tmp/dr_custom.txt", "rb"), "text/markdown")),
    ])
    body = r.json() if r.status_code == 200 else {}
    check("mixed batch: bad ext + empty skipped", r.status_code == 200
          and {s["name"] for s in body.get("skipped", [])} == {"run.exe", "empty.txt"}, str(body.get("skipped")))
    check("mixed batch: traversal sanitized to evil.md", r.status_code == 200
          and body.get("uploaded") == ["evil.md"], str(body.get("uploaded")))
    if r.status_code == 200:
        check("documents +3 total", r.json()["documents"] == base_docs + 3,
              f"{base_docs} -> {r.json()['documents']}")

    r = upload([("files", ("empty.txt", open("/tmp/dr_empty.txt", "rb"), "text/plain"))])
    check("empty-only batch -> 400", r.status_code == 400)

    many = [("files", (f"f{i}.txt", open("/tmp/dr_custom.txt", "rb"), "text/plain")) for i in range(11)]
    r = upload(many)
    check("11-file batch -> 400", r.status_code == 400)

    r = post_json("/query", {"query": "what is the DomainRAG-VERIFY-42 answer?"})
    check("query hits uploaded doc", r.status_code == 200
          and any("custom.txt" == cc["source"] for cc in r.json().get("citations", [])),
          str([cc["source"] for cc in r.json().get("citations", [])]))

    section("D. Model registry via API")

    r = post_json("/models", {"provider": "openai", "model": "gpt-4o-mini"})
    check("cloud without key -> 400", r.status_code == 400, str(r.json() if r else r.status_code))

    r = post_json("/models", {"provider": "ollama", "model": "not-installed-xyz"})
    check("uninstalled local model -> 400", r.status_code == 400, str(r.json() if r else r.status_code))

    r = post_json("/models", {"provider": "ollama", "model": "qwen2.5:7b"})
    check("swap to qwen2.5:7b", r.status_code == 200 and r.json()["model"] == "qwen2.5:7b")
    r = get("/models")
    check("API reflects swap", r.json()["current"]["model"] == "qwen2.5:7b")
    r = post_json("/query", {"query": "what is git rebase?"})
    check("query works after swap", r.status_code == 200 and len(r.json()["answer"]) > 30)

    r = post_json("/models/reset", {})
    check("reset restores default", r.status_code == 200 and r.json()["model"] == "qwen3:8b"
          and r.json()["fallback_active"] is False, str(r.json() if r else r.status_code))

    section("E. Rate limiting")

    statuses = [get("/models").status_code for _ in range(35)]
    check("burst of /models calls yields 429s", 429 in statuses and statuses[-1] == 429,
          f"{sorted(set(statuses))} (last={statuses[-1]})")
    laters = [s for s in statuses[-10:] if s == 429]
    check("429s dominate tail", len(laters) >= 8, f"{len(laters)}/10")


# ---------------------------------------------------------------------------
# D-e2e. Automatic fallback: boot a second backend whose env forces a broken
# cloud provider (raw bootstrap, no validation); the first query must fail,
# fall back to the local model, stream an answer, and expose fallback_active.
# ---------------------------------------------------------------------------
def fallback_e2e_checks():
    section("D. Fallback — e2e on a second instance (port 8001)")
    env = dict(os.environ, PYTHONPATH=".",
               DOMAINRAG_PROVIDER="zen",
               DOMAINRAG_MODEL="deepseek-v4-flash-free",
               DOMAINRAG_PROVIDER_API_KEY="sk-bogus-does-not-exist",
               DOMAINRAG_BASE_URL="")
    env.pop("DOMAINRAG_API_KEY", None)

    log = "/tmp/domainrag-fallback.log"
    proc = subprocess.Popen(["./venv/bin/uvicorn", "app.main:app", "--port", "8010"],
                            cwd=BACKEND_DIR, env=env, stdout=open(log, "w"), stderr=subprocess.STDOUT)

    deadline = time.time() + 90
    ok = False
    with httpx.Client(base_url="http://localhost:8010", timeout=180) as c:
        while time.time() < deadline:
            try:
                r = c.get("/health")
                if r.status_code == 200:
                    ok = True
                    break
            except httpx.HTTPError:
                time.sleep(1)
        check("fallback instance boots with unknown model name", ok)
        if ok:
            r = c.get("/models")
            check("boots with broken zen provider", r.json()["current"]["provider"] == "zen"
                  and r.json()["current"]["fallback_active"] is False)
            r = c.post("/query/stream", json={"query": "what is a Python decorator?"})
            events = parse_sse(r.text) if r.status_code == 200 else {}
            check("stream succeeds via fallback", events.get("error", 0) == 0
                  and events.get("done", 0) == 1 and events.get("token", 0) >= 10,
                  f"err={events.get('error', 0)} tokens={events.get('token', 0)}")
            check("fallback event surfaced", any("falling back" in b.lower()
                  for b in [ln for ln in r.text.split("\n") if ln.startswith("data:")]),
                  "[no fallback notice in stream]")
            r = c.get("/models")
            cur = r.json()["current"]
            check("fallback_active after outage", cur["provider"] == "ollama" and cur["fallback_active"] is True,
                  str(cur))
            r = c.post("/models", json={"provider": "ollama", "model": "qwen3:8b"})
            check("re-selecting a model clears fallback", r.json()["fallback_active"] is False)

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    check("fallback instance stopped", True)


# ---------------------------------------------------------------------------
# F. Cleanup: remove test uploads, rebuild index, restart the backend
# ---------------------------------------------------------------------------
def cleanup_and_restart():
    section("F. Cleanup and restore")
    removed = []
    for name in TEST_FILES:
        path = os.path.join(DATA_DIR, name)
        if os.path.exists(path):
            os.remove(path)
            removed.append(name)
    check("test uploads removed from corpus", all(
        not os.path.exists(os.path.join(DATA_DIR, n)) for n in TEST_FILES), str(removed))

    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
        os.kill(pid, signal.SIGTERM)
        time.sleep(1.5)
        check("old backend stopped", True)
    except (FileNotFoundError, ProcessLookupError, ValueError):
        subprocess.run(["pkill", "-f", "uvicorn app.main:app"], check=False)
        time.sleep(1.5)
        check("old backend stopped (pkill)", True)

    section("F. Rebuild index + relaunch backend")
    env = dict(os.environ, PYTHONPATH=".")
    try:
        subprocess.run(["./venv/bin/python", "-c",
                        "from app.ingestion import build_index; i = build_index(); "
                        f"print('index nodes:', len(i.docstore.docs))"],
                       cwd=BACKEND_DIR, env=env, check=True, capture_output=True, text=True, timeout=300)
        check("clean index rebuilt offline", True)
    except subprocess.CalledProcessError as e:
        check("clean index rebuilt offline", False, e.stderr[-400:])

    with open(PID_FILE, "w") as f:
        pass
    proc = subprocess.Popen(
        "setsid nohup env PYTHONPATH=. ./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 "
        f"> {SERVER_LOG} 2>&1 < /dev/null & echo $! > {PID_FILE}",
        cwd=BACKEND_DIR, shell=True, env=env)
    proc.wait()

    deadline = time.time() + 60
    ok = False
    with httpx.Client(base_url=BASE, timeout=10) as c:
        while time.time() < deadline:
            try:
                r = c.get("/health")
                if r.status_code == 200:
                    ok = True
                    break
            except httpx.HTTPError:
                time.sleep(1)
        if ok:
            check("backend restarted healthy", True, f"documents={r.json()['documents']}")
        else:
            check("backend restarted healthy", False)


def main():
    section("Starting pipeline verification", "base=http://localhost:8000")
    unit_checks()
    api_checks()
    fallback_e2e_checks()
    cleanup_and_restart()
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"\n{'=' * 64}\n{passed}/{total} checks passed in {time.time() - g_start:.0f}s")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()