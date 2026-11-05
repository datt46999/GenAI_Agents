
import os

from typing import Optional
from IPython.display import display, Markdown


from pydantic import BaseModel, Field


from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool

from langgraph.graph.state import CompiledStateGraph

class SearchPaperInputs(BaseModel):
    """
    Input object to search paper with CORE API
    """
    query : str= Field(description = "The query to search for on the query archive")
    max_papers: int = Field(description = "The maximum mumber of paper to return. It's default to 1, but you can increate it up to 10 in case you need to perform a more comprehensive search",
                            default = 1, ge = 1, le = 10)

class DecisionMakingOutput(BaseModel):
    """
    output object of the decsion making node
    """
    requires_search :bool = Field(description = "Whether the user query requires research or not")
    answer : Optional[str] = Field(default = None, description = "The answer to the user query. It should be None if the user query requires research, otherwise it should be a direct answer to the user query.")

class JudgeOutput(BaseModel):
    """Output object of the judge node."""
    is_good_answer: bool = Field(description="Whether the answer is good or not.")
    feedback: Optional[str] = Field(default=None, description="Detailed feedback about why the answer is not good. It should be None if the answer is good.")

def format_tools_description(tools: list[BaseTool]) -> str:
    return "\n\n".join([f"- {tool.name}: {tool.description}\n Input arguments: {tool.args}" for tool in tools])


async def print_stream(app: CompiledStateGraph, input: str) -> Optional[BaseMessage]:
    display(Markdown("## New research running"))
    display(Markdown(f"### Input:\n\n{input}\n\n"))
    display(Markdown("### Stream:\n\n"))

    # Stream the results 
    all_messages = []
    async for chunk in app.astream({"messages": [input]}, stream_mode="updates"):
        for updates in chunk.values():
            if messages := updates.get("messages"):
                all_messages.extend(messages)
                for message in messages:
                    message.pretty_print()
                    print("\n\n")
 
    # Return the last message if any
    if not all_messages:
        return None
    return all_messages[-1]

