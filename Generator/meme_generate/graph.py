import os
from dotenv import load_dotenv


from langgraph.graph import StateGraph, START, END
from langchain_core.runnables.graph import MermaidDrawMethod

load_dotenv()

from config import *
from helper_fuction import *

def create_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("get_website_content", get_website_content)
    workflow.add_node("analyze_company", analyze_company_insights)
    workflow.add_node("generate_concepts", generate_meme_concepts)
    workflow.add_node("select_templates", select_meme_templates)
    workflow.add_node("generate_text", generate_text_elements)
    workflow.add_node("create_url", create_meme_url)


    workflow.add_edge("get_website_content", "analyze_company")
    workflow.add_edge("analyze_company", "generate_concepts")
    workflow.add_edge("generate_concepts", "select_templates")
    workflow.add_edge("select_templates", "generate_text")
    workflow.add_edge("generate_text", "create_url")
    workflow.add_edge("create_url", END)

    # Set entry point
    workflow.set_entry_point("get_website_content")

    return workflow.compile()

if __name__ == "__main__":

    app = create_graph()
        
        
    png = app.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.API)

    # Chạy bằng `python file.py` thì display() không hiện gì -> lưu file
    with open("meme_gen.png", "wb") as f:
        f.write(png)
    print("Saved meme_gen.png")