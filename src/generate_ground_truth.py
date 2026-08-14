"""Generate ground-truth questions per chunk with an LLM, for retrieval evaluation."""

# IMPORTS and CONSTANTS
import csv
import json
import os
import time

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError
from tqdm import tqdm

from src.parse import parse_all

MODEL = "gemini-3.5-flash-lite"
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
N_QUESTIONS = 2
OUTPUT = "data/ground_truth.csv"


# PROMPT
PROMPT_TEMPLATE = """You are building a retrieval evaluation set for a HACCP food safety compliance assistant.

Based ONLY on the regulatory text below, write {n} distinct questions a food safety professional might ask whose answer is contained in this text. Make each question specific and self-contained: do not refer to "this section" or "the text". Vary the wording and do not copy sentences verbatim.

Source: {citation}
Title: {title}

Text:
{text}

Return a JSON object: {{"questions": ["...", "..."]}}"""


# LLM CALL: generate questions for one chunk, with retry and robust JSON parsing
def generate_questions(client, chunk):
    prompt = PROMPT_TEMPLATE.format(
        n=N_QUESTIONS, citation=chunk["citation"], title=chunk["title"], text=chunk["text"]
    )
    for _ in range(6):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            raw = response.choices[0].message.content.strip()
            raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return json.loads(raw)["questions"]
        except RateLimitError:
            time.sleep(20)
        except (json.JSONDecodeError, KeyError):
            return []
    return []


# LOOP
def main():
    load_dotenv()
    client = OpenAI(api_key=os.getenv("GEMINI_API_KEY"), base_url=BASE_URL)
    chunks = parse_all()

    rows = []
    for chunk_id, chunk in enumerate(tqdm(chunks)):
        for question in generate_questions(client, chunk):
            rows.append(
                {
                    "chunk_id": chunk_id,
                    "citation": chunk["citation"],
                    "source": chunk["source"],
                    "question": question,
                }
            )

    # saves the csv
    with open(OUTPUT, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["chunk_id", "citation", "source", "question"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} questions to {OUTPUT}")


if __name__ == "__main__":
    main()
