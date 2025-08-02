import pytest
import json
from icecream import ic
from dotenv import load_dotenv


from subprocess import Popen
from pathlib import Path
import os
from intai.utils.file_utils import (
    extract_with_llama_parse,
    get_bytes_from_url,
    extract_text,
)


class TestFileUtils:
    def setup_class(self):
        ic("setup_class is being called **** ")
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

        self.doc_url = "http://localhost:9229/jp.docx"

        self.pdf_url = "http://localhost:9229/ja.pdf"

    def teardown_class(self):
        ic("teardown_class is being called **** ")

    def test_extract_with_llama_parse(self):
        """Test for LLamaParse to parse pdf and docx file."""
        bytes_data, docType = get_bytes_from_url(self.pdf_url)
        content = extract_with_llama_parse(bytes_data, docType)
        ic(self.doc_url)
        ic(content)
        assert content is not None

        bytes_data, docType = get_bytes_from_url(self.doc_url)
        content = extract_with_llama_parse(bytes_data, docType)
        ic(self.doc_url)
        ic(content)
        assert content is not None
