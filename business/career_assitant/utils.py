import os
from datetime import datetime


from langchain_core.messages import  SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

from config import *



    # Render the content in Markdown format within the notebook
    # display(Markdown(content))

"""
using 👉 Few Shot prompting: to make our LLM understand  the categiries
"""

def categorize(state: State)->State:

    """
    Categorize the user query into one of four main categorize:
    Learn  generative AI technology, Resume Making, Interview Preparation, job search
    """

    prompt =ChatPromptTemplate.from_template(
        "Categorize the following customer query into one of these categories:\n"
        "1: Learn Generative AI Technology\n"
        "2: Resume Making\n"
        "3: Interview Preparation\n"
        "4: Job Search\n"
        "Give the number only as an output.\n\n"
        "Examples:\n"
        "1. Query: 'What are the basics of generative AI, and how can I start learning it?' -> 1\n"
        "2. Query: 'Can you help me improve my resume for a tech position?' -> 2\n"
        "3. Query: 'What are some common questions asked in AI interviews?' -> 3\n"
        "4. Query: 'Are there any job openings for AI engineers?' -> 4\n\n"
        "Now, categorize the following customer query:\n"
        "Query: {query}"
    )

    # Creates a categorization chain and invokes it with the user's query to get the category
    chain = prompt | llm 
    print('Categorizing the customer query...')
    category = chain.invoke({"query": state["query"]}).content
    return {"category": category}


def handle_learning_resource(state: State)-> State:
    """
    Detemine if the query is related to Tutorial creation or geneation Question on generate AI Topics
    """
    prompt = ChatGoogleGenerativeAI.from_template(
        "Categorize the following user query into one of these categories:\n\n"
        "Categories:\n"
        "- Tutorial: For queries related to creating tutorials, blogs, or documentation on generative AI.\n"
        "- Question: For general queries asking about generative AI topics.\n"
        "- Default to Question if the query doesn't fit either of these categories.\n\n"
        "Examples:\n"
        "1. User query: 'How to create a blog on prompt engineering for generative AI?' -> Category: Tutorial\n"
        "2. User query: 'Can you provide a step-by-step guide on fine-tuning a generative model?' -> Category: Tutorial\n"
        "3. User query: 'Provide me the documentation for Langchain?' -> Category: Tutorial\n"
        "4. User query: 'What are the main applications of generative AI?' -> Category: Question\n"
        "5. User query: 'Is there any generative AI course available?' -> Category: Question\n\n"
        "Now, categorize the following user query:\n"
        "The user query is: {query}\n"
    )
    chain = prompt | llm 
    print('Categorizing the customer query further...')
    response = chain.invoke({"query": state["query"]}).content
    return {"category": response}

def handle_interview_preparation(state: State) -> State:
    """
    Detemine if the query is related to Mock interviews or General Interview Question
    """
    prompt = ChatPromptTemplate.from_template(
        """
        Categorize the following user query into one of their categories:\n
        Categorize:
        - Mock: For requests related to mock interview
        - Question: For general queries asking about interview topics or preparation
        - Default to Question if the query doesn't fit eather of these categories

        Examples:\n
        1. User query: 'Can you conduct a mock interview with me for a Gen AI role?' -> Category: Mock\n
        2. User query: 'What topics should I prepare for an AI Engineer interview?' -> Category: Question\n
        3. User query: 'I need to practice interview focused on Gen AI.' -> Category: Mock\n"
        4. User query: 'Can you list important coding topics for AI tech interviews?' -> Category: Question\n\n
        Now, categorize the following user query:\n
        The user query is: {query}\n
        """
    )
    chain = prompt | llm 
    print('Categorizing the customer query further...')
    response = chain.invoke({"query": state["query"]}).content
    return {"category": response}

def job_search(state: State) -> State:
    """
    Provide a job search response based on user query requirements
    """
    prompt = ChatPromptTemplate.from_template(
        """
        Your task is to refactor and make .md file for the this content which include the jobs available in the market.
        Refactor such that user can refer easily. Content: {result}
        """
    )

    jobSearch = JobSearch(prompt)
    state['query'] = input("Please make sure to mention Job location you want, Job roles\n ")
    path = jobSearch.find_jobs(state['query'])
    show_md_file(path)
    return {'response': path}

