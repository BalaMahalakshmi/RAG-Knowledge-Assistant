import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient

# Load environment variables
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Validate configuration
if not QDRANT_URL or not QDRANT_API_KEY:
    raise ValueError("QDRANT_URL or QDRANT_API_KEY is missing in .env")

# Connect to Qdrant Cloud
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=30)

try:
    # Test connection by retrieving collections
    response = client.get_collections()

    print("Qdrant Cloud connection successful!")
    print("\nAvailable collections:")

    for collection in response.collections:
        print(f"- {collection.name}")

    print("\nConnection test completed successfully!")

except Exception as error:
    print("Qdrant connection failed!")
    print("Error:", error)

finally:
    client.close()
