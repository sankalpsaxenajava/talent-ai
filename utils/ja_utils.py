import json
from intai.ml.llm_client import LLMClient
from intai.models.models import JobApplicationScore
from typing import Any
from intai.ml.ai_prompt import (
    FactorAnalysisAIPrompt,
    JobApplicationAIPrompt,
    JobApplicationMatchSummaryAIPrompt,
    JobApplicationBasicsAIPrompt
)
from intai.ml.utils.llm_types import LLMResponseType

from loguru import logger

def ja_parse_jd(jd_json):

        parsed_jd = json.loads(jd_json)
        
        assert parsed_jd is not None and "skills" in parsed_jd
        # TODO: Q: Should we handle when JD doesn't have skills?

        # NOTE: We are not using standard skills anymore so we currently copy it.
        # Should we just store the standard skill in parsed_jd?
        jd_skills = parsed_jd["skills"]
    
        # collect skill names where skillName is present in parsed_jd skill?
        # Why would it not be present?
        jd_skill_names = [
            skill["skillName"] for skill in jd_skills if "skillName" in skill
        ]

        organizationsIndustrySegment = None
        job_title = None
        if "basics" in parsed_jd and len(parsed_jd["basics"]) > 0:
            basics_first = parsed_jd["basics"][0]
            if "organizationsIndustrySegment" in basics_first:
                organizationsIndustrySegment = basics_first["organizationsIndustrySegment"]
            if "jobTitle" in basics_first:
                job_title = basics_first["jobTitle"]

        # Find the overall years of experience
        assert "overallYearsOfExperience" in parsed_jd
        overall_experience = parsed_jd["overallYearsOfExperience"]

        # Find the people management experience
        assert "peopleManagementExperience" in parsed_jd
        management_experience = parsed_jd["peopleManagementExperience"]

        return organizationsIndustrySegment, job_title, jd_skill_names, overall_experience, management_experience

def ja_parse_application(ja_extracted_text: str, session_id, client_id):
        """Extract the entities from JobApplication & store in the database.

        This will call openAI and get the parsed json entities for
        job application.
        """
        # TODO #C Potentially refactor extract_entities
        # into a common utility method later.

        try:
            if ja_extracted_text is None or len(ja_extracted_text) == 0:
                raise Exception("Extracted text is null. Check if previous task to _extract_text finished succesfully.")

            # Call OpenAI directly. Previously we were using the cached entities but now we are always call openAI.
            # NOTE: For repeat calls if job posting is not changing in future we can store a checksum in db and decide that
            # to determine whether to call openai or not.
            ai_client = LLMClient(session_id=session_id, client_id=client_id)
            prompt = JobApplicationAIPrompt(ja_text=ja_extracted_text)
            import timeit
            start_time = timeit.default_timer()
            extracted_entities = ai_client.get_model_response(ai_prompt=prompt, response_type=LLMResponseType.JSON_OBJECT)
            end_time = timeit.default_timer()
            execution_time = end_time - start_time
            logger.warning(f"[[[[[[[[[ ------   Execution time for resume parsing get_model_response: {execution_time} seconds  ------ ]]]]]]]]")

            if extracted_entities is not None and len(extracted_entities) > 0:
                logger.debug(f"len of Extracted ENtities: {len(extracted_entities)}")
                logger.debug(f"Extracted ENtities: {extracted_entities}")

                extracted_entities_dict = json.loads(
                    extracted_entities
                )  # Can throw Json decode exception
                extracted_entities = json.dumps(
                    extracted_entities_dict
                )  # Trim the json by dumping from dict.
                logger.debug(f"Length after trimming is {len(extracted_entities)}")

            return extracted_entities
            
        except Exception as err:
            logger.error(
                f"Exception while extracting save entities: {err}\n ja_text: {ja_extracted_text}"
            )
            raise err

def ja_get_basics (ja_text: str, session_id, client_id):
    """ Get the basics from openai for this resume and return"""
    try:
        prompt = JobApplicationBasicsAIPrompt(ja_text=ja_text)
        ai_client = LLMClient(session_id=session_id, client_id=client_id)
        response = ai_client.get_model_response(prompt, response_type = LLMResponseType.JSON_SCHEMA, response_json=prompt.response_schema)
        logger.debug(f"Job Application Basics Response from OpenAI:\n {response}")
        return response
    except Exception as err:
        logger.error(
            f"Exception while extracting basic ja entity: {err}\n ja_text: {ja_text}"
        )
        raise err   
        
