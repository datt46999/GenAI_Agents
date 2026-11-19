import os

from typing import TypedDict, Annotated, List, Dict, Sequence
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME")
llm = ChatOpenAI(
    model = MODEL_NAME,
    temperature=0.0,
    streaming=True,

)


class GraphState(TypedDict):
    messages: Annotated[Sequence[HumanMessage | AIMessage], "The messages in the conversation"]
    query: Annotated[str, "A user containing instruction for the creating of the test case."]
    actions: Annotated[List[str], "List of actions for which to generate the code"]
    script: Annotated[str, "The generated Playwright script."]


    target_url: Annotated[str, "Valid URL of the website to test."]
    current_action: Annotated[int, "The index of the current action to generate the code for."]
    current_action_code: Annotated[int, "Code for the current actions."]
    website_state: Annotated[str, "DOM state of website"]

    aggregated_raw_actions: Annotated[str, "Raw aggregation of the actions"]

    error_message: Annotated[str, "Message that occurred during the processing of the action."]
    
    test_name: Annotated[str, "Name of the generated test."]
    test_evaluation_output: Annotated[str, "Evaluation of the final test script."]
    
    report: Annotated[str, "Final report of the test generation."]

    
class ActionList(BaseModel):
    actions: List[str] = Field(..., description = "List of automic actions for end-to-end testing")