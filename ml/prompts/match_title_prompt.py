from loguru import logger


def get_title_match_system_prompt():
    """Get title match system prompt."""
    system_prompt = """Decide whether given list of Job titles perform similar job
        responsibilities as JD JobTitle ,create json with key as
        result and value as true or false if any of the job title
        in list matches with JD JobTitle.
                {{
                    'result': true/false
                }}
                """
    # logger.debug(system_prompt)
    return system_prompt


def get_title_match_user_prompt(jp_title, ja_titles):
    """Get title match system prompt."""
    user_prompt = f"Job Title List: {ja_titles} and JD JobTitle: {jp_title}"
    # logger.debug(user_prompt)
    return user_prompt
