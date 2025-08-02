from time import sleep
from .test_db import (
    BackgroundTaskDb,
    BackgroundTaskTypeEnum,
    global_test_get_candidate,
    global_test_get_job_application,
    global_test_get_job_posting_for_ja,
)
from intai.models.models import (
    SessionLocal,
    CandidateDb,
    JobPostingDb,
    JobApplicationDb,
    SkillDb,
    JobApplicationSkillDb,
    JobPostingSkillDb,
    JobApplicationDetailDb,
    JobApplicationProjectDb,
    JobApplicationAddressDb,
    JobApplicationAwardDb,
    JobApplicationCertificationDb,
    JobApplicationCertificationSkillDb,
    JobApplicationEducationDb,
    JobApplicationExperienceDb,
    JobApplicationInterestDb,
    JobApplicationLanguageDb,
    JobApplicationPublicationDb,
    JobApplicationScoreDb,
    JobApplicationVolunteerDb,
)

from intai.workers.candidate_worker import CandidateWorker
from icecream import ic
import json
from dotenv import load_dotenv

from subprocess import Popen
from pathlib import Path
import os

def delete_candidate_entities(session, company_id):
    JobApplicationAddressDb.delete_all(session, company_id)
    JobApplicationAwardDb.delete_all(session, company_id)
    JobApplicationCertificationSkillDb.delete_all(session, company_id)
    JobApplicationCertificationDb.delete_all(session, company_id)
    JobApplicationEducationDb.delete_all(session, company_id)
    JobApplicationExperienceDb.delete_all(session, company_id)
    JobApplicationInterestDb.delete_all(session, company_id)
    JobApplicationLanguageDb.delete_all(session, company_id)
    JobApplicationProjectDb.delete_all(session, company_id)
    JobApplicationPublicationDb.delete_all(session, company_id)
    JobApplicationVolunteerDb.delete_all(session, company_id)
    CandidateDb.delete_all(session, company_id)

    JobApplicationDetailDb.delete_all(session, company_id)


class TestJobApplicationWorker:
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
        sleep(2)
        ic("Server running for local test docs")
        self.session = SessionLocal()
       
        self.valid_candidate = global_test_get_candidate(self.session)
        self.valid_candidate_db = CandidateDb(
            self.valid_candidate
        )
        self.company_id = self.valid_candidate.company_id
   
        ic(self.valid_candidate_db)
        assert self.valid_candidate_db is not None

    def teardown_class(self):
        ic(self.test_server.kill())
        delete_candidate_entities(self.session, self.company_id)

        JobApplicationSkillDb.delete_all(self.session, self.company_id)
        SkillDb.delete_all(self.session, self.company_id)
        BackgroundTaskDb.delete_all(self.session, self.company_id)

    def test_run(self):
        """Test running of candidate worker."""
        ic("****************************************************************")
        ic("test update run")
        ic("****************************************************************")
        ic(self.valid_candidate_db)

        bg_task = BackgroundTaskDb(
            self.valid_candidate.company_id,
            message="Message",
            message_type=BackgroundTaskTypeEnum.Candidate,
        )
        bg_task.insert_background_task(self.session)
        ic(bg_task)
        worker = CandidateWorker(self.valid_candidate, self.session, bg_task.id)
        worker.run(bg_task.id)

        actual_candidate = CandidateDb.get_candidate(
           self.session, self.company_id, client_candidate_id=self.valid_candidate.client_candidate_id
        )

        ic(f"{actual_candidate}")
        assert actual_candidate.status == "PROCESSED"
        actual_bg_tasks = BackgroundTaskDb.get_background_tasks(
            self.session, self.company_id
        )
        print(actual_bg_tasks)
        actual_bg_task = actual_bg_tasks[0]
        ic(actual_bg_task)
        assert actual_bg_task.status == "COMPLETED FE ERROR"

        BackgroundTaskDb.delete_all(self.session, self.company_id)
        delete_candidate_entities(self.session, self.company_id)