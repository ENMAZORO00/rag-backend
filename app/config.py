import os
from dotenv import load_dotenv

load_dotenv()

# 🔥 OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL")

# 🔥 Milvus
MILVUS_URI = os.getenv("MILVUS_URI")
MILVUS_TOKEN = os.getenv("MILVUS_TOKEN")

# 🔥 Embedding dimension
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", 1536))
