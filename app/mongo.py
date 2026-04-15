from pymongo import MongoClient
from app.config import MONGODB_URI, MONGODB_DB_NAME, MONGO_MEDIA_COLLECTION

_mongo_client = MongoClient(MONGODB_URI)
_db = _mongo_client[MONGODB_DB_NAME]


def get_media_collection():
    return _db[MONGO_MEDIA_COLLECTION]
