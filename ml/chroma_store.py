"""This implements the VectorStore interface for local chromadb"""

from loguru import logger
import chromadb

from intai.ml.vector_db import (
    VectorDbCollectionInterface,
    VectorEmbeddingDocument,
    VectorEmbeddingResponse,
)


class ChromaDbCollection(VectorDbCollectionInterface):
    """ChromaDb implementation of the VectorDbCollectionInterface"""

    PATH_CHROMA_DB = "chroma_idx"

    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=ChromaDbCollection.PATH_CHROMA_DB)

        # TODO: move the algo names and other config to config file.
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name, metadata={"hnsw:space": "cosine"}
        )

    def query_collection(self, query_embedding: list[float]) -> VectorEmbeddingResponse:
        """Query the collection with query text embedding. This will return the distance and documents."""

        logger.info(f"len of query_embeddings: {len(query_embedding)}")
        num_results = 1

        query_result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=num_results,
            include=["embeddings", "metadatas", "documents", "distances"],
        )

        logger.debug(
            f"Query ressult from chromadb: {query_result} \nlen-metadatas: {len(query_result['metadatas'][0])}"
        )
        embedding_result = None

        if len(query_result["metadatas"][0]) >= 1:
            embedding_result = VectorEmbeddingResponse(
                entity=query_result["metadatas"][0][0]["entity"],
                distance=query_result["distances"][0][0],
                document=query_result["documents"][0][0],
            )
            logger.info(f"Embedding_Result: {embedding_result}")
        else:
            logger.warning(f"Else block : {query_result}")

        return embedding_result

    def add_to_collection(self, vector_embedding_doc: VectorEmbeddingDocument):
        """Generate an id and add the embedding data, metadata and document(s) to the collection."""

        logger.info(f"vector_embedding_doc: {vector_embedding_doc}")
        metadatas = [
            {
                "entity": vector_embedding_doc.entity,
            }
        ]
        logger.info(f"metadatas: {metadatas}")

        self.collection.add(
            ids=[str(self.collection.count())],
            embeddings=vector_embedding_doc.embedding,
            metadatas=metadatas,
            documents=[vector_embedding_doc.document],
        )
