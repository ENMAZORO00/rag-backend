from app.embedding import get_embedding
from app.db import get_collection
import uuid

def chunk_text(text, size=800, overlap=100):
    chunks = []
    for i in range(0, len(text), size - overlap):
        chunks.append(text[i:i+size])
    return chunks


def index_document(text: str):
    collection = get_collection()
    document_id = str(uuid.uuid4())

    chunks = chunk_text(text)
    embeddings = [get_embedding(chunk) for chunk in chunks]

    # Insert data
    collection.insert([
        embeddings,                     # vector field
        chunks,                         # text field
        [document_id] * len(chunks)     # metadata field
    ])

    # Create index only if not already created
    if not collection.indexes:
        collection.create_index(
            field_name="embedding",  # must match your schema exactly
            index_params={
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
        )

    # Load collection for searching
    collection.load()

    return document_id
