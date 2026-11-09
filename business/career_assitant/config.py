import os
from datetime import datetime
from typing import TypedDict
from dotenv import load_dotenv




from langchain_core.messages import  AIMessage, HumanMessage, trim_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor


load_dotenv()


MODEL_NAME = "gemini-3.5-flash"
llm= ChatGoogleGenerativeAI(model=MODEL_NAME,
                             verbose=True,
                             temperature=0.5)




def trim_conversation(prompt):
    """
    Trims conversation history to retain only the latest messages within the limit
    """
    max_messages = 10
    return trim_messages(
        prompt,
        max_tokens = max_messages,
        strategy = "last",
        token_counter = len,
        start_on = "human",
        include_system = True,
        allow_partial = False
    )




def save_file(data, filename):
    """Saves data to a markdown file with a timestamped filename."""
    folder_name = "Agent_output"  # Folder to store output files
    os.makedirs(folder_name, exist_ok=True)  # Creates the folder if it doesn't exist
    
    # Generate a timestamped filename for uniqueness
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # Format: YYYYMMDDHHMMSS
    filename = f"{filename}_{timestamp}.md"
    
    # Define the full file path
    file_path = os.path.join(folder_name, filename)
    
    # Save the data to the file in the specified path
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(data)
        print(f"File '{file_path}' created successfully.")
    
    # Return the full path of the saved file
    return file_path

def show_md_file(file_path):
    """Displays the content of a markdown file as Markdown in the notebook."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    
class State(TypedDict):
    query: str
    category: str
    response: str




"""
---------------------------------------------------
Reponsible and learning(Tutorial and Q&A sessions)

create_tool_calling_agent-> AgentExecutor-> DuckDuckGoSearchResults
---------------------------------------------------
"""

class LearningResourceAgent:
    def __init__(self, prompt):
        """
        Initialize chat model, prompt template and tools search        
        """
        self.model = ChatGoogleGenerativeAI(model="gemini-flash-latest")
        self.prompt = prompt
        self.tools = [DuckDuckGoSearchResults()]

    def tutorial_agent(self, user_input):
        """
        set up agent to access and execute  a tutorial-style response
        """
        agent = create_tool_calling_agent(self.model, self.tools, self.prompt )
        agent_execute = AgentExecutor(agent = agent, tools = self.tools, verbose = True)
        response = agent_execute.invoke({"input": user_input})

        path = save_file(str(response.get('output')).replace("```markdown", "").strip(), 'Tutorial')
        print(f"Tutorial saved to {path}")
        return path

    def query_bot(self):
        """
        Initialize a Q&A loop for continious interaction with the user
        """
        print("\nStarting the mock interview. Type 'exit' to end the session.")

        initial_message = "I'm ready for the interview. \n"
        interview_record = []
        interview_record.append("Candidate: %s \n" % initial_message)

        interview_record.append(HumanMessage(content = initial_message))

        while True:
            self.prompt = trim_conversation(self.prompt)

            response = self.model.invoke(self.prompt)
            self.prompt.append(AIMessage(content = response.content))

            print("\nInterviewer: ", response.content)
            interview_record.append("\nInterviewer: %s \n" % response.content )

            user_input = input("\nCandidate: ")
            interview_record.append('\nCandidate: %s \n' % user_input)
            
            # Add user input to the conversation history
            self.prompt.append(HumanMessage(content=user_input))
            
            # End the interview if the user types "exit"
            if user_input.lower() == "exit":
                print("Ending the interview session.")
                path = save_file(''.join(interview_record),'Mock_Interview')
                print(f"Mock Interview saved to {path}")
                return path



"""
-----------------------------------------------------
Interview handling (Interview question prep and MockInterview)
+ interview question
    Runs a loop for handling  interview question  from the user, generating response using the agent executor
    Response a store in question_bank for leter reference. The conversation will end when user types 'exit' and chat histories is saces as  a Markdown file
+ Mock interview
    Similate mock interview by initiating a conversation loop. Response from the model are displayed as 'Interviewer' messages, and user input as 'Candidate' message.
    The conversation is trimmed as it grows  to maintain prompt size. The interview session end when user types 'exit', returning a record  of the entire interview

