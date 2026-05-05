"""
AIOS Tools for Middleware Demo

This module provides custom tools for the AIOS framework to:
1. Fetch data from the source Flask server
2. Push transformed data to the destination Flask server

These tools follow the AIOS BaseTool pattern and can be registered
with the AIOS Tool Manager.
"""

import requests
from typing import Dict, Any, Optional
import json


class SourceDataFetcherTool:
    """
    Tool 1: Fetches legacy customer data from the source server

    This tool implements the AIOS BaseTool interface and provides
    functionality to retrieve data from Endpoint A (source server).
    """

    def __init__(self, source_url: str = "http://localhost:5001"):
        """
        Initialize the source data fetcher tool

        Args:
            source_url: Base URL of the source Flask server
        """
        self.name = "fetch_source_data"
        self.source_url = source_url

    def get_tool_call_format(self) -> Dict[str, Any]:
        """
        Get tool calling format following OpenAI function calling format

        Returns:
            Dictionary describing the tool's function signature
        """
        return {
            "type": "function",
            "function": {
                "name": "fetch_source_data",
                "description": (
                    "Fetches legacy customer data from the source server. "
                    "Returns a JSON object containing customer records with fields: "
                    "customer_id, first_name, last_name, contact_num, email_addr, "
                    "join_date, and status_code. This data is in the old legacy format "
                    "and needs to be transformed before sending to the destination server."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "endpoint": {
                            "type": "string",
                            "description": "Optional custom endpoint path. Defaults to '/api/source'",
                            "default": "/api/source"
                        }
                    },
                    "required": []
                }
            }
        }

    def run(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the tool to fetch data from source server

        Args:
            params: Optional parameters dictionary. Can contain:
                - endpoint: Custom endpoint path (default: /api/source)

        Returns:
            Dictionary containing the response from the source server with structure:
            {
                "success": bool,
                "data": dict or None,
                "error": str or None
            }
        """
        if params is None:
            params = {}

        endpoint = params.get("endpoint", "/api/source")
        url = f"{self.source_url}{endpoint}"

        print(f"🔧 [TOOL: fetch_source_data] Fetching data from {url}")

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            print(f"✅ [TOOL: fetch_source_data] Successfully fetched data")
            print(f"📊 [TOOL: fetch_source_data] Received {data.get('total_count', 0)} customer records")

            return {
                "success": True,
                "data": data,
                "error": None
            }

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to fetch data from source server: {str(e)}"
            print(f"❌ [TOOL: fetch_source_data] {error_msg}")

            return {
                "success": False,
                "data": None,
                "error": error_msg
            }

        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON response: {str(e)}"
            print(f"❌ [TOOL: fetch_source_data] {error_msg}")

            return {
                "success": False,
                "data": None,
                "error": error_msg
            }


class DestinationDataPusherTool:
    """
    Tool 2: Pushes transformed user data to the destination server

    This tool implements the AIOS BaseTool interface and provides
    functionality to send data to Endpoint B (destination server).
    """

    def __init__(self, destination_url: str = "http://localhost:5002"):
        """
        Initialize the destination data pusher tool

        Args:
            destination_url: Base URL of the destination Flask server
        """
        self.name = "push_destination_data"
        self.destination_url = destination_url

    def get_tool_call_format(self) -> Dict[str, Any]:
        """
        Get tool calling format following OpenAI function calling format

        Returns:
            Dictionary describing the tool's function signature
        """
        return {
            "type": "function",
            "function": {
                "name": "push_destination_data",
                "description": (
                    "Pushes transformed user data to the destination server. "
                    "Expects data in modernized format with fields: userId, fullName, "
                    "phoneDetails (object with 'number' and optional 'formatted'), "
                    "emailAddress, registrationDate (ISO format), and accountStatus "
                    "(either 'active' or 'inactive'). The payload must be a dictionary "
                    "with a 'users' key containing a list of user objects."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "payload": {
                            "type": "object",
                            "description": (
                                "The data payload to send. Must contain a 'users' key "
                                "with a list of user objects in the modernized format."
                            ),
                            "properties": {
                                "users": {
                                    "type": "array",
                                    "description": "Array of user objects",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                           
                                            "fullName": {"type": "string"},
                                            "phoneDetails": {
                                                "type": "object",
                                                "properties": {
                                                    "number": {"type": "string"},
                                                    "formatted": {"type": "string"}
                                                },
                                                "required": ["number"]
                                            },
                                            "emailAddress": {"type": "string"},
                                            "registrationDate": {"type": "string"},
                                            "accountStatus": {
                                                "type": "string",
                                                "enum": ["active", "inactive"]
                                            }
                                        },
                                        "required": [
                                            "fullName", "phoneDetails",
                                            "emailAddress", "registrationDate", "accountStatus"
                                        ]
                                    }
                                }
                            },
                            "required": ["users"]
                        },
                        "endpoint": {
                            "type": "string",
                            "description": "Optional custom endpoint path. Defaults to '/api/destination'",
                            "default": "/api/destination"
                        }
                    },
                    "required": ["payload"]
                }
            }
        }

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool to push data to destination server

        Args:
            params: Parameters dictionary containing:
                - payload: The data to send (required)
                - endpoint: Custom endpoint path (optional, default: /api/destination)

        Returns:
            Dictionary containing the response from the destination server with structure:
            {
                "success": bool,
                "response": dict or None,
                "error": str or None
            }
        """
        if not params or "payload" not in params:
            error_msg = "Missing required parameter: 'payload'"
            print(f"❌ [TOOL: push_destination_data] {error_msg}")
            return {
                "success": False,
                "response": None,
                "error": error_msg
            }

        payload = params["payload"]
        endpoint = params.get("endpoint", "/api/destination")
        url = f"{self.destination_url}{endpoint}"

        print(f"🔧 [TOOL: push_destination_data] Pushing data to {url}")

        # Validate payload structure
        if not isinstance(payload, dict) or "users" not in payload:
            error_msg = "Payload must be a dictionary with a 'users' key"
            print(f"❌ [TOOL: push_destination_data] {error_msg}")
            return {
                "success": False,
                "response": None,
                "error": error_msg
            }

        print(f"📊 [TOOL: push_destination_data] Sending {len(payload['users'])} user records")

        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()

            response_data = response.json()

            print(f"✅ [TOOL: push_destination_data] Successfully pushed data")
            print(f"📥 [TOOL: push_destination_data] Server response: {response_data.get('message', 'Success')}")

            return {
                "success": True,
                "response": response_data,
                "error": None
            }

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to push data to destination server: {str(e)}"
            print(f"❌ [TOOL: push_destination_data] {error_msg}")

            # Try to extract error details from response if available
            try:
                if hasattr(e, 'response') and e.response is not None:
                    error_data = e.response.json()
                    error_msg += f" - {error_data.get('message', '')}"
            except:
                pass

            return {
                "success": False,
                "response": None,
                "error": error_msg
            }

        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON response: {str(e)}"
            print(f"❌ [TOOL: push_destination_data] {error_msg}")

            return {
                "success": False,
                "response": None,
                "error": error_msg
            }


# =============================================================================
# Tool Registration Helper
# =============================================================================

def create_middleware_tools(
    source_url: str = "http://localhost:5001",
    destination_url: str = "http://localhost:5002"
) -> tuple:
    """
    Factory function to create both middleware tools

    Args:
        source_url: Base URL of the source Flask server
        destination_url: Base URL of the destination Flask server

    Returns:
        Tuple of (SourceDataFetcherTool, DestinationDataPusherTool)
    """
    fetcher = SourceDataFetcherTool(source_url=source_url)
    pusher = DestinationDataPusherTool(destination_url=destination_url)

    print("🔧 Created middleware tools:")
    print(f"  - {fetcher.name}")
    print(f"  - {pusher.name}")

    return fetcher, pusher


# =============================================================================
# Testing Functions
# =============================================================================

def test_tools():
    """Test function to verify tools work correctly"""
    print("\n" + "=" * 70)
    print("🧪 TESTING AIOS MIDDLEWARE TOOLS")
    print("=" * 70 + "\n")

    # Create tools
    fetcher, pusher = create_middleware_tools()

    # Test 1: Fetch source data
    print("Test 1: Fetching source data...")
    print("-" * 70)
    fetch_result = fetcher.run()

    if fetch_result["success"]:
        print("✅ Fetch test passed!")
        source_data = fetch_result["data"]

        # Test 2: Transform and push data
        print("\n\nTest 2: Transforming and pushing data...")
        print("-" * 70)

        # Manual transformation for testing
        if source_data and "customers" in source_data:
            transformed_users = []
            for customer in source_data["customers"]:
                user = {
                    "fullName": f"{customer['first_name']} {customer['last_name']}",
                    "phoneDetails": {
                        "number": customer["contact_num"].replace("-", ""),
                        "formatted": customer["contact_num"]
                    },
                    "emailAddress": customer["email_addr"],
                    "registrationDate": customer["join_date"],
                    "accountStatus": "active" if customer["status_code"] == "A" else "inactive"
                }
                transformed_users.append(user)

            push_payload = {"users": transformed_users}
            push_result = pusher.run({"payload": push_payload})

            if push_result["success"]:
                print("✅ Push test passed!")
            else:
                print(f"❌ Push test failed: {push_result['error']}")
        else:
            print("❌ No customer data to transform")
    else:
        print(f"❌ Fetch test failed: {fetch_result['error']}")

    print("\n" + "=" * 70)
    print("🧪 TOOL TESTING COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    test_tools()
