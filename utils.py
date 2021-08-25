# Imports from python.
import json


# Imports from this library.
from constants import PATHS


def get_show_configs():
    with open(PATHS["config"], "r") as config_json:
        project_config = json.load(config_json)

    return project_config["podcasts"]
