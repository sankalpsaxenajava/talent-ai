from loguru import logger

from intai.ml.llm_client import LLMClient
from intai.ml.utils.llm_types import LLMModelType
from .embedding_utils import save_updated_embeddings_and_skills
from .ai_prompt import MatchTitleAIPrompt
from intai.config import load_config_files
from intai.utils.util import WorkType
import numpy as np
from scipy.spatial.distance import cosine
import json
import os


def get_ideal_candidate_score_for_job(
    skills, overall_years_of_experience, weightage_dict
):
    """Get the ideal candidate score for this job.

    Returns a tuple of
    (total_cum_score:float, cum_skill_score:{"string": float})
    """
    total_cumulative_score = 0
    skill_cumulative_scores = {}
    if overall_years_of_experience is None or overall_years_of_experience == 0:
        overall_years_of_experience = 1
        logger.warning(
            f"Overall Experience is None or 0. Setting to 1 {overall_years_of_experience}"
        )
    logger.info(
        f"Skills: {skills}, Overall Years of Experience:"
        f" {overall_years_of_experience}, Weightage Dictionary:"
        f" {weightage_dict}"
    )
    for skill in skills:
        # Convert score from string percentage to a float
        # score_percentage = skill["score"].strip('%')
        # score = float(score_percentage) / 100

        # ignoring GPT score and using only weightage
        score = 1

        # Initialize cumulative score for this skill
        cumulative_score = 0

        # Calculate weighted cumulative score for each year of experience
        for year in range(1, overall_years_of_experience + 1):
            year_str = str(year)
            weightage = weightage_dict.get(
                year_str, 1
            )  # Default weightage is 1 if not defined
            cumulative_score += score * weightage
        logger.info(
            f"Skill: {skill['skillName']}, Cumulative Score: {cumulative_score}, overall_years_of_experience: {overall_years_of_experience}"
        )
        # Add this skill's cumulative score to the total
        total_cumulative_score += cumulative_score

        # Store the individual cumulative score in the dictionary
        skill_cumulative_scores[skill["skillName"]] = cumulative_score
    logger.info(
        f"Total Cumulative Score: {total_cumulative_score}, Skill Cumulative Scores: {skill_cumulative_scores}"
    )
    return total_cumulative_score, skill_cumulative_scores


def match_certificate_skills_with_jd_skills(certificate_skills, jd_skills, company_id, session_id):
    """Certification Skills is a List of JobApplicationCertification
    certificate_skills is list of skill names: [str] and jd_skills is also list of
    jd skills names : [str]

    Return True or false for if there is a match.

    """
    logger.info(f"Certificate Skills: {certificate_skills}, JD Skills: {jd_skills}")
    certificate_embeddings = {}
    new_skills = []

    new_embeddings = []
    # Load the config files for embeddings and lookup
    (
        cluster_embeddings,
        embeddings,
        cluster_names,
        skill_lookup,
        unique_skills_lookup,
        weightage_dict,
    ) = load_config_files()

    ai_client = LLMClient(model=LLMModelType.EMBEDDING_ADA, session_id=session_id, client_id=company_id)
    for cert_skill in certificate_skills:
        if cert_skill.lower() in unique_skills_lookup:
            logger.info(f"Certificate Skill [{cert_skill.lower()}] found in lookup")
            index = unique_skills_lookup.index(cert_skill.lower())
            certificate_embeddings[cert_skill.lower()] = embeddings[index]
        else:
            logger.info(
                f"Certificate Skill {cert_skill.lower()} is not found in lookup"
            )
            new_embedding = ai_client.get_embeddings(cert_skill.lower())
            certificate_embeddings[cert_skill.lower()] = new_embedding
            new_skills.append(cert_skill.lower())
            new_embeddings.append(new_embedding)

    skill_list_embeddings = {}
    for skill in jd_skills:
        if skill.lower() in unique_skills_lookup:
            logger.info(f"JD Skill {skill.lower()} found in lookup")
            index = unique_skills_lookup.index(skill.lower())
            skill_list_embeddings[skill.lower()] = embeddings[index]
        else:
            logger.info(f"JD Skill {skill.lower()} is not found in lookup")
            new_embedding = ai_client.get_embeddings(skill.lower())
            skill_list_embeddings[skill.lower()] = new_embedding
            new_skills.append(skill.lower())
            new_embeddings.append(new_embedding)

    # check if new_skills is not empty
    if new_skills:
        updated_skills = unique_skills_lookup + new_skills
        updated_embeddings = np.vstack((embeddings, new_embeddings))
        save_updated_embeddings_and_skills(
            updated_embeddings, updated_skills
        )  # update embedding and skill lookup
    else:
        logger.info(f"No New Skills found for embedding Lookup")

    has_shown_learnability = False
    for cert_skill, cert_embedding in certificate_embeddings.items():
        for skill, skill_embedding in skill_list_embeddings.items():
            distance = cosine(cert_embedding, skill_embedding)
            logger.debug(
                f"Distance between Certificate Skill: {cert_skill} and JD Skill: {skill} is {distance}"
            )
            if distance < float(os.getenv("distance_based_threshold")):
                logger.info(
                    f"JD Skill {skill} and Certificate Skill {cert_skill} is a match with the distance {distance}"
                )
                has_shown_learnability = True
                break
    logger.info(f"learnability: {has_shown_learnability}")
    return has_shown_learnability


