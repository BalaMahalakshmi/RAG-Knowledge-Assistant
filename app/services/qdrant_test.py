from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# 1. Connect to Qdrant
client = QdrantClient(url="http://localhost:6333")

COLLECTION_NAME = "rag_demo_4d"


def setup_collection():

    # 2. Check whether collection exists
    if not client.collection_exists(COLLECTION_NAME):

        # 3. Create a collection
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=4, distance=Distance.COSINE),
        )

        print("Collection created successfully!")

    else:
        print("Collection already exists!")


def insert_sample_vectors():

    # 4. Insert sample vectors with payload
    points = [
        PointStruct(
            id=1,
            vector=[0.1, 0.2, 0.3, 0.4],
            payload={
                "text": "Python is a programming language",
                "category": "Programming",
            },
        ),
        PointStruct(
            id=2,
            vector=[0.2, 0.3, 0.4, 0.5],
            payload={
                "text": "Machine Learning is a subset of AI",
                "category": "Artificial Intelligence",
            },
        ),
        PointStruct(
            id=3,
            vector=[0.9, 0.8, 0.7, 0.6],
            payload={
                "text": "Deep Learning uses neural networks",
                "category": "Deep Learning",
            },
        ),
    ]

    client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)

    print("Sample vectors inserted successfully!")


def search_vectors():

    # 5. Search using a sample query vector
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=[0.1, 0.2, 0.3, 0.4],
        limit=2,
        with_payload=True,
    )

    print("\nSearch Results:")

    for result in results.points:
        print("Score:", result.score)
        print("Payload:", result.payload)
        print("----------------------")


if __name__ == "__main__":

    setup_collection()

    insert_sample_vectors()

    search_vectors()

    print("\nQdrant integration successful!")
