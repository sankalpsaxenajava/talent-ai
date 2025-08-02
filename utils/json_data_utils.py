from datetime import datetime
import json
from intai.models.models import (
    JobApplicationAddress,
    JobApplicationAward,
    JobApplicationCertification,
    JobApplicationCertificationSkill,
    JobApplicationEducation,
    JobApplicationExperience,
    JobApplicationInterest,
    JobApplicationLanguage,
    JobApplicationPublication,
    JobApplicationVolunteer,
    JobApplicationProject,
)
from intai.schemas.candidate_fe import CandidateFrontEnd
from intai.utils.str_utils import check_str_not_null
from intai.schemas.job_application import JobApplicationDetail
from intai.config import load_weightage_config
import traceback

from loguru import logger


CONSIDER_INTERNSHIP = False


def _floor_half_year(value):
    """Multiply the value by 2 to convert it to half-year units.

    make sure value is number it can be string also eg "2"
    """
    try:
        if not isinstance(value, (int, float)):
            value = float(value)

        half_years = value * 2

        # Calculate the floor value of half-years
        floor_value = int(half_years)

        # Convert the floor value back to the original unit (6 months)
        result = floor_value / 2
    except Exception as e:
        logger.error(f"Error in floor_half_year: {e}")
        result = 0
    return result


def ja_calculate_overall_years_of_experience(data):
    """Calculate overall years of experience from ja"""
    try:
        basics = data["basics"]
        total_years = basics["totalExperienceInYears"]
        if total_years is not None and len(total_years) > 0:
            total_years = float(total_years)
        else:
            total_years = 0

        logger.debug(f"OverallYearsOfExperience: {round(total_years,2)}")
        return round(total_years, 2)
    except Exception as e:
        logger.error(e)


def ja_calculate_avg_tenure_in_organization(data):
    """Calcualte average tenure in organization."""
    if CONSIDER_INTERNSHIP == False:
        unique_organizations = set(
            exp["company"]
            for exp in data["experience"]
            if exp["employment_type"] != "Internship"
        )
    else:
        unique_organizations = set(exp["company"] for exp in data["experience"])

    # Calculating total number of organizations
    total_organizations = len(unique_organizations)
    overall_years_of_experience = ja_calculate_overall_years_of_experience(data)

    if overall_years_of_experience is not None and total_organizations > 0:
        # Calculating average tenure in organization in years
        average_tenure_in_organization = (
            overall_years_of_experience / total_organizations
        )
    else:
        logger.warning(
            f"Unexpected error: overall_years_of_experience [{overall_years_of_experience}] is None or total_organizations [{total_organizations}] is 0."
        )

    return round(average_tenure_in_organization, 2)


def ja_calculate_avg_tenure_in_roles(data):
    """Calculate the avg tenure in roles for job application."""
    if CONSIDER_INTERNSHIP == False:
        unique_roles = set(
            exp["title"]
            for exp in data["experience"]
            if exp["employment_type"] != "Internship"
        )
    else:
        unique_roles = set(exp["title"] for exp in data["experience"])

    # Calculating total number of unique roles
    total_unique_roles = len(unique_roles)
    overall_years_of_experience = ja_calculate_overall_years_of_experience(data)

    if overall_years_of_experience is not None and total_unique_roles > 0:
        # Calculating average tenure in role in years
        average_tenure_in_role = overall_years_of_experience / total_unique_roles

    else:
        logger.warning(
            f"overall_years_of_experience [{overall_years_of_experience}] is None or total_unique_roles[{total_unique_roles}] is 0."
        )
    return round(average_tenure_in_role, 2)


def ja_extract_skills_from_certifications_and_trainings(
    certifications_data, job_application_data
):
    """Extract skills from certification and training."""
    certification_skills = []
    for cert_id, cert_name in certifications_data:
        # Search for the certification in the job_application data
        for job_application_cert_data in job_application_data:
            if job_application_cert_data["name"] == cert_name:
                certification_skills.append(
                    (cert_id, cert_name, job_application_cert_data["skills"])
                )
                break
    return certification_skills


