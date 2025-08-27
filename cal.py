import requests
import os
from typing import List, Dict
from icalendar import Calendar
from models import CalendarNode
from dotenv import load_dotenv
from jinja2 import Template

# Load environment variables
load_dotenv()

# Get multiple Google Calendar iCal URLs from environment
# Expected format: CALENDAR_<NAME>=<ICAL_URL>
# Example: CALENDAR_WORK=https://...&CALENDAR_PERSONAL=https://...
CALENDAR_URLS = {}
for key, value in os.environ.items():
    if key.startswith("CALENDAR_") and key != "CALENDAR_":
        calendar_name = key[9:]  # Remove "CALENDAR_" prefix
        CALENDAR_URLS[calendar_name] = value

# Fallback to old format for backward compatibility
if not CALENDAR_URLS and os.getenv("SECRET_GCAL_ICAL"):
    CALENDAR_URLS["default"] = os.getenv("SECRET_GCAL_ICAL")

CALENDAR_PROMPT_TEMPLATE = """{% for event in events %}
---
Event: {{ event.name }}{% if event.description %}
Description: {{ event.description }}{% endif %}{% if event.location %}
Location: {{ event.location }}{% endif %}{% if event.start_time %}
Date: {{ event.start_time.strftime('%Y-%m-%d') }}
Start Time: {{ event.start_time.strftime('%H:%M') }}{% endif %}{% if event.end_time %}
End Time: {{ event.end_time.strftime('%H:%M') }}{% endif %}{% if event.organizer %}
Organizer: {{ event.organizer }}{% endif %}{% if event.calendar_name %}
Calendar: {{ event.calendar_name }}{% endif %}{% endfor %}
"""


def create_calendar_prompt(events: List[CalendarNode]) -> str:
    """
    Create a formatted prompt from a list of CalendarNode objects.
    """
    template = Template(CALENDAR_PROMPT_TEMPLATE)
    return template.render(events=events)


def get_events_from_calendar(
    calendar_name: str, calendar_url: str
) -> List[CalendarNode]:
    """
    Fetch events from a specific calendar by URL.

    Args:
        calendar_name: Name of the calendar
        calendar_url: iCal URL for the calendar

    Returns:
        List of CalendarNode objects from this calendar
    """
    events = []

    try:
        # Fetch the iCal feed
        response = requests.get(calendar_url)
        response.raise_for_status()

        # Parse the iCal data
        cal = Calendar.from_ical(response.content)

        # Extract all VEVENT components
        for event in cal.walk("vevent"):
            try:
                calendar_node = CalendarNode.from_ical_event(event)
                # Add calendar name to the node
                calendar_node.calendar_name = calendar_name
                events.append(calendar_node)
            except Exception as e:
                print(
                    f"Error parsing event {event.get('uid', 'unknown')} from {calendar_name}: {e}"
                )
                continue

        print(f"Successfully parsed {len(events)} events from {calendar_name} calendar")

    except requests.RequestException as e:
        print(f"Error fetching {calendar_name} calendar data: {e}")
    except Exception as e:
        print(f"Error parsing {calendar_name} calendar data: {e}")

    return events


def get_all_events() -> List[CalendarNode]:
    """
    Fetch all calendar events from all configured Google Calendar iCal feeds.

    Returns:
        List of CalendarNode objects representing all calendar events
    """
    all_events = []

    if not CALENDAR_URLS:
        print("No calendar URLs found in environment variables")
        print("Expected format: CALENDAR_<NAME>=<ICAL_URL>")
        return all_events

    print(f"Found {len(CALENDAR_URLS)} calendars: {list(CALENDAR_URLS.keys())}")

    for calendar_name, calendar_url in CALENDAR_URLS.items():
        print(f"Fetching events from {calendar_name} calendar...")
        events = get_events_from_calendar(calendar_name, calendar_url)
        all_events.extend(events)

    print(f"Total events across all calendars: {len(all_events)}")
    return all_events


def get_events_by_calendar(calendar_name: str) -> List[CalendarNode]:
    """
    Get events from a specific named calendar.

    Args:
        calendar_name: Name of the calendar to fetch events from

    Returns:
        List of CalendarNode objects from the specified calendar
    """
    if calendar_name not in CALENDAR_URLS:
        print(
            f"Calendar '{calendar_name}' not found. Available calendars: {list(CALENDAR_URLS.keys())}"
        )
        return []

    return get_events_from_calendar(calendar_name, CALENDAR_URLS[calendar_name])


def get_events_by_date_range(
    start_date, end_date, calendar_name: str = None
) -> List[CalendarNode]:
    """
    Get events within a specific date range, optionally filtered by calendar.

    Args:
        start_date: Start date for filtering
        end_date: End date for filtering
        calendar_name: Optional calendar name to filter by

    Returns:
        List of CalendarNode objects within the date range
    """
    if calendar_name:
        all_events = get_events_by_calendar(calendar_name)
    else:
        all_events = get_all_events()

    return [
        event
        for event in all_events
        if event.start_time
        and event.start_time >= start_date
        and event.start_time <= end_date
    ]


def get_upcoming_events(
    days_ahead: int = 7, calendar_name: str = None
) -> List[CalendarNode]:
    """
    Get events in the next N days, optionally filtered by calendar.

    Args:
        days_ahead: Number of days to look ahead (default: 7)
        calendar_name: Optional calendar name to filter by

    Returns:
        List of CalendarNode objects for upcoming events
    """
    from datetime import datetime, timedelta

    now = datetime.now()
    future_date = now + timedelta(days=days_ahead)

    return get_events_by_date_range(now, future_date, calendar_name)


def get_past_events(
    days_back: int = 7, calendar_name: str = None
) -> List[CalendarNode]:
    """
    Get events from the past N days, optionally filtered by calendar.

    Args:
        days_back: Number of days to look back (default: 7)
        calendar_name: Optional calendar name to filter by

    Returns:
        List of CalendarNode objects for past events
    """
    from datetime import datetime, timedelta

    now = datetime.now()
    past_date = now - timedelta(days=days_back)

    return get_events_by_date_range(past_date, now, calendar_name)


def list_available_calendars() -> List[str]:
    """
    Get list of available calendar names.

    Returns:
        List of calendar names
    """
    return list(CALENDAR_URLS.keys())


if __name__ == "__main__":
    # Test the functionality
    print("Available calendars:", list_available_calendars())

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
        print(f"  Calendar: {getattr(event, 'calendar_name', 'unknown')}")
        print(f"  Tags: {event.tags}")
