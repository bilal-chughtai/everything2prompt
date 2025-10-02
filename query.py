from models import (
    ObsidianNode,
    TodoistNode,
    InstapaperNode,
    CalendarNode,
    HealthNode,
    Cache,
)
from obsidian import create_obsidian_prompt
from todoist import create_todoist_prompt
from instapaper import create_instapaper_prompt
from cal import create_calendar_prompt
from health import create_health_prompt
from cache import load_cache
from tag_descriptions import get_source_tag_descriptions
from typing import Callable
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from jinja2 import Template
import re
import functools

# Jinja template for formatting all data sources together
MASTER_PROMPT_TEMPLATE = """QUERY: "{{ query }}"
CURRENT DATE: {{ current_datetime }}
{% if obsidian_output %}
*** OBSIDIAN NOTES ***
{{ obsidian_output }}
{% endif %}{% if todoist_output %}
*** TODOIST TASKS ***
{{ todoist_output }}
{% endif %}{% if instapaper_output %}
*** INSTAPAPER ARTICLES ***
{{ instapaper_output }}
{% endif %}{% if calendar_output %}
*** CALENDAR EVENTS ***
{{ calendar_output }}
{% endif %}{% if health_output %}
*** HEALTH DATA ***
{{ health_output }}
{% endif %}
{% if not obsidian_output and not todoist_output and not instapaper_output and not calendar_output and not health_output %}
No results found for the given query.
{% endif %}"""


class Query(BaseModel):
    source: list[str] | None = Field(
        default=None,
        description="Sources of the data (e.g., ['obsidian', 'todoist', 'calendar'])",
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
        valid_sources = ["obsidian", "todoist", "instapaper", "calendar", "health"]
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
        valid_parameters = {"source", "tag", "from", "to"}
        unrecognized_parts = []

        for part in parts:
            if ":" in part:
                key, value = part.split(":", 1)

                if key in valid_parameters:
                    if key == "source":
                        source = [s.strip() for s in value.split(",")]
                    elif key == "tag":
                        tag = [t.strip() for t in value.split(",")]
                    elif key == "from":
                        from_date = value
                    elif key == "to":
                        to_date = value
                else:
                    unrecognized_parts.append(part)
            else:
                # Parts without colons are not valid parameters
                unrecognized_parts.append(part)

        # Check if there are any unrecognized parts
        if unrecognized_parts:
            raise ValueError(
                f"Invalid query format. Unrecognized parts: {unrecognized_parts}. "
                f"Valid parameters are: {', '.join(valid_parameters)}. "
                f"All parts must be in format 'parameter:value'"
            )

        # Create Query object with validation
        query_obj = cls(source=source, tag=tag, from_date=from_date, to_date=to_date)

        # If to_date is set, modify it to be 23:59:59 of that day
        if query_obj.to_date:
            query_obj.to_date = query_obj.to_date.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )

        return query_obj


@functools.cache
def get_all_nodes() -> list[
    ObsidianNode | TodoistNode | InstapaperNode | CalendarNode | HealthNode
]:
    """
    Loads all the nodes from cache.
    """
    cache = load_cache()

    # Concatenate all nodes from different sources
    all_nodes = []
    all_nodes.extend(cache.obsidian_notes)
    all_nodes.extend(cache.todoist_tasks)
    all_nodes.extend(cache.instapaper_articles)
    all_nodes.extend(cache.calendar_events)
    all_nodes.extend(cache.health_data)
    return all_nodes


