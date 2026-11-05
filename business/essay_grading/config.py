from typing import TypedDict

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()
MODEL_NAME = "gpt-4o-mini"
llm = ChatOpenAI(model = MODEL_NAME, temperature =0)

class State(TypedDict):
    """Represent state of essay grading process"""
    essay: str
    relevance_score: float
    grammar_score: float
    structure_score: float
    depth_score: float
    final_score: float