
import logging
import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.evaluation_service import (
    run_rag_evaluation
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/evaluation",
    tags=["RAG Evaluation"]
)


class EvaluationRequest(BaseModel):

    document_id: str = Field(
        ...,
        min_length=32,
        max_length=32
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=10
    )


@router.post("/run")
async def run_evaluation(request: EvaluationRequest):
    """
    Run the RAG evaluation dataset against
    the selected uploaded document.
    """

    if not re.fullmatch(
        r"[a-f0-9]{32}",
        request.document_id
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID."
        )

    try:

        report = await run_rag_evaluation(
            document_id=request.document_id,
            top_k=request.top_k
        )

        return report

    except FileNotFoundError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except ValueError as error:

        raise HTTPException(
            status_code=422,
            detail=str(error)
        )

    except Exception:

        logger.exception(
            "RAG evaluation endpoint failed."
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to complete RAG evaluation."
        )
