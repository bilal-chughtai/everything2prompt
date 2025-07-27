#!/usr/bin/env python3
"""
Scratch file to test and display the query help output.
"""

# %%
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from query import get_query_help


def main():
    """Print out the query help output."""
    print("=" * 80)
    print("EVERYTHING2PROMPT QUERY HELP OUTPUT")
    print("=" * 80)
    print()

    try:
        help_text = get_query_help()
        print(help_text)
    except Exception as e:
        print(f"Error getting query help: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

# %%
