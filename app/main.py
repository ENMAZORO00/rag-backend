from fastapi import FastAPI, UploadFile, File
from app.ingestion import index_document
from app.retrieval import retrieve
from app.llm import generate_answer
from app.utils.parsers import *
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.llm import generate_answer  # already exists

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

    # ✅ generate summary
    summary = summarize_text(text)

    return {
        "document_id": doc_id,
        "summary": summary
    }


@app.post("/ask")
async def ask(request: AskRequest):

    print("Incoming Query:", request.query)

    chunks = retrieve(request.query)
    print("Chunks Found:", len(chunks))

    answer = generate_answer(request.query, chunks)
    print("Generated Answer:", answer)

    return {"answer": answer}