def ja_get_volunteers_from_json(json_data, company_id):
    """Get the volunteer from json."""
    volunteers_details_list = []

    volunteers = json_data.get("volunteer", [])

    if check_str_not_null(volunteers):
        for volunteer in volunteers:
            organization = volunteer.get("organization")
            position = volunteer.get("position")
            if check_str_not_null(organization) or check_str_not_null(position):
                ja_volunteer = JobApplicationVolunteer(
                    company_id=company_id,
                    organization=organization,
                    position=position,
                    start_date=volunteer.get("start"),
                    end_date=volunteer.get("end"),
                )
                volunteers_details_list.append(ja_volunteer)

        return volunteers_details_list
    else:
        return None


def ja_get_publications_from_json(json_data, company_id):
    """Get the publications for job application from json."""
    publications_details_list = []

    publications = json_data.get("publications", [])
    if check_str_not_null(publications):
        for publication in publications:
            publication = JobApplicationPublication(
                company_id=company_id,
                title=publication.get("title"),
                publisher=publication.get("publisher"),
                issue_date=publication.get("release date"),
                description=publication.get("description"),
            )
            publications_details_list.append(publication)

        return publications_details_list
    else:
        return None


def ja_get_awards_from_json(json_data, company_id):
    """Get the awards for job application from json."""
    awards_details_list = []

    awards = json_data.get("awards", [])
    logger.debug(f"awards: {awards}")
    if check_str_not_null(awards):
        for award in awards:
            if award is not None:
                title = award.get("title")
                if check_str_not_null(title):
                    ja_award = JobApplicationAward(
                        company_id=company_id,
                        title=title,
                        date_award=award.get("date"),
                        award_authority=award.get("awarder"),
                    )
                    awards_details_list.append(ja_award)

        return awards_details_list
    else:
        return None


def ja_get_certifications_from_json(json_data, company_id):
    """Get the certification and skills for job application from json.

    Return: ([JobApplicationCertification], {"Cert title: str":List("SkillName:str"})
    """
    certifications_details_list = []
    skills_cert_dict = {}

    certifications = json_data.get("certificationsAndTrainings", [])
    if check_str_not_null(certifications):
        for certification in certifications:
            title = certification.get("name")
            if check_str_not_null(title):
                ja_certification = JobApplicationCertification(
                    company_id=company_id,
                    title=certification.get("name"),
                    issue_authority=certification.get("issuer"),
                    issue_date=certification.get("issued date"),
                )
                certifications_details_list.append(ja_certification)
                # TODO #D: Do we need to return the skill_score_dict as we
                # are passing by reference.
                skills_cert_dict = ja_get_certification_skills_from_json(
                    certification, ja_certification, company_id, skills_cert_dict
                )

        return certifications_details_list, skills_cert_dict
    else:
        logger.debug("No Certification data found.")
        return None, None


def ja_get_certification_skills_from_json(
    json_certification_data, ja_certification, company_id, ret_skills_dict
):
    """Get the certification  skills for job application from json.
    Args:
    json_certification_data: Json Certification dictionary
    ja_certification: JobApplicationCertification Object
    company_id: company id for this application
    ret_score_dict: Skills score dict mapping cert title(str) to list of skillname(str).

    NOTE: Returns the ret_score_dict as well.

    """
    if (
        len(json_certification_data) > 0
        and json_certification_data["name"] == ja_certification.title
        and json_certification_data["skills"] is not None
    ):
        # Search for certification in resume data
        # NOTE: skills is already a list of skills in json dict.
        ret_skills_dict[ja_certification.title] = json_certification_data["skills"]
        logger.info(
            f"Added {ja_certification.title} cert with skills {json_certification_data['skills']}"
        )
    else:
        logger.error(
            "Unexpected data: Json certification data not matching ja_certification or is null. "
        )

    return ret_skills_dict


def ja_get_languages_from_json(json_data, company_id):
    """get the languages in job application from json."""
    resume_languages_list = []

    languages = json_data.get("languages", [])
    if check_str_not_null(languages):
        for language in languages:
            language_name = language.get("name")
            if check_str_not_null(language_name):
                language = JobApplicationLanguage(
                    company_id=company_id,
                    language_name=language_name,
                    fluency_level=language.get("fluency"),
                )
                resume_languages_list.append(language)

        return resume_languages_list
    else:
        return None


def ja_get_interests_from_json(json_data, company_id):
    """Get the awards for job application from json."""
    interests_details_list = []

    interests = json_data.get("interests", [])
    if check_str_not_null(interests):
        for interest in interests:
            if check_str_not_null(interest):
                interest = JobApplicationInterest(company_id=company_id, title=interest)
                interests_details_list.append(interest)

        return interests_details_list
    else:
        return None


