from app.embedding import get_embedding
from app.db import get_collection
import uuid


def chunk_text(text, size=800, overlap=100):
    chunks = []
    for i in range(0, len(text), size - overlap):
        chunks.append(text[i:i + size])
    return chunks


def index_document(text: str):
    collection = get_collection()
    document_id = str(uuid.uuid4())

    chunks = chunk_text(text)
    embeddings = [get_embedding(chunk) for chunk in chunks]

    if not chunks:
        return document_id

    # Insert data in collection field order (except auto-id).
    collection.insert([
        embeddings,
        chunks,
        [document_id] * len(chunks),
        ["document"] * len(chunks),
        [""] * len(chunks),
        [""] * len(chunks),
        [0.0] * len(chunks),
        [0.0] * len(chunks),
        ["text"] * len(chunks)
    ])

    collection.load()

    return document_id
