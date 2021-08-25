# Imports from python.
import json
import os
import time


# Imports from other dependencies.
from slugify import slugify
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# Imports from this library.
from constants import DIRECTORIES
from constants import ERROR_STATUSES
from constants import PATHS
from fix_metadata import add_episode_metadata
from logger_klass import METADATA_LOGGER
from reorder_playlist import check_reordering
from utils import get_show_configs


# Set the directory on watch
WATCHED_DIRECTORY = DIRECTORIES["watched_media"]

CURRENT_PLAYLIST_FILE = PATHS["current_playlists"]

METADATA_ERROR_FILE = PATHS["metadata_errors"]


class OnMyWatch:
    watchDirectory = WATCHED_DIRECTORY

    def __init__(self):
        self.observer = Observer()

        if not os.path.isfile(PATHS["episode_aliases"]):
            with open(PATHS["episode_aliases"], "w") as alias_list:
                json.dump([], alias_list)

        if not os.path.isfile(METADATA_ERROR_FILE):
            with open(METADATA_ERROR_FILE, "w") as error_report:
                json.dump({}, error_report)

        if not os.path.isfile(CURRENT_PLAYLIST_FILE):
            with open(CURRENT_PLAYLIST_FILE, "w") as receipts_file:
                json.dump({}, receipts_file)

        METADATA_LOGGER.info("Watching...")

    def run(self):
        event_handler = Handler()
        self.observer.schedule(
            event_handler, self.watchDirectory, recursive=True
        )
        self.observer.start()
        try:
            while True:
                time.sleep(5)
                check_reordering()
        except Exception:
            self.observer.stop()
            METADATA_LOGGER.info("Observer Stopped")

        self.observer.join()


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None

        if event.event_type == "created":
            all_show_configs = get_show_configs()

            (inner_filepath, filename) = os.path.split(
                event.src_path.lstrip(WATCHED_DIRECTORY)
            )

            if os.path.splitext(filename)[-1] == ".mp3":
                show_with_new_ep = slugify(
                    inner_filepath, separator="_", replacements=[["'", ""]]
                )
                if show_with_new_ep in all_show_configs.keys():
                    new_metadata, error_code = add_episode_metadata(
                        show_with_new_ep, event.src_path
                    )

                    if error_code:
                        with open(METADATA_ERROR_FILE, "r") as error_report:
                            errors = json.load(error_report)

                        if error_code == ERROR_STATUSES["no_audio_file"]:
                            file_key = "empty_files"
                        elif error_code == ERROR_STATUSES["no_match"]:
                            file_key = "mismatches"

                        wall_time = int(time.time())

                        METADATA_LOGGER.info(
                            "".join(
                                [
                                    f"New {file_key.upper()} error: ",
                                    f"{show_with_new_ep} / ",
                                    f"{event.src_path} @ {wall_time}",
                                ]
                            )
                        )

                        typed_errors = errors.get(file_key, [])

                        # Don't add a new error if this file has caused trouble
                        # previously — just append those times to the list.
                        same_file_errors = [
                            error_obj
                            for error_obj in typed_errors
                            if error_obj["show"] == show_with_new_ep
                            and error_obj["file_path"] == event.src_path
                        ]

                        different_errors = [
                            error_obj
                            for error_obj in typed_errors
                            if error_obj not in same_file_errors
                        ]

                        all_observed_times = [wall_time]
                        all_observed_times.extend(
                            [
                                past_time
                                for error_obj in same_file_errors
                                for past_time in error_obj["when_seen"]
                            ]
                        )

                        errors[file_key] = [
                            *different_errors,
                            dict(
                                show=show_with_new_ep,
                                file_path=event.src_path,
                                when_seen=all_observed_times,
                            ),
                        ]

                        with open(METADATA_ERROR_FILE, "w") as error_report:
                            json.dump(errors, error_report)
                    else:
                        METADATA_LOGGER.info("New mp3 tagged!")
                        METADATA_LOGGER.info(f"  - File: '{event.src_path}'")
                        METADATA_LOGGER.info(
                            f"  - Output: '{json.dumps(new_metadata)}'"
                        )

                        with open(CURRENT_PLAYLIST_FILE, "r") as receipts_file:
                            receipts = json.load(receipts_file)

                        show_section = receipts.get(
                            show_with_new_ep,
                            {
                                "processed_and_placed": [],
                                "to_be_placed": [],
                                "to_be_deleted": [],
                            },
                        )

                        if "to_be_placed" not in show_section:
                            show_section["to_be_placed"] = []

                        show_section["to_be_placed"].append(
                            new_metadata["title"]
                        )

                        receipts[show_with_new_ep] = show_section

                        with open(CURRENT_PLAYLIST_FILE, "w") as receipts_file:
                            json.dump(receipts, receipts_file)

                        with open(METADATA_ERROR_FILE, "r") as error_report:
                            errors = json.load(error_report)

                        for error_type, failed_episodes in errors.items():
                            errors_to_remove = [
                                _
                                for _ in failed_episodes
                                if _["show"] == show_with_new_ep
                                and _["file_path"] == event.src_path
                            ]

                            if errors_to_remove:
                                errors[error_type] = [
                                    error_obj
                                    for error_obj in failed_episodes
                                    if error_obj not in errors_to_remove
                                ]

                                METADATA_LOGGER.info(
                                    "".join(
                                        [
                                            "Metadata task for ",
                                            f"'{event.src_path}' ",
                                            "succeeded on retry. ",
                                            "Error removed.",
                                        ]
                                    )
                                )
                        with open(METADATA_ERROR_FILE, "w") as error_report:
                            json.dump(errors, error_report)
                else:
                    METADATA_LOGGER.info("PASS 2")
            else:
                METADATA_LOGGER.info("PASS")
        elif event.event_type == "deleted":
            all_show_configs = get_show_configs()

            (inner_filepath, filename) = os.path.split(
                event.src_path.lstrip(WATCHED_DIRECTORY)
            )

            if os.path.splitext(filename)[-1] == ".mp3":
                with open(CURRENT_PLAYLIST_FILE, "r") as receipts_file:
                    receipts = json.load(receipts_file)

                show_with_new_ep = slugify(
                    inner_filepath, separator="_", replacements=[["'", ""]]
                )
                if show_with_new_ep in all_show_configs.keys():
                    METADATA_LOGGER.info("Episode mp3 deleted!")
                    METADATA_LOGGER.info(f"  - File: '{event.src_path}'")

                    show_section = receipts.get(
                        show_with_new_ep,
                        {
                            "processed_and_placed": [],
                            "to_be_placed": [],
                            "to_be_deleted": [],
                        },
                    )

                    if "to_be_deleted" not in show_section:
                        show_section["to_be_deleted"] = []

                    show_section["to_be_deleted"].append(filename)

                    receipts[show_with_new_ep] = show_section

                    with open(CURRENT_PLAYLIST_FILE, "w") as receipts_file:
                        json.dump(receipts, receipts_file)
        # elif event.event_type == "modified":
        #     return None
        # else:
        #     METADATA_LOGGER.info(f"ET: {event.event_type}")


if __name__ == "__main__":
    watch = OnMyWatch()
    watch.run()
