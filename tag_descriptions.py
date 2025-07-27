"""
Tag descriptions for the Everything2Prompt query system.

This file contains descriptions for all tags across different data sources
to provide context to the model when using the query tool.
"""

TAG_DESCRIPTIONS = {
    # Instapaper tags
    "instapaper": {
        "ai": "Articles about artificial intelligence, machine learning, and AI-related topics",
        "fiction": "Fictional stories, novels, and creative writing",
        "work": "Work-related articles, career advice, and professional development",
        "other": "Miscellaneous articles that don't fit other categories",
        "optimisation": "Articles about productivity, efficiency, and optimization",
        "people": "Articles about people, biographies, and human stories",
        "health": "Health, fitness, and wellness articles",
        "careers": "Career development, job hunting, and professional growth",
        "research": "Research papers, academic articles, and scientific studies",
        "ea": "Effective altruism and related topics",
        "favourites": "Favorite articles",
        "science": "Scientific articles and discoveries",
        "money": "Financial articles, investing, and money management",
        "odyssey": "A reading group I attended.",
        "interp": "Interpretability, my main research field.",
        "rationality": "Lesswrong style rationality.",
        "coding": "Programming, software development, and technical articles",
        "*": "Things I should really read soon",
    },
    # Obsidian tags
    "obsidian": {
        "ai": "Notes about artificial intelligence, machine learning, and AI research",
        "projects": "Project notes, planning, and documentation",
        "other": "Miscellaneous notes that don't fit other categories",
        "admin": "Administrative tasks, organization, and management notes",
        "journal": "Personal journal entries and reflections",
        "people": "Notes about people, relationships, and social connections",
        "health": "Health, fitness, and wellness notes",
        "career": "Career-related notes, job search, and professional development",
        "external": "Things I have written for other people",
        "finances": "Financial planning, budgeting, and money management",
        "interview_prep": "Interview preparation, questions, and strategies",
        "meeting": "Meeting notes, agendas, and follow-ups",
        "relationships": "Personal relationships and social notes",
        "blog": "My personal blog posts",
        "temp": "Temporary or draft notes",
        "bluedot": "Notes relating to that time I worked at BlueDot Impact for a month",
        "deception_detection": "Notes about a deception detection AI safety project I wroked on",
        "content/youtube": "YouTube content notes and summaries",
        "content/papers": "Academic paper summaries and notes",
        "content/books": "Book summaries, reviews, and notes",
        "events": "Event notes, planning, and memories",
        "ethan_mats": "Notes related to Ethan Mats or specific person",
        "apollo": "Notes related to the Apollo project or initiative",
        "content/talks": "Talk and presentation notes",
        "content/blogs": "Blog post notes and summaries",
        "phd": "PhD-related notes, research, and academic work",
        "content/courses": "Course notes and educational content",
        "content/advice": "Advice and guidance notes",
        "travel": "Travel planning and experiences",
        "sad": "Notes about the Situational Awareness Dataset project for AIs.",
        "mars": "A AI safety mentorship program I mentored for.",
        "finances journal": "Do not use",
        "content/papers ai": "Do not use",
        "recipe": "Recipes I like",
        "content/talks ai": "Do not use",
    },
    # Todoist tags
    "todoist": {
        "Inbox": "Default tasks without specific categorization",
        "work": "Work-related tasks and professional responsibilities",
        "projects": "Personal projects I am working on",
        "other": "Do not use",
        "admin": "Administrative tasks and organizational work",
        "people": "Tasks related to people, meetings, and social obligations",
        "health": "Health and fitness related tasks",
        "soon": "Tasks that need to be done soon or are high priority",
        "finances": "Financial tasks, bill payments, and money management",
        "demo": "Do not use",
        "some_tag": "Do not use",
    },
}


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


if __name__ == "__main__":
    # Example usage
    print("Tag Descriptions:")
    for source, tags in TAG_DESCRIPTIONS.items():
        print(f"\n{source.upper()}:")
        for tag, description in tags.items():
            print(f"  {tag}: {description}")
