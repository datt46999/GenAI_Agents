import os 
import re
import json
import asyncio
import aiohttp
import random

from config import *
from urllib.parse import quote
from PIL import Image
from io import BytesIO

from langchain_community.document_loaders import WebBaseLoader
from langchain_core.messages import HumanMessage

MAX_CONTENT_CHARS = 12000  # keep prompt within Groq token limits


def ensure_url(string: str)-> str:
    """
    Ensurelt a given string is a properly formatted URL by adding 'http://' if needed and validating the URL format

    Example:
        >>> ensure_url("example.com")
        'http://example.com'
        >>> ensure_url("https://example.com")
        'https://example.com'
    """

    if not string.startswith(("http://", "https://")):
        string = "http://"+string

    url_regex = re.compile(
        r"^(https?:\/\/)?"  # optional protocol
        r"(www\.)?"  # optional www
        r"([a-zA-Z0-9.-]+)"  # domain
        r"(\.[a-zA-Z]{2,})?"  # top-level domain
        r"(:\d+)?"  # optional port
        r"(\/[^\s]*)?$",  # optional path
        re.IGNORECASE,
    )

    if not url_regex.match(string):
        msg = f"Invalid URL: {string}"
        raise ValueError(msg)

    return string


def extract_json(text: str):
    """Extract the first JSON object/array from LLM text (handles ```json fences)."""
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in LLM output: {text[:200]}")
    return json.loads(match.group(1))


async def get_website_content(state: GraphState) -> GraphState:
    """
    Fetches and analyzes website content using WebBaseLoader
    

    Note: 
        - Uses WebBaseLoader for fetch HTML content
        - Handle encoding with utf-8
        - Update state with domained text content from all pages
        - Handle error and updates state with error message if fetch fail
    """
    website_url = state.get("website_url", "")
    try:
        validated_url = ensure_url(website_url)

        # FIX: web_paths must be a list, a plain str is iterated char by char ('h', 't', ...)
        web_loader = WebBaseLoader(web_paths=[validated_url], encoding='utf-8')
        text_docs = await asyncio.to_thread(web_loader.load)


        # extract content from all document
        content = []
        for doc in text_docs:
            content.append(doc.page_content)

        # Collapse excessive whitespace to save tokens
        text = re.sub(r"\n\s*\n+", "\n\n", "\n\n".join(content)).strip()
        state["website_content"] = text
        return state

    except Exception as e:
        print(f"Error fetching website content: {str(e)}")
        state["website_content"] = ""
        return state



def analyze_company_insights(state: GraphState) -> GraphState:
    """
    Analyzes company information from website content using llm
   
    Notes:
        - Using structure LLM with the consistant format
        - Analysis tone, target audience, value proposition, target products, and brand personality
        - Handle case where no content is available 
    """

    
    web_data = state.get("website_content") or ""
    if not web_data.strip():
        # FIX: stop early instead of sending an empty prompt (caused Groq tool_use_failed)
        raise ValueError(f"No website content fetched from {state.get('website_url')}")

    # Truncate to stay under the model's context / Groq TPM limit
    web_data = web_data[:MAX_CONTENT_CHARS]
    prompt =f"""
Analyze this company website content and provide insights in a JSON format  with the following structure:
{{
    'tone' : 'string describing the brand tone of voice(professional, casual, technical, etc.)',
    'target_audience' : 'string describing target audience/personal',
    'value_proposition': 'string describing their unique value proposition',
    'key_products': ['array', 'of', 'key', 'products', 'or','services' ],
    'brand_personality': 'string describing 3-5 brand personality traits' 
}}
Website Content:
{web_data}


Please ensure key_product always return as a array/list, if there's only one a product.
Be specific and base insights on the actual content.
"""


    # Groq models often return JSON as text (```json ...```) instead of calling the tool,
    # which makes with_structured_output() fail with 400 tool_use_failed.
    # -> call the LLM normally, then parse + validate the JSON ourselves.
    last_err = None
    for attempt in range(3):
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            data = extract_json(response.content)
            if isinstance(data.get("key_products"), str):
                data["key_products"] = [data["key_products"]]
            state["company_context"] = CompanyContext.model_validate(data)
            return state
        except Exception as e:
            last_err = e
            print(f"Company analysis failed (attempt {attempt + 1}/3): {e}")
    raise RuntimeError(f"Company analysis failed: {last_err}")


