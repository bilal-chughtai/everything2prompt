# Everything2Prompt MCP Server

This MCP (Model Context Protocol) server provides tools to search across multiple data sources including Obsidian notes, Todoist tasks, Instapaper articles, and Calendar events.

## Features

The MCP server provides the following tools:

1. **search_data** - Search across all data sources with a flexible query string
2. **search_obsidian_notes** - Search specifically in Obsidian notes
3. **search_todoist_tasks** - Search specifically in Todoist tasks
4. **search_instapaper_articles** - Search specifically in Instapaper articles
5. **search_calendar_events** - Search specifically in Calendar events
6. **search_by_tag** - Search across all sources for items with a specific tag
7. **search_by_date_range** - Search across all sources within a date range

## Setup

### Prerequisites

- Python 3.11 or higher
- All your data sources must be properly configured and cached (Obsidian, Todoist, Instapaper, Calendar)

### Installation

1. **Install dependencies using pip:**
   ```bash
   pip install -r requirements.txt
   ```

   **Or using Poetry:**
   ```bash
   poetry install
   ```

2. **Ensure your data is cached:**
   Make sure you have run your data collection scripts to populate the cache with your Obsidian notes, Todoist tasks, Instapaper articles, and Calendar events.

## Usage

### Running the MCP Server

```bash
python mcp.py
```

The server will start and listen for MCP connections via standard I/O.

### Query Format

The `search_data` tool accepts query strings in the following format:

```
source:obsidian,todoist tag:health,work from:2025-01-01 to:2025-12-31
```

**Supported parameters:**
- `source`: Filter by data source (obsidian, todoist, instapaper, calendar)
- `tag`: Filter by tags (comma-separated)
- `from`: Start date (YYYY-MM-DD format)
- `to`: End date (YYYY-MM-DD format)

**Examples:**
- `tag:health` - Find all items with 'health' tag
- `source:obsidian tag:work,project` - Find Obsidian notes with work or project tags
- `from:2025-01-01 to:2025-12-31` - Find items from 2025
- `source:todoist` - Find all Todoist tasks

### Integration with Claude for Desktop

1. **Install Claude for Desktop** from [claude.ai/download](https://claude.ai/download)

2. **Configure Claude for Desktop:**
   Open the configuration file at:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%AppData%\Claude\claude_desktop_config.json`

3. **Add the MCP server configuration:**
   ```json
   {
     "mcpServers": {
       "everything2prompt": {
         "command": "python",
         "args": ["/ABSOLUTE/PATH/TO/YOUR/PROJECT/mcp.py"]
       }
     }
   }
   ```

   **Important:** Replace `/ABSOLUTE/PATH/TO/YOUR/PROJECT/` with the actual absolute path to your project directory.

4. **Restart Claude for Desktop**

5. **Test the integration:**
   - Look for the "Search and tools" icon in Claude for Desktop
   - Try queries like:
     - "Search for all my health-related notes"
     - "Show me my Todoist tasks from last week"
     - "Find all my work-related items"

## Troubleshooting

### Server not showing up in Claude for Desktop

1. **Check the configuration file syntax** - Ensure the JSON is valid
2. **Verify the absolute path** - Make sure the path to `mcp.py` is correct and absolute
3. **Check permissions** - Ensure the Python script is executable
4. **Restart Claude for Desktop** completely

### Tool calls failing

1. **Check Claude's logs:**
   - macOS: `~/Library/Logs/Claude/mcp*.log`
   - Windows: Check the Claude logs directory

2. **Verify your data cache:**
   - Ensure your data collection scripts have run successfully
   - Check that the cache files exist and are readable

3. **Test the server manually:**
   ```bash
   python mcp.py
   ```
   The server should start without errors.

### Common Issues

- **Import errors:** Make sure all dependencies are installed
- **Cache not found:** Run your data collection scripts first
- **Permission errors:** Check file permissions on your project directory

## Development

### Adding New Tools

To add new tools to the MCP server:

1. Add a new function decorated with `@mcp.tool()` in `mcp.py`
2. Use proper type hints and docstrings for automatic tool definition
3. Handle exceptions gracefully and return meaningful error messages

### Testing

Test your server locally before integrating with Claude for Desktop:

```bash
# Test the basic functionality
python query.py "tag:test"

# Test the MCP server
python mcp.py
```

## Logging

The server uses logging to stderr (not stdout) to avoid interfering with MCP communication. Logs include:
- Server startup information
- Tool execution results
- Error messages

## Support

For issues with the MCP server specifically, check the Claude for Desktop logs and ensure your data sources are properly configured and cached. 