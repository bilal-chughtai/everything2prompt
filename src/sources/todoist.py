import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from datetime import datetime, timedelta, date, time
from todoist_api_python.api import TodoistAPI
import os
from dotenv import load_dotenv
from src.models import TodoistNode, TodoistProject
from typing import Tuple
from jinja2 import Template


# Jinja template for formatting Todoist tasks
TODOIST_PROMPT_TEMPLATE = """*** Todoist Tasks ***
Task = task name
Description = detailed task description
Priority = priority level: 1=Highest, 2=High, 3=Medium, 4=Low
Tags = user-applied labels/tags
Due = due date set by user
Deadline = hard deadline set by user
Updated = when task was last modified
Completed = when task was marked as done (date) or "False" if not completed
Created = when task was created
{% for task in tasks %}
--- Task {{ loop.index }} ---
Task: {{ task.name }}{% if task.description %}
Description: {{ task.description }}{% endif %}{% if task.priority %}
Priority: {{ task.priority }}{% endif %}{% if task.tags %}
Tags: {{ task.tags | join(', ') }}{% endif %}{% if task.due %}
Due: {{ task.due.strftime('%Y-%m-%d') }}{% endif %}{% if task.deadline %}
Deadline: {{ task.deadline.strftig('%Y-%m-%d') }}{% endif %}{% if task.created_at %}
Created: {{ task.created_at.strftime('%Y-%m-%d') }}{% endif %}{% if task.updated_at %}
Updated: {{ task.updated_at.strftime('%Y-%m-%d') }}{% endif %}
Completed: {{ task.completed_at.strftime('%Y-%m-%d') if task.completed_at else 'False' }}{% endfor %}
"""


def create_todoist_prompt(tasks: list[TodoistNode]) -> str:
    """
    Create a formatted prompt from a list of Todoist tasks.
    Tasks are sorted by date (most recent first).
    """
    # Sort tasks by date (most recent first, None dates at the end)
    sorted_tasks = sorted(tasks, key=lambda x: (x.date is None, x.date), reverse=True)

    # Render the template
    template = Template(TODOIST_PROMPT_TEMPLATE)
    return template.render(tasks=sorted_tasks)


