from loguru import logger


def get_ja_matching_summary_system_prompt(jp_text, ja_text):
    """Get summary match system prompt."""
    system_prompt = f""" You are a helpful recruiting assistant whose job is to analyze
    the resume and job description mentioned below and provide 100 word summary on
    specific reasons based on education, experience and skills to describe why this profile
    is a good match and why this is not a good match for the job.

    Job Description Text:
    ```{jp_text}```
    Resume Text:
    ```{ja_text}```
    Make sure output is valid JSON with the following format:
    {{
        "summary":""

    }}
                """
    # logger.debug(system_prompt)
    return system_prompt
