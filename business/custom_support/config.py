from typing import TypedDict

MODEL_NAME = "gpt-4o-mini"
class State(TypedDict):
    query: str
    category: str
    sentiment: str
    response: str