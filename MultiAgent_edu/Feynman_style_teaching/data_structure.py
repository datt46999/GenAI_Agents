
import uuid
from typing import List

from pydantic import BaseModel, Field

from langgraph.store.memory import InMemoryStore

class Goals(BaseModel):
    """Structure of define learning goal"""
    goals : str = Field(None, description="Learning goals")

class LearningCheckPoint(BaseModel):
    """Structure for a single chechpoint"""
    description :str = Field(..., description ="Main checkpoint description")
    criteria : List[str] = Field(..., description = "List of success criterial")
    verification : str = Field(..., description="How to verify this checkpoint")


class Checkpoints(BaseModel):
    """Main checkpoint container for index tracking"""
    checkpoints : List[LearningCheckPoint] = Field(
            ..., description = "Main checkpoints covering foundation, application, mastery level."
        )


class SearchQuery(BaseModel):
    """Structure for search query collect"""
    search_queries :List = Field(..., description = "Search queries for retrieval")

class LearningVerification(BaseModel):
    """Structure for verification results"""
    understand_level : float= Field(..., ge =0, le = 1)
    feedback : str
    suggestions: List[str]
    context_aligment: bool
class FeynmanTeaching(BaseModel):
    """Structure base main teaching method"""
    similarity_level: str
    key_concepts: List[str]
    anologies: List[str]

class OutputStruture(BaseModel):
    """Structure question generate output"""
    question : str

class InContext(BaseModel):
    """Structure for verification context"""
    in_context : str = Field(..., description="Yes or No")


class ContextStore:
    """
        Store to management context chunks and their embedding in memory.

        A class that provides storage and retrieval of context data using an in-memory store.
        Each context entry consists of context chunk and corresponding their embedding
    """
    def __init__(self):
        """Initialize Context Store with empty in memory store"""

        self.store = InMemoryStore()

    def save_context(self, context_chunks: list, embeddings :list, key : str= None)-> str:
        """
        Save context chunks and their embedding to store
        """

        namespace = ('context', )


        if key is None:
            key = str(uuid.uuid4())

        value = {
            "chunks": context_chunks,
            "embeddings": embeddings
        }
        self.store.put(namespace, key, value)
        return key
    def get_context(self, context_key: str):
        """
        Retrieval context data from store using key
        """
        namespace = ('context', )
        memory = self.store.get(namespace, context_key) 
        return memory.value

