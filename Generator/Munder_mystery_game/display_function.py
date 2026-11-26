import random

from IPython.display import display, HTML
from rich.box import HEAVY_EDGE
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

console = Console()


def _content(obj):
    """Return the text of an LLM response object or a plain string, escaped for Rich markup."""
    text = getattr(obj, "content", obj)
    return escape(str(text))


def _is_victim(character):
    return str(getattr(character, "role", "")).lower() == "victim"


def print_game_header():
    """
    Displays the main header for the Murder Mystery Investigation game using HTML formatting.
    """
    display(HTML("""
        <div style="text-align:center; padding:16px; margin:8px 0;
                    border:3px solid #1e3a8a; border-radius:10px;
                    background:linear-gradient(90deg,#0f172a,#1e3a8a,#0f172a);">
            <h1 style="color:#facc15; font-family:Georgia,serif; margin:0; letter-spacing:2px;">
                🕵️‍♂️ MURDER MYSTERY INVESTIGATION 🔍
            </h1>
        </div>
    """))


def print_narration(narration):
    """
    Prints the narration dialogue from Dr. John Watson with styled formatting.

    Args:
        narration: The LLM response object containing the narration content in its 'content' attribute.
    """
    console.print(Panel(
        f"[bold]Dr. John Watson[/bold]:\n\n{_content(narration)}",
        border_style="blue",
        padding=(1, 2),
        title="💬 Dialogue",
        title_align="left"
    ))
    console.rule(style="blue")


def print_introduction(character, narration):
    """
    Displays the introduction dialogue for a character with styled formatting.

    Args:
        character: Character object containing character information.
        narration: LLM response object containing the narration content in its 'content' attribute.
    """
    name = escape(character.name)
    console.rule(f"[bold blue]Conversation with {name}[/bold blue]", style="blue")
    console.print(Panel(
        f"[bold]{name}[/bold]:\n\n{_content(narration)}",
        border_style="blue",
        padding=(1, 2),
        title="💬 Dialogue",
        title_align="left"
    ))
    console.rule(style="blue")


def get_player_input(character_name):
    """
    Prompts the player for input during character interactions.

    Args:
        character_name (str): Name of the character being questioned.

    Returns:
        str: The player's input question or 'EXIT' to end the conversation.
    """
    console.print(Panel(
        f"[bold blue]Ask your question to {escape(character_name)}[/bold blue]\n"
        f"[dim]Type 'EXIT' to end conversation[/dim]",
        box=HEAVY_EDGE,
        border_style="blue",
        padding=(1, 2),
        title="💭 Your Question",
        title_align="left"
    ))

    question = Prompt.ask(
        "[bold yellow]Detective[/bold yellow]",
        default="",
        show_default=False
    ).strip()

    if question and question.lower() != "exit":
        console.print(Panel(
            f"[italic]{escape(question)}[/italic]",
            border_style="yellow",
            padding=(1, 1),
            title="🔍 Asked",
            title_align="left"
        ))

    return question


def print_character_answer(character, reaction):
    """
    Displays a character's answer with styled formatting.

    Args:
        character: Character object containing character information.
        reaction (str): The character's response or reaction as generated from the LLM.
    """
    console.print(Panel(
        f"[bold]{escape(character.name)}'s Answer[/bold]:\n\n[italic]{_content(reaction)}[/italic]",
        border_style="cyan",
        padding=(1, 2),
        title="🗣️ Answer",
        title_align="left"
    ))


