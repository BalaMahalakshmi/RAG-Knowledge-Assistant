from fastapi import FastAPI

from app.routes.documents import router as documents_router

app = FastAPI(
    title="RAG Knowledge Assistant",
    description="AI assistant that answers questions from uploaded documents",
    version="1.0.0",
)


@app.get("/")
def home():
    return {"message": "Welcome to RAG Knowledge Assistant", "status": "Running"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "application": "RAG Knowledge Assistant"}


# Register document routes
app.include_router(documents_router)
