import os
import timeit
from typing import List, Dict, Any
from uuid import uuid4
import litellm
from langfuse.client import Langfuse
from loguru import logger
import numpy as np
from intai.ml.ai_prompt import AIPrompt
from intai.ml.utils.llm_types import LLMModelType, LLMResponseType



from intai.utils.str_utils import check_str_not_null
class LLMClient:
    DEFAULT_MODEL = LLMModelType.GPT40S
    def __init__(self, model: LLMModelType = DEFAULT_MODEL, session_id: str = None, client_id: str = None):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.session_id = session_id if session_id is not None else str(uuid4())
        self.model_type = model
        self.client_id = client_id
        logger.info(f"Using model: {self.model_type}")
        litellm.set_verbose=True
        if os.getenv("USE_LANGFUSE") is not None:
            logger.info("Langfuse Enabled")
            self.langfuse = Langfuse(
                os.environ.get("LANGFUSE_PUBLIC_KEY"),
                os.environ.get("LANGFUSE_SECRET_KEY")
            )
            litellm.success_callback = ["langfuse"]
            # set callbacks
            litellm.failure_callback = ["langfuse"]

    def get_model_response(self, ai_prompt:AIPrompt, response_type: LLMResponseType=LLMResponseType.JSON_OBJECT, response_json: str=None) -> Any:
        
         # log input/output to lunary, langfuse, supabase, athina, helicone etc
        logger.info(
            f"OpenAI Call Started for model: {self.model_type}; prompt {ai_prompt}; response_type: {response_type} json: {response_json}"
        )
        try:
            # NOTE: We are retrying to fallback to a different model. Potentially there could be 
            # other reasons to fallback in future as well.

            tries = 1
            model_name = self.model_type.get_model_name()
            is_completed = False
            metadata = {"session_id": self.session_id, "trace_user_id":self.client_id, "tags": [type(ai_prompt).__name__, model_name]}
            while tries <3 and not is_completed:
                logger.debug(f"session_id={self.session_id} response_type: {response_type} tries {tries} is_completed: {is_completed}")
                start_time = timeit.default_timer()

                if response_type == LLMResponseType.JSON_OBJECT:
                    logger.debug(f"AAAAAA")
                    response = litellm.completion(
                        model=model_name,
                        messages=ai_prompt.messages,
                        api_key=self.api_key,
                        response_format={"type": "json_object"},
                        temperature=0, 
                        metadata=metadata,
                    )
                elif response_type == LLMResponseType.JSON_SCHEMA:
                    logger.debug(f"CCCCCC")
                    litellm.enable_json_schema_validation = True
                    
                    response = litellm.completion(
                        model=model_name,
                        messages=ai_prompt.messages,
                        api_key=self.api_key,
                        response_format={"type": "json_schema", "json_schema": response_json},
                        temperature=0,
                        metadata=metadata,
                    )
                else:
                    logger.debug(f"BBBBBB")

                    response = litellm.completion(
                        model=model_name,
                        messages=ai_prompt.messages,
                        api_key=self.api_key,
                        temperature=0,
                        metadata=metadata,
                    )

                end_time = timeit.default_timer()
                execution_time = end_time - start_time
                logger.warning(f"[[[[[[[[[ ------   Execution time for OpenAI ({type(ai_prompt)}) get_model_response: {execution_time} seconds  ------ ]]]]]]]]")
   
                # TODO: Log the response and message in db for tracking.
                if response is None or len(response.choices) == 0:
                    logger.error(
                        f"Open AI called returned none response or response has no choice. {self}"
                    )
                    return None

                if (
                    response.choices[0].finish_reason == "length"
                    and tries > 0
                    and model_name != LLMModelType.MODEL_GPT35
                ):
                    tries -= 1
                    model_name = LLMModelType.MODEL_GPT35
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
        except Exception as e:
            logger.error(str(e))
            raise e
        

    def get_embeddings(self, text: str) -> List[float]:
        """Create embedding for the given text."""
        try:
            metadata = {"session_id": self.session_id, "trace_user_id":self.client_id, "tags": ["embeddings"]}
            start_time = timeit.default_timer()
            response = litellm.embedding(
                model="text-embedding-ada-002",
                input=[text],
                api_key=self.api_key,
                metadata=metadata,
            )
            embedding = response.data[0]["embedding"]
            end_time = timeit.default_timer()
            execution_time = end_time - start_time
            logger.warning(f"[[[[[[[[[ ------   Execution time for OpenAI embedding: {execution_time} seconds  ------ ]]]]]]]]")
            return np.array(embedding)
        except Exception as e:
            logger.error(str(e))
            raise e
       

