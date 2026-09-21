"""
LangGraph framework for creating using graph-base workflow.
Each node represents a function or computation step.
Edges define the flow between these nodes base on certain condition


Key Features:
+ State Managerment
+ Flexible Routing
+ Presistence
+ Visialization


Demonstrate the power of LangGraph by a multi-step text analytic pipeline.
Focus on process given text through three key stages:
    + Text classification: The Input text will predifine categories (EX: New, Blog, Research)
    + Entity extraction: Identify and extract key entities such as person, organizaion, and location
    + Text Summarization: Generate concise summary of the text input
"""

import os 


from dotenv import load_dotenv
from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.runnables.graph import MermaidDrawMethod
from IPython.display import display, Image

load_dotenv()


"""
Define the state of initialize LLM
"""

class State(TypedDict):
    text : str
    classification : str
    entities: list[str]
    summary: str
llm = ChatOpenAI(model="gpt-4o-mini", temperature = 0)


"""
Define node Function
"""
def classification_node(state: State):
    """Classify the text into one of the categories: News, Blog, or Other"""
    prompt = PromptTemplate(
        input_varriables =["text"],
        template = "Classify the following text into one of the categories: News, Blog, Research, or Other.\n\nText: {text}\n\nCategory:"
    )
    message = HumanMessage(content= prompt.format(text = state["text"]))
    classification = llm.invoke([message]).content.strip()
    return {"classification": classification}

def entities_node(state: State):
    """Extract all entities (Person, Organization, Location) from the text"""
    prompt = PromptTemplate(
        input_varriables =["text"],
        template = "Extract all the entities (Person, Organization, Location) from the following text. Provide the result as a comma-separated list.\n\nText: {text}\n\nEntities:"
    )
    message = HumanMessage(content = prompt.format(text = state["text"]))
    entity = llm.invoke([message]).content.strip()
    return {"entities": entity}

def summarization_node(state = State):
    """summarize text in on short sentence"""
    prompt = PromptTemplate(
        input_varriables = ["text"],
        template = "Summarize the following text in one short sentence.\n\nText: {text}\n\nSummary: "
    )
    message = HumanMessage(content = prompt.format(text = state["text"]))
    summary = llm.invoke([message]).content.strip()
    return {"summary": summary}

"""
Create Tool and build workflow
"""

workflow = StateGraph(State)
workflow.add_node("classification_node", classification_node)
workflow.add_node("entities_extraction_node", entities_node)
workflow.add_node("summarization_node", summarization_node)

workflow.set_entry_point("classification_node")
workflow.add_edge("classification_node", "entities_extraction_node")
workflow.add_edge("entities_extraction_node", "summarization_node")
workflow.add_edge("summarization_node", END)
app = workflow.compile()



sample_text = """
OpenAI has announced the GPT-4 model, which is a large multimodal model that exhibits human-level performance on various professional benchmarks. It is developed to improve the alignment and safety of AI systems.
additionally, the model is designed to be more efficient and scalable than its predecessor, GPT-3. The GPT-4 model is expected to be released in the coming months and will be available to the public for research and development purposes.
"""

state_input = {"text": sample_text}
result = app.invoke(state_input)

print("Classification:", result["classification"])
print("\nEntities:", result["entities"])
print("\nSummary:", result["summary"])



