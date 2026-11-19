import asyncio
import webbrowser
from pathlib import Path

from dotenv import load_dotenv

# Load env vars BEFORE importing config, since config likely builds the LLM client at import time
load_dotenv()

from langgraph.graph import StateGraph, START, END
from config import GraphState  
from helper_function import ( 
    generate_character_description,
    generate_plot,
    generate_image_prompts,
    create_images,
    create_gif,
)


def create_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("generate_character_description", generate_character_description)
    workflow.add_node("generate_plot", generate_plot)
    workflow.add_node("generate_image_prompts", generate_image_prompts)
    workflow.add_node("create_images", create_images)
    workflow.add_node("create_gif", create_gif)

    workflow.add_edge(START, "generate_character_description")
    workflow.add_edge("generate_character_description", "generate_plot")
    workflow.add_edge("generate_plot", "generate_image_prompts")
    workflow.add_edge("generate_image_prompts", "create_images")
    workflow.add_edge("create_images", "create_gif")
    workflow.add_edge("create_gif", END)

    return workflow.compile()


async def run_workflow(app, query: str):
    """Run the LangGraph workflow and print results."""
    initial_state = {
        "messages": [],
        "query": query,
        "plot": "",
        "character_description": "",
        "image_prompts": [],
        "image_urls": [],
        "gif_data": None,
    }

    try:
        result = await app.ainvoke(initial_state)

        print("Character/Scene Description:")
        print(result["character_description"])

        print("\nGenerated Plot:")
        print(result["plot"])

        print("\nImage Prompts:")
        for i, prompt in enumerate(result["image_prompts"], 1):
            print(f"{i}. {prompt}")

        print("\nGenerated Image URLs:")
        for i, url in enumerate(result["image_urls"], 1):
            print(f"{i}. {url[:100] if url else url}")

        print("\nGIF generated successfully." if result["gif_data"] else "\nFailed to generate GIF.")
        return result
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def save_gif(gif_data: bytes) -> None:
    answer = input("Do you want to save the GIF? (yes/no): ").lower().strip()
    if answer not in ("yes", "y"):
        print("GIF not saved.")
        return

    filename = input("Enter the filename to save the GIF (e.g., animation_result.gif): ").strip() or "animation_result.gif"
    if not filename.endswith(".gif"):
        filename += ".gif"

    path = Path(filename).resolve()
    path.write_bytes(gif_data)
    print(f"GIF saved as {path}")

    # Replacement for IPython display(): open it in the default viewer/browser
    webbrowser.open(path.as_uri())


async def main():
    app = create_graph()
    query = "A dog wearing a top hat and monocle, sitting at a desk and writing a letter with a quill pen."
    result = await run_workflow(app, query)

    if result and result.get("gif_data"):
        save_gif(result["gif_data"])
    else:
        print("No GIF data available to display or save.")


if __name__ == "__main__":
    asyncio.run(main())