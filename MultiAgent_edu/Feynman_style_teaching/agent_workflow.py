import os
from IPython.display import Image, display


from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from function_executes import *
from data_structure import ContextStore
from route import *

from dotenv import load_dotenv
load_dotenv()
def create_graph():
    searcher = StateGraph(LearningState)
    memory = MemorySaver()
    context_store = ContextStore()

    searcher.add_node("generate_query", generate_query)
    searcher.add_node("search_web", search_web)
    searcher.add_node("chunk_context", chunk_context)
    searcher.add_node("context_validation", context_validation)
    searcher.add_node("generate_checkpoints", generate_checkpoints)
    searcher.add_node("generate_question", generate_question)
    searcher.add_node("next_checkpoint", next_checkpoint)
    searcher.add_node("user_answer", user_answer)
    searcher.add_node("verify_answer", verify_answer)
    searcher.add_node("teach_concept", teach_concept)

    searcher.add_edge(START, "generate_checkpoints")
    searcher.add_conditional_edges("generate_checkpoints", route_context, ['chunk_context', 'generate_query'])
    searcher.add_edge("generate_query", "search_web")
    searcher.add_edge("search_web", "generate_question")
    searcher.add_edge("chunk_context", "context_validation")
    searcher.add_conditional_edges("context_validation", route_search, ['search_web', 'generate_question'])

    searcher.add_edge("generate_question", "user_answer")
    searcher.add_edge("user_answer", "verify_answer" )
    searcher.add_conditional_edges("verify_answer", route_verification, 
                                   {
                                       "next_checkpoint": "next_checkpoint",
                                        "teach_concept" : "teach_concept",
                                        END: END                                    
                                    })
    searcher.add_conditional_edges("teach_concept", route_teaching,
                                   {
                                    "next_checkpoint": "next_checkpoint",
                                    END: END
                                })
    searcher.add_edge("next_checkpoint", "generate_question")
    return searcher.compile(interrupt_after = ["generate_checkpoints"], interrupt_before = ["user_answer"], checkpointer = memory)



if __name__ == "__main__":
    graph = create_graph()
    png = graph.get_graph(xray=True).draw_mermaid_png()
    with open("graph.png", "wb") as f:
        f.write(png)
    print("Saved graph.png")