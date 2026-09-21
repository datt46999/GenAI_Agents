"""
Basic QA agent using langchain with OpenAI LM. 

The aims:
+ Demonstrate the basics of AI-driven QA
+ Inroduce key concept in building AI agent
+ Provide foundation for more advanced agent architechtures

Methob detail:
1. Setup and initialization
2. Define the prompt template
3. Create LLM chain
4. Implement QA
5. User interaction
"""

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.prompts import ChatPromptTemplate, PromptTemplate

load_dotenv()
# prompt = ChatPromptTemplate.from_messages([

# ])

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", max_tokens=1000, temperature=0)
template = """
You are a helpful AI assistant. Your task is to answer the user's question to the best of your ability.

User's question: {question}

Please provide a clear and concise answer:
"""
prompt = PromptTemplate(template=template, input_variables=["question"])

qa_chain = prompt | llm

def get_answer(question):
    """
    Get an answer to the given question using the QA chain.
    """
    input_variables = {"question": question}
    response = qa_chain.invoke(input_variables).content
    return response

user_question = input("Enter your question: ")
user_answer = get_answer(user_question)
print(f"Answer: {user_answer}")