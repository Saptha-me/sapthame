"""
Example script demonstrating how to use the Sapthame Conductor.

This example shows:
1. Basic setup with agent URLs
2. Running a research stage with turn-based execution
3. Running a complete orchestration task
"""

import os
from pathlib import Path
from sapthame.orchestrator.conductor import Conductor
from sapthame.orchestrator.utils.turn_logger import TurnLogger


def example_research_stage():
    """Example: Run a research stage with the Conductor."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Research Stage")
    print("="*60)
    
    # Initialize the conductor
    conductor = Conductor(
        model="claude-sonnet-4-5-20250929",  # or your preferred model
        temperature=0.0,
        api_key=os.getenv("ANTHROPIC_API_KEY"),  # Set your API key
    )
    
    # Define agent URLs (replace with your actual agent endpoints)
    agent_urls = [
        "file:///Users/rahuldutta/Documents/saptha-me/saptha.me/agents/market-intel-agent.get-info.json",
        "file:///Users/rahuldutta/Documents/saptha-me/saptha.me/agents/traction-metrics-agent.get-info.json",
        "file:///Users/rahuldutta/Documents/saptha-me/saptha.me/agents/market-opportunity-agent.get-info.json",
    ]
    
    # Setup logging directory (optional)
    logging_dir = Path("./logs")
    logging_dir.mkdir(exist_ok=True)
    
    # Setup the conductor with agents
    conductor.setup(agent_urls=agent_urls, logging_dir=logging_dir)
    
    # Initialize turn logger (optional)
    conductor.turn_logger = TurnLogger(logging_dir / "research_turns")
    
    # Load system message for research stage
    conductor.system_message = conductor._load_research_system_message()
    
    # Run research stage
    research_question = "What are the key market trends in AI-powered healthcare diagnostics?"
    
    result = conductor.run_research_stage(
        client_question=research_question,
        max_turns=10
    )
    
    # Print results
    print("\n" + "="*60)
    print("RESEARCH RESULTS")
    print("="*60)
    print(f"Completed: {result['completed']}")
    print(f"Turns executed: {result['turns_executed']}")
    print(f"Finish message: {result['finish_message']}")
    print(f"\nScratchpad content:\n{result['scratchpad']}")
    print(f"\nTodo status:\n{result['todo']}")
    
    return result


def example_full_orchestration():
    """Example: Run a complete orchestration task."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Full Orchestration")
    print("="*60)
    
    # Initialize the conductor
    conductor = Conductor(
        model="claude-sonnet-4-5-20250929",
        temperature=0.0,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    
    # Define agent URLs
    agent_urls = [
        "file:///Users/rahuldutta/Documents/saptha-me/saptha.me/agents/protocol-orchestrator.get-info.json",
    ]
    
    # Setup logging
    logging_dir = Path("./logs")
    logging_dir.mkdir(exist_ok=True)
    
    # Setup the conductor
    conductor.setup(agent_urls=agent_urls, logging_dir=logging_dir)
    
    # Initialize turn logger
    conductor.turn_logger = TurnLogger(logging_dir / "orchestration_turns")
    
    # Load system message (you can customize this)
    system_msg_path = Path(__file__).parent / "sapthame" / "system_msgs" / "research_turn_based_prompt.md"
    if system_msg_path.exists():
        with open(system_msg_path, 'r', encoding='utf-8') as f:
            conductor.system_message = f.read()
    else:
        conductor.system_message = conductor._load_research_system_message()
    
    # Define the task
    instruction = """
    Analyze the competitive landscape for AI-powered customer service platforms.
    Identify the top 3 competitors, their key features, and market positioning.
    """
    
    # Run the orchestration
    result = conductor.run(
        instruction=instruction,
        max_turns=20
    )
    
    # Print results
    print("\n" + "="*60)
    print("ORCHESTRATION RESULTS")
    print("="*60)
    print(f"Completed: {result['completed']}")
    print(f"Turns executed: {result['turns_executed']}")
    print(f"Finish message: {result['finish_message']}")
    print(f"Max turns reached: {result['max_turns_reached']}")
    
    return result


def example_custom_configuration():
    """Example: Custom configuration with different LLM settings."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Custom Configuration")
    print("="*60)
    
    # Initialize with custom settings
    conductor = Conductor(
        model="gpt-4",  # Use OpenAI model
        temperature=0.2,  # Slightly higher temperature
        api_key=os.getenv("OPENAI_API_KEY"),
        api_base="https://api.openai.com/v1",  # Custom API base
    )
    
    # Agent URLs
    agent_urls = [
        "file:///Users/rahuldutta/Documents/saptha-me/saptha.me/agents/market-intel-agent.get-info.json",
    ]
    
    # Setup
    conductor.setup(agent_urls=agent_urls)
    
    # Load system message
    conductor.system_message = conductor._load_research_system_message()
    
    # Run a simple research task
    result = conductor.run_research_stage(
        client_question="What is the current state of quantum computing?",
        max_turns=5
    )
    
    print(f"\nCompleted: {result['completed']}")
    print(f"Turns: {result['turns_executed']}")
    
    return result


def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("SAPTHAME CONDUCTOR - USAGE EXAMPLES")
    print("="*80)
    
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  WARNING: No API key found!")
        print("Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable")
        print("Example: export ANTHROPIC_API_KEY='your-key-here'")
        return
    
    # Run examples (uncomment the ones you want to run)
    
    # Example 1: Research stage
    example_research_stage()
    
    # Example 2: Full orchestration
    # example_full_orchestration()
    
    # Example 3: Custom configuration
    # example_custom_configuration()
    
    print("\n✓ Examples completed!")
    print("\nTo run an example, uncomment the corresponding line in main()")


if __name__ == "__main__":
    main()
