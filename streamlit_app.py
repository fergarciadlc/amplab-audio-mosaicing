import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from analyzer import (analyze_collection, analyze_target,
                      plot_waveform_with_frames)
from downloader import download_collection
from mosaicer import reconstruct_audio

st.set_page_config(layout="wide")
st.title("Audio Mosaicing with Freesound and Essentia 🎶🎸")
st.header("Welcome to the Audio Mosaicing App!")
st.markdown(
    """
This app allows you to download sounds from Freesound, 
analyze them, and then reconstruct a target audio file using the source collection.

Developed with ♥️ by [Fernando Garcia de la Cruz](https://fergarciadlc.github.io/)
    """
)

# Initialize session state variables if not present
if "source_df" not in st.session_state:
    st.session_state.source_df = None
if "target_df" not in st.session_state:
    st.session_state.target_df = None
if "target_audio_path" not in st.session_state:
    st.session_state.target_audio_path = None
if "frame_size" not in st.session_state:
    st.session_state.frame_size = 8192

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

    st.session_state.frame_size = st.number_input(
        "Frame Size (samples)", min_value=1024, max_value=44100, value=8192, step=1024
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
        source_df = analyze_collection(
            meta_df,
            frame_size=st.session_state.frame_size,
            output_csv="dataframe_source.csv",
        )
        st.session_state.source_df = source_df
        st.success("Source collection analyzed!")
        st.dataframe(source_df)
        st.info("You can now go to the 'Analyzer' tab to analyze a target audio file.")

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
        f"Frame Size (samples) - Audio collection used {st.session_state.frame_size} for feature analysis",
        min_value=1024,
        max_value=44100,
        value=st.session_state.frame_size,
        step=1024,
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
        seconds_to_plot = st.number_input(
            "Seconds to plot", min_value=1, max_value=600, value=4
        )
        plot_waveform_with_frames(
            target_path, target_df, duration_seconds=seconds_to_plot
        )
        st.pyplot(plt.gcf())
        plt.clf()

        st.subheader("Mosaicing Options")
        st.write("Select the features to use for similarity:")

        # Default list of similarity features
        default_features = [
            "mfcc_0",
            "mfcc_1",
            "mfcc_2",
            "mfcc_3",
            "mfcc_4",
            "mfcc_5",
            "mfcc_6",
            "mfcc_7",
            "mfcc_8",
            "mfcc_9",
            "mfcc_10",
            "mfcc_11",
            "mfcc_12",
            "loudness",
            "spectral_centroid",
            "danceability",
            "flux",
            "hfc",
            "spectral_complexity",
            "pitch_salience",
            "intensity",
        ]

        # Split into three columns (using slicing to preserve order)
        col1, col2, col3 = st.columns(3)
        selected_features = []

        for feature in default_features[0:7]:
            if col1.checkbox(feature, value=True):
                selected_features.append(feature)
        for feature in default_features[7:14]:
            if col2.checkbox(feature, value=True):
                selected_features.append(feature)
        for feature in default_features[14:]:
            if col3.checkbox(feature, value=True):
                selected_features.append(feature)

        st.write("Select frame selection strategy:")
        selected_choice = st.radio("Choice", ("random", "best"))

        # Now add the "Mosaic It!" button on the same page.
        if st.button("Mosaic It!"):
            if st.session_state.source_df is None:
                st.error("Please run the Downloader & Source Analysis step first!")
            else:
                output_filename = "reconstructed_output.wav"
                generated_audio, target_audio, selected_ids = reconstruct_audio(
                    st.session_state.source_df,
                    st.session_state.target_df,
                    output_filename,
                    similarity_features=selected_features,
                    choice=selected_choice,
                )
                st.success("Audio mosaicing complete!")
                st.info(f"Selected features: {selected_features}")
                st.info(f"Selected choice: {selected_choice}")

                st.subheader("Reconstructed Audio Waveform")
                fig2, ax2 = plt.subplots(figsize=(15, 4))
                ax2.plot(generated_audio)
                ax2.set_title("Reconstructed Audio")
                st.pyplot(fig2)
                plt.clf()

                st.subheader("Listen to the Results")
                st.write("**Target Audio:**")
                st.audio(st.session_state.target_audio_path)
                st.write("**Reconstructed Audio:**")
                st.audio(output_filename)
                st.write("**Mixed Audio (50/50):**")
                mix = (target_audio * 0.5 + generated_audio * 0.5).astype(np.float32)
                mix_file = "mix.wav"
                from essentia.standard import MonoWriter

                MonoWriter(filename=mix_file, format="wav", sampleRate=44100)(mix)
                st.audio(mix_file)

                st.write("**Freesound IDs used in the reconstruction:**")
                ids_used = st.session_state.source_df[
                    st.session_state.source_df["freesound_id"].isin(selected_ids)
                ]
                st.dataframe(ids_used)