def ja_get_education_from_json(json_data, company_id:int) -> list[JobApplicationEducation]:
    """
    Get the education details for a job application from the provided JSON data.
    
    Args:
        json_data (dict): The JSON data containing the job application information.
        company_id (int): The ID of the company associated with the job application.
    
    Returns:
        list[JobApplicationEducation]: A list of `JobApplicationEducation` objects representing the education details for the job application.
    """
    education_details_list = []

    educations = json_data.get("education", [])

    for edu_entry in educations:
        degree_level = edu_entry.get("degree_level")
        degree_field = edu_entry.get("degree")
        institution = edu_entry.get("institution")
        if (
            check_str_not_null(degree_level)
            and check_str_not_null(degree_field)
            and check_str_not_null(institution)
        ):
            start_date = edu_entry.get("start_date")
            end_date = edu_entry.get("end_date")
            if start_date == "null":
                start_date = ""
            if end_date == "null":
                end_date = ""
            education = JobApplicationEducation(
                company_id=company_id,
                institution=institution,
                start_date=start_date,
                end_date=end_date,
                degree_level=degree_level,
                degree_field=degree_field,
            )
            education_details_list.append(education)

    return education_details_list


def ja_get_projects_from_json(json_data, company_id):
    """Get the projects for this job application from json."""
    projects_details_list = []

    projects = json_data.get("projects", [])
    logger.info(projects)
    if check_str_not_null(projects):
        for project in projects:
            title = project.get("title")
            if check_str_not_null(title):
                project_dict = JobApplicationProject(
                    company_id=company_id,
                    title=title,
                    start_date=project.get("start date"),
                    end_date=project.get("end date"),
                    tech_stack=project.get("techstack"),
                    public_urls=project.get("github link"),
                )
                projects_details_list.append(project_dict)

        return projects_details_list
    else:
        return None


def ja_calculate_years_of_experience(experience):
    """Calcualte the years of experience based on start and end date."""
    start = experience.get("start")
    end = experience.get("end")
    years_of_experience = experience.get("yearsOfExperience")
    logger.debug(f"start: {start}, end: {end}, years_exp: {years_of_experience}")

    # Check if 'start' or 'end' are 'null' or absent, and 'yearsOfExperience' is provided
    if (
        (start == "null" or not start) or (end == "null" or not end)
    ) and years_of_experience:
        try:
            # Ensure that years_of_experience is a float
            return float(years_of_experience)
        except ValueError as e:
            logger.error(f"Error converting yearsOfExperience to float: {e}")
            return 0

    if start and end and start != "null" and end != "null":
        try:
            start_date = datetime.strptime(start, "%m-%Y")
            end_date = datetime.strptime(end, "%m-%Y")
            total_months = (end_date.year - start_date.year) * 12 + (
                end_date.month - start_date.month
            )
            return round(total_months / 12, 1)
        except ValueError as e:
            logger.error(f"Date parsing error: {e}")
            return 0  # Return 0 or handle error as needed

    # If dates are invalid or missing and no valid years of experience is provided, handle as needed
    logger.warning("Insufficient or invalid data to calculate years of experience.")
    return 0

def ja_populate_from_basics(json_basics, candidate_fe: CandidateFrontEnd):
    """Populate the candidate_fe object with the basics from the json_data."""
    candidate_fe.firstName = json_basics.get("firstName")
    candidate_fe.lastName = json_basics.get("lastName")
    candidate_fe.email = json_basics.get("email")
    candidate_fe.phone = json_basics.get("phone")
    candidate_fe.yearsOfExperience = json_basics.get("experienceInYears")
    candidate_fe.linkedInUrl = json_basics.get("linkedin")
    candidate_fe.currentCompany = json_basics.get("currentCompany")
    candidate_fe.currentDesignation = json_basics.get("currentDesignation")
    candidate_fe.latestDegree = json_basics.get("latestDegree")
    candidate_fe.yearOfGraduation = json_basics.get("yearrOfGraduation")
    candidate_fe.latestInstitution = json_basics.get("latestInstitution")
    candidate_fe.location = json_basics.get("location")

