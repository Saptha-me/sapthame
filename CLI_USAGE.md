# Saptami CLI Usage Guide

## Overview

Saptami provides a multi-stage orchestration workflow for coordinating AI agents:

1. **Research Stage**: Analyze the problem and gather context using multiple agents
2. **Plan Stage**: Create a detailed implementation plan based on research
3. **Implement Stage**: Execute the plan using orchestrated agents

## Installation

```bash
# Install dependencies
pip install -e .

# Or with uv
uv pip install -e .
```

## Command Structure

```bash
saptami run \
  --id <unique_run_id> \
  --stage <research|plan|implement> \
  --client-question "<your question>" \
  [--agent <name>=<path/to/config.json>] \
  [--plan-in <path/to/plan.md>] \
  [--plan-out <path/to/plan.md>] \
  [--out <output_directory>] \
  [--concurrency <N>] \
  [--deadline-sec <N>]
```

## Stage 1: Research

Analyze a problem by coordinating multiple specialized agents.

### Example: VC Pitch Deck Analysis

```bash
saptami run \
  --id vc_pitchdeck_research_2025_10_17 \
  --stage research \
  --client-question "Summarize market context, market opportunity and traction for each uploaded AI deck." \
  --agent market=./agents/market-intel-agent.get-info.json \
  --agent opp=./agents/market-opportunity-agent.get-info.json \
  --agent traction=./agents/traction-metrics-agent.get-info.json \
  --concurrency 8 \
  --deadline-sec 90 \
  --out ./runs/vc_pitchdeck_research_2025_10_17
```

**What happens:**
- Saptami discovers the 3 agents and their capabilities
- Executes research phase to analyze the question
- Coordinates agents to gather market, opportunity, and traction data
- Saves results to `./runs/vc_pitchdeck_research_2025_10_17/research_results.json`

**Output:**
- `research_results.json`: Complete research findings
- `run_metadata.json`: Run configuration and metadata

### Example: Healthcare Protocol Research

```bash
saptami run \
  --id hc_2025_10_17_sepsis_research \
  --stage research \
  --client-question "Research best practices for sepsis protocol implementation across multiple hospital sites" \
  --agent clinical=./agents/clinical-research-agent.get-info.json \
  --agent quality=./agents/quality-metrics-agent.get-info.json \
  --concurrency 4 \
  --out ./runs/hc_2025_10_17_sepsis_research
```

## Stage 2: Plan

Create or update an implementation plan based on research and requirements.

### Example: Create New Plan

```bash
saptami run \
  --id hc_2025_10_17_sepsis_plan \
  --stage plan \
  --plan-out ./plans/2025-08-01_sepsis_v2.md \
  --client-question "Create implementation plan for sepsis protocol rollout across 3 sites"
```

**What happens:**
- Saptami executes planning phase
- Creates detailed implementation plan with phases
- Saves plan to specified output file

### Example: Update Existing Plan

```bash
saptami run \
  --id hc_2025_10_17_sepsis_plan \
  --stage plan \
  --plan-in ./plans/2025-08-01_sepsis_v2.md \
  --plan-out ./plans/2025-08-01_sepsis_v2.md \
  --client-question "Phase rollout across 3 sites; include training & monitoring metrics"
```

**What happens:**
- Reads existing plan from `--plan-in`
- Updates plan based on new requirements
- Saves updated plan to `--plan-out`

**Output:**
- Updated plan file with new requirements
- `plan_results.json`: Planning phase results

## Stage 3: Implement

Execute an implementation plan using orchestrated agents.

### Example: Execute Plan

```bash
saptami run \
  --id hc_2025_10_18_sepsis_impl \
  --stage implement \
  --plan-in ./plans/2025-08-01_sepsis_v2.md \
  --agent impl=./agents/protocol-orchestrator.get-info.json \
  --out ./runs/hc_2025_10_18_sepsis_impl
```

**What happens:**
- Reads implementation plan from `--plan-in`
- Discovers and coordinates implementation agents
- Executes plan steps sequentially
- Saves results and logs

