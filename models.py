import datetime
import pydantic
from typing import Literal
from todoist_api_python.models import Task


def strip_timezone(
    dt: datetime.datetime | datetime.date | None,
) -> datetime.datetime | datetime.date | None:
    """
    Remove timezone information from datetime objects to make them timezone-naive.
    Also handles date objects by converting them to datetime if needed.
    """
    if dt is None:
        return None

    # If it's a date object, convert to datetime
    if isinstance(dt, datetime.date) and not isinstance(dt, datetime.datetime):
        return datetime.datetime.combine(dt, datetime.time.min)

    # If it's a datetime object with timezone info, remove it
    if isinstance(dt, datetime.datetime) and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)

    return dt


class Node(pydantic.BaseModel):
    """
    Base class for all nodes, containing common mandatory fields.
    """

    data_source: str = pydantic.Field(description="Data source of the node")
    name: str = pydantic.Field(description="Name of the node")
    tags: list[str] = pydantic.Field(
        default_factory=list,
        description="Tags of the node",
    )
    date: datetime.datetime | None = pydantic.Field(description="Date of the node")


class ObsidianNode(Node):
    data_source: Literal["obsidian"] = "obsidian"
    absolute_path: str = pydantic.Field(
        description="Absolute path of the obsidian file"
    )
    markdown_content: str = pydantic.Field(description="Content of the obsidian file.")
    yaml_content: dict = pydantic.Field(
        description="YAML content of the obsidian file."
    )
    # TODO: add links

    def __str__(self) -> str:
        content_preview = (
            self.markdown_content[:20] + "..."
            if len(self.markdown_content) > 20
            else self.markdown_content
        )
        return f"ObsidianNode(name='{self.name}', tags={self.tags}, date={self.date}, absolute_path='{self.absolute_path}', markdown_content='{content_preview}')"


class TodoistProject(pydantic.BaseModel):
    """
    Represents a Todoist project with all its key data.
    """

    data_source: Literal["todoist"] = "todoist"
    project_id: str = pydantic.Field(
        description="Unique identifier for the Todoist project."
    )
    name: str = pydantic.Field(description="Name of the project.")

    @classmethod
    def from_api_response(cls, response) -> "TodoistProject":
        return cls(
            name=response.name,  # Set the name field
            project_id=response.id,
        )


class TodoistNode(Node):
    """
    Represents a Todoist task with all its key data.
    """

    data_source: Literal["todoist"] = "todoist"
    task_id: str = pydantic.Field(description="Unique identifier for the Todoist task.")
    content: str = pydantic.Field(description="Content of the task.")
    description: str | None = pydantic.Field(
        default=None, description="Additional description for the task."
    )
    project_id: str = pydantic.Field(description="Project ID this task belongs to.")
    parent_id: str | None = pydantic.Field(
        default=None, description="ID of the parent task if this is a subtask."
    )
    labels: list[str] = pydantic.Field(
        default_factory=list, description="Tags assigned to the task"
    )
    priority: int = pydantic.Field(
        default=1, description="Priority level of the task (1-4, where 4 is highest)"
    )
    due: datetime.datetime | None = pydantic.Field(
        default=None, description="Due date and time for the task"
    )
    deadline: datetime.datetime | None = pydantic.Field(
        default=None, description="Deadline for the task"
    )
    completed_at: datetime.datetime | None = pydantic.Field(
        default=None, description="When the task was completed"
    )
    created_at: datetime.datetime | None = pydantic.Field(
        default=None, description="When the task was created"
    )
    updated_at: datetime.datetime | None = pydantic.Field(
        default=None, description="When the task was last updated"
    )

    def __str__(self) -> str:
        content_preview = (
            self.content[:30] + "..." if len(self.content) > 30 else self.content
        )
        return f"TodoistNode(name='{self.name}', task_id='{self.task_id}', content='{content_preview}', priority={self.priority}, due={self.due})"

    @classmethod
    def from_api_response(
        cls, task: Task, projects: list[TodoistProject]
    ) -> "TodoistNode":
        return cls(
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
            date=strip_timezone(cls.get_canonical_date(task)),
            tags=cls.get_union_of_labels_and_project(task, projects),
        )

    @staticmethod
    def get_union_of_labels_and_project(
        task: Task, projects: list[TodoistProject]
    ) -> list[str]:
        """
        Get the union of the labels and the project name.
        """
        # For now, just return labels since we don't have project name
        # You'll need to pass project info separately or fetch it
        project_name = TodoistNode.get_project_name(task, projects)
        return task.labels + [project_name] if project_name else task.labels

    @staticmethod
    def get_canonical_date(task: Task) -> datetime.datetime | None:
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
        # if no date return None
        return None

    @staticmethod
    def get_project_name(task: Task, projects: list[TodoistProject]) -> str | None:
        """
        Get the project name of the task.
        """
        return next(
            (
                project.name
                for project in projects
                if project.project_id == task.project_id
            ),
            None,
        )

    @classmethod
    def from_api_response_with_project(
        cls, task: Task, project: TodoistProject
    ) -> "TodoistNode":
        """
        Create TodoistNode from task with project information for proper tag generation.
        """
        return cls(
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
            date=strip_timezone(cls.get_canonical_date(task)),
            tags=cls.get_union_of_labels_and_project_with_project(task, project),
        )

    @staticmethod
    def get_union_of_labels_and_project_with_project(
        task: Task, project: TodoistProject
    ) -> list[str]:
        """
        Get the union of the labels and the project name.
        """
        combined_tags = set(task.labels)
        if project and project.name:
            combined_tags.add(project.name)
        return list(combined_tags)


