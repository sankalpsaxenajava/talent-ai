"""Chat Bot memory object."""

import threading
from intai.models.models import JobConversationChatDb
from loguru import logger
import json
import msgpack


class ChatbotMemory:
    """Singleton class for Chatbot memory"""

    _instance = None
    _lock = threading.Lock()
    # memory is dictionary of conversation ids and list of messages for that conversation
    # where each message is a dictionary of key, value pair where key is role, content
    _memory: dict[str, list[dict[str, str]]] = {}

    def __new__(cls, company_id):
        if cls._instance is None:
            with cls._lock:
                # Another thread could have created the instance
                # before we acquired the lock. So check that the
                # instance is still nonexistent.
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, company_id):
        logger.trace(company_id)
        self.company_id = company_id

    def store_db(self, session, conversation_id, company_id, message):
        """Store the conversation in database"""
        job_conversation_db = JobConversationChatDb(
            conversation_id=conversation_id,
            company_id=company_id,
            message=message,
        )
        job_conversation_db.insert_job_conversation_chat(session)

    def add_message(self, session, conversation_id: str, message: dict[str, str]):
        """Add the message for conversation to memory"""
        if conversation_id not in self._memory:
            self._memory[conversation_id] = []

        msgs_conv = self._memory[conversation_id]
        msgs_conv.append(message)
        message_bytes = msgpack.packb(msgs_conv)
        logger.debug(f"message_bytes: {message_bytes}")
        self.store_db(
            session,
            conversation_id=conversation_id,
            company_id=self.company_id,
            message=message_bytes,
        )

    def get_messages_by_conversation(self, session, conversation_id: str):
        """Get the messages by conversation id.

        NOTE: This will look first in the in-memory dictionary and
        if not found try to load from the database."""
        if conversation_id in self._memory:
            return self._memory[conversation_id]

        # load from the database
        job_conversation_chat_db = JobConversationChatDb.get_job_conversation_chat(
            session, self.company_id, conversation_id
        )
        dict_message = None
        if job_conversation_chat_db:
            message_bytes = job_conversation_chat_db.message
            logger.debug(f"Loading from Db: {message_bytes}")
            dict_message = msgpack.unpackb(message_bytes)
            logger.debug(f"dict_message: {dict_message}")
            self._memory[conversation_id] = dict_message

        return dict_message

    def __repr__(self):
        return f"{self._memory}"
