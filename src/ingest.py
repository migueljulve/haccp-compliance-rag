"""Embed the HACCP corpus and load it into Qdrant."""


# Imports and constants
import os

from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

from src.parse import parse_all

COLLECTION = "haccp"
MODEL_NAME = "multi-qa-mpnet-base-dot-v1"
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))


# Upload chunks and generate embeddings.
def main():
    chunks = parse_all()
    print(f"Parsed {len(chunks)} chunks")

    model = SentenceTransformer(MODEL_NAME)
    vector_size = model.get_sentence_embedding_dimension()

    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)


    # create collection in Qdrant

    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=models.VectorParams(
        size=vector_size, distance=models.Distance.DOT
        ),
    )

    # Upload points

    points = [
        models.PointStruct(id=i, vector=embeddings[i].tolist(), payload=chunks[i])
        for i in range(len(chunks))
    ]
    client.upsert(collection_name=COLLECTION, points=points)

    print(f"Uploaded {len(points)} points to '{COLLECTION}' (dim={vector_size})")


if __name__ == "__main__":
    main()

