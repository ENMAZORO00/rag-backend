import certifi
from pymongo import ASCENDING, MongoClient
from app.config import (
    MONGODB_URI,
    MONGODB_DB_NAME,
    MONGO_MEDIA_COLLECTION,
    MONGO_USERS_COLLECTION,
)

_mongo_options = {}
if MONGODB_URI.startswith("mongodb+srv://") or "tls=true" in MONGODB_URI.lower():
    _mongo_options["tlsCAFile"] = certifi.where()

_mongo_client = MongoClient(MONGODB_URI, **_mongo_options)
_db = _mongo_client[MONGODB_DB_NAME]


def get_media_collection():
    return _db[MONGO_MEDIA_COLLECTION]


def get_users_collection():
    collection = _db[MONGO_USERS_COLLECTION]
    collection.create_index([("email", ASCENDING)], unique=True)
    return collection
