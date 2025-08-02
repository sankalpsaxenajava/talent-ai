"""This implements the VectorStore interface for AstraDb vector store"""

from loguru import logger
from astrapy.db import AstraDB

from intai.ml.vector_db import (
    VectorDbCollectionInterface,
    VectorEmbeddingDocument,
    VectorEmbeddingResponse,
)

ASTRA_DB_API_ENDPOINT = (
    "https://c0b58714-2c59-47db-b9ae-5ae05e4df504-us-east1.apps.astra.datastax.com"
)
ASTRA_DB_APPLICATION_TOKEN = "AstraCS:ZbiKZrzPREywJYZJMmcrwljR:4435dbfb80c47a300a29e1285cf08310c62f22da7b13eea11d764cb7fd5dc08b"


class AstraDbCollection(VectorDbCollectionInterface):
    """ChromaDb implementation of the VectorDbCollectionInterface"""

    def __init__(self, collection_name: str, dimension: int = 405):
        self.collection_name = collection_name
        self.astradb = AstraDB(
            api_endpoint=ASTRA_DB_API_ENDPOINT,
            token=ASTRA_DB_APPLICATION_TOKEN,
        )

        self.collection = None
        # TODO: move the algo names and other config to config file.
        # self.collection = self.astradb.collection(collection_name=self.collection_name)
        # logger.info(self.collection)
        if not self.collection:
            self.collection = self.astradb.create_collection(
                collection_name=self.collection_name, dimension=dimension
            )
            logger.info(f"Created collection: {self.collection}")

    def query_collection(self, query_embedding: list[float]) -> VectorEmbeddingResponse:
        """Query the collection with query text embedding. This will return the distance and documents."""

        logger.info(f"len of query_embeddings: {len(query_embedding)}")
        num_results = 1

        query_result = self.collection.vector_find(
            vector=query_embedding,
            limit=num_results,
            fields=["entity", "document"],
        )
        embedding_result = None

        logger.debug(f"Query ressult from chromadb: {query_result}.")

        if len(query_result) >= 1:
            distance = 1.0 - query_result[0]["$similarity"]
            embedding_result = VectorEmbeddingResponse(
                entity=query_result[0]["entity"],
                distance=distance,
                document=query_result[0]["document"],
            )
            logger.info(f"Embedding_Result: {embedding_result}")
        else:
            logger.warning(f"Else block : {query_result}")

        return embedding_result

    def add_to_collection(self, vector_embedding_doc: VectorEmbeddingDocument):
        """Add the embedding data, metadata and document(s) to the collection."""

        logger.info(f"vector_embedding_doc: {vector_embedding_doc}")
        astra_docs = [
            {
                "entity": vector_embedding_doc.entity,
                "$vector": vector_embedding_doc.embedding,
                "document": vector_embedding_doc.document,
            }
        ]
        logger.info(f"Adding astra_docs to astradb now: {astra_docs}")
        self.collection.insert_many(astra_docs)
        logger.info(f"[{len(astra_docs)}]")
