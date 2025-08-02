from enum import Enum


class LLMModelType(Enum):
    """LLM Model types sorted."""

    INVALID = 0
    GPT35 = 1
    GPT40 = 2
    GPT40T = 3
    GPT40S = 4
    GPT40M = 5
    EMBEDDING_ADA = 6

    @classmethod
    def get_model_name_cls(cls, model_type):
        model_names = {
            cls.INVALID: "gpt-3.5-turbo",
            cls.GPT35: "gpt-3.5-turbo",
            cls.GPT40: "gpt-4o",
            cls.GPT40T: "gpt-4-turbo-preview",
            cls.GPT40S: "gpt-4o-2024-08-06",
            cls.GPT40M: "gpt-4o-mini",
            cls.EMBEDDING_ADA: "text-embedding-ada-002"
        }

        model_name = model_names.get(model_type, "unknown")
        print(f"LLMMODELTYPE: {model_name}")
        return model_name

    def get_model_name(self):
        return LLMModelType.get_model_name_cls(self)
    
class LLMResponseType(Enum):
    "OpenAI response type."
    TEXT = 0
    JSON_OBJECT = 1
    JSON_SCHEMA = 2