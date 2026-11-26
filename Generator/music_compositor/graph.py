import os
import pygame

from dotenv import load_dotenv

from langchain_core.runnables.graph import MermaidDrawMethod
from langgraph.graph import StateGraph, START, END



from helper_function import *
from config import AgentState
load_dotenv()
def create_graph():
    workflow = StateGraph(AgentState)

    # Add nodes to the graph    
    workflow.add_node("melody_generator", melody_generator)
    workflow.add_node("harmony_creator", harmony_creator)
    workflow.add_node("rhythm_analyzer", rhythm_analyzer)
    workflow.add_node("style_adapter", style_adapter)
    workflow.add_node("midi_converter", midi_converter)

    # Set the entry point of the graph
    workflow.set_entry_point("melody_generator")

    # Add edges to connect the nodes
    workflow.add_edge("melody_generator", "harmony_creator")
    workflow.add_edge("harmony_creator", "rhythm_analyzer")
    workflow.add_edge("rhythm_analyzer", "style_adapter")
    workflow.add_edge("style_adapter", "midi_converter")
    workflow.add_edge("midi_converter", END)

    return workflow.compile()


def play_midi(midi_file_path):
    """Play the generated MIDI file."""
    pygame.mixer.init()
    pygame.mixer.music.load(midi_file_path)
    pygame.mixer.music.play()

    # Wait for playback to finish
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    
    # Clean up
    pygame.mixer.quit()


if __name__ =="__main__":
    app = create_graph()
    
    
    png = app.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.API)

    # Chạy bằng `python file.py` thì display() không hiện gì -> lưu file
    with open("music_compositor.png", "wb") as f:
        f.write(png)
    print("Saved music_compositor.png")