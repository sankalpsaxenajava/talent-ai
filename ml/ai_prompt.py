"""Encapsulates the prompt messages based on worktype."""

from intai.ml.prompts.find_screening_score_prompt import get_find_screening_score_prompt
from intai.ml.prompts.jd_prompt import prompt_jd_without_example
from intai.ml.prompts.resume_prompt import get_resume_prompt
from intai.ml.prompts.factor_analysis_prompt import get_factor_analysis_prompt
from intai.ml.prompts.match_title_prompt import (
    get_title_match_system_prompt,
    get_title_match_user_prompt,
)
from intai.ml.prompts.ja_matching_summary_prompt import (
    get_ja_matching_summary_system_prompt,
)
from intai.ml.prompts.chatbot_prompt import (
    get_chatbot_system_prompt,
    get_chatbot_user_prompts,
)
from intai.ml.prompts.jobs_chatbot_prompt import (
    get_jobs_chatbot_system_prompt,
    get_jobs_chatbot_user_prompts,
    get_jobs_response_schema,
)
from intai.ml.prompts.qa_chatbot_prompt import (
    get_qa_chatbot_system_prompt,
    get_qa_chatbot_user_prompts,
    get_qa_response_schema,
)

from intai.ml.prompts.ja_basics_prompt import (
    get_ja_basics_system_prompt,
    get_ja_basics_user_prompts,
    get_ja_basics_response_schema
)
from intai.ml.prompts.generate_questions_prompt import get_generate_questions_prompt
from intai.ml.prompts.format_transcript_prompt import get_format_transcript_system_prompt, get_format_transcript_user_prompts
from loguru import logger


class AIPrompt:
    """Provides a base class for prompts"""

    def __init__(self, prompt_messages: list[dict[str, str]], resp_schema: str = None):
        self._messages = prompt_messages
        self._response_schema = resp_schema
        logger.debug(f"{self.__class__} Prompt Messages: {self._messages}")

    @property
    def messages(self):
        return self._messages
    
    @property 
    def response_schema(self):
        return self._response_schema


class JobApplicationAIPrompt(AIPrompt):
    """Provides prompt for Job Application"""

    def __init__(self, ja_text: str):
        prompt_resume = get_resume_prompt(ja_text=ja_text)
        prompt_messages = [
            {"role": "system", "content": prompt_resume},
        ]
        super().__init__(prompt_messages=prompt_messages)


class JobPostingAIPrompt(AIPrompt):
    """Provide the prompt message for Job Posting."""

    def __init__(self, jp_text: str):
        prompt_messages = [
            {"role": "system", "content": prompt_jd_without_example},
            {
                "role": "user",
                "content": f"Job Description: '''{jp_text}'''\n\nJSON:",
            },
        ]
        super().__init__(prompt_messages=prompt_messages)


class FactorAnalysisAIPrompt(AIPrompt):
    """Provide the prompt message for Factor Analysis."""

    def __init__(self, jp_text: str, ja_text: str):
        system_prompt = get_factor_analysis_prompt(jp_text, ja_text)
        logger.trace(system_prompt)
        prompt_messages = [
            {"role": "system", "content": system_prompt},
        ]
        super().__init__(prompt_messages=prompt_messages)


class JobApplicationMatchSummaryAIPrompt(AIPrompt):
    """Provide the prompt message for JobApplication Matching summary."""

    def __init__(self, jp_text: str, ja_text: str):
        system_prompt = get_ja_matching_summary_system_prompt(jp_text, ja_text)
        logger.trace(system_prompt)
        prompt_messages = [
            {"role": "system", "content": system_prompt},
        ]
        super().__init__(prompt_messages=prompt_messages)


class MatchTitleAIPrompt(AIPrompt):
    """Provide the prompt message for Matching Titles."""

    def __init__(self, jp_title: str, ja_titles: str):
        """Initializes the Match Title AI Prompt.

        jp:title is title in job description.
        ja_titles is titles mentioned in the resume.
        """
        system_prompt = get_title_match_system_prompt()
        user_prompt = get_title_match_user_prompt(jp_title, ja_titles)
        logger.trace(system_prompt)
        prompt_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        super().__init__(prompt_messages=prompt_messages)


