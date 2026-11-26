import os
from dotenv import load_dotenv
load_dotenv()

from config import *
from helper_functions import *
from display_function import *

from langgraph.graph import StateGraph, START, END
from langchain_core.runnables.graph import MermaidDrawMethod


def sub_conversation():
    conversation_builder = StateGraph(ConversationState)
    conversation_builder.add_node("character_introduction", character_introduction)
    conversation_builder.add_node("ask_question", ask_question)
    conversation_builder.add_node("answer_question", answer_question)

    conversation_builder.add_edge(START, "character_introduction")
    conversation_builder.add_edge("character_introduction", "ask_question")
    conversation_builder.add_conditional_edges(
        "ask_question", where_to_go,
        {"continue": "answer_question", "end": END},
    )
    conversation_builder.add_edge("answer_question", "ask_question")
    return conversation_builder.compile()


# Build at module level so it also works when this file is imported
conversation_graph = sub_conversation()


def conversation(state: GenerateGameState):
    selected_character_id = state["selected_character_id"]
    if selected_character_id is None:
        return {}  # a node must return a dict, not END
    character = state["characters"][selected_character_id]
    inputs = {"character": character, "story_details": state["story_details"]}
    response = conversation_graph.invoke(inputs, {"recursion_limit": 50})
    return {"messages": response["messages"]}


def create_graph(conversation_node=conversation):
    builder = StateGraph(GenerateGameState)

    builder.add_node("create_characters", create_characters)
    builder.add_node("create_story", create_story)
    builder.add_node("narrartor", narrartor)
    builder.add_node("sherlock", sherlock)
    builder.add_node("guesser", guesser)
    builder.add_node("conversation", conversation_node)   # function OR compiled subgraph

    builder.add_edge(START, "create_characters")
    builder.add_edge("create_characters", "create_story")
    builder.add_edge("create_story", "narrartor")
    builder.add_edge("narrartor", "sherlock")
    builder.add_conditional_edges(
        "sherlock",
        lambda s: "next_talk" if s.get("selected_character_id") is not None else "end_talks",
        {"next_talk": "conversation", "end_talks": "guesser"},
    )
    builder.add_edge("conversation", "sherlock")
    builder.add_conditional_edges(
        "guesser", lambda s: s.get("result"),
        {"sherlock": "sherlock", "end": END},
    )
    return builder.compile()


if __name__ == "__main__":
    app = create_graph()                     # real app, used to run the game

    # Visualization only: put the compiled subgraph in as the node so xray can expand it
    viz_app = create_graph(conversation_node=conversation_graph)
    png = viz_app.get_graph(xray=True).draw_mermaid_png(draw_method=MermaidDrawMethod.API)

    with open("Munder_mystery_game.png", "wb") as f:
        f.write(png)
    print("Saved Munder_mystery_game.png")