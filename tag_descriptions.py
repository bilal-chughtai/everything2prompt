"""
Tag descriptions for the Everything2Prompt query system.

This file loads tag descriptions from a JSON file to provide context
to the model when using the query tool.
"""

import json
import os
from pathlib import Path


def load_tag_descriptions() -> dict:
    """
    Load tag descriptions from JSON file.

    Returns:
        Dictionary of tag descriptions organized by source
    """
    # Try to load custom tag descriptions first
    custom_path = Path("tag_descriptions.json")
    if custom_path.exists():
        with open(custom_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # Fall back to template if custom file doesn't exist
    template_path = Path("tag_descriptions_template.json")
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # If neither exists, return empty dict
    return {}


# Load tag descriptions on module import
TAG_DESCRIPTIONS = load_tag_descriptions()


def get_tag_description(source: str, tag: str) -> str:
    """
    Get the description for a specific tag in a specific source.

    Args:
        source: The data source (obsidian, todoist, instapaper, etc.)
        tag: The tag name

    Returns:
        Description of the tag, or "No description available" if not found
    """
    return TAG_DESCRIPTIONS.get(source, {}).get(tag, "No description available")


def get_all_tag_descriptions() -> dict:
    """
    Get all tag descriptions organized by source.

    Returns:
        Dictionary of all tag descriptions
    """
    return TAG_DESCRIPTIONS


def get_source_tag_descriptions(source: str) -> dict:
    """
    Get all tag descriptions for a specific source.

    Args:
        source: The data source (obsidian, todoist, instapaper, etc.)

    Returns:
        Dictionary of tag descriptions for the specified source
    """
    return TAG_DESCRIPTIONS.get(source, {})


def reload_tag_descriptions() -> dict:
    """
    Reload tag descriptions from JSON file.

    Returns:
        Updated dictionary of tag descriptions
    """
    global TAG_DESCRIPTIONS
    TAG_DESCRIPTIONS = load_tag_descriptions()
    return TAG_DESCRIPTIONS


if __name__ == "__main__":
    # Example usage
    print("Tag Descriptions:")
    for source, tags in TAG_DESCRIPTIONS.items():
        print(f"\n{source.upper()}:")
        for tag, description in tags.items():
            print(f"  {tag}: {description}")
