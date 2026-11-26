import os
from typing import TypedDict

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv


load_dotenv()
MODEL_NAME = os.getenv("MODEL_NAME")

llm = ChatOpenAI(model = MODEL_NAME, reasoning_effort="none")
class AgentState(TypedDict):
    musician_input: str
    melody: str
    harmory: str
    rhythm: str
    style: str
    composition: str
    midi_style: str

