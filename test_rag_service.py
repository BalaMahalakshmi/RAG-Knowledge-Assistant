
import asyncio

from app.services.rag_service import answer_document_question


async def main():

    document_id = "0782bb757295485fa19dfec29435ceeb"

    question = "What is supervised learning?"

    print("=" * 60)
    print("COMPLETE RAG PIPELINE TEST")
    print("=" * 60)

    result = await answer_document_question(
        document_id=document_id,
        question=question,
        top_k=3
    )

    print("\nQUESTION:")
    print(question)

    print("\nGENERATED ANSWER:")
    print(result["answer"])

    print("\nSOURCES:")

    for source in result["sources"]:
        print(
            f"{source['source_label']} | "
            f"{source['filename']} | "
            f"Page {source['page_number']}"
        )

    print("\nRETRIEVED CHUNKS:")
    print(result["retrieved_chunks"])


if __name__ == "__main__":
    asyncio.run(main())
