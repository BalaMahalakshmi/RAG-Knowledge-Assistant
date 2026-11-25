import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "rag_knowledge_assistant")

VECTOR_SIZE = 384

if not QDRANT_URL or not QDRANT_API_KEY:
    raise ValueError("Qdrant credentials are missing in .env")

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=30)

try:
    # Check whether collection already exists
    if not client.collection_exists(COLLECTION_NAME):

        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE, distance=models.Distance.COSINE
            ),
        )

        print("Collection created successfully!")

    else:
        print("Collection already exists.")

    # Verify collection configuration
    info = client.get_collection(COLLECTION_NAME)

    print("\nCollection Details:")
    print("Name:", COLLECTION_NAME)
    print("Vector dimensions:", info.config.params.vectors.size)
    print("Distance:", info.config.params.vectors.distance)
    print("Points count:", info.points_count)
    print("\nQdrant collection setup successful!")

except Exception as error:
    print("Collection setup failed!")
    print("Error:", error)

finally:
    client.close()
