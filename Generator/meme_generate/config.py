import os 
from groq import Groq
from typing import TypedDict, Annotated, Dict, List, Sequence, Optional, Any
from pydantic import BaseModel, Field

from langchain_core.messages import HumanMessage, AIMessage
from langchain_groq import ChatGroq

# Initialize GROQ client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.7,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)
class CompanyContext(BaseModel):
    """Company context to be used to generate memes."""
    tone: str = Field(description = "The tone of voice of the company")
    target_audience: str = Field(description = "The target audience of the company")
    value_proposition: str = Field(description = "The value proposition of the company")
    key_products: List[str] = Field(description = "A list with the company's key products")
    brand_personality: str = Field(description = "The brand personality of the company")


class MemeConcept(BaseModel):
    message : str = Field(..., description = "The core message of the meme")
    emotion : str = Field(..., description = "The emotion conveyed of the meme")
    audience_relevant: str = Field(...,description = "The relevance of the meme to the audience")

class MemeConcepts(BaseModel):
    concepts: List[MemeConcept] = Field(description="List of meme concepts")


class TemplateInfo(BaseModel):
    template_id: str = Field(..., description="Unique identifier for the template")
    name: str = Field(..., description="Name of the meme template")
    blank_template_api_link: str = Field(..., description="API link to the blank template")
    description: str = Field(..., description="Description of the meme template")
    example_text_1: Optional[str] = Field("", description="Example text for the first line")
    example_text_2: Optional[str] = Field("", description="Example text for the second line")
    lines: int = Field(..., description="Number of text lines in the meme")
    keywords: List[str] = Field(..., description="Keywords associated with the template")

class SelectedMeme(BaseModel):
    meme_id : str = Field(..., description = "Unique identifier for the selected meme")
    template_id: str = Field(..., description = "Name of the meme template")
    concept: str = Field(..., description = "The concept associated with the meme")

    is_text_example1_filled: bool = Field(..., description = "Indicate if the first text element is filled")
    is_text_example2_filled: bool = Field(..., description = "Indicate if the second text element is filled")
    example_text1: Optional[str] = Field("", description = "Example text for the first line")
    example_text2: Optional[str] = Field("", description = "Example text for the second line")
    template_info: TemplateInfo = Field(...,description = "Information about the select template")
    blank_template_api_link : str = Field(..., description = "API link for the bland template without extension")

    blank_tempalte_api_extension: str = Field(..., description = "File extension for the bland template link")


class PreGeneratedMeme(BaseModel):
    meme_id: str = Field(..., description="Unique identifier for the selected meme")
    template_id: str = Field(..., description="ID of the selected template")
    concept: MemeConcept = Field(..., description="The concept associated with the meme")
    is_text_element1_filled: bool = Field(..., description="Indicates if the first text element is filled")
    is_text_element2_filled: bool = Field(..., description="Indicates if the second text element is filled")
    template_info: TemplateInfo = Field(..., description="Information about the selected template")
    blank_template_api_link: str = Field(..., description="API link to the blank template without extension")
    blank_template_api_link_extension: str = Field(..., description="File extension of the blank template link")
    generated_text_element1: str = Field(..., description="Generated text element 1")
    generated_text_element2: str = Field(..., description="Generated text element 2")

class GeneratedMeme(BaseModel):
    meme_id: str = Field(..., description="Unique identifier for the selected meme")
    template_id: str = Field(..., description="ID of the selected template")
    concept: MemeConcept = Field(..., description="The concept associated with the meme")
    is_text_element1_filled: bool = Field(..., description="Indicates if the first text element is filled")
    is_text_element2_filled: bool = Field(..., description="Indicates if the second text element is filled")
    template_info: TemplateInfo = Field(..., description="Information about the selected template")
    blank_template_api_link: str = Field(..., description="API link to the blank template without extension")
    blank_template_api_link_extension: str = Field(..., description="File extension of the blank template link")
    generated_text_element1: str = Field(..., description="Generated text element 1")
    generated_text_element2: str = Field(..., description="Generated text element 2")
    treated_text_element1: str = Field(..., description="Treated text element 1")
    treated_text_element2: str = Field(..., description="Treated text element 2")
    final_url: str = Field(..., description="Final URL of the generated meme")


class GraphState(TypedDict):
    """Enhanced state object for the meme generation workflow."""
    messages: Annotated[Sequence[HumanMessage | AIMessage], "Conversation messages"]
    website_url: Annotated[str, "Company website URL"]
    website_content: Annotated[List, "Website content"]
    company_context: Annotated[Dict[str, Any], "Analyzed company information"]
    meme_concepts: Annotated[List[dict], "Generated meme concepts"]
    selected_concepts: Annotated[List[dict], "Selected top 3 meme concepts"]
    selected_memes: Annotated[Dict[str, SelectedMeme], "Selected memes with their info"]
    pre_generated_memes: Annotated[Dict[str, PreGeneratedMeme], "Pre-Generated memes with their info"]
    generated_memes: Annotated[Dict[str, GeneratedMeme], "Pre-Generated memes with their info"]
    available_templates: Annotated[Dict[str, TemplateInfo], "Available meme templates"]



