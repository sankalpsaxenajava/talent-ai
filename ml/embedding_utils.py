#!/usr/bin/env python3
from .utils.llm_types import LLMModelType
from .llm_client import LLMClient
from intai.config import load_config_files
from loguru import logger
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from intai.config import EMBEDDINGS_CONFIG_PATH, UNIQUE_SKILL_CONFIG_PATH
import os
import json


def find_nearest_cluster_center(skill_embedding, cluster_embeddings, cluster_names):
    """Find the nearest cluster center based on skill and cluster embeddings.

    NOTE: skill_embedding is calculated for this instance while cluster embedding and names
    are loaded from the config file.
    """
    logger.debug(
        f"cluster_names_len: {len(cluster_names)}\n cluster_embeddings_len: {len(cluster_embeddings)}"
    )
    similarities = cosine_similarity([skill_embedding], cluster_embeddings)[0]
    nearest_cluster_index = np.argmax(similarities)
    logger.debug(
        f"nearest_cluster_idx: {nearest_cluster_index}\n clustern_names_length: {len(cluster_names)}"
    )
    if len(cluster_names) >= nearest_cluster_index:
        return cluster_names[nearest_cluster_index]


# Function to lookup the cluster center skill
def find_cluster_center_skill(skill: str, ai_client: LLMClient):
    """Find the center from the cluster for text passed."""
    # TODO: We don't need open_ai_client here. Just get the word_embedding and use that
    logger.info(f"find_cluster_center_skill {skill}")
    (
        cluster_embeddings,
        embeddings,
        cluster_names,
        skill_lookup,
        skills,
        weightage_dict,
    ) = load_config_files()
    if skill.lower() in skill_lookup:
        return skill_lookup[skill.lower()]
    else:
        logger.info("Skill not found in lookup. Finding nearest cluster center...")
        skill_embedding = ai_client.get_embeddings(skill)
        cluster_skill = find_nearest_cluster_center(
            skill_embedding, cluster_embeddings, cluster_names
        )
        logger.debug(f"Nearest cluster center for {skill} is {cluster_skill}")
        return cluster_skill


def find_cluster_center_skills(skills: [str], ai_client: LLMClient):
    """Find the center of all the skills in list and return."""
    cluster_center_list = []
    for word in skills:
        cluster_center_word = find_cluster_center_skill(word, ai_client=ai_client)
        cluster_center_list.append(cluster_center_word)
    return cluster_center_list


def save_updated_embeddings_and_skills(updated_embeddings, updated_skills):
    try:
        # Save updated embeddings
        np.save(EMBEDDINGS_CONFIG_PATH, updated_embeddings)
        logger.info("Updated embeddings saved successfully.")

        # Save updated skills
        with open(UNIQUE_SKILL_CONFIG_PATH, "w") as file:
            json.dump(updated_skills, file)
        logger.info("Updated skills saved successfully.")
    except Exception as e:
        logger.error(
            f"An error occurred while saving updated embeddings and skills: {str(e)}"
        )
        raise e
