# %%
# autoreload
%load_ext autoreload
%autoreload 2

# %%
from datetime import datetime, timedelta
from todoist_api_python.api import TodoistAPI
import os
from dotenv import load_dotenv
from models import TodoistNode, TodoistProject
import zoneinfo

# Load environment variables from .env file
load_dotenv()

# Initialize Todoist API client
TODOIST_TOKEN = os.getenv("TODOIST_ACCESS_TOKEN")
api = TodoistAPI(TODOIST_TOKEN) if TODOIST_TOKEN else None


# %%
tasks_paginator = api.get_tasks()
task_nodes = []
for task_page in tasks_paginator:
    for task in task_page:
        print(task)
        task_nodes.append(TodoistNode.from_api_response(task))
        print(task_nodes[-1])

# %%
print(len(task_nodes))
# %%
completed_tasks_paginator = api.get_completed_tasks_by_completion_date(
    since=datetime.now() - timedelta(days=30),
    until=datetime.now(),
)
completed_task_nodes = []
for task_page in completed_tasks_paginator:
    for completed_task in task_page:
        completed_task_nodes.append(TodoistNode.from_api_response(completed_task))
        print(completed_task_nodes[-1])
# %%
print(len(completed_task_nodes))
# %%
project_paginator = api.get_projects()
project_nodes = []
for project_page in project_paginator:
    for project in project_page:
        project_nodes.append(TodoistProject.from_api_response(project))
        print(project_nodes[-1])

# %%
print(len(project_nodes))
# %%
