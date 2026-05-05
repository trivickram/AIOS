"""
AIOS Middleware Agent Implementation

This module implements an intelligent middleware agent using the AIOS SDK
(Cerebrum). The agent:
1. Fetches data from a source server (legacy format) via MCP tools
2. Uses LLM reasoning to transform the data structure
3. Pushes the transformed data to a destination server (modern format)
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from mcp import StdioServerParameters
from cerebrum.llm.apis import llm_chat_with_json_output
from cerebrum.tool.mcp_tool import MCPClient, MCPPool


# =============================================================================
# SYSTEM PROMPTS FOR THE MIDDLEWARE AGENT
# =============================================================================

MAPPING_SYSTEM_PROMPT = """You are an intelligent middleware agent operating within the AIOS (AI Agent Operating System) framework. Your task is to infer a mapping table between a legacy payload and a destination schema.

Guidelines:
- Infer mappings by field names, value types, and example values.
- Include any required transformations (concatenation, formatting, normalization, value mapping).
- Output ONLY the JSON mapping table requested by the schema.
"""

TRANSFORM_SYSTEM_PROMPT = """You are an intelligent middleware agent operating within the AIOS (AI Agent Operating System) framework. Apply the provided mapping table to transform the legacy payload into the destination schema.

Guidelines:
- Follow the mapping table strictly.
- Output ONLY the JSON that matches the required schema.
"""


# =============================================================================
# MIDDLEWARE AGENT CONFIGURATION
# =============================================================================

class MiddlewareAgentConfig:
    """Configuration for the middleware agent."""

    def __init__(
        self,
        llm_name: str = "llama-3.3-70b-versatile",
        llm_backend: str = "groq",
        aios_kernel_url: str = "http://localhost:8000",
        source_server_url: str = "http://localhost:5001",
        destination_server_url: str = "http://localhost:5002",
        mcp_server_path: Optional[str] = None,
        agent_name: str = "middleware_agent",
    ):
        self.llm_name = llm_name
        self.llm_backend = llm_backend
        self.aios_kernel_url = aios_kernel_url
        self.source_server_url = source_server_url
        self.destination_server_url = destination_server_url
        self.agent_name = agent_name

        if mcp_server_path:
            self.mcp_server_path = mcp_server_path
        else:
            self.mcp_server_path = str(Path(__file__).with_name("mcp_tools_server.py"))


# =============================================================================
# MIDDLEWARE AGENT
# =============================================================================

class MiddlewareAgent:
    """Intelligent middleware agent using AIOS SDK + MCP tools."""

    def __init__(self, config: MiddlewareAgentConfig):
        self.config = config
        self.mcp_pool = MCPPool()
        self.mcp_client: Optional[MCPClient] = None
        self.debug = False

    async def start_tools(self) -> None:
        """Start the MCP tool server and connect to it."""
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[self.config.mcp_server_path],
            env={
                "SOURCE_SERVER_URL": self.config.source_server_url,
                "DESTINATION_SERVER_URL": self.config.destination_server_url,
            },
        )

        self.mcp_client = MCPClient(
            name="middleware-tools",
            description="MCP tools for the middleware demo",
            server_params=server_params,
        )
        self.mcp_pool.add_mcp_client("middleware", self.mcp_client)
        await self.mcp_pool.start(["middleware"])

    async def stop_tools(self) -> None:
        """Stop the MCP tool server connection."""
        await self.mcp_pool.stop()

    def _parse_tool_result(self, raw: Any) -> Dict[str, Any]:
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": f"Invalid tool response: {raw}",
                }
        return {
            "success": False,
            "error": f"Unexpected tool response type: {type(raw)}",
        }

    async def fetch_source_data(self) -> Dict[str, Any]:
        if not self.mcp_client:
            return {"success": False, "error": "Tool client not initialized"}
        tool = self.mcp_client.call_tool("fetch_source_data")
        raw = await tool()
        return self._parse_tool_result(raw)

    async def push_destination_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.mcp_client:
            return {"success": False, "error": "Tool client not initialized"}
        tool = self.mcp_client.call_tool("push_destination_data")
        raw = await tool(payload=payload)
        return self._parse_tool_result(raw)

    def _parse_llm_json(self, llm_result: Any) -> Dict[str, Any]:
        if not isinstance(llm_result, dict):
            raise ValueError(f"LLM call returned unexpected result: {llm_result}")

        if llm_result.get("error"):
            raise ValueError(f"LLM call failed: {llm_result['error']}")

        response = llm_result.get("response") or {}
        response_error = response.get("error")
        if response_error:
            raise ValueError(f"LLM call failed: {response_error}")

        response_message = response.get("response_message")
        if response_message is None:
            response_message = llm_result.get("response_message")

        if response_message is None:
            raise ValueError(f"LLM returned empty response_message: {response}")

        payload = response_message
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise ValueError(f"LLM response is not valid JSON: {payload}") from exc

        if not isinstance(payload, dict):
            raise ValueError(f"LLM response must be a JSON object, got {type(payload)}")

        return payload

    def _extract_users(self, payload: Dict[str, Any]) -> Optional[list]:
        if "users" in payload and isinstance(payload["users"], list):
            return payload["users"]
        if "payload" in payload and isinstance(payload["payload"], dict):
            users = payload["payload"].get("users")
            if isinstance(users, list):
                return users
        return None

    def _find_mapping_target(self, mapping: Dict[str, Any], target: str) -> Optional[Dict[str, Any]]:
        for entry in mapping.get("mappings", []):
            if entry.get("target") == target:
                return entry
        return None

    def _resolve_source_value(
        self,
        source_data: Dict[str, Any],
        source_field: str,
        index: int,
    ) -> Optional[str]:
        if not source_field or not isinstance(source_field, str):
            return None

        customers = source_data.get("customers") if isinstance(source_data, dict) else None
        record = None
        if isinstance(customers, list) and index < len(customers):
            if isinstance(customers[index], dict):
                record = customers[index]

        parts = [part for part in source_field.split(".") if part]
        current: Any
        if parts and parts[0] == "customers":
            current = source_data
        else:
            current = record if record is not None else source_data

        for part in parts:
            if part == "customers" and isinstance(current, dict):
                current = current.get("customers")
                continue
            if isinstance(current, list):
                if index >= len(current):
                    return None
                current = current[index]
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None

        if isinstance(current, (str, int, float)):
            return str(current)
        return None

    def _normalize_registration_date(
        self,
        value: Any,
        source_data: Dict[str, Any],
        mapping: Dict[str, Any],
        index: int,
    ) -> Optional[str]:
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            for key in ["date", "value", "iso", "isoDate", "formatted"]:
                if isinstance(value.get(key), str):
                    return value[key]
            year = value.get("year")
            month = value.get("month")
            day = value.get("day")
            if year and month and day:
                return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
        if isinstance(value, (list, tuple)):
            for item in value:
                if isinstance(item, str):
                    return item

        mapping_entry = self._find_mapping_target(mapping, "registrationDate")
        if mapping_entry:
            for field in mapping_entry.get("source_fields", []):
                resolved = self._resolve_source_value(source_data, field, index)
                if resolved:
                    return resolved
        return None

    def _sanitize_payload(
        self,
        payload: Dict[str, Any],
        source_data: Dict[str, Any],
        mapping: Dict[str, Any],
    ) -> Dict[str, Any]:
        users = payload.get("users")
        if not isinstance(users, list):
            return payload

        for idx, user in enumerate(users):
            if not isinstance(user, dict):
                continue
            reg_value = user.get("registrationDate")
            normalized = self._normalize_registration_date(reg_value, source_data, mapping, idx)
            if normalized is not None:
                user["registrationDate"] = normalized

        return payload

    def _needs_correction(self, source_data: Dict[str, Any], payload: Dict[str, Any]) -> bool:
        users = self._extract_users(payload)
        if not users:
            return False

        customers = []
        if isinstance(source_data, dict) and isinstance(source_data.get("customers"), list):
            customers = source_data["customers"]

        status_bad = any(
            user.get("accountStatus") not in {"active", "inactive"}
            for user in users
        )

        name_bad = False
        for idx, user in enumerate(users):
            if idx >= len(customers):
                break
            record = customers[idx]
            if not isinstance(record, dict):
                continue
            first = record.get("first_name") or record.get("given_name")
            last = record.get("last_name") or record.get("surname")
            if first and last:
                full_name = user.get("fullName", "")
                if first not in full_name or last not in full_name:
                    name_bad = True
                    break

        return status_bad or name_bad

    def correct_payload_with_llm(
        self,
        source_data: Dict[str, Any],
        mapping: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "transformed_payload",
                "schema": {
                    "type": "object",
                    "properties": {
                        "payload": {
                            "type": "object",
                            "properties": {
                                "users": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "userId": {"type": "string"},
                                            "fullName": {"type": "string"},
                                            "phoneDetails": {
                                                "type": "object",
                                                "properties": {
                                                    "number": {"type": "string"},
                                                    "formatted": {"type": "string"},
                                                },
                                                "required": ["number", "formatted"],
                                            },
                                            "emailAddress": {"type": "string"},
                                            "registrationDate": {"type": "string"},
                                            "accountStatus": {
                                                "type": "string",
                                                "enum": ["active", "inactive"],
                                            },
                                        },
                                        "required": [
                                            "userId",
                                            "fullName",
                                            "phoneDetails",
                                            "emailAddress",
                                            "registrationDate",
                                            "accountStatus",
                                        ],
                                    },
                                }
                            },
                            "required": ["users"],
                        }
                    },
                    "required": ["payload"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        }

        messages = [
            {
                "role": "system",
                "content": TRANSFORM_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    "The previous transformed payload does not fully apply the mapping table. "
                    "Fix the payload to strictly follow the mapping table and schema. "
                    "Ensure fullName uses both name parts when available, and accountStatus is "
                    "either 'active' or 'inactive'. Return only the corrected JSON.\n\n"
                    f"Mapping table:\n{json.dumps(mapping, indent=2)}\n\n"
                    f"Legacy payload:\n{json.dumps(source_data, indent=2)}\n\n"
                    f"Current transformed payload:\n{json.dumps(payload, indent=2)}"
                ),
            },
        ]

        llm_result = llm_chat_with_json_output(
            agent_name=self.config.agent_name,
            messages=messages,
            base_url=self.config.aios_kernel_url,
            llms=[{
                "name": self.config.llm_name,
                "backend": self.config.llm_backend,
            }],
            response_format=response_format,
        )

        corrected = self._parse_llm_json(llm_result)
        if "payload" in corrected:
            return corrected["payload"]
        if "users" in corrected:
            return corrected

        preview = json.dumps(corrected, indent=2)[:1000]
        raise ValueError(
            "Corrected response missing 'payload' or 'users' key. "
            f"Response preview: {preview}"
        )

    def _get_sample_record(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        customers = source_data.get("customers") if isinstance(source_data, dict) else None
        if isinstance(customers, list) and customers:
            first = customers[0]
            if isinstance(first, dict):
                return first
        return {}

    def _infer_status_source(self, source_data: Dict[str, Any]) -> Optional[str]:
        record = self._get_sample_record(source_data)
        for key in ["status_code", "status", "account_status", "state"]:
            if key in record:
                return key
        return None

    def _normalize_mapping(self, mapping: Any, source_data: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(mapping, dict):
            normalized_keys = {
                (key.strip() if isinstance(key, str) else key): value
                for key, value in mapping.items()
            }
            if normalized_keys != mapping:
                return self._normalize_mapping(normalized_keys, source_data)

            if isinstance(mapping.get("mappings"), list):
                normalized_list = []
                for entry in mapping["mappings"]:
                    if not isinstance(entry, dict):
                        normalized_list.append(entry)
                        continue
                    source_fields = entry.get("source_fields")
                    if source_fields is None:
                        source = entry.get("source")
                        if isinstance(source, list):
                            source_fields = source
                        elif source is None:
                            source_fields = []
                        else:
                            source_fields = [source]
                    target = entry.get("target") or entry.get("destination")
                    if target is None:
                        normalized_list.append(entry)
                        continue
                    normalized_list.append({
                        "source_fields": source_fields,
                        "target": target,
                        "transform": entry.get("transform") or "identity",
                        "notes": entry.get("notes", ""),
                    })
                return {
                    "mappings": normalized_list,
                    "assumptions": mapping.get("assumptions", []),
                }
            if isinstance(mapping.get("payload"), dict):
                return self._normalize_mapping(mapping["payload"], source_data)
            if isinstance(mapping.get("mapping"), list):
                return {
                    "mappings": mapping["mapping"],
                    "assumptions": mapping.get("assumptions", []),
                }
            if isinstance(mapping.get("data"), dict):
                return self._normalize_mapping(mapping["data"], source_data)

            if all(isinstance(value, dict) for value in mapping.values()):
                mappings = []
                for target, spec in mapping.items():
                    source_field = spec.get("source")
                    transform = spec.get("transform")
                    if source_field is None:
                        continue
                    mappings.append({
                        "source_fields": [source_field],
                        "target": target,
                        "transform": transform or "identity",
                        "notes": spec.get("notes", ""),
                    })
                if mappings:
                    return {"mappings": mappings}

            mappings = []
            for target, spec in mapping.items():
                if isinstance(spec, str):
                    mappings.append({
                        "source_fields": [spec],
                        "target": target,
                        "transform": "identity",
                        "notes": "",
                    })
                    continue

                if isinstance(spec, dict):
                    if "source" in spec:
                        mappings.append({
                            "source_fields": [spec["source"]],
                            "target": target,
                            "transform": spec.get("transform") or "identity",
                            "notes": spec.get("notes", ""),
                        })
                        continue

                    if spec and all(isinstance(v, str) for v in spec.values()):
                        # Treat as value map when keys look like codes (e.g., A/I).
                        if target.lower().endswith("status") or all(
                            isinstance(k, str) and len(k) <= 3 for k in spec.keys()
                        ):
                            source_field = self._infer_status_source(source_data) or target
                            mappings.append({
                                "source_fields": [source_field],
                                "target": target,
                                "transform": f"value_map({json.dumps(spec)})",
                                "notes": "",
                            })
                            continue

                        # Treat as nested field map (e.g., phoneDetails.number/formatted).
                        for child_key, child_source in spec.items():
                            mappings.append({
                                "source_fields": [child_source],
                                "target": f"{target}.{child_key}",
                                "transform": "identity",
                                "notes": "",
                            })

            if mappings:
                return {"mappings": mappings}

        if isinstance(mapping, list):
            return {"mappings": mapping}

        raise ValueError(
            "Mapping response missing 'mappings' key and could not be normalized"
        )

    def generate_mapping(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "mapping_table",
                "schema": {
                    "type": "object",
                    "properties": {
                        "mappings": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "source_fields": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "target": {"type": "string"},
                                    "transform": {"type": "string"},
                                    "notes": {"type": "string"},
                                },
                                "required": ["source_fields", "target", "transform"],
                            },
                        },
                        "assumptions": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["mappings"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        }

        messages = [
            {
                "role": "system",
                "content": MAPPING_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    "Infer a mapping table between the legacy payload and the destination schema. "
                    "Destination fields: userId, fullName, phoneDetails.number, phoneDetails.formatted, "
                    "emailAddress, registrationDate, accountStatus.\n\n"
                    f"Legacy payload:\n{json.dumps(source_data, indent=2)}"
                ),
            },
        ]

        llm_result = llm_chat_with_json_output(
            agent_name=self.config.agent_name,
            messages=messages,
            base_url=self.config.aios_kernel_url,
            llms=[{
                "name": self.config.llm_name,
                "backend": self.config.llm_backend,
            }],
            response_format=response_format,
        )

        mapping = self._parse_llm_json(llm_result)
        if self.debug:
            print("[DEBUG] Raw mapping response:\n" + json.dumps(mapping, indent=2))
        try:
            return self._normalize_mapping(mapping, source_data)
        except ValueError as exc:
            preview = json.dumps(mapping, indent=2)[:1000]
            raise ValueError(
                f"Mapping response missing 'mappings' key. Response preview: {preview}"
            ) from exc

    def apply_mapping_with_llm(self, source_data: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "transformed_payload",
                "schema": {
                    "type": "object",
                    "properties": {
                        "payload": {
                            "type": "object",
                            "properties": {
                                "users": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "userId": {"type": "string"},
                                            "fullName": {"type": "string"},
                                            "phoneDetails": {
                                                "type": "object",
                                                "properties": {
                                                    "number": {"type": "string"},
                                                    "formatted": {"type": "string"},
                                                },
                                                "required": ["number", "formatted"],
                                            },
                                            "emailAddress": {"type": "string"},
                                            "registrationDate": {"type": "string"},
                                            "accountStatus": {
                                                "type": "string",
                                                "enum": ["active", "inactive"],
                                            },
                                        },
                                        "required": [
                                            "userId",
                                            "fullName",
                                            "phoneDetails",
                                            "emailAddress",
                                            "registrationDate",
                                            "accountStatus",
                                        ],
                                    },
                                }
                            },
                            "required": ["users"],
                        }
                    },
                    "required": ["payload"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        }

        messages = [
            {
                "role": "system",
                "content": TRANSFORM_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    "Apply the mapping table to transform the legacy payload into the destination format. "
                    "Return only the JSON that matches the required schema. "
                    "Response shape: {\"payload\": {\"users\": [...]}}. "
                    "Use both name parts for fullName when available, and map accountStatus to "
                    "'active' or 'inactive'.\n\n"
                    f"Mapping table:\n{json.dumps(mapping, indent=2)}\n\n"
                    f"Legacy payload:\n{json.dumps(source_data, indent=2)}"
                ),
            },
        ]

        llm_result = llm_chat_with_json_output(
            agent_name=self.config.agent_name,
            messages=messages,
            base_url=self.config.aios_kernel_url,
            llms=[{
                "name": self.config.llm_name,
                "backend": self.config.llm_backend,
            }],
            response_format=response_format,
        )

        payload = self._parse_llm_json(llm_result)
        if self._needs_correction(source_data, payload):
            payload = self.correct_payload_with_llm(source_data, mapping, payload)

        if "payload" in payload:
            return self._sanitize_payload(payload["payload"], source_data, mapping)
        if "users" in payload:
            return self._sanitize_payload(payload, source_data, mapping)

        preview = json.dumps(payload, indent=2)[:1000]
        raise ValueError(
            "LLM response missing 'payload' or 'users' key. "
            f"Response preview: {preview}"
        )

    def transform_with_llm(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        mapping = self.generate_mapping(source_data)
        return self.apply_mapping_with_llm(source_data, mapping)

    async def run(self) -> Dict[str, Any]:
        await self.start_tools()
        try:
            fetch_result = await self.fetch_source_data()
            if not fetch_result.get("success"):
                return {
                    "success": False,
                    "error": fetch_result.get("error", "fetch_source_data failed"),
                }

            source_data = fetch_result.get("data", {})
            transformed_payload = self.transform_with_llm(source_data)

            push_result = await self.push_destination_data(transformed_payload)
            if not push_result.get("success"):
                return {
                    "success": False,
                    "error": push_result.get("error", "push_destination_data failed"),
                }

            return {
                "success": True,
                "records_fetched": len(source_data.get("customers", [])),
                "records_pushed": len(transformed_payload.get("users", [])),
                "destination_response": push_result.get("response"),
            }
        finally:
            await self.stop_tools()


# =============================================================================
# MAIN EXECUTION
# =============================================================================


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AIOS Middleware Agent - Intelligent Data Bridge"
    )
    parser.add_argument(
        "--llm-name",
        default="llama-3.3-70b-versatile",
        help="LLM model to use (default: llama-3.3-70b-versatile)",
    )
    parser.add_argument(
        "--llm-backend",
        default="groq",
        choices=["openai", "anthropic", "gemini", "groq", "ollama", "vllm"],
        help="LLM backend to use (default: groq)",
    )
    parser.add_argument(
        "--aios-kernel-url",
        default="http://localhost:8000",
        help="AIOS kernel URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--source-url",
        default="http://localhost:5001",
        help="Source server URL (default: http://localhost:5001)",
    )
    parser.add_argument(
        "--destination-url",
        default="http://localhost:5002",
        help="Destination server URL (default: http://localhost:5002)",
    )
    parser.add_argument(
        "--mcp-server-path",
        default=None,
        help="Path to mcp_tools_server.py (defaults to middleware_demo/mcp_tools_server.py)",
    )

    args = parser.parse_args()

    config = MiddlewareAgentConfig(
        llm_name=args.llm_name,
        llm_backend=args.llm_backend,
        aios_kernel_url=args.aios_kernel_url,
        source_server_url=args.source_url,
        destination_server_url=args.destination_url,
        mcp_server_path=args.mcp_server_path,
    )

    agent = MiddlewareAgent(config)
    result = asyncio.run(agent.run())

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
