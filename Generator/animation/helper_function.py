import os
import base64
import asyncio
import aiohttp
import io

from PIL import Image
from langchain_core.messages import HumanMessage, AIMessage


from config import GraphState, llm, client 



async def get_image_data(session, url: str):
    """Fetch image data from a given URL."""
    if url.startswith("data:"):
        return base64.b64decode(url.split(",", 1)[1])
    async with session.get(url) as response:
        if response.status == 200:
            return await response.read()
    return None


def generate_character_description(state: GraphState) -> GraphState:
    """
    Generate detailed description of the main character of scene
    """
    query = state["query"]
    response = llm.invoke([HumanMessage(content = f"""Base on the query '{query}', create detail description of main charactoer or scene. 
                                       Include specific details about appearance, characteristics, and any unique features.
                                       This description will be use to maintain consistency across multiple images.""")])

    state['character_description'] = response.content
    return state


def generate_plot(state: GraphState)-> GraphState:
    """
    generate a 5 step plot for the GIF animation
    """
    query = state["query"]
    character_description = state["character_description"]
    response = llm.invoke([HumanMessage(content = f"""Create a short, 5-step plot for a GIF based on this query: '{query}' and feature description: {character_description}.
    Each step should be a brief description of a single frame, maintaining consistency thoughout.
    Keep it family-friendly and avoid any sensitive themes.
    """)])

    state["plot"] = response.content

    return state

def generate_image_prompts(state: GraphState)-> GraphState:
    """
    Generate specific of prompt of generate each frame of the GIF
    """
    plot = state["plot"]
    character_description = state['character_description']
    response = llm.invoke([HumanMessage(content = f"""Based on the plot: {plot} and feature description: {character_description}, generate 5 specific, family-friendly image prompts, one for each step.
    Each prompt should be detailed enough for image generation, maintaining consisquenc, and suitable for an AI image model.

    Alway include the following in EVERY prompt in maintain consistency:
    1. A brief remainder of the main character or object key images.
    2. The specific action or scene described in the per plot.
    3. Any relevant background or enviromental details.

    Format each prompt as number each item like this:
    1. [Your prompt here]
    2. [Your prompt here]
    ... and so on
    """)])

    prompts = []
    for line in response.content.split('\n'):
        if line.strip().startswith(('1.', '2.','3.', '4.', '5.')):
            prompt = line.split('.',1)[1].strip()
            # prompt.append(f"Create detail, photorealistic image for the following scene: {prompt}")
            prompts.append(f"Create a detailed, photorealistic image of the following scene: {prompt}")

    if len(prompts )!=5:
        raise ValueError(f"Expected 5 prompts, but get {len(prompts)}. Please try again.")

    state['image_prompts'] = prompts
    return state


async def create_image(prompt: str, retries: int= 3)-> GraphState:
    """
    Generate image using LLM base on given prompt
    """
    for attempt in range(retries):
        for attempt in range(retries):
            try:
                response = await asyncio.to_thread(
                    client.images.generate,
                    model="gpt-image-2.5-flare",
                    prompt=prompt,
                    size="1024x1024",
                    n=1,
                )
                # GPT image models return base64 data instead of a URL
                return f"data:image/png;base64,{response.data[0].b64_json}"
            except Exception as e:
                if attempt == retries - 1:
                    print(f"Failed to generate image for prompt: {prompt}")
                    print(f"Error: {str(e)}")
                    return None
                await asyncio.sleep(2)  # Wait before retrying


async def create_images(state: GraphState) -> GraphState:
    """Generate images for all prompts in parallel."""
    image_prompts = state["image_prompts"]
    tasks = [create_image(prompt) for prompt in image_prompts]
    image_urls = await asyncio.gather(*tasks)
    state["image_urls"] = image_urls
    return state

async def create_gif(state: GraphState) -> GraphState:
    """Create a GIF from the generated images."""
    image_urls = state["image_urls"]
    images = []
    async with aiohttp.ClientSession() as session:
        tasks = [get_image_data(session, url) for url in image_urls if url]
        image_data_list = await asyncio.gather(*tasks)
    
    for img_data in image_data_list:
        if img_data:
            images.append(Image.open(io.BytesIO(img_data)))
    
    if images:
        gif_buffer = io.BytesIO()
        images[0].save(gif_buffer, format='GIF', save_all=True, append_images=images[1:], duration=1000, loop=0)
        state["gif_data"] = gif_buffer.getvalue()
    else:
        state["gif_data"] = None
    return state