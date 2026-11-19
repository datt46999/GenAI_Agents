from langgraph.graph import StateGraph, END
from langchain_core.runnables.graph import MermaidDrawMethod

from config import *
from helper_function import *

"""
Define function to determine the next step in the process base on the current state
"""

def decide_next_path(state: GraphState)-> str:
    """
    Pick of graph path base of the state of action generation
    """

    if state['error_message'] is not None:
        return "handle_generation_error"
    elif state['current_action']>= len(state['actions']):
        return 'post_process_script'
    elif state['current_action']<len(state['actions']):
        return 'get_website_state'

def create_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("convert_user_instruction_to_actions", covert_user_instruction_to_actions)
    workflow.add_node("get_initial_action", get_initial_action)
    workflow.add_node("get_website_state", get_website_state)
    workflow.add_node("generate_code_for_action", generate_code_for_action)
    workflow.add_node("validate_generated_action", validate_generated_action)
    workflow.add_node("handle_generation_error", handle_generation_error)
    workflow.add_node("post_process_script", post_process_script)
    workflow.add_node("execute_test_case", execute_test_case)
    workflow.add_node("generate_test_report", generate_test_report)

    workflow.set_entry_point("convert_user_instruction_to_actions")

    workflow.add_edge("convert_user_instruction_to_actions", "get_initial_action")
    workflow.add_edge("get_initial_action", "get_website_state")
    workflow.add_edge("get_website_state", "generate_code_for_action")
    workflow.add_edge("generate_code_for_action", "validate_generated_action")

    workflow.add_conditional_edges("validate_generated_action", decide_next_path, ['get_website_state', 'handle_generation_error', "post_process_script"])

    workflow.add_edge('handle_generation_error', END)
    workflow.add_edge("post_process_script", "execute_test_case")

    workflow.add_edge("execute_test_case", "generate_test_report")
    workflow.add_edge("generate_test_report", END)

    return workflow.compile()


if __name__ =="__main__":
    app = create_graph()
    
    
    png = app.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.API)

    # Chạy bằng `python file.py` thì display() không hiện gì -> lưu file
    with open("E2E.png", "wb") as f:
        f.write(png)
    print("Saved graph.png")