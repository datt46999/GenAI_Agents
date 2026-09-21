import asyncio
import json
import os
import re
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, Union, Literal

from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, START, END

from utils import AcademicState, NeMoLLaMa
from advisor_agent import AdvisorAgent
from notewrite_agent import NoteWriteAgent
from planner_agent import PlannerAgent
from data_manager import DataManager
from coordinator_agent import coordinator_agent
from system_prompts import PROFILE_ANALYZER_PROMPT

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.style import Style
"""
setting:

"""
load_dotenv()
llm_key= os.getenv("MEMOTRON_3_5_LIGHTNING_30B_A3B_KEY")
llm = NeMoLLaMa(llm_key)

class AgentExecutor:
    def __init__(self, llm):
        """
        Initialize executor with a langguage model and crete agent instance
        
        Args:
            llm: langguage model instance to use create agent


        """
        self.llm = llm
        self.agents ={
            "PLANNER": PlannerAgent(llm),
            "NOTEWRITER": NoteWriteAgent(llm),
            "ADVISOR":AdvisorAgent(llm)
        } 


    async def execute(self, state: AcademicState)-> dict:
        """
        Orchestrates concurrent executor  of multiple agent base on analysis results 
        
        This methob implements a sophiticated executed pattern 
        1 Reads coordination analysis to determini required agent
        2. Group agents and concurrent executor
        3. Execute agent group in parallel
        4. Handel faillure gratefull with fallback machanisms

        Args:
            state: current academic state with containing analysis result
        Return: 
            dict: merge all of results  from exeuted agent return 
        """
        try:
            analysis = state["results"].get("coordinator_analysis", {})
            required_agents = analysis.get("required_agents", ["PLANNER"])  # PLANNER as default
            concurrent_groups = analysis.get("concurrent_groups", [])  

            results = {}

            for group in concurrent_groups:
                tasks= []
                for agent_name in group:
                    if agent_name in required_agents and agent_name in self.agents:
                        tasks.append(self.agents[agent_name](state))

                if tasks:
                    # gather result from concurrent execution
                    group_result = await asyncio.gather(*tasks, return_exceptions= True)

                    for agent_name, result in zip(group, group_result):
                        if not isinstance(result, Exception):
                            results[agent_name.lower()]= result

            if not results and 'PLANNER' in self.agents:
                planner_results = await self.agents['PLANNER'](state)
                results["planner"] = planner_results

            print("agent output: ", results )

            return {
                'results':{
                    'agent_output': results
                }
            }
        except Exception as e:
            print(f"Execution error: {e}")
            # Emergency fallback with minimal response
            return {
                "results": {
                    "agent_outputs": {
                        "planner": {
                            "plan": "Emergency fallback plan: Please try again or contact support."
                        }
                    }
                }
            }

"""
========================
Agent action and agent ouput
========================
"""
class AgentAction(BaseModel):
    """
    Model representing agent's action decision
    
    Attributes:
        action [str]: the specific action to be taken (eg: search_calendar, analysis_task)
        tools (Optional[str]): The action tool use to be for the action 
        thought [str]: The reasing process behind the action choice
        action_input Optional[Dict]: Input parameter for the action
    """
    action: str
    thought : str
    tools : Optional[str] = None
    action_input : Optional[dict] = None


class AgentOutput(BaseModel):
    """
    The Model represented output for agent action.
    Attributed
        obsevation (str): the results or obsevation for excuting the action
        output (Dict): Structured output data from action
    """
    obsevation : str
    output : dict 
    



"""
=======================
Profile analyzer

Analysis student profile and interpret learning preference usin ReAct frameWork

=======================
"""

async def profile_analyzer(state : AcademicState)-> dict:
    """
    Analysis student profile and interpret learning preferences using ReAct framework

    This agent specialized in:
    1 Deep analysis of student learning profile
    2 Extraction of learning preferences and patterns
    3 Interpreptation of academic history and tendencies
    4 Generate of personalized  learning insight
    """
    profile = state['profile']
    prompt = PROFILE_ANALYZER_PROMPT

    messages = [
        # System message defines analysis framework and expectations
        {"role": "system", "content": prompt},
        # User message contains serialized profile data for analysis
        {"role": "user", "content": json.dumps(profile)}
    ]
    response = await llm.agenerate(messages)

    # Format and structure the analysis results
    return {
        "results": {
            "profile_analysis": {
                "analysis": response  # Contains structured learning preference analysis
            }
        }
    }


