import os

from config import MODEL_NAME, State
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI



def categorize(state: State) -> State:
    """
    Categorize user query into Tecnical, billing, general
    """

    prompt =ChatPromptTemplate.from_template("""
        Categorize the following customer query into one of these categories: 
        Technical, Billing, General.
        Query: {query}
        """)

    chain = prompt | ChatOpenAI(model = MODEL_NAME, temperature = 0)
    category = chain.invoke({"query": state['query']}).content

    return {"category": category}


def sentiment_analysis(state: State)-> State:
    """
    Analysis the sentiment of cutomer query as Positive, Neutual ot Negative
    """

    prompt = ChatPromptTemplate.from_template("""
        Analyze sentiment of the following customer query.
        Response with either 'Positive', 'Neutral' or 'Negative'. Query: {query}
    """)

    chain = prompt | ChatOpenAI(model = MODEL_NAME, temperature = 0)
    sentiment = chain.invoke({'query': state["query"]}).content

    return {"sentiment": sentiment}


def handle_technical(state: State) -> State:
    """
    Provide technical support response to user query
    """
    prompt = ChatPromptTemplate.from_template("""
        Provide technical build supprot response to the following query: {query}
    """)
    chain = prompt | ChatOpenAI(model = MODEL_NAME, temperature = 0)
    response = chain.invoke({"query": state["query"]}).content
    return {"response": response}


def handle_billing(state: State)->State:
    """
    Provide billing support provide to the query
    """
    prompt = ChatPromptTemplate.from_template("""
        Provide billing support response to the following query: {query}
    """)
    chain = prompt | ChatOpenAI(model = MODEL_NAME, temperature = 0)
    response = chain.invoke({"query": state["query"]}).content
    return {"response": response}


def handle_general(state: State) -> State:
    """Provide a general support response to the query."""
    prompt = ChatPromptTemplate.from_template(
        "Provide a general support response to the following query: {query}"
    )
    chain = prompt | ChatOpenAI(model=MODEL_NAME, temperature=0)
    response = chain.invoke({"query": state["query"]}).content
    return {"response": response}

def escalate(state: State) -> State:
    """Escalate the query to a human agent due to negative sentiment."""
    return {"response": "This query has been escalated to a human agent due to its negative sentiment."}



def route_query(state: State) -> State:
    """Router query based on uts sentiment and category"""
    if state["sentiment"] == "Negative":
        return "escalate"
    elif state["category"] == "Technical":
        return "handle_technical"
    elif state["category"] == "Billing":
        return "handle_billing"
    else:
        return "handle_general"