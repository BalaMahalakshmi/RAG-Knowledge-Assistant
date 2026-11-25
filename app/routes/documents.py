import json
import uuid

from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
import re

from app.services.chunking_service import create_chunks
from app.services.pdf_service import extract_pdf_text
from app.services.embeddings_service import (
    generate_embeddings,
    generate_query_embedding,
)

from app.services.qdrant_service import store_embeddings, search_similar_chunks
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=3, ge=1, le=10)


# Project root / uploads directory
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Maximum upload size: 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    # 1. Validate filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    # 2. Validate file extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    # 3. Read uploaded file
    pdf_bytes = await file.read(MAX_FILE_SIZE + 1)

    # 4. Validate file size
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(pdf_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File size must not exceed 10 MB.")

    # 5. Validate PDF signature
    if not pdf_bytes.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    try:

        # 6. Extract PDF text
        extraction_result = extract_pdf_text(pdf_bytes)

        # 7. Generate unique document ID
        document_id = uuid.uuid4().hex

        # Never use the original filename as the storage path
        pdf_path = UPLOAD_DIR / f"{document_id}.pdf"
        json_path = UPLOAD_DIR / f"{document_id}.json"

        # 8. Save original PDF
        pdf_path.write_bytes(pdf_bytes)

        # 9. Prepare extracted text data
        document_data = {
            "document_id": document_id,
            "original_filename": file.filename,
            "total_pages": extraction_result["total_pages"],
            "total_characters": extraction_result["total_characters"],
            "pages": extraction_result["pages"],
        }

        # 10. Save extracted text and page information
        json_path.write_text(
            json.dumps(document_data, ensure_ascii=False, indent=4), encoding="utf-8"
        )

        # 11. Return upload result
        return {
            "success": True,
            "message": "PDF uploaded and text extracted successfully.",
            "document_id": document_id,
            "filename": file.filename,
            "total_pages": extraction_result["total_pages"],
            "total_characters": extraction_result["total_characters"],
            "pages": [
                {
                    "page_number": page["page_number"],
                    "character_count": page["character_count"],
                    "preview": page["text"][:500],
                }
                for page in extraction_result["pages"]
            ],
        }

    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))

    except OSError:
        raise HTTPException(
            status_code=500, detail="Unable to save the uploaded document."
        )

    finally:
        await file.close()


@router.post("/{document_id}/chunk")
async def chunk_uploaded_document(document_id: str):

    # 1. Validate document ID
    if not re.fullmatch(r"[a-f0-9]{32}", document_id):
        raise HTTPException(status_code=400, detail="Invalid document ID.")

    # 2. Find extracted JSON file
    json_path = UPLOAD_DIR / f"{document_id}.json"

    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Uploaded document not found.")

    try:

        # 3. Read extracted document data
        document_data = json.loads(json_path.read_text(encoding="utf-8"))

        # 4. Generate chunks
        chunks = create_chunks(
            document_data["pages"], chunk_size=1000, chunk_overlap=200
        )

        if not chunks:
            raise HTTPException(
                status_code=422, detail="No text available for chunking."
            )

        # 5. Save chunked output
        chunk_path = UPLOAD_DIR / f"{document_id}_chunks.json"

        chunk_data = {
            "document_id": document_id,
            "original_filename": document_data["original_filename"],
            "total_pages": document_data["total_pages"],
            "total_chunks": len(chunks),
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "chunks": chunks,
        }

        chunk_path.write_text(
            json.dumps(chunk_data, ensure_ascii=False, indent=4), encoding="utf-8"
        )

        # 6. Return chunking results
        return {
            "success": True,
            "message": "Document chunking completed successfully.",
            "document_id": document_id,
            "total_chunks": len(chunks),
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "chunks": [
                {
                    "chunk_id": chunk["chunk_id"],
                    "page_number": chunk["page_number"],
                    "character_count": chunk["character_count"],
                    "preview": chunk["text"][:200],
                }
                for chunk in chunks
            ],
        }

    except HTTPException:
        raise

    except (KeyError, json.JSONDecodeError):
        raise HTTPException(status_code=422, detail="Invalid extracted document data.")

    except OSError:
        raise HTTPException(status_code=500, detail="Unable to save chunked document.")


