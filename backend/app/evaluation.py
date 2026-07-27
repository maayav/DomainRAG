"""RAGAS evaluation pipeline."""
import os
import csv
import logging
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision

logger = logging.getLogger(__name__)

TEST_SET_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "evaluation", "test_set.csv")


def load_test_set():
    questions, answers, contexts = [], [], []
    with open(TEST_SET_PATH, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions.append(row["question"])
            answers.append(row["answer"])
            contexts.append([row["contexts"]])
    return questions, answers, contexts


def run_ragas_eval(questions, answers, contexts, generated_answers):
    dataset = Dataset.from_dict({
        "question": questions,
        "answer": generated_answers,
        "contexts": contexts,
        "ground_truth": answers,
    })
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
    )
    return result


def save_results(result, output_path):
    import json
    df = result.to_pandas()
    csv_path = output_path + ".csv"
    json_path = output_path + ".json"
    df.to_csv(csv_path, index=False)
    with open(json_path, "w") as f:
        json.dump(result.__dict__, f, indent=2, default=str)
    logger.info(f"Results saved to {csv_path} and {json_path}")