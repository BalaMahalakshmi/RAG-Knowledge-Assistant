import logging

from app.services.embeddings_service import generate_query_embedding

from app.services.qdrant_service import search_similar_chunks

from app.services.llm_service import generate_answer, rewrite_followup_question

logger = logging.getLogger(__name__)


def build_context(retrieved_chunks: list) -> str:
    """
    Build LLM context from the retrieved document chunks.
    Each chunk receives a source label and page reference.
    """

    if not retrieved_chunks:
        return ""

    context_parts = []

    for index, chunk in enumerate(retrieved_chunks, start=1):

        filename = chunk.get("filename", "Unknown document")

        page_number = chunk.get("page_number", "Unknown")

        text = chunk.get("text", "")

        source_label = f"Source {index}"

        context_part = f"""
[{source_label}]

Filename: {filename}
Page: {page_number}

Document content:
{text}
"""

        context_parts.append(context_part)

    return "\n\n".join(context_parts)


async def answer_document_question(
    document_id: str, question: str, top_k: int = 3, conversation_history: list = None
) -> dict:
    """
    Complete conversational RAG workflow:

    1. Understand the follow-up question.
    2. Generate a standalone retrieval query.
    3. Embed the retrieval query.
    4. Retrieve relevant document chunks.
    5. Build document context.
    6. Generate a grounded answer using Groq.
    7. Return answer and source references.
    """

    if not document_id:
        raise ValueError("Document ID is required.")

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    conversation_history = conversation_history or []

    # STEP 1: Rewrite the follow-up question.
    retrieval_query = await rewrite_followup_question(
        question=question, conversation_history=conversation_history
    )

    # STEP 2: Generate the retrieval embedding.
    query_vector = generate_query_embedding(retrieval_query)

    # STEP 3: Retrieve relevant document chunks.
    retrieved_chunks = search_similar_chunks(
        query_vector=query_vector, document_id=document_id, top_k=top_k
    )

    # STEP 4: Handle no-result situations.
    if not retrieved_chunks:

        return {
            "answer": (
                "I could not find relevant information "
                "in the uploaded document to answer this question."
            ),
            "sources": [],
            "retrieved_chunks": 0,
            "retrieval_query": retrieval_query,
        }

    # STEP 5: Build context from retrieved chunks.
    context = build_context(retrieved_chunks)

    if not context.strip():
        raise RuntimeError("Unable to build context from retrieved chunks.")

    # STEP 6: Generate answer with conversation history.
    answer = await generate_answer(
        question=question, context=context, conversation_history=conversation_history
    )

    # STEP 7: Prepare source references.
    sources = []

    seen_sources = set()

    for index, chunk in enumerate(retrieved_chunks, start=1):

        filename = chunk.get("filename")
        page_number = chunk.get("page_number")
        chunk_id = chunk.get("chunk_id")

        source_key = (filename, page_number)

        if source_key in seen_sources:
            continue

        seen_sources.add(source_key)

        sources.append(
            {
                "source_label": f"Source {index}",
                "filename": filename,
                "page_number": page_number,
                "chunk_id": chunk_id,
                "similarity_score": chunk.get("similarity_score"),
            }
        )

    return {
        "answer": answer,
        "sources": sources,
        "retrieved_chunks": len(retrieved_chunks),
        "retrieval_query": retrieval_query,
    }
