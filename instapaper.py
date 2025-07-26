import csv
import os
from pathlib import Path
from typing import List
from models import InstapaperNode
from jinja2 import Template

# Path to the Instapaper CSV file
INSTAPAPER_CSV_PATH = "/Users/bilal/Code/everything2prompt/instapaper.csv"


# Jinja template for formatting Instapaper articles
INSTAPAPER_PROMPT_TEMPLATE = """{% for article in articles %}
---
Title: {{ article.title }}
URL: {{ article.url }}{% if article.tags %}
Tags: {{ article.tags | join(', ') }}{% endif %}{% if article.date %}
Date: {{ article.date.strftime('%Y-%m-%d') }}{% endif %}
Read: {{ article.is_read }}{% endfor %}
"""


def create_instapaper_prompt(articles: List[InstapaperNode]) -> str:
    """
    Create a formatted prompt from a list of Instapaper articles.
    """
    template = Template(INSTAPAPER_PROMPT_TEMPLATE)
    return template.render(articles=articles)


def get_all_articles() -> List[InstapaperNode]:
    """
    Parse the Instapaper CSV file and return all articles as InstapaperNode objects.

    Returns:
        List of InstapaperNode objects representing all articles in the CSV
    """
    articles = []

    if not os.path.exists(INSTAPAPER_CSV_PATH):
        print(f"Instapaper CSV file not found at {INSTAPAPER_CSV_PATH}")
        return articles

    try:
        with open(INSTAPAPER_CSV_PATH, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                try:
                    article = InstapaperNode.from_csv_row(row)
                    articles.append(article)
                except Exception as e:
                    print(f"Error parsing row {row}: {e}")
                    continue

        print(f"Successfully parsed {len(articles)} articles from Instapaper CSV")

    except Exception as e:
        print(f"Error reading Instapaper CSV file: {e}")

    return articles


def get_articles_by_folder(folder: str) -> List[InstapaperNode]:
    """
    Get articles from a specific folder (starred or unread).

    Args:
        folder: The folder to filter by ("starred" or "unread")

    Returns:
        List of InstapaperNode objects from the specified folder
    """
    all_articles = get_all_articles()
    folder_lower = folder.lower()

    return [
        article for article in all_articles if article.folder.lower() == folder_lower
    ]


def get_read_articles() -> List[InstapaperNode]:
    """
    Get all articles that have been read (starred).

    Returns:
        List of InstapaperNode objects that are marked as read
    """
    all_articles = get_all_articles()
    return [article for article in all_articles if article.is_read]


def get_unread_articles() -> List[InstapaperNode]:
    """
    Get all articles that haven't been read yet (unread).

    Returns:
        List of InstapaperNode objects that are marked as unread
    """
    all_articles = get_all_articles()
    return [article for article in all_articles if not article.is_read]


if __name__ == "__main__":
    # Test the functionality
    articles = get_all_articles()
    print(f"Total articles: {len(articles)}")

    read_articles = get_read_articles()
    print(f"Read articles: {len(read_articles)}")

    unread_articles = get_unread_articles()
    print(f"Unread articles: {len(unread_articles)}")

    # Print first few articles as examples
    for i, article in enumerate(articles[:3]):
        print(f"\nArticle {i + 1}:")
        print(f"  Title: {article.title}")
        print(f"  URL: {article.url}")
        print(f"  Folder: {article.folder}")
        print(f"  Is Read: {article.is_read}")
        print(f"  Tags: {article.tags}")
        print(f"  Date: {article.date}")
