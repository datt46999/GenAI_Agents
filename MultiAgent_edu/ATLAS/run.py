import os
import json
import asyncio
import re

from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.style import Style


from utils import NeMoLLaMa, AcademicState, OpenAILLM
from data_manager import DataManager
from multi_agents import create_agent_graph
load_dotenv()



# llm_name = os.getenv("MODEL_NAME")
# llm_key = os.getenv("MEMOTRON_3_5_LIGHTNING_30B_A3B_KEY")

openai_key = os.getenv("OPENAI_API_KEY")
llm = OpenAILLM(openai_key)
async def run_all_system(profile_json: str, calendar_json: str, task_json: str):
    """
    Run the entire academic assistance system with improve output handling.

    This is the main entry point for the ATLAS
    It handles initialization, use interaction, workflow execution and results presentation.

    Args:
        profile_json: JSON string containing student profile data
        calendar_json: JSON string containing calendar/schedule data
        task_json: JSON string containing academic tasks data

    Returns:
        Tuple[Dict, Dict]: Coordinator output and final state, or (None, None) on error

    """
    try:
        console = Console()

        console.print("\n[bold magenta]🎓 ATLAS: Academic Task Learning Agent System[/bold magenta]")
        console.print("[italic blue]Initializing academic support system...[/italic blue]\n")

        # llm = NeMoLLaMa(llm_key)
        # llm = ChatOpenAI(model= 'gpt-4o-mini', temperature = 0.5)
        dm = DataManager()
        dm.load_data(profile_json, calendar_json, task_json)

        console.print("[bold green]Please enter your academic request:[/bold green]")
        user_input = str(input())
        console.print(f"\n[dim italic]Processing request: {user_input}[/dim italic]\n")


        # Construct initial state object
        # This contains all context needed by the agents

       
        state = {
            "messages": [HumanMessage(content=user_input)],  # User request
            "profile": dm.get_student_profile("student_123"),  # Student info
            "calendar": {"events": dm.get_upcoming_events()},  # Schedule
            "tasks": {"tasks": dm.get_active_tasks()},        # Active tasks
            "results": {}                                     # Will store agent outputs
        }

        graph = create_agent_graph(llm)
        print("INIT messages:", state["messages"])
        
        coordinator_output = None  # Initial analysis
        final_state = None        # Final results

        # Process workflow with live status updates
        with console.status("[bold green]Processing...", spinner="dots") as status:
            # Stream workflow steps asynchronously
            async for step in graph.astream(state):
                # Capture coordinator analysis when available
                if "coordinator_analysis" in step.get("results", {}):
                    coordinator_output = step
                    analysis = coordinator_output["results"]["coordinator_analysis"]

                    # Display selected agents for transparency
                    console.print("\n[bold cyan]Selected Agents:[/bold cyan]")
                    for agent in analysis.get("required_agents", []):
                        console.print(f"• {agent}")

                # Capture final execution state
                if "execute" in step:
                    final_state = step


        # # Display formatted results if available
            # if final_state:
            #     display_formatted_output(final_state)
            # Replace with simpler console output:
            if final_state:
                agent_outputs = final_state.get("execute", {}).get("results", {}).get("agent_outputs", {})

                # Simple console output for each agent
                for agent, output in agent_outputs.items():
                    console.print(f"\n[bold cyan]{agent.upper()} Output:[/bold cyan]")

                    # Handle nested dictionary output
                    if isinstance(output, dict):
                        for key, value in output.items():
                            if isinstance(value, dict):
                                for subkey, subvalue in value.items():
                                    if subvalue and isinstance(subvalue, str):
                                        console.print(subvalue.strip())
                            elif value and isinstance(value, str):
                                console.print(value.strip())
                    # Handle direct string output
                    elif isinstance(output, str):
                        console.print(output.strip())

            # Indicate completion
            console.print("\n[bold green]✓[/bold green] [bold]Task completed![/bold]")
            return coordinator_output, final_state

    except Exception as e:
        # Comprehensive error handling with stack trace
        console.print(f"\n[bold red]System error:[/bold red] {str(e)}")
        console.print("[yellow]Stack trace:[/yellow]")
        import traceback
        console.print(traceback.format_exc())
        return None, None

async def load_json_and_test(path_file: str):

    """
    Run all system 
    """

    print("Academic Assistant Test Setup")
    print("-" * 50)
    print("\nPlease upload your JSON files...")

    try:


        # Define patterns for matching file types
        patterns = {
            'profile': r'^profile.*\.json$',
            'calendar': r'^calendar.*\.json$',
            'task': r'^task.*\.json$'
        }
        files = os.listdir(path_file)
        # Find matching files
        found_files = {
            file_type: next(
                (os.path.join(path_file, f) for f in files
                if re.match(pattern, f, re.IGNORECASE)),
                None
            )
            for file_type, pattern in patterns.items()
        }

        # Check if all required files are present
        missing = [k for k, v in found_files.items() if v is None]
        if missing:
            print(f"Error: Missing required files: {missing}")
       
            return

        print("\nFiles found:")
        for file_type, filename in found_files.items():
            print(f"- {file_type}: {filename}")

        # Load JSON contents
        json_contents = {}
        for file_type, filename in found_files.items():
            with open(filename, 'r', encoding='utf-8') as f:
                try:
                    json_contents[file_type] = f.read()
                except Exception as e:
                    print(f"Error reading {file_type} file: {str(e)}")
                    return

        print("\nStarting academic assistance workflow...")
        # llm = NeMoLLaMa(llm_key)
        llm = ChatOpenAI(model= 'gpt-4o-mini', temperature = 0.5)
        coordinator_output, output = await run_all_system(
            json_contents['profile'],
            json_contents['calendar'],
            json_contents['task']
        )
        return coordinator_output, output

    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nDetailed error information:")
        import traceback
        print(traceback.format_exc())
        return None, None

# Run the system


async def process():
    """Show output in markdown format"""
    file_path = 'data/'
    coordinator_output, output = await load_json_and_test(file_path)

    try:
        json_content = json.loads(output) if isinstance(output, str) else output

        plan_content = json_content.get('plan', '')

        console = Console()
        console.print(Panel(Markdown(plan_content), title="LLM Output", border_style="blue"))

    except Exception as e:
        print(f"Error formatting output: {e}")
        print("Raw output:", output)


if __name__ == "__main__":
    asyncio.run(process())