def generate_meme_concepts(state: GraphState)-> GraphState:
    """
    Generate meme concepts base on analyzed company insights

    notes:
        - Create 3 meme concepts base on company insights
        - Each concepts includs message, emotion and audience relevance
        - Parses JSON response to extract structure concept
        - Select top 3 concepts for further processing
    """
    insights = state["company_context"]  # FIX: typo "compapy"

    prompt = f"""
    Create 3 meme concept base on these company insights:

    Tone: {insights.tone}
    Target Audience: {insights.target_audience}
    Value Proposition: {insights.value_proposition}
    Key Products: {', '.join(insights.key_products)}
    Brand Personality: {insights.brand_personality}


    For each meme concept, provide:
    1. The main message/joke
    2. The intended emotional response
    3. How it ralates to the target audience


    Format the response as JSON array with structure:
    [{{"message": "string", "emotion": "string", "audience_relevance": "string"}}]

    """
    response = llm.invoke([HumanMessage(content = prompt)])
    # FIX: old regex r'\s*.*\s*' matched everything incl. ```json fences / extra text
    json_match = re.search(r'\[.*\]', response.content, re.DOTALL)

    if json_match:
        concepts_json = json_match.group(0)
        try:
            concepts = json.loads(concepts_json)
            state["meme_concepts"] = concepts
            state["selected_concepts"] = concepts[:3]  # Select top 3 concepts
            return state
        except json.JSONDecodeError:
            print("Failed to parse JSON response")

    print(f"Could not extract meme concepts from LLM output:\n{response.content}")
    return state


async def get_meme_templates() -> Dict[str, TemplateInfo]:
    """
    Fetch available meme templates from Memegen.link Api

    Notes:
        - Fetches templates from Memegen.link API
        - Filters templates to those with 2 or fewer lines
        - Randomly selects 20 templates
        - Converts API response to TemplateInfo objects
        - Includes template metadata like name, description, and example text
    """

    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.memegen.link/templates/") as response:
            all_templates = await response.json()

            # Filter templates with 2 or fewer lines
            filtered_templates = [
                template for template in all_templates
                if template.get("lines", 0) <= 2
            ]

            # Select 20 random templates
            selected_templates = random.sample(filtered_templates, min(20, len(filtered_templates)))

            # Convert to dictionary with template ID as key, mapping fields to TemplateInfo
            template_dict = {
                template["id"]: TemplateInfo(
                    template_id=template["id"],
                    name=template["name"],
                    blank_template_api_link=template["blank"],
                    description=f"{template['name']} meme with {template['lines']} text lines.",
                    example_text_1=template.get('example', {}).get('text', [''])[0] or '',
                    example_text_2=template.get('example', {}).get('text', ['', ''])[1] if len(template.get('example', {}).get('text', [])) > 1 else '',
                    lines=template["lines"],
                    keywords=template.get("keywords", [])
                )
                for template in selected_templates
            }
            return template_dict


def select_meme_templates(state: GraphState) -> GraphState:
    """
    Select appropriate meme tempalate for each concept


    Notes:
        - Create simiplited template description for LLM
        - Matches concept with appropritate template
        - Falls back to random selection if no match found
        - Handle tamplate selection with for each concept
        - Create structures meme object with template info
    """

    concepts = state["selected_concepts"]
    templates = state["available_templates"]
    selected_memes ={}

    template_descriptions = [
        {
            'template_id': template_id,
            'name': template_data.name,
            'description': template_data.description,
            'lines': template_data.lines
        }
        for template_id, template_data in templates.items()
    ]


    for idx, concept in enumerate(concepts):
        prompt = f"""
        Select a meme template that best fits this concept:

                Concept:
                - Message: {concept['message']}
                - Emotion: {concept['emotion']}
                - Audience Relevance: {concept['audience_relevance']}

                Available Templates:
                {json.dumps(template_descriptions, indent=2)}

        Return only the template ID that best matches the concept's message and emotion.

        """

        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            # Extract template ID from response, removing quotes and whitespace
            raw = response.content.strip().strip('`').strip().strip('"').strip("'").lower()
            # LLM may answer with extra words -> pick the first known id it mentions
            template_id = raw if raw in templates else next(
                (tid for tid in templates if re.search(rf"\b{re.escape(tid)}\b", raw)), raw
            )

            # Fallback to random template if not found
            if template_id not in templates:
                template_id = random.choice(list(templates.keys()))

            # Create meme object
            selected_memes[f"meme_{idx+1}"] = {
                "meme_id": f"meme_{idx+1}",
                "template_id": template_id,
                "concept": concept,
                "template_info": templates[template_id],
                "blank_template_api_link": templates[template_id].blank_template_api_link,
                "is_text_element1_filled": True,
                "is_text_element2_filled": templates[template_id].lines >= 2
            }

        except Exception as e:
            print(f"Error selecting template: {str(e)}")
            continue

    state["selected_memes"] = selected_memes
    return state

