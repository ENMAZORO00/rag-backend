from fastapi import FastAPI, UploadFile, File
from app.ingestion import index_document
from app.retrieval import retrieve
from app.llm import generate_answer
from app.utils.parsers import *
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

class AskRequest(BaseModel):
    query: str





app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload")
async def upload(file: UploadFile = File(...)):

    content = await file.read()

    if file.filename.endswith(".pdf"):
        text = parse_pdf(content)
    elif file.filename.endswith(".docx"):
        text = parse_docx(content)
    elif file.filename.endswith(".pptx"):
        text = parse_pptx(content)
    elif file.filename.endswith(".xlsx"):
        text = parse_excel(content)
    else:
        text = content.decode()

    doc_id = index_document(text)

    return {"document_id": doc_id}


@app.post("/ask")
async def ask(request: AskRequest):

    print("Incoming Query:", request.query)

    chunks = retrieve(request.query)
    print("Chunks Found:", len(chunks))

    answer = generate_answer(request.query, chunks)
    print("Generated Answer:", answer)

    return {"answer": answer}

