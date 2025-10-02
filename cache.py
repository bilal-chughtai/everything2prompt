import argparse
import os
import fcntl
import time
from pathlib import Path
from models import Cache
from dotenv import load_dotenv
import obsidian
import todoist
import instapaper
import cal as calendar
import health

# Load environment variables
load_dotenv()

# Get cache and lock file paths from environment variables
# Default to relative paths if not specified
CACHE_FILE_PATH = os.getenv("CACHE_FILE_PATH", "cache.json")
LOCK_FILE_PATH = os.getenv("LOCK_FILE_PATH", "cache.lock")


class CacheLock:
    """
    File-based lock for cache operations to prevent multiple processes from
    modifying the cache simultaneously.
    """

    def __init__(self, lock_file_path: str = LOCK_FILE_PATH, timeout: int = 30):
        self.lock_file_path = lock_file_path
        self.timeout = timeout
        self.lock_file = None

    def __enter__(self):
        start_time = time.time()

        while time.time() - start_time < self.timeout:
            try:
                # Ensure the directory exists
                lock_dir = Path(self.lock_file_path).parent
                lock_dir.mkdir(parents=True, exist_ok=True)

                # Open the lock file
                self.lock_file = open(self.lock_file_path, "w")

                # Try to acquire an exclusive lock
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

                # Write the current process info to the lock file
                self.lock_file.write(f"PID: {os.getpid()}, Time: {time.time()}\n")
                self.lock_file.flush()

                print(f"Acquired cache lock (PID: {os.getpid()})")
                return self

            except (IOError, OSError) as e:
                if self.lock_file:
                    self.lock_file.close()
                    self.lock_file = None

                if time.time() - start_time >= self.timeout:
                    raise TimeoutError(
                        f"Failed to acquire cache lock after {self.timeout} seconds: {e}"
                    )

                print(
                    f"Waiting for cache lock to be released... (elapsed: {time.time() - start_time:.1f}s)"
                )
                time.sleep(0.5)

        raise TimeoutError(f"Failed to acquire cache lock after {self.timeout} seconds")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_file:
            try:
                # Release the lock
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                self.lock_file.close()
                print("Released cache lock")
            except Exception as e:
                print(f"Error releasing cache lock: {e}")
            finally:
                self.lock_file = None


def load_cache() -> Cache:
    """
    Load cache from the global cache file path.
    Creates a new cache if the file doesn't exist.
    """
    if os.path.exists(CACHE_FILE_PATH):
        try:
            return Cache.from_path(CACHE_FILE_PATH)
        except Exception as e:
            print(f"[main] Error loading cache from {CACHE_FILE_PATH}: {e}")
            print("[main] Creating new cache...")
            return Cache()
    else:
        print(
            f"[main] Cache file not found at {CACHE_FILE_PATH}, creating new cache..."
        )
        return Cache()


def update_obsidian_cache(cache: Cache) -> Cache:
    """
    Update the obsidian notes in the cache.
    """
    print("[obsidian] Updating Obsidian cache...")
    obsidian_nodes = obsidian.get_all_nodes(obsidian.OBSIDIAN_PATH)
    cache.obsidian_notes = obsidian_nodes
    print(f"[obsidian] Updated {len(obsidian_nodes)} Obsidian notes")
    return cache


def update_todoist_cache(cache: Cache, days_back: int = 7) -> Cache:
    """
    Update the todoist tasks in the cache.

    Args:
        cache: The cache to update
        days_back: Number of days to look back for completed tasks (default: 7)
    """
    print(f"[todoist] Updating Todoist cache (looking back {days_back} days)...")
    api = todoist.get_todoist_api()
    if not api:
        print("[todoist] Failed to initialize Todoist API, skipping Todoist update")
        return cache

    # Get all Todoist data including completed tasks from the specified days back
    active_tasks, completed_tasks, todoist_projects = todoist.get_all_todoist_data(
        days_back
    )

    # Combine active and completed tasks
    all_tasks = active_tasks + completed_tasks

    # Replace cache data with fresh data (no merging since we fetch fresh data)
    cache.todoist_tasks = all_tasks
    cache.todoist_projects = todoist_projects
    return cache


def update_instapaper_cache(cache: Cache) -> Cache:
    """
    Update the Instapaper articles in the cache.
    """
    print("[instapaper] Updating Instapaper cache...")
    instapaper_articles = instapaper.get_all_articles()
    cache.instapaper_articles = instapaper_articles
    print(f"[instapaper] Updated {len(instapaper_articles)} Instapaper articles")
    return cache


def update_calendar_cache(cache: Cache) -> Cache:
    """
    Update the calendar events in the cache.
    """
    print("[calendar] Updating Calendar cache...")
    calendar_events = calendar.get_all_events()
    cache.calendar_events = calendar_events
    print(f"[calendar] Updated {len(calendar_events)} Calendar events")
    return cache


def update_health_cache(cache: Cache) -> Cache:
    """
    Update the health data in the cache.
    """
    print("[health] Updating Health cache...")
    health_data = health.get_all_health_data()
    cache.health_data = health_data
    print(f"[health] Updated {len(health_data)} Health data entries")
    return cache


def save_cache(cache: Cache) -> None:
    """
    Save cache to the global cache file path.
    """
    # Ensure the directory exists
    cache_dir = Path(CACHE_FILE_PATH).parent
    cache_dir.mkdir(parents=True, exist_ok=True)

    try:
        cache.to_path(CACHE_FILE_PATH)
        print(f"[main] Cache saved to {CACHE_FILE_PATH}")
    except Exception as e:
        print(f"[main] Error saving cache to {CACHE_FILE_PATH}: {e}")


def update_cache_for_sources(sources: list[str], days_back: int = 7) -> None:
    """
    Update cache for the specified data sources.

    Args:
        sources: List of data sources to update
        days_back: Number of days to look back for Todoist completed tasks (default: 7)
    """
    # Load existing cache
    cache = load_cache()

    # Update cache for each specified source
    for source in sources:
        if source.lower() == "obsidian":
            cache = update_obsidian_cache(cache)
        elif source.lower() == "todoist":
            cache = update_todoist_cache(cache, days_back)
        elif source.lower() == "instapaper":
            cache = update_instapaper_cache(cache)
        elif source.lower() == "calendar":
            cache = update_calendar_cache(cache)
        elif source.lower() == "health":
            cache = update_health_cache(cache)
        else:
            print(f"Unknown data source: {source}")

    # Save updated cache
    save_cache(cache)


def main():
    """
    Main function to handle command line arguments and update cache.
    """
    parser = argparse.ArgumentParser(
        description="Update cache for specified data sources"
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        default=["obsidian", "todoist", "instapaper", "calendar", "health"],
        help="Data sources to update (default: all sources)",
    )
    parser.add_argument(
        "--api-num-days-back",
        type=int,
        default=7,
        help="Number of days back to fetch completed tasks from Todoist API (default: 7)",
    )
    args = parser.parse_args()
    with CacheLock():
        print(f"[main] Updating cache for sources: {args.sources}")
        update_cache_for_sources(args.sources, args.api_num_days_back)


if __name__ == "__main__":
    main()
