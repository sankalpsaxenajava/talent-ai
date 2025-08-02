from loguru import logger

def get_qa_chatbot_system_prompt(context: dict[str, str]):
    """Get QA chatbot system prompt."""

    system_prompt = """
    You are a helpful recruiting assistant who will answer queries from potential candidates based on the JobsFAQ document provided below.  
    Strictly keep the answer to the questions related to company and culture and stick to the information available in the JobsFAQ document. 
    If there are queries do not match this criteria then response with 'I am sorry I don't have information about this'. 
    Always return strictly in JSON format specified and populate answer to query in answer property. Also, always populate intent as general_question intent.

    """
    logger.debug(context)
    message = {"role": "system"}
    for key in context:
        system_prompt += "\n" + key + ": " + context[key]

    logger.debug(system_prompt)
    message["content"] = system_prompt
    return message


def get_qa_chatbot_user_prompts(history: list[str], query: str):
    """Get chatbot user prompt."""
    messages = []
    if history:
        for hist_msg in history:
            messages.append(hist_msg)
    message = {"role": "user", "content": query}
    messages.append(message)
    logger.debug(messages)
    return messages

def get_qa_response_schema():
    """Return the QA reponse JSON schema"""
    return {
        "name": "get_qachatbotintent_response",
        "strict": False,
        "schema": {
            "type": "object",
            "properties": {
            "intent": {
                "type": "string",
                "enum": ["general_question"]
            },
            "answer": {
                "type": "string",
                "description": "Response based on documents specified in context"
            }
            },
            "required": [
            "intent",
            "answer"
            ],
            "additionalProperties": False
        }
    }