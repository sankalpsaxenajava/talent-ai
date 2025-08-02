import json
from loguru import logger
from dotenv import load_dotenv
import os
import numpy as np
from pathlib import Path


load_dotenv()
FRONT_END_URL = os.getenv("FRONT_END_URL")
UNIQUE_SKILL_CONFIG_PATH = Path(os.getenv("CONFIG_PATH"), "unique_skills.json")
SKILL_CONFIG_PATH = Path(os.getenv("CONFIG_PATH"), "skill_lookup.json")

WEIGHTAGE_CONFIG_PATH = Path(os.getenv("CONFIG_PATH"), "weightage_config.json")
CLUSTER_EMBEDDINGS_CONFIG_PATH = Path(
    os.getenv("CONFIG_PATH"), "cluster_embeddings.npy"
)
EMBEDDINGS_CONFIG_PATH = Path(os.getenv("CONFIG_PATH"), "embeddings.npy")
CLUSTER_NAMES_CONFIG_PATH = Path(os.getenv("CONFIG_PATH"), "cluster_names.json")


# Load weightage configuration
def load_weightage_config():
    """Load the weightage config file."""
    weightage_config_path = WEIGHTAGE_CONFIG_PATH
    assert weightage_config_path.exists()
    logger.debug(f"weightage_file_path: {weightage_config_path}")
    with weightage_config_path.open() as f:
        weightage_dict = json.load(f)
    assert "max" in weightage_dict
    return weightage_dict


def load_skill_lookup():
    """Load the skill lookup dictionary."""
    skill_config_path = SKILL_CONFIG_PATH
    assert skill_config_path.exists()
    logger.debug(f"skill_config_path: {skill_config_path}")
    with skill_config_path.open() as file:
        return json.load(file)


def load_unique_skills():
    """Load the skills dictionary."""
    skill_config_path = UNIQUE_SKILL_CONFIG_PATH
    assert skill_config_path.exists()
    logger.debug(f"unique_skill_config_path: {skill_config_path}")
    with skill_config_path.open() as file:
        return json.load(file)


def load_embeddings():
    """Load the skills dictionary."""
    cluster_embeddings_config_path = CLUSTER_EMBEDDINGS_CONFIG_PATH
    logger.debug(f"cluster embeddings path: {cluster_embeddings_config_path}")
    assert cluster_embeddings_config_path.exists()
    cluster_embeddings = np.load(str(cluster_embeddings_config_path))

    embeddings_config_path = EMBEDDINGS_CONFIG_PATH
    assert embeddings_config_path.exists()
    embeddings = np.load(str(embeddings_config_path))
    return cluster_embeddings, embeddings


def load_cluster_names():
    """Load the cluster names from config."""
    cluster_names_config_path = CLUSTER_NAMES_CONFIG_PATH
    assert cluster_names_config_path.exists()
    with cluster_names_config_path.open() as file:
        return json.load(file)


def load_config_files():
    """Load all config files."""
    cluster_embeddings, embeddings = load_embeddings()
    cluster_names = load_cluster_names()
    skill_lookup = load_skill_lookup()
    skills = load_unique_skills()
    weightage_dict = load_weightage_config()
    return (
        cluster_embeddings,
        embeddings,
        cluster_names,
        skill_lookup,
        skills,
        weightage_dict,
    )