-----------------------------------------------------
"""

class InterviewAgent:
    def __init__(self, prompt):
        """
        Inititalize interview agent with chat mode, prompt template, tools for user in the agent
        """
        self.model = ChatGoogleGenerativeAI(model = MODEL_NAME)
        self.prompt = prompt
        self.tools = [DuckDuckGoSearchResults()]
    def interview_question(self, user_input):
        """
        Hold the conversation histoty and cumulative question and answer
        """
        print("Starting with interview question preparation. Type 'exit' to end the session.")
        chat_history = []
        questions_bank =''

        self.agent = create_tool_calling_agent(self.model, self.prompt, self.tools)
        self.agent_executor = AgentExecutor(agent = self.agent, tools = self.tools, verbose= True, handle_parsing_error = True) 
        
        
        while True:
            
            if user_input == "exit":
                print("End of the conversation.")
                break

            response = self.agent_executor.invoke({'input': user_input, 'chat_history' : chat_history })
            questions_bank += str(response.get('output')).replace("```markdown", "").strip() + "\n"

            # update history with user input and Ai response
            chat_history.extend([HumanMessage(content= user_input), response['output']])
            if len(chat_history)>10:
                chat_history = chat_history[-10:]

            user_input = input("You: ")

        # Save the entire question-response history to a markdown file and display it
        path = save_file(questions_bank, 'Interview_questions')
        print(f"Interviews question saved to {path}")
        return path


    def Mock_interview(self):
        """
        Similate mock interview question by intititing conversation loop
        The conversation is trimmed as it grows to maintain prompt size.
        """
        initial_message = "I'm ready for the interview.\n"
        interview_record = []
        interview_record.append('Candidate: %s \n' % initial_message)
        self.prompt.append(HumanMessage(content=initial_message))


        while True:
            self.prompt = trim_conversation(self.prompt)

            response = self.model.invoke(self.prompt)

            self.prompt.append(AIMessage(content = response.content))
            interview_record.append("\nInterview: %s\n" % response.content)

            user_input = input("Candidate: ")
            interview_record.append("\nCandidate: %s\n" % user_input)

            self.prompt.append(HumanMessage(content=user_input))
            
            # End the interview if the user types "exit"
            if user_input.lower() == "exit":
                print("Ending the interview session.")
                path = save_file(''.join(interview_record),'Mock_Interview')
                print(f"Mock Interview saved to {path}")
                return path






        
"""
-----------------------------------------------------
Handle create resume by chating with user

ResumeMaker
Create_resume
-----------------------------------------------------
"""
class ResumeMaker: 
    def __init__(self, prompt):
        """Initialize the chat model, prompt template and search tool    for resyme creation"""

        self.model = llm
        self.prompt = prompt
        self.tools = [DuckDuckGoSearchResults]

        # create an agent execute with witl tools access, enabling verbose and error handling
        self.agent = create_tool_calling_agent(self.model, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True, handle_parsing_errors=True)
    def create_resume(self, user_input):
        """
        Engaged in the conversation loop to garther user input  and generate resume content based on  response from agent

        """

        chat_history = []
        while True:
            # print("\nStarting the Resume create session. Type 'exit' to end the session.\n")
            if user_input.lower() == "exit":
                print("Ending the conversation. Goodbye!")
                break
            response = self.agent_executor.invoke({"input": user_input, "chat_history": chat_history})
            chat_history.extend([HumanMessage(content=user_input), response["output"]])
            
            # Limit the chat history to the last 10 messages
            if len(chat_history) > 10:
                chat_history = chat_history[-10:]
            
            # Prompt for the next user input to continue the resume creation conversation
            user_input = input("You: ")
        
        # Save the final output as a markdown file and return the file path
        path = save_file(str(response.get('output')).replace("```markdown", "").strip(), 'Resume')
        print(f"Resume saved to {path}")
        return path




"""
Job search
Conduct conversation loop assist user with jobs search queries, using the agent response based on user input

"""

class JobSearch:
    """
    Conduct conversation loop assist user with jobs search queries, using the agent response based on user input
    """

    def __init__(self, prompt):
        """Initialize with chat model, prompt template and search tools"""
        self.model = llm
        self.prompt = prompt
        self.tools = DuckDuckGoSearchResults()

    def find_jobs(self, user_input):
        results = self.tools.invoke(user_input)
        chain = self.prompt | self.model  
        jobs = chain.invoke({"result": results}).content
        
        path = save_file(str(jobs).replace("```markdown", "").strip(), 'Job_search')
        print(f"Jobs saved to {path}")
        return path


