import json
from enum import Enum


class DocType(Enum):
    """Describes the DocType of the associated file."""

    PDF = 1
    DOCX = 2
    INVALID = 3

    def __repr__(self):
        """Return string representation of the Enum."""
        return "DocType::" + self.name


class WorkType(Enum):
    """Describes the work type."""

    JOBPOSTING = 1
    JOBAPPLICATION = 2
    MATCHING_FACTORS_ANALYSIS = 3
    MATCH_TITLE = 4
    INVALID = 9


def is_valid_json(json_str):
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError:
        return False
