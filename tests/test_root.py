from fastapi.testclient import TestClient
from intai.main import app
import json
from .test_db import (
    BaseTestJobPostingDb,
    BaseTestJobApplicationDb,
    global_test_get_job_posting,
)
from intai.models.models import (
    SessionLocal,
    JobPostingDb,
    JobPostingSkillDb,
    SkillDb,
    JobApplicationSkillDb,
)
from icecream import ic
from dotenv import load_dotenv
import os
from subprocess import Popen

client = TestClient(app)


def test_root_path():
    response = client.get("/")

    # Check the response context now
    assert response.text == '"Welcome to Intalent API!"'


class TestProcessJobApplication(BaseTestJobApplicationDb):

    @classmethod
    def test_process_job_application(cls):
        job_application = cls.valid_job_application

        print(job_application)

        response = client.post(
            "/jobapplication",
            json=job_application.model_dump(),
        )
        print(response)

        # Check response code
        assert response.status_code == 200
        json_resp = json.loads(response.text)
        assert "task_id" in json_resp.keys()
        assert json_resp["task_id"] > 0


class TestProcessJobPosting(BaseTestJobPostingDb):
    def setup_class(self):
        ic("Running python web server")
        load_dotenv()

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
        ic(self.test_server.kill())
        JobPostingDb.delete_all(self.session, self.company_id)
        JobPostingSkillDb.delete_all(self.session, self.company_id)
        JobApplicationSkillDb.delete_all(self.session, self.company_id)
        SkillDb.delete_all(self.session, self.company_id)

    def test_process_job_posting(self):
        job_posting = self.valid_job_posting
        company_id = job_posting.company_id
        client_job_id = job_posting.client_job_id
        response = client.post("/jobposting", json=job_posting.model_dump())

        # Check response code
        assert response.status_code == 200
        json_resp = json.loads(response.text)
        assert "task_id" in json_resp.keys()
        assert json_resp["task_id"] > 0

        # get the status from the db
        actual_job_posting_db = JobPostingDb.get_job_posting(
            self.session, company_id, client_job_id
        )
        ic(f"test_process_job::{actual_job_posting_db}")
        ic(
            "NOTE: if there is a failure here then check if front end server or mock is available."
        )
        assert (
            actual_job_posting_db.status == "PROCESSED"
            or actual_job_posting_db.status == "PROCESSED_FE_ERROR"
        )
