from intai.ml.llm_client import LLMClient
from intai.ml.utils.llm_types import LLMResponseType
from intai.ml.ai_prompt import FindScreeningScoreAIPrompt, GenerateScreeningQuestionsAIPrompt, FormatTranscriptAIPrompt
import json
from loguru import logger
from intai.models.models import (
    JobApplicationDb,
    JobPostingDb,
    SessionLocal)


# Function to generate screening questions using openai_client given job description and resume
def generate_screening_questions(client_job_application_id: int, client_job_id: int,company_id: int, screening_focus_area: str):
    """
    Generate screening questions using openai_client.

    Args:
        job_description (str): The job description provided by the user.
        resume (str): The resume of the candidate."""
    ja_text = ""
    jp_text = ""
    with SessionLocal() as session:
        # get the extracted text for job description and job application based on ja_id
        job_application_db = JobApplicationDb.get_job_application(session=session, company_id=company_id, client_job_application_id=client_job_application_id)
        job_posting_db = JobPostingDb.get_job_posting(session=session, company_id=company_id, client_job_id=client_job_id)
        ja_text = job_application_db.extracted_text
        jp_text = job_posting_db.extracted_text
    prompt = GenerateScreeningQuestionsAIPrompt(jp_text=jp_text, ja_text=ja_text, screening_focus_area=screening_focus_area)
    ai_client = LLMClient(session_id=client_job_application_id, client_id=company_id)
    response = ai_client.get_model_response(prompt, response_type = LLMResponseType.JSON_OBJECT)
    logger.debug(f"Response from OpenAI:\n {response}")
    data = json.loads(response)
    logger.debug(f"Questions: {data['questions']}")
    return response


# Function to generate screening questions using openai_client given job description and resume
def find_screening_score(client_job_application_id: int, client_job_id: int,company_id: int, transcript: str, screening_focus_area: str):
    """
    Find the screening score using openai_client.

    Args:
        job_description (str): The job description provided by the user.
        resume (str): The resume of the candidate."""
    ja_text = ""
    jp_text = ""
    with SessionLocal() as session:
        # get the extracted text for job description and job application based on ja_id
        job_application_db = JobApplicationDb.get_job_application(session=session, company_id=company_id, client_job_application_id=client_job_application_id)
        job_posting_db = JobPostingDb.get_job_posting(session=session, company_id=company_id, client_job_id=client_job_id)
        ja_text = job_application_db.extracted_text
        jp_text = job_posting_db.extracted_text
    prompt = FindScreeningScoreAIPrompt(jp_text=jp_text, ja_text=ja_text, transcript=transcript, screening_focus_area=screening_focus_area)
    ai_client = LLMClient(session_id=client_job_application_id, client_id=company_id)
    response = ai_client.get_model_response(prompt, response_type = LLMResponseType.JSON_OBJECT)
    logger.debug(f"Response from OpenAI for score is:\n {response}")
    data = json.loads(response)
    logger.debug(f"Score: {data}")
    return response

def format_transcript(transcript: str, session_id, client_id):
    """
    Format the transcript using openai_client.

    Args:
        transcript (str): The transcript of the interview."""
    prompt = FormatTranscriptAIPrompt(transcript=transcript)
    ai_client = LLMClient(session_id=session_id, client_id=client_id)
    response = ai_client.get_model_response(prompt, response_type = LLMResponseType.TEXT)
    logger.debug(f"Response from OpenAI for formatted transcript is:\n {response}")
    # Remove whitespace from start of response
    response = response.lstrip()

    # Remove ```markdown if it's the first line
    if response.startswith("```markdown"):
        logger.warning("Removing markdown line from transcript response.")
        response = response[len("```markdown"):].lstrip()
    return response