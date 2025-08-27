#!/bin/bash

# Comprehensive cache update script for everything2prompt
# This script handles all data sources with their respective update frequencies

cd /Users/bilal/Code/everything2prompt
source .venv/bin/activate

# Get current timestamp for frequency checking
CURRENT_TIME=$(date +%s)
CURRENT_MINUTE=$(date +%M)
CURRENT_HOUR=$(date +%H)

echo "Running cache update at $(date)"

# Function to update cache for specific sources
update_sources() {
    local sources=("$@")
    echo "Updating sources: ${sources[*]}"
    python cache.py --sources "${sources[@]}"
}

# Check if it's time for frequent updates (every 5 minutes)
if [ $((CURRENT_MINUTE % 5)) -eq 0 ]; then
    echo "Time for frequent update (every 5 minutes) - updating Obsidian..."
    update_sources obsidian
fi

# Check if it's time for hourly updates (every 4 hours)
if [ $((CURRENT_HOUR % 4)) -eq 0 ] && [ $CURRENT_MINUTE -eq 0 ]; then
    echo "Time for hourly update (every 4 hours) - updating all sources..."
    update_sources obsidian todoist calendar health instapaper
fi

# If no frequency conditions met, check command line arguments
if [ $# -gt 0 ]; then
    echo "Manual update requested for: $*"
    update_sources "$@"
fi

echo "Cache update completed at $(date)"