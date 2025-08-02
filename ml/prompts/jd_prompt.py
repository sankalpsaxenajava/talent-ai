from datetime import date
from .industries import industries
import re
from loguru import logger


def remove_text_in_parentheses(text):
    return re.sub(r"\([^)]*\)", "", text)


modified_industries = [remove_text_in_parentheses(industry) for industry in industries]
modified_industries_string = "|".join(modified_industries)

today = date.today()
print(today)  # Outputs something like: 2023-11-09
# Extracting month and year
month_year = today.strftime("%m-%Y")

prompt_jd_without_example = f"""
Your task is to extract specific peices of infomation from a given text and present it in a strictly formatted JSON structure. It's crucial that the JSON structure is accurately maintained, as any extraneous characters or formatting mistakes will lead to errors.

The text contains a job description. Carefully read the entire text to assess and extract the seven most critical skills required for the role. Concentrate on identifying specific technical skills and soft skills that are directly applicable to job tasks. Assign a percentage to each skill ensuring the total is 100%.
Exclude the following from your analysis:
- Software, technical tools, and applications
- Programming languages
- Personal character traits such as resilience or punctuality
- Job performance conditions or expectations, such as meeting deadlines or working under pressure

Extract the overall years of experience required for the job and assign a value to it. Extract the years of experience required for each of the above mentioned skills and assign a value to it. If the years of experience is not mentioned for a skill, use the value of overall years of experience for the job.

For education if  multiple qualifications are presented as options and if atleast one is mandatory, then make sure to mark each as education option as mandatory.

If a certain piece of information is not available in the resume, use the placeholder "null" for that field. Be especially careful with characters that can break JSON formatting like quotes or extraneous commas. If any information in Job description is ambigous or unclear, opt for the "null" placeholder.

When any dates are mentioned as present or current, consider it as {month_year}.
Strictly output in the following format:
{{
    "summary": "",
    "basics": [
        {{  "jobTitle": "",
            "jobLevel": "",
            "organization": "",
            "organizationsIndustrySegment": "<Select only from the list provided: {modified_industries_string} >",
            "department": "",
            "location": "",
            "reportingTo": "",
            "preferredCandidateCurrentRole": "",
            "minBaseSalaryRange" : "",
            "maxBaseSalaryRange": "",
            "minCurrentBaseSalaryOfCandidates": "(if defined)",
            "maxCurrentBaseSalaryOfCandidates": "(if defined)",
            "relocationSupport": true or false,
            "IsworkAuthorizationRequired": true or false,

        }}
    ],
    "overallYearsOfExperience": 0,
    "keyResponsibilities": [""]
    "peopleManagementExperience" : true or false,
    "softwareToolsOrProgrammingLanguages": [
        {{"name": "",
        "isMandatory": true or false
        }}
    ]
     "skills": [
        {{
            "skillName": "<Extracted Skill 1>",
            "yearsOfExperience": 0,
            "score":  "Percentage reflecting importanceof Skill 1"
        }},
        // Repeat for 7 skills
        {{
            "skillName": "Extracted Skill 7>",
            "yearsOfExperience": 0,
            "score":  "Percentage reflecting importanceof Skill 7"
        }}
    ]
    "education": [
        {{
            "degree_level": "Secondary, Higher Secondary, Diploma, Bachelor's, Graduate, Master's, Postgraduate, Doctorate, Certification etc", //If multiple, then write by comma seperated
            "degree": "BSc,MBA,BE,MD,PhD etc ",//If not specified, try to infer as per eduactional requirement else null
            "field_of_study": "Computer Science, Law, Medicine etc",
            "specialization": "Finance, Artificial Intelligence, Marketing, Pediatrics etc",
            "EducationInstitution'sPreference": [""],
            "isMandatory": "true or false"
        }}
    ],
    "languages": [
        {{
            "name": "",
            "fluency": ""
        }}
    ],
    "certifications": [""],
    "industryPreference": [""],
    "organizationPreference": [""],
    "organizationsToAvoid": [""],
    "papersPublished": count,
    "patentsFiled": count

}}"""
# logger.debug(prompt_jd_without_example)