class ChatbotAIPrompt(AIPrompt):
    """Provide the prompt message for Conversational Bot (Whatsapp/Single Job)."""

    def __init__(
        self, context: dict[str, str], history: list[dict[str, str]], user_query: str
    ):
        """Initializes the Match Title AI Prompt.

        jp:title is title in job description.
        ja_titles is titles mentioned in the resume.
        """
        system_prompt = get_chatbot_system_prompt(context)
        user_prompts = get_chatbot_user_prompts(history, user_query)
        logger.trace(system_prompt)
        prompt_messages = []
        prompt_messages.append(system_prompt)
        for prompt in user_prompts:
            prompt_messages.append(prompt)

        super().__init__(prompt_messages=prompt_messages)


class JobsChatbotAIPrompt(AIPrompt):
    """Provide the prompt message for Conversational Jobs chatBot."""

    def __init__(
        self, context: dict[str, str], history: list[dict[str, str]], user_query: str
    ):
        """Initializes the Jobs Chatbot AI Prompt.

        jp:title is title in job description.
        ja_titles is titles mentioned in the resume.
        """
        system_prompt = get_jobs_chatbot_system_prompt(context)
        user_prompts = get_jobs_chatbot_user_prompts(history, user_query)
        response_schema = get_jobs_response_schema()
        logger.trace(system_prompt)
        logger.debug(f"Response Schema: {response_schema}")
        prompt_messages = []
        prompt_messages.append(system_prompt)
        for prompt in user_prompts:
            prompt_messages.append(prompt)

        super().__init__(prompt_messages=prompt_messages, resp_schema= response_schema)


class QAChatbotAIPrompt(AIPrompt):
    """Provide the prompt message for Conversational Jobs chatBot."""

    def __init__(
        self, context: dict[str, str], history: list[dict[str, str]], user_query: str
    ):
        """Initializes the Match Title AI Prompt.

        jp:title is title in job description.
        ja_titles is titles mentioned in the resume.
        """
        system_prompt = get_qa_chatbot_system_prompt(context)
        user_prompts = get_qa_chatbot_user_prompts(history, user_query)
        response_schema = get_qa_response_schema()
        logger.trace(system_prompt)
        logger.debug(f"Response Schema: {response_schema}")
        prompt_messages = []
        prompt_messages.append(system_prompt)
        for prompt in user_prompts:
            prompt_messages.append(prompt)

        super().__init__(prompt_messages=prompt_messages, resp_schema= response_schema)

class GenerateScreeningQuestionsAIPrompt(AIPrompt):
    """Provide the prompt message for Generationg of screening questions."""

    def __init__(self, jp_text: str, ja_text: str, screening_focus_area: str):
        system_prompt = get_generate_questions_prompt(jp_text, ja_text, screening_focus_area)
        logger.info(system_prompt)
        prompt_messages = [
            {"role": "system", "content": system_prompt},
        ]
        super().__init__(prompt_messages=prompt_messages)

class FindScreeningScoreAIPrompt(AIPrompt):
    """Provide the prompt message for Find screening score."""

    def __init__(self, jp_text: str, ja_text: str, transcript: str, screening_focus_area: str):
        system_prompt = get_find_screening_score_prompt(jp_text, ja_text, transcript, screening_focus_area)
        logger.info(system_prompt)
        prompt_messages = [
            {"role": "system", "content": system_prompt},
        ]
        super().__init__(prompt_messages=prompt_messages)

class FormatTranscriptAIPrompt(AIPrompt):
    """Provide the prompt message for Formatting of transcript."""

    def __init__(self, transcript: str):
        system_prompt = get_format_transcript_system_prompt()
        logger.info(system_prompt)
        prompt_messages = [
            {"role": "system", "content": system_prompt},
        ]
        user_prompts = get_format_transcript_user_prompts(transcript=transcript)
        for prompt in user_prompts:
            prompt_messages.append(prompt)
        super().__init__(prompt_messages=prompt_messages)

class JobApplicationBasicsAIPrompt(AIPrompt):
    """Provide the prompt message for JA Basics chatBot."""

    def __init__(
        self, ja_text: str
    ):
        """Initializes the Match Title AI Prompt.

        jp:title is title in job description.
        ja_titles is titles mentioned in the resume.
        """
        system_prompt = get_ja_basics_system_prompt()
        user_prompts = get_ja_basics_user_prompts(ja_text=ja_text)
        response_schema = get_ja_basics_response_schema()
        logger.trace(system_prompt)
        logger.debug(f"JA Response Schema: {response_schema}")
        prompt_messages = []
        prompt_messages.append(system_prompt)
        for prompt in user_prompts:
            prompt_messages.append(prompt)

        super().__init__(prompt_messages=prompt_messages, resp_schema=response_schema)