def get_query_lambdas(
    query: Query,
) -> list[
    Callable[
        [ObsidianNode | TodoistNode | InstapaperNode | CalendarNode | HealthNode], bool
    ]
]:
    """
    Returns a list of lambda functions, one for each field in the query.
    """
    lambdas = []

    # Source filtering lambda
    if query.source is not None:

        def source_filter(
            node: ObsidianNode
            | TodoistNode
            | InstapaperNode
            | CalendarNode
            | HealthNode,
        ) -> bool:
            return node.data_source in query.source

        lambdas.append(source_filter)

    # Tag filtering lambda
    if query.tag is not None:

        def tag_filter(
            node: ObsidianNode
            | TodoistNode
            | InstapaperNode
            | CalendarNode
            | HealthNode,
        ) -> bool:
            return any(tag in node.tags for tag in query.tag)

        lambdas.append(tag_filter)

    # From date filtering lambda
    if query.from_date is not None:

        def from_date_filter(
            node: ObsidianNode
            | TodoistNode
            | InstapaperNode
            | CalendarNode
            | HealthNode,
        ) -> bool:
            return node.date is None or node.date >= query.from_date

        lambdas.append(from_date_filter)

    # To date filtering lambda
    if query.to_date is not None:

        def to_date_filter(
            node: ObsidianNode
            | TodoistNode
            | InstapaperNode
            | CalendarNode
            | HealthNode,
        ) -> bool:
            return node.date is None or node.date <= query.to_date

        lambdas.append(to_date_filter)

    return lambdas


def get_query_help() -> str:
    """
    Returns comprehensive help information about the query language.
    """
    # Get all nodes to extract available sources and tags
    all_nodes = get_all_nodes()

    # Extract unique sources
    sources = list(set(node.data_source for node in all_nodes))
    sources.sort()

    # Extract tags by source with counts
    tags_by_source = {}
    tag_counts = {}

    for node in all_nodes:
        if node.data_source not in tags_by_source:
            tags_by_source[node.data_source] = set()
        tags_by_source[node.data_source].update(node.tags)

        # Count occurrences of each tag
        for tag in node.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # Sort tags within each source by count (most common first)
    for source in tags_by_source:
        source_tags = list(tags_by_source[source])
        source_tags.sort(key=lambda tag: tag_counts.get(tag, 0), reverse=True)
        tags_by_source[source] = source_tags

    help_text = f"""# Everything2Prompt Query Language Guide

## Overview
The query language allows you to search across all your data sources (Obsidian notes, Todoist tasks, Instapaper articles, Calendar events, and Health data) using a simple text-based syntax. 

You should always pick the most relevant sources to query, and pick an appropriate date range, else the result may be too long.

## Query Format
```
source:source1,source2 tag:tag1,tag2 from:YYYY-MM-DD to:YYYY-MM-DD
```

Meaning: "Find all nodes in the date range that are in (source1 or source 2) AND have either (tag1 or tag2)

## Available Sources
{sources}

Make sure to only query these sources.

## Available Tags by Source
"""

    # Add tag information for each source
    for source in sources:
        if source in tags_by_source and tags_by_source[source]:
            # Get tag descriptions for this source
            tag_descriptions = get_source_tag_descriptions(source)

            # Format tags with descriptions
            tag_lines = []
            for tag in tags_by_source[source]:
                count = tag_counts.get(tag, 0)
                description = tag_descriptions.get(tag, "No description available")
                tag_lines.append(f"  - {tag}({count}): {description}")

            help_text += f"**{source.title()}**:\n" + "\n".join(tag_lines) + "\n\n"
        elif source == "calendar":
            help_text += (
                "**Calendar**: No tags available (calendar events are not tagged)\n\n"
            )
        elif source == "health":
            help_text += "**Health**: No tags available (health data is not tagged)\n\n"
        else:
            help_text += f"**{source.title()}**: No tags available\n\n"

    help_text += """**Note**: Using the more common tags will typically give you better search results with more relevant items.

## Query Parameters

### source
Filter by specific data sources. Multiple sources can be specified with commas.
- **Format**: `source:obsidian,todoist,instapaper,calendar`
- **Examples**:
  - `source:obsidian` - Search only Obsidian notes
  - `source:todoist,calendar` - Search Todoist tasks and Calendar events

### tag
Filter by tags. Multiple tags can be specified with commas.
- **Format**: `tag:tag1,tag2,tag3`
- **Examples**:
  - `tag:health` - Find all items tagged with "health"
  - `tag:work,project` - Find items tagged with either "work" or "project"

### from_date
Filter items from a specific start date onwards.
- **Format**: `from:YYYY-MM-DD`
- **Examples**:
  - `from:2025-01-01` - Find items from January 1, 2025 onwards

### to_date
Filter items up to a specific end date.
- **Format**: `to:YYYY-MM-DD`
- **Examples**:
  - `to:2025-12-31` - Find items up to December 31, 2025

Do NOT write queries without parameters.

## Example Queries

1. **Find all health-related items**:
   ```
   tag:health
   ```

2. **Find work-related Obsidian notes**:
   ```
   source:obsidian tag:work
   ```

3. **Find Todoist tasks and Calendar events from 2025**:
   ```
   source:todoist,calendar from:2025-01-01 to:2025-12-31
   ```

4. **Find project-related items across all sources**:
   ```
   tag:project
   ```

5. **Find all items from the last month**:
   ```
   from:2025-01-01 to:2025-01-31
   ```

## Tips
- Parameters can be combined in any order
- If no source is specified, all sources are searched
- If no tag is specified, all tags are included
- If no date range is specified, all dates are included
- Results are sorted by date (most recent first)
- Items without dates appear at the end of results
- Parameters are necessary. e.g. query "birthday" is invalid.

## Data Sources

- **Obsidian**: Personal notes and knowledge base
- **Todoist**: Task management and to-do items
- **Instapaper**: Saved articles and reading list
- **Calendar**: Scheduled events and appointments
- **Health**: Health metrics and fitness data from CSV files
"""

    return help_text


