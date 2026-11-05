import os
from typing import Dict, Any
from dotenv import load_dotenv


from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.utils.math import cosine_similarity
from langchain_tavily import TavilySearch
from langchain_core.messages import HumanMessage, SystemMessage


from semantic_chunkers import StatisticalChunker
from semantic_router.encoders import OpenAIEncoder

from route import LearningState 
from helper_functions import extract_content_from_chunk, generate_checkpoint_message, format_checkpoint_as_message
from data_structure import ContextStore, InContext, SearchQuery, OutputStruture, LearningVerification, FeynmanTeaching, Checkpoints


"""
========================================================

Configure setting

========================================================
"""
load_dotenv()

MODEL_EMBEDDING = os.getenv("MODEL_EMBEDDING")
embedding = OpenAIEmbeddings(model = MODEL_EMBEDDING)
context_store = ContextStore()
llm = ChatOpenAI(model= os.getenv("MODEL_NAME"), temperature = 0)


tavily_search = TavilySearch(max_results=3)



"""
========================================================

Prompts config

========================================================
"""
LEARNING_CHECKPOINT_GENERATER =SystemMessage(content ="""You will be given a learning topic title and learning objectives.
Your goal is to generate clear learning checkpoints that will help verify understanding and progress through the topic.
The output should be in the following dictionary structure:
checkpoint 
-> description (level checkpoint description)
-> criteria
-> verification (How to verify this checkpoint (Feynman Methods))
Requirements for each checkpoint:
- Description should be clear and concise
- Criteria should be specific and measurable (3-5 items)
- Verification method should be practical and appropriate for the level
- Verification will be checked by language model, so it must by in natural language
- All elements should align with the learning objectives
- Use action verbs and clear language
Ensure all checkpoints progress logically from foundation to mastery.
IMPORTANT - ANSWER ONLY 3 CHECKPOINTS
""")
VALIDATE_CONTEXT = SystemMessage(content ="""You will be given learning a criteria and context.
Check if the criteria could be answered using the context
Alway answer YES or NO""")
CHECKPOINT_BASE_QUERY_GENERATOR=SystemMessage(content ="""You will be given learning checkpoint for a topic.
Your goal to generate search queries that will retrive content each checkpoint's requirement from retrieve system or web search.
1. Analyze each checkpoit carefully.
2. For each generate, each generate ONE targeted search query that will retrieve: 
    -Content for checkpoitn verification
"""
)

QUESTION_GENERATOR =SystemMessage(content ="""You will be given a checkpoint description, success criteria, and verification method.
Your goal is to generate an appropriate question that aligns with the checkpoint's verification requirements.
The question should:
1. Follow the specified verification method
2. Cover all success criteria
3. Encourage demonstration of understanding
4. Be clear and specific
Output should be a single, well-formulated question that effectively tests the checkpoint's learning objectives.
""")


ANSWER_VERIFIER=SystemMessage(content ="""You will be given a student's answer, question, checkpoint details, and relevant context.
Your goal is to analyze the answer against the checkpoint criteria and provided context.
Analyze considering:
1. Alignment with verification method specified
2. Coverage of all success criteria
3. Use of relevant concepts from context
4. Depth and accuracy of understanding
Output should include:
- understanding_level: float between 0 and 1
- feedback: detailed explanation of the assessment
- suggestions: list of specific improvements
- context_alignment: boolean indicating if the answer aligns with provided context""")


FEYNMAN_TEACHING=SystemMessage(content ="""You will be given verification results, checkpoint criteria, and learning context.
Your goal is to create a Feynman-style teaching explanation for concepts that need reinforcement.
The explanation should include:
1. Simplified explanation without technical jargon
2. Concrete, relatable analogies
3. Key concepts to remember
Output should follow the Feynman technique:
- simplified_explanation: clear, jargon-free explanation
- key_concepts: list of essential points
- analogies: list of relevant, concrete comparisons
Focus on making complex ideas accessible and memorable.""")










