from .test_db import BaseTestJobPostingDb
from dotenv import load_dotenv
import os
from intai.ml.vector_store import (
    VectorStoreDriver,
    ReferenceInfoModelType,
    VectorReferenceInfoModel,
)
from intai.utils.util import WorkType
from intai.utils.file_utils import get_bytes_from_file, extract_text
import pytest
import json


class TestVectorStore(BaseTestJobPostingDb):
    @classmethod
    # @pytest.mark.skip(reason="no way of currently testing this")
    def test_get_embeddings_job_posting(cls):
        load_dotenv()
        doc_path = f"{os.getenv('TEST_DATA_FOLDER')}/jp.docx"
        bytes_data, docType = get_bytes_from_file(doc_path)
        extracted_text = extract_text(bytes_data, docType)
        assert len(extracted_text) > 0
        assert "Finance" in extracted_text

        # Only test open ai code if explicitly enabled
        if os.getenv("TEST_OPENAI_CODE"):
            reference_info = VectorReferenceInfoModel(
                cls.valid_job_posting_db.company_id,
                cls.valid_job_posting_db.id,
                ReferenceInfoModelType.JOB_POSTING,
                None,
                filtering_criteria=cls.valid_job_posting_db.filtering_criteria,
            )
            vector_store = VectorStoreDriver(WorkType.JOBPOSTING, reference_info)
            extracted_entities = vector_store.get_embeddings(extracted_text)

            print(f"Response from VectorStore:\n {extracted_entities}\n ")
            assert len(extracted_entities) > 0

    @classmethod
    def test_vectorstore_add_collection(cls):
        """Test the vector store add collection"""

        load_dotenv()
        embedding_file_path = f"{os.getenv('TEST_DATA_FOLDER')}/embeddings_data.bin"
        # load the embeddings from the file

        embeddings_file = open(embedding_file_path, "r")
        embeddings_str = embeddings_file.read()
        in_embeddings = [float(i) for i in embeddings_str.split(",")]

        json_path = f"{os.getenv('TEST_DATA_FOLDER')}/sample_oai.json"
        f = open(json_path)
        gpt_response = json.load(f)
        print(gpt_response)

        doc_path = f"{os.getenv('TEST_DATA_FOLDER')}/jp.docx"
        bytes_data, docType = get_bytes_from_file(doc_path)
        extracted_text = extract_text(bytes_data, docType)
        assert len(extracted_text) > 0
        assert "Finance" in extracted_text

        reference_info = VectorReferenceInfoModel(
            cls.valid_job_posting_db.company_id,
            cls.valid_job_posting_db.id,
            ReferenceInfoModelType.JOB_POSTING,
            1,
            filtering_criteria=cls.valid_job_posting_db.filtering_criteria,
        )
        print(reference_info)
        print(reference_info.job_application_id)
        vector_store = VectorStoreDriver(WorkType.JOBPOSTING, reference_info)
        vector_store.add_to_collection(extracted_text, gpt_response, in_embeddings)

        embedding_result = vector_store.query_collection(extracted_text)
        assert embedding_result
        distance = embedding_result.distance

        print(f"Distance: {distance}")
        assert distance is not None

        extracted_entities = embedding_result.entity

        print(f"Response from VectorStore:\n {extracted_entities}")
        assert len(extracted_entities) > 0
