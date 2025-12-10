# Project Description: ChatWithPDF

## Main Idea
**ChatWithPDF** is a multimodal Retrieval-Augmented Generation (RAG) application that enables users to interactively "chat" with their PDF documents. The system allows users to upload a PDF file, processes its content (including text, tables, and images), and provides accurate answers to user queries by leveraging advanced LLMs and vector search technologies. The application is capable of understanding and synthesizing information from diverse data modalities found within standard research papers or technical documents.

## Core Concepts
- **Multimodal Ingestion**: The system doesn't just read text; it partitions the PDF to extract and process text, tables, and images separately.
- **Summarization-Based Indexing**: Instead of indexing raw chunks, the system generates concise summaries for text segments, tables, and images. These summaries are embedded for retrieval, while links to the original content (raw text, HTML tables, base64 images) are stored for context generation.
- **Multi-Vector Retrieval**: Utilizes LangChain's `MultiVectorRetriever` to decouple the documents used for retrieval (summaries) from the documents used for answer generation (original detailed content).
- **Interactive Chat**: A user-friendly chat interface built with Streamlit that maintains conversation history.

## Design Details
### Frontend
- **Framework**: [Streamlit](https://streamlit.io/)
- **Features**:
    - File uploader for PDFs.
    - Chat interface with history.
    - Status indicators for processing stages.
    - Session state management for maintaining chat history and processed data.

### Backend Architecture
1.  **Ingestion Service** (`ChatWithPDFApp.ingest`):
    - **Partitioning**: Splits PDF into raw text, table, and image elements.
    - **Summarization Chains**:
        - **Text & Tables**: Uses **Llama-3.1-8b-instant** (via Groq) to generate concise summaries.
        - **Images**: Uses **GPT-4o-mini** (via OpenAI) to describe visual content (charts, graphs, diagrams).
    - **Vector Storage**: Adds the generated summaries to the vector store and maps them to their original raw content.
    
2.  **Retrieval & Generation (`app/services/rag.py` & `chains.py`)**:
    - Queries are embedded using OpenAI Embeddings.
    - Relevant documents are retrieved based on the similarity of the query to the *summaries*.
    - The *original content* associated with the retrieved summaries is passed to the LLM to generate the final answer.

## Dataset Concept
The "dataset" is dynamic and user-provided. It consists of **unstructured PDF documents** uploaded during the session. The system is optimized for:
- Research papers with mixed content (text + figures).
- Technical reports containing tables and data visualization.

## System Technical Details
- **Language**: Python 3.x
- **Orchestration**: [LangChain](https://www.langchain.com/)
- **LLMs & APIs**:
    - **Text Generation/Summarization**: `ChatGroq` (model: `llama-3.1-8b-instant`).
    - **Vision/Image Description**: `ChatOpenAI` (model: `gpt-4o-mini`).
    - **Embeddings**: `OpenAIEmbeddings`.
- **Vector Database**: 
    - **Engine**: [Chroma](https://www.trychroma.com/).
    - **Retriever**: `MultiVectorRetriever` with `InMemoryStore` for the docstore.
- **PDF Processing**: Likely uses `unstructured` (inferred from usage patterns like `partition_pdf` or similar helpers in `app.utils.pdf`).
- **Configuration**: Environment variables for API keys (`GROQ_API_KEY`, `OPENAI_API_KEY`) managed via `app.core.config`.

## Requirements
- **Environment Variables**:
    - `OPENAI_API_KEY`
    - `GROQ_API_KEY`
- **Python Dependencies**:
    - `streamlit`
    - `langchain`, `langchain-groq`, `langchain-openai`, `langchain-chroma`
    - `unstructured[all-docs]` (or specific PDF processing libs)
    - `pydantic`
    - `poppler-utils` and `tesseract-ocr` (system dependencies for PDF processing).

## Limitations
1.  **Non-Persistent Storage**: The current implementation uses `InMemoryStore` for the document store part of the MultiVectorRetriever. This means that if the application restarts, the mapping between summaries and original content constitutes is lost, requiring re-ingestion.
2.  **Processing Speed**: Extracting and summarizing every image and table can be time-consuming for large documents. The application currently implements explicit `time.sleep(15)` delays to avoid hitting Groq's rate limits.
3.  **API Costs**: Heavy reliance on commercial APIs (OpenAI) and rate-limited free tiers (Groq) limits scalability without paid plans.
4.  **Single Document Focus**: The UI currently focuses on processing one PDF at a time per session (uploading a new one might overwrite the previous context depending on specific logic not fully detailed in the snippets).


## Link to video demo
```txt
https://drive.google.com/file/d/1dNtRiExK0I9XtZa3hBHMZ8TURBLI-4gO/view?usp=sharing
```