import os
from pathlib import Path
import json

from dotenv import load_dotenv
from icecream import ic
from intai.ml.scoring_utils import (
    get_ideal_candidate_score_for_job,
    ja_calculate_matching_skill_score,
    match_certificate_skills_with_jd_skills,
    ja_match_industry_with_jd,
    ja_match_title_with_jd,
)
from intai.config import load_weightage_config
from intai.schemas.job_application import JobApplicationSkill, JobApplicationExperience
from intai.models.models import JobApplicationExperienceDb


class TestScoringUtils:
    def setup_class(self):
        load_dotenv()

    def teardown_class(self):
        pass

    def test_get_ideal_candidate_score(self):
        entities_path = Path(os.getenv("TEST_DATA_FOLDER"), "jp_entities.json")
        assert entities_path.exists()
        f = entities_path.open()
        entities = f.read()

        # ic(f"Entities: {entities}")
        json_entities = json.loads(entities)
        ic(json_entities)
        assert "overallYearsOfExperience" in json_entities
        assert "skills" in json_entities
        skills = json_entities["skills"]
        experience = json_entities["overallYearsOfExperience"]
        weightage_dict = load_weightage_config()
        ic(f"{weightage_dict}")
        total_cum_score, skill_cum_scores = get_ideal_candidate_score_for_job(
            skills, experience, weightage_dict
        )

        ic(total_cum_score)
        ic(skill_cum_scores)
        assert total_cum_score > 0
        assert len(skill_cum_scores) > 0

    def test_match_certificate_skills_with_jd_skills(self):
        entities_path = Path(os.getenv("TEST_DATA_FOLDER"), "jp_entities.json")
        assert entities_path.exists()
        f = entities_path.open()
        entities = f.read()

        # ic(f"Entities: {entities}")
        json_entities = json.loads(entities)
        ic(json_entities)
        assert "overallYearsOfExperience" in json_entities
        assert "skills" in json_entities
        jd_skills = json_entities["skills"]
        jd_skill_names = [
            skill["skillName"] for skill in jd_skills if "skillName" in skill
        ]
        learnability = match_certificate_skills_with_jd_skills(
            ["budget", "AWS", "Software Design"], jd_skill_names
        )
        ic(learnability)

    def test_calculate_distance_based_candidate_score(self):
        entities_path = Path(os.getenv("TEST_DATA_FOLDER"), "jp_entities.json")
        assert entities_path.exists()
        f = entities_path.open()
        entities = f.read()

        # ic(f"Entities: {entities}")
        json_entities = json.loads(entities)
        ic(json_entities)
        assert "overallYearsOfExperience" in json_entities
        assert "skills" in json_entities
        jd_skills = json_entities["skills"]
        jd_skill_names = [
            skill["skillName"] for skill in jd_skills if "skillName" in skill
        ]
        ja_skills = []
        ja_skills.append(JobApplicationSkill(company_id=1, skill_name="AWS", score=0.3))
        ja_skills.append(
            JobApplicationSkill(company_id=1, skill_name="Excel", score=0.5)
        )

        score, matching_skills = ja_calculate_matching_skill_score(
            ja_skills, jd_skill_names
        )
        ic(score)
        assert score > 0
        ic(matching_skills)
        assert len(matching_skills) > 0

    def test_ja_match_industry_with_jd(self):
        jae = JobApplicationExperience(
            company_id=1, title="Sr.Engineer", industry="Technology", years_experience=2
        )
        jaed = JobApplicationExperienceDb(jae, 2)
        jae2 = JobApplicationExperience(
            company_id=1, title="Trainee ", industry="Retail", years_experience=2
        )
        jaed = JobApplicationExperienceDb(jae, 2)
        jaed2 = JobApplicationExperienceDb(jae2, 2)
        experiences = [jaed, jaed2]
        jd_industry = "Retail"
        match = ja_match_industry_with_jd(experiences, jd_industry)
        ic(match)
        assert match

        jd_industry = "Telecom"
        match = ja_match_industry_with_jd(experiences, jd_industry)
        assert not match

    def test_ja_match_title_with_jd(self):
        jae = JobApplicationExperience(
            company_id=1,
            title="Sr. Software Engineer",
            industry="Technology",
            years_experience=2,
        )
        jaed = JobApplicationExperienceDb(jae, 2)
        jae2 = JobApplicationExperience(
            company_id=1, title="Trainee ", industry="Retail", years_experience=2
        )
        jaed = JobApplicationExperienceDb(jae, 2)
        jaed2 = JobApplicationExperienceDb(jae2, 2)
        experiences = [jaed, jaed2]
        jd_title = "SDE"
        match = ja_match_title_with_jd(experiences, jd_title)
        ic(match)
        assert match

        jd_title = "Fashion Designer"
        match = ja_match_industry_with_jd(experiences, jd_title)
        assert not match
