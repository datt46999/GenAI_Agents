from langchain_core.runnables.graph import MermaidDrawMethod
from langgraph.graph import StateGraph, START, END

from typing import Dict
from IPython.display import display, Image
from dotenv import load_dotenv

from config import MODEL_NAME, State
from node_function import *
load_dotenv()


def create_graph( State):
    """
    Define graph by langgraph
    """
    workflow = StateGraph(State)

    workflow.add_node("categorize", categorize)
    workflow.add_node("analyze_sentiment", sentiment_analysis)
    workflow.add_node("handle_technical", handle_technical)
    workflow.add_node("handle_billing", handle_billing)
    workflow.add_node("handle_general", handle_general)
    workflow.add_node("escalate", escalate)

    workflow.add_edge("categorize", "analyze_sentiment")
    workflow.add_conditional_edges(
        "analyze_sentiment",
        route_query,
        {
            "handle_technical": "handle_technical",
            "handle_billing": "handle_billing",
            "handle_general": "handle_general",
            "escalate": "escalate"
        }
    )
    workflow.add_edge("handle_technical", END)
    workflow.add_edge("handle_billing", END)
    workflow.add_edge("handle_general", END)
    workflow.add_edge("escalate", END)

    workflow.set_entry_point("categorize")

    return workflow.compile()



def run_customer_support(query: str, app) -> Dict[str, str]:
    """Process a customer query through the LangGraph workflow.
    
    Args:
        query (str): The customer's query
        
    Returns:
        Dict[str, str]: A dictionary containing the query's category, sentiment, and response
    """
    results = app.invoke({"query": query})
    return {
        "category": results["category"],
        "sentiment": results["sentiment"],
        "response": results["response"]
    }
if __name__ =="__main__":
    app = create_graph(State)
    png = app.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.API)

    # Chạy bằng `python file.py` thì display() không hiện gì -> lưu file
    with open("graph.png", "wb") as f:
        f.write(png)
    print("Saved graph.png")



    query = "My internet connection keeps dropping. Can you help?"
    result = run_customer_support(query, app)
    print(f"Query: {query}")
    print(f"Category: {result['category']}")
    print(f"Sentiment: {result['sentiment']}")
    print(f"Response: {result['response']}")
    print("\n")

    # handle_technical

    # query = "I need help talking to chatGPT"
    # result = run_customer_support(query, app)
    # print(f"Query: {query}")
    # print(f"Category: {result['category']}")
    # print(f"Sentiment: {result['sentiment']}")
    # print(f"Response: {result['response']}")
    # print("\n")

    # # handle_billing

    # query = "where can i find my receipt?"
    # result = run_customer_support(query, app)
    # print(f"Query: {query}")
    # print(f"Category: {result['category']}")
    # print(f"Sentiment: {result['sentiment']}")
    # print(f"Response: {result['response']}")
    # print("\n")

    # # handle_general

    # query = "What are your business hours?"
    # result = run_customer_support(query, app)
    # print(f"Query: {query}")
    # print(f"Category: {result['category']}")
    # print(f"Sentiment: {result['sentiment']}")
    print(f"Response: {result['response']}")