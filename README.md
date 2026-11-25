# 🧠 RAG Knowledge Assistant

An intelligent document-based AI assistant powered by **Retrieval-Augmented Generation (RAG)** that enables users to upload PDF documents and ask questions based on their content.

The system retrieves relevant information from uploaded documents using semantic search and generates context-aware responses using Large Language Models (LLMs), along with source citations.

## 🚀 Project Overview

The RAG Knowledge Assistant bridges the gap between traditional document search and Generative AI.

Instead of relying entirely on an LLM's pre-trained knowledge, this application retrieves relevant information from user-provided documents and uses that context to generate accurate and relevant answers.

## ✨ Key Features

- **PDF Upload:** Upload PDF documents as a knowledge source.
- **Text Extraction:** Extract meaningful text from uploaded PDF files.
- **Document Chunking:** Split extracted text into smaller, manageable chunks.
- **Text Embeddings:** Convert document chunks into numerical vector representations.
- **Vector Storage:** Store and manage embeddings using Qdrant.
- **Semantic Search:** Retrieve relevant document chunks based on user queries.
- **AI-Powered Responses:** Generate context-aware answers using an LLM.
- **Source Citations:** Provide references to retrieved document content.
- **REST API:** Expose backend functionality through FastAPI.

## 🏗️ System Architecture

```text
              User
                |
                v
          PDF Upload
                |
                v
         Text Extraction
                |
                v
         Document Chunking
                |
                v
          Embeddings
                |
                v
        Qdrant Vector DB
                |
                |
          User Question
                |
                v
          Query Embedding
                |
                v
          Semantic Search
                |
                v
       Relevant Document Chunks
                |
                v
          LLM Processing
                |
                v
       Context-Aware Answer
                |
                v
         Source Citations
```

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Backend Framework | FastAPI |
| Document Processing | PyMuPDF |
| Embeddings | Sentence Transformers |
| Vector Database | Qdrant |
| AI / LLM | Large Language Models |
| API Testing | Postman |
| Version Control | Git & GitHub |

## 📂 Project Workflow

1. Upload a PDF document.
2. Extract text from the document.
3. Split the extracted text into smaller chunks.
4. Generate embeddings for each chunk.
5. Store embeddings in the Qdrant vector database.
6. Accept a question from the user.
7. Convert the question into an embedding.
8. Perform semantic similarity search.
9. Retrieve the most relevant document chunks.
10. Pass the retrieved context and question to the LLM.
11. Generate an answer with relevant source citations.

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.10+
- Git
- Qdrant instance (local or cloud)
- LLM API credentials, if using a hosted model

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/RAG-Knowledge-Assistant.git
```

```bash
cd RAG-Knowledge-Assistant
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it:

**Windows:**
```bash
venv\Scripts\activate
```

**Linux / macOS:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root and configure the required credentials and service settings.

Example:

```env
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
LLM_API_KEY=your_llm_api_key
```

Use the actual variable names expected by your application.

### 5. Run the Application

```bash
uvicorn main:app --reload
```

Replace `main:app` with your actual FastAPI application entry point if different.

Access the API documentation:

```text
http://127.0.0.1:8000/docs
```

## 🎯 Learning Objectives

- Understand Retrieval-Augmented Generation architecture.
- Implement document ingestion and preprocessing.
- Work with text embeddings and vector databases.
- Understand semantic similarity search.
- Integrate LLMs with retrieved document context.
- Build AI-powered REST APIs using FastAPI.
- Implement source-grounded responses and citations.

## 🔮 Future Enhancements

- Support multiple document formats.
- Implement conversational memory.
- Add multi-document knowledge retrieval.
- Improve retrieval using hybrid search.
- Implement reranking for better retrieval accuracy.
- Build an interactive frontend.
- Add authentication and user-specific document collections.

## 👨‍💻 Author

**Bala Mahalakshmi Srinivasan**

Artificial Intelligence & Data Science Engineer

GitHub: [YOUR_GITHUB_PROFILE](https://github.com/YOUR_USERNAME)

LinkedIn: [YOUR_LINKEDIN_PROFILE](https://www.linkedin.com/)

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.