
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from config import *
from helper_function import *
from langchain_core.runnables.graph import MermaidDrawMethod

load_dotenv()
def create_graph():
    builder = StateGraph( OverallState, input=InputState, output=GeneratedContent)

    # Nodes
    builder.add_node("summary_node",summary_text)
    builder.add_node("research_node", research_node)
    builder.add_node("intent_matching_node", IntentMatching)
    builder.add_node("instagram", Insta)
    builder.add_node("twitter", Twitter)
    builder.add_node("linkedin", Linkedin)
    builder.add_node("blog", Blog)
    builder.add_node("combine_content", combining_content)


    # Flow
    builder.add_edge(START, "summary_node")
    builder.add_edge("summary_node", "research_node")
    builder.add_edge("research_node", "intent_matching_node")
    builder.add_edge("intent_matching_node", "instagram")
    builder.add_edge("intent_matching_node", "twitter")
    builder.add_edge("intent_matching_node", "linkedin")
    builder.add_edge("intent_matching_node", "blog")
    builder.add_edge("blog", "combine_content")
    builder.add_edge("twitter", "combine_content")
    builder.add_edge("instagram", "combine_content")
    builder.add_edge("linkedin", "combine_content")
    builder.add_edge("combine_content", END)

    return builder.compile()

if __name__ == "__main__":
    app = create_graph()
        
        
    png = app.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.API)

    # Chạy bằng `python file.py` thì display() không hiện gì -> lưu file
    with open("content.png", "wb") as f:
        f.write(png)
    print("Saved content.png")