**Output:**
- `implementation_results.json`: Complete implementation results
- `run_metadata.json`: Run configuration
- Detailed execution logs

## Complete Workflow Example

### 1. Research Phase
```bash
saptami run \
  --id product_launch_2025_10_17 \
  --stage research \
  --client-question "Analyze market readiness for AI-powered code review tool" \
  --agent market=./agents/market-intel-agent.get-info.json \
  --agent competitor=./agents/competitor-analysis-agent.get-info.json \
  --agent tech=./agents/tech-trends-agent.get-info.json \
  --concurrency 8 \
  --out ./runs/product_launch_research
```

### 2. Planning Phase
```bash
saptami run \
  --id product_launch_2025_10_17_plan \
  --stage plan \
  --plan-out ./plans/product_launch_2025_10_17.md \
  --client-question "Create go-to-market plan based on research findings"
```

### 3. Implementation Phase
```bash
saptami run \
  --id product_launch_2025_10_18_impl \
  --stage implement \
  --plan-in ./plans/product_launch_2025_10_17.md \
  --agent marketing=./agents/marketing-agent.get-info.json \
  --agent content=./agents/content-creator-agent.get-info.json \
  --agent analytics=./agents/analytics-agent.get-info.json \
  --out ./runs/product_launch_impl
```

## Agent Configuration Format

Agent configuration files follow the A2A protocol `get-info.json` format:

```json
{
  "id": "agent-id",
  "name": "Agent Name",
  "description": "What this agent does",
  "url": "http://localhost:8001",
  "version": "1.0.0",
  "protocolVersion": "1.0",
  "skills": [
    {
      "name": "skill_name",
      "description": "What this skill does"
    }
  ],
  "capabilities": {
    "key": "value"
  },
  "extraData": {
    "specialization": "domain"
  },
  "agentTrust": "high"
}
```

## Output Structure

Each run creates an output directory with:

```
./runs/<run_id>/
├── run_metadata.json          # Run configuration
├── research_results.json      # Research stage output (if applicable)
├── plan_results.json          # Planning stage output (if applicable)
├── implementation_results.json # Implementation stage output (if applicable)
└── logs/                      # Detailed execution logs
```

## Options Reference

### Required Options
- `--id`: Unique identifier for this run
- `--stage`: Stage to execute (research, plan, implement)
- `--client-question`: The question or task to execute

### Stage-Specific Options

**Research Stage:**
- `--agent`: One or more agents (format: `name=path/to/config.json`)
- `--concurrency`: Number of concurrent agent calls (default: 1)
- `--deadline-sec`: Execution deadline in seconds

**Plan Stage:**
- `--plan-in`: Input plan file (for updates)
- `--plan-out`: Output plan file (required)

**Implement Stage:**
- `--plan-in`: Input plan file (required)
- `--agent`: One or more agents (format: `name=path/to/config.json`)

### Common Options
- `--out`: Output directory (default: `./runs/<run_id>`)

## Tips

1. **Use descriptive run IDs**: Include date and project name for easy tracking
2. **Start with research**: Always begin with research stage to gather context
3. **Iterate on plans**: Use `--plan-in` and `--plan-out` to refine plans
4. **Monitor output**: Check `run_metadata.json` and result files for details
5. **Agent naming**: Use short, memorable names for agents in `--agent` flags

## Troubleshooting

### "Agent config not found"
- Verify the path to your agent configuration file
- Ensure the file is valid JSON

### "Plan file not found"
- Check the path specified in `--plan-in`
- Ensure the file exists before running implement stage

### "Stage requires agents"
- Research and implement stages require at least one `--agent` flag
- Add appropriate agent configurations

### "Plan stage requires --plan-out"
- Planning stage must specify where to save the plan
- Add `--plan-out` with desired output path

## Examples Directory

See the `agents/` directory for example agent configurations:
- `market-intel-agent.get-info.json`
- `market-opportunity-agent.get-info.json`
- `traction-metrics-agent.get-info.json`
- `protocol-orchestrator.get-info.json`

See the `plans/` directory for example plans:
- `2025-08-01_sepsis_v2.md`
