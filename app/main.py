from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.documents import router as documents_router
from app.routes.chat import router as chat_router
from app.routes.evaluation import router as evaluation_router
from app.services.conversation_service import (
    initialize_conversation_database

)

app = FastAPI(
    title="RAG Knowledge Assistant",
    description="AI assistant that answers questions from uploaded documents",
    version="1.0.0",
)

initialize_conversation_database()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Welcome to RAG Knowledge Assistant", "status": "Running"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "application": "RAG Knowledge Assistant"}


# Register document routes
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(evaluation_router)