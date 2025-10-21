#!/usr/bin/env python3
"""Minimal example demonstrating Saptha research stage via CLI.

Run this file or use the launch.json configuration for debugging.
"""

import sys

# Set up CLI arguments
sys.argv = [
    "saptami",
    "run",
    "--id", "research_001",
    "--stage", "research",
    "--client-question", "Analyze the market opportunity for AI agent orchestration platforms.",
    "--agent", "market=./agents/market-intel-agent.get-info.json",
    "--agent", "traction=./agents/traction-metrics-agent.get-info.json",
    "--out", "./runs/research_001",
    "--concurrency", "2",
]

# Import and run CLI
from sapthame.cli import main

if __name__ == "__main__":
    main()