from openai import OpenAI
from app.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def _build_context(context_chunks: list):
    texts = []
    seen_media_ids = set()
    for chunk in context_chunks:
        if isinstance(chunk, dict):
            chunk_text = (chunk.get("text") or "").strip()
            if chunk_text:
                texts.append(chunk_text)
            media_id = (chunk.get("media_id") or "").strip()
            transcript_text = (chunk.get("transcript_text") or "").strip()
            if media_id and transcript_text and media_id not in seen_media_ids:
                seen_media_ids.add(media_id)
                texts.append(transcript_text)
        elif isinstance(chunk, str):
            chunk_text = chunk.strip()
            if chunk_text:
                texts.append(chunk_text)
    return "\n\n".join(texts)


def generate_answer(query: str, context_chunks: list):

    if not context_chunks:
        return "No relevant information found."

    context = _build_context(context_chunks)

    prompt = f"""
You are an AI assistant.
Answer the question using only the context below.

Context:
{context}

Question:
{query}

Answer:
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content


def stream_answer(query: str, context_chunks: list):
    if not context_chunks:
        yield "No relevant information found."
        return

    context = _build_context(context_chunks)
    prompt = f"""
You are an AI assistant.
Answer the question using only the context below.

Context:
{context}

Question:
{query}

Answer:
"""

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )
    for event in stream:
        delta = event.choices[0].delta.content if event.choices else None
        if delta:
            yield delta