def create_agent_graph(llm)->StateGraph:
    """
    Create a coordinated workflow graph for multi agents.

    This orchestration system manager parallel execution of three specialize agent:
    +planner agent: Handle schedule and calendar managerment
    +note writer agent: create personalized study material
    +advisor agent: procide academis guidance and suppost

    The workflow uses a state machine approach with conditional routing base on analysis and student needs
    Args:
        llm: langguage model instance
    Return: 
        Complied workflow graph with parallel execution path
    """

    workflow = StateGraph(AcademicState)
    planner_agent = PlannerAgent(llm)
    notewriter_agent = NoteWriteAgent(llm)
    advisor_agent = AdvisorAgent(llm)
    executor = AgentExecutor(llm)
    # pallel execution routing
    
    workflow.add_node('coordinator', coordinator_agent)
    workflow.add_node('execute', executor.execute)
    workflow.add_node('profile_analyzer', profile_analyzer)
    def route_to_parallel_agents(state: AcademicState)-> StateGraph:
        """
            determine which agent should be process with current agent

            Analyzer coordination's output to route work to apporiable agent.
            Default planner if no specific agents are required

            Args:
                state : Current academy state with coordination analysis
            return:
                List of agent next
        """
        analysis = state["results"].get("coordinator_analysis", {})
        require_agent = analysis.get("required_agents",[])

        next_nodes = []

        if "PLANNER" in require_agent:
            next_nodes.append('calendar_analyzer')
        if "NOTEWRITE" in require_agent:
            next_nodes.append('notewriter_analyze')
        if "ADVISOR" in require_agent:
            next_nodes.append('advisor_analyze')

        return next_nodes if next_nodes else ['calendar_analyzer']

    """
    ===============================
    Agent Subgraph Node
    ===============================
    """
    # planner agent workflow
    workflow.add_node("calendar_analyzer", planner_agent.calendar_analysis)
    workflow.add_node("task_analyzer", planner_agent.task_analysis)
    workflow.add_node("plan_generator", planner_agent.plan_generate)

    # planner agent workflow
    workflow.add_node("notewriter_analyze", notewriter_agent.learning_style_analysis)
    workflow.add_node("notewriter_generate", notewriter_agent.generate_notes)

    # Advisor agent's workflow  
    workflow.add_node("advisor_analyze", advisor_agent.analyze_situation)
    workflow.add_node("advisor_generate", advisor_agent.generate_guidance)


    """
    ===============================
    Work Connection
    ===============================
    """

    workflow.add_edge(START, 'coordinator')
    workflow.add_edge('coordinator', 'profile_analyzer')

    # connect profile analyzer to potential parallel paths
    workflow.add_conditional_edges(
        'profile_analyzer',
        route_to_parallel_agents,
        ["calendar_analyzer", "notewriter_analyze", "advisor_analyze"]
    )

    # Connect Planner agent's internal workflow
    workflow.add_edge("calendar_analyzer", "task_analyzer")
    workflow.add_edge("task_analyzer", "plan_generator")
    workflow.add_edge("plan_generator", "execute")

    # Connect NoteWriter agent's internal workflow
    workflow.add_edge("notewriter_analyze", "notewriter_generate")
    workflow.add_edge("notewriter_generate", "execute")

    # Connect Advisor agent's internal workflow
    workflow.add_edge("advisor_analyze", "advisor_generate")
    workflow.add_edge("advisor_generate", "execute")


    def should_end(state) -> Union[Literal["coordinator"], Literal[END]]:
        """Determines if all required agents have completed their tasks.

        Compares the set of completed agent outputs against required agents
        to decide whether to end or continue the workflow.

        Args:
            state: Current academic state

        Returns:
            Either "coordinator" to continue or END to finish
        """
        analysis = state["results"].get("coordinator_analysis", {})
        executed = set(state["results"].get("agent_outputs", {}).keys())
        required = set(a.lower() for a in analysis.get("required_agents", []))
        return END if required.issubset(executed) else "coordinator"

    # Add conditional loop back to coordinator if needed
    workflow.add_conditional_edges(
        "execute",
        should_end,
        {
            "coordinator": "coordinator",  # Loop back if more work needed
            END: END  # End workflow if all agents complete
        }
    )

    # Compile and return the complete workflow
    return workflow.compile()
     

