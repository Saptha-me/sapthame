"""
Saptha - Distributed Agent Orchestrator Demo
"""

import asyncio
import uuid
from datetime import datetime

from saptha.context.manager import ContextManager
from saptha.core.orchestrator import DistributedOrchestrator
from saptha.core.types import AgentCapability, AgentInfo, Message
from saptha.routing.router import TaskRouter


async def demo_orchestrator():
    """Demonstrate the distributed orchestrator functionality."""
    print("🚀 Saptha - Distributed Agent Orchestrator")
    print("=" * 50)
    
    # Initialize context manager (would use real PostgreSQL in production)
    database_url = "postgresql+asyncpg://user:password@localhost:5432/saptha"
    context_manager = ContextManager(database_url)
    
    try:
        # Initialize (this would create tables in real PostgreSQL)
        print("📊 Initializing context manager...")
        await context_manager.initialize()
        
        # Create orchestrator
        task_router = TaskRouter()
        orchestrator = DistributedOrchestrator(context_manager, task_router)
        await orchestrator.initialize()
        
        print("✅ Orchestrator initialized successfully!")
        
        # Register some demo agents
        print("\n🤖 Registering demo agents...")
        
        demo_agents = [
            AgentInfo(
                id="web-search-agent",
                name="Web Search Agent",
                description="Searches the web for current information",
                capabilities=[AgentCapability.WEB_SEARCH, AgentCapability.TEXT_PROCESSING],
                endpoint="http://localhost:8001"
            ),
            AgentInfo(
                id="knowledge-agent",
                name="Knowledge Base Agent", 
                description="Provides information from knowledge base",
                capabilities=[AgentCapability.KNOWLEDGE_BASE, AgentCapability.REASONING],
                endpoint="http://localhost:8002"
            ),
            AgentInfo(
                id="code-agent",
                name="Code Generation Agent",
                description="Generates and analyzes code",
                capabilities=[AgentCapability.CODE_GENERATION, AgentCapability.TEXT_PROCESSING],
                endpoint="http://localhost:8003"
            )
        ]
        
        for agent in demo_agents:
            await context_manager.register_agent(agent)
            print(f"   ✓ Registered {agent.name} ({agent.id})")
        
        # Demo task routing
        print("\n🎯 Demonstrating task routing...")
        
        demo_messages = [
            "What is the latest news about AI developments?",
            "Explain how neural networks work",
            "Write a Python function to calculate fibonacci numbers",
            "Search for the current weather in San Francisco and analyze the data"
        ]
        
        for i, message_content in enumerate(demo_messages, 1):
            print(f"\n📝 Demo Message {i}: {message_content}")
            
            # Analyze requirements
            capabilities = task_router.analyze_task_requirements(message_content)
            execution_mode = task_router.determine_execution_mode(message_content, capabilities)
            
            print(f"   🔍 Inferred capabilities: {[cap.value for cap in capabilities]}")
            print(f"   ⚙️  Execution mode: {execution_mode.value}")
            
            # Get available agents
            available_agents = await context_manager.get_available_agents()
            
            # Route task (this would normally execute agents, but we'll just show routing)
            try:
                message = Message(content=message_content, role="user")
                from saptha.core.types import TaskRequest
                task_request = TaskRequest(
                    message=message,
                    required_capabilities=capabilities,
                    execution_mode=execution_mode
                )
                
                selected_agents = await task_router.route_task(task_request, available_agents)
                print(f"   🎯 Selected agents: {[agent.name for agent in selected_agents]}")
                
            except Exception as e:
                print(f"   ❌ Routing failed: {str(e)}")
        
        print("\n🏁 Demo completed successfully!")
        print("\nNote: This is a demonstration of the orchestration logic.")
        print("In production, agents would be running as separate services")
        print("and the orchestrator would communicate with them via A2A protocol.")
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        print("Note: This demo requires PostgreSQL. The orchestrator is designed")
        print("to work with real database and agent services.")
    
    finally:
        # Cleanup
        try:
            await orchestrator.close()
        except:
            pass


def main():
    """Main entry point."""
    print("Starting Saptha Orchestrator Demo...")
    asyncio.run(demo_orchestrator())


if __name__ == "__main__":
    main()