"""
==============================================================

define function

==============================================================
"""

def generate_checkpoints(state: LearningState):
    """Creates learning checkpoints based on given topic and goals."""
    structured_llm = llm.with_structured_output(Checkpoints)
    messages = [
        LEARNING_CHECKPOINT_GENERATER,
        SystemMessage(content=f"Topic: {state['topic']}"),
        SystemMessage(content=f"Goals: {', '.join(str(goal) for goal in state['goals'])}")
    ]
    checkpoints = structured_llm.invoke(messages)
    return {"checkpoints": checkpoints}


def chunk_context(state: LearningState):
    """Splipts text into manageable chunk and generate text embedding"""

    encoder = OpenAIEncoder(name=MODEL_EMBEDDING )
    chunker = StatisticalChunker(
        encoder = encoder,
        min_split_tokens =128,
        max_split_tokens = 512 
    )

    chunks = chunker([state['context']])

    content = []
    for chunk in chunks:
        content.append(extract_content_from_chunk(chunk))

    chunk_embedding = embedding.embed_documents(content)
    context_key = context_store.save_context(
        content, 
        chunk_embedding,
        key = state.get('context_key')
    )

    return {"context_chunks": content, "context_key": context_key}
# def chunk_context(state: LearningtState):
#     """Splits context into manageable chunks and generates their embeddings."""
#     encoder = OpenAIEncoder(name="text-embedding-3-large")
#     chunker = StatisticalChunker(
#         encoder=encoder,
#         min_split_tokens=128,
#         max_split_tokens=512
#     )
    
#     chunks = chunker([state['context']])
#     content = []
#     for chunk in chunks:
#         content.append(extract_content_from_chunks(chunk))

#     chunk_embeddings = embeddings.embed_documents(content)
#     context_key = context_store.save_context(
#         content,
#         chunk_embeddings,
#         key=state.get('context_key')
#     )
#     return {"context_chunks": content, "context_key": context_key}

def context_validation(state: LearningState)-> Dict[str, Any]:
    """Validation context coverage againts checkpoint criteria using stored embedding"""
    context = context_store.get_context(state['context_key'])
    chunks = context['chunks']
    chunks_embeddings = context["embeddings"]

    checks =[]
    struture_llm = llm.with_structured_output(InContext)

    for checkpoint in state['checkpoints'].checkpoints:
        query = embedding.embed_query(checkpoint.verification)

        similarities = cosine_similarity([query], chunks_embeddings)[0]
        # get top 3 highest
        top_similar = sorted(range(len(similarities)), key = lambda i : similarities[i], reverse= True)[:3]

        relevant_chunk = [chunks[i] for i in top_similar]
        messages = [
            VALIDATE_CONTEXT, 
            HumanMessage(content = f"""
            Criteria:
            {chr(10).join(f"- {c}" for c in checkpoint.criteria)}


            Context:
            {chr(10).join(relevant_chunk)}
            """)
        ]

        response = struture_llm.invoke(messages)

        if response.in_context.lower() == "no":
            checks.append(checkpoint)
    
    if checks:
        structured_llm = llm.with_structured_output(SearchQuery)
        checkpoints_message = generate_checkpoint_message(checks)
        
        messages = [CHECKPOINT_BASE_QUERY_GENERATOR, checkpoints_message]
        search_queries = structured_llm.invoke(messages)
        return {"search_queries": search_queries}
    
    return {"search_queries": None}



def generate_query(state: LearningState)-> Dict[str, Any]:
    """Generate search query base on learning checkpoint form current state"""
    structure_llm = llm.with_structured_output(SearchQuery)
    checkpoint_message = HumanMessage(content = format_checkpoint_as_message(state['checkpoints']))
    messages = [CHECKPOINT_BASE_QUERY_GENERATOR, checkpoint_message]
    search_queries = structure_llm.invoke(messages)
    return {"search_queries": search_queries}