def ja_get_matching_skills(ja_skills, jd_skills, client_id, session_id):
    """Get the matching skills with jd skills
    ja_skills is list of JobApplicationSkill
    jd_skills is list of skills [skill:str]"""
    matching_skills = {}
    new_skills = []
    new_embeddings = []
    candidate_embeddings = {}
    (
        cluster_embeddings,
        embeddings,
        cluster_names,
        skill_lookup,
        unique_skills_lookup,
        weightage_dict,
    ) = load_config_files()
    ai_client = LLMClient(model=LLMModelType.EMBEDDING_ADA, session_id=session_id, client_id=client_id)
    for ja_skill in ja_skills:
        if ja_skill.skill_name.lower() in unique_skills_lookup:
            logger.info(f"Skill {ja_skill.skill_name.lower()} found in the lookup")
            index = unique_skills_lookup.index(ja_skill.skill_name.lower())
            candidate_embeddings[ja_skill.skill_name.lower()] = embeddings[index]
        else:
            logger.info(
                f"Skill {ja_skill.skill_name.lower()} not found in the lookup, creating embedding"
            )
            new_embedding = ai_client.get_embeddings(ja_skill.skill_name.lower())
            candidate_embeddings[ja_skill.skill_name.lower()] = new_embedding
            # Update skills and embeddings
            new_skills.append(ja_skill.skill_name.lower())
            new_embeddings.append(new_embedding)

    for req_jd_skill in jd_skills:
        matching_skills_list = []

        for ja_skill in ja_skills:
            cand_embedding = candidate_embeddings[ja_skill.skill_name.lower()]
            if req_jd_skill.lower() in unique_skills_lookup:
                index = unique_skills_lookup.index(req_jd_skill.lower())
                req_embedding = embeddings[index]
            else:
                new_embedding = ai_client.get_embeddings(req_jd_skill.lower())
                req_embedding = new_embedding
                # Update skills and embeddings
                new_skills.append(req_jd_skill.lower())
                new_embeddings.append(new_embedding)
            distance = cosine(req_embedding, cand_embedding)
            if distance < float(os.getenv("distance_based_threshold")):
                matching_skills_list.append(
                    (
                        ja_skill.skill_name.lower(),
                        ja_skill.score,
                        round(distance, 2),
                    )
                )

        if matching_skills_list:
            matching_skills[req_jd_skill.lower()] = matching_skills_list
        else:
            logger.info(f"No matching skills found for required skill: {req_jd_skill}")

    if new_skills:
        updated_skills = unique_skills_lookup + new_skills
        updated_embeddings = np.vstack((embeddings, new_embeddings))
        save_updated_embeddings_and_skills(updated_embeddings, updated_skills)
    else:
        logger.info("No New Skills found for embedding Lookup")

    return matching_skills


def ja_select_next_skill(ja_skills, ja_used_skills):
    """Select the next application skill not already used."""
    selected_skill = None
    ja_sorted_skills = sorted(ja_skills, key=lambda x: (-x[1], x[2]))
    for ja_skill, score, distance in ja_sorted_skills:
        if ja_skill not in ja_used_skills:
            selected_skill = ja_skill
            break

    if selected_skill is None:
        selected_skill = ja_sorted_skills[0][0]
        logger.debug(
            f"selected skill is None so selecting first skill. {selected_skill}"
        )

    return selected_skill


def ja_match_title_with_jd(ja_experiences, jp_job_title, client_id, session_id):
    """Match title with job description.

    Args: ja_experineces is list of JobApplicationExperiences (max 3)
          jp_job_title is the job title from jd.

    Returns bool
    """
    if ja_experiences is not None:
        ja_titles = [exp.title for exp in ja_experiences]
        ja_titles_str = ",".join(ja_titles)
        logger.info(f"ja_titles: {ja_titles_str} # jb_job_title: {jp_job_title}")

        prompt = MatchTitleAIPrompt(jp_title=jp_job_title, ja_titles=ja_titles_str)
        ai_client = LLMClient(session_id=session_id, client_id=client_id)
        response = ai_client.get_model_response(prompt)

        logger.debug(f"Response from OpenAI:\n {response}\n")
        assert response is not None and len(response) > 0

        response_dict = json.loads(response)
        if "result" in response_dict:
            return response_dict["result"]

    return False


