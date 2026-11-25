
from fastapi import FastAPI #We import FastAPI so that we can create our backend application.

app = FastAPI(
    title="RAG Knowledge Assistant",
    description="AI assistant that answers questions from uploaded documents",
    version="1.0.0"
)


@app.get("/") #This creates a GET endpoint.
def home():
    return {
        "message": "Welcome to RAG Knowledge Assistant",
        "status": "Running"
    }


@app.get("/health") #This endpoint checks whether our backend is running.This is called a health-check endpoint.
def health_check():
    return {
        "status": "healthy",
        "application": "RAG Knowledge Assistant"
    }
