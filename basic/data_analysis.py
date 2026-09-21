"""
Creating AI-power data analysis agent that can interpret and answer question about dataset by using LM.
"""

import os
import numpy as np
import pandas as pd


from dotenv import load_dotenv
from datetime import datetime, timedelta


from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_classic.agents import AgentType
from langchain_openai import ChatOpenAI




load_dotenv()
df_path="data/simple_data.csv"


def create_df(output_path =df_path):
    if not os.path.exists(output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # Generate sample data
    n_rows = 1000

    # Generate dates
    start_date = datetime(2022, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(n_rows)]

    # Define data categories
    makes = ['Toyota', 'Honda', 'Ford', 'Chevrolet', 'Nissan', 'BMW', 'Mercedes', 'Audi', 'Hyundai', 'Kia']
    models = ['Sedan', 'SUV', 'Truck', 'Hatchback', 'Coupe', 'Van']
    colors = ['Red', 'Blue', 'Black', 'White', 'Silver', 'Gray', 'Green']

    # Create the dataset
    data = {
        'Date': dates,
        'Make': np.random.choice(makes, n_rows),
        'Model': np.random.choice(models, n_rows),
        'Color': np.random.choice(colors, n_rows),
        'Year': np.random.randint(2015, 2023, n_rows),
        'Price': np.random.uniform(20000, 80000, n_rows).round(2),
        'Mileage': np.random.uniform(0, 100000, n_rows).round(0),
        'EngineSize': np.random.choice([1.6, 2.0, 2.5, 3.0, 3.5, 4.0], n_rows),
        'FuelEfficiency': np.random.uniform(20, 40, n_rows).round(1),
        'SalesPerson': np.random.choice(['Alice', 'Bob', 'Charlie', 'David', 'Eva'], n_rows)
    }

    # Create DataFrame and sort by date
    df = pd.DataFrame(data).sort_values('Date')

    # Display sample data and statistics
    print("\nFirst few rows of the generated data:")
    print(df.head())

    print("\nDataFrame info:")
    print(df.info())

    print("\nSummary statistics:")
    print(df.describe())
    df.to_csv(output_path, index = False)



def ask_agent(question):
    """Function to ask questions to the agent and display the response"""
    response = agent.invoke({
        "input": question,
        "agent_scratchpad": f"Human: {question}\nAI: To answer this question, I need to use Python to analyze the dataframe. I'll use the python_repl_ast tool.\n\nAction: python_repl_ast\nAction Input: ",
    })
    print(f"Question: {question}")
    print(f"Answer: {response}")
    print("---")

if __name__ == "__main__":
    # create_df(df_path)
    df = "data/simple_data.csv"
    df = pd.read_csv(df)
    agent = create_pandas_dataframe_agent(
        ChatOpenAI(model="gpt-4o", temperature=0),
        df,
        verbose=True,
        allow_dangerous_code=True,
        agent_type=AgentType.OPENAI_FUNCTIONS,
    )   
    print("Data Analysis Agent is ready. You can now ask questions about the data.")


    ask_agent("What are the column names in this dataset?")
    ask_agent("How many rows are in this dataset?")
    ask_agent("What is the average price of cars sold?")