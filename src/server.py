from typing import Any
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from mcp.server.fastmcp import FastMCP
from src.query import run, get_query_help

# Configure logging to write to stderr instead of stdout
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Initialize FastMCP server
mcp = FastMCP("everything2prompt")


@mcp.tool(description=get_query_help())
async def get_query_result(query_string: str) -> str:
    """
    Execute a query.
    """
    try:
        result = run(query_string)
        return result
    except Exception as e:
        logging.error(f"Error in get_query_result: {e}")
        return f"Error executing query: {str(e)}"


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
