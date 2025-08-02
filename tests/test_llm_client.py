import os
import pytest
from unittest.mock import patch, MagicMock
from intai.ml.ai_prompt import AIPrompt, JobPostingAIPrompt
from intai.ml.llm_client import LLMClient, get_llm_client
from dotenv import load_dotenv

from intai.utils.file_utils import extract_text, get_bytes_from_file

@pytest.fixture
def ai_client():
    load_dotenv()
    return LLMClient(client_id="1234")

def test_get_ai_client():
    client = get_llm_client("1234")
    assert isinstance(client, LLMClient)

def test_ai_client_initialization():
    client = LLMClient("1234")
    assert client.api_key == os.environ.get("OPENAI_API_KEY")
    assert client.model_type == LLMClient.DEFAULT_MODEL
    #assert client.langfuse is not None

def test_llm_success(ai_client):
    messages = [{"role": "user", "content": "Write a description about Microsoft and return in JSON format"}]
    prompt = AIPrompt(prompt_messages=messages)
    response = ai_client.get_model_response(ai_prompt=prompt)
    assert response is not None
    print(response)

def test_job_posting(ai_client):
        load_dotenv()
        from pathlib import Path

        input_jp_path = Path(os.getenv("TEST_DATA_FOLDER"), "jp.docx")
        assert input_jp_path.exists()
        # TODO Get the file from test config.
        bytes_data, docType = get_bytes_from_file(str(input_jp_path))
        extracted_text = extract_text(bytes_data, docType)
        print(extracted_text)
        assert len(extracted_text) > 0
        assert "Finance" in extracted_text

        # Only test open ai code if explicitly enabled
        if os.getenv("TEST_OPENAI_CODE"):
            prompt = JobPostingAIPrompt(jp_text=extracted_text)
            response = ai_client.get_model_response(prompt)
            print(f"Response from OpenAI:\n {response}")
            assert len(response) > 0