# RAG Backend (FastAPI)

Quick start guide for running the backend locally, required environment variables, and how to interact with the API.

## Requirements

- Python 3.8+
- A running Milvus instance (self-hosted or managed) or change `MILVUS_URI` to point to your deployment
- OpenAI account / API key (or any compatible LLM provider if you adapt the code)

## Setup

1. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root (same folder as this README).

### Recommended `.env` variables

Put the following values in your `.env` file. Variables shown with examples — replace them with your real values.

```
# OpenAI settings
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small   # example: text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini                   # example chat model

# Milvus connection (host:port or a connection string your Milvus deployment expects)
MILVUS_URI=127.0.0.1:19530
MILVUS_TOKEN=                                 # leave blank if not required

# Optional: embedding vector dimension (defaults to 1536)
EMBEDDING_DIM=1536
```

Notes:

- `OPENAI_API_KEY` is required. The embedding and chat model names should match available models for your account.
- `MILVUS_URI` must point to a reachable Milvus server. If you run Milvus locally, default port is commonly `19530`.
- `MILVUS_TOKEN` may be required if your Milvus deployment uses authentication.

## Running the backend

Start the FastAPI server (development mode):

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

This exposes the API at `http://localhost:8000`.

The frontend included in this workspace expects the backend CORS origin `http://localhost:5173`.

## API Endpoints

- `POST /upload` — accepts a file upload (PDF, DOCX, PPTX, XLSX, or plain text). Returns a JSON with `document_id` after ingestion.

Example using `curl` (file upload):

```bash
curl -F "file=@./some-document.pdf" http://localhost:8000/upload
```

- `POST /ask` — accepts JSON body `{ "query": "your question" }`. Returns `{ "answer": "..." }`.

Example using `curl`:

```bash
curl -X POST -H "Content-Type: application/json" \
	-d '{"query":"What is the summary of the document?"}' \
	http://localhost:8000/ask
```

## Notes & Troubleshooting

- If embeddings fail or dimensions don't match, confirm `EMBEDDING_DIM` matches the model's output dimension.
- If you cannot connect to Milvus, verify `MILVUS_URI` and network reachability. Check Milvus logs for authentication or port issues.
- Ensure `OPENAI_API_KEY` has sufficient quota/permissions for the chosen models.

## Development tips

- The backend uses `python-dotenv` to load `.env` automatically.
- To change CORS allowed origins, edit `app/main.py` middleware configuration.

---

If you'd like, I can also add a matching README for the frontend with commands to run the Vite app.
