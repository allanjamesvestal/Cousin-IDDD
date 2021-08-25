# Imports from python.
import json
import os


# Imports from other dependencies.
import eyed3
import requests
from slugify import slugify


# Imports from this library.
from constants import ERROR_STATUSES
from constants import MATCH_ERROR_TEXT
from constants import PATHS
from constants import PODGRAB_BASE_URL
from logger_klass import METADATA_LOGGER
from metadata_fetching import ATTRIBUTE_FETCHERS
from utils import get_show_configs


def load_episode_aliases():
    with open(PATHS["episode_aliases"], "r") as alias_list:
        raw_aliases = json.load(alias_list)

    return {
        f"{raw_alias['show']}@@{raw_alias['original_filename']}": raw_alias[
            "alias"
        ]
        for raw_alias in raw_aliases
    }


def add_episode_metadata(show_id, episode_file):
    audio_file = eyed3.load(episode_file)

    if not audio_file:
        return None, ERROR_STATUSES["no_audio_file"]

    if not audio_file.tag:
        audio_file.initTag()

    all_show_configs = get_show_configs()
    show_config = all_show_configs[show_id]

    show_podgrab_id = show_config["podgrab_id"]
    show_podgrab_feed = f"{PODGRAB_BASE_URL}/podcasts/{show_podgrab_id}"
    show_json = requests.get(show_podgrab_feed).json()

    filename_only = os.path.split(audio_file.path)[-1]

    alias_key = f"{show_id}@@{filename_only}"

    episode_aliases = load_episode_aliases()

    if alias_key in episode_aliases:
        METADATA_LOGGER.info(f"Applying override '{alias_key}'...")
        filename_only = episode_aliases[alias_key]

    current_filename = slugify(os.path.splitext(filename_only)[0])

    matching_episodes = [
        episode
        for episode in show_json["PodcastItems"]
        if slugify(episode["Title"]) == current_filename
    ]

    attributes_to_add = {
        k: ATTRIBUTE_FETCHERS[k](
            show_config, show_json, audio_file, matching_episodes
        )
        for k in show_config["metadata_attributes"]
    }

    if "title" in show_config["metadata_attributes"]:
        if attributes_to_add["title"] == MATCH_ERROR_TEXT:
            return None, ERROR_STATUSES["no_match"]

        audio_file.tag.title = attributes_to_add["title"]

    if "artist" in show_config["metadata_attributes"]:
        audio_file.tag.artist = attributes_to_add["artist"]

    if "album" in show_config["metadata_attributes"]:
        audio_file.tag.album = attributes_to_add["album"]

    if "track_num" in show_config["metadata_attributes"]:
        audio_file.tag.track_num = attributes_to_add["track_num"]

    if "genre" in show_config["metadata_attributes"]:
        audio_file.tag.genre = attributes_to_add["genre"]

    if "date" in show_config["metadata_attributes"]:
        audio_file.tag.release_date = attributes_to_add["date"]

    audio_file.tag.save()

    return attributes_to_add, None
