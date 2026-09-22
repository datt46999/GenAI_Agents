import os
import json

from dotenv import load_dotenv
from typing import Dict, List
from utils import AcademicState, NeMoLLaMa, OpenAILLM
import traceback


from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage


from system_prompts import COORDINATOR_PROMPT

load_dotenv()
# llm_key = os.getenv("MEMOTRON_3_5_LIGHTNING_30B_A3B_KEY")
# llm = NeMoLLaMa(llm_key)


openai_key = os.getenv("OPENAI_API_KEY")
llm = OpenAILLM(openai_key)
async def analyses_context(state: AcademicState) -> Dict:
    """
    Analysis the academic state context to inform coordination decision-making
    This function performs comprehensive context analysis by:
    1 Extract student profile information.
    2 Analysis calendar and task load
    3 Identifying relevant course context from the last messager
    4 Gather learning preferences and study patterns


    Args:
        state: current academic state include profile, calander, tasks
    Return:
        Structure analysis of the student's context for decision making
    """

    profile = state.get('profile', {})
    calendar = state.get('calendar', {})
    tasks = state.get('tasks', {})

    courses = profile.get('academic_info',{}).get('current_courses', [])
    current_course = None
    request = state['messages'][-1].content.lower()


   

    for course in courses:
        if course['name'].lower() in request:
            current_course = course
            break

    return {
        "student": {
            "major": profile.get("personal_info", {}).get("major", "Unknown"),
            "year": profile.get("personal_info", {}).get("academic_year"),
            "learning_style": profile.get("learning_preferences", {}).get("learning_style", {}),
        },
        "course": current_course,
        "upcoming_events": len(calendar.get("events", [])),  # Calendar load indicator
        "active_tasks": len(tasks.get("tasks", [])),        # Task load indicator
        "study_patterns": profile.get("learning_preferences", {}).get("study_patterns", {})
    }


  

def parse_coordinator_response(response: str) -> Dict:
    """
    Parse coordinator response into structure analysis for agent execution


    This function implements a robust parsing trategy:
    1 Start with safe default configuration
    2 Analysis ReAct base on response
    3 Adjust agent requirement and priorities base on content
    4 Organize the concurrent execution group
    
    Args:
        response: Raw LLM response text
    Return:
        dict: structure analysis containing
            requiered_agent : List of agent needed
            priority : priority level need for each agent
            concurrent_group: group of agent that can run together 
            reasoning: extracted reasoning for decisions
    """
    try:
        analysis = {
            "required_agents": ["PLANNER"],         # PLANNER is always required
            "priority": {"PLANNER": 1},             # Base priority structure
            "concurrent_groups": [["PLANNER"]],     # Default execution group
            "reasoning": "Default coordination"      # Default reasoning
        }
        # parse ReAct for advance coordination
        if "Thought" in response and "Decision" in response:
            # check NoteWriter requirements
            if "NoteWriter" in response or 'note' in response.lower():
                analysis['required_agents'].append("NOTEWRITER")
                analysis['priority']['NOTEWRITE'] = 2
                analysis["concurrent_groups"] = [['PLANNER', 'NOTEWRITER']]

            # check advisor requirements
            if 'Advisor' in response or 'guidance' in response.lower():
                analysis['required_agents'].append("ADVISOR")
                analysis['priority']['ADVISOR'] = 3

            # extract and store reasoning from throught section
            though_section = response.split('Thought:')[1].split('Action:')[0].strip()
            analysis['reasoning'] = though_section

        return analysis
    except Exception as e:
        print(f"Parse error: {str(e)}")
        # Fallback to safe default configuration
        return {
            "required_agents": ["PLANNER"],
            "priority": {"PLANNER": 1},
            "concurrent_groups": [["PLANNER"]],
            "reasoning": "Fallback due to parse error"
        }

async def coordinator_agent(state: AcademicState) -> dict:
    """
    Primary coordinator agent the orchestrate multiple academic support agents using ReAct Framework

    this agent implements a sophiticated coordination trategy:
    1 Analysis academic context and student need
    2 uses ReAct framework for structured decision making
    3 Coordination parrallel agent execution
    4 handel fallback scenarios

    Args:
        state: current academic state including messages and context
    Return:
        Coordination analysis including require agent, priorities and execution group 
    """
    # print("COORD state keys:", list(state.keys()), "| messages:", state.get("messages"))
    try:
        # Analyze current context and extract lastest querry
            context = await analyses_context(state)
            query = state['messages'][-1].content
        
        
            # define ReAct base on coordination prompt
            prompt = COORDINATOR_PROMPT
        
            # generate coordination plan using llm
            response = await llm.agenerate([
                {'role':'system', 'content':prompt.format(
                    request= query,
                    context = json.dumps(context, indent = 2)
                )},
        
            ])


            
            # # parse response and structure coordinary analysis
            # analysis = parse_coordinator_response(response)
            # system_prompt = COORDINATOR_PROMPT.format(
            #     request=query,
            #     context=json.dumps(context, indent=2),
            # )

            # response = await llm.ainvoke([
            #     SystemMessage(content=system_prompt),
            #     HumanMessage(content=query),
            # ])
            # text = response.content

            analysis = parse_coordinator_response(response) or {}

            
            return {
                    "results": {
                        "coordinator_analysis": {
                            "required_agents": analysis.get("required_agents", ["PLANNER"]),
                            "priority": analysis.get("priority", {"PLANNER": 1}),
                            "concurrent_groups": analysis.get("concurrent_groups", [["PLANNER"]]),
                            "reasoning": response
                        }
                    }
                }
        
    except Exception as e:
        print(f"Coordinator error: {e}")
        traceback.print_exc()
        # Fallback to basic planning configuration
        return {
            "results": {
                "coordinator_analysis": {
                    "required_agents": ["PLANNER"],
                    "priority": {"PLANNER": 1},
                    "concurrent_groups": [["PLANNER"]],
                    "reasoning": "Error in coordination. Falling back to planner."
                }
            }
        }

