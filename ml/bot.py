"""Implements the Conversational Chatbot high level API and management."""

from intai.ml.ai_prompt import ChatbotAIPrompt, JobsChatbotAIPrompt, QAChatbotAIPrompt
from intai.ml.bot_memory import ChatbotMemory
from intai.ml.llm_client import LLMClient
from intai.ml.utils.llm_types import LLMModelType, LLMResponseType
from intai.utils.str_utils import check_str_not_null
from loguru import logger
import uuid
from enum import Enum as PyEnum


class BotMessageType(PyEnum):
    """Describes the type of Bot message"""

    HUMAN = 1
    AI = 2


class BotMessage:
    def __init__(self, message: str, message_type: BotMessageType):
        self.content = message
        self.role = "assistant" if message_type == BotMessageType.AI else "user"

    def __repr__(self):
        return f"{self.role}: {self.content}"

    def as_dict(self):
        return {"role": self.role, "content": self.content}


class BotMessageTurn:
    def __init__(
        self, conversation_id: str, ai_message: BotMessage, human_message: BotMessage
    ):
        self.conversation_id = conversation_id
        self.ai_message = ai_message
        self.human_message = human_message

    def __repr__(self):
        return f"{self.human_message}\n {self.ai_message}"

    def as_list(self):
        ret = []
        ret.append(self.human_message)
        ret.append(self.ai_message)
        return ret

class ChatbotType(PyEnum):
    "Describes if the Chatbot is Jobs, QA or SingleJob"
    SingleJob = 1
    Jobs = 2
    QA = 3
    
class Chatbot:
    """Recruitment Chatbot.
    TODO: Make this as a generic chatbot and create a subclass for recruitment chatbot.
    """

    def __init__(
        self,
        session,
        company_id: int,
        conversation_id: str = "",
        chatbot_type: ChatbotType = ChatbotType.SingleJob,
    ) -> None:
        self.company_id = company_id
        self.session = session
        if check_str_not_null(conversation_id):
            self.conversation_id = conversation_id
        else:
            self.conversation_id = str(uuid.uuid4())

        logger.debug(
            f"conversation_id: {conversation_id}; is_jobs_chatbot: {chatbot_type}"
        )
        self.memory = ChatbotMemory(company_id=company_id)
        self.type = chatbot_type
        logger.debug(f"{self.memory} type: {self.type}")
        logger.debug("Bot init")

    def add_message_to_memory(self, user_query: str, ai_response: str):
        """Add the message to the memory and persist if needed"""
        user_bot_message = BotMessage(user_query, BotMessageType.HUMAN)
        ai_bot_message = BotMessage(ai_response, BotMessageType.AI)

        turn = BotMessageTurn(
            self.conversation_id,
            ai_message=ai_bot_message,
            human_message=user_bot_message,
        )

        # TODO Summarize if the length of memory is greater than say 20 messages?
        # TODO Store this memory in database. NOTE: In database we always summarize and store.
        turn_messages = turn.as_list()
        for item in turn_messages:
            self.memory.add_message(self.session, self.conversation_id, item.as_dict())

    def get_memory(self):
        return self.memory.get_messages_by_conversation(
            self.session, self.conversation_id
        )

    def start(
        self,
        context: dict[str, str],
        user_query: str = "",
    ):
        """Start the conversation bot.

        NOTE: Currently start basically ends up calling the predict etc.
        But predict is needed separately in case of a web socket connection
        where a start will accept the socket and predict will answer subsequent
        queries.
        """

        logger.debug(
            f"bot context: {context}; user_query: {user_query}; chatbot_type: {self.type}; conversation_id: {self.conversation_id}"
        )
        # TODO Load the conversation history from db.
        self.context = context
        memory = self.get_memory()

        if check_str_not_null(user_query):
            return self.predict(user_query)
        elif not memory or len(memory) == 0:
            return self._call("Whats up?")

        # TODO Summarize if needed.

    def _call(self, user_query: str):

        prompt = ""
        ai_client: OpenAIClient = LLMClient(client_id=self.company_id, session_id=self.conversation_id)
        if self.type == ChatbotType.Jobs:
            logger.debug("In Call for Jobs Chatbot")
            prompt = JobsChatbotAIPrompt(self.context, self.get_memory(), user_query)
            response = ai_client.get_model_response(prompt, response_type = LLMResponseType.JSON_SCHEMA, response_json=prompt.response_schema)

        elif self.type == ChatbotType.QA:
            logger.debug("In Call for QA Chatbot")

            prompt = QAChatbotAIPrompt(
                self.context,
                self.get_memory(),
                user_query,
            )
        
            response = ai_client.get_model_response(prompt, response_type = LLMResponseType.JSON_SCHEMA, response_json=prompt.response_schema)
        else: 

            logger.debug("In Call for Single Job Chatbot")

            prompt = ChatbotAIPrompt(
                self.context,
                self.get_memory(),
                user_query,
            )
        
            response = ai_client.get_model_response(prompt, response_type=LLMResponseType.JSON_OBJECT)
        self.add_message_to_memory(user_query=user_query, ai_response=response)
        logger.debug(
            f"query: {user_query}\n response: {response}\n memory: {self.memory} "
        )
        return response

    def predict(self, user_query: str):
        """Call OpenAI to get the next response based on context. This function is supposed to
        always be called with the user-query"""
        response = ""
        if check_str_not_null(user_query):
            response = self._call(user_query)
        else:
            logger.error("user message is null for conversation: {self}")

        return response
