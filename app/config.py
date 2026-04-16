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
MILVUS_COLLECTION_NAME = os.getenv("MILVUS_COLLECTION_NAME", "rag_collection_v2")

# 🔥 Embedding dimension
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", 1536))

# 🔥 MongoDB + media storage
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "rag_app")
MONGO_MEDIA_COLLECTION = os.getenv("MONGO_MEDIA_COLLECTION", "media_transcripts")
MONGO_USERS_COLLECTION = os.getenv("MONGO_USERS_COLLECTION", "users")
MEDIA_STORAGE_DIR = os.getenv("MEDIA_STORAGE_DIR", "uploaded_media")

# 🔥 Auth
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-env")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
)
