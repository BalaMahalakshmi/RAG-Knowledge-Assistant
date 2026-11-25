from app.services.qdrant_service import (
    ensure_collection,
    get_qdrant_client,
    COLLECTION_NAME,
)


def main():

    print("Connecting to Qdrant Cloud...")

    client = get_qdrant_client()

    try:
        # Pass the client as an argument
        ensure_collection(client)

        info = client.get_collection(COLLECTION_NAME)

        print("\nQdrant Collection Details:")
        print("Name:", COLLECTION_NAME)
        print("Status:", info.status)
        print("Vector count:", info.points_count)
        print("Vector size:", info.config.params.vectors.size)
        print("Distance:", info.config.params.vectors.distance)

        print("\nQdrant storage service test successful!")

    finally:
        client.close()


if __name__ == "__main__":
    main()
