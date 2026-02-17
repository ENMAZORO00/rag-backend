from openai import OpenAI
from app.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_answer(query: str, context_chunks: list):

    if not context_chunks:
        return "No relevant information found."

    context = "\n\n".join(context_chunks)

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
