
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from config import *
from system_prompt import *
from display_function import *

def character_introduction(state: ConversationState):
    """
    Path of the Conversation Sub-graph

    Generate and display a charactor introduction to Sherlock Holmoes in the murder nystery game.

    Args:
        state (ConversationState): The LangGraph State object containing:
            - messages: List of previous conversation messages. Used to store conversation history
            - character: Character object with persona and character details
            - story_details: Object containing crime details including:
                - victim_name, time_of_death, location_found
                - murder_weapon, cause_of_death
                - crime_scene_details, initial_clues

    Returns:
        dict: Adds the introduction messages to the conversation history
            - messages: Introduction messages to be added

    Notes: 
        The function use an LLM to generate approriate character dialogue while ensuring
        the character doesn't reveal their role  or incriminate themselves
    """

    character  = state["character"]
    story = state["story_details"]
    

    system_message = CHARACTER_INSTRUCTIONS.format(
        subject_persona=character.persona,
        victim=story.victim_name,
        time=story.time_of_death,
        location=story.location_found,
    )


    narration = llm.invoke([
        SystemMessage(content=system_message),
        HumanMessage(content="Introduce yourself to Sherlock Holmes")
    ])

    return {'messages':[narration]}

def get_generation(state: ConversationState):
    """
    Path of the Conversation Sug-graph.

    Generates an investigative question from Sherlock Holmes to ask a character.

    Args:
        state (ConversationState): The LangGraph State object containing:
            - messages: List of previous conversation messages. Used to store conversation history
            - character: Character object with persona and character details specific to the character being interviewed
            - story_details: Object containing crime details including:
                - victim_name, time_of_death, location_found
                - murder_weapon, cause_of_death
                - crime_scene_details, initial_clues

    Returns:
        str: Generated question content from Sherlock AI assistance.

    Note:
        The question is generated considering:
        - The crime scene details and initial clues
        - Previous conversation history with the character
        - Sherlock Holmes' characteristic investigative style
    """
    messages = state["messages"]
    character = state["character"]
    story = state["story_details"]

    system_message = SHERLOCK_ASK_PROMPT.format(
        character_name=character.name,
        victim_name=story.victim_name,
        time_of_death=story.time_of_death,
        location_found=story.location_found,
        murder_weapon=story.murder_weapon,
        cause_of_death=story.cause_of_death,
        crime_scene_details=story.crime_scene_details,
        initial_clues=story.initial_clues,
        conversation_history="\n".join([f"{msg.type}: {msg.content}" for msg in messages])
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                  "system",
                  system_message,
            ),
            MessagesPlaceholder(variable_name="messages"),
          ]
      )

    chain = prompt | llm
    question = chain.invoke(messages)

    return question.content


def ask_question(state: ConversationState):
    """
    Part of the Conversation Sub-Graph.

    Handles the question-asking process, allowing either AI-generated Sherlock questions
    or direct player input.

    Args:
        state (ConversationState): The LangGraph State object containing:
            - messages: List of previous conversation messages. Used to store conversation history
            - character: Character object with persona and character details
            - story_details: Object containing crime details including:
                - victim_name, time_of_death, location_found
                - murder_weapon, cause_of_death
                - crime_scene_details, initial_clues

    Returns:
        dict: Adds question asked to the conversation history
            - messages : Question to be added

    Note:
        - Provides option to use AI-generated "SherlockAI" questions
        - Handles input validation and error cases
        - Allows for conversation termination
    """
    character = state['character']
    # Get user input
    while True:
      try:
        use_ai_sherlock = get_player_yesno_answer("Do you want SherlockAI to ask a question?")
        if use_ai_sherlock.lower()[0] == 'y':
          question = get_question(state)
        else:
          question = get_player_input(character.name)
        return {"messages": [HumanMessage(content=question)]}
      except ValueError:
            print("Invalid input. Please enter a valid question")

