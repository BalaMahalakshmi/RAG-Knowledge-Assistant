
import json
import urllib.request
import urllib.error


BASE_URL = "http://127.0.0.1:8000"

DOCUMENT_ID = "0782bb757295485fa19dfec29435ceeb"


def send_request(url, method="GET", data=None):

    headers = {
        "Content-Type": "application/json"
    }

    body = None

    if data is not None:
        body = json.dumps(data).encode("utf-8")

    request = urllib.request.Request(
        url=url,
        data=body,
        headers=headers,
        method=method
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=120
        ) as response:

            return json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.HTTPError as error:

        print("HTTP Error:", error.code)
        print(error.read().decode("utf-8"))
        raise

    except urllib.error.URLError as error:

        print("Connection Error:", error.reason)
        raise


def main():

    print("=" * 60)
    print("CONVERSATION MEMORY TEST")
    print("=" * 60)

    # STEP 1: Create a new conversation.
    print("\nSTEP 1: Starting a new conversation...")

    first_response = send_request(
        f"{BASE_URL}/api/v1/chat/ask",
        method="POST",
        data={
            "document_id": DOCUMENT_ID,
            "question": "What is supervised learning?",
            "top_k": 3
        }
    )

    conversation_id = first_response["conversation_id"]

    print("\nFirst Answer:")
    print(first_response["answer"])

    print("\nConversation ID:")
    print(conversation_id)

    # STEP 2: Continue the conversation.
    print("\nSTEP 2: Asking a follow-up question...")

    second_response = send_request(
        f"{BASE_URL}/api/v1/chat/ask",
        method="POST",
        data={
            "document_id": DOCUMENT_ID,
            "conversation_id": conversation_id,
            "question": "What are its advantages?",
            "top_k": 3
        }
    )

    print("\nFollow-up Answer:")
    print(second_response["answer"])

    print("\nRetrieval Query:")
    print(second_response["retrieval_query"])

    # STEP 3: Retrieve saved history.
    print("\nSTEP 3: Retrieving conversation history...")

    history_response = send_request(
        f"{BASE_URL}/api/v1/chat/conversations/{conversation_id}"
    )

    print("\nConversation Messages:")

    for message in history_response["messages"]:

        print(
            f"\n{message['role'].upper()}: "
            f"{message['content']}"
        )

    # STEP 4: List document conversations.
    print("\nSTEP 4: Listing document conversations...")

    list_response = send_request(
        f"{BASE_URL}/api/v1/chat/conversations"
        f"?document_id={DOCUMENT_ID}"
    )

    print(
        json.dumps(
            list_response,
            indent=4
        )
    )

    print("\n" + "=" * 60)
    print("CONVERSATION MEMORY TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()
