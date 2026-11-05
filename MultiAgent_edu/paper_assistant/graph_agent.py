import os
import urllib3
import pdfplumber
import time
import io
import json
from typing import Optional, TypedDict, Annotated, Sequence


from langchain_core.messages import BaseMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import BaseTool, tool
from langchain_openai import ChatOpenAI

from langgraph.graph.message import add_message
from langgraph.graph import START, END, StateGraph
from core_wrapper import CoreAPIWrapper
from utils import *
from prompts_system import *




"""
=============================================
Agent state
=============================================
"""
class AgentState(TypedDict):
    """
    The state of agent during paper research process
    """

    required_search: bool = False
    num_feedback_request: int = 0
    is_good_answer : bool=False
    message: Annotated[Sequence[BaseModel], add_message]

"""
==========================================
Agent tools
==========================================
"""   

@tool('search-papers', args_schema=SearchPaperInputs)
def search_paper(query: str, max_papers: int = 1) -> str:
    """Search for scientific papers using the CORE API.

    Example:
    {"query": "Attention is all you need", "max_papers": 1}

    Returns:
        A list of the relevant papers found with the corresponding relevant information.
    """

    try:
        return CoreAPIWrapper(top_k_results= max_papers).search(query)
    except Exception as e:
        return f"Error performing paper search: {e}"

@tool('dowload-paper')
def download_paper(url: str) -> str:
    """Download a specific scientific paper from a given URL.

    Example:
    {"url": "https://sample.pdf"}

    Returns:
        The paper content.
    """
    try:        
        http = urllib3.PoolManager(
            cert_reqs='CERT_NONE',
        )
        
        # Mock browser headers to avoid 403 error
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        max_retries = 5
        for attempt in range(max_retries):
            response = http.request('GET', url, headers=headers)
            if 200 <= response.status < 300:
                pdf_file = io.BytesIO(response.data)
                with pdfplumber.open(pdf_file) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() + "\n"
                return text
            elif attempt < max_retries - 1:
                time.sleep(2 ** (attempt + 2))
            else:
                raise Exception(f"Got non 2xx when downloading paper: {response.status_code} {response.text}")
    except Exception as e:
        return f"Error downloading paper: {e}"

@tool("ask-human-feedback")
def ask_human_feedback(question: str) -> str:
    """Ask for human feedback. You should call this tool when encountering unexpected errors."""
    return input(question)

tools = [search_paper, download_paper, ask_human_feedback]
tools_dict = {tool.name: tool for tool in tools}

"""
===================================
define workflow
===================================
"""
# llm
base_llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
decision_making_llm = base_llm.with_structured_output(DecisionMakingOutput)
agent_llm = base_llm.bind_tools(tools)
judge_llm = base_llm.with_structured_output(JudgeOutput)


# Decision making node
def decision_making_node(state: AgentState):
    """
    Entry point for workflow. 
    Base on the user query, the model can either respond directly or perform a full research, routing workflow to the planning node
    """
    system_prompt = SystemMessage(content= DECISION_MAKING_PROMPT)
    response: DecisionMakingOutput = decision_making_llm.invoke([system_prompt] + state["messages"])
    output = {"requires_research": response.requires_research}
    if response.answer:
        output["messages"] = [AIMessage(content=response.answer)]
    return output

# Task router function
def router(state: AgentState):
    """Router directing the user query to the appropriate branch of the workflow."""
    if state["requires_research"]:
        return "planning"
    else:
        return "end"
# Agent call node
def agent_node(state: AgentState):
    """Agent call node that uses the LLM with tools to answer the user query."""
    system_prompt = SystemMessage(content=AGENT_PROMPT)
    response = agent_llm.invoke([system_prompt] + state["messages"])
    return {"messages": [response]}

# Should continue function
def should_continue(state: AgentState):
    """Check if the agent should continue or end."""
    messages = state["messages"]
    last_message = messages[-1]

    # End execution if there are no tool calls
    if last_message.tool_calls:
        return "continue"
    else:
        return "end"

# planning node
def planning_node(state: AgentState):
    """
    Planning node that create step by step plan to answer and user query 
    """

    system_prompt = SystemMessage(content=PLANNING_PROMPT.format(tools = format_tools_description(tools)))
    response = base_llm.invoke([system_prompt] + state['messages'])
    return {"messages": [response]}

# Tool call node
def tools_node(state: AgentState):
    """
    Tool call node that executes that tool base one plan
    """
    outputs = []
    for tool_call in state['message'][-1].tool_calls:
        tool_result = tools_dict[tool_call['name']].invoke(tool_call['args'])
        outputs.append(
            ToolMessage(
                content=json.dumps(tool_result),
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
        )
    return {"messages": outputs}

# judge node
def judge_node(state: AgentState):
    """
    Node to let the LLM judge the quality of its own final answer.
    """
    # end if llm failed to provide a good answer twice
    num_feedback_request = state.get('num_feedback_request', 0)
    if num_feedback_request >= 2:
        return {'is_good_answer': True}

    system_prompt = SystemMessage(content=JUDGE_PROMPT)
    response: JudgeOutput = judge_llm.invoke([system_prompt] + state["messages"])
    output = {
        "is_good_answer": response.is_good_answer,
        "num_feedback_requests": num_feedback_request + 1
    }
    if response.feedback:
        output["messages"] = [AIMessage(content=response.feedback)]
    return output


# Final answer router function
def final_answer_router(state: AgentState):
    """Router to end the workflow or improve the answer."""
    if state["is_good_answer"]:
        return "end"
    else:
        return "planning"


def create_graph():
    """
    defines the workflow using LangGraph
    """

    # Initialize the StateGraph
    workflow = StateGraph(AgentState)

    # Add nodes to the graph
    workflow.add_node("decision_making", decision_making_node)
    workflow.add_node("planning", planning_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("agent", agent_node)
    workflow.add_node("judge", judge_node)

    # Set the entry point of the graph
    workflow.set_entry_point("decision_making")

    # Add edges between nodes
    workflow.add_conditional_edges(
        "decision_making",
        router,
        {
            "planning": "planning",
            "end": END,
        }
    )
    workflow.add_edge("planning", "agent")
    workflow.add_edge("tools", "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "end": "judge",
        },
    )
    workflow.add_conditional_edges(
        "judge",
        final_answer_router,
        {
            "planning": "planning",
            "end": END,
        }
    )


    return workflow.compile()

async def test():
    test_inputs = [
    "Download and summarize the findings of this paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC11379842/pdf/11671_2024_Article_4070.pdf",

    "Can you find 8 papers on quantum machine learning?",

    """Find recent papers (2024-2025) about CRISPR applications in treating genetic disorders, 
    focusing on clinical trials and safety protocols""",

    """Find and analyze papers from 2024-2025 about the application of transformer architectures in protein folding prediction, 
    specifically looking for novel architectural modifications with experimental validation."""
    ]

    outputs = []
    for test_input in test_inputs:
        final_answer = await print_stream(create_graph, test_input)
        outputs.append(final_answer.content)

    for input, output in zip(test_inputs, outputs):
        display(Markdown(f"## Input:\n\n{input}\n\n"))
        display(Markdown(f"## Output:\n\n{output}\n\n"))

if __name__ =="__main__":
    import asyncio
    asyncio.run(test())
