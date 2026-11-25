import os
import math

from uuid import uuid5, NAMESPACE_URL
from dotenv import load_dotenv

from qdrant_client import QdrantClient, models

load_dotenv()

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "rag_knowledge_assistant")

VECTOR_SIZE = 384
BATCH_SIZE = 64


def get_qdrant_client():
    """Connect to Qdrant Cloud."""

    if not QDRANT_URL or not QDRANT_API_KEY:
        raise ValueError("QDRANT_URL or QDRANT_API_KEY missing in .env")

    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=30)


def ensure_collection(client):
    """Verify that the required collection exists."""

    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE, distance=models.Distance.COSINE
            ),
        )

        print("Qdrant collection created successfully!")

    else:
        info = client.get_collection(COLLECTION_NAME)

        vector_config = info.config.params.vectors

        if not isinstance(vector_config, models.VectorParams):
            raise ValueError("Expected a default unnamed vector configuration.")

        if vector_config.size != VECTOR_SIZE:
            raise ValueError(
                f"Dimension mismatch: expected {VECTOR_SIZE}, "
                f"received {vector_config.size}"
            )

        if vector_config.distance != models.Distance.COSINE:
            raise ValueError("Collection distance must be COSINE.")

        print("Qdrant collection verified successfully!")


def ensure_document_id_index(client):
    """
    Create a keyword payload index for document_id
    if it does not already exist.
    """

    info = client.get_collection(COLLECTION_NAME)

    payload_schema = info.payload_schema or {}

    # Check whether the index already exists.
    if "document_id" not in payload_schema:

        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="document_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
            wait=True,
        )

        print("document_id payload index created successfully!")

    else:
        print("document_id payload index already exists!")


def store_embeddings(embedded_chunks: list, document_id: str, original_filename: str):
    """Store document embeddings and metadata in Qdrant."""

    if not embedded_chunks:
        raise ValueError("No embeddings received.")

    client = get_qdrant_client()

    try:
        ensure_collection(client)

        ensure_document_id_index(client)

        points = []

        for chunk in embedded_chunks:

            vector = chunk.get("embedding")

            if not isinstance(vector, list):
                raise ValueError(f"Missing embedding: {chunk.get('chunk_id')}")

            if len(vector) != VECTOR_SIZE:
                raise ValueError(f"Invalid vector dimension: {len(vector)}")

            if not all(
                isinstance(value, (int, float)) and math.isfinite(value)
                for value in vector
            ):
                raise ValueError("Invalid vector values detected.")

            chunk_id = chunk["chunk_id"]

            # Generate a deterministic UUID for every chunk.
            point_id = str(uuid5(NAMESPACE_URL, f"{document_id}:{chunk_id}"))

            # Store original text and source information.
            payload = {
                "document_id": document_id,
                "original_filename": original_filename,
                "chunk_id": chunk_id,
                "page_number": chunk["page_number"],
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"],
                "character_count": chunk["character_count"],
            }

            points.append(
                models.PointStruct(id=point_id, vector=vector, payload=payload)
            )

        # Upload vectors in batches.
        for start in range(0, len(points), BATCH_SIZE):

            batch = points[start : start + BATCH_SIZE]

            client.upsert(collection_name=COLLECTION_NAME, points=batch, wait=True)

        return {
            "success": True,
            "document_id": document_id,
            "collection_name": COLLECTION_NAME,
            "total_vectors_stored": len(points),
            "message": "Embeddings stored successfully in Qdrant.",
        }

    finally:
        client.close()


def search_similar_chunks(query_vector: list, document_id: str, top_k: int = 3):
    """
    Search Qdrant for the most relevant document chunks.
    """

    if not query_vector:
        raise ValueError("Query vector cannot be empty.")

    if len(query_vector) != VECTOR_SIZE:
        raise ValueError(
            f"Expected {VECTOR_SIZE} dimensions, " f"received {len(query_vector)}."
        )

    if not document_id:
        raise ValueError("Document ID is required.")

    if not 1 <= top_k <= 10:
        raise ValueError("top_k must be between 1 and 10.")

    client = get_qdrant_client()

    try:
        ensure_collection(client)

        ensure_document_id_index(client)

        # Search only within the requested document.
        search_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="document_id", match=models.MatchValue(value=document_id)
                )
            ]
        )

        # Find the most similar stored vectors.
        response = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=search_filter,
            limit=top_k,
            with_payload=True,
        )

        results = []

        for point in response.points:

            payload = point.payload or {}

            results.append(
                {
                    "chunk_id": payload.get("chunk_id"),
                    "document_id": payload.get("document_id"),
                    "filename": payload.get("original_filename"),
                    "page_number": payload.get("page_number"),
                    "chunk_index": payload.get("chunk_index"),
                    "text": payload.get("text"),
                    "similarity_score": float(point.score),
                }
            )

        return results

    finally:
        client.close()
