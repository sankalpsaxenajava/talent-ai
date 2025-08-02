from .test_db import global_test_get_job_posting
from intai.workers.job_posting_worker import JobPostingWorker
from intai.models.models import SessionLocal
from intai.models.models import JobPostingDb, SkillDb, JobPostingSkillDb
from icecream import ic
import json
from dotenv import load_dotenv

from subprocess import Popen
from pathlib import Path
import os

# import requests


def delete_job_posting_entities(session, company_id):
    ic("Test: Deleting job posting entities")
    JobPostingSkillDb.delete_all(session, company_id)
    JobPostingDb.delete_all(session, company_id)
    SkillDb.delete_all(session, company_id)


class TestJobPostingWorking:
    def setup_class(self):
        ic("Running python web server")
        load_dotenv()

        # TODO: Get the path from os.env
        self.test_server = Popen(
            [
                "python",
                "-m",
                "http.server",
                "-d",
                os.getenv("TEST_DATA_FOLDER"),
                "-b",
                "127.0.0.1",
                "9229",
            ]
        )

        ic("Server running for local test docs")
        self.session = SessionLocal()
        self.valid_job_posting = global_test_get_job_posting(self.session)
        self.valid_job_posting_db = JobPostingDb(self.valid_job_posting)
        self.company_id = self.valid_job_posting.company_id
        self.valid_job_posting_db.ideal_candidate_score = 2

    def teardown_class(self):
        delete_job_posting_entities(self.session, self.company_id)
        ic(self.test_server.kill())

    # @pytest.mark.skip(reason="disable openai calls test")
    def test_insert_update_entities(self):
        ic("test_insert_update_entities")
        worker = JobPostingWorker(self.valid_job_posting, self.session)

        # Insert into jobpostingdb
        worker.insert_update_entities()
        actual_jp = JobPostingDb.get_job_posting(
            self.session, self.company_id, self.valid_job_posting.client_job_id
        )
        ic(f"Prior to update actual_jp: {actual_jp}")
        self.valid_job_posting.job_posting_doc_url = "http://iamupdated.com"

        worker = JobPostingWorker(self.valid_job_posting, self.session)

        worker.insert_update_entities(True)
        actual_jp = JobPostingDb.get_job_posting(
            self.session, self.company_id, self.valid_job_posting.client_job_id
        )
        ic(f"actual_jp: {actual_jp}")
        assert actual_jp.job_posting_doc_url == "http://iamupdated.com"

    # @pytest.mark.skip(reason="disable openai calls test")
    def test_extract_entities(self):
        ic("test_extract_entities")
        worker = JobPostingWorker(self.valid_job_posting, self.session)

        # Insert into jobpostingdb
        worker.jobPostingDb.insert_job_posting(self.session)
        actual_entities = worker.extract_save_entities()
        ic(f"Entities: {actual_entities}")
        actual_jp = JobPostingDb.get_job_posting(
            self.session, self.company_id, self.valid_job_posting.client_job_id
        )
        ic(f"actual_jp: {actual_jp}")
        ic(f"actual_jp.parsed_jd: {actual_jp.parsed_jd}")
        assert actual_jp.status == "Extracted Entities"
        assert len(actual_jp.extracted_text) > 0
        assert len(actual_jp.extracted_text) > 0
        assert len(actual_jp.parsed_jd) > 0
        delete_job_posting_entities(self.session, self.company_id)

    def test_extract_save_skill_names(self):
        """This test calls extractsaveskillnames. It also inserts a skill before calling
        and ensure that existing skill is not returned but new skills are returned"""
        ic("test_extract_save_skill_names")

        # This is to ensure this existing skill is not
        # inserted by the worker
        worker = JobPostingWorker(self.valid_job_posting, self.session)
        worker.jobPostingDb.insert_job_posting(self.session)
        SkillDb.insert_skills_no_duplicates(
            self.session, self.company_id, [("Communication", "Communication")]
        )

        entities_path = Path(os.getenv("TEST_DATA_FOLDER"), "jp_entities.json")
        assert entities_path.exists()
        f = entities_path.open()
        entities = f.read()

        ic(f"Entities: {entities}")

        parsed_jp = json.loads(entities)
        assert "skills" in parsed_jp
        ic(f"Parsed JP: {parsed_jp}")
        parsed_skills = parsed_jp["skills"]
        new_skills = worker.extract_save_skill_names(parsed_skills)
        # Since this was previously added. It should not have been returned
        # by the worker for extracting session.
        assert "Communication" not in new_skills
        session = self.session
        company_id = self.company_id
        ic(f"company_id {company_id}")
        skills = SkillDb.get_skills(session, company_id, None)
        ic(f"Test Verification: Skills {skills}")
        skill_names = [x.skill_name for x in skills]
        assert "Financial Analysis" in skill_names
        assert "Budgeting" in skill_names
        delete_job_posting_entities(self.session, self.company_id)

    def test_save_candidate_score(self):
        worker = JobPostingWorker(self.valid_job_posting, self.session, True)
        worker.jobPostingDb.insert_job_posting(self.session)
        ic(
            f"test_save_candidate_score: jp: {self.valid_job_posting} {self.valid_job_posting_db}"
        )

        entities_path = Path(os.getenv("TEST_DATA_FOLDER"), "jp_entities.json")
        assert entities_path.exists()
        f = entities_path.open()
        entities = f.read()
        parsed_job_posting = json.loads(entities)
        parsed_skills = parsed_job_posting["skills"]
        parsed_experience = parsed_job_posting["overallYearsOfExperience"]
        # NOTE: this is needed as it creates entries in skillsdb needed for next step.
        new_skills = worker.extract_save_skill_names(parsed_skills)
        ic(f"test_save_candidate_score: After extract_save_skill_names\n{new_skills}")
        worker.calc_save_candidate_score(parsed_skills, parsed_experience)
        actual_jp = JobPostingSkillDb.get_job_posting_skills(
            self.session, self.company_id, self.valid_job_posting_db.id
        )
        ic(actual_jp)
        assert len(actual_jp) > 0
        # assert actual_jp[0].score > 0
        delete_job_posting_entities(self.session, self.company_id)