def search_web(state: LearningState) -> Dict[str, Any]:
    """
    Retrieval and process web search results base on search queries
    """
    search_query = state['search_queries'].search_queries

    all_search_doc =[]
    for query in search_query:
        search_docs = tavily_search.invoke(query)
        all_search_doc.extend(search_docs)

    format_search_docs = [
        f"Context: {doc['content']}\n Source: {doc['url']}\n" for doc in all_search_doc
    ]

    chunk_embedding = embedding.embed_documents(format_search_docs)

    context_key = context_store.save_context(
        format_search_docs,
        chunk_embedding,
        key = state.get('context_key')
    )
    return {'context_chunks': format_search_docs}

def generate_question(state: LearningState)-> Dict[str, Any]:
    """generate assissment question base on current checkpoint verification requirement"""    

    structured_llm = llm.with_structured_output(OutputStruture)
    cur_checkpoint = state['current_checkpoint']
    checkpoint_info = state['checkpoints'].checkpoints[cur_checkpoint]

    message = [
        QUESTION_GENERATOR, 
        HumanMessage(content = f"""
        Checkpoint Description: {checkpoint_info.description}
        Success Criteria:
        {chr(10).join(f"- {c}" for c in checkpoint_info.criteria)}
        Verification Method: {checkpoint_info.verification}
        
        Generate an appropriate verification question.
        """)
    ]
    question_cur = structured_llm.invoke(message)
    return {"current_question": question_cur.question}



def verify_answer(state: LearningState)-> Dict[str, Any]:
    """Evaluates user answer against  checkpoint criteria user relevant context chunk"""
    print("STATE KEYS:", list(state.keys()))
    structure_llm = llm.with_structured_output(LearningVerification)

    cur_checkpoint = state["current_checkpoint"]
    checkpoint_info = state["checkpoints"].checkpoints[cur_checkpoint]

    context = context_store.get_context(state['context_key'])
    chunks = context['chunks']
    chunk_embedding= context["embeddings"]


    query = embedding.embed_query(checkpoint_info.verification)

    similarity = cosine_similarity([query], chunk_embedding)[0]
    top_similarty = sorted(range(len(similarity)), key = lambda i: similarity[i], reverse= True)[:3]

    relevant_chunks = [chunks[i] for i in top_similarty]

    message = [
        ANSWER_VERIFIER,
        HumanMessage(content=f"""
        Question: {state['current_question']}
        Answer: {state['current_answer']}
        
        Checkpoint Description: {checkpoint_info.description}
        Success Criteria:
        {chr(10).join(f"- {c}" for c in checkpoint_info.criteria)}
        Verification Method: {checkpoint_info.verification}
        
        Context:
        {chr(10).join(relevant_chunks)}
        
        Assess the answer.""")

    ]

    verification = structure_llm.invoke(message)
    return {"verifications": verification}

def teach_concept(state: LearningState) -> Dict[str, Any]:
    """Create Similified feynama-style explanations the concept that need reinforcement"""
    structure_llm = llm.with_structured_output(FeynmanTeaching)

    cur_checkpoint = state['current_checkpoint']
    checkpoint_info = state['checkpoints'].checkpoints[cur_checkpoint]

    message =[
        FEYNMAN_TEACHING,
        HumanMessage(content = f"""
        Criteria: {checkpoint_info.criteria}
        Verification: {state['verifications']}
        
        Context:
        {state['context_chunks']}
        
        Create a Feynman teaching explanation.""")
    ]
    teaching = structure_llm.invoke(message)

    return {'teachings': teaching}


def user_answer(state: LearningState):
    """Placeholder for handling user's answer input."""
    pass

def next_checkpoint(state: LearningState):
    """Advances to the next checkpoint in the learning sequence."""
    cur_checkpoint = state['current_checkpoint'] + 1
    return {'current_checkpoint': cur_checkpoint}