def print_characters_list(characters):
    """
    Displays a formatted table of all characters in the game with their backgrounds.

    Args:
        characters (list): List of character objects containing name, role, and backstory.

    Returns:
        dict: Mapping of displayed positions (0-based) to original character indices.
    """
    console.print("\n[bold blue]CHARACTERS[/bold blue]", justify="center")

    char_list = list(enumerate(characters))
    random.shuffle(char_list)

    table = Table(
        show_header=True,
        header_style="bold magenta",
        box=HEAVY_EDGE,
        expand=True,
        show_lines=True  # border between rows
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Name", style="bold cyan", width=20)
    table.add_column("Background", style="green")

    display_to_original = {}
    for display_pos, (orig_idx, character) in enumerate(char_list):
        name_text = escape(character.name)
        if _is_victim(character):
            name_text += " [red](victim)[/red]"

        table.add_row(
            str(display_pos + 1),
            name_text,
            Text(str(character.backstory), overflow="fold")
        )
        display_to_original[display_pos] = orig_idx

    console.print(table)
    return display_to_original


def get_character_selection(characters, display_to_original):
    """
    Handles the player's character selection for investigation during the game.

    Args:
        characters (list): List of character objects.
        display_to_original (dict): Mapping of displayed positions to original indices.

    Returns:
        dict: {"selected_character_id": int} or {"selected_character_id": None}
              when the player enters -1 to guess the killer.
    """
    while True:
        console.print(Panel(
            "[bold blue]Enter the number of the character to investigate[/bold blue]\n"
            "[dim]Enter -1 to Guess the Killer[/dim]",
            border_style="blue",
            title="👤 Selection",
            title_align="left"
        ))

        raw = Prompt.ask(
            "[bold yellow]Detective[/bold yellow]",
            default="-1",
            show_default=False
        )

        try:
            choice = int(raw)
        except ValueError:
            console.print("[red]Invalid input. Please enter a number.[/red]")
            continue

        if choice == -1:
            return {"selected_character_id": None}

        if not (0 < choice <= len(characters)) or (choice - 1) not in display_to_original:
            console.print("[red]Invalid input. Please enter a number within the range or -1.[/red]")
            continue

        original_idx = display_to_original[choice - 1]
        selected_character = characters[original_idx]

        if _is_victim(selected_character):
            console.print("[red]Invalid input. You are unable to choose the victim.[/red]")
            continue

        console.print(f"You have selected [bold cyan]{escape(selected_character.name)}[/bold cyan]")
        return {"selected_character_id": original_idx}


def get_player_yesno_answer(question):
    """
    Prompts the player for a yes/no response regarding Sherlock AI assistance.

    Args:
        question (str): The player instruction/question to display to the player.

    Returns:
        str: Player's response, lowercased ('y' for yes, 'n' for no/exit).
    """
    console.print(Panel(
        f"[bold blue]{escape(question)}[/bold blue]\n"
        f"Enter 'y' to get his help or 'n' to ask by yourself or exit",
        box=HEAVY_EDGE,
        border_style="blue",
        padding=(1, 2),
        title="🤖🕵️ Sherlock AI",
        title_align="left"
    ))

    answer = Prompt.ask(
        "[bold yellow]Detective[/bold yellow]",
        default="",
        show_default=False
    )
    return answer.strip().lower()


def print_suspect_list(characters):
    """
    Displays a formatted table of all suspects in the investigation (sorted by name).

    Args:
        characters (list): List of character objects to be displayed as suspects.
    """
    table = Table(
        show_header=True,
        header_style="bold bright_red",
        box=HEAVY_EDGE,
        expand=True,
        title="[bold bright_red]🔍 Suspects[/bold bright_red]"
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Name", style="bold bright_red")

    for idx, character in enumerate(sorted(characters, key=lambda x: x.name), 1):
        table.add_row(str(idx), escape(character.name))

    console.print(table)


def print_guesses_remaining(num_guesses):
    """
    Displays the number of remaining guesses available to the player.

    Args:
        num_guesses (int): Number of guesses remaining.
    """
    console.print(Panel(
        f"[bold]You have {num_guesses} {'guess' if num_guesses == 1 else 'guesses'} remaining[/bold]",
        border_style="yellow",
        title="⏳ Guesses",
        title_align="left"
    ))


def print_result(is_win, is_lose, killer_name=None):
    """
    Displays the game result message indicating whether the player won or lost.

    Args:
        is_win (bool): True if player won the game.
        is_lose (bool): True if player lost the game.
        killer_name (str, optional): Name of the killer to reveal if player lost.
    """
    if is_win:
        console.print(Panel(
            "[bold green]Congratulations! You have correctly identified the killer.[/bold green]",
            border_style="green",
            title="🎯 Success",
            title_align="left"
        ))
    elif is_lose:
        killer = escape(killer_name) if killer_name else "unknown"
        console.print(Panel(
            f"[bold bright_red]Investigation Failed![/bold bright_red]\n"
            f"[bright_red]The killer was {killer}.[/bright_red]",
            border_style="bright_red",
            title="❌ Game Over",
            title_align="left"
        ))


def print_incorrect_guess():
    """
    Displays a message indicating that the player's guess was incorrect.
    """
    console.print(Panel(
        "[bold yellow]The person you chose was innocent.[/bold yellow]",
        border_style="yellow",
        title="❗ Wrong Guess",
        title_align="left"
    ))