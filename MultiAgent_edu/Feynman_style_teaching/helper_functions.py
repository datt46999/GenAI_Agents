from typing import List

from langchain_core.messages import HumanMessage

from data_structure import LearningCheckPoint, Checkpoints
"""
System include three utility function:

extract content from chunk

format checkpoint as message

generate checkpoint message
    


"""


def generate_checkpoint_message(checks: List[LearningCheckPoint]) -> HumanMessage:
    """
    Generate format message for learning checkpoint that need context

    Args:
        check (List[LearningCheckPoint]) : List of learning checkpoint object
    Return:
        (HumanMessage): Format message containing for checkpoint decristions, criteria and
                        verification methob, realy for context search
    """

    format_checkpoint = {}

    #chr(10) == \n
    for check in checks:
        checkpoint_text = f"""
        Description : {check.description}
        Success criteria:
        {chr(10).join(f'-{criterion}' for criterion in check.criteria)}
        Verification Methob : {check.verification}
        """
        format_checkpoint.appen(checkpoint_text)


    all_checks = "\n---\n".join(format_checkpoint)
    checkpoint_message = HumanMessage(content = f"""The following learning checkpoint need additional context:
    {all_checks}

    Please generate search requires to find relevant information.
    """)
    return checkpoint_message


def extract_content_from_chunk(chunks: list)-> str:
    """
    Extract and combine content from chunk and splits attributes

    Args: 
        chunk (list): list of chunk object that may contain split attibute
    Return:
        str: Combine content from all chunk join with new line
    """
    content = []

    for chunk in chunks:
        if hasattr(chunk, 'splits') and chunk.splits:
            chunk_content = '. '.join(chunk.splits)
            content.append(chunk_content)
    return '\n'.join(content)

def format_checkpoint_as_message(checkpoints: Checkpoints)-> str:
    """Convert checkpoint object to a format string for checkpoint message
    
    Args:
        checkpoints (Checkpoints): checkpoint object containinh  learning checkpoint

    Return:
        str : Formatted containing numbered checkpoint with with description and criteria
    """
    message = "Here are the learning checkpoints:\n\n"
    for i, checkpoint in enumerate(checkpoints.checkpoints, 1):
        message += f"Checkpoint {i}:\n"
        message += f"Description: {checkpoint.description}\n"
        message += "Success Criteria:\n"
        for criterion in checkpoint.criteria:
            message += f"- {criterion}\n"
    return message