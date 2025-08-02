"""Resume Prompt File."""

from datetime import date
from .industries import industries
import re
from loguru import logger


def remove_text_in_parentheses(text):
    return re.sub(r"\([^)]*\)", "", text)

def get_resume_prompt(ja_text: str):
    """Get the resume parsing prompt."""

    
    
    modified_industries = [remove_text_in_parentheses(industry) for industry in industries]
    modified_industries_string = "|".join(modified_industries)

    # print(modified_industries_string)

    today = date.today()
    print(today)  # Outputs something like: 2023-11-09
    # Extracting month and year
    month_year = today.strftime("%m-%Y")

    prompt_resume = f"""You are a expert resume parser and your task is to extract specific pieces of information from a given resume text
    and present it in a strictly formatted JSON structure. 

    ## INSTRUCTIONS
    1. Arrange the 'experience' section including any internships, trainings in strict chronological order placing the most recent roles at the top.
    2. Arrange the 'education' section in strict chronological order placing the most recent education at the top.
    3. Extract phone number as country code and mobile number. if country code is not mentioned infer it from address
    4. Only extract the dates mentioned in the resume and do not assume any other dates and show as null if not mentioned.
    When experience end date is mentioned as present or current, consider it as {month_year}.
    5. Assess the text to identify for each role, 7 most important technical or soft skills. 
    In case resume text does not provide enough details then suggest skills based on role title,organisation and industry.
    It should definitly not include softwares, techincal tools and applications, languages and personal character traits. 
    For each specific role assess if it is explicitly indicated that the candidate had direct and formal responsibility to lead a team as their manager.
    6. Assess certifications and trainings taken by the candidate and list upto three  most relevant skills for each.


    NOTE: If a certain piece of information is not available or ambiguous in the resume, use the placeholder null for that field.
    ## RESUME TEXT:
    ```{ja_text}```

    ## RESPONSE FORMAT:
    {{
        "summary": "",
        "basics": {{
                "address": [
                    {{
                        "city": "",
                        "state": "",
                        "country": "",
                        "full_address": ""
                    }}
                ]
                "totalExperienceInYears": "number decimal. Total experience in years, don't double count in case of overlapping roles",
            }},
        "experience": [
            {{
                "title": "",
                "company": "",
                "employment_type": "Full-time, Part-time, Self-employed, Freelance, Internship, Trainee",
                "start": "month number-year",
                "end": "month number-year",
                "yearsOfExperience": "number decimal",
                "description": "",
                "industry": "<Select only from the list provided: {modified_industries_string} >"
                "location": "city, state, country",
                "teamLeadingExperience": false
                "skills": [
                        {{
                            "skillName": "<Extracted Skill 1>",
                        }},
                        // Repeat for 7 skills
                        {{
                            "skillName": "<Extracted Skill 7>",
                        }}
                ]
                // Strictly Repeat for every year in yearsOfExperience
        }},
        "softwareToolsOrProgrammingLanguages": "",
        "languages": [
            {{
                "name": "",
                "fluency": ""
            }}
        ],
        "education": [
            {{
                "institution": "",
                "start_date": "number-year",
                "end_date": "number-year",
                "degree_level": "Secondary, Higher Secondary, Diploma, Bachelor's, Master's, Doctorate, Certification etc",
                "degree": "BSc,MBA,BE,MD,PhD etc ",
                "field_of_study": "Computer Science, Law, Medicine etc",
                "specialization": "Finance, Artificial Intelligence, Marketing, Pediatrics etc",
            }}
        ]

        "projects": [
            {{
                "title": "",
                "description": "",
                "start date": "",
                "end date": "",
                "techstack": "",
                "github link (optional)": ""
            }}
        ],
        "certificationsAndTrainings": [
            {{
                "name": "",
                "issuer": "",
                "issued date": "",
                "skills": []
            }}
        ],
        "volunteer": [
            {{
                "organization": "",
                "position": "",
                "start": "",
                "end": ""
            }}
        ],
        "publications": [
            {{
                "title": "",
                "publisher": "",
                "release date": "",
                "description": ""
            }}
        ],
        "awards": [
            {{
                "title": "",
                "date": "",
                "awarder": ""
            }}
        ],
        "interests": [
            ""
        ]
        "PromotionsOrRoleChangesInOrganization": 0,
        "awardsCount": 0,
        "certificationsOrEducationInNewDomain": false,
        "significantSkillChange": false,
        "papersPublishedCount": 0,
        "patentsFiledCount": 0,
        "conferencePresentationsCount": 0,
        "openSourceContributionsCount": 0
    }}
    """
    logger.debug(prompt_resume)
    return prompt_resume
