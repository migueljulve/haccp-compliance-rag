"""Compare gemini-3.5-flash-lite vs gemini-3.5-flash on a sample of ground truth questions."""

import pandas as pd
from tqdm import tqdm

from src.rag import rag

SAMPLE_SIZE = 30
MODELS = ["gemini-3.5-flash-lite", "gemini-3.5-flash"]


def main():
    gt_df = pd.read_csv("data/ground_truth.csv")
    sample = gt_df.sample(n=SAMPLE_SIZE, random_state=1).to_dict(orient="records")

    for model in MODELS:
        relevance_counts = {"RELEVANT": 0, "PARTLY_RELEVANT": 0, "NON_RELEVANT": 0, "UNKNOWN": 0}
        response_times = []
        total_tokens = []

        for q in tqdm(sample, desc=model):
            result = rag(q["question"], model=model)
            relevance_counts[result["relevance"]] += 1
            response_times.append(result["response_time"])
            total_tokens.append(result["total_tokens"] + result["eval_total_tokens"])

        print(f"\n{model}")
        print(f"  Relevance distribution: {relevance_counts}")
        print(f"  Avg response time: {sum(response_times) / len(response_times):.2f}s")
        print(f"  Avg total tokens: {sum(total_tokens) / len(total_tokens):.0f}")


if __name__ == "__main__":
    main()
