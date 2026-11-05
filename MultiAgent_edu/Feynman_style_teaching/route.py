
import operator
from typing import TypedDict, Annotated, List, Dict
from pydantic import BaseModel, Field

from langgraph.graph import END
from data_structure import ContextStore,SearchQuery, Checkpoints, LearningVerification, FeynmanTeaching, OutputStruture, Goals

class LearningState(TypedDict):
    topic: str
    goals: List[Goals]
    context: str
    context_chunks: Annotated[List, operator.add]
    context_key : str
    search_queries: SearchQuery 
    checkpoints: Checkpoints
    verifications: LearningVerification
    teachings: FeynmanTeaching
    current_checkpoint: int
    current_question: OutputStruture
    current_answer: str


    
"""
=======================================================
Router logic functions
=======================================================
"""
def route_context(state: ContextStore):
    
    """determite whether to process existing context or generate new search query"""
    if state.get('context'):
        return "chunk_context"

    return "generate_query"

def route_verification(state: LearningState):
    """Determines next step based one verification resutls and  checkpoint process"""
    cur_checkpoint = state["current_checkpoint"]

    if state["verifications"].understand_level<0.7:
        return "teach_concept"


    if cur_checkpoint + 1 < len(state['checkpoints'].checkpoints):
        return 'next_checkpoint'
    
    return END

def route_teaching(state: LearningState):
    """Routes to next step or end  session after teaching intervention"""
    cur_checkpoint = state["current_checkpoint"]
    if cur_checkpoint +1 < len(state["checkpoints"].checkpoints):
        return "next_checkpoint"

    return END


def route_search(state: LearningState):
    """Directs flow between question generation and web search based on query status."""
    if state['search_queries'] is None:
        return "generate_question"
    return "search_web"