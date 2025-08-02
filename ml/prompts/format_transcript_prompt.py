from loguru import logger


def get_format_transcript_system_prompt():
    """Get the screening questions generation prompt."""
    # TODO: get the areas, job title as an input as well.
    
    system_prompt = f""" Generate the responses mentioned in another format to transcript of interview specified. 
    You will be given a transcript of interview between a Candidate and Interviewer (bot) with a timestamp. 
    Candidate will reply multiple times to the question by interviewer. Bot will ask if users want to continue 
    to next or provide more input in which case user will continue to provide answer to previous question. 
    NOTE: that this is text converted from speech to text so treat it accordingly. Also don't change any answers 
    in any way and strictly just change into the required format. In addition every conversation has a timestamp
    which you need to convert to GMT.
    Your task is to combine the answers together by Candidate in markdown format as per the TRANSCRIPT format described below.
    NOTE: TIME below should be in format 2024-09-19T00:57:53Z
    ## TRANSCRIPT

    **BOT** *[TIME: START TIME IN GMT, DURATION: DURATION IN SECONDS like 4s]*:
    > Q: <Question goes here> 

    **CANDIDATE** *[TIME: START TIME IN GMT, DURATION: DURATION IN SECONDS like 4s]*:
    > A: <Combined Answers go here>  
    
    ...
    """
    # logger.debug(system_prompt)
    return system_prompt

def get_format_transcript_user_prompts(transcript:str):
    """Get the user prompts for format transcript."""
    user_prompt = f"""
    Here is the transcript of interview to convert:
    ```{transcript}```"""
    user_prompts = [
        {"role": "user", "content": user_prompt},
    ]
    return user_prompts