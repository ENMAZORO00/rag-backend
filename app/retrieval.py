from app.db import get_collection
from app.embedding import get_embedding


def retrieve(query: str, top_k: int = 5):

    collection = get_collection()
    collection.load()

    embedding = get_embedding(query)

    results = collection.search(
        data=[embedding],
        anns_field="embedding",
        param={
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        },
        limit=top_k,
        output_fields=["text"]
    )

    chunks = []

    for hit in results[0]:
        print(hit.entity)
        text = hit.entity.get("text")
        if text:  # 🔥 prevent None
            chunks.append(text)

    print("Chunks Found:", len(chunks))

    return chunks
