"""Load the TTS model.

Run this file directly to pre-download/load the model ahead of time, e.g.
during deployment before starting the Streamlit app, so the multi-GB model
download/load happens in the background instead of blocking the first
user request.
"""

import torch
from TTS.api import TTS

MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"


def load_model() -> TTS:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return TTS(MODEL_NAME).to(device)


if __name__ == "__main__":
    load_model()
    print("Model ready.")
