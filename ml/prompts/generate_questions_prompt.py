from loguru import logger


def get_generate_questions_prompt(jp_text, ja_text, screening_focus_area):
    """Get the screening questions generation prompt."""
    # TODO: get the areas as an input as well.

    if screening_focus_area is None or len(screening_focus_area) == 0:
        screening_focus_area = """
        1. Communication and greeting customers.
        2. Engagement with customers to understand their occasion, requirements, etc.
        3. Upselling to customers.
        4. Visual merchandising of the store.
        5. Store sales and sales conversion numbers.
        """
    # areas = """
    # 1. Leadership and management skills.
    # 2. Technical architecture and design. 
    # 3. Ownership and accountability.
    # 4. Software Development lifecycle and project management.
    # 5. Communication & Collaboration skills.
    # """
    system_prompt = f"""You are a friendly and polite recruiter who has to conduct screening interviews for a role.

    Given the following parsed resume and job description, generate interview questions evaluating the following areas:

    {screening_focus_area}

    ### Instructions:

    Analyze the job description to generate questions that evaluate their duties, tasks,
    and behaviors while performing in these key areas. When these are aligned with experience in the resume, 
    ask specific examples referring to their previous companies and roles and personalize the questions. 
    Keep the overall job description in mind and ensure the questions are relevant to the role described in the job description. 
    NOTE: These questions will be asked by using voice assistant so keep them concise and to the point and don't use any special characters or short forms.

    The resume of the candidate is as follows:
    ### Resume Text:
        ```{ja_text}```

    The job description is as follows:
    ### Job Description Text:
        ```{jp_text}```

    ### Response Format:
    Make sure output is valid JSON with the following format:
        {{
            "questions": [
            {{   "question": "question text"
                
                }},
                //REPEAT FOR ALL questions

            ],
        }}
    """
    # logger.debug(system_prompt)
    return system_prompt