def ja_get_experience_from_json(json_data, company_id) -> tuple[list[JobApplicationExperience], dict[str, float]]:
    """Get the experience for job application from json.

    NOTE: Experience also contains skill so parse the skills from
    experience section as well.
    Returns ([JobApplicationExperience], {"SkillName:String": score:float})
    """
    experiences_list :list[JobApplicationExperience] = []

    # List of dictionary of each skill and scores
    # [{"skillname": 34.2}]
    skills_score_dict = {}
    current_year = 0.5
    experience_details = json_data.get("experience", [])
    if (
        experience_details is not None
        and experience_details != "null"
        and len(experience_details) > 0
    ):
        for exp in experience_details:
            start_date = exp.get("start", None)
            if start_date == "null":
                start_date = ""
            end_date = exp.get("end", None)
            if end_date == "null":
                end_date = ""
            years_experience = ja_calculate_years_of_experience(exp)

            ja_experience = JobApplicationExperience(
                company_id=company_id,
                title=exp.get("title"),
                experience_company=exp.get("company"),
                start_date=start_date,
                end_date=end_date,
                description=exp.get("description"),
                years_experience=years_experience,
                industry=exp.get("industry"),
                location=exp.get("location"),
                team_lead_experience=exp.get("teamLeadingExperience"),
                employment_type=exp.get("employment_type"),
            )
            experiences_list.append(ja_experience)

            if start_date is None and end_date is None and years_experience == 0:
                # If dates are missing, process skills from the fixed starting point (0.5)
                # without adjusting current_year
                start_year = 0.5
            else:
                start_year = current_year
                current_year += years_experience

            # TODO #D: Do we need to return the skill_score_dict as we
            # are passing by reference.
            # NOTE: It is modified and returned.
            skills_score_dict = ja_get_experience_skills_from_json(
                exp, ja_experience, company_id, skills_score_dict, start_year
            )

        return experiences_list, skills_score_dict
    else:
        return None, None


def ja_get_yearwise_skills_scores(years_experience, start_year, skills_list):
    """Process and get yearwise skills-score-dict."""

    i = 0
    skills_score_dict = {}
    while i < years_experience:
        for skill in skills_list:
            skill_name = get_json_skip_null(skill, "skillName")
            if skill_name:
                assert skill_name != "null"
                if skill_name not in skills_score_dict:
                    skills_score_dict[skill_name] = {}

                year_key = i + start_year
                # NOTE: Mark the score for this skill and this year
                # to be 1.0
                skills_score_dict[skill_name][year_key] = 1.0

        # After processsing all sills for this year, go to next year.
        i += 0.5
    return skills_score_dict


def ja_get_aggregate_skills_scores(skills_score_yearwise_dict, ret_skills_score_dict):
    """Aggregate the yearwise skills_score_dict.

    Args:
    yearwise_skills_scores_dict:
    Dictionary with {"skill_names:str", {"year:str", score}}

    Returns a dictionary with {"skill_names:str", score}

    """
    # Calculate Skill Scores
    # TODO: Refactor this into a function for easier understanding.
    logger.debug(
        f"skills_score_yearwise_dict is {skills_score_yearwise_dict}; ret_skills_score_dict is {ret_skills_score_dict}"
    )
    try:
        weightage_dict = load_weightage_config()
        max_score = weightage_dict.get("max")
        for skill, yearly_scores in skills_score_yearwise_dict.items():
            logger.debug(f"skill: {skill} # yearl_scores: {yearly_scores}")
            new_score = 0
            for year, _ in yearly_scores.items():
                year_weightage = weightage_dict.get(
                    str(year), max_score
                )  # Handle 'max' key
                new_score += year_weightage
            if skill not in ret_skills_score_dict.keys():
                # TODO #B: We are maxing the max score across experiences for
                # a skill. Verify if its ok.
                # ret_skills_score_dict[skill] = min(max_score, round(new_score, 2))
                ret_skills_score_dict[skill] = round(new_score, 2)
            else:
                # TODO #B: We might be going above all the max score across experiences for
                # a skill if it exists across experiences. Verify if its ok.
                new_score_total = ret_skills_score_dict[skill] + round(new_score, 2)

                logger.debug(
                    f"skill in ret_score_dict already so adding \n ret_score_dict item: {ret_skills_score_dict[skill]} \n skill: {skill} \nnew score: {new_score_total}"
                )
                # max_score_skill = max_score * total years? or get from json
                # ret_skills_score_dict[skill] = min(max_score_skill, new_score_total)
                ret_skills_score_dict[skill] = new_score_total
    except Exception as e:
        logger.error(
            f"Error in calculating final resume scores {e} {traceback.format_exc()}"
        )
    return ret_skills_score_dict


