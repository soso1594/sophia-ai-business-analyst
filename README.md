# Sophia: AI Business Analyst

Sophia is a local AI assistant designed to analyze business documents and answer questions using a Retrieval-Augmented Generation (RAG) pipeline.

## Features

- PDF document upload
- Semantic search with ChromaDB
- Page-aware document chunking
- Local LLM with Ollama
- Conversational memory
- Source pages for retrieved information
- Streamlit interface
- Multilingual responses

## Architecture

PDF
→ Text extraction
→ Chunking
→ ChromaDB
→ Semantic retrieval
→ Sophia (Llama 3.2)
→ Answer + sources

## Tech stack

- Python
- Streamlit
- ChromaDB
- Ollama
- Llama 3.2
- PyPDF

## Run locally

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
