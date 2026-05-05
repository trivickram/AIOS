"""
MCP tool server for the AIOS middleware demo.

Exposes two tools over JSON-RPC (stdio transport):
- fetch_source_data
- push_destination_data
"""

from typing import Any, Dict
import json
import os

import requests
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("middleware-demo-tools")

SOURCE_SERVER_URL = os.getenv("SOURCE_SERVER_URL", "http://localhost:5001")
DESTINATION_SERVER_URL = os.getenv("DESTINATION_SERVER_URL", "http://localhost:5002")


def _normalize_endpoint(endpoint: str) -> str:
    if not endpoint.startswith("/"):
        return f"/{endpoint}"
    return endpoint


def _build_url(base_url: str, endpoint: str) -> str:
    return f"{base_url}{_normalize_endpoint(endpoint)}"


@mcp.tool(description="Fetch legacy customer data from the source server.")
def fetch_source_data(endpoint: str = "/api/source") -> Dict[str, Any]:
    url = _build_url(SOURCE_SERVER_URL, endpoint)
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return {
            "success": True,
            "data": response.json(),
        }
    except requests.RequestException as exc:
        return {
            "success": False,
            "error": f"Failed to fetch source data: {exc}",
        }
    except json.JSONDecodeError as exc:
        return {
            "success": False,
            "error": f"Failed to parse JSON response: {exc}",
        }


@mcp.tool(description="Push transformed user data to the destination server.")
def push_destination_data(
    payload: Dict[str, Any],
    endpoint: str = "/api/destination",
) -> Dict[str, Any]:
    url = _build_url(DESTINATION_SERVER_URL, endpoint)
    if not isinstance(payload, dict) or "users" not in payload:
        return {
            "success": False,
            "error": "Payload must be a dict with a 'users' key",
        }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return {
            "success": True,
            "response": response.json(),
        }
    except requests.RequestException as exc:
        return {
            "success": False,
            "error": f"Failed to push destination data: {exc}",
        }
    except json.JSONDecodeError as exc:
        return {
            "success": False,
            "error": f"Failed to parse JSON response: {exc}",
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")
