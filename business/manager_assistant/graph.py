import os 
from dotenv import load_dotenv

from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from config import *
from helper_function import *


def router(state: AgentState):
    """
    Route the agent to approriate node based on the project  description
    """
    max_iteration = state["max_iteration"]
    iteration_number = state["iteration_number"]

    if iteration_number < max_iteration:
        if len(state["project_risk_score_iterations"])>1:
            if state["project_risk_score_iterations"][-1] < state["project_risk_score_iterations"][0]:
                return END
            else:
                return "insight_generator"
        else:
            return "insight_generator"
    else:
        return END


def create_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("task_generation", task_generation_node)
    workflow.add_node("task_dependencies", task_dependency_node)
    workflow.add_node("task_scheduler", task_scheduler_node)
    workflow.add_node("task_allocator", task_allocation_node)
    workflow.add_node("risk_assessor", risk_assessment_node)
    workflow.add_node("insight_generator", insight_generation_node)

    # Add edges to the workflow
    workflow.set_entry_point("task_generation")
    workflow.add_edge("task_generation", "task_dependencies")
    workflow.add_edge("task_dependencies", "task_scheduler")
    workflow.add_edge("task_scheduler", "task_allocator")
    workflow.add_edge("task_allocator", "risk_assessor")
    workflow.add_conditional_edges("risk_assessor", router, ["insight_generator", END])
    workflow.add_edge("insight_generator", "task_scheduler")

    # Set up memory
    memory = MemorySaver()

    # Compile the workflow
    return workflow.compile(checkpointer=memory)