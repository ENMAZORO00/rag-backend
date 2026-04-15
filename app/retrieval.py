from app.db import get_collection
from app.embedding import get_embedding
from app.mongo import get_media_collection


def retrieve(query: str, top_k: int = 5):
    results = retrieve_with_sources(query, top_k=top_k)
    return [item["text"] for item in results]


def retrieve_with_sources(query: str, top_k: int = 5):
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
        output_fields=[
            "text",
            "document_id",
            "source_type",
            "media_id",
            "segment_id",
            "start_sec",
            "end_sec",
            "media_type"
        ]
    )

    chunks = []
    media_collection = get_media_collection()

    for hit in results[0]:
        text = hit.entity.get("text")
        if not text:
            continue

        source_type = hit.entity.get("source_type") or "document"
        media_id = hit.entity.get("media_id") or ""
        start_sec = float(hit.entity.get("start_sec") or 0.0)
        end_sec = float(hit.entity.get("end_sec") or 0.0)
        source = {
            "source_type": source_type,
            "document_id": hit.entity.get("document_id"),
            "media_id": media_id,
            "segment_id": hit.entity.get("segment_id"),
            "start_sec": start_sec,
            "end_sec": end_sec,
            "media_type": hit.entity.get("media_type"),
            "text": text
        }

        if source_type == "media" and media_id:
            media_doc = media_collection.find_one(
                {"media_id": media_id},
                {"_id": 0, "media_url": 1, "filename": 1, "media_type": 1, "transcript_text": 1}
            )
            if media_doc:
                source["media_url"] = media_doc.get("media_url")
                source["filename"] = media_doc.get("filename")
                source["media_type"] = media_doc.get("media_type") or source["media_type"]
                source["transcript_text"] = media_doc.get("transcript_text") or ""

        chunks.append(source)

    return chunks
