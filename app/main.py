from pathlib import Path

from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from app.ingestion import index_document
from app.retrieval import retrieve_with_sources
from app.llm import generate_answer, stream_answer
from app.utils.parsers import *
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.config import MEDIA_STORAGE_DIR
from app.media_ingestion import process_media_upload

class AskRequest(BaseModel):
    query: str





app = FastAPI()
Path(MEDIA_STORAGE_DIR).mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_STORAGE_DIR), name="media")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def summarize_text(text: str):
    from openai import OpenAI
    from app.config import OPENAI_API_KEY

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
Summarize the following document in 3-4 short bullet points:

{text[:4000]}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


def _build_sources(chunks):
    sources = []
    seen = set()
    for chunk in chunks:
        if chunk.get("source_type") != "media":
            continue
        media_url = chunk.get("media_url")
        if not media_url:
            continue
        dedupe_key = (
            chunk.get("media_id"),
            float(chunk.get("start_sec") or 0.0),
            float(chunk.get("end_sec") or 0.0),
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        sources.append({
            "media_id": chunk.get("media_id"),
            "media_url": media_url,
            "start_sec": float(chunk.get("start_sec") or 0.0),
            "end_sec": float(chunk.get("end_sec") or 0.0),
            "media_type": chunk.get("media_type") or "application/octet-stream",
            "filename": chunk.get("filename") or "media"
        })
    return sources


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    filename = file.filename or "upload.txt"
    extension = filename.lower().split(".")[-1]
    media_extensions = {"mp3", "wav", "m4a", "webm", "mp4", "mov", "mkv", "mpeg", "mpga"}

    if extension in media_extensions or (file.content_type or "").startswith(("audio/", "video/")):
        return process_media_upload(content, filename, file.content_type or "")

    if filename.endswith(".pdf"):
        text = parse_pdf(content)
    elif filename.endswith(".docx"):
        text = parse_docx(content)
    elif filename.endswith(".pptx"):
        text = parse_pptx(content)
    elif filename.endswith(".xlsx"):
        text = parse_excel(content)
    else:
        text = content.decode()

    doc_id = index_document(text)

    # ✅ generate summary
    summary = summarize_text(text)

    return {
        "document_id": doc_id,
        "summary": summary
    }


@app.post("/ask")
async def ask(request: AskRequest):

    print("Incoming Query:", request.query)

    chunks = retrieve_with_sources(request.query)
    print("Chunks Found:", len(chunks))

    answer = generate_answer(request.query, chunks)
    print("Generated Answer:", answer)

    return {"answer": answer, "sources": _build_sources(chunks)}


@app.websocket("/ws/ask")
async def ask_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            if payload.get("type") != "ask":
                await websocket.send_json({
                    "type": "error",
                    "message": "Unsupported event type."
                })
                continue

            query = (payload.get("query") or "").strip()
            if not query:
                await websocket.send_json({
                    "type": "error",
                    "message": "Query is required."
                })
                continue

            chunks = retrieve_with_sources(query)
            complete_answer = ""
            for token in stream_answer(query, chunks):
                complete_answer += token
                await websocket.send_json({"type": "token", "text": token})

            await websocket.send_json({
                "type": "done",
                "answer": complete_answer,
                "sources": _build_sources(chunks)
            })
    except WebSocketDisconnect:
        return

