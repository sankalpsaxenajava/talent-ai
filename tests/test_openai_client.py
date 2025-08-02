from .test_db import BaseTestJobPostingDb
from dotenv import load_dotenv
import os
from intai.ml.llm_client import LLMClient, LLMModelType, LLMResponseType
from intai.ml.ai_prompt import (
    AIPrompt,
    JobApplicationAIPrompt,
    JobApplicationMatchSummaryAIPrompt,
    JobPostingAIPrompt,
    FactorAnalysisAIPrompt,
    MatchTitleAIPrompt,
)
from intai.utils.util import WorkType
from intai.utils.file_utils import get_bytes_from_file, extract_text
from intai.ml.embedding_utils import find_cluster_center_skills
import pytest
from icecream import ic


class TestLLMClient(BaseTestJobPostingDb):
    # @pytest.mark.skip(reason="disable openai calls test")
    @classmethod
    def test_aimodel_job_posting(cls):
        load_dotenv()
        from pathlib import Path

        input_jp_path = Path(os.getenv("TEST_DATA_FOLDER"), "jp.docx")
        assert input_jp_path.exists()
        # TODO Get the file from test config.
        bytes_data, docType = get_bytes_from_file(str(input_jp_path))
        extracted_text = extract_text(bytes_data, docType)
        ic(extracted_text)
        assert len(extracted_text) > 0
        assert "Finance" in extracted_text

        # Only test open ai code if explicitly enabled
        if os.getenv("TEST_OPENAI_CODE"):
            ai_client = LLMClient()
            prompt = JobPostingAIPrompt(jp_text=extracted_text)
            response = ai_client.get_model_response(prompt)
            ic(f"Response from OpenAI:\n {response}")
            assert len(response) > 0

    @classmethod
    def test_aimodel_job_application(cls):
        load_dotenv()
        from pathlib import Path

        input_ja_path = Path(os.getenv("TEST_DATA_FOLDER"), "ja.pdf")
        assert input_ja_path.exists()
        # TODO Get the file from test config.
        bytes_data, docType = get_bytes_from_file(str(input_ja_path))
        ic(docType)
        extracted_text = extract_text(bytes_data, docType)
        ic(extracted_text)
        assert len(extracted_text) > 0
        assert "HANA" in extracted_text

        # Only test open ai code if explicitly enabled
        if os.getenv("TEST_OPENAI_CODE"):
            ai_client = LLMClient()
            prompt = JobApplicationAIPrompt(ja_text=extracted_text)
            response = ai_client.get_model_response(prompt, response_type=LLMResponseType.JSON_OBJECT)
            ic(f"Response from OpenAI:\n {response}")
            assert len(response) > 0

    @classmethod
    def test_aimodel_factor_analysis(cls):
        load_dotenv()
        from pathlib import Path

        input_ja_path = Path(os.getenv("TEST_DATA_FOLDER"), "ja.pdf")
        input_jp_path = Path(os.getenv("TEST_DATA_FOLDER"), "jp.docx")
        assert input_ja_path.exists()
        assert input_jp_path.exists()
        # TODO Get the file from test config.
        bytes_data_ja, docType_ja = get_bytes_from_file(str(input_ja_path))
        ic(docType_ja)
        extracted_text_ja = extract_text(bytes_data_ja, docType_ja, True)
        ic(extracted_text_ja)
        assert len(extracted_text_ja) > 0
        assert "HANA" in extracted_text_ja

        # TODO Get the jp file from test config.
        bytes_data_jp, docType_jp = get_bytes_from_file(str(input_jp_path))
        ic(docType_jp)
        extracted_text_jp = extract_text(bytes_data_jp, docType_jp, True)
        ic(extracted_text_jp)
        assert len(extracted_text_jp) > 0
        assert "Finance" in extracted_text_jp

        # Only test open ai code if explicitly enabled
        if os.getenv("TEST_OPENAI_CODE"):
            ai_client = LLMClient()
            prompt = FactorAnalysisAIPrompt(
                jp_text=extracted_text_jp, ja_text=extracted_text_ja
            )
            response = ai_client.get_model_response(prompt)
            ic(f"Response from OpenAI:\n {response}")
            assert len(response) > 0
            import json

            data = json.loads(response)
            ic(data["final_score_explanation"])
            ic(data["calculations"])
            ic(data["final_score"])
            assert float(data["final_score"]) > 0.0

    def test_aimodel_matching_summary_analysis(cls):
        load_dotenv()
        from pathlib import Path

        input_ja_path = Path(os.getenv("TEST_DATA_FOLDER"), "ja.pdf")
        input_jp_path = Path(os.getenv("TEST_DATA_FOLDER"), "jp.docx")
        assert input_ja_path.exists()
        assert input_jp_path.exists()
        # TODO Get the file from test config.
        bytes_data_ja, docType_ja = get_bytes_from_file(str(input_ja_path))
        ic(docType_ja)
        extracted_text_ja = extract_text(bytes_data_ja, docType_ja, True)
        ic(extracted_text_ja)
        assert len(extracted_text_ja) > 0
        assert "HANA" in extracted_text_ja

        # TODO Get the jp file from test config.
        bytes_data_jp, docType_jp = get_bytes_from_file(str(input_jp_path))
        ic(docType_jp)
        extracted_text_jp = extract_text(bytes_data_jp, docType_jp, True)
        ic(extracted_text_jp)
        assert len(extracted_text_jp) > 0
        assert "Finance" in extracted_text_jp

        # Only test open ai code if explicitly enabled
        if os.getenv("TEST_OPENAI_CODE"):
            ai_client = LLMClient()
            prompt = JobApplicationMatchSummaryAIPrompt(
                jp_text=extracted_text_jp, ja_text=extracted_text_ja
            )
            response = ai_client.get_model_response(prompt)
            ic(f"Response from OpenAI:\n {response}")
            assert len(response) > 0
            import json

            data = json.loads(response)
            ic(data["summary"])

    @classmethod
    def test_get_factor_json(cls):
        """Just test the json repsonse for factors. Probably can be deleted."""
        load_dotenv()
        from pathlib import Path

        response_path = Path(os.getenv("TEST_RESPONSE_FOLDER"), "factor_analysis.json")
        import json

        with open(response_path, "r") as f:
            response = json.load(f)
            ic(response)
            ic(response["explanations"])
            ic(response["calculations"])
            ic(response["final_score"])

    @classmethod
    def test_get_embeddings(cls):
        load_dotenv()
        text = "Software engineering Java Python Ruby Ocaml"
        if os.getenv("TEST_OPENAI_CODE"):
            open_ai_client = LLMClient(model=LLMModelType.EMBEDDING_ADA)
            embeddings_array = open_ai_client.get_embeddings(text)
            assert embeddings_array.size > 0
            ic(embeddings_array)
            ic(embeddings_array.size)

    @pytest.mark.skip(
        reason="Not applicable and cluster embeddings and skills don't match"
    )
    @classmethod
    def test_find_cluster_center_skill(cls):
        load_dotenv()
        text = "Software engineering, Developer, python, medicine, Finance Analyst "
        if os.getenv("TEST_OPENAI_CODE"):
            open_ai_client = LLMClient(model=LLMModelType.EMBEDDING_ADA)
            prompt = JobApplicationAIPrompt(text)
            embeddings_array = open_ai_client.get_embeddings(text)
            assert embeddings_array.size > 0
            ic(embeddings_array)
            ic(embeddings_array.size)
            skills = ["Sofware Engg.", "Programmer", "Finance Manager"]
            cluster_skills = find_cluster_center_skills(skills, open_ai_client)
            cluster_skill = cluster_skills[0]
            cluster_skill_same = cluster_skills[1]
            cluster_skill_diff = cluster_skills[2]
            ic(cluster_skill, cluster_skill_same, cluster_skill_diff)
            assert cluster_skill == cluster_skill_same
            assert cluster_skill != cluster_skill_diff

    @classmethod
    def test_aimodel_match_title(cls):
        # Only test open ai code if explicitly enabled
        if os.getenv("TEST_OPENAI_CODE"):
            prompt = MatchTitleAIPrompt(
                jp_title="Software Engineering Manager",
                ja_titles="SDM, Software Engineer",
            )
            ai_client = LLMClient()
            response = ai_client.get_model_response(prompt)
            ic(f"Response from OpenAI:\n {response}\n ")
            assert len(response) > 0
            import json

            resp = json.loads(response)
            assert resp["result"]
