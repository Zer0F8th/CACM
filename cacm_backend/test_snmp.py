#!/usr/bin/env python3
"""
Quick test script — polls the Docker SNMP target and prints JSON.

Usage:
    # Start the target first:
    docker compose -f docker-compose.test.yml up -d

    # Then run from the project root:
    uv run python test_snmp.py
    uv run python test_snmp.py --host 10.0.0.1 --community private
"""

import argparse
import asyncio
import sys

from core.snmp_poller import SNMPPoller


async def main() -> int:
    parser = argparse.ArgumentParser(description="Quick SNMP poll test")
    parser.add_argument("--host", default="127.0.0.1", help="Target host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=1161, help="SNMP port (default: 1161 for Docker)")
    parser.add_argument("--community", default="public", help="Community string")
    parser.add_argument(
        "--section",
        default="all",
        choices=["all", "system", "interfaces"],
        help="What to poll",
    )
    args = parser.parse_args()

    poller = SNMPPoller(
        host=args.host,
        port=args.port,
        community=args.community,
        timeout=10,
        retries=1,
    )

    print(f"Polling {args.host}:{args.port} (community={args.community})...\n")

    if args.section == "system":
        result = await poller.async_poll_system()
    elif args.section == "interfaces":
        result = await poller.async_poll_interfaces()
    else:
        result = await poller.async_poll()

    print(result.to_json())

    if result.status == "success":
        print(f"\n✓ Poll succeeded in {result.duration_ms:.0f}ms")
    else:
        print(f"\n✗ Poll failed: {result.error}", file=sys.stderr)

    return 0 if result.status == "success" else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
