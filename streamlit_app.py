import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from analyzer import (analyze_collection, analyze_target,
                      plot_waveform_with_frames)
# Import our modules (ensure these are in your PYTHONPATH or same folder)
from downloader import download_collection
from mosaicer import reconstruct_audio

# Initialize session state variables if not present
if "source_df" not in st.session_state:
    st.session_state.source_df = None
if "target_df" not in st.session_state:
    st.session_state.target_df = None
if "target_audio_path" not in st.session_state:
    st.session_state.target_audio_path = None

# Sidebar for navigation (only two pages now)
page = st.sidebar.radio("Choose Action", ("Downloader", "Analyzer"))

##############################
# Downloader Section
##############################
if page == "Downloader":
    st.title("Downloader & Source Analysis")
    st.write(
        "Define queries to download sounds from Freesound and analyze the source collection."
    )

    # Dynamic query input
    num_queries = st.number_input(
        "Number of queries", min_value=1, max_value=10, value=3
    )
    queries = []
    default_queries = ["organ", "violin", "scream"]
    for i in range(int(num_queries)):
        st.subheader(f"Query {i+1}")
        query_text = st.text_input(
            f"Query text {i+1}",
            value=default_queries[i] if i < len(default_queries) else "",
        )
        query_filter = st.text_input(f"Filter (optional) {i+1}", value="")
        num_results = st.number_input(
            f"Number of results {i+1}", min_value=1, max_value=100, value=20
        )
        queries.append(
            {
                "query": query_text,
                "filter": query_filter if query_filter != "" else None,
                "num_results": num_results,
            }
        )

    if st.button("Download & Analyze Source Collection"):
        st.info("Downloading sounds...")
        # Download sounds and get metadata DataFrame
        meta_df = download_collection(queries, override_files=True)
        st.success("Download complete!")
        st.dataframe(meta_df)

        st.info("Analyzing source collection...")
        # You can also allow the user to choose the frame size for source analysis if needed
        frame_size = 8192
        source_df = analyze_collection(
            meta_df, frame_size=frame_size, output_csv="dataframe_source.csv"
        )
        st.session_state.source_df = source_df
        st.success("Source collection analyzed!")
        st.dataframe(source_df)

##############################
# Analyzer & Mosaicer Section
##############################
elif page == "Analyzer":
    st.title("Target Audio Analysis & Mosaicing")
    st.write(
        "Upload your target audio file, set the frame size for analysis, and then mosaic the audio."
    )

    uploaded_file = st.file_uploader("Upload Target Audio", type=["wav", "mp3", "ogg"])
    frame_size = st.number_input(
        "Frame Size (samples)", min_value=1024, max_value=16384, value=8192, step=1024
    )

    if uploaded_file is not None:
        # Save the uploaded file to the current directory as "target.wav"
        target_path = "target.wav"
        with open(target_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state.target_audio_path = target_path
        st.audio(target_path, format="audio/wav")

        st.info("Analyzing target audio...")
        target_df = analyze_target(
            target_path,
            frame_size=frame_size,
            sync_with_beats=False,
            output_csv="dataframe_target.csv",
        )
        st.session_state.target_df = target_df
        st.success("Target analysis complete!")
        st.dataframe(target_df)

        st.write("Target Analysis Waveform:")
        plot_waveform_with_frames(target_path, target_df)
        st.pyplot(plt.gcf())
        plt.clf()

        # Now add the "Mosaic It!" button on the same page.
        if st.button("Mosaic It!"):
            # Ensure that source analysis is available
            if st.session_state.source_df is None:
                st.error("Please run the Downloader & Source Analysis step first!")
            else:
                output_filename = "reconstructed_output.wav"
                generated_audio, target_audio, selected_ids = reconstruct_audio(
                    st.session_state.source_df,
                    st.session_state.target_df,
                    output_filename,
                )
                st.success("Audio mosaicing complete!")

                # Plot target waveform (re-using the analyzer plotting function)
                st.subheader("Target Audio Waveform")
                fig, ax = plt.subplots(figsize=(15, 4))
                plot_waveform_with_frames(target_path, st.session_state.target_df)
                st.pyplot(fig)
                plt.clf()

                # Plot reconstructed audio waveform
                st.subheader("Reconstructed Audio Waveform")
                fig2, ax2 = plt.subplots(figsize=(15, 4))
                ax2.plot(generated_audio)
                ax2.set_title("Reconstructed Audio")
                st.pyplot(fig2)
                plt.clf()

                st.subheader("Listen to the Results")
                st.write("**Target Audio:**")
                st.audio(target_path)
                st.write("**Reconstructed Audio:**")
                st.audio(output_filename)
                st.write("**Mixed Audio (50/50):**")
                # Create a mixed signal for playback
                mix = (target_audio * 0.5 + generated_audio * 0.5).astype(np.float32)
                mix_file = "mix.wav"
                from essentia.standard import MonoWriter

                MonoWriter(filename=mix_file, format="wav", sampleRate=44100)(mix)
                st.audio(mix_file)

                st.write("**Freesound IDs used in the reconstruction:**")
                # Filter metadata by selected freesound ids (assumes source_df has a 'freesound_id' column)
                ids_used = st.session_state.source_df[
                    st.session_state.source_df["freesound_id"].isin(selected_ids)
                ]
                st.dataframe(ids_used)
