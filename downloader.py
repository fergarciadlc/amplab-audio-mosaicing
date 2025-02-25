import os
import shutil

import freesound
import pandas as pd

# Configuration
FREESOUND_API_KEY = os.getenv("FREESOUND_API_KEY", None)
if not FREESOUND_API_KEY:
    raise ValueError("FREESOUND_API_KEY environment variable is not set")

FILES_DIR = "files"  # Folder for downloaded audio files
DATAFRAME_FILENAME = "dataframe.csv"
FREESOUND_STORE_METADATA_FIELDS = [
    "id",
    "name",
    "username",
    "previews",
    "license",
    "tags",
]

# Initialize Freesound client
freesound_client = freesound.FreesoundClient()
freesound_client.set_token(FREESOUND_API_KEY)

if not os.path.exists(FILES_DIR):
    os.mkdir(FILES_DIR)


def query_freesound(query, filter=None, num_results=10):
    """Query Freesound using the given query and filter."""
    if filter is None:
        filter = "duration:[0 TO 30]"  # Default filter for short sounds
    pager = freesound_client.text_search(
        query=query,
        filter=filter,
        fields=",".join(FREESOUND_STORE_METADATA_FIELDS),
        group_by_pack=1,
        page_size=num_results,
    )
    return list(pager)


def retrieve_sound_preview(sound, directory):
    """Download the high-quality OGG preview of a given Freesound sound."""
    file_url = sound.previews.preview_hq_ogg
    filename = os.path.join(directory, os.path.basename(file_url))
    return freesound.FSRequest.retrieve(file_url, freesound_client, filename)


def make_pandas_record(sound):
    """Create a dictionary with selected metadata for the given sound."""
    record = {key: sound.as_dict()[key] for key in FREESOUND_STORE_METADATA_FIELDS}
    del record["previews"]  # Remove preview details
    record["freesound_id"] = record.pop("id")
    record["path"] = os.path.join(
        FILES_DIR, os.path.basename(sound.previews.preview_hq_ogg)
    )
    return record


def download_collection(queries, override_files=True):
    """
    Download the source audio collection.

    :param queries: List of dictionaries with keys 'query', 'filter', and 'num_results'
    :param override_files: If True, clears the FILES_DIR before downloading.
    :return: DataFrame containing metadata of the downloaded sounds.
    """
    if override_files and os.path.exists(FILES_DIR):
        shutil.rmtree(FILES_DIR)
    os.makedirs(FILES_DIR, exist_ok=True)

    # Aggregate sounds from all queries
    sounds = []
    for query_info in queries:
        q = query_info.get("query")
        f = query_info.get("filter")
        n = query_info.get("num_results", 10)
        sounds += query_freesound(q, f, n)

    # Download each sound preview
    for count, sound in enumerate(sounds):
        print(f"Downloading sound with id {sound.id} [{count + 1}/{len(sounds)}]")
        retrieve_sound_preview(sound, FILES_DIR)

    # Save metadata as a CSV file
    df = pd.DataFrame([make_pandas_record(s) for s in sounds])
    df.to_csv(DATAFRAME_FILENAME, index=False)
    print(f"Saved DataFrame with {len(df)} entries to {DATAFRAME_FILENAME}")
    return df
