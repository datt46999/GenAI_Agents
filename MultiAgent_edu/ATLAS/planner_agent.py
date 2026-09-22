"""
planner analysis -> Calendar analysis -> Plan generate
"""
import os
import json
from datetime import datetime, timezone, timedelta

from langgraph.graph import StateGraph, END, START

from utils import AcademicState, ReActAgent

class PlannerAgent(ReActAgent):
    """
    Planner agent with own subgraph for the plan generate.
    This agent will be analysis student calander and analysis task determine 
    then combine with the student profile to generate comprehensive study plan
    """
    def __init__(self, llm):
        """
        Inititalize with the planner agent
        Args:
            llm: large languare model instance for text generate
        """
        super().__init__(llm)
        self.llm = llm
        self.few_shot_example = self._initialize_fewshot()
        self.workflow = self.create_subgraph()

    def _initialize_fewshot(self):
        """
        Define example scenarior to help AI Understand how to handle different situation
        """
        return [
            {
                'input': 'Help with exam prep while managing ADHD and football',
                'thought': 'Need to check calendar conflicts and energy patterns',
                'action': 'search_calendar',
                'observation': 'Football match at 6PM exam tomorrow 9AM',
                'plan':"""ADHD-OPTIMIZED SCHEDULE:
                    PRE-FOOTBALL (2PM-5PM):
                    - 3x20min study sprints
                    - Movement breaks
                    - Quick rewards after each sprint

                    FOOTBALL MATCH (6PM-8PM):
                    - Use as dopamine reset
                    - Formula review during breaks

                    POST-MATCH (9PM-12AM):
                    - Environment: Café noise
                    - 15/5 study/break cycles
                    - Location changes hourly

                    EMERGENCY PROTOCOLS:
                    - Focus lost → jumping jacks
                    - Overwhelmed → room change
                    - Brain fog → cold shower"""
            },
            {
                "input": "Struggling with multiple deadlines",
                "thought": "Check task priorities and performance issues",
                "action": "analyze_tasks",
                "observation": "3 assignments due, lowest grade in Calculus",
                "plan": """PRIORITY SCHEDULE:
                    HIGH-FOCUS SLOTS:
                    - Morning: Calculus practice
                    - Post-workout: Assignments
                    - Night: Quick reviews

                    ADHD MANAGEMENT:
                    - Task timer challenges
                    - Reward system per completion
                    - Study buddy accountability"""
            }
        ]
    def create_subgraph(self) -> StateGraph:
        """

        calendar_analysis
        Create workflow graph that define how to planner processes request
        1. First analysis calendar of student 
        2. Seconde analysis task
        3. Finally generate plan
        """
        subgraph = StateGraph(AcademicState)
        subgraph.set_entry_point("calendar_analyzer")
        subgraph.add_node("calendar_analyzer", self.calendar_analysis)
        subgraph.add_node("task_analysis", self.task_analysis)
        subgraph.add_node("plan_generate", self.plan_generate)

        subgraph.add_edge("calendar_analyzer", "task_analysis")
        subgraph.add_edge("task_analysis", "plan_generate")
        subgraph.add_edge("plan_generate", END) 


        # set where is workflow begin
        
        return subgraph.compile()

    async def calendar_analysis(self, state: AcademicState) -> AcademicState: 
        """
        Analysis calender of student to find:
        + available study time
        + potential scheduling conflict
        + Energy pattern throughout the day
        """
        events = state["calendar"].get('events', [])
        now = datetime.now(timezone.utc)
        future = now + timedelta(days=7)

        filtered_events =[event for event in events
                       if now <= datetime.fromisoformat(event['starts']['dateTime'])<future]

        prompt = """Analyze calender event and identify:
        Events: {events}

        Focus on:
        - Available time blocks
        - Energy impact of activities
        - Potential conflicts
        - Recovery periods
        - Study opportunity windows
        - Activity patterns
        - Schedule optimization
        """
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(filtered_events)}
        ]

        response = await self.llm.agenerate(messages)
   
        return {
            "results": {
                "calendar_analyzer": {
                    "analysis":response
                }
            }
        }

    async def task_analysis(self, state: AcademicState)-> AcademicState:
        """
        Analize task a determine:
        + Priority order
        + Time need for each task 
        + Best approach for completed
        """
        tasks = state['tasks'].get('tasks', [])
        prompt ="""Analysis tasks and create priority structure:
        Tasks: {tasks}

        Consider:
        - Urgency levels
        - Task complexity
        - Energy requirements
        - Dependencies
        - Required focus levels
        - Time estimations
        - Learning objectives
        - Success criteria
        """
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(tasks)}
        ]

        response = await self.llm.agenerate(messages)

        return {
            "results": {
                "task_analysis": {
                    "analysis": response
                }
            }
        }

    async def plan_generate(self, state: AcademicState) -> AcademicState:
        """
        Create comprehensive study plan by combining:
        -Profile student (student learning type)
        -Calendar student (avalable time)
        -tasks student (what time need to be done)
        """
        # gather all previous analysis
        profile_analysis = state["results"]["profile_analysis"]
        calendar_analysis = state["results"]["calendar_analyzer"]
        task_analysis = state["results"]["task_analysis"]

        prompt = f"""AI Planning Assistant: Create focused study plan using ReACT framework.

          INPUT CONTEXT:
          - Profile Analysis: {profile_analysis}
          - Calendar Analysis: {calendar_analysis}
          - Task Analysis: {task_analysis}

          EXAMPLES:
          {json.dumps(self.few_shot_example, indent=2)}

          INSTRUCTIONS:
          1. Follow ReACT pattern:
            Thought: Analyze situation and needs
            Action: Consider all analyses
            Observation: Synthesize findings
            Plan: Create structured plan

          2. Address:
            - ADHD management strategies
            - Energy level optimization
            - Task chunking methods
            - Focus period scheduling
            - Environment switching tactics
            - Recovery period planning
            - Social/sport activity balance

          3. Include:
            - Emergency protocols
            - Backup strategies
            - Quick wins
            - Reward system
            - Progress tracking
            - Adjustment triggers

          Pls act as an intelligent tool to help the students reach their goals or overcome struggles and answer with informal words.

          FORMAT:
          Thought: [reasoning and situation analysis]
          Action: [synthesis approach]
          Observation: [key findings]
          Plan: [actionable steps and structural schedule]
          """

        messages = [
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': state["messages"][-1].content}
        ]

        response = await self.llm.agenerate(messages, temperature = 0.5)
        return {
                'results': {
                    'generated_notes':{
                        'notes': response
                    }
                }
            }

    async def __call__(self, state: AcademicState) -> AcademicState:
        """
        Main execution method that run the entire planning workflow
        1. calendar Analysis
        2. Tasks analysis
        3. plan generate
        """
        try:
            final_state = await self.workflow.ainvoke(state)

            return {"notes": final_state["results"]["generated_notes"]['notes']}

        except:
            return {'notes', 'Error generate notes. Please try again.'}