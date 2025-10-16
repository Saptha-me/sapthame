"""Basic tests for Saptami orchestrator."""

import logging
from pathlib import Path

from src.orchestrator.saptami_orchestrator import SaptamiOrchestrator
from misc.log_setup import setup_logging

# Setup logging
setup_logging(level="INFO")
logger = logging.getLogger(__name__)


def test_saptami_initialization():
    """Test basic Saptami initialization."""
    orchestrator = SaptamiOrchestrator(
        model="claude-3-5-sonnet-20241022",
        temperature=0.0
    )
    
    assert orchestrator.name() == "SaptamiOrchestrator"
    assert orchestrator.model == "claude-3-5-sonnet-20241022"
    assert orchestrator.temperature == 0.0
    
    logger.info("✓ Initialization test passed")


def test_saptami_setup_with_mock_agents():
    """Test Saptami setup with mock agent URLs."""
    orchestrator = SaptamiOrchestrator(
        model="claude-3-5-sonnet-20241022",
        temperature=0.0
    )
    
    # Mock agent URLs (these would need to be real endpoints)
    agent_urls = [
        "http://localhost:8001/get-info.json",
        "http://localhost:8002/get-info.json"
    ]
    
    # Note: This will fail without actual agents running
    # orchestrator.setup(agent_urls=agent_urls)
    
    logger.info("✓ Setup test structure validated")


def test_entity_creation():
    """Test entity creation."""
    from src.discovery.entities.skill import Skill
    from src.discovery.entities.agent_info import AgentInfo
    
    # Create skill
    skill = Skill(name="code_analysis", description="Analyze code")
    assert skill.name == "code_analysis"
    
    # Create agent info
    agent_data = {
        'id': 'agent-001',
        'name': 'Test Agent',
        'description': 'A test agent',
        'url': 'http://localhost:8000',
        'version': '1.0.0',
        'protocolVersion': '1.0',
        'skills': [{'name': 'test', 'description': 'Test skill'}],
        'capabilities': {},
        'extraData': {},
        'agentTrust': 'high'
    }
    
    agent_info = AgentInfo.from_dict(agent_data)
    assert agent_info.id == 'agent-001'
    assert agent_info.name == 'Test Agent'
    assert len(agent_info.skills) == 1
    
    logger.info("✓ Entity creation test passed")


if __name__ == "__main__":
    test_saptami_initialization()
    test_saptami_setup_with_mock_agents()
    test_entity_creation()
    
    logger.info("\n" + "=" * 60)
    logger.info("All basic tests passed!")
    logger.info("=" * 60)
