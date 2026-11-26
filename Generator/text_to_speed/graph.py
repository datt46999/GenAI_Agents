from langgraph.graph import StateGraph, START, END
from langchain_core.runnables.graph import MermaidDrawMethod

from config import AgentState
from helper_functions import *
def create_graph():
    workflow = StateGraph(AgentState)

    # Add nodes to the graph
    workflow.add_node("classify_content", classify_context)
    workflow.add_node("process_general", process_generate)
    workflow.add_node("process_poem", process_poem)
    workflow.add_node("process_news", process_news)
    workflow.add_node("process_joke", process_joke)
    workflow.add_node("text_to_speech", text_to_speech)

    # Set the entry point of the graph
    workflow.set_entry_point("classify_content")

    # Define conditional edges based on content type
    workflow.add_conditional_edges(
        "classify_content",
        lambda x: x["content_type"],
        {
            "general": "process_general",
            "poem": "process_poem",
            "news": "process_news",
            "joke": "process_joke",
        }
    )

    # Connect processors to text-to-speech
    workflow.add_edge("process_general", "text_to_speech")
    workflow.add_edge("process_poem", "text_to_speech")
    workflow.add_edge("process_news", "text_to_speech")
    workflow.add_edge("process_joke", "text_to_speech")
    return workflow.compile()


if __name__ =="__main__":
    app = create_graph()
    
    
    png = app.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.API)

    # Chạy bằng `python file.py` thì display() không hiện gì -> lưu file
    with open("tts.png", "wb") as f:
        f.write(png)
    print("Saved graph.png")