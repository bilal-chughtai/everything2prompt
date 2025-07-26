# %%
import requests
from icalendar import Calendar
from dotenv import load_dotenv
import os

load_dotenv()

response = requests.get(os.getenv("SECRET_GCAL_ICAL"))
cal = Calendar.from_ical(response.content)
events = list(cal.walk("vevent"))
for event in reversed(events):
    print(event.get("summary"), event.get("dtstart"))
    print(event)
    break

# %%
