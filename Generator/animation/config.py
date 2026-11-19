import os
from typing import TypedDict, Annotated, Sequence, List
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from openai import OpenAI
client = OpenAI()
load_dotenv()
llm = ChatOpenAI(model = os.getenv("MODEL_NAME"), use_responses_api=False)


class GraphState(TypedDict): 
    messages: Annotated[Sequence[HumanMessage | AIMessage], "This message in the conversation."]
    query : Annotated[str, "Input query describing the character and scene."]

    character_description: Annotated[str, "Detailed description of the main character or object"]
    plot: Annotated[str, "Generate plor fot the GIF"]
    
    image_prompts : Annotated[List[str], "List of prompt for each frame"]
    image_urls: Annotated[List[str], "List of URLs for generated images"]

    gif_data: Annotated[bytes, "GIF data in bytes"]
