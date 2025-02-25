import argparse

import pandas as pd

from analyzer import (analyze_collection, analyze_target,
                      plot_waveform_with_frames)
from downloader import DATAFRAME_FILENAME, download_collection
from mosaicer import display_audio, plot_audio_signals, reconstruct_audio


def main():
    parser = argparse.ArgumentParser(description="Audio Mosaicing Application")
    parser.add_argument(
        "--step",
        choices=["download", "analyze", "mosaic", "all"],
        default="all",
        help="Step to execute: download, analyze, mosaic, or all",
    )
    parser.add_argument(
        "--target_audio",
        type=str,
        default="574234__kbrecordzz__groove-metal-break-6.wav",
        help="Path to the target audio file",
    )
    parser.add_argument(
        "--frame_size",
        type=int,
        default=8192,
        help="Frame size (in samples) for analysis",
    )
    args = parser.parse_args()

    # Step 1: Download collection
    if args.step in ["download", "all"]:
        queries = [
            {"query": "organ", "filter": None, "num_results": 20},
            {"query": "violin", "filter": "duration:[0 TO 1]", "num_results": 20},
            {"query": "scream", "filter": "duration:[1 TO 2]", "num_results": 20},
        ]
        print("Downloading audio collection...")
        df = download_collection(queries, override_files=True)
    else:
        df = pd.read_csv(DATAFRAME_FILENAME)

    # Step 2: Analyze source collection and target file
    if args.step in ["analyze", "all"]:
        print("Analyzing source collection...")
        df_source = analyze_collection(
            df, frame_size=args.frame_size, output_csv="dataframe_source.csv"
        )
        print("Analyzing target audio file...")
        df_target = analyze_target(
            args.target_audio,
            frame_size=args.frame_size,
            sync_with_beats=False,
            output_csv="dataframe_target.csv",
        )
        plot_waveform_with_frames(args.target_audio, df_target)
    else:
        df_source = pd.read_csv("dataframe_source.csv")
        df_target = pd.read_csv("dataframe_target.csv")

    # Step 3: Audio mosaicing reconstruction
    if args.step in ["mosaic", "all"]:
        print("Performing audio mosaicing...")
        output_filename = f"{args.target_audio}.reconstructed.wav"
        generated_audio, target_audio, selected_ids = reconstruct_audio(
            df_source, df_target, output_filename
        )
        plot_audio_signals(target_audio, generated_audio)
        display_audio(target_audio, generated_audio)
        print("Freesound IDs used in the reconstruction:")
        print(df[df["freesound_id"].isin(selected_ids)])


if __name__ == "__main__":
    main()