def run(query_string: str) -> str:
    """
    Loads all the nodes from cache, runs a query, and returns a prompt.
    """
    # Parse the query string
    query = Query.from_string(query_string)

    # Get all nodes from cache
    all_nodes = get_all_nodes()

    # Get filtering lambdas
    filter_lambdas = get_query_lambdas(query)

    # Apply all filters sequentially
    filtered_nodes = all_nodes
    for filter_func in filter_lambdas:
        filtered_nodes = [node for node in filtered_nodes if filter_func(node)]

    # Sort by date (most recent first)
    filtered_nodes.sort(key=lambda x: (x.date is None, x.date), reverse=True)

    # Separate nodes by type
    obsidian_nodes = [node for node in filtered_nodes if isinstance(node, ObsidianNode)]
    todoist_nodes = [node for node in filtered_nodes if isinstance(node, TodoistNode)]
    instapaper_nodes = [
        node for node in filtered_nodes if isinstance(node, InstapaperNode)
    ]
    calendar_nodes = [node for node in filtered_nodes if isinstance(node, CalendarNode)]
    health_nodes = [node for node in filtered_nodes if isinstance(node, HealthNode)]

    obsidian_output = create_obsidian_prompt(obsidian_nodes) if obsidian_nodes else ""
    todoist_output = create_todoist_prompt(todoist_nodes) if todoist_nodes else ""
    instapaper_output = (
        create_instapaper_prompt(instapaper_nodes) if instapaper_nodes else ""
    )
    calendar_output = create_calendar_prompt(calendar_nodes) if calendar_nodes else ""
    health_output = create_health_prompt(health_nodes) if health_nodes else ""

    # Create formatted prompt using the master template
    template = Template(MASTER_PROMPT_TEMPLATE)
    prompt = template.render(
        query=query_string,
        obsidian_output=obsidian_output,
        todoist_output=todoist_output,
        instapaper_output=instapaper_output,
        calendar_output=calendar_output,
        health_output=health_output,
        current_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    return prompt


if __name__ == "__main__":
    import sys
    import logging

    # Configure logging to write to stderr instead of stdout
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    if len(sys.argv) < 2:
        logging.info(
            "Usage: python query.py 'source:obsidian tag:health from:2025-01-01 to:2025-12-31'"
        )
        logging.info("Example queries:")
        logging.info("  python query.py 'tag:health'")
        logging.info("  python query.py 'source:obsidian tag:work,project'")
        logging.info("  python query.py 'from:2025-01-01 to:2025-12-31'")
        sys.exit(1)

    query_string = sys.argv[1]

    try:
        out = run(query_string)
        logging.info(out)
    except Exception as e:
        logging.error(f"Error: {e}")
        sys.exit(1)
