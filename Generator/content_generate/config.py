import os
import operator

from typing import TypedDict, List, Literal, Annotated

from pydantic import BaseModel

import os
import getpass



from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()
def _set_env(name: str):
    if not os.getenv(name):
        os.environ[name] = getpass.getpass(f"{name}: ")

# _set_env("LANGCHAIN_API_KEY")
# _set_env("LANGCHAIN_ENDPOINT")
# _set_env("LANGCHAIN_PROJECT")
# _set_env("LANGCHAIN_TRACING_V2")
# _set_env("TAVILY_API_KEY")




user_details = {
  "user_name": "LangGraph Team",
  "business_name": "LangGraph",
  "industry": "AI Tools and Frameworks",
  "business_type": "Tech Startup",
  "target_audience": ["AI Developers", "Machine Learning Enthusiasts", "Enterprise AI Teams"],
  "tone": "Professional",
  "objectives": ["Awareness", "Education"],
  "platforms": ["LinkedIn", "Twitter", "Medium"],
  "preferred_platforms": ["LinkedIn", "Twitter"],
  "platform_specific_details": {
    "twitter_handle": "@LangGraphAI",
    "linkedin_page": "linkedin.com/company/langgraph",
    "medium_page": "medium.com/langgraph"
  },
  "campaigns": [
    {
      "title": "Memory Management Module Launch",
      "date": "2024-05-20",
      "platform": "LinkedIn",
      "success_metric": "1000+ Shares"
    }
  ],
  "popular_hashtags": ["#LangGraph", "#MemoryManagement", "#AIFrameworks"],
  "themes": ["Memory Management", "AI Agent Development"],
  "short_length": 280,
  "long_length": 2000,
  "assets_link": "https://drive.google.com/drive/folders/langgraph-assets",
  "colors": ["#1E88E5", "#FFC107"],
  "brand_keywords": ["Innovative", "Efficient"],
  "restricted_keywords": ["Buggy", "Outdated"],
  "competitors": ["LangChain", "Pinecone"],
  "competitor_metrics": ["Content Shares", "Follower Growth"],
  "posting_schedule": ["Tuesday 10 AM", "Friday 3 PM"],
  "formats": ["Carousel", "Technical Blog"],
  "personal_preferences": "Use technical terms but keep explanations concise."
}


MODEL = 'gpt-4o-mini'
summ_model = ChatOpenAI(model =MODEL, reasoning_effort='none', temperature = 0.6 )
model = ChatOpenAI(model =MODEL, reasoning_effort='none', temperature = 0.6 )

Platform = Literal["Twitter","Linkedin","Instagram", "Blog"]


class ReserachQuestions(TypedDict):
    questions: List[str]


class InputState(TypedDict):
    text: str
    platforms: List[Platform]

class Sumamry_OutputState(TypedDict):
    text: str
    text_summary: str
    platforms: List[Platform]
class ResearchOutputState(TypedDict):
    text: str
    research: str
    platforms: list[Platform]
class FinalState(TypedDict):
    contents: Annotated[List, operator.add]

class IntentMatchingInputState(TypedDict):
    text: str
    research: str
    platforms: list[Platform]


class GeneratedContent(TypedDict):
    generated_content: str


class OverallState(TypedDict, total=False):
    text: str
    platforms: List[Platform]
    text_summary: str
    research: str
    contents: Annotated[List, operator.add]   # 4 nhánh song song cùng append vào đây
    generated_content: str