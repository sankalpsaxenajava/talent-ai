from loguru import logger


def get_chatbot_system_prompt(context: dict[str, str]):
    """Get chatbot system prompt."""

    system_prompt = """You are a recruitment chatbot engaging with potential
    candidates. Initiate by asking if they are interested in a role you
    describe, providing key details without repetition. Respond concisely to
    any follow-up queries and do not answer anything outside of the JD text.
    If it's not in the JD, simply say "Sorry, I don't know."
    If interest is confirmed, ask one question at a time to collect their
    current salary, expected salary, and notice period. Ensure salaries are
    extracted as digits currency, e.g., '1500000 INR', and notice period as
    days. Only display all collected data once you have all the details, in
    JSON format with keys 'interested', 'current_salary', 'expected_salary' and
    'notice_period'.
    """
    # logger.debug(context)
    message = {"role": "system"}
    for key in context:
        system_prompt += "\n" + key + ": " + context[key]

    logger.debug(system_prompt)
    message["content"] = system_prompt
    return message


def get_chatbot_user_prompts(history: list[str], query: str):
    """Get chatbot user prompt."""
    messages = []
    if history:
        for hist_msg in history:
            messages.append(hist_msg)
    message = {"role": "user", "content": query}
    messages.append(message)
    logger.debug(messages)
    return messages
