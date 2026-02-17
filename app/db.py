from pymilvus import (
    connections,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    utility
)
from app.config import MILVUS_URI, MILVUS_TOKEN, EMBEDDING_DIM

# Connect once at startup
connections.connect(
    alias="default",
    uri=MILVUS_URI,
    token=MILVUS_TOKEN
)

COLLECTION_NAME = "rag_collection"


def get_collection():
    """
    Returns Milvus collection.
    Creates collection + index if not exists.
    """

    # Create collection if it does not exist
    if not utility.has_collection(COLLECTION_NAME):

        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True
            ),
            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=EMBEDDING_DIM
            ),
            FieldSchema(
                name="text",
                dtype=DataType.VARCHAR,
                max_length=5000
            ),
            FieldSchema(
                name="document_id",
                dtype=DataType.VARCHAR,
                max_length=200
            )
        ]

        schema = CollectionSchema(fields)

        collection = Collection(
            name=COLLECTION_NAME,
            schema=schema
        )

        # ✅ Create index with COSINE (for OpenAI embeddings)
        collection.create_index(
            field_name="embedding",
            index_params={
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
        )

    else:
        collection = Collection(COLLECTION_NAME)

    return collection