def ja_match_industry_with_jd(ja_experiences, org_industry_segment):
    """Match industry with job description.

    Args: ja_experineces is list of JobApplicationExperiences (max 3)
          org_industry_segment is None or string

    Returns bool
    """
    logger.info(
        f"experiences: {ja_experiences}; org_ind_segment: {org_industry_segment}"
    )
    if org_industry_segment is not None and ja_experiences is not None:
        # Check if organizationsIndustrySegment is a single string,
        # if so, convert it to a list
        if isinstance(org_industry_segment, str):
            org_industry_segment = (
                [org_industry_segment.lower()]
                if org_industry_segment is not None
                else []
            )
        elif isinstance(org_industry_segment, list):
            # Filter out None values and convert everything to lowercase
            organizationsIndustrySegment = [
                seg.lower() for seg in org_industry_segment if seg is not None
            ]

        # Convert the list of organization's industry segments to a
        # set for efficient searching
        industry_set = set(org_industry_segment)

        logger.info(f"Checking industry match for industries: {industry_set}")

        # Loop through each experience to check for a match
        for experience in ja_experiences:
            industry = experience.industry
            # logger.debug(f"Checking industry: {experience.industry}")
            if industry is not None and industry.lower() in industry_set:
                return True

    return False


def ja_calculate_matching_skill_score(ja_skills, jd_skills, session_id, client_id):
    """Find the distanced based on job application with jd_skills.

    ja_skills is a list of JobApplicationSkill model
    jd_skills is a list of skill names.
    returns final candidate score and matching skills.
    """
    matching_skills = ja_get_matching_skills(ja_skills, jd_skills, session_id=session_id, client_id=client_id)
    logger.info(f"Matching Skills: {matching_skills}")

    overall_score = 0
    ja_used_skills = {}

    for req_skill, ja_skill_names_scores in matching_skills.items():
        if len(ja_skill_names_scores) == 1:
            selected_skill = ja_skill_names_scores[0][0]
            ja_used_skills[req_skill] = selected_skill
            overall_score += ja_skill_names_scores[0][1]
        else:
            selected_skill = ja_select_next_skill(
                ja_skill_names_scores, set(ja_used_skills.values())
            )
            ja_used_skills[req_skill] = selected_skill
            overall_score += next(
                score
                for skill, score, _ in ja_skill_names_scores
                if skill == selected_skill
            )

    # Logging the used job application skills
    logger.info(f"Used JobApplication Skills: {ja_used_skills} ")

    return overall_score, matching_skills


def ja_calculate_matching_percentage(ja_matching_score, jd_ideal_score):
    """Calculate the matching percentage based on job application
    matching score (based on skills) and jd ideal score."""
    # Avoid division by zero
    if jd_ideal_score == 0:
        return 0
    else:
        jd_ideal_score = float(jd_ideal_score)
        ja_matching_score = float(ja_matching_score)
        percentage = (ja_matching_score / jd_ideal_score) * 100
        return round(percentage, 2)  # rounding to 2 decimal places


def ja_calculate_matching_percentage(ja_matching_score, jd_ideal_score):
    """Calculate the matching percentage based on job application
    matching score (based on skills) and jd ideal score."""
    # Avoid division by zero
    if jd_ideal_score == 0:
        return 0
    else:
        jd_ideal_score = float(jd_ideal_score)
        ja_matching_score = float(ja_matching_score)
        percentage = (ja_matching_score / jd_ideal_score) * 100
        return round(percentage, 2)  # rounding to 2 decimal places


def ja_get_bucket(ja_matching_percentage):
    """Get the bucket based on percentage of matching."""
    if ja_matching_percentage >= 90:
        bucket = "A"
    elif 75 <= ja_matching_percentage < 90:
        bucket = "B"
    elif 60 <= ja_matching_percentage < 75:
        bucket = "C"
    elif 40 <= ja_matching_percentage < 60:
        bucket = "D"
    else:
        bucket = "E"
    return bucket


def ja_calculate_distance_based_score(experience_skills, required_skill_list, session_id, client_id):
    """Calculate the distance based candidate score.
    Experience_skills is a list of (ExperiienceSkillnames:str, scores:float)

    """
    matching_skills = ja_get_matching_skills(experience_skills, required_skill_list, session_id=session_id, client_id=client_id)
    logger.info(f"Matching Skills: {matching_skills} ")

    overall_score = 0
    used_candidate_skills = {}

    for req_skill, cand_skills_list in matching_skills.items():
        if len(cand_skills_list) == 1:
            selected_skill = cand_skills_list[0][0]
            used_candidate_skills[req_skill] = selected_skill
            overall_score += cand_skills_list[0][1]
        else:
            selected_skill = ja_select_next_skill(
                cand_skills_list, set(used_candidate_skills.values())
            )
            used_candidate_skills[req_skill] = selected_skill
            overall_score += next(
                score for skill, score, _ in cand_skills_list if skill == selected_skill
            )

    # Logging the used candidate skills
    logger.info(f"Used Candidate Skills: {used_candidate_skills} ")

    return overall_score

def get_skill_score_job(skills):
        """Get the score for skills."""
        logger.debug(f"skills: {skills}")
        skill_score_dict = {}
        for skill in skills:
            # TODO #A Calculate the score here based on experience
            # number of years etc.
            skill_score_dict[skill] = 0.5

        return skill_score_dict