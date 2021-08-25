# Imports from python.
import os

DIRECTORIES = dict(
    config=os.environ.get("CONFIG_DIRECTORY", "/config"),
    logs=os.environ.get("LOGS_DIRECTORY", "/logs"),
    watched_media=os.environ.get("WATCHED_DIRECTORY", "/watched_media"),
)

PATHS = dict(
    config=f"{DIRECTORIES['config']}/cousin-iddd.config.json",
    current_playlists=f"{DIRECTORIES['config']}/current_playlists.json",
    episode_aliases=f"{DIRECTORIES['config']}/episode_aliases.json",
    metadata_errors=f"{DIRECTORIES['config']}/coding_errors.json",
    stderr_logfile=f"{DIRECTORIES['logs']}/cousin-iddd.err.log",
    stdout_logfile=f"{DIRECTORIES['logs']}/cousin-iddd.log",
)

ERROR_STATUSES = dict(no_audio_file=2, no_match=3)

MATCH_ERROR_TEXT = "! Matching error"

PODGRAB_CREDENTIALS_LINE = (
    f"{os.getenv('PODGRAB_USERNAME')}:{os.getenv('PODGRAB_PASSWORD')}@"
    if os.environ.get("PODGRAB_USERNAME", False)
    and os.environ.get("PODGRAB_PASSWORD", False)
    else ""
)

PODGRAB_BASE_URL = "".join(
    ["http://", PODGRAB_CREDENTIALS_LINE, os.getenv("PODGRAB_HOST")]
)
