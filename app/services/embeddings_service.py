from functools import lru_cache
from typing import List, Dict

from sentence_transformers import SentenceTransformer

# Embedding model configuration
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

EMBEDDING_DIMENSION = 384

BATCH_SIZE = 16


@lru_cache(maxsize=1)
def load_embedding_model():
    """
    Load the embedding model once and reuse it.
    """

    print(f"Loading embedding model: {MODEL_NAME}")

    model = SentenceTransformer(MODEL_NAME)

    print("Embedding model loaded successfully!")

    return model


def generate_embeddings(chunks: List[Dict]) -> List[Dict]:
    """
    Convert document chunks into numerical vectors.
    """

    if not chunks:
        raise ValueError("No chunks provided for embedding.")

    model = load_embedding_model()

    texts = [chunk["text"] for chunk in chunks]

    # Generate embeddings in batches
    vectors = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    if vectors.shape[1] != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Expected {EMBEDDING_DIMENSION} dimensions, "
            f"received {vectors.shape[1]}."
        )

    embedded_chunks = []

    for chunk, vector in zip(chunks, vectors):

        embedded_chunks.append(
            {
                "chunk_id": chunk["chunk_id"],
                "page_number": chunk["page_number"],
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"],
                "character_count": chunk["character_count"],
                "embedding": vector.tolist(),
            }
        )

    return embedded_chunks


def generate_query_embedding(query: str) -> List[float]:
    """
    Convert a student's question into a numerical vector.
    Uses the same model as document embeddings.
    """

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    model = load_embedding_model()

    vector = model.encode(
        [query.strip()], normalize_embeddings=True, convert_to_numpy=True
    )

    if vector.shape[1] != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Expected {EMBEDDING_DIMENSION} dimensions, "
            f"received {vector.shape[1]}."
        )

    return vector[0].tolist()
