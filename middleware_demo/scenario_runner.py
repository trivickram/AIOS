#!/usr/bin/env python3
"""Run mapping scenarios through the AIOS kernel LLM."""

import argparse
import json
from typing import Dict, Any

from middleware_agent import MiddlewareAgent, MiddlewareAgentConfig


def build_payload(customers: list, data_format: str) -> Dict[str, Any]:
    return {
        "status": "success",
        "data_format": data_format,
        "customers": customers,
        "total_count": len(customers),
    }


def scenario_payloads() -> Dict[str, Dict[str, Any]]:
    return {
        "baseline": build_payload(
            [
                {
                    "customer_id": "CUST001",
                    "first_name": "John",
                    "last_name": "Doe",
                    "contact_num": "555-0123",
                    "email_addr": "john.doe@example.com",
                    "join_date": "2020-01-15",
                    "status_code": "A",
                }
            ],
            "legacy_v1",
        ),
        "aliases": build_payload(
            [
                {
                    "cust_id": "CUST101",
                    "given_name": "Ava",
                    "surname": "Li",
                    "phone": "555-1010",
                    "email": "ava.li@example.com",
                    "joined_at": "2021-03-22",
                    "status": "A",
                }
            ],
            "legacy_aliases",
        ),
        "nested_phone": build_payload(
            [
                {
                    "customer_id": "CUST202",
                    "first_name": "Maya",
                    "last_name": "Rao",
                    "contact": {
                        "number": "5550120",
                        "formatted": "555-0120",
                    },
                    "email_addr": "maya.rao@example.com",
                    "join_date": "2022-09-30",
                    "status_code": "I",
                }
            ],
            "legacy_nested_phone",
        ),
        "status_words": build_payload(
            [
                {
                    "customer_id": "CUST303",
                    "first_name": "Noah",
                    "last_name": "Kim",
                    "contact_num": "555-2222",
                    "email_addr": "noah.kim@example.com",
                    "join_date": "2019-11-05",
                    "status_code": "inactive",
                }
            ],
            "legacy_status_words",
        ),
    }


def run_scenario(name: str, payload: Dict[str, Any], agent: MiddlewareAgent) -> None:
    print("=" * 70)
    print(f"Scenario: {name}")
    print("Legacy payload:")
    print(json.dumps(payload, indent=2))
    print("-")

    mapping = agent.generate_mapping(payload)
    print("Mapping table:")
    print(json.dumps(mapping, indent=2))
    print("-")

    transformed = agent.apply_mapping_with_llm(payload, mapping)
    print("Transformed payload:")
    print(json.dumps(transformed, indent=2))
    print("=")


def main() -> int:
    parser = argparse.ArgumentParser(description="AIOS mapping scenario runner")
    parser.add_argument(
        "--scenario",
        default="baseline",
        help="Scenario name (use --list to see options)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available scenarios",
    )
    parser.add_argument(
        "--llm-name",
        default="llama-3.3-70b-versatile",
        help="LLM model name",
    )
    parser.add_argument(
        "--llm-backend",
        default="groq",
        help="LLM backend",
    )
    parser.add_argument(
        "--aios-kernel-url",
        default="http://localhost:8000",
        help="AIOS kernel URL",
    )
    parser.add_argument(
        "--debug-mapping",
        action="store_true",
        help="Print raw LLM mapping response",
    )

    args = parser.parse_args()

    payloads = scenario_payloads()
    if args.list:
        print("Available scenarios:")
        for key in payloads:
            print(f"- {key}")
        return 0

    if args.scenario not in payloads:
        print(f"Unknown scenario: {args.scenario}")
        print("Use --list to see available options.")
        return 1

    config = MiddlewareAgentConfig(
        llm_name=args.llm_name,
        llm_backend=args.llm_backend,
        aios_kernel_url=args.aios_kernel_url,
    )
    agent = MiddlewareAgent(config)
    agent.debug = args.debug_mapping

    run_scenario(args.scenario, payloads[args.scenario], agent)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
