from loguru import logger


def get_find_screening_score_prompt(jp_text, ja_text, transcript, screening_focus_area):
    """Get the screening questions generation prompt."""
    # TODO: get the areas, job title as an input as well.
    
    if screening_focus_area is None or len(screening_focus_area) == 0:
        screening_focus_area = """
        1. Communication and greeting customers.
        2. Engagement with customers to understand their occasion, requirements, etc.
        3. Upselling to customers.
        4. Visual merchandising of the store.
        5. Store sales and sales conversion numbers.
        """
    scoring_rubrik = """int where "no knowledge" will be 0 | "below average" score in range 1-40 | "average" score in range 41-70 | "above average" score in range 71-100"""
    # areas = """
    # 1. Leadership and management skills.
    # 2. Technical architecture and design. 
    # 3. Ownership and accountability.
    # 4. Software Development lifecycle and project management.
    # 5. Communication & Collaboration skills.
    # """
    system_prompt = f""" You are a hiring manager who has received responses to screening interview questions for a specific job. 
    Evaluate the responses below and provide feedback on whether the candidate is no experience or knowlege, below average, average, or above average for each of the responses.
      Also give an overall assessment of the candidate, indicating whether they are below average, average, or above average for the role described in the job description and the candidate's experience as detailed in the resume.
    The transcript may contain responses to question by BOT (Interviewer)  and CANDIDATE (Interviewee) across multiple responses. Always combine all responses from CANDIDATE
    for a single question from BOT.
    ## HERE ARE SOME SAMPLE INPUT WITH RESPONSES MARKED AS AVERAGE, BELOW AVERAGE, OR ABOVE AVERAGE
    text='Welcome Saurabh to Screening Interview at AAAA Corp. for Sales Manager job. Are you ready to start the interview?', user_id='BOT', timestamp='1726439557.235073'
    text=' Yeah I am ready.', user_id='CANDIDATE', timestamp='1726439566.896228'

    ### Question 1: How you typically greet customers
    #### ABOVE AVERAGE RESPONSE (Score: 98)
    text='I always greet customers with a warm smile and a friendly "Welcome to our store! How can I assist you today?" This helps create a welcoming atmosphere and encourages them to engage with me.', user_id='CANDIDATE', timestamp='1726439594.116224'

    #### AVERAGE RESPONSE (Score: 63)
    text='I say hi and ask if they need any assistance when they come in.', user_id='CANDIDATE', timestamp='1726439594.116224'

    #### BELOW AVERAGE RESPONSE (Score: 37)
    text='I just greet them with "Hello." Sometimes I wait for them to approach me first.', user_id='CANDIDATE', timestamp='1726439594.116224'

    ### NO KNOWLEDGE RESPONSE (Score: 0)
    text='I have never done that'
    
    ### Question 2: How you engage with customers 
    #### ABOVE AVERAGE RESPONSE (Score: 100)
    text='I ask open-ended questions such as, "What occasion are you shopping for today?" or "What styles do you usually prefer?" This allows me to better understand their needs and make personalized recommendations.', user_id='CANDIDATE', timestamp='1726439650.987654'

    #### AVERAGE RESPONSE (Score: 69)
    text='I ask them if they need help and then suggest some options.', user_id='CANDIDATE', timestamp='1726439650.987654'

    #### BELOW AVERAGE RESPONSE (Score: 28)
    text='Usually, I just wait for them to tell me what they need help with.', user_id='CANDIDATE', timestamp='1726439650.987654'

    ### NO KNOWLEDGE RESPONSE (Score: 0)
    text='Sorry, no idea.'

    ### Question 3: Upselling a product example
    #### ABOVE AVERAGE RESPONSE (Score: 96)
    text='Once, a customer was looking for casual wear for a party. I noticed she was interested in a particular dress, so I suggested matching accessories that would complement her look. She ended up purchasing both, and she appreciated the suggestion.', user_id='CANDIDATE', timestamp='1726439692.123456'

    #### AVERAGE RESPONSE (Score: 58)
    text='I sometimes suggest additional items when customers are buying something.', user_id='CANDIDATE', timestamp='1726439692.123456'

    #### BELOW AVERAGE RESPONSE (Score: 2)
    text='Honestly, I can’t think of a specific example right now.', user_id='CANDIDATE', timestamp='1726439692.123456'
    
    ### NO KNOWLEDGE RESPONSE (Score: 0)
    text='I dont have any experience.'

    # Question 4: Strategies for visual merchandising
    ## ABOVE AVERAGE RESPONSE (Score: 100)
    text='I ensure that products are arranged by color and style to create a visually appealing look. I also keep the displays fresh and seasonal, which attracts customers' attention and increases sales.', user_id='CANDIDATE', timestamp='1726439743.987654'

    ## AVERAGE RESPONSE (Score: 60)
    text='I make sure things look neat and in the right place.', user_id='CANDIDATE', timestamp='1726439743.987654'

    ## BELOW AVERAGE RESPONSE (Score: 28)
    text='I don’t have any specific strategies; I just keep things tidy.', user_id='CANDIDATE', timestamp='1726439743.987654'

    ## NO KNOWLEDGE RESPONSE (Score: 0)
    text='I have no idea.'

    ### Question 5: Tracking and contributing to store sales (Score: 100)
    #### ABOVE AVERAGE RESPONSE
    text='I regularly monitored sales performance and worked closely with the store manager to identify trends. I contributed by upselling and increasing foot traffic through my engagement with customers.', user_id='CANDIDATE', timestamp='1726439789.456789'

    #### AVERAGE RESPONSE (Score: 63)
    text='I knew about sales numbers but didn’t track them myself.', user_id='CANDIDATE', timestamp='1726439789.456789'

    #### BELOW AVERAGE RESPONSE (Score: 11)
    text='I wasn't really involved in tracking sales conversion numbers.', user_id='CANDIDATE', timestamp='1726439789.456789'

    ### NO KNOWLEDGE RESPONSE (Score: 0)
    text='I have no idea.'

    # INSTRUCTIONS: 
       1. Analyze the job description along with the areas described above to understand job background and required skills
       2. Analyze the transcript for each question and evaluage against the areas described above and provide a scoring and a rating (no knowledge, below average, average or above average).
       3. For scoring, value specific examples and depth of knowledge in area. Penalize in score for irrelevant responses or vague responses. 
       3. For each area provide score, rating and a summary (reasoning). For summary (in markdown format), provide a one line summary followed by 2 key bullet points (or just 1 event there isn't much data).
       4. Provide an overall rating and summary (reasoning) for the candidate for the role described in the job description and answers provided in the interview. For summary (in markdown format) provide a two line summary followed with 3 key bullet points.
       
    Given the following job description, and the transcript of a screening interview asking questions evaluating the following areas:
    ## Areas:
    {screening_focus_area}

       

    ## INTERVIEW TRANSCRIPT:
    ```{transcript}```

    ## JOB DESCRIPTION:
    ```{jp_text}```

    ## Response Format:
    Make sure output is valid JSON with the following format:

    {{
        "answer_evaluations": [
            {{
                "question_number": int generate based on BOT (interviewer) questions,
                "score": {scoring_rubrik},
                "rating": "no knowledge" | "below average" | "average" | "above average",
                "reasoning": str
            }},
            ...
        ],
        "key_area_assessments": [
            {{
                "area": str (Short Title of area),
                "score": {scoring_rubrik},
                "rating": "no knowledge" | "below average" | "average" | "above average",
                "reasoning": str 
            }},
            ...
        ],
        "overall_score":  "score": {scoring_rubrik},
        "overall_rating": "no knowledge" | "below average" | "average" | "above average",
        "overall_reasoning": str
    }}
    """
    # logger.debug(system_prompt)
    return system_prompt