def  generate_text_elements(state: GraphState) -> GraphState:
    """
    Generate meme text based on selected concepts and template

    Notes:
        - Generates appropriate text for each template
        - Consider template format and number of line
        - Maintains guide tone and target audience
        - Creates concise, punchy text elements
        - Handles errors gracefully for each meme
    """


    selected_meme = state["selected_memes"]
    context = state["company_context"]
    pre_generated_memes = {}


    for meme_id, meme in selected_meme.items():
        concept = meme["concept"]
        template_info = meme["template_info"]

        prompt = f"""
        Create text for a meme bases on this template and concept:


        Template: {template_info.name}
        Number of lines: {template_info.lines}
        Example Text 1: {template_info.example_text_1}
        Example Text 2: {template_info.example_text_2}
        Concept Message: {concept['message']}
        Emotion: {concept['emotion']}

        Company Context:
        Target Audience: {context.target_audience}
        Brand Tone: {context.tone}

        Return ONLY the text lines, one per line. Keep each line concise and punchy.
        """
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            # FIX: drop blank lines, numbering ("1.", "Line 1:") and wrapping quotes
            text_elements = []
            for line in response.content.strip().split('\n'):
                line = re.sub(r'^\s*(?:line\s*\d+\s*[:.-]|\d+\s*[.):-]|[-*])\s*', '', line, flags=re.I)
                line = line.strip().strip('"').strip("'").strip()
                if line:
                    text_elements.append(line)

            generated_text1 = text_elements[0] if len(text_elements) > 0 else ""
            generated_text2 = text_elements[1] if len(text_elements) > 1 else ""

            pre_generated_memes[meme_id] = {
                **meme,
                "generated_text_element1": generated_text1,
                "generated_text_element2": generated_text2
            }

        except Exception as e:
            print(f"Error generating text: {str(e)}")
            continue

    state["pre_generated_memes"] = pre_generated_memes
    return state


def escape_memegen_text(text: str) -> str:
    """
    Escape text for the Memegen.link URL format.
    See https://memegen.link/#special-characters
    """
    if not text:
        return "_"  # memegen's placeholder for an empty line
    replacements = [
        ("_", "__"), ("-", "--"), (" ", "_"), ("?", "~q"), ("&", "~a"),
        ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\\", "~b"),
        ("<", "~l"), (">", "~g"), ('"', "''"), ("\n", "~n"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return quote(text, safe="_~'")


def create_meme_url(state: GraphState) -> GraphState:
    """
    Creates final meme URLs using the Memegen.link API format.

  
    Notes:
        - Processes text elements for URL compatibility
        - Handles URL encoding of text
        - Extracts and manages file extensions
        - Constructs final meme URLs
        - Maintains all meme metadata in state
    """
    pre_generate_meme = state["pre_generated_memes"]
    generated_memes ={}


    for meme_id, meme in pre_generate_meme.items():
        # FIX: proper memegen escaping (plain quote() breaks on '_', '-', '?', '/')
        text1 = escape_memegen_text(meme["generated_text_element1"])
        text2 = escape_memegen_text(meme["generated_text_element2"])

        # Get template info
        template_info = meme["template_info"]
        base_url = template_info.blank_template_api_link

        # Extract extension
        extension = os.path.splitext(base_url)[1]
        base_url = base_url.rsplit('.', 1)[0]

        # Construct final URL
        if meme.get("is_text_element2_filled", True):
            final_url = f"{base_url}/{text1}/{text2}{extension}"
        else:
            final_url = f"{base_url}/{text1}{extension}"  # 1-line template

        generated_memes[meme_id] = {
            **meme,
            "final_url": final_url,
            "text_elements": [text1, text2]
        }

    state["generated_memes"] = generated_memes
    return state

async def display_meme(url: str):
    """
    Display a meme from a given URL
    
    Notes:
        - Fetches image data asynchronously
        - Converts bytes to PIL image
        - Handles HTTP errors
        - Reports failures without crashing
    """


    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    image = Image.open(BytesIO(image_data))
                    return image
                else:
                    print(f"Failed to fetch image: Status {response.status}")
                    return None
    except Exception as e:
        print(f"Error displaying meme: {str(e)}")
        return None