def answer_question(state: ConversationState):
    """
    Part of the Conversation Sub-Graph.

    Generates a character's response to a question during the investigation.

    Args:
        state (ConversationState): The LangGraph State object containing:
            - messages: List of previous conversation messages. Used to store conversation history
            - character: Character object with persona and character details specifc to the character answering the question
            - story_details: Object containing crime details including:
                - victim_name, time_of_death, location_found
                - murder_weapon, cause_of_death
                - crime_scene_details, initial_clues

    Returns:
        dict: Adds response from the character to the conversation history
            - messages : Response to be added

    Note:
        The character's response:
        - Maintains consistency with their personal and knowledge
        - Considers their relationships with other characters
        - May include deception based on character motivations
        - Takes into account all previous conversation context
    """
    messages = state['messages']
    character = state['character']
    last_message = messages[-1]
    story = state['story_details']


    system_message = ANSWER_INSTRUCTIONS.format(
        subject_persona=character.persona,
        victim=story.victim_name,
        time=story.time_of_death,
        location=story.location_found,
        weapon=story.murder_weapon,
        cause=story.cause_of_death,
        scene=story.crime_scene_details,
        npc_brief=story.npc_brief,
        question=last_message.content
    )


    prompt = ChatPromptTemplate.from_messages(
          [
              (
                  "system",
                  system_message,
              ),
              MessagesPlaceholder(variable_name="messages"),
          ]
      )
    chain = prompt | llm
    answer = chain.invoke(messages)



    return {"messages":[answer]}


def where_to_go(state: ConversationState):
    """
    Part of the Conversation Sub-Graph.

    Determines the next conversation state based on the last message.

    Args:
        state (ConversationState): The LangGraph State object containing:
            - messages: List of previous conversation messages. Used to store conversation history
            - character: Character object with persona and character details
            - story_details: Object containing crime details including:
                - victim_name, time_of_death, location_found
                - murder_weapon, cause_of_death
                - crime_scene_details, initial_clues

    Returns:
        str: Either "end" to terminate conversation or "continue" to proceed

    Note:
        Checks for "EXIT" keyword in the last message to determine conversation flow.
    """

    messages = state['messages']
    last_message = messages[-1]
    if "EXIT" in last_message.content:
        return "end"
    else:
        return "continue"

def create_characters(state: GenerateGameState):
    """
    Create a cast of characters of the muder mystery game base on environment and the max characters.
    

    Args:
        state (GenerateGameState): The LangGraph State object containing:
            - environment: Description of the game's setting
            - max_characters: Maximum number of characters to create

    Returns:
        dict : Contains the generated character list. Adds to the State object.
            - characters : List of NPC objects with defined roles, including:
            - One killer
            - One victim
            - Supporting characters


    Notes: 
        - Uses structured LLM ouput to ensure consitent character creation
        - Each character has a name, role, detailed persona
        - Ensures character diversity and setting appropriateness
    """

    environment = state['environment']
    max_characters = state['max_characters']

    # Enforce structured output
    structured_llm = llm.with_structured_output(NPC)

    # System message
    system_message = CHARACTER_INSTRUCTIONS.replace("{{environment}}", environment)
    system_message = system_message.replace("{{max_characters}}", str(max_characters))

    # Generate characters
    result = structured_llm.invoke([
        SystemMessage(content=system_message),
        HumanMessage(content="Generate the set of characters")
    ])

    # Return the characters from the NPC object
    return {"characters": result.characters}

def create_story(state: GenerateGameState):
    """
    Generates the complete murder mystery scenario and storyline based on the provided environment and the generated characters.

    Args:
        state (GenerateGameState): The LangGraph State object containing:
            - environment: Description of the game's setting
            - characters: List of character objects generated in create_character step

    Returns:
        dict: Contains the complete story details. Adds to the State Object.
            - story_details: StoryDetails object including:
                - Crime scene information
                - Evidence and clues
                - Character relationships
                - Environmental factors

    Note:
        - Creates a solvable mystery without revealing the killer
        - Includes both true clues and red herrings
        - Ensures consistency between characters and environment
    """

    environment = state['environment']
    characters = state['characters']

    # Format character list for the prompt
    character_list = "\n".join([char.persona for char in characters])

    # Enforce structured output
    structured_llm = llm.with_structured_output(StoryDetails)

    # System message
    system_message = STORY_INSTRUCTIONS.replace("{{environment}}", environment)
    system_message = system_message.replace("{{characters}}", character_list)

    # Generate story details
    result = structured_llm.invoke([
        SystemMessage(content=system_message),
        HumanMessage(content="Generate the murder mystery scenario")
    ])

    # Return the story details
    return {"story_details": result}

