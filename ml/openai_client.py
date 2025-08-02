import os
from enum import Enum
from openai import OpenAI
from intai.utils.util import WorkType
from intai.ml.ai_prompt import AIPrompt
from intai.ml.prompts.jd_prompt import prompt_jd_without_example
from intai.ml.prompts.resume_prompt import get_resume_prompt
from intai.ml.prompts.factor_analysis_prompt import get_factor_analysis_prompt
from intai.ml.prompts.match_title_prompt import (
    get_title_match_system_prompt,
    get_title_match_user_prompt,
)
from loguru import logger
from icecream import ic
import numpy as np
import timeit
from intai.utils.str_utils import check_str_not_null


class OpenAIModelType(Enum):
    """OpenAIModel types sorted."""

    INVALID = 0
    GPT35 = 1
    GPT40 = 2
    GPT40T = 3
    GPT40S = 4
    GPT40M = 5
    EMBEDDING_ADA = 6

class OpenAIResponseType(Enum):
    "OpenAI response type."
    TEXT = 0
    JSON_OBJECT = 1
    JSON_SCHEMA = 2

class OpenAIClient:
    """OpenAI Client code to call Open AI.

    TODO: Create child classes for job application and job posting and move
    all custom logic there and have this class be just the generic openai
    client.
    """

    MODEL_GPT35 = "gpt-3.5-turbo"
    MODEL_GPT40T = "gpt-4-turbo"
    MODEL_GPT40S = "gpt-4o-2024-08-06"
    MODEL_GPT40 = "gpt-4o"
    MODEL_GPT40M = "gpt-4o-mini"
    MODEL_EMBEDDING_ADA = "text-embedding-ada-002"
    DEFAULT_OPENAI_MODEL = OpenAIModelType.GPT40S

    def __init__(
        self,
        model: OpenAIModelType = None,
    ):
        """Construct for OpenAIClient."""
        raise NotImplementedError("OpenAIClient is not implemented yet.")
    
        logger.debug(f"OPEN API Key: {os.getenv('OPENAI_API_KEY')}")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._set_model(model)

    def _get_model_from_type(self, model: OpenAIModelType):
        """Get the model from the model type."""
        if model == OpenAIModelType.GPT35:
            return OpenAIClient.MODEL_GPT35
        elif model == OpenAIModelType.GPT40:
            return OpenAIClient.MODEL_GPT40
        elif model == OpenAIModelType.GPT40T:
            return OpenAIClient.MODEL_GPT40T
        elif model == OpenAIModelType.GPT40S:
            return OpenAIClient.MODEL_GPT40S
        elif model == OpenAIModelType.GPT40M:
            return OpenAIClient.MODEL_GPT40M
        elif model == OpenAIModelType.EMBEDDING_ADA:
            return OpenAIClient.MODEL_EMBEDDING_ADA
        else:
            raise Exception("Unsupported model type passed to OpenAIDriver.set_model")

    def _set_model(self, model: OpenAIModelType):
        """Set the model for this instance."""
        if model is None:
            model = OpenAIClient.DEFAULT_OPENAI_MODEL
        self.model_name = self._get_model_from_type(model)
        logger.debug(f"Model: {self.model_name}")

    def get_model_response(self, ai_prompt: AIPrompt, response_type: OpenAIResponseType = OpenAIResponseType.JSON_OBJECT, response_json: str = None):
        """Call OpenAI to get the completion for message.

        NOTE: For factor_analysis both the fields are required.
        """
        logger.info(
            f"OpenAI Call Started for model: {self.model_name}; prompt {ai_prompt}; response_type: {response_type} json: {response_json}"
        )
        try:
            tries = 2
            model_name = self.model_name
            is_completed = False
            while tries > 0 and not is_completed:
                logger.debug(f"tries {tries} is_completed: {is_completed}")
                
                start_time = timeit.default_timer()
                if response_type is OpenAIResponseType.JSON_OBJECT:
                    response = self.client.chat.completions.create(
                        model=model_name,
                        temperature=0,
                        messages=ai_prompt.messages,
                        response_format={"type": "json_object"},
                    )
                elif response_type is OpenAIResponseType.JSON_SCHEMA:
                    assert response_json is not None
                    response = self.client.chat.completions.create(
                        model = model_name,
                        temperature=0,
                        messages=ai_prompt.messages,
                        response_format={"type": "json_schema", "json_schema": response_json}

                    )
                else:
                    response = self.client.chat.completions.create(
                        model=model_name,
                        temperature=0,
                        messages=ai_prompt.messages,
                    )
                end_time = timeit.default_timer()
                execution_time = end_time - start_time
                logger.warning(f"[[[[[[[[[ ------   Execution time for OpenAI ({type(ai_prompt)}) get_model_response: {execution_time} seconds  ------ ]]]]]]]]")
   
                logger.debug(
                    f"OpenAI Call Completed for model: {model_name} response: {response}, tries: {tries}"
                )

                # TODO: Log the response and message in db for tracking.
                if response is None or len(response.choices) == 0:
                    logger.error(
                        f"Open AI called returned none response or response has no choice. {self}"
                    )
                    return None

                if (
                    response.choices[0].finish_reason == "length"
                    and tries > 0
                    and model_name != OpenAIClient.MODEL_GPT35
                ):
                    tries -= 1
                    model_name = OpenAIClient.MODEL_GPT35
                    is_completed = False
                    logger.warning(
                        "Failed with length of tokens error so now trying with GPT35 model"
                    )
                else:
                    is_completed = True

            content = response.choices[0].message.content
            if check_str_not_null(content):
                content = content.strip()
            logger.debug(content)
            assert len(content) > 0
            return content
        except Exception as err:
            logger.error(str(err))
            raise err

    def get_embeddings(self, text: str):
        """Get the embeddings for text from OpenAI."""
        logger.info(f"OpenAI Embeddingss call started for model: {self.model_name}")
        try:
            response = self.client.embeddings.create(input=text, model=self.model_name)
            embedding = response.data[0].embedding
            return np.array(embedding)
        except Exception as err:
            logger.error(str(err))
            raise err
