from loguru import logger


def get_factor_analysis_prompt(jp_text, ja_text):
    """Get the factor analysis prompt."""
    definitions = """

    Relevant experience, Title, Responsibilities performed, Preferred Industry, Brand:

    Relevant Experience: Assess the experience and skills required for the job description role, and evaluate the experience and skills of the candidate against that. Look for skills that are directly applicable to the requirements of the job description role, such as technical skills, leadership abilities, or domain knowledge. Give a higher score if relevant or mandatory skills and experiences are recent and sufficient, and a lower score if relevant or mandatory skills and experiences are not recent and not sufficient for the role.

    Title: Assess the title of the role in the job description role, and review it against the job titles the candidate has held and look for ones that are the same. Give a higher score if the titles are same and recent, and a lower score if the titles are not same or not recent.

    Responsibilities: Assess the responsibilities mentioned in the job description and evaluate the candidate's role descriptions and responsibilities for each role. Look for specific tasks, projects, and duties that are relevant to the job description role. Evaluate the level of complexity and scope of the candidate's responsibilities against what is required in the job description. Give a higher score if the candidate's responsibilities are recent and sufficient, and a lower score if the candidate's responsibilities are not recent and not sufficient for the role.

    Preferred Industry: Assess the industry of the organization in the job description, and evaluate it against the industries the candidate has worked in. Give a higher score if there are a higher number and more recent industry matches, and a lower score if there are a lower number and less recent industry matches.

    Brand: Assess the brand positioning of the organization in the job description. Review the brand positioning of the organizations the candidate has worked for. Give a higher score if the candidate’s brands are similarly well-positioned as well as recent, and a lower score if the candidate’s brands are less well-positioned or not recent.  

    Education:

    Education: Assess education qualifications required for the job in the job description. Review the candidate's academic credentials and assess whether those meet the educational requirements specified for the job. Give a full score if the candidate meets the minimum educational requirements as mentioned in the job description.

    Learnability, Growth, Accomplishments:

    Learnability: Review any additional training, certifications, courses, or whether the candidate has acquired new skills or expanded their skill set over time. This could include learning new technologies, tools, or methodologies relevant to their field. 

    Growth: Look for evidence of the candidate receiving promotions, taking on new challenges, roles, implementing innovative solutions or increasing responsibilities throughout their career and progression over time. 

    Accomplishments: Assess any notable achievements or accomplishments the candidate has listed for each role. Look for quantifiable results, awards, recognitions, papers published, patents filed, conference presentations made , open source contributions or successful projects that demonstrate their capabilities and contributions.

    Stability, Adaptability:

    Stability: Review the candidate's employment history to assess the length of time spent in each organization. Look for indications of stable job tenure, such as holding positions for several years without frequent job changes. Longer tenures may indicate more extensive experience and a deeper understanding of the role's requirements.
    Take into account industry norms and standards for job tenure and career progression. Some industries may have higher turnover rates or shorter average job tenures, so it's essential to consider the context when evaluating stability.

    Adaptability: Assess whether the candidate has experience in different industries, roles, locations or environments. A varied background can indicate adaptability and an ability to thrive in diverse settings.

    People Management Experience:

    People Management Experience: Look for specific job titles that indicate management or leadership responsibilities. Assess the candidate's job descriptions and responsibilities for each previous role. Look for indications of managing teams, departments, or projects, as well as supervising direct reports or overseeing the work of others.

    Programming Languages and Software:

    Programming Languages and Software: Assess the proficiency or years of experience required in programming languages, tools or software as mentioned in the job description. Evaluate whether the candidate’s proficiency or years of experience matches the requirement. Evaluate whether the candidate has completed coursework, training programs, or certifications that are directly applicable to the requirements of the job. Give a higher score if the candidate matches the requirements, and a lower score if the candidate does not match any of the requirements.

    Communication Skills:
    Communication Skills: Evaluate the candidate's resume to assess their ability to convey information clearly and concisely. Look for well-structured sentences, organized bullet points, consistent formatting, appropriate font sizes, clear section headings, and coherent descriptions of their experiences and achievements. Check for proper grammar, punctuation, and spelling throughout the resume. Give a higher score if it meets a high standard, and much lower score if it is below average.

    """
    factors = """
    Relevant experience, Title, Responsibilities performed, Preferred Industry, Brand:130
    Education:20
    Learnability, Growth, Accomplishments:20
    Stability, Adaptability:20
    People Management Experience:20
    Programming Languages and Software:20
    Communication Skills:20
    """
    system_prompt = f"""You are a recruiter whose job is to analyse the resume and assess it for a given Job description.
    Below are all the factors and maximum score possible for each factor on which you will assess a candidature.
    {factors}
    Give me a score for each factor out of maximum score and also provide a brief explanation for the score.

    Calculate the percentage score out of 100 for the candidature.

    Refer the below definitions for the factors:
    {definitions}
    Job Description Text:
    ```{jp_text}```
    Resume Text:
    ```{ja_text}```
    Make sure output is valid JSON with the following format:
    {{
        "factors": [
           {{   "factor": "factor name"
                "score": score/maximum score,
                "explanation": "The candidate has a good experience in the field."
            }},
            //REPEAT FOR ALL FACTORS

        ],
        "calculations": [{{
            "factor": "factor name",
            "score": "score/maximum score",
            factor: score/maximum score, ...",

        }},]

        "total_score": "sum of scores of all factors/250",
        "percentage_score": "score out of 100",
        "final_score_explanation": ""
        "final_score": "Should not be more than 100",

    }}
    """
    # logger.debug(system_prompt)
    return system_prompt
