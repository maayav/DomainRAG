"""RAGAS evaluation pipeline."""
import os
import csv
import json
import logging
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
from langchain_ollama import OllamaLLM
from langchain_huggingface import HuggingFaceEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

from app.config import DATA_DIR

logger = logging.getLogger(__name__)

TEST_SET_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "evaluation", "test_set.csv")

EVAL_MODEL = os.environ.get("EVAL_MODEL", "qwen2.5:7b")
EVAL_TIMEOUT = int(os.environ.get("EVAL_TIMEOUT", "180"))


def resolve_contexts(source_names):
    """Expand document filenames to the actual source text used as ground-truth context."""
    contexts = []
    for name in source_names:
        path = os.path.join(DATA_DIR, name)
        try:
            with open(path, encoding="utf-8") as f:
                contexts.append(f.read().strip())
        except OSError:
            logger.warning(f"Ground-truth source not found: {name}")
            contexts.append(name)
    return contexts


def load_test_set():
    questions, answers, contexts = [], [], []
    with open(TEST_SET_PATH, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions.append(row["question"])
            answers.append(row["answer"])
            contexts.append(resolve_contexts([row["contexts"]]))
    return questions, answers, contexts


def run_ragas_eval(questions, answers, contexts, generated_answers):
    dataset = Dataset.from_dict({
        "question": questions,
        "answer": generated_answers,
        "contexts": contexts,
        "ground_truth": answers,
    })
    llm = LangchainLLMWrapper(
        OllamaLLM(
            model=EVAL_MODEL,
            temperature=0,
            num_ctx=8192,
            format="json",
            timeout=EVAL_TIMEOUT,
        )
    )
    embeddings = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    )
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        llm=llm,
        embeddings=embeddings,
    )
    return result


def save_results(result, output_path):
    df = result.to_pandas()
    csv_path = output_path + ".csv"
    json_path = output_path + ".json"
    df.to_csv(csv_path, index=False)
    with open(json_path, "w") as f:
        json.dump(result.__dict__, f, indent=2, default=str)
    logger.info(f"Results saved to {csv_path} and {json_path}")