def handle_resume_making(state: State)-> State:
    """
    Generate a customize resume based on user details for a tech role in AI and generative AI
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", '''You are a skilled resume expert with extensive experience in crafting resumes tailored for tech roles, especially in AI and Generative AI. 
        Your task is to create a resume template for an AI Engineer specializing in Generative AI, incorporating trending keywords and technologies in the current job market. 
        Feel free to ask users for any necessary details such as skills, experience, or projects to complete the resume. 
        Try to ask details step by step and try to ask all details within 4 to 5 steps.
        Ensure the final resume is in .md format.'''),
       MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    resumeMaker = ResumeMaker(prompt)
    path = resumeMaker.Create_Resume(state["query"])
    show_md_file(path)
    return {"response": path}


def ask_query_bot(state: State)-> State:
    """
    Provide detailed answers to user queries to generation AI
    """
    system_message = """
        You are an expert Generative AI Engineer with extensive experience in training and guiding others in AI engineering. 
        You have a strong track record of solving complex problems and addressing various challenges in AI. 
        Your role is to assist users by providing insightful solutions and expert advice on their queries.
        Engage in a back-and-forth chat session to address user queries.
    """
    prompt = [SystemMessage(content = system_message)]
    learning_agent = LearningResourceAgent(prompt)

    path = learning_agent.QueryBot(state["query"])
    show_md_file(path)
    return {"response": path}


def tutorial_agent(state: State)-> State:
    """
    Generate a tutorial blog for Generative AI based on user requirements.
    """

    system_message = """You are a knowledgeable assistant specializing as a Senior Generative AI Developer with extensive experience in both development and tutoring. 
         Additionally, you are an experienced blogger who creates tutorials focused on Generative AI.
         Your task is to develop high-quality tutorials blogs in .md file with Coding example based on the user's requirements. 
         Ensure tutorial includes clear explanations, well-structured python code, comments, and fully functional code examples.
         Provide resource reference links at the end of each tutorial for further learning.
    """
    prompt = ChatPromptTemplate.from_messages([("system", system_message),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),])
    #agent_scratchpad is a function that formats the intermediate steps of the agent's actions and observations into a string. 
    #This function is used to keep track of the agent's thoughts or actions during the execution of the program. But its not necessary, we can do without this so we will not include it only define it.
    learning_agent = LearningResourceAgent(prompt)
    path = learning_agent.TutorialAgent(state["query"])
    show_md_file(path)
    return {"response": path}  


def interview_topics_question(state: State)-> State:
    """
    Create a curated list of interview question related in Generative AI based on user input
    """
    system_message = """
        You are a good researcher in finding interview questions for Generation AI topics and jobs.
        Your task is to provide a list of interview questions for Generation AI topics and jobs based on user requirements.
        Provide top questions  with references and links if possible. You may ask for clarification if needed.
        Generate a .md document containing  the questions.
    """
    prompt = ChatPromptTemplate.from_message([
        ('system', system_message),
        MessagesPlaceholder('chat_history'),
        ('human', '{input}'),
        ('placeholder', "{agent_scratchpad}")
    ])

    interview_agent = InterviewAgent(prompt)
    path = interview_agent.interview_question(state['query'])
    show_md_file(path)
    return {'response': path}


def mock_interview(state: State)->State:
    """
    Conduct mock interview for a Generative AI possible, including evaluation at the end
    """

    system_message ="""
        You are Generative AI interviewer. You have conducted numerous interviews for Generative AI roles.
        Your task is to conduct a mock interview for Generative AI Position, engaging in back-and-forth interview session.
        The conversation should not exceed more than 15 to 20 minutes.
        At the end of the interview, provide an evaluation for candidate.
    """
    prompt = [SystemMessage(content = system_message)]
    interview_agent = InterviewAgent(prompt)
    path = interview_agent.Mock_interview()
    show_md_file(path)
    return {'response': path}