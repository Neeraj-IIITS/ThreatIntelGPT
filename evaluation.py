# evaluation.py
"""
Simple evaluation of the summariser using ROUGE on a tiny dataset.
You can create a JSON or CSV with fields: 'text', 'reference_summary'.
"""

from typing import List, Dict
from rouge_score import rouge_scorer
from src.summariser import summarise


def compute_rouge(
    texts: List[str],
    reference_summaries: List[str]
) -> Dict[str, float]:
    scorer = rouge_scorer.RougeScorer(
        ["rouge1", "rouge2", "rougeL"], use_stemmer=True
    )
    r1_f, r2_f, rl_f = 0.0, 0.0, 0.0
    n = len(texts)

    for text, ref in zip(texts, reference_summaries):
        gen = summarise(text)
        scores = scorer.score(ref, gen)
        r1_f += scores["rouge1"].fmeasure
        r2_f += scores["rouge2"].fmeasure
        rl_f += scores["rougeL"].fmeasure

    return {
        "rouge1_f": r1_f / n,
        "rouge2_f": r2_f / n,
        "rougeL_f": rl_f / n
    }


if __name__ == "__main__":
    # Example dummy data – replace with your own samples
    texts = [
        "Long CTI article text 1 ...",
        "Long CTI article text 2 ..."
    ]
    refs = [
        "Human-written short summary 1 ...",
        "Human-written summary 2 ..."
    ]

    metrics = compute_rouge(texts, refs)
    print("ROUGE metrics:", metrics)
