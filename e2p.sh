#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title e2p
# @raycast.packageName bilal's tools
# @raycast.mode silent

# Optional parameters:
# @raycast.icon 🤖
# @raycast.argument1 { "type": "text", "placeholder": "query" }

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Activate virtual environment
source .venv/bin/activate

# Run the query and capture output
QUERY_OUTPUT=$(python query.py "$1" 2>&1)

# Check if the command was successful
if [ $? -eq 0 ]; then
    # Calculate number of words and tokens
    WORD_COUNT=$(echo "$QUERY_OUTPUT" | wc -w)
    TOKEN_COUNT=$(echo "$WORD_COUNT * 1.33" | bc | cut -d. -f1)
    
    # Copy output to clipboard
    echo "$QUERY_OUTPUT" | pbcopy
    osascript -e 'tell application "System Events" to keystroke "v" using command down'
    
    # Display token count
    echo "Copied to clipboard. ~$TOKEN_COUNT tokens"
else
    # Error - show the error message
    echo "Error: $QUERY_OUTPUT"
    exit 1
fi


