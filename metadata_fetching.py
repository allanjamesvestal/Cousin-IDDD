# Imports from other dependencies.
from dateutil import parser


# Imports from this library.
from constants import MATCH_ERROR_TEXT


def dummy_fn(show_config, show_metadata, audio_file, matching_episodes):
    return "TK"


def fetch_title(show_config, show_metadata, audio_file, matching_episodes):
    return (
        matching_episodes[0]["Title"]
        if len(matching_episodes) == 1
        else MATCH_ERROR_TEXT
    )


def fetch_artist(show_config, show_metadata, audio_file, matching_episodes):
    return show_metadata["Author"]


def fetch_album(show_config, show_metadata, audio_file, matching_episodes):
    return show_metadata["Title"]


def fetch_track_num(show_config, show_metadata, audio_file, matching_episodes):
    if len(matching_episodes) == 1 and "episode_prefix" in show_config:
        show_prefix = show_config["episode_prefix"]

        if matching_episodes[0]["Title"].startswith(show_prefix["start"]):
            episode_candidate = (
                matching_episodes[0]["Title"]
                .lstrip(show_prefix["start"])
                .split(show_prefix["end"])[0]
                .split(" ")[0]
            )

            if episode_candidate.isnumeric():
                highest_numbered_episode = max(
                    [
                        int(
                            _["Title"]
                            .lstrip(show_prefix["start"])
                            .split(show_prefix["end"])[0]
                            .split(" ")[0]
                        )
                        for _ in show_metadata["PodcastItems"]
                        if _["Title"].startswith(show_prefix["start"])
                        and _["Title"]
                        .lstrip(show_prefix["start"])
                        .split(show_prefix["end"])[0]
                        .split(" ")[0]
                        .isnumeric()
                    ]
                )
                return (int(episode_candidate), highest_numbered_episode)

    return (None, None)


def fetch_genre(show_config, show_metadata, audio_file, matching_episodes):
    return "Podcast"


def fetch_date(show_config, show_metadata, audio_file, matching_episodes):
    if len(matching_episodes) != 1:
        return None

    parsed_date = parser.isoparse(matching_episodes[0]["PubDate"])
    return f"{parsed_date.isoformat()[:-6]}Z"


ATTRIBUTE_FETCHERS = dict(
    title=fetch_title,
    artist=fetch_artist,
    album=fetch_album,
    track_num=fetch_track_num,
    genre=fetch_genre,
    date=fetch_date,
)
