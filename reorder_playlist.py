# Imports from python.
import json
import os


# Imports from other dependencies.
import requests
from slugify import slugify
from urllib.parse import urlencode


# Imports from this library.
from constants import PATHS
from constants import PODGRAB_BASE_URL
from logger_klass import METADATA_LOGGER
from utils import get_show_configs


CURRENT_PLAYLIST_FILE = PATHS["current_playlists"]

NAVIDROME_HOST = os.environ.get("NAVIDROME_HOST")
NAVIDROME_USERNAME = os.environ.get("NAVIDROME_USERNAME")
NAVIDROME_PASSWORD = os.environ.get("NAVIDROME_PASSWORD")


def check_reordering():
    all_show_configs = get_show_configs()

    with open(CURRENT_PLAYLIST_FILE, "r") as receipts_file:
        receipts = json.load(receipts_file)

    for show_id, episode_dict in receipts.items():
        show_config = all_show_configs[show_id]

        if "album_id" in show_config and "playlist_id" in show_config:
            if episode_dict.get("to_be_placed", []):
                reorder_podcast_playlist(
                    show_config, receipts, show_id, "add_episode"
                )
            elif episode_dict.get("to_be_deleted", []):
                reorder_podcast_playlist(
                    show_config, receipts, show_id, "remove_episode"
                )


def reorder_podcast_playlist(
    show_config, receipts, show_id, mode="add_episode"
):
    receipts_per_show = receipts[show_id]

    base_navidrome_dict = dict(
        u=NAVIDROME_USERNAME,
        p=NAVIDROME_PASSWORD,
        f="json",
        v="1.8.0",
        c="apiAccess",
    )

    album_query_dict = dict(**base_navidrome_dict, id=show_config["album_id"])
    album_query_string = urlencode(album_query_dict)

    podcast_album_query = (
        f"http://{NAVIDROME_HOST}/rest/getAlbum?{album_query_string}"
    )

    album_response = requests.get(podcast_album_query)
    album_json = album_response.json().get("subsonic-response", {})

    cancel_run = album_json.get("status", "failed") == "failed"

    if not cancel_run:
        song_map = {
            song["title"]: song["id"] for song in album_json["album"]["song"]
        }

        if mode == "add_episode":
            for downloading_song in receipts_per_show.get("to_be_placed", []):
                if downloading_song not in song_map:
                    cancel_run = True
        elif mode == "remove_episode":
            # If a to-be-deleted episode is in song_map, cancel this run.
            filename_title_map = {
                slugify(os.path.split(song["path"])[-1]): song["title"]
                for song in album_json["album"]["song"]
            }
            for pending_delete_filename in receipts_per_show.get(
                "to_be_deleted", []
            ):
                if slugify(pending_delete_filename) in filename_title_map:
                    cancel_run = True

    if not cancel_run:
        show_podgrab_id = show_config["podgrab_id"]
        show_podgrab_feed = f"{PODGRAB_BASE_URL}/podcasts/{show_podgrab_id}"
        show_response = requests.get(show_podgrab_feed)
        show_json = show_response.json()

        if "filtered_prefixes" in show_config:
            latest_episode_titles = [
                episode["Title"]
                for episode in show_json["PodcastItems"]
                if not any(
                    [
                        episode["Title"].startswith(prefix)
                        for prefix in show_config["filtered_prefixes"]
                    ]
                )
            ]
        else:
            latest_episode_titles = [
                _["Title"] for _ in show_json["PodcastItems"]
            ]

        latest_episode_ids = [
            song_map[episode_title]
            for episode_title in latest_episode_titles
            if episode_title in song_map
        ]

        playlist_query_dict = dict(
            **base_navidrome_dict, playlistId=show_config["playlist_id"],
        )

        playlist_query_string = "".join(
            [
                urlencode(playlist_query_dict),
                f"&songId={'&songId='.join(latest_episode_ids[:17])}",
            ]
        )

        playlist_creation_query = "".join(
            [
                f"http://{NAVIDROME_HOST}/rest/",
                f"createPlaylist?{playlist_query_string}",
            ]
        )

        updated_playlist = requests.get(playlist_creation_query).json()

        playlist_obj = updated_playlist.get("subsonic-response", {}).get(
            "playlist", {}
        )
        playlist_name = playlist_obj.get("name", None)
        playlist_songs = playlist_obj.get("entry", [])
        playlist_song_count = len(playlist_songs)
        playlist_song_pluralized = (
            "songs" if playlist_song_count != 1 else "song"
        )

        all_playlist_ids = [song["id"] for song in playlist_songs]
        latest_album_ids = latest_episode_ids[:playlist_song_count]

        playlist_and_album_ids_match = json.dumps(
            all_playlist_ids
        ) == json.dumps(latest_album_ids)

        if playlist_name and playlist_and_album_ids_match:
            METADATA_LOGGER.info(
                " ".join(
                    [
                        f"Updated '{playlist_name}'",
                        f"(it now has {playlist_song_count}",
                        f"{playlist_song_pluralized})",
                    ]
                )
            )

            receipts[show_id]["processed_and_placed"] = [
                song["title"] for song in playlist_songs
            ]
            receipts[show_id]["to_be_placed"] = []
            receipts[show_id]["to_be_deleted"] = []

            # Write out the JSON, removing episodes we were able to place.
            with open(CURRENT_PLAYLIST_FILE, "w") as receipts_file:
                json.dump(receipts, receipts_file)
        else:
            METADATA_LOGGER.info(f"SKIPPING {show_id}")
