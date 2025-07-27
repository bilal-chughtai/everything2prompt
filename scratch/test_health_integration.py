#!/usr/bin/env python3
"""
Test script for health data integration.
"""

import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from health import get_all_health_data, create_health_prompt, HEALTH_CSV_PATH


def test_health_integration():
    """Test the health data integration."""
    print("Testing health data integration...")

    try:
        # Test loading health data
        print(f"Loading health data from: {HEALTH_CSV_PATH}")
        health_nodes = get_all_health_data()

        if health_nodes:
            print(f"Successfully loaded {len(health_nodes)} health data entries")

            # Test creating prompt
            prompt = create_health_prompt(health_nodes[:3])  # Just first 3 entries
            print("\nSample health prompt:")
            print("=" * 50)
            print(prompt)
            print("=" * 50)
        else:
            print("No health data found or directory doesn't exist")

    except Exception as e:
        print(f"Error testing health integration: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_health_integration()
