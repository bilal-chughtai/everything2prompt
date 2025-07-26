from datetime import datetime, timedelta
from todoist_api_python.api import TodoistAPI
import os
from dotenv import load_dotenv
from models import TodoistNode, TodoistProject
from typing import Tuple
from jinja2 import Template


# Jinja template for formatting Todoist tasks
TODOIST_PROMPT_TEMPLATE = """{% for task in tasks %}
---
Task: {{ task.name }}
Priority: {{ task.priority }}{% if task.tags %}
Tags: {{ task.tags | join(', ') }}{% endif %}{% if task.description %}
Description: {{ task.description }}{% endif %}{% if task.due %}
Due: {{ task.due.strftime('%Y-%m-%d') }}{% endif %}{% if task.deadline %}
Deadline: {{ task.deadline.strftime('%Y-%m-%d') }}{% endif %}{% if task.completed_at %}
Completed: {{ task.completed_at.strftime('%Y-%m-%d') }}{% endif %}{% if task.created_at %}
Updated: {{ task.updated_at.strftime('%Y-%m-%d') }}{% endif %}{% endfor %}
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
                task_nodes.append(TodoistNode.from_api_response(task, projects))

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
                    TodoistNode.from_api_response(completed_task, projects)
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
                project_nodes.append(TodoistProject.from_api_response(project))

        print(f"Fetched {len(project_nodes)} projects")
        return project_nodes
    except Exception as e:
        print(f"Error fetching projects: {e}")
        return []


def update_tasks(
    existing_tasks: list[TodoistNode], new_tasks: list[TodoistNode]
) -> list[TodoistNode]:
    """
    Update existing tasks with new tasks, overwriting tasks with shared task IDs.

    Args:
        existing_tasks: List of existing TodoistNode tasks
        new_tasks: List of new TodoistNode tasks from API

    Returns:
        Updated list of tasks with new tasks overwriting existing ones with same IDs
    """
    # Create a dictionary of existing tasks by task_id for quick lookup
    existing_tasks_dict = {task.task_id: task for task in existing_tasks}

    # Update with new tasks, overwriting existing ones with same task_id
    for new_task in new_tasks:
        existing_tasks_dict[new_task.task_id] = new_task

    # Convert back to list
    updated_tasks = list(existing_tasks_dict.values())

    print(
        f"Updated tasks: {len(existing_tasks)} existing + {len(new_tasks)} new = {len(updated_tasks)} total"
    )
    return updated_tasks


def update_projects(
    existing_projects: list[TodoistProject], new_projects: list[TodoistProject]
) -> list[TodoistProject]:
    """
    Update existing projects with new projects, overwriting projects with shared project IDs.

    Args:
        existing_projects: List of existing TodoistProject projects
        new_projects: List of new TodoistProject projects from API

    Returns:
        Updated list of projects with new projects overwriting existing ones with same IDs
    """
    # Create a dictionary of existing projects by project_id for quick lookup
    existing_projects_dict = {
        project.project_id: project for project in existing_projects
    }

    # Update with new projects, overwriting existing ones with same project_id
    for new_project in new_projects:
        existing_projects_dict[new_project.project_id] = new_project

    # Convert back to list
    updated_projects = list(existing_projects_dict.values())

    print(
        f"Updated projects: {len(existing_projects)} existing + {len(new_projects)} new = {len(updated_projects)} total"
    )
    return updated_projects


def get_all_todoist_data(
    days_back: int = 7,
) -> Tuple[list[TodoistNode], list[TodoistNode], list[TodoistProject]]:
    """
    Get all Todoist data: active tasks, completed tasks from past N days, and all projects.

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


if __name__ == "__main__":
    # Test the functionality with different time ranges
    print("Testing with default 7 days:")
    active_tasks, completed_tasks, projects = get_all_todoist_data()

    print(f"\nSummary (7 days):")
    print(f"Active tasks: {len(active_tasks)}")
    print(f"Completed tasks (past 7 days): {len(completed_tasks)}")
    print(f"Projects: {len(projects)}")

    # Test with 30 days
    print("\n" + "=" * 50)
    print("Testing with 30 days:")
    active_tasks_30, completed_tasks_30, projects_30 = get_all_todoist_data(30)

    print(f"\nSummary (30 days):")
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
