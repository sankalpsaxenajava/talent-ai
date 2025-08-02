import pytest
import json
from icecream import ic
from dotenv import load_dotenv

from subprocess import Popen
from pathlib import Path
import os
from intai.utils.json_data_utils import (
    ja_get_details_from_json,
    ja_get_address_from_json,
    ja_get_experience_from_json,
    ja_get_certifications_from_json,
    ja_calculate_years_of_experience,
)


class TestJsonDataUtils:
    def setup_class(self):
        ic("setup_class is being called **** ")
        entities_path = Path(os.getenv("TEST_DATA_FOLDER"), "ja_entities.json")
        assert entities_path.exists()
        f = entities_path.open()
        self.entities = f.read()
        self.json_entities = json.loads(self.entities)

    def teardown_class(self):
        ic("teardown_class is being called **** ")

    def test_ja_get_details(self):
        ja_detail = ja_get_details_from_json(self.json_entities, 2)
        ic(ja_detail)
        assert ja_detail.applicant_name == "Ishan Shukla"
        assert ja_detail.applicant_resume_email == "ishanshuklaa@gmail.com"
        assert ja_detail.applicant_resume_linkedin == "linkedin.com/in/ishan"

        assert ja_detail.experience_years > 0
        assert ja_detail.avg_tenure_org_years > 0
        assert ja_detail.avg_tenure_role_years > 0

    def test_ja_get_address(self):
        ja_addresses = ja_get_address_from_json(self.json_entities, 2)
        ic(ja_addresses)
        assert len(ja_addresses) >= 1
        ja_address = ja_addresses[0]
        assert ja_address.city == "Ahmedabad"
        assert ja_address.state == "Gujarat"
        assert ja_address.country == "India"

    def test_ja_get_experience(self):
        """Test the get experience from json.

        This will get the experience
        as well as the skills score."""
        ja_experiences, skill_score_dict = ja_get_experience_from_json(
            self.json_entities, 2
        )
        ic(ja_experiences)
        ic(skill_score_dict)
        assert len(ja_experiences) >= 1
        ja_experience = ja_experiences[0]
        assert ja_experience.title is not None and len(ja_experience.title) > 0
        assert ja_experience.title == "Sr. Executive-Costing"

        assert len(skill_score_dict) > 0
        assert len(skill_score_dict.keys()) > 0
        assert "Stock Audit" in skill_score_dict.keys()
        assert skill_score_dict["Stock Audit"] > 0

    def test_ja_get_certification(self):
        ic(self.json_entities)
        ja_certifications, skill_dict = ja_get_certifications_from_json(
            self.json_entities, 2
        )
        ic(ja_certifications)
        ic(skill_dict)
        assert len(ja_certifications) >= 1
        ja_cert = [x for x in ja_certifications if x.title == "ICAI Final"][0]

        expected_cert_title = "ICAI Final"
        assert ja_cert.title is not None and len(ja_cert.title) > 0
        assert ja_cert.title == expected_cert_title

        assert skill_dict is not None
        assert len(skill_dict) > 0
        assert expected_cert_title in skill_dict.keys()
        skills_for_cert = skill_dict[expected_cert_title]
        ic(skills_for_cert)
        assert "Costing" in skills_for_cert

    def test_ja_calculate_years_of_experience(self):
        exp_dict = {"start": "05-2020", "end": "05-2022", "yearsOfExperience": 5}
        exp_years = ja_calculate_years_of_experience(exp_dict)
        ic(exp_years)
        assert exp_years == 2
        exp_dict_null = {"start": "null", "end": "05-2022", "yearsOfExperience": 5}
        exp_years = ja_calculate_years_of_experience(exp_dict_null)
        ic(exp_years)
        assert exp_years == 5
