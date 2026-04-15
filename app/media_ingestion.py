import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI
from pymongo.errors import PyMongoError

from app.config import OPENAI_API_KEY, MEDIA_STORAGE_DIR
from app.db import get_collection
from app.embedding import get_embedding
from app.mongo import get_media_collection

client = OpenAI(api_key=OPENAI_API_KEY)
logger = logging.getLogger(__name__)


def _safe_filename(filename: str) -> str:
    return filename.replace("/", "_").replace("\\", "_")


def _chunk_transcript_segments(segments, max_chars: int = 900):
    chunked = []
    current_parts = []
    current_start = None
    current_end = None
    part_counter = 0

    for segment in segments:
        text = (segment.get("text") or "").strip()
        if not text:
            continue
        seg_start = float(segment.get("start", 0.0))
        seg_end = float(segment.get("end", seg_start))

        if current_start is None:
            current_start = seg_start

        candidate = " ".join(current_parts + [text]).strip()
        if current_parts and len(candidate) > max_chars:
            chunk_text = " ".join(current_parts).strip()
            chunked.append({
                "segment_id": f"seg_{part_counter}",
                "start_sec": current_start,
                "end_sec": current_end if current_end is not None else current_start,
                "text": chunk_text
            })
            part_counter += 1
            current_parts = [text]
            current_start = seg_start
            current_end = seg_end
            continue

        current_parts.append(text)
        current_end = seg_end

    if current_parts:
        chunked.append({
            "segment_id": f"seg_{part_counter}",
            "start_sec": current_start if current_start is not None else 0.0,
            "end_sec": current_end if current_end is not None else 0.0,
            "text": " ".join(current_parts).strip()
        })

    return chunked


def process_media_upload(content: bytes, filename: str, content_type: str):
    media_id = str(uuid.uuid4())
    media_dir = Path(MEDIA_STORAGE_DIR)
    media_dir.mkdir(parents=True, exist_ok=True)

    stored_name = f"{media_id}_{_safe_filename(filename)}"
    stored_path = media_dir / stored_name
    stored_path.write_bytes(content)

    with stored_path.open("rb") as media_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=media_file,
            response_format="verbose_json",
            timestamp_granularities=["segment"]
        )

    segments_raw = getattr(transcription, "segments", None) or []
    if segments_raw and not isinstance(segments_raw[0], dict):
        segments_raw = [seg.model_dump() for seg in segments_raw]

    chunked_segments = _chunk_transcript_segments(segments_raw)
    full_text = " ".join([seg["text"] for seg in chunked_segments]).strip()
    duration_sec = float(chunked_segments[-1]["end_sec"]) if chunked_segments else 0.0

    media_collection = get_media_collection()
    media_doc = {
        "media_id": media_id,
        "filename": filename,
        "stored_path": str(stored_path),
        "media_url": f"/media/{stored_name}",
        "media_type": content_type or "application/octet-stream",
        "duration_sec": duration_sec,
        "segments": chunked_segments,
        "created_at": datetime.now(timezone.utc),
        "transcript_text": full_text
    }
    metadata_persisted = True
    warning = None
    try:
        media_collection.insert_one(media_doc)
    except PyMongoError as exc:
        # Keep upload/transcription usable even if metadata DB is temporarily misconfigured.
        logger.exception("Failed to persist media metadata in MongoDB: %s", exc)
        metadata_persisted = False
        warning = "Media uploaded, but metadata store is unavailable."

    if chunked_segments:
        collection = get_collection()
        chunk_texts = [segment["text"] for segment in chunked_segments]
        embeddings = [get_embedding(chunk) for chunk in chunk_texts]
        collection.insert([
            embeddings,
            chunk_texts,
            [media_id] * len(chunked_segments),
            ["media"] * len(chunked_segments),
            [media_id] * len(chunked_segments),
            [segment["segment_id"] for segment in chunked_segments],
            [float(segment["start_sec"]) for segment in chunked_segments],
            [float(segment["end_sec"]) for segment in chunked_segments],
            [content_type or "application/octet-stream"] * len(chunked_segments)
        ])
        collection.load()

    summary_text = (
        f"Media transcribed and indexed successfully.\n\nTranscript:\n{full_text[:1200]}"
        if full_text
        else "Media transcribed and indexed successfully, but transcript was empty."
    )

    response = {
        "document_id": media_id,
        "summary": summary_text,
        "media_id": media_id,
        "media_url": media_doc["media_url"],
        "transcript_preview": full_text[:400],
        "metadata_persisted": metadata_persisted
    }
    if warning:
        response["warning"] = warning

    return response
