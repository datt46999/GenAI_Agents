
import os
from dotenv import load_dotenv
from graph import create_graph


load_dotenv()


app = create_graph()
def run_query_user(query: str) -> dict[str, str]:
    """Process a user query through the LangGraph workflow.
    
    Args:
        query (str): The user's query
        
    Returns:
        Dict[str, str]: A dictionary containing the query's category and response
    """
    results = app.invoke({"query": query})
    return {
        "category": results["category"],
        "response": results["response"]
    }

