import requests
import os
from typing import List
from icalendar import Calendar
from models import CalendarNode
from dotenv import load_dotenv
from jinja2 import Template

# Load environment variables
load_dotenv()

# Get the Google Calendar iCal URL from environment
GCAL_ICAL_URL = os.getenv("SECRET_GCAL_ICAL")

CALENDAR_PROMPT_TEMPLATE = """{% for event in events %}
---
Event: {{ event.name }}{% if event.description %}
Description: {{ event.description }}{% endif %}{% if event.location %}
Location: {{ event.location }}{% endif %}{% if event.start_time %}
Date: {{ event.start_time.strftime('%Y-%m-%d') }}
Start Time: {{ event.start_time.strftime('%H:%M') }}{% endif %}{% if event.end_time %}
End Time: {{ event.end_time.strftime('%H:%M') }}{% endif %}{% if event.organizer %}
Organizer: {{ event.organizer }}{% endif %}{% endfor %}
"""


def create_calendar_prompt(events: List[CalendarNode]) -> str:
    """
    Create a formatted prompt from a list of CalendarNode objects.
    """
    template = Template(CALENDAR_PROMPT_TEMPLATE)
    return template.render(events=events)


def get_all_events() -> List[CalendarNode]:
    """
    Fetch all calendar events from the Google Calendar iCal feed.

    Returns:
        List of CalendarNode objects representing all calendar events
    """
    events = []

    if not GCAL_ICAL_URL:
        print("Google Calendar iCal URL not found in environment variables")
        return events

    try:
        # Fetch the iCal feed
        response = requests.get(GCAL_ICAL_URL)
        response.raise_for_status()

        # Parse the iCal data
        cal = Calendar.from_ical(response.content)

        # Extract all VEVENT components
        for event in cal.walk("vevent"):
            try:
                try:
                    calendar_node = CalendarNode.from_ical_event(event)
                    events.append(calendar_node)
                except Exception as e:
                    print(f"Error parsing event {event.get('uid', 'unknown')}: {e}")
                    print(event)
                    continue
            except Exception as e:
                print(f"Error parsing event {event.get('uid', 'unknown')}: {e}")
                continue

        print(f"Successfully parsed {len(events)} calendar events")

    except requests.RequestException as e:
        print(f"Error fetching calendar data: {e}")
    except Exception as e:
        print(f"Error parsing calendar data: {e}")

    return events


def get_events_by_date_range(start_date, end_date) -> List[CalendarNode]:
    """
    Get events within a specific date range.

    Args:
        start_date: Start date for filtering
        end_date: End date for filtering

    Returns:
        List of CalendarNode objects within the date range
    """
    all_events = get_all_events()

    return [
        event
        for event in all_events
        if event.start_time
        and event.start_time >= start_date
        and event.start_time <= end_date
    ]


def get_upcoming_events(days_ahead: int = 7) -> List[CalendarNode]:
    """
    Get events in the next N days.

    Args:
        days_ahead: Number of days to look ahead (default: 7)

    Returns:
        List of CalendarNode objects for upcoming events
    """
    from datetime import datetime, timedelta

    now = datetime.now()
    future_date = now + timedelta(days=days_ahead)

    all_events = get_all_events()

    return [
        event
        for event in all_events
        if event.start_time
        and event.start_time >= now
        and event.start_time <= future_date
    ]


def get_past_events(days_back: int = 7) -> List[CalendarNode]:
    """
    Get events from the past N days.

    Args:
        days_back: Number of days to look back (default: 7)

    Returns:
        List of CalendarNode objects for past events
    """
    from datetime import datetime, timedelta

    now = datetime.now()
    past_date = now - timedelta(days=days_back)

    all_events = get_all_events()

    return [
        event
        for event in all_events
        if event.start_time
        and event.start_time >= past_date
        and event.start_time <= now
    ]


if __name__ == "__main__":
    # Test the functionality
    events = get_all_events()
    print(f"Total events: {len(events)}")

    upcoming = get_upcoming_events(7)
    print(f"Upcoming events (next 7 days): {len(upcoming)}")

    past = get_past_events(7)
    print(f"Past events (last 7 days): {len(past)}")

    # Print first few events as examples
    for i, event in enumerate(events[:3]):
        print(f"\nEvent {i + 1}:")
        print(f"  Name: {event.name}")
        print(f"  Start: {event.start_time}")
        print(f"  End: {event.end_time}")
        print(f"  Location: {event.location}")
        print(f"  Tags: {event.tags}")
