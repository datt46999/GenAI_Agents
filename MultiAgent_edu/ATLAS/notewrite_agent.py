import os
import json
from datetime import datetime, timezone, timedelta

from langgraph.graph import StateGraph, END, START

from utils import AcademicState, ReActAgent

class NoteWriteAgent(ReActAgent):
    """
    NoteWrite agent with it own subgraph workflow for note generation.
    this agent specilizes in creating personlized study materials by analyzing
    learning styles and generate structured notes.
    """

    def __init__(self, llm):
        """
        Initilize the NoteWrite agent with an llm backend and example template
        Args:
            llm: language model instance for text generate
        """
        super().__init__(llm)
        self.llm = llm
        self.few_shot_examples = self._instance_fewshot()
        self.workflow = self.create_subgraph()

    def _instance_fewshot(self)->list[dict]:
        """
        Define example scenarior to help AI Understand how to handle different situation
        """
        return [
            {
                "input": "Need to cram Calculus III for tomorrow",
                "template": "Quick Review",
                "notes": """CALCULUS III ESSENTIALS:

                1. CORE CONCEPTS (80/20 Rule):
                   • Multiple Integrals → volume/area
                   • Vector Calculus → flow/force/rotation
                   • KEY FORMULAS:
                     - Triple integrals in cylindrical/spherical coords
                     - Curl, divergence, gradient relationships

                2. COMMON EXAM PATTERNS:
                   • Find critical points
                   • Calculate flux/work
                   • Optimize with constraints

                3. QUICKSTART GUIDE:
                   • Always draw 3D diagrams
                   • Check units match
                   • Use symmetry to simplify

                4. EMERGENCY TIPS:
                   • If stuck, try converting coordinates
                   • Check boundary conditions
                   • Look for special patterns"""
            }
        ]
    def create_subgraph(self)->StateGraph:
        """
        NoteWriter interal workflow as a state machine
        The workflow consists of two main steps:
        + Analysis learning style and centent requirement
        + Generate personalized notes
        """
        subgraph = StateGraph(AcademicState)
        subgraph.add_node("notewriter_analyze", self.learning_style_analysis)
        subgraph.add_node("notewriter_generate", self.generate_notes)


        subgraph.add_edge(START, "notewriter_analyze")
        subgraph.add_edge("notewriter_analyze", "notewriter_generate")
        subgraph.add_edge("notewriter_generate", END)

        return subgraph.compile()
    async def learning_style_analysis(self, state: AcademicState)->AcademicState:
        """
        Analysis student profile and request to determine optimize note structure

        Using LLM to analyse:
        - student's learning style of preference
        - specific content request
        - Time containts and requirement

        Args:
            state: Current academic state containing student profile and message
        Returns:
            Update state with learining analysis result 
        """

        profile_student = state["profile"]
        learning_style = profile_student["learning_preferences"]["learning_style"]
        prompt = f"""Analyze content requirements and determine optimal note structure:

        STUDENT PROFILE:
        - Learning Style: {json.dumps(learning_style, indent=2)}
        - Request: {state['messages'][-1].content}

        FORMAT:
        1. Key Topics (80/20 principle)
        2. Learning Style Adaptations
        3. Time Management Strategy
        4. Quick Reference Format

        FOCUS ON:
        - Essential concepts that give maximum understanding
        - Visual and interactive elements
        - Time-optimized study methods
        """

        response = await self.llm.agenerate(
            {'role':'user', 'content': prompt}
        )
        return {
            "results":{
                "learning_analysis":{
                    "analysis": response
                }
            }
        }

    async def generate_notes(self, state: AcademicState) -> AcademicState:
        """
        Genetate personalized study notes by on the learning analysis
        
        Use the LLM  to create structure note that are:
        - Adapted the student's learning style
        - forcus on essitial concepts(80/20 principle)
        - Time optimize fot study period

        Args:
            state: current academic with the learning analysis
        Return:
            Updata state with generate note
        """

        analysis = state["results"].get('learning_style', '')
        learning_style = state['profile']['learning_preferences']['learning_style']

        prompt = f"""Create concise, high-impact study materials based on analysis:

        ANALYSIS: {analysis}
        LEARNING STYLE: {json.dumps(learning_style, indent=2)}
        REQUEST: {state['messages'][-1].content}

        EXAMPLES:
        {json.dumps(self.few_shot_examples, indent=2)}

        FORMAT:
        **THREE-WEEK INTENSIVE STUDY PLANNER**

        [Generate structured notes with:]
        1. Weekly breakdown
        2. Daily focus areas
        3. Core concepts
        4. Emergency tips
        """
        responses = await self.llm.agenerate(
            {'role':'system', 'content': prompt}
        )
        return {
            'results': {
                'generated_notes':{
                    'notes': responses
                }
            }
        }
    async def __call__(self, state: AcademicState)->dict:
        """
        The main execution method for the Notewriter agent.
        Executes the complete workflow:
        + analysis learning requirements
        + generate personalize notes
        """
        try:
            final_state = await self.workflow.ainvoke(state)
            # notes = final_state['results'].get('generated_notes', {})
            return {'notes', final_state['results'].get('generated_notes')}
        except Exception as e:
            return{'notes': "Error generate note. Please try again"}