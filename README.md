# Everything2Prompt

Turn any data source into a prompt. A powerful tool that aggregates and searches across multiple personal data sources including Obsidian notes, Todoist tasks, Instapaper articles, Calendar events, and Health data.

## 🚀 Features

- **Multi-source data aggregation**: Combine data from Obsidian, Todoist, Instapaper, Calendar, and Health sources
- **Flexible query system**: Search across all sources with powerful filtering options
- **MCP (Model Context Protocol) server**: Single tool integration with Claude for Desktop and other MCP-compatible applications
- **Dynamic help generation**: Automatically generates comprehensive query documentation based on your actual data
- **Raycast integration**: Quick access via Raycast script with clipboard output
- **Smart caching**: Efficient data caching for fast queries
- **Tag-based organization**: Organize and filter data using tags with usage statistics

## 📋 Supported Data Sources

- **Obsidian Notes**: Search through your Obsidian vault
- **Todoist Tasks**: Access your task management system
- **Instapaper Articles**: Search saved articles and highlights
- **Calendar Events**: Query your calendar data
- **Health Data**: Access health-related information

## 🛠️ Installation

### Prerequisites

- Python 3.11 or higher
- Poetry (recommended) or pip

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd everything2prompt
   ```

2. **Install dependencies:**
   ```bash
   poetry install
   ```

3. **Configure environment variables:**
   ```bash
   cp env_template.txt .env
   # Edit .env with your actual values
   ```

4. **Test setup:**
   ```bash
   poetry run python cache.py --sources obsidian
   poetry run python query.py "tag:health"
   ```

5. **Set up automated cache updates:**
   ```bash
   crontab -e
   # Add this line (replace with your actual project path):
   */5 * * * * /path/to/everything2prompt/update_cache.sh
   ```

6. **Configure tag descriptions (MCP server):**
   ```bash
   cp tag_descriptions_template.json tag_descriptions.json
   # Edit tag_descriptions.json with your actual tags
   ```

## 🎯 Usage

### Command Line Interface

Search your data using the query system:

```bash
python query.py "tag:health"
python query.py "source:obsidian,todoist tag:work from:2024-01-01 to:2024-12-31"
python query.py "source:instapaper"
```

### Query Syntax

The query system supports flexible filtering:

```
source:obsidian,todoist tag:health,work from:2024-01-01 to:2024-12-31
```

**Supported parameters:**
- `source`: Filter by data source (`obsidian`, `todoist`, `instapaper`, `calendar`, `health`)
- `tag`: Filter by tags (comma-separated)
- `from`: Start date (YYYY-MM-DD format)
- `to`: End date (YYYY-MM-DD format)

**Examples:**
- `tag:health` - Find all health-related items
- `source:obsidian tag:work,project` - Find Obsidian notes with work or project tags
- `from:2024-01-01 to:2024-12-31` - Find items from 2024
- `source:todoist` - Find all Todoist tasks

### Raycast Integration

Use the included Raycast script for quick access:

1. Copy `e2p.sh` to your Raycast scripts directory
2. Use the command `e2p <query>` in Raycast
3. Results are automatically copied to clipboard

### MCP Server

The project includes a Model Context Protocol (MCP) server that provides a single powerful tool for querying all your data sources. This allows you to integrate Everything2Prompt with Claude for Desktop and other MCP-compatible applications.

#### Running the MCP Server

```bash
python server.py
```

The server runs on stdio transport and provides one main tool:

- **`get_query_result`**: Execute queries across all data sources using the same query syntax as the CLI

#### MCP Tool Description

The MCP server automatically generates comprehensive help documentation that includes:
- Available data sources in your cache
- All available tags organized by source
- Tag descriptions and usage counts
- Complete query syntax guide

#### Integration with Claude for Desktop

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
         "args": ["/ABSOLUTE/PATH/TO/YOUR/PROJECT/server.py"]
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

For detailed MCP setup instructions and troubleshooting, see [README_MCP.md](README_MCP.md).

## 📁 Project Structure

```
everything2prompt/
├── cache.py              # Caching system
├── cal.py                # Calendar integration
├── e2p.sh               # Raycast script
├── health.py            # Health data integration
├── instapaper.py        # Instapaper integration
├── models.py            # Data models
├── obsidian.py          # Obsidian integration
├── query.py             # Main query engine with help generation
├── server.py            # MCP server (FastMCP implementation)
├── todoist.py           # Todoist integration
├── tag_descriptions.py  # Tag descriptions and metadata
├── update_cache.sh      # Cache update script
├── README_MCP.md        # Detailed MCP setup guide
└── scratch/             # Development files
```

## 🔄 Caching

The system uses intelligent caching to improve performance:

- Data is cached locally in `cache.json`
- Use `./update_cache.sh` to refresh your data
- Cache is automatically managed and updated

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.