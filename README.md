# Audio Mosacing with Freesound and Essentia

## Demo Video
Watch the demo for the project [here](https://www.youtube.com/watch?v=Krot_22pL9s).
![Audio Mosacing with Freesound and Essentia](https://img.youtube.com/vi/Krot_22pL9s/maxresdefault.jpg)


Tested on Python 3.12 Apple Silicon M1

Install dependencies:
```bash
pip install -r requirements.txt
```

## Run web app
```bash
streamlit run streamlit_app.py
```

## Run python scripts
Without GUI, but showing plots.
```bash
python main.py --step mosaic --target_audio "574234__kbrecordzz__groove-metal-break-6.wav" --frame_size 4192
```
