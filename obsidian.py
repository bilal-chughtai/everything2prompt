import os
import re
import yaml
from datetime import datetime
from pathlib import Path
from typing import Tuple
from jinja2 import Template
from models import ObsidianNode

OBSIDIAN_PATH = "/Users/bilal/obsidian/bilal-obsidian"

# Jinja template for formatting Obsidian notes
OBSIDIAN_PROMPT_TEMPLATE = """{% for note in notes %}
---
Note: {{ note.name }}{% if note.tags %}
Tags: {{ note.tags | join(', ') }}{% endif %}{% if note.date %}
Date: {{ note.date.strftime('%Y-%m-%d') }}{% endif %}
Content: {{ note.markdown_content }}{% endfor %}
"""


def create_obsidian_prompt(notes: list[ObsidianNode]) -> str:
    """
    Create a formatted prompt from a list of Obsidian nodes.
    Notes are sorted by date (most recent first).
    """
    # Sort notes by date (most recent first, None dates at the end)
    sorted_notes = sorted(notes, key=lambda x: (x.date is None, x.date), reverse=True)

    # Render the template
    template = Template(OBSIDIAN_PROMPT_TEMPLATE)
    return template.render(notes=sorted_notes)


def split_yaml_and_content(content: str) -> Tuple[dict, str]:
    """
    Split YAML frontmatter from markdown content.
    Returns (yaml_data, markdown_content)
    """
    # Pattern to match YAML frontmatter between --- markers
    yaml_pattern = r"^---\s*\n(.*?)\n---\s*\n"
    match = re.match(yaml_pattern, content, re.DOTALL)

    if match:
        yaml_content = match.group(1)
        markdown_content = content[match.end() :]
        yaml_data = yaml.safe_load(yaml_content) or {}
        return yaml_data, markdown_content
    else:
        return {}, content


def extract_date_from_filename(filename: str) -> datetime | None:
    """
    Extract date from filename if it matches YYYY-MM-DD format.
    """
    import re

    date_pattern = r"^(\d{4}-\d{2}-\d{2})$"
    match = re.match(date_pattern, filename)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y-%m-%d")
        except ValueError:
            return None
    return None


def parse_yaml_metadata(
    yaml_data: dict, filename: str
) -> Tuple[list[str], datetime | None]:
    """
    Parse YAML metadata to extract tags and date.
    Returns (tags, date)
    """
    # Extract tags from YAML
    tags = yaml_data.get("tags", [])
    if isinstance(tags, str):
        # Split space-separated tags
        tags = tags.split()
    elif isinstance(tags, list):
        # Keep as is if it's already a list
        tags = tags
    else:
        # Fallback to empty list
        tags = []

    # Extract date from YAML
    date_obj = yaml_data.get("date")

    if hasattr(date_obj, "date") and not hasattr(date_obj, "hour"):
        # Convert date to datetime
        date_obj = datetime.combine(date_obj, datetime.min.time())

    # If no date in YAML, try to extract from filename
    if date_obj is None:
        date_obj = extract_date_from_filename(filename)

    return tags, date_obj


def is_template_content(content: str, yaml_data: dict) -> bool:
    """
    Check if content contains Templater syntax before creating ObsidianNode.
    """
    return any(
        [
            "<%tp." in content,
            "tp.file.cursor()" in content,
            "<%tp" in str(yaml_data),
            "tp.file.cursor()" in str(yaml_data),
        ]
    )


def get_obsidian_file_by_path(path: str) -> ObsidianNode | None:
    """
    Get an obsidian file by its path. Returns None if it's a template file.
    """
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Get file name without extension
    file_name = Path(path).stem

    # Split YAML and content
    yaml_data, markdown_content = split_yaml_and_content(content)

    # Check if this is a template file before processing
    if is_template_content(content, yaml_data):
        return None

    # Parse YAML metadata
    tags, date_obj = parse_yaml_metadata(yaml_data, file_name)

    return ObsidianNode(
        name=file_name,
        tags=tags,
        date=date_obj,
        absolute_path=os.path.abspath(path),
        markdown_content=markdown_content,
        yaml_content=yaml_data,
    )


def is_template_file(node: ObsidianNode) -> bool:
    """
    Check if a file is a template file by looking for Templater syntax.
    """
    if any(
        [
            "<%tp." in node.markdown_content,
            "tp.file.cursor()" in node.markdown_content,
            "<%tp" in node.yaml_content,
            "tp.file.cursor()" in node.yaml_content,
        ]
    ):
        return True
    return False


def is_date_none(node: ObsidianNode) -> bool:
    return node.date is None


def filter_obsidian_nodes(nodes: list[ObsidianNode]) -> list[ObsidianNode]:
    """
    Filter out template files and nodes with no date.
    """
    filtered_nodes = []
    for node in nodes:
        if is_template_file(node):
            continue
        if is_date_none(node):
            continue
        filtered_nodes.append(node)
    return filtered_nodes


def get_all_nodes(path: str) -> list[ObsidianNode]:
    """
    Get all obsidian files in the given path.
    """
    obsidian_nodes = []

    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                try:
                    obsidian_node = get_obsidian_file_by_path(file_path)
                    if obsidian_node is not None:  # Only add non-template files
                        obsidian_nodes.append(obsidian_node)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    continue

    return filter_obsidian_nodes(obsidian_nodes)


if __name__ == "__main__":
    obsidian_files = get_all_nodes(OBSIDIAN_PATH)

    if obsidian_files:
        # Filter for notes with 'health' tag
        health_notes = [note for note in obsidian_files if "health" in note.tags]

        print(f"Found {len(obsidian_files)} total Obsidian files")
        print(f"Found {len(health_notes)} notes with 'health' tag")
        print(f"Showing first 5 health notes:")
        print("=" * 50)

        # Create and print the formatted prompt
        prompt = create_obsidian_prompt(health_notes[:1])
        print(prompt)
    else:
        print("No obsidian files found in the specified path.")
