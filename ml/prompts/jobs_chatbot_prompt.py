from loguru import logger


def get_jobs_chatbot_system_prompt(context: dict[str, str]):
    """Get chatbot system prompt."""

    system_prompt = """
    You are a helpful recruiting and job search assistant chatting with potential candidates and identifying
    following intents:
    get_jobs, apply_job, get_application_status, general_question in JSON output format.

    Once all parameters for intent are provided confirm with candidate with those values. Maintain the state of parameters from previous intents.

    get_jobs Intent:
    Candidate is interested in finding a job that matches their experience, position, department and location.

    apply_job Intent:
    Candidate is interested in applying for a job by providing a job id.

    get_application_status Intent:
    Candidate can also ask for an application status by providing  their email

    welcome Intent:
    Candidate is saying 'Hi' or 'Hello' to initiate a conversation. Respond in intent_question with 'Hi there! I can help you to find a job, apply for a job, get application status or general questions about company and culture'.

    general_question Intent:
    Candidate can also at anytime ask questions about culture, company, perks, benefits.  Always reply with None intent_question and current_intent_completed to true.
    """
    # logger.debug(context)
    message = {"role": "system"}
    #for key in context:
    #    system_prompt += "\n" + key + ": " + context[key]

    logger.debug(system_prompt)
    message["content"] = system_prompt
    return message


def get_jobs_chatbot_user_prompts(history: list[str], query: str):
    """Get chatbot user prompt."""
    messages = []
    if history:
        for hist_msg in history:
            messages.append(hist_msg)
    message = {"role": "user", "content": query}
    messages.append(message)
    logger.debug(messages)
    return messages

def get_jobs_response_schema():
    """Return the reponse JSON schema"""
    return {
        "name": "get_jobschatbotintent_response",
        "strict": False,
        "schema": {
            "type": "object",
            "properties": {
            "intent": {
                "type": "string",
                "description": "Current Intent",
                "enum": [
                "welcome",
                "get_jobs",
                "apply_job",
                "get_application_status",
                "general_question"
                ]
            },
            "intent_question": {
                "type": "string",
                "description": "Follow up question for the current intent or None when all parameters for intent are filled. For general_question intent always return as None"
            },
            "current_intent_completed": {
                "type": "boolean",
                "description": "True if all parameters have been asked for this intent else False. If intent changes then reset this parameter to False."
            },
             "current_intent_confirmed": {
                "type": "boolean",
                "description": "True if user has confirmed after current_intent_completed is set to True else False. If intent changes then reset this parameter to False."
            },
            "location": {
                "type": "array",
                "description": "Locations of job candidate is interested in for get_jobs intent. If user responds with all or anywhere etc. then set value to Any.",
                "items": {
                "type": "string"
                }
            },
            "department": {
                "type": "array",
                "description": "Departments of jobs candidate is interested in for get_jobs intent. If not provided default to Any. ",
                "items": {
                "type": "string",
                "enum": [
                    "Software",
                    "Finance",
                    "Sales",
                    "Marketing",
                    "Supply Chain",
                    "Manufacturing",
                    "Customer Support",
                    "Management",
                    "HR",
                    "Administration",
                    "Any"
                ],
                }
            },
            "job_type": {
                "type": "string",
                "description": "job_type for get_jobs intent",
                "enum": [
                "Part-Time",
                "Full-Time",
                "Any"
                ]
            },
            "years_experience": {
                "type": "number",
                "description": "Experience of candidate in years for get_jobs intent"
            },
            "job_id": {
                "type": "string",
                "description": "Id of the job for apply_job intent"
            },
            "email": {
                "type": "string",
                "description": "email Id of the candidate for get_application_status intent"
            }
            },
            "required": [
            "intent",
            "intent_question"
            ],
            "additionalProperties": False
        }
    }