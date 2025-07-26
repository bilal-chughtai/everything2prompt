from models import ObsidianNode
import obsidian
from typing import Callable
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from jinja2 import Template
import re

# Jinja template for formatting all data sources together
MASTER_PROMPT_TEMPLATE = """QUERY: "{{ query }}"

{{ obsidian_output }}

{% if not obsidian_output %}
No results found for the given query.
{% endif %}
"""


class Query(BaseModel):
    source: list[str] | None = Field(
        default=None, description="Sources of the data (e.g., ['obsidian', 'todoist'])"
    )
    tag: list[str] | None = Field(default=None, description="Tags to filter by")
    from_date: datetime | None = Field(
        default=None, description="Start date for filtering"
    )
    to_date: datetime | None = Field(default=None, description="End date for filtering")

    @field_validator("source")
    @classmethod
    def validate_source(cls, v):
        if v is None:
            return v
        valid_sources = ["obsidian", "todoist"]
        for source in v:
            if source not in valid_sources:
                raise ValueError(f"Source must be one of {valid_sources}")
        return v

    @field_validator("from_date", "to_date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if v is None or isinstance(v, datetime):
            return v
        try:
            return datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")

    @field_validator("to_date")
    @classmethod
    def validate_date_order(cls, v, info):
        if v is not None and info.data and info.data.get("from_date") is not None:
            if info.data["from_date"] > v:
                raise ValueError("from_date must be before or equal to to_date")
        return v

    @classmethod
    def from_string(cls, query_string: str) -> "Query":
        """
        Parse a query string like 'source:obsidian,todoist tag:health,work from:2025-01-01 to:2025-12-31'
        """
        # Initialize default values
        source = None
        tag = None
        from_date = None
        to_date = None

        # Parse the query string
        parts = query_string.split()

        for part in parts:
            if ":" in part:
                key, value = part.split(":", 1)

                if key == "source":
                    source = [s.strip() for s in value.split(",")]
                elif key == "tag":
                    tag = [t.strip() for t in value.split(",")]
                elif key == "from":
                    from_date = value
                elif key == "to":
                    to_date = value

        # Create Query object with validation
        return cls(source=source, tag=tag, from_date=from_date, to_date=to_date)


def get_all_nodes() -> list[ObsidianNode]:
    """
    Loads all the nodes.
    """
    return obsidian.get_all_nodes(obsidian.OBSIDIAN_PATH)


def get_query_lambdas(query: Query) -> list[Callable[[ObsidianNode], bool]]:
    """
    Returns a list of lambda functions, one for each field in the query.
    """
    lambdas = []

    # Source filtering lambda
    if query.source is not None:

        def source_filter(node: ObsidianNode) -> bool:
            return "obsidian" in query.source

        lambdas.append(source_filter)

    # Tag filtering lambda
    if query.tag is not None:

        def tag_filter(node: ObsidianNode) -> bool:
            return any(tag in node.tags for tag in query.tag)

        lambdas.append(tag_filter)

    # From date filtering lambda
    if query.from_date is not None:

        def from_date_filter(node: ObsidianNode) -> bool:
            return node.date is None or node.date >= query.from_date

        lambdas.append(from_date_filter)

    # To date filtering lambda
    if query.to_date is not None:

        def to_date_filter(node: ObsidianNode) -> bool:
            return node.date is None or node.date <= query.to_date

        lambdas.append(to_date_filter)

    return lambdas


def run(query_string: str) -> str:
    """
    Loads all the nodes, runs a query, and returns a prompt.
    """
    # Parse the query string
    query = Query.from_string(query_string)

    # Get all nodes from different sources
    all_nodes = get_all_nodes()

    # Get filtering lambdas
    filter_lambdas = get_query_lambdas(query)

    # Apply all filters sequentially
    filtered_nodes = all_nodes
    for filter_func in filter_lambdas:
        filtered_nodes = [node for node in filtered_nodes if filter_func(node)]

    # Sort by date (most recent first)
    filtered_nodes.sort(key=lambda x: (x.date is None, x.date), reverse=True)

    # Get formatted output from each source
    obsidian_output = (
        obsidian.create_obsidian_prompt(filtered_nodes) if filtered_nodes else ""
    )

    # Create formatted prompt using the master template
    template = Template(MASTER_PROMPT_TEMPLATE)
    prompt = template.render(
        query=query_string,
        obsidian_output=obsidian_output,
    )

    return prompt


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python query.py 'source:obsidian tag:health from:2025-01-01 to:2025-12-31'"
        )
        print("Example queries:")
        print("  python query.py 'tag:health'")
        print("  python query.py 'source:obsidian tag:work,project'")
        print("  python query.py 'from:2025-01-01 to:2025-12-31'")
        sys.exit(1)

    query_string = sys.argv[1]

    try:
        out = run(query_string)
        print(out)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