class InstapaperNode(Node):
    """
    Represents an Instapaper article with all its key data.
    """

    data_source: Literal["instapaper"] = "instapaper"
    url: str = pydantic.Field(description="URL of the article")
    title: str = pydantic.Field(description="Title of the article")
    folder: str = pydantic.Field(
        description="Folder the article is in (starred/unread)"
    )
    is_read: bool = pydantic.Field(description="Whether the article has been read")
    timestamp: int = pydantic.Field(
        description="Unix timestamp when the article was saved"
    )
    selection: str | None = pydantic.Field(
        default=None, description="Selected text from the article (ignored)"
    )

    def __str__(self) -> str:
        title_preview = self.title[:30] + "..." if len(self.title) > 30 else self.title
        return f"InstapaperNode(name='{self.name}', title='{title_preview}', url='{self.url}', is_read={self.is_read}, folder='{self.folder}')"

    @classmethod
    def from_csv_row(cls, row: dict) -> "InstapaperNode":
        """
        Create InstapaperNode from a CSV row.
        """
        # Parse tags from the tags field (assuming it's a string representation of a list)
        tags_str = row.get("Tags", "[]")
        try:
            # Remove brackets and split by comma, then strip whitespace
            tags = [
                tag.strip().strip("\"'")
                for tag in tags_str.strip("[]").split(",")
                if tag.strip()
            ]
        except:
            tags = []

        # Determine if the article is read based on folder
        folder = row.get("Folder", "").lower()
        is_read = folder == "starred"

        # Convert timestamp to datetime
        timestamp = int(row.get("Timestamp", 0))
        date = datetime.datetime.fromtimestamp(timestamp) if timestamp > 0 else None

        return cls(
            name=row.get("Title", ""),  # Use title as the name
            url=row.get("URL", ""),
            title=row.get("Title", ""),
            folder=row.get("Folder", ""),
            is_read=is_read,
            timestamp=timestamp,
            date=date,
            tags=tags,
            selection=row.get("Selection", None),
        )


class CalendarNode(Node):
    """
    Represents a calendar event with all its key data.
    """

    data_source: Literal["calendar"] = "calendar"
    event_id: str = pydantic.Field(
        description="Unique identifier for the calendar event"
    )
    description: str | None = pydantic.Field(
        default=None, description="Description of the event"
    )
    location: str | None = pydantic.Field(
        default=None, description="Location of the event"
    )
    start_time: datetime.datetime = pydantic.Field(
        description="Start time of the event"
    )
    end_time: datetime.datetime | None = pydantic.Field(
        default=None, description="End time of the event"
    )
    organizer: str | None = pydantic.Field(
        default=None, description="Organizer of the event"
    )
    status: str | None = pydantic.Field(
        default=None, description="Status of the event (CONFIRMED, TENTATIVE, etc.)"
    )
    created_at: datetime.datetime | None = pydantic.Field(
        default=None, description="When the event was created"
    )
    last_modified: datetime.datetime | None = pydantic.Field(
        default=None, description="When the event was last modified"
    )

    def __str__(self) -> str:
        name_preview = self.name[:30] + "..." if len(self.name) > 30 else self.name
        return f"CalendarNode(name='{name_preview}', start_time={self.start_time}, end_time={self.end_time})"

    @classmethod
    def from_ical_event(cls, event) -> "CalendarNode":
        """
        Create CalendarNode from an iCalendar event.
        """
        # Extract basic event data
        summary = str(event.get("summary", "")) if event.get("summary") else ""
        description = (
            str(event.get("description", "")) if event.get("description") else None
        )
        location = str(event.get("location", "")) if event.get("location") else None
        organizer = str(event.get("organizer", "")) if event.get("organizer") else None
        status = str(event.get("status", "")) if event.get("status") else None

        # Extract dates
        start_time = event.get("dtstart")
        end_time = event.get("dtend")
        created_at = event.get("created")
        last_modified = event.get("last-modified")

        # Convert to datetime objects and strip timezone
        start_dt = strip_timezone(start_time.dt if start_time else None)
        end_dt = strip_timezone(end_time.dt if end_time else None)
        created_dt = strip_timezone(created_at.dt if created_at else None)
        modified_dt = strip_timezone(last_modified.dt if last_modified else None)

        # Use start time as the canonical date
        date = start_dt

        # Generate tags from event properties
        tags = []
        if location:
            tags.append("location")
        if organizer:
            tags.append("organized")
        if status:
            tags.append(status.lower())

        return cls(
            name=summary,  # Use summary as the name
            event_id=str(event.get("uid", "")) if event.get("uid") else "",
            description=description,
            location=location,
            start_time=start_dt,
            end_time=end_dt,
            organizer=organizer,
            status=status,
            created_at=created_dt,
            last_modified=modified_dt,
            date=date,
            tags=tags,
        )


class Cache(pydantic.BaseModel):
    """
    All the data.
    """

    todoist_projects: list[TodoistProject] = pydantic.Field(
        default_factory=list, description="Projects of the TodoistNode."
    )
    todoist_tasks: list[TodoistNode] = pydantic.Field(
        default_factory=list, description="Tasks of the TodoistNode."
    )
    obsidian_notes: list[ObsidianNode] = pydantic.Field(
        default_factory=list, description="Notes of the TodoistNode."
    )
    instapaper_articles: list[InstapaperNode] = pydantic.Field(
        default_factory=list, description="Articles from Instapaper."
    )
    calendar_events: list[CalendarNode] = pydantic.Field(
        default_factory=list, description="Events from Calendar."
    )

    @classmethod
    def from_path(cls, path: str) -> "Cache":
        """
        Load the cache from the path.
        """
        with open(path, "r") as f:
            return cls.model_validate_json(f.read())

    def to_path(self, path: str) -> None:
        """
        Save the cache to the path.
        """
        with open(path, "w") as f:
            f.write(self.model_dump_json())
