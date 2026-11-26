import os
from dotenv import load_dotenv

from typing import TypedDict

from openai import OpenAI


load_dotenv()

client = OpenAI()
MODEL_NAME = os.getenv("MODEL_NAME")

TTS_MODEL = os.getenv("TTS_MODEL")
TTS_SAMPLE_RATE = 24000
class AgentState(TypedDict):
    input_text: str
    content_type: str

    audio_data: bytes
    audio_path: str
    processed_text : str