def get_todoist_api() -> TodoistAPI | None:
    """
    Initialize and return Todoist API client.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Initialize Todoist API client
    TODOIST_TOKEN = os.getenv("TODOIST_ACCESS_TOKEN")
    if not TODOIST_TOKEN:
        print("Warning: TODOIST_ACCESS_TOKEN not found in environment variables")
        return None

    return TodoistAPI(TODOIST_TOKEN)


def get_all_tasks(api: TodoistAPI, projects: list[TodoistProject]) -> list[TodoistNode]:
    """
    Get all active tasks from Todoist API.

    Args:
        api: Todoist API client
        projects: List of TodoistProject objects for task association
    """
    print("Fetching all active tasks...")
    task_nodes = []

    try:
        tasks_paginator = api.get_tasks()
        for task_page in tasks_paginator:
            for task in task_page:
                task_nodes.append(create_todoist_node_from_api_response(task, projects))

        print(f"Fetched {len(task_nodes)} active tasks")
        return task_nodes
    except Exception as e:
        print(f"Error fetching active tasks: {e}")
        return []


def get_completed_tasks_past_days(
    api: TodoistAPI, projects: list[TodoistProject], days_back: int = 7
) -> list[TodoistNode]:
    """
    Get completed tasks from the past N days.

    Args:
        api: Todoist API client
        projects: List of TodoistProject objects for task association
        days_back: Number of days to look back (default: 7)
    """
    print(f"Fetching completed tasks from the past {days_back} days...")
    completed_task_nodes = []

    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        completed_tasks_paginator = api.get_completed_tasks_by_completion_date(
            since=start_date,
            until=end_date,
        )

        for task_page in completed_tasks_paginator:
            for completed_task in task_page:
                completed_task_nodes.append(
                    create_todoist_node_from_api_response(completed_task, projects)
                )

        print(
            f"Fetched {len(completed_task_nodes)} completed tasks from the past {days_back} days"
        )
        return completed_task_nodes
    except Exception as e:
        print(f"Error fetching completed tasks: {e}")
        return []


def get_completed_tasks_past_week(
    api: TodoistAPI, projects: list[TodoistProject]
) -> list[TodoistNode]:
    """
    Get completed tasks from the past week (7 days).
    """
    return get_completed_tasks_past_days(api, projects, 7)


def get_all_projects(api: TodoistAPI) -> list[TodoistProject]:
    """
    Get all projects from Todoist API.
    """
    print("Fetching all projects...")
    project_nodes = []

    try:
        project_paginator = api.get_projects()
        for project_page in project_paginator:
            for project in project_page:
                project_nodes.append(create_todoist_project_from_api_response(project))

        print(f"Fetched {len(project_nodes)} projects")
        return project_nodes
    except Exception as e:
        print(f"Error fetching projects: {e}")
        return []


def get_all_todoist_data(
    days_back: int = 7,
) -> Tuple[list[TodoistNode], list[TodoistNode], list[TodoistProject]]:
    """
    Get all Todoist data: active tasks, completed tasks from past N days, and all projects.
    This fetches fresh data from the API, overwriting any existing/local data.

    Args:
        days_back: Number of days to look back for completed tasks (default: 7)

    Returns:
        Tuple of (active_tasks, completed_tasks, projects)
    """
    api = get_todoist_api()
    if not api:
        print("Failed to initialize Todoist API")
        return [], [], []

    # Get projects first, then tasks
    projects = get_all_projects(api)
    active_tasks = get_all_tasks(api, projects)
    completed_tasks = get_completed_tasks_past_days(api, projects, days_back)

    return active_tasks, completed_tasks, projects


def strip_timezone(
    dt: datetime | date | None,
) -> datetime | date | None:
    """
    Remove timezone information from datetime objects to make them timezone-naive.
    Also handles date objects by converting them to datetime if needed.
    """
    if dt is None:
        return None

    # If it's a date object, convert to datetime
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return datetime.combine(dt, time.min)

    # If it's a datetime object with timezone info, remove it
    if isinstance(dt, datetime) and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)

    return dt


def get_union_of_labels_and_project(task, projects: list) -> list[str]:
    """
    Get the union of the labels and the project name.
    """
    project_name = get_project_name(task, projects)
    return task.labels + [project_name] if project_name else task.labels


def get_canonical_date(task) -> datetime | None:
    """
    Get the canonical date of the task.
    """
    if task.completed_at:
        return strip_timezone(task.completed_at)
    if task.due:
        return strip_timezone(task.due.date)
    if task.deadline:
        return strip_timezone(task.deadline)
    if task.updated_at:
        return strip_timezone(task.updated_at)
    return None


def get_project_name(task, projects: list) -> str | None:
    """
    Get the project name of the task.
    """
    return next(
        (project.name for project in projects if project.project_id == task.project_id),
        None,
    )


def get_union_of_labels_and_project_with_project(task, project) -> list[str]:
    """
    Get the union of the labels and the project name.
    """
    combined_tags = set(task.labels)
    if project and project.name:
        combined_tags.add(project.name)
    return list(combined_tags)


def create_todoist_node_from_task_with_project(task, project):
    """
    Create TodoistNode from task with project information for proper tag generation.
    """
    return TodoistNode(
        name=task.content,  # Use content as the name
        task_id=task.id,
        content=task.content,
        description=task.description,
        project_id=task.project_id,
        parent_id=task.parent_id,
        labels=task.labels,
        priority=task.priority,
        due=strip_timezone(task.due),
        deadline=strip_timezone(task.deadline),
        completed_at=strip_timezone(task.completed_at),
        created_at=strip_timezone(task.created_at),
        updated_at=strip_timezone(task.updated_at),
        date=strip_timezone(get_canonical_date(task)),
        tags=get_union_of_labels_and_project_with_project(task, project),
    )


def create_todoist_project_from_api_response(response):
    """
    Create TodoistProject from API response.
    """
    return TodoistProject(
        name=response.name,
        project_id=response.id,
    )


def create_todoist_node_from_api_response(task, projects: list):
    """
    Create TodoistNode from API response.
    """
    return TodoistNode(
        name=task.content,  # Use content as the name
        task_id=task.id,
        content=task.content,
        description=task.description,
        project_id=task.project_id,
        parent_id=task.parent_id,
        labels=task.labels,
        priority=task.priority,
        due=strip_timezone(task.due.date if task.due else None),
        deadline=strip_timezone(task.deadline),
        completed_at=strip_timezone(task.completed_at),
        created_at=strip_timezone(task.created_at),
        updated_at=strip_timezone(task.updated_at),
        date=strip_timezone(get_canonical_date(task)),
        tags=get_union_of_labels_and_project(task, projects),
    )


if __name__ == "__main__":
    # Test the functionality with different time ranges
    print("Testing with default 7 days:")
    active_tasks, completed_tasks, projects = get_all_todoist_data()

    print("\nSummary (7 days):")
    print(f"Active tasks: {len(active_tasks)}")
    print(f"Completed tasks (past 7 days): {len(completed_tasks)}")
    print(f"Projects: {len(projects)}")

    # Test with 30 days
    print("\n" + "=" * 50)
    print("Testing with 30 days:")
    active_tasks_30, completed_tasks_30, projects_30 = get_all_todoist_data(30)

    print("\nSummary (30 days):")
    print(f"Active tasks: {len(active_tasks_30)}")
    print(f"Completed tasks (past 30 days): {len(completed_tasks_30)}")
    print(f"Projects: {len(projects_30)}")

    # Show some examples
    if active_tasks:
        print(f"\nExample active task: {active_tasks[0]}")

    if completed_tasks:
        print(f"Example completed task (7 days): {completed_tasks[0]}")

    if completed_tasks_30:
        print(f"Example completed task (30 days): {completed_tasks_30[0]}")

    if projects:
        print(f"Example project: {projects[0]}")
