"""Vector Store Class."""

import json
import os
from enum import Enum
from typing import Optional

from intai.ml.vector_db import VectorEmbeddingDocument, VectorEmbeddingResponse
from intai.ml.chroma_store import ChromaDbCollection
from intai.ml.ai_prompt import JobApplicationAIPrompt, JobPostingAIPrompt
from intai.ml.chroma_store import ChromaDbCollection
from intai.utils.util import WorkType, is_valid_json
from loguru import logger
from sentence_transformers import SentenceTransformer

from .openai_client import OpenAIClient, LLMModelType


class EmbeddingModelType(Enum):
    """Embedding Model Type."""

    INVALID = 0
    SENTENCE_TRANSFORMER = 1


class ReferenceInfoModelType(Enum):
    """Reference Model Type (JobApplication or JobPosting)."""

    JOB_POSTING = 1
    JOB_APPLICATION = 2


class VectorReferenceInfoModel:
    """
    Reference the Information from db in Embedding Store.

    This is  used to back reference information in our database
    from embeddings store.
    """

    def __init__(
        self,
        company_id: int,
        job_posting_id: int,
        reference_type: ReferenceInfoModelType,
        job_application_id: Optional[int] = None,
        filtering_criteria: Optional[str] = None,
    ):
        """Construct the Chroma API Model."""
        if company_id is None:
            raise Exception("Invalid Company id passed")

        self.company_id = company_id
        self.job_application_id = job_application_id or 0
        self.job_posting_id = job_posting_id or 0
        self.filtering_criteria = filtering_criteria or ""
        self.reference_type = reference_type
        logger.debug(f"referenceinfomodel: {reference_type}")

    def __repr__(self):
        return f"ReferenceType: {self.reference_type.name}: {self.company_id}, {self.job_application_id}, {self.job_posting_id}, {self.filtering_criteria}"


class VectorStoreDriver:
    """Use Vector Store (Chroma DB) for finding the embeddings and searching."""

    COLLECTION_JOB_APPLICATION = "JobApplication"
    COLLECTION_JOB_POSTING = "JobPosting"

    def __init__(
        self,
        work_type: WorkType,
        reference_info: VectorReferenceInfoModel,
        model: EmbeddingModelType = EmbeddingModelType.SENTENCE_TRANSFORMER,
    ):
        """Construct the ChromaDriver."""
        if work_type == WorkType.JOBAPPLICATION:
            self.collection_name = VectorStoreDriver.COLLECTION_JOB_APPLICATION
        elif work_type == WorkType.JOBPOSTING:
            self.collection_name = VectorStoreDriver.COLLECTION_JOB_POSTING
        else:
            raise Exception("Invalid WorkType passed: f{work_type}")

        self.vector_store = ChromaDbCollection(self.collection_name)

        self.work_type = work_type
        self._set_embedding_model(model)
        self.reference_info = reference_info
        logger.debug(f"Reference Info:{self.reference_info}\n")
        self.use_vector_db = os.getenv("use_vector_db") == "True"

    def _get_model_from_type(self, model: EmbeddingModelType):
        """Get the model from the model type."""
        if model == EmbeddingModelType.SENTENCE_TRANSFORMER:
            # TODO: move the model names and other config to config file.
            return SentenceTransformer("all-MiniLM-L6-v2")
        else:
            raise Exception(
                f"Unsupported model type passed for EmbeddingModelType. model:{model}"
            )

    def _set_embedding_model(self, model: EmbeddingModelType):
        """Set the model for this instance."""
        self.embedding_model = self._get_model_from_type(model)

    def _get_text_embeddings(self, texts):
        """Get embeddings based on our embedding models."""
        # if models == 'SentenceTransformer':
        return self.embedding_model.encode(texts).tolist()

    def query_collection(self, text) -> VectorEmbeddingResponse:
        """Query the collection of this instance in VectorStore for text.

        There are two modes:
        1: VectorDB Mode: Tries to get the embeddings from the local store
        2: Always go Downstream mode: In this mode it will always call
           downstream service for embeddings (OpenAI etc.)
        NOTE: This method can return None.
        """
        embedding_result: VectorEmbeddingResponse = None
        logger.trace(f"Collection Queried vector_db_use: {self.use_vector_db}")
        if self.use_vector_db:
            # logger.debug(f"Collection Queried: {self.collection}")
            input_embeddings = self._get_text_embeddings([text])
            assert len(input_embeddings) > 0
            embedding_result = self.vector_store.query_collection(input_embeddings[0])
            logger.debug(f"embedding_result: {embedding_result}")

        return embedding_result

    def add_to_collection(self, text, gpt_response, embedding_data):
        """Add to embeddings store the response in reference info format."""

        logger.info(f"add-to-collection: {self.reference_info}")
        vectorEmbeddingInput = VectorEmbeddingDocument(
            entity=gpt_response, embedding=embedding_data, document=text
        )

        logger.debug(f"vectorEmbeddingDoc: {vectorEmbeddingInput}")
        self.vector_store.add_to_collection(vectorEmbeddingInput)

    def create_new_embedding_record(
        self, text: str, openai_prompt: str, openai_model: LLMModelType = None
    ):
        """Create a new embedding and stores in the Vector Store.

        This allows subsequent calls for the same job application/job posting to be
        retrieved from vector store."""
        try:
            openai_client = OpenAIClient(openai_model)

            if self.work_type == WorkType.JOBAPPLICATION:
                prompt = JobApplicationAIPrompt(ja_text=text)
                gpt_response = openai_client.get_model_response(prompt)
            elif self.work_type == WorkType.JOBPOSTING:
                prompt = JobPostingAIPrompt(jp_text=text)
                gpt_response = openai_client.get_model_response(prompt)
            else:
                raise Exception(f"Unexpected work type for embedding {self.work_type}")

            # logger.debug(f"Length without trimming is {len(gpt_response)}")
            # Can throw Json decode exception
            gpt_response_dict = json.loads(gpt_response)
            gpt_response = json.dumps(
                gpt_response_dict
            )  # Trim the json by dumping from dict.
            # logger.debug(f"Length after trimming is {len(gpt_response)}")

            embedding_data = self._get_text_embeddings(text)
            if self.use_vector_db:
                if is_valid_json(gpt_response):
                    self.add_to_collection(text, gpt_response, embedding_data)
                    # logger.debug(f"{self.work_type} added to collection")
                    return gpt_response
                else:
                    logger.error("Invalid GPT response, not adding to vector DB.")
                    return None

            else:
                return gpt_response
        except Exception as err:
            logger.error(str(err))
            raise err

    def get_embeddings(self, text, openai_prompt=None, openai_model=None):
        """
        High-level method to fetch the embeddings.

        It will look in the cache and returned existing embeddings or
        will fetch a new one from downstream model (like OpenAI) and cache.

        FIX: Do we need to pass openai_model here?
        """
        logger.debug(
            "model in chromadb_ans (If None uses default model): ", openai_model
        )
        try:
            embedding_result = self.query_collection(text)
            if embedding_result:
                distance = embedding_result.distance

                logger.debug(f"Distance: {distance}")

                if distance is not None and distance <= 0.01:
                    logger.trace(f"{embedding_result.entity}")
                    return embedding_result.entity

            logger.debug("EmbeddingResult none or distance not in threshold")
            # if embedding result is none or distance is none or distance is > 0.01
            return self.create_new_embedding_record(text, openai_prompt, openai_model)
        except Exception as err:
            logger.error(
                f"Exception while getting embeddings: {err}\n JobPosting: {self}"
            )
            raise err
