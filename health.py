import csv
import os
from datetime import datetime
from pathlib import Path
from typing import List
from jinja2 import Template
from models import HealthNode

HEALTH_CSV_PATH = "/Users/bilal/code/health_dashboard/data/health_data.csv"

HEALTH_PROMPT_TEMPLATE = """{% for entry in entries %}---
Date: {{ entry.date.strftime('%Y-%m-%d') }}{% for key, value in entry.health_metrics.items() %}
{{ key.replace('__', ' - ').replace('_', ' ').title() }}: {% if value is number %}{{ "%.2f"|format(value) }}{% else %}{{ value }}{% endif %}{% endfor %}
{% endfor %}
"""


def create_health_prompt(health_nodes: List[HealthNode]) -> str:
    """
    Create a formatted prompt from health nodes using Jinja template.

    Args:
        health_nodes: List of HealthNode objects

    Returns:
        Formatted string representation of health data
    """
    if not health_nodes:
        return ""

    # Sort by date (most recent first)
    health_nodes.sort(key=lambda x: x.date, reverse=True)

    # Use Jinja template to format the data
    template = Template(HEALTH_PROMPT_TEMPLATE)

    return template.render(entries=health_nodes)


def get_all_health_data() -> List[HealthNode]:
    """
    Read all health data from the configured CSV file.

    Returns:
        List of HealthNode objects, one for each day with data
    """
    health_nodes = []
    csv_path = Path(HEALTH_CSV_PATH)

    if not csv_path.exists():
        print(f"Health data file not found: {HEALTH_CSV_PATH}")
        return health_nodes

    print(f"Reading health data from: {csv_path}")

    try:
        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                try:
                    # Parse the date
                    date_str = row.get("date", "").strip()
                    if not date_str:
                        continue

                    # Try different date formats
                    date = None
                    for date_format in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]:
                        try:
                            date = datetime.strptime(date_str, date_format)
                            break
                        except ValueError:
                            continue

                    if date is None:
                        print(f"Could not parse date: {date_str}")
                        continue

                    # Extract health metrics
                    health_data = {}
                    for key, value in row.items():
                        if key == "date":
                            continue

                        # Skip empty values
                        if not value or value.strip() == "":
                            continue

                        # Try to convert to appropriate type
                        try:
                            # Try float first
                            float_val = float(value)
                            # If it's a whole number, store as int
                            if float_val.is_integer():
                                health_data[key] = int(float_val)
                            else:
                                health_data[key] = float_val
                        except ValueError:
                            # If not a number, store as string
                            health_data[key] = value.strip()

                    # Create the health node
                    health_node = HealthNode(
                        name=f"Health Data - {date.strftime('%Y-%m-%d')}",
                        date=date,
                        tags=[],
                        health_metrics=health_data,
                    )

                    health_nodes.append(health_node)

                except Exception as e:
                    print(f"Error processing row: {row}, Error: {e}")
                    continue

    except Exception as e:
        print(f"Error reading CSV file {csv_path}: {e}")

    print(f"Loaded {len(health_nodes)} health data entries")
    return health_nodes


def create_health_prompt(health_nodes: List[HealthNode]) -> str:
    """
    Create a formatted prompt from health nodes using Jinja template.

    Args:
        health_nodes: List of HealthNode objects

    Returns:
        Formatted string representation of health data
    """
    if not health_nodes:
        return ""

    # Sort by date (most recent first)
    health_nodes.sort(key=lambda x: x.date, reverse=True)

    # Use Jinja template to format the data
    template = Template(HEALTH_PROMPT_TEMPLATE)

    return template.render(entries=health_nodes)
