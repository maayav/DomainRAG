"""Quick smoke test: run RAGAS eval on a 3-question subset."""
import os
import sys
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
logging.basicConfig(level=logging.WARNING)

from app.evaluation import run_ragas_eval, resolve_contexts

questions = [
    "What is a Python decorator?",
    "What does an INNER JOIN return?",
    "What is the purpose of a CI/CD pipeline?",
]
answers = [
    "A decorator is a function that takes another function and extends its behavior without explicitly modifying it using the @ syntax.",
    "Only rows where there is a match in both tables based on the join condition.",
    "To automate the building testing and deployment of software changes after every merge.",
]
contexts = [resolve_contexts(["python-decorators.md"]), resolve_contexts(["sql-joins.md"]), resolve_contexts(["ci-cd-basics.md"])]
generated = [
    "A Python decorator is a function that takes another function as an argument and extends its behavior without modifying it.",
    "An INNER JOIN returns only the rows where there is a match in both tables.",
    "A CI/CD pipeline automates the building, testing, and deployment of software changes.",
]

print("Running RAGAS on 3-question subset...")
result = run_ragas_eval(questions, answers, contexts, generated)
df = result.to_pandas()
print(df[["faithfulness", "answer_relevancy", "context_recall", "context_precision"]].to_string())
