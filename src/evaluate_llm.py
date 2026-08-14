"""Compare prompt variants and models on a sample of ground truth questions.

Answers are scored two ways: LLM-as-a-judge relevance (see evaluate_relevance in
src/rag.py), and citation rate — whether the answer actually points at the regulation
it came from, which is what makes a compliance answer verifiable rather than merely
plausible. Relevance alone cannot separate the prompt variants, since the judge is only
asked whether the answer addresses the question, not whether it cites its source.
"""

import re

import pandas as pd
from tqdm import tqdm

from src.rag import prompt_template_cited, prompt_template_plain, rag

SAMPLE_SIZE = 30

# Matches the citation formats produced by src/parse.py, e.g. "21 CFR 123 § 123.6",
# "Codex CXC 1-1969 § 9.3.2", "FSIS HACCP Guidebook, STEP 2".
CITATION_RE = re.compile(r"§\s*[\d.]+|FSIS HACCP Guidebook,\s*STEP\s*\d+", re.IGNORECASE)


def evaluate(sample, label, **rag_kwargs):
    """Run the RAG pipeline over the sample and report answer quality, speed and tokens."""
    relevance_counts = {"RELEVANT": 0, "PARTLY_RELEVANT": 0, "NON_RELEVANT": 0, "UNKNOWN": 0}
    response_times = []
    total_tokens = []
    cited = 0
    failed = 0

    for q in tqdm(sample, desc=label):
        # A model whose free-tier quota is exhausted raises after exhausting its retries.
        # Skip that question instead of losing the results already collected.
        try:
            result = rag(q["question"], **rag_kwargs)
        except RuntimeError:
            failed += 1
            continue
        relevance_counts[result["relevance"]] += 1
        response_times.append(result["response_time"])
        total_tokens.append(result["total_tokens"] + result["eval_total_tokens"])
        if CITATION_RE.search(result["answer"]):
            cited += 1

    print(f"\n{label}")
    if not response_times:
        print(f"  No questions completed ({failed}/{len(sample)} failed: quota exhausted)")
        return

    answered = len(response_times)
    print(f"  Relevance distribution: {relevance_counts}")
    print(f"  Answers citing a source: {cited}/{answered} ({cited / answered:.0%})")
    print(f"  Avg response time: {sum(response_times) / answered:.2f}s")
    print(f"  Avg total tokens: {sum(total_tokens) / answered:.0f}")
    if failed:
        print(f"  Skipped: {failed}/{len(sample)} (quota exhausted)")


def main():
    gt_df = pd.read_csv("data/ground_truth.csv")
    sample = gt_df.sample(n=SAMPLE_SIZE, random_state=1).to_dict(orient="records")

    # Prompt comparison, both on flash-lite: does demanding explicit citations and
    # explicit abstention change answer quality?
    #
    # gemini-3.5-flash was evaluated the same way in an earlier run and could not finish:
    # it exhausted its free-tier quota partway through the sample even with retries, so it
    # is not part of the default comparison. To reproduce that finding, add:
    #     evaluate(sample, "flash", model="gemini-3.5-flash")
    evaluate(sample, "prompt A (cited)", prompt_template=prompt_template_cited)
    evaluate(sample, "prompt B (plain)", prompt_template=prompt_template_plain)


if __name__ == "__main__":
    main()
