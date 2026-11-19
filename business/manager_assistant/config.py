import os
import uuid
from pydantic import BaseModel, Field

from typing import List, TypedDict
from langchain_openai import AzureChatOpenAI, ChatOpenAI




llm = ChatOpenAI(
        deployment_name='gpt-4o-mini',  # Your actual deployment name
    )
"""
Data Models
"""
class Task(BaseModel):
    id: uuid.UUID = Field(default_factory = uuid.uuid4, description = "Unique identifier for the task")
    task_name: str = Field(description = "Name of the task")
    task_description: str = Field(description = "Description of the task")

    estimated_day: int = Field(description= "Estimated number of days to complete the task")

class TaskList(BaseModel):
    tasks: List[Task] = Field(description ="List of tasks")
class TaskDependency(BaseModel):
    """Task dependency model"""
    task: Task = Field(description="Task")
    dependent_tasks: List[Task] = Field(description="List of dependent tasks")

class TeamMember(BaseModel):
    name: str = Field(description="Name of the team member")
    profile: str = Field(description="Profile of the team member")

"""
Iterative assessment
"""
class TaskSchedule(BaseModel):
    """Schedule schedule class"""
    task: Task = Field(description="Task")
    start_day: int = Field(description="Start day of the task")
    end_day: int = Field(description="End day of the task")


class TaskAllocation(BaseModel):
    """Task allocation class"""
    task: Task = Field(description="Task")
    team_member: TeamMember = Field(description="Team members assigned to the task")
"""
Lists
"""

class DependencyList(BaseModel):
    """List of task dependencies"""
    dependencies: List[TaskDependency] = Field(description="List of task despendencies")

class Schedule(BaseModel):
    """List of task schedule"""
    schedule: List[TaskSchedule] = Field(description = "List of task schedule")

class TaskAllocationList(BaseModel):
    """List of task allocation"""
    task_allocations: List[TaskAllocation] = Field(description ="List of tasks allocation for each iteration")
"""
Iteration
"""

class Risk(BaseModel):
    """Risk of a task"""
    task: Task = Field(description="Task")
    score: str = Field(description="Risk associated with the task")

class RiskList(BaseModel):
    """List of risks for each iteration"""
    risks: List[Risk] = Field(description="List of risks")

class RiskListIteration(BaseModel):
    """List of risks for each iteration"""
    risks_iteration: List[RiskList] = Field(description="List of risks for each iteration")




class AgentState(TypedDict):
    project_description: str
    tasks: TaskList
    dependencies: DependencyList

    insights:List[str]
    schedule: Schedule
    schedule_interaction : List[Schedule]

    task_allocations: TaskAllocationList
    task_allocations_iteration: List[TaskAllocationList]

    risks: RiskList
    risks_iterations: List[RiskList]
    project_rick_score: int
    iteration_number: int
    project_rick_score_iteration: List[int]

    max_iteration: int
