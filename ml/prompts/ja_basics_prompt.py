from loguru import logger

def get_ja_basics_system_prompt():
    """Get JA Basics  system prompt."""

    system_prompt = """
    Your task is to extract specific pieces of information from a given resume  and present it in a strictly formatted JSON structure.
    If a certain piece of information is not available in the resume, use the placeholder null for that field.
    """
   
    message = {"role": "system"}

    logger.debug(system_prompt)
    message["content"] = system_prompt
    return message


def get_ja_basics_user_prompts(ja_text: str):
    """Get JA basics user prompt."""
    messages = []
    
    message = {"role": "user", "content": "Parse the following resume in required JSON format: \n" + ja_text}
    messages.append(message)
    logger.debug(messages)
    return messages

def get_ja_basics_response_schema():
    """Return the QA reponse JSON schema"""
    return {
        "name": "job_application_basics",
        "strict": True,
        "schema": {
            "type": "object",
            "required": [
            "firstName",
            "lastName",
            "phone",
            "linkedin",
            "email",
            "experienceInYears",
            "currentCompany",
            "currentDesignation",
            "latestDegree",
            "yearOfGraduation",
            "latestInstitution",
            "location"
            ],
            "properties": {
            "firstName": {
                "type": "string"
            },
            "lastName": {
                "type": "string"
            },
            "email": {
                "type": "string"
            },
            "phone": {
                "type": "string",
                "description": "country_code phone_number"
            },
            "linkedin": {
                "type": "string"
            },
            "location": {
                "type": "string",
                "description": "city if present else state or country"
            },
            "latestInstitution": {
                "type": "string"
            },
            "latestDegree": {
                "type": "string"
            },
            "currentCompany": {
                "type": "string"
            },
            "yearOfGraduation": {
                "type": "string",
                "description": "YYYY"
            },
            "currentDesignation": {
                "type": "string"
            },
            "experienceInYears": {
                "type": "number",
                "description": "years of experience in years like 10.5"
            }
            },
            "additionalProperties": False
        }
    }