def narrartor(state: GenerateGameState):
    """
    Part of the Game Loop Graph.

    Generates Dr. Watson's narration of the crime scene for Sherlock Holmes.

    Args:
        state (GenerateGameState): The LangGraph State object containing:
            - story_details: Complete information about the crime

    Returns:
        dict: Contains the narration message. Adds to the State Object.
            - messages: Dr. Watson's narrative description

    Note:
        - Provides a concise (100 words or less) introduction to the crime
        - Maintains Dr. Watson's characteristic narrative style
        - Sets the initial atmosphere for the investigation
    """
    story = state['story_details']

    # Format the message with the story details
    system_message = NARRATOR_INSTRUCTION.format(
        victim=story.victim_name,
        time=story.time_of_death,
        location=story.location_found,
        weapon=story.murder_weapon,
        cause=story.cause_of_death,
        scene=story.crime_scene_details
    )
    # Generate narration
    narration = llm.invoke([
        SystemMessage(content=system_message),
        HumanMessage(content="Create an atmospheric narration of the crime scene")
    ])

    return {"messages": [narration]}




def sherlock(state: GenerateGameState):
    """
    Part of the Game Loop Graph.

    Handles the character selection phase of the investigation.

    Args:
        state (GenerateGameState): The LangGraph State object containing:
            - characters: List of all character objects

    Returns:
        dict: Result of get_character_selection containing. Adds to the State Object.
            - selected_character_id: Index of selected character or None for guessing phase

    Note:
        - Displays character list with randomized order
        - Maintains mapping between display order and original character indices
        - Prevents selection of the victim character
    """
    characters = state['characters']

    # Display characters and get the mapping of displayed order to original indices
    display_to_original = print_characters_list(characters)

    # Get user selection
    return get_character_selection(characters, display_to_original)


KILLER_ROLE = "Killer"

def guesser(state: GenerateGameState):
    """
    Part of the Game Loop Graph.

    Manages the final phase where the player attempts to identify the killer.

    Args:
        state (GenerateGameState): The LangGraph State object containing:
            - num_guesses_left: Number of remaining guess attempts
            - characters: List of all character objects

    Returns:
        dict: Contains:
            - result: "end" if game is over, "sherlock" to continue investigation
            - num_guesses_left: Updated number of remaining guesses

    Note:
        - Handles the win/loss conditions
        - Maintains guess counter
        - Provides feedback on incorrect guesses
        - Excludes victim from suspect list
    """
    console = Console()
    num_guesses_left = state['num_guesses_left']
    all_characters = state['characters']
    non_victims = [char for char in all_characters if char.role != 'Victim']
    killer_character = next(char for char in all_characters if char.role == KILLER_ROLE)
    characters = list(sorted(non_victims, key=lambda x: x.name))

    # Print initial state
    console.rule("[bold red]🔍 Final Deduction[/bold red]")
    print_guesses_remaining(num_guesses_left)
    print_suspect_list(characters)

    is_win, is_lose = False, False

    while True:
        try:
            # Get user input
            choice = Prompt.ask(
                "\n[bold red]Who is the killer?[/bold red] (Enter suspect number)",
                default="",
                show_default=False
            )

            choice = int(choice)
            if 0 < choice <= len(characters):
                selected_character_id = choice - 1
                selected_character = characters[selected_character_id]

                if selected_character.role == KILLER_ROLE:
                    is_win = True
                    break
                else:
                    print_incorrect_guess()
                    num_guesses_left -= 1
                    if num_guesses_left > 0:
                        print_guesses_remaining(num_guesses_left)

                if num_guesses_left == 0:
                    is_lose = True
                    break

            else:
                console.print("[red]Invalid input. Please enter a valid suspect number.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a number.[/red]")

    # Print final result
    print_result(is_win, is_lose, killer_character.name)

    is_end = is_win or is_lose
    return {"result": "end", "num_guesses_left": num_guesses_left} if is_end else {"result": "sherlock", "num_guesses_left": num_guesses_left}
