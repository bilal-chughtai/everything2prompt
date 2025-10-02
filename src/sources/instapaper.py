import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

import requests
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.models import InstapaperNode
from jinja2 import Template
from requests_oauthlib import OAuth1Session
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

# Instapaper API configuration
INSTAPAPER_BASE_URL = "https://www.instapaper.com/api/1"
CONSUMER_KEY = os.getenv("INSTAPAPER_CONSUMER_KEY")  # Your OAuth Consumer ID
CONSUMER_SECRET = os.getenv("INSTAPAPER_CONSUMER_SECRET")  # Your OAuth Consumer Secret

# Store user credentials (you'll need to get these through xAuth)
ACCESS_TOKEN = os.getenv("INSTAPAPER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("INSTAPAPER_ACCESS_TOKEN_SECRET")

# Jinja template for formatting Instapaper articles
INSTAPAPER_PROMPT_TEMPLATE = """*** Instapaper Articles ***
Title = article headline/title
URL = web page URL
Tags = user-applied tags for organization
Date = date saved to Instapaper (none if no date available). importantly, not the date of reading.
Read = true=marked as read, false=unread
{% for article in articles %}
--- Article {{ loop.index }} ---
Title: {{ article.title }}
URL: {{ article.url }}{% if article.tags %}
Tags: {{ article.tags | join(', ') }}{% endif %}{% if article.date %}
Date: {{ article.date.strftime('%Y-%m-%d') }}{% else %}
Date: none{% endif %}
Read: {{ article.is_read }}{% endfor %}
"""


class InstapaperAPI:
    """
    A read-only class to interact with the Instapaper API using OAuth 1.0a authentication.
    """

    def __init__(
        self,
        consumer_key: str = None,
        consumer_secret: str = None,
        access_token: str = None,
        access_token_secret: str = None,
    ):
        self.consumer_key = consumer_key or CONSUMER_KEY
        self.consumer_secret = consumer_secret or CONSUMER_SECRET
        self.access_token = access_token or ACCESS_TOKEN
        self.access_token_secret = access_token_secret or ACCESS_TOKEN_SECRET

        if not all([self.consumer_key, self.consumer_secret]):
            raise ValueError("Consumer key and secret are required")

    def get_access_token(self, username: str, password: str = "") -> tuple:
        """
        Get access token using xAuth (username/password authentication).
        Only needed once to get your access tokens.

        Args:
            username: Instapaper username (usually email)
            password: Instapaper password (empty string if no password)

        Returns:
            Tuple of (access_token, access_token_secret)
        """
        auth = OAuth1Session(self.consumer_key, client_secret=self.consumer_secret)

        data = {
            "x_auth_username": username,
            "x_auth_password": password,
            "x_auth_mode": "client_auth",
        }

        response = requests.post(
            f"{INSTAPAPER_BASE_URL}/oauth/access_token", auth=auth.auth, data=data
        )

        if response.status_code == 200:
            # Parse the response (format: oauth_token=...&oauth_token_secret=...)
            parsed = urllib.parse.parse_qs(response.text)
            access_token = parsed["oauth_token"][0]
            access_token_secret = parsed["oauth_token_secret"][0]

            # Update instance variables
            self.access_token = access_token
            self.access_token_secret = access_token_secret

            return access_token, access_token_secret
        else:
            raise Exception(
                f"Failed to get access token: {response.status_code} - {response.text}"
            )

    def _make_request(
        self, endpoint: str, params: Dict[str, Any] = None
    ) -> requests.Response:
        """
        Make an authenticated GET request to the Instapaper API.

        Args:
            endpoint: API endpoint (without base URL)
            params: Request parameters

        Returns:
            Response object
        """
        if not self.access_token or not self.access_token_secret:
            raise ValueError(
                "Access token and secret are required. Call get_access_token() first."
            )

        auth = OAuth1Session(
            self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret,
        )

        url = f"{INSTAPAPER_BASE_URL}/{endpoint.lstrip('/')}"

        response = requests.post(url, auth=auth.auth, data=params or {})
        return response

    def verify_credentials(self) -> Dict[str, Any]:
        """
        Verify the current user's credentials and get user info.

        Returns:
            User information dictionary
        """
        response = self._make_request("/account/verify_credentials")

        if response.status_code == 200:
            data = response.json()
            if data and data[0].get("type") == "user":
                return data[0]

        raise Exception(
            f"Failed to verify credentials: {response.status_code} - {response.text}"
        )

    def get_bookmarks(
        self, limit: int = 25, folder_id: str = "unread", tag: str = None
    ) -> Dict[str, Any]:
        """
        Get bookmarks from the user's account.

        Args:
            limit: Number of bookmarks to retrieve (1-500, default 25)
            folder_id: Folder to retrieve from ("unread", "starred", "archive", or folder ID)
            tag: Optional tag to filter by

        Returns:
            Dictionary containing bookmarks, highlights, and metadata
        """
        params = {"limit": min(max(1, limit), 500), "folder_id": folder_id}

        if tag:
            params["tag"] = tag

        response = self._make_request("/bookmarks/list", params)

        if response.status_code == 200:
            data = response.json()

            # Handle both old API format (list) and new API format (dict)
            if isinstance(data, list):
                # Old format: parse the list into categories
                bookmarks = []
                highlights = []
                user = None
                delete_ids = []

                for item in data:
                    if isinstance(item, dict):
                        item_type = item.get("type")
                        if item_type == "bookmark":
                            bookmarks.append(item)
                        elif item_type == "highlight":
                            highlights.append(item)
                        elif item_type == "user":
                            user = item
                        elif item_type == "meta" and "delete_ids" in item:
                            delete_ids = item.get("delete_ids", [])

                return {
                    "bookmarks": bookmarks,
                    "highlights": highlights,
                    "user": user,
                    "delete_ids": delete_ids,
                }
            else:
                # New format: return as-is
                return data
        else:
            raise Exception(
                f"Failed to get bookmarks: {response.status_code} - {response.text}"
            )

    def get_folders(self) -> List[Dict[str, Any]]:
        """
        Get user's folders.

        Returns:
            List of folder dictionaries
        """
        response = self._make_request("/folders/list")

        if response.status_code == 200:
            data = response.json()
            return [item for item in data if item.get("type") == "folder"]

        raise Exception(
            f"Failed to get folders: {response.status_code} - {response.text}"
        )


def create_instapaper_prompt(articles: List[InstapaperNode]) -> str:
    """
    Create a formatted prompt from a list of Instapaper articles.
    """
    template = Template(INSTAPAPER_PROMPT_TEMPLATE)
    return template.render(articles=articles)


def create_instapaper_node_from_csv_row(row: dict) -> InstapaperNode:
    """
    Create InstapaperNode from a CSV row.
    """
    # Parse tags from the tags field (assuming it's a string representation of a list)
    tags_str = row.get("Tags", "[]")
    try:
        # Remove brackets and split by comma, then strip whitespace
        tags = [
            tag.strip().strip("\"'")
            for tag in tags_str.strip("[]").split(",")
            if tag.strip()
        ]
    except:
        tags = []

    # Determine if the article is read based on folder
    folder = row.get("Folder", "").lower()
    is_read = folder == "starred"

    # Convert timestamp to datetime
    timestamp_str = row.get("Timestamp", "")
    date = None
    if timestamp_str:
        try:
            timestamp = int(timestamp_str)
            if timestamp > 0:
                date = datetime.fromtimestamp(timestamp)
        except (ValueError, TypeError):
            # Invalid timestamp, date remains None
            pass

    return InstapaperNode(
        name=row.get("Title", ""),  # Use title as the name
        url=row.get("URL", ""),
        title=row.get("Title", ""),
        folder=row.get("Folder", ""),
        is_read=is_read,
        timestamp=timestamp,
        date=date,
        tags=tags,
        selection=row.get("Selection", None),
    )


def bookmark_to_instapaper_node(bookmark: Dict[str, Any]) -> InstapaperNode:
    """
    Convert a bookmark dictionary from the API to an InstapaperNode.

    Args:
        bookmark: Bookmark dictionary from API response

    Returns:
        InstapaperNode object
    """
    # Extract tags if present
    tags = []
    if "tags" in bookmark and bookmark["tags"]:
        tags = [tag.get("name", "") for tag in bookmark["tags"] if tag.get("name")]

    # Get timestamp (required field)
    timestamp = bookmark.get("time", 0)

    # Parse date from timestamp only if timestamp exists
    date = None
    if timestamp:
        try:
            timestamp = int(timestamp)
            date = datetime.fromtimestamp(timestamp)
        except (ValueError, TypeError):
            date = None  # Invalid timestamp, set to None
    # If no timestamp, date remains None

    # Determine if read based on whether it's in the archive folder
    # The API response includes folder information
    folder = bookmark.get("folder", "unread")
    is_read = folder == "archive"  # Archive folder indicates it has been read

    # Ensure folder is properly set for archive items
    if bookmark.get("folder_id") == "archive" or folder == "archive":
        folder = "archive"
        is_read = True

    title = bookmark.get("title", "Untitled")

    return InstapaperNode(
        name=title,  # Required field - use title as name
        title=title,
        url=bookmark.get("url", ""),
        folder=folder,
        tags=tags,
        date=date,
        timestamp=timestamp,  # Required field
        is_read=is_read,
        selection=bookmark.get("description", None),  # Use description as selection
    )


def get_all_articles(
    api: InstapaperAPI = None, limit_per_request: int = 2000
) -> List[InstapaperNode]:
    """
    Get all articles from Instapaper using the API from archive and unread folders.

    Args:
        api: InstapaperAPI instance (will create one if None)
        limit_per_request: Number of articles to fetch per request (default: 2000)

    Returns:
        List of InstapaperNode objects representing all articles
    """
    if api is None:
        api = InstapaperAPI()

    articles = []
    folders = ["archive", "unread"]

    for folder in folders:
        try:
            response = api.get_bookmarks(limit=limit_per_request, folder_id=folder)
            bookmarks = response.get("bookmarks", [])

            print(f"Fetched {len(bookmarks)} bookmarks from {folder} folder")

            for bookmark in bookmarks:
                if isinstance(bookmark, dict) and bookmark.get("type") == "bookmark":
                    # Mark archive items as read
                    if folder == "archive":
                        bookmark["folder"] = "archive"
                    article = bookmark_to_instapaper_node(bookmark)
                    articles.append(article)

        except Exception as e:
            print(f"Error fetching articles from {folder}: {e}")

    print(f"Successfully fetched {len(articles)} articles from Instapaper API")
    return articles


if __name__ == "__main__":
    # Example usage
    try:
        # Initialize API (make sure environment variables are set)
        api = InstapaperAPI()

        # If you don't have access tokens yet, get them with username/password
        # username = "your-email@example.com"
        # password = "your-password"  # or "" if you don't have one
        # access_token, access_token_secret = api.get_access_token(username, password)
        # print(f"Access token: {access_token}")
        # print(f"Access token secret: {access_token_secret}")

        # Verify credentials
        user_info = api.verify_credentials()
        print(
            f"Authenticated as: {user_info.get('username')} (ID: {user_info.get('user_id')})"
        )

        # Test the functionality
        articles = get_all_articles(api)
        print(f"Total articles: {len(articles)}")

        # Count articles by status
        read_count = len([a for a in articles if a.is_read])
        unread_count = len([a for a in articles if not a.is_read])
        print(f"Read articles: {read_count}")
        print(f"Unread articles: {unread_count}")

        # Get user's folders
        folders = api.get_folders()
        print(f"Custom folders: {len(folders)}")
        for folder in folders:
            print(f"  - {folder.get('title')} (ID: {folder.get('folder_id')})")

        # Print first few articles as examples
        for i, article in enumerate(articles):
            print(f"\nArticle {i + 1}:")
            print(f"  Title: {article.title}")
            print(f"  URL: {article.url}")
            print(f"  Folder: {article.folder}")
            print(f"  Is Read: {article.is_read}")
            print(f"  Tags: {article.tags}")
            print(f"  Date: {article.date}")

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you have set the following environment variables:")
        print("- INSTAPAPER_CONSUMER_KEY")
        print("- INSTAPAPER_CONSUMER_SECRET")
        print("- INSTAPAPER_ACCESS_TOKEN (after getting it via xAuth)")
        print("- INSTAPAPER_ACCESS_TOKEN_SECRET (after getting it via xAuth)")
        print("\nNote: Articles are now fetched from archive and unread folders.")
        print(
            "Read status is determined by whether the article is in the archive folder."
        )
