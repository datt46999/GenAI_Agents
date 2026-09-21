"""
Using Ai framework to builf agent capable of engaging into natural and conherent conversation.

Simple chatbots lacks the abilities to maintain context, leading to disjointed and frustuation user experiences.
-> the aim to solve that prolbem by implement the agent that can remember and refer the previous part of the convertation.


Metail detail:

1. Set up environment: setup the necessatu AI Framework
2. Create chat histories store
3. Define conversation structure:
    Create the template that include:
        + A system message the AI's role
        + The plauholder for conversation history.
        + The user input.

4. Build the conversation chain
5. Interacting with agent
"""

from dotenv import load_dotenv

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI

load_dotenv()


store = {}
def chat_history(session_id: str):
    """get id of chat """
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]



def process(user_input: str, user_id: str):
    llm = ChatOpenAI(model="gpt-4o-mini", max_tokens=1000, temperature=0)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpfull AI  ASSISTANT."),
            MessagesPlaceholder(variable_name = "history"),
            ("human", "{input}")
        ]
    )
    chain = prompt | llm
    run_chain = RunnableWithMessageHistory(
        chain,
        chat_history,
        input_messages_key = "input",
        history_messages_key = "history"
    )


    return run_chain.invoke(
        {'input': user_input},
        config={"configurable": {"session_id": user_id}}
    ).content


# if __name__ == "__main__":
#     user_input = "How are you today?"
#     session_id = "1"
#     print(process(user_input, session_id))
#     # for message in store[session_id].messages:
#     #     print(f"{message.type}: {message.content}")

    