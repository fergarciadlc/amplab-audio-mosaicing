import essentia
import essentia.standard as estd
import matplotlib.pyplot as plt
import pandas as pd


def analyze_sound(audio_path, frame_size=None, audio_id=None, sync_with_beats=False):
    """
    Analyze an audio file by splitting it into frames and computing features.

    :param audio_path: Path to the audio file.
    :param frame_size: Size of the frame (in samples) to use; if None the entire file is one frame.
    :param audio_id: Identifier for the audio (used in output).
    :param sync_with_beats: If True, use beat positions to determine frames.
    :return: List of dictionaries with analysis results per frame.
    """
    analysis_output = []
    loader = estd.MonoLoader(filename=audio_path)
    audio = loader()

    if frame_size is None:
        frame_size = len(audio)
    if frame_size % 2 != 0:
        frame_size += 1

    if sync_with_beats:
        beat_tracker_algo = estd.BeatTrackerDegara()
        beat_positions = beat_tracker_algo(audio)
        beat_positions = [int(round(position * 44100)) for position in beat_positions]
        frame_start_end_samples = list(zip(beat_positions[:-1], beat_positions[1:]))
    else:
        frame_start_samples = list(range(0, len(audio), frame_size))
        frame_start_end_samples = list(
            zip(frame_start_samples[:-1], frame_start_samples[1:])
        )

    for count, (fstart, fend) in enumerate(frame_start_end_samples):
        frame = audio[fstart:fend]
        frame_output = {
            "freesound_id": audio_id,
            "id": f"{audio_id}_f{count}",
            "path": audio_path,
            "start_sample": fstart,
            "end_sample": fend,
        }
        # Compute loudness and normalize by frame length
        loudness_algo = estd.Loudness()
        loudness = loudness_algo(frame)
        frame_output["loudness"] = loudness / len(frame)

        # Extract MFCC features
        w_algo = estd.Windowing(type="hann")
        spectrum_algo = estd.Spectrum()
        mfcc_algo = estd.MFCC()
        spec = spectrum_algo(w_algo(frame))
        _, mfcc_coeffs = mfcc_algo(spec)
        for j, coeff in enumerate(mfcc_coeffs):
            frame_output[f"mfcc_{j}"] = coeff

        analysis_output.append(frame_output)
    return analysis_output


def analyze_collection(df, frame_size, output_csv):
    """
    Analyze each sound in the source collection.

    :param df: DataFrame with source sounds metadata.
    :param frame_size: Frame size (in samples) for analysis.
    :param output_csv: CSV file to store analysis results.
    :return: DataFrame with analysis results.
    """
    analyses = []
    for i in range(len(df)):
        sound = df.iloc[i]
        print(f'Analyzing sound with id {sound["freesound_id"]} [{i + 1}/{len(df)}]')
        try:
            analysis_output = analyze_sound(
                sound["path"], frame_size=frame_size, audio_id=sound["freesound_id"]
            )
            analyses.extend(analysis_output)
        except RuntimeError:
            continue
    df_source = pd.DataFrame(analyses)
    df_source.to_csv(output_csv, index=False)
    print(
        f"Saved source analysis DataFrame with {len(df_source)} entries to {output_csv}"
    )
    return df_source


def analyze_target(audio_path, frame_size, sync_with_beats, output_csv):
    """
    Analyze the target audio file.

    :param audio_path: Path to the target audio.
    :param frame_size: Frame size (in samples) for analysis.
    :param sync_with_beats: Whether to sync frames with beats.
    :param output_csv: CSV file to store target analysis results.
    :return: DataFrame with target analysis.
    """
    print(f"Analyzing target sound: {audio_path}")
    target_analysis = analyze_sound(
        audio_path,
        frame_size=frame_size,
        audio_id=audio_path,
        sync_with_beats=sync_with_beats,
    )
    df_target = pd.DataFrame(target_analysis)
    df_target.to_csv(output_csv, index=False)
    print(
        f"Saved target analysis DataFrame with {len(df_target)} entries to {output_csv}"
    )
    return df_target


def plot_waveform_with_frames(audio_path, df_target, duration_seconds=4):
    """Plot the waveform of an audio file with vertical lines at each frame start."""
    loader = estd.MonoLoader(filename=audio_path)
    audio = loader()
    plt.figure(figsize=(15, 5))
    plt.plot(audio)
    plt.vlines(df_target["start_sample"].values, -1, 1, color="red")
    plt.axis([0, min(len(audio), 44100 * duration_seconds), -1, 1])
    plt.title("Target audio file (first 4 seconds)")
    plt.show()
