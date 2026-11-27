
import logging
import re

from typing import Optional

from fastapi import (
    APIRouter,
    HTTPException,
    Query
)

from pydantic import BaseModel, Field

from app.services.rag_service import (
    answer_document_question
)

from app.services.conversation_service import (
    create_conversation,
    get_conversation,
    save_message,
    get_recent_messages,
    get_conversation_messages,
    list_conversations,
    delete_conversation
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["Chat"]
)


class ChatRequest(BaseModel):

    document_id: str = Field(
        ...,
        min_length=32,
        max_length=32
    )

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=10
    )

    conversation_id: Optional[str] = Field(
        default=None,
        min_length=32,
        max_length=32
    )


@router.post("/ask")
async def ask_document_question(request: ChatRequest):
    """
    Ask a question and continue an existing conversation,
    or create a new conversation automatically.
    """

    # STEP 1: Validate document ID.
    if not re.fullmatch(
        r"[a-f0-9]{32}",
        request.document_id
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID."
        )

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=422,
            detail="Question cannot be empty."
        )

    try:

        # STEP 2: Find or create a conversation.
        if request.conversation_id:

            if not re.fullmatch(
                r"[a-f0-9]{32}",
                request.conversation_id
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid conversation ID."
                )

            conversation = get_conversation(
                request.conversation_id
            )

            if not conversation:
                raise HTTPException(
                    status_code=404,
                    detail="Conversation not found."
                )

            # A conversation must remain associated
            # with its original uploaded document.
            if conversation["document_id"] != request.document_id:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Conversation does not belong "
                        "to the requested document."
                    )
                )

            conversation_id = request.conversation_id

        else:

            conversation_id = create_conversation(
                document_id=request.document_id,
                title=question[:100]
            )

        # STEP 3: Load previous messages.
        conversation_history = get_recent_messages(
            conversation_id=conversation_id,
            limit=10
        )

        # STEP 4: Save the student's question.
        save_message(
            conversation_id=conversation_id,
            role="user",
            content=question
        )

        # STEP 5: Execute conversational RAG.
        result = await answer_document_question(
            document_id=request.document_id,
            question=question,
            top_k=request.top_k,
            conversation_history=conversation_history
        )

        # STEP 6: Save the assistant's response.
        assistant_message = save_message(
            conversation_id=conversation_id,
            role="assistant",
            content=result["answer"],
            sources=result["sources"]
        )

        # STEP 7: Return the final response.
        return {
            "success": True,
            "message": "Conversational RAG response generated successfully.",
            "document_id": request.document_id,
            "conversation_id": conversation_id,
            "question": question,
            "answer": result["answer"],
            "sources": result["sources"],
            "retrieved_chunks": result["retrieved_chunks"],
            "retrieval_query": result["retrieval_query"],
            "assistant_message_id": assistant_message["id"]
        }

    except HTTPException:
        raise

    except ValueError as error:

        raise HTTPException(
            status_code=422,
            detail=str(error)
        )

    except Exception:

        logger.exception(
            "Conversational RAG request failed."
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to process the chat request."
        )


@router.get("/conversations")
async def get_document_conversations(
    document_id: str = Query(...)
):
    """
    List all conversations for a document.
    """

    if not re.fullmatch(
        r"[a-f0-9]{32}",
        document_id
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID."
        )

    conversations = list_conversations(
        document_id=document_id
    )

    return {
        "success": True,
        "document_id": document_id,
        "total_conversations": len(conversations),
        "conversations": conversations
    }


@router.get("/conversations/{conversation_id}")
async def get_chat_history(conversation_id: str):
    """
    Retrieve a conversation and its complete history.
    """

    if not re.fullmatch(
        r"[a-f0-9]{32}",
        conversation_id
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid conversation ID."
        )

    conversation = get_conversation(
        conversation_id
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    messages = get_conversation_messages(
        conversation_id
    )

    return {
        "success": True,
        "conversation": conversation,
        "total_messages": len(messages),
        "messages": messages
    }


@router.delete("/conversations/{conversation_id}")
async def remove_conversation(conversation_id: str):
    """
    Delete a conversation and all associated messages.
    """

    if not re.fullmatch(
        r"[a-f0-9]{32}",
        conversation_id
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid conversation ID."
        )

    deleted = delete_conversation(
        conversation_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    return {
        "success": True,
        "message": "Conversation deleted successfully.",
        "conversation_id": conversation_id
    }