@router.post("/{document_id}/embed")
async def embed_uploaded_document(document_id: str):

    # 1. Validate document ID
    if not re.fullmatch(r"[a-f0-9]{32}", document_id):
        raise HTTPException(status_code=400, detail="Invalid document ID.")

    # 2. Locate chunked JSON
    chunk_path = UPLOAD_DIR / f"{document_id}_chunks.json"

    if not chunk_path.exists():
        raise HTTPException(
            status_code=404, detail="Chunked document not found. Run chunking first."
        )

    try:

        # 3. Read chunked document
        chunk_data = json.loads(chunk_path.read_text(encoding="utf-8"))

        chunks = chunk_data["chunks"]

        if not chunks:
            raise HTTPException(
                status_code=422, detail="No chunks available for embedding."
            )

        # 4. Generate embeddings
        embedded_chunks = generate_embeddings(chunks)

        # 5. Prepare embedding output
        embedding_data = {
            "document_id": document_id,
            "original_filename": chunk_data["original_filename"],
            "total_chunks": len(embedded_chunks),
            "embedding_model": ("sentence-transformers/all-MiniLM-L6-v2"),
            "embedding_dimension": 384,
            "distance_metric": "Cosine",
            "chunks": embedded_chunks,
        }

        # 6. Save embedding JSON
        embedding_path = UPLOAD_DIR / f"{document_id}_embeddings.json"

        embedding_path.write_text(
            json.dumps(embedding_data, ensure_ascii=False, indent=4), encoding="utf-8"
        )

        # 7. Return summary, not the entire vectors
        return {
            "success": True,
            "message": "Embeddings generated successfully.",
            "document_id": document_id,
            "total_chunks": len(embedded_chunks),
            "embedding_model": ("sentence-transformers/all-MiniLM-L6-v2"),
            "embedding_dimension": 384,
            "total_vectors": len(embedded_chunks),
            "sample_embedding": (embedded_chunks[0]["embedding"][:10]),
            "embedding_file": str(embedding_path.name),
        }

    except HTTPException:
        raise

    except (KeyError, json.JSONDecodeError):
        raise HTTPException(status_code=422, detail="Invalid chunked document data.")

    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    except OSError:
        raise HTTPException(status_code=500, detail="Unable to save embedding data.")


@router.post("/{document_id}/store")
async def store_document_embeddings(document_id: str):

    # Validate document ID
    if not re.fullmatch(r"[a-f0-9]{32}", document_id):
        raise HTTPException(status_code=400, detail="Invalid document ID.")

    # Locate embedding JSON
    embedding_path = UPLOAD_DIR / f"{document_id}_embeddings.json"

    if not embedding_path.exists():
        raise HTTPException(
            status_code=404, detail="Embeddings not found. Generate embeddings first."
        )

    try:

        # Read embedding JSON
        embedding_data = json.loads(embedding_path.read_text(encoding="utf-8"))

        # Verify dimensions of every vector
        chunks = embedding_data.get("chunks", [])

        if not chunks:
            raise HTTPException(status_code=422, detail="No embedding vectors found.")

        invalid_chunks = [
            chunk.get("chunk_id", "unknown")
            for chunk in chunks
            if len(chunk.get("embedding", [])) != 384
        ]

        if invalid_chunks:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Invalid embedding dimensions.",
                    "invalid_chunks": invalid_chunks,
                },
            )

        # Store vectors in Qdrant
        result = store_embeddings(
            embedded_chunks=chunks,
            document_id=document_id,
            original_filename=embedding_data["original_filename"],
        )

        return {
            "success": True,
            "message": "Embeddings stored in Qdrant successfully.",
            "document_id": document_id,
            "filename": embedding_data["original_filename"],
            "total_chunks": len(chunks),
            "stored_vectors": result["total_vectors_stored"],
            "collection_name": result["collection_name"],
            "vector_dimension": 384,
            "distance_metric": "Cosine",
            **result,
        }

    except HTTPException:
        raise

    except (json.JSONDecodeError, KeyError):
        raise HTTPException(status_code=422, detail="Invalid embedding JSON structure.")

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception:
        raise HTTPException(
            status_code=500, detail="Failed to store embeddings in Qdrant."
        )


@router.post("/{document_id}/search")
async def search_document(document_id: str, request: SearchRequest):
    """
    Search for relevant chunks inside an uploaded document.
    """

    # 1. Validate document ID
    if not re.fullmatch(r"[a-f0-9]{32}", document_id):
        raise HTTPException(status_code=400, detail="Invalid document ID.")

    # 2. Validate question
    if not request.query.strip():
        raise HTTPException(status_code=422, detail="Search query cannot be empty.")

    try:

        # 3. Convert question into an embedding
        query_vector = generate_query_embedding(request.query)

        # 4. Search relevant chunks in Qdrant
        results = search_similar_chunks(
            query_vector=query_vector, document_id=document_id, top_k=request.top_k
        )

        # 5. Return search results
        return {
            "success": True,
            "message": "Semantic search completed successfully.",
            "document_id": document_id,
            "query": request.query,
            "total_results": len(results),
            "results": results,
        }

    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))

    except Exception:
        logger.exception("Semantic search failed")

    raise HTTPException(status_code=500, detail="Failed to perform semantic search.")
