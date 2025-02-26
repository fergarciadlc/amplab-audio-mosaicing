import os
import random

import essentia
import essentia.standard as estd
import matplotlib.pyplot as plt
import numpy as np
from IPython.display import Audio, display
from sklearn.neighbors import NearestNeighbors

# Cache for loaded audio files
loaded_audio_files = {}

# Features to use for similarity
# fmt: off
similarity_features = [
    "mfcc_0", "mfcc_1", "mfcc_2", "mfcc_3", "mfcc_4", "mfcc_5", "mfcc_6", "mfcc_7", "mfcc_8", "mfcc_9", "mfcc_10", "mfcc_11", "mfcc_12",
    "loudness",
    "spectral_centroid",
    "danceability",
    "flux",
    "hfc",
    "spectral_complexity",
    "pitch_salience",
    "intensity",
]
# fmt: on


def get_audio_file_segment(file_path, start_sample, n_samples):
    """
    Load an audio file (with caching) and return a segment.

    :param file_path: Path to the audio file.
    :param start_sample: Starting sample index.
    :param n_samples: Number of samples to return.
    :return: Audio segment as a numpy array.
    """
    if file_path not in loaded_audio_files:
        loader = estd.MonoLoader(filename=file_path)
        audio = loader()
        loaded_audio_files[file_path] = audio
    else:
        audio = loaded_audio_files[file_path]
    return audio[start_sample : start_sample + n_samples]


def find_similar_frames(query_frame, df_source_frames, n, features):
    """
    Find the n most similar frames in the source DataFrame.

    :param query_frame: Numpy array of feature values for the query.
    :param df_source_frames: DataFrame containing source frames.
    :param n: Number of neighbors to find.
    :param features: List of feature column names to use.
    :return: List of similar frame records.
    """
    query_frame = query_frame.reshape(1, -1)
    nbrs = NearestNeighbors(n_neighbors=n, algorithm="ball_tree").fit(
        df_source_frames[features].values
    )
    distances, indices = nbrs.kneighbors(query_frame)
    return [df_source_frames.iloc[k] for k in indices[0]]


def choose_frame_from_source_collection(
    target_frame,
    df_source_frames,
    similarity_features=similarity_features,
    choice="random",  # random or best
):
    """
    Choose a source frame that best matches the target frame.

    This function uses MFCC features for similarity and returns a random
    frame among the top similar candidates.
    """
    n_neighbours_to_find = 10
    query_frame = target_frame[similarity_features].values
    similar_frames = find_similar_frames(
        query_frame, df_source_frames, n_neighbours_to_find, similarity_features
    )
    # return random.choice(similar_frames)
    if choice == "random":
        return random.choice(similar_frames)
    elif choice == "best":
        return similar_frames[0]
    else:
        raise ValueError(f"Invalid choice: {choice}")


def reconstruct_audio(
    df_source,
    df_target,
    output_filename,
    similarity_features=similarity_features,
    choice="random",  # random or best
):
    """
    Reconstruct the target audio using source frames.

    :param df_source: DataFrame with analysis of the source collection.
    :param df_target: DataFrame with analysis of the target audio.
    :param output_filename: Output WAV filename.
    :return: Tuple (generated_audio, target_audio, selected_freesound_ids)
    """
    target_sound_filename = df_target.iloc[0]["path"]
    target_audio = estd.MonoLoader(filename=target_sound_filename)()
    total_length_target_audio = len(target_audio)
    generated_audio = np.zeros(total_length_target_audio)
    selected_freesound_ids = []

    print("Reconstructing audio file...")
    for i in range(len(df_target)):
        target_frame = df_target.iloc[i]
        source_frame = choose_frame_from_source_collection(
            target_frame=target_frame,
            df_source_frames=df_source,
            similarity_features=similarity_features,
            choice=choice,
        )
        selected_freesound_ids.append(source_frame["freesound_id"])
        frame_length = target_frame["end_sample"] - target_frame["start_sample"]
        source_audio_segment = get_audio_file_segment(
            source_frame["path"], source_frame["start_sample"], frame_length
        )
        generated_audio[
            target_frame["start_sample"] : target_frame["start_sample"]
            + len(source_audio_segment)
        ] = source_audio_segment

    estd.MonoWriter(filename=output_filename, format="wav", sampleRate=44100)(
        essentia.array(generated_audio)
    )
    print(f"Audio generated and saved in {output_filename}!")
    return generated_audio, target_audio, selected_freesound_ids


def plot_audio_signals(target_audio, generated_audio):
    """Plot the waveforms of the target and reconstructed audio."""
    plt.figure(figsize=(15, 5))
    plt.plot(target_audio)
    plt.axis([0, len(target_audio), -1, 1])
    plt.title("Target audio")
    plt.show()

    plt.figure(figsize=(15, 5))
    plt.plot(generated_audio)
    plt.axis([0, len(target_audio), -1, 1])
    plt.title("Reconstructed audio")
    plt.show()


def display_audio(target_audio, generated_audio):
    """Display audio players for listening to the target, reconstructed, and mix."""
    print("Target audio")
    display(Audio(target_audio, rate=44100))
    print("Reconstructed audio")
    display(Audio(generated_audio, rate=44100))
    print("Mix of both signals")
    display(Audio(generated_audio * 0.5 + target_audio * 0.5, rate=44100))
