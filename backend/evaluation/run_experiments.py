"""Run RAGAS evaluation and experiments across multiple configurations."""
import os
import sys
import json
import time
import csv
import logging
from copy import deepcopy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONFIGS = {
    "A_baseline": {"chunk_size": 512, "chunk_overlap": 128, "top_k": 3},
    "B_large_chunks": {"chunk_size": 1024, "chunk_overlap": 256, "top_k": 5},
    "C_more_docs": {"chunk_size": 512, "chunk_overlap": 128, "top_k": 5},
}

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
TEST_SET_PATH = os.path.join(os.path.dirname(__file__), "test_set.csv")


def load_test_set():
    questions, answers, contexts = [], [], []
    with open(TEST_SET_PATH, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions.append(row["question"])
            answers.append(row["answer"])
            contexts.append([row["contexts"]])
    return questions, answers, contexts


def run_experiment(config_name, config):
    from app.ingestion import build_index, load_index
    from app.query_engine import query_index
    from app import config as cfg
    from app.evaluation import run_ragas_eval

    cfg.CHUNK_SIZE = config["chunk_size"]
    cfg.CHUNK_OVERLAP = config["chunk_overlap"]
    cfg.TOP_K = config["top_k"]

    questions, answers, contexts = load_test_set()
    generated_answers = []
    retrieved_contexts = []
    latencies = []

    try:
        index = load_index()
        logger.info(f"Loaded existing index for {config_name}")
    except Exception:
        index = build_index()
        logger.info(f"Built new index for {config_name}")

    for q in questions:
        start = time.time()
        result = query_index(index, q)
        elapsed = time.time() - start
        generated_answers.append(result["answer"])
        retrieved_contexts.append([c["text"] for c in result["citations"]])
        latencies.append(elapsed)

    logger.info(f"Running RAGAS evaluation for {config_name}...")
    ragas_result = run_ragas_eval(questions, answers, contexts, generated_answers)
    ragas_df = ragas_result.to_pandas()

    return {
        "config": config_name,
        "params": config,
        "latency_avg": sum(latencies) / len(latencies),
        "latencies": latencies,
        "faithfulness": float(ragas_df["faithfulness"].mean()),
        "answer_relevancy": float(ragas_df["answer_relevancy"].mean()),
        "context_recall": float(ragas_df["context_recall"].mean()),
        "context_precision": float(ragas_df["context_precision"].mean()),
    }


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    all_results = []

    for config_name, config in CONFIGS.items():
        logger.info(f"Running config: {config_name} ({config})")
        result = run_experiment(config_name, config)
        all_results.append(result)

    df_data = []
    for r in all_results:
        df_data.append({
            "config": r["config"],
            "chunk_size": r["params"]["chunk_size"],
            "chunk_overlap": r["params"]["chunk_overlap"],
            "top_k": r["params"]["top_k"],
            "latency_avg": round(r["latency_avg"], 3),
            "faithfulness": round(r.get("faithfulness", 0), 3),
            "answer_relevancy": round(r.get("answer_relevancy", 0), 3),
            "context_recall": round(r.get("context_recall", 0), 3),
            "context_precision": round(r.get("context_precision", 0), 3),
        })

    import pandas as pd
    df = pd.DataFrame(df_data)
    csv_path = os.path.join(RESULTS_DIR, "comparison.csv")
    df.to_csv(csv_path, index=False)
    logger.info(f"Results saved to {csv_path}")

    json_path = os.path.join(RESULTS_DIR, "comparison.json")
    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    logger.info(f"Results saved to {json_path}")

    print("\n=== EXPERIMENT RESULTS ===")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()