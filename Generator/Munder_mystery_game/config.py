import operator



from typing import TypedDict, Annotated, Sequence, Optional, List
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage


MODEL = "gpt-4o-mini"  # OpenAI's listed successor to gpt-4o, which it retires on 2027-01-14
llm = ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0) 

class Character(BaseModel):
    """
    Define the class charactor and all structure output from the LLM while generate characters
    """

    role: str = Field(description = "Primary role of the character in the story")
    name: str = Field(description = "Name of the character")
    backstory: str = Field(description = "Backstory of the character focus, concerns, and motives.")


class StoryDetails(BaseModel):
    """
    Define the game story and allow for structure output from the LLM while generation the Game Story
    """
  
    victim_name: str = Field(
        description="Name of the murder victim"
    )
    time_of_death: str = Field(
        description="Approximate time when the murder occurred"
    )
    location_found: str = Field(
        description="Where the body was discovered"
    )
    murder_weapon: str = Field(
        description="The weapon or method used in the murder"
    )
    cause_of_death: str = Field(
        description="Specific medical cause of death"
    )
    crime_scene_details: str = Field(
        description="Description of the crime scene and any relevant evidence found"
    )
    witnesses: str = Field(
        description="Information about potential witnesses or last known sightings"
    )
    initial_clues: str = Field(
        description="Initial clues or evidence found at the scene"
    )
    npc_brief:str = Field(
        description="Brief description of the characters and their relationships"
    )

class ConversationState(TypedDict):
    """
    A class define an manage the state for a conversation
    """
    messages: Annotated[Sequence[BaseMessage], operator.add]
    character: Character # Character being interviewed
    story_details: Optional[StoryDetails]  # Details about the murder mystery


class GenerateGameState(TypedDict):

    """
    Define and manage the overrall State of the game
    """
    messages: Annotated[Sequence[BaseMessage], operator.add]
    environment: str  # Story environment
    max_characters: int  # Number of characters
    characters: List[Character]  # Characters in the story
    story_details: Optional[StoryDetails]  # Details about the murder mystery
    selected_character_id: Optional[int] # Index of the selected character
    num_guesses_left: int # Number of guesses the player has
    result: str #Store the Guesser result and evalute Correct/Incorrect