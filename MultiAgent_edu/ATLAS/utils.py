import os

from dotenv import load_dotenv
from typing import Dict, List, Annotated, Literal, TypeVar, Any, TypedDict, Optional
from operator import add
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone


from langchain_core.messages import BaseMessage


from openai import AsyncOpenAI, OpenAI
"""
========================
State definition
=========================
T  = TypeVar("T")
"""


load_dotenv()

def dict_reducer(dict1: Dict[str, Any], dict2: Dict[str, Any])-> Dict[str, Any]:
    """
    Merge two dictionaries recusively
    exmaple
    dict1 = {"a": {"x": 1}, "b": 2}
    dict2 = {"a": {"y": 2}, "c": 3}
    result = {"a": {"x": 1, "y": 2}, "b": 2, "c": 3}

    """
    merge = dict1.copy()
    for key, val  in dict2.items():
        if key in merge and isinstance(merge[key], dict) and isinstance(val, dict):
            merge[key] = dict_reducer(merge[key], val)
        else:
            merge[key] = val
    return merge





class AcademicState(TypedDict):
    """Master state container for acadamic assistance system"""

    messages: Annotated[List[BaseMessage], add]

    profile: Annotated[Dict, dict_reducer]          
    calendar: Annotated[Dict, dict_reducer]           
    tasks: Annotated[Dict, dict_reducer]             
    results: Annotated[Dict[str, Any], dict_reducer]  
class LLM_Config:
    """configuration set up llm"""
    base_url: str = os.getenv('BASE_URL')
    model: str = os.getenv("MODEL_NAME")
    max_tokens: int = 1024
    default_temp: float = 0.5


class NeMoLLaMa:
    """
    A class user the NVIDA's model through their API.
    This implementation uses AsyncOpenAI client for asychronous operation
    """

    def __init__(self, api_key: str):
        """Initialize with NeMoLLaMa with AOI key"""
        self.config = LLM_Config()
        self.client = AsyncOpenAI(
            base_url = self.config.base_url,
            api_key = api_key
        )
        self._is_authenticated = False

    async def check_auth(self) ->bool:
        """
        verify API authentication with test request
        Return:
            bools: authentication status
        """

        test_message = [{'role': 'user', 'content':'test'}]
        try:
            await self.agenerate(test_message, temperature = 0.1)
            self._is_authenticated = True
            return True
        except Exception as e:
            print(f" Authentication failed: {str(e)}")
            return False

    async def agenerate(self, messages: list[dict], temperature: Optional[float] = None)-> str:
        """
        Generate text using NeMo LLaMa model.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 1.0, default from config)

        Returns:
            str: Generated text response
        """
        completion = await self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=temperature or self.config.default_temp,
            max_tokens=self.config.max_tokens,
            stream=False
        )
        return completion.choices[0].message.content


"""
==========================
React agent

React is framework that combine reasoning and interactive process. It enables LLMs to complex tasks by break them down into:
1. REact: take action base on obsecation and tool
2. REason: Think about what to do next
3. REflect: learn from the output 

==========================
"""
class ReActAgent:
    """
    Base for class ReRact-based agent implementing for reasoning and action capability

    Features:
        - Tool managerment for specific actions
        - Few-shot learning example
        - Structured throught process
        - Action execution framework
    
    """
    def __init__(self, llm):
        """
        Initialize ReAct with language model and available tools.


        Attribution:
            llm: language model for agent operation        
        """

        self.llm = llm
        self.few_shot_examples = []
        self.tools = {
            'search_calendar':self.search_calendar,
            'analysis_tasks': self.analysis_tasks,
            'check_learning_style': self.check_learning_style,
            'check_performance': self.check_performance
        }
    async def search_calendar(self, state : AcademicState)-> list[dict]:
        """
        Search upcomming calendar event
        Args: 
            state: current academic state

        Return:
            List of upcomming event
        """

        events = state['calendar'].get('events', [])
        now = datetime.now(timezone.utc)

        return [e for e in events if datetime.fromisocalendar(e['start']['dateTime'])>now]


    async def analysis_tasks(self, state: AcademicState) -> list[dict]:
        """
        Analysis academic task from current state
        Args:
            state: current accademic state
        Return:
            List of academic tasks
        """
        return state['tasks'].get('tasks',[])

    async def check_learning_style(self, state: AcademicState)-> AcademicState:
        """
        Retrieval student's learning style and study patterns

        Args: 
            state: current academic state
        return
            update Academic state with learning style analysis 
        """
        profile = state['profile']
        learning_data = {
            'style': profile.get("learning_preferences", {}).get("learning_style", {}),
            'patterns': profile.get("learning_preferences", {}).get("study_patterns", {})
        }

        
        if 'results' not in state:
            state['results']= {}

        state['resutls']['learning_analysis'] = learning_data
        return state

    async def check_performance(self, state: AcademicState) -> AcademicState:
        """
        Check current academic performance across courses

        Args: 
            state: current academic state
        
        Return:
            Update state with performace analysis
        """
        profile = state["profile"]

        courses = profile.get('academic_info', {}).get('current_courses', [])

        if 'results' not in state:
            state['results'] = {}

        state['results']['performance_analysis'] = {'courses':courses}
        return state


