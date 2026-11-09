
import os

from langgraph.graph import StateGraph, START, END
from langchain_core.runnables.graph import MermaidDrawMethod

from config import State
from utils import * 



def route_query(state: State):
    """
    Router the query based on its category to the appropriate handle
    """
    if '1' in state['category']:
        print("Category: handle_learning_response")
        return "handle_learning_response"
    elif '2' in state['category']:
        print("Category: handle_resume_making")
        return "handle_resume_making"
    elif '3' in state['category']:
        print("Category: handle_interview_preparation")
        return "handle_interview_preparation"
    elif '4' in state['category']:
        print("Category: Job_search")
        return "job_search"
    else:
        print("Please ask your question based on my description")
        return False

def route_interview(state: State) ->str:
    """
    Router the query to the appropriate interview-relative handler
    """
    if "Question".lower() in state['category'].lower():
        print("Category: interview_topics_question")
        return "interview_topics_question"
    else:
        print("Category: Mock_interview")
        return 'mock_interview'


def route_learning(state: State):
    """
    router learning query based on learning path categories
    """

    if "Question".lower() in state['category'].lower():
        print("Category: ask_query_bot")
        return "ask_query_bot"

    elif 'Tutorial'.lower() in state["category"].lower():
        print('Category: tutorial_agent')
        return "tutorial_agent"
    else:
        print("Please ask your question based on the interview description")
        return False        


def create_graph():
    workflow = StateGraph(State)


    
    workflow.add_node("categorize", categorize)  # Initial categorization node
    workflow.add_node("handle_learning_resource", handle_learning_resource)  # Handles learning-related queries
    workflow.add_node("handle_resume_making", handle_resume_making)  # Handles resume-making queries
    workflow.add_node("handle_interview_preparation", handle_interview_preparation)  # Handles interview prep queries
    workflow.add_node("job_search", job_search)  # Handles job search queries
    workflow.add_node("mock_interview", mock_interview)  # Handles mock interview sessions
    workflow.add_node("interview_topics_questions", interview_topics_question)  # Handles interview topic questions
    workflow.add_node("tutorial_agent", tutorial_agent)  # Tutorial agent for generative AI learning resources
    workflow.add_node("ask_query_bot", ask_query_bot)  # General query bot for learning resources


    workflow.add_edge(START, "categorize")
    workflow.add_conditional_edges(
        "categorize",
        route_query,
        {
            "handle_learning_resource":"handle_learning_resource",
            "handle_resume_making": "handle_resume_making",
            "handle_interview_preparation": 'handle_interview_preparation',
            "job_search":"job_search"
        }
    )
    workflow.add_conditional_edges(
        "handle_learning_resource",
        route_learning,
        {
            "ask_query_bot":"ask_query_bot",
            "tutorial_agent":"tutorial_agent"
        }
    )
    workflow.add_conditional_edges(
        "handle_interview_preparation",
        route_interview,
        {
            "mock_interview": "mock_interview",
            "interview_topics_questions": "interview_topics_questions",
        }
    )

    workflow.add_edge("handle_resume_making", END)
    workflow.add_edge("job_search", END)
    workflow.add_edge("interview_topics_questions", END)
    workflow.add_edge("mock_interview", END)
    workflow.add_edge("ask_query_bot", END)
    workflow.add_edge("tutorial_agent", END)

    # Set the initial entry point to start the workflow at the categorize node
    workflow.set_entry_point("categorize")

    return workflow.compile()


if __name__ == "__main__":
    app = create_graph()


    png = app.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.API)

    # Chạy bằng `python file.py` thì display() không hiện gì -> lưu file
    with open("graph.png", "wb") as f:
        f.write(png)
    print("Saved graph.png")
