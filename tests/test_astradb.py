from dotenv import load_dotenv
import os
import pytest
import json
from intai.ml.astradb import AstraDbCollection
from intai.ml.vector_db import VectorEmbeddingDocument, VectorEmbeddingResponse
from icecream import ic


class TestAstraDbCollection:
    @classmethod
    def test_get_embeddings_job_posting(cls):
        load_dotenv()
        extracted_text = "test the west"
        entity = "west is the test"
        astradb = AstraDbCollection("testcol", 4)
        assert astradb.collection

        text_embedding = [
            -0.08616924285888672,
            0.038357339799404144,
            -0.045690566301345825,
            0.044376011937856674,
        ]
        embedding_doc = VectorEmbeddingDocument(
            embedding=text_embedding, entity=entity, document=extracted_text
        )

        astradb.add_to_collection(embedding_doc)
        search_embedding = [
            -0.04916924285888671,
            0.038357339799404044,
            -0.045690566301345865,
            0.044376011937858674,
        ]
        actual_embedding_result = astradb.query_collection(search_embedding)
        ic(actual_embedding_result)
        assert actual_embedding_result.entity == entity
        assert actual_embedding_result.document == extracted_text
