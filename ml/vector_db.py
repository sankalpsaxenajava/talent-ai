"""Interface for vector db storage."""

from chromadb.api.types import Metadatas


class VectorEmbeddingDocument:
    """Vector Embedding Document"""

    def __init__(self, embedding, entity, document):
        """Constructor for VectorEmbeddingDocument.

        Embedding: Embeddings for content,
        Entity: reference entity like a GPT JSON response for resume/jd,
        Document: Actual incoming text document.
        """
        self.embedding = embedding
        self.entity = entity
        self.document = document

    def __repr__(self):
        return f"<embedding: {self.embedding}; \n entity: {self.entity}; \ndocument: {self.document}>"


class VectorEmbeddingResponse:
    """Vector Embedding Response"""

    def __init__(self, document, entity, distance):
        self.document = document
        self.distance = distance
        self.entity = entity

    def __repr__(self):
        return f"<distance: {self.distance}; \n entity: {self.entity};\n document: {self.document}>"


class VectorDbCollectionInterface:
    """Vector DB Collection interface describing the vector db implementations."""

    def __init__(self, collection_name: str):
        self.collection_name = collection_name

    def query_collection(self, query_text: str) -> VectorEmbeddingResponse:
        """Query the collection with query text. This will return the distance and documents."""

        pass

    def add_to_collection(self, vector_embedding_docs: list[VectorEmbeddingDocument]):
        """Generate an id and add the embedding data, metadata and document(s) to the collection."""
        pass