def ja_get_experience_skills_from_json(
    exp_dict, ja_experience, company_id, ret_skill_score_dict, start_year
):
    """Get the experience skills for job application from json.

    Args:
    exp_dict is the json dictionary of specific experience details.
    ja_experience is the jobapplicationExperience object.
    ret_score_dict is dictionary of {"SkillName: Str": score:float}
    start_year is 0.5 if dates are missing or actual start_year based
    on calculations of experience years

    Return: updates the ret_score_dict and returns it.

    """
    logger.debug(f"***** Experience is {ja_experience}")
    years_experience = _floor_half_year(ja_experience.years_experience)
    skills_list = exp_dict.get("skills", [])

    # Process Skills now for experience
    skills_score_yearwise_dict = ja_get_yearwise_skills_scores(
        years_experience, start_year, skills_list
    )
    logger.debug(f"Yearwise skills score is: {skills_score_yearwise_dict}")

    # NOTE ret_skill_score_dict is passed in and modified
    ret_skill_score_dict = ja_get_aggregate_skills_scores(
        skills_score_yearwise_dict, ret_skill_score_dict
    )
    logger.debug(f" Skills score dict is: {ret_skill_score_dict}")
    return ret_skill_score_dict


def ja_get_address_from_json(json_data, company_id):
    """Get the job pplication address from json data.

    Return: List of JobApplicationAddress or empty if none found.
    """
    basics_json = json_data.get("basics", None)
    addresses = basics_json.get("address", [])
    logger.debug(addresses)

    ja_addresses = []
    for address in addresses:
        ja_address = JobApplicationAddress(
            company_id=company_id,
            city=address["city"],
            state=address["state"],
            country=address["country"],
            full_address=str(address),
        )
        ja_addresses.append(ja_address)
    return ja_addresses


def get_json_skip_null(json_data, key: str):
    val = json_data.get(key, None)
    if val == "null":
        val = None
    return val


def ja_get_details_from_json(json_data, json_basics, company_id:int):
    """Get the jobapplicationdetails from the json entities."""
    logger.debug(f"JSON_DATA: {json_data}, json_basics: {json_basics}")
    #basics_json = json_data.get("basics", None)
    # exp_years: float = ja_calculate_overall_years_of_experience(json_data)
    # exp_years = 0 if exp_years is None else exp_years

    ja_details = JobApplicationDetail(company_id=company_id)

    if (json_data) :
        avg_tenure_in_org: float = ja_calculate_avg_tenure_in_organization(json_data)
        avg_tenure_in_org = 0 if avg_tenure_in_org is None else avg_tenure_in_org

        avg_tenure_in_roles: float = (
            ja_calculate_avg_tenure_in_roles(json_data) if not None else 0
        )
        avg_tenure_in_roles = 0 if avg_tenure_in_roles is None else avg_tenure_in_roles
        
        ja_details.summary = json_data.get("summary", None)
        ja_details.software_skills = get_json_skip_null(
                json_data, "softwareToolsOrProgrammingLanguages"
            )
        ja_details.num_promotions = get_json_skip_null(
            json_data, "PromotionsOrRoleChangesInOrganization"
        )
        ja_details.avg_tenure_org_years = avg_tenure_in_org
        ja_details.avg_tenure_role_years = avg_tenure_in_roles
        ja_details.num_awards = get_json_skip_null(json_data, "awardsCount")
        ja_details.cert_education_new_domain = get_json_skip_null(
            json_data, "certificationsOrEducationInNewDomain"
        )
        ja_details.num_published_papers = get_json_skip_null(
            json_data, "papersPublishedCount"
        )
        ja_details.num_patents = get_json_skip_null(json_data, "patentsFiledCount")
        ja_details.num_conf_presentations = get_json_skip_null(
            json_data, "conferencePresentationsCount"
        )
    
    if (json_basics):
        name = get_json_skip_null(json_basics, "firstName") + " " + get_json_skip_null(json_basics, "lastName")
        ja_details.applicant_name = name 
        ja_details.applicant_resume_email = get_json_skip_null(json_basics, "email")
        ja_details.applicant_resume_phone = get_json_skip_null(json_basics, "phone")
        ja_details.applicant_resume_linkedin = get_json_skip_null(json_basics, "linkedin")
        ja_details.experience_years = get_json_skip_null(json_basics, "experienceInYears")

        
    logger.debug(f"JobApplicationDetail: {ja_details}")
    return ja_details