def ja_calculate_factor_score(ja_text: str, jp_text: str, jp_parsed: Any, session_id, client_id):
    """Calculate the ranking based on factors.

    """
    try:
        logger.debug(f"Calculating factor score for ja_text: {ja_text} jp_text: {jp_text} jp_parsed: {jp_parsed}")
                
        factor_prompt = FactorAnalysisAIPrompt(jp_text=jp_text, ja_text=ja_text)
        
        ai_client = LLMClient(session_id=session_id, client_id=client_id)
        
        factor_response = ai_client.get_model_response(factor_prompt)
        
        logger.debug(f"Factor Analysis Response from OpenAI:\n {factor_response}")

        factor_data = json.loads(factor_response)
        
    
        logger.debug(factor_data["final_score_explanation"])
        logger.debug(factor_data["calculations"])
        logger.debug(factor_data["final_score"])
        ja_get_adjusted_factor_score(factor_data=factor_data, parsed_jd=jp_parsed)
        logger.debug(f"factor_data after adjusting: {factor_data}")
        
        return factor_data
    except Exception as err:
        logger.error(
            f"Exception while calculating factor score: {err}\n ja_text={ja_text}\n jp_text={jp_text}\n jp_parsed = {jp_parsed}\n factor_data: {factor_data}"
        )
        raise err

def ja_get_score_summary(ja_text: str, jp_text: str, session_id, client_id) -> str:
    summary_prompt = JobApplicationMatchSummaryAIPrompt(jp_text=jp_text, ja_text=ja_text)
    ai_client = LLMClient(session_id=session_id, client_id=client_id)
    
    summary_response = ai_client.get_model_response(summary_prompt)
    summary_data = json.loads(summary_response)
    
    score_summary = json.dumps(summary_data["summary"])
    logger.debug(f"Summary: {score_summary}")
    return score_summary

def ja_get_adjusted_factor_score(factor_data, parsed_jd):
    """Get the adjusted score in case people management and software skills are
    required in job description.
    """
    logger.info(f"Initial factor data: {factor_data}")
    adj_factor_score:float = float(factor_data["final_score"])
    factor_json=factor_data["calculations"]
    logger.info(f"Factor json: {factor_json}")
    logger.info(f"People Management is jd: {parsed_jd['peopleManagementExperience']}")
    if ("peopleManagementExperience" not in parsed_jd or not parsed_jd["peopleManagementExperience"]):
        # if the people management experience not in jd then remove from adjusted score.
        assert len(factor_json) > 0 and "score" in factor_json[0]

        management_score = [x["score"] for x in factor_json if "People Management Experience" in x["factor"]]
        logger.info(f"Management score is: {management_score}")
        assert (len(management_score) > 0 and "/" in management_score[0])
        mgmt_score_parts = management_score[0].split("/")

        # TODO: Should we get by adding factor scores though we know its sum is always 250.0
        assert (len(mgmt_score_parts) > 1)
        adj_mgmt_score = float(mgmt_score_parts[0]) /2.50
        adj_factor_score = adj_factor_score - adj_mgmt_score
        logger.info(f"adjust Management score for candidate is: {adj_mgmt_score}, adjusted_score: {adj_factor_score}, factor_score: {factor_data['final_score']}")

    software = "softwareToolsOrProgrammingLanguages"
    logger.info(f"Software and programming language in jd: {parsed_jd[software]}")
    if (software not in parsed_jd or len(parsed_jd[software]) == 0
        or "name" not in parsed_jd[software][0] or
        (len(parsed_jd[software]) == 1 and parsed_jd[software][0]["name"] == "null")):
        # if the software and prog. experience not in jd then remove from adjusted score.
        assert len(factor_json) > 0 and "score" in factor_json[0]

        software_score = [x["score"] for x in factor_json if "Programming Languages and Software" in x["factor"]]
        logger.info(f"Software/Prog lang score is: {software_score}")
        assert (len(software_score) > 0 and "/" in software_score[0])
        soft_score_parts = software_score[0].split("/")

        # TODO: Should we get by adding factor scores though we know its sum is always 250.0
        assert (len(soft_score_parts) > 1)
        adj_soft_score = float(soft_score_parts[0]) /2.50
        adj_factor_score = adj_factor_score - adj_soft_score
        logger.info(f"adjust Management score for candidate is: {software_score}, adjusted_score: {adj_factor_score}, factor_score: {factor_data['final_score']}")

    factor_data["final_score"] = adj_factor_score

