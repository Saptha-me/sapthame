"""Parser for extracting actions from LLM output."""

import re
import logging
from typing import List, Tuple, Optional
from xml.etree import ElementTree as ET

from sapthame.orchestrator.actions.entities.actions import (
    Action,
    QueryAgentAction,
    UpdateScratchpadAction,
    UpdateTodoAction,
    FinishStageAction
)

logger = logging.getLogger(__name__)


class ActionParser:
    """Parses LLM output to extract structured actions."""
    
    def parse_response(self, llm_output: str) -> Tuple[List[Action], List[str], bool]:
        """Parse LLM response to extract actions.
        
        Args:
            llm_output: Raw LLM output text
            
        Returns:
            Tuple of (actions, parsing_errors, found_action_attempt)
        """
        actions = []
        parsing_errors = []
        found_action_attempt = False
        
        # Find all action blocks using regex
        action_pattern = r'<action\s+type="([^"]+)">(.*?)</action>'
        matches = re.finditer(action_pattern, llm_output, re.DOTALL)
        
        for match in matches:
            found_action_attempt = True
            action_type = match.group(1)
            action_content = match.group(2).strip()
            
            try:
                action = self._parse_action(action_type, action_content)
                if action:
                    actions.append(action)
            except Exception as e:
                error_msg = f"Failed to parse {action_type} action: {str(e)}"
                logger.error(error_msg)
                parsing_errors.append(error_msg)
        
        return actions, parsing_errors, found_action_attempt
    
    def _parse_action(self, action_type: str, content: str) -> Optional[Action]:
        """Parse a specific action type.
        
        Args:
            action_type: Type of action (query_agent, update_scratchpad, etc.)
            content: XML content inside the action tag
            
        Returns:
            Parsed Action object or None
        """
        try:
            # Wrap content in a root element for parsing
            xml_str = f"<root>{content}</root>"
            root = ET.fromstring(xml_str)
            
            if action_type == "query_agent":
                return QueryAgentAction(
                    agent_id=self._get_text(root, "agent_id"),
                    query=self._get_text(root, "query"),
                    context_id=self._get_text(root, "context_id", required=False)
                )
            
            elif action_type == "update_scratchpad":
                return UpdateScratchpadAction(
                    content=self._get_text(root, "content"),
                    operation=self._get_text(root, "operation", default="append")
                )
            
            elif action_type == "update_todo":
                return UpdateTodoAction(
                    item=self._get_text(root, "item"),
                    operation=self._get_text(root, "operation", default="add"),
                    index=self._get_int(root, "index", required=False)
                )
            
            elif action_type == "finish_stage":
                return FinishStageAction(
                    message=self._get_text(root, "message"),
                    summary=self._get_text(root, "summary")
                )
            
            else:
                logger.warning(f"Unknown action type: {action_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error parsing action: {e}")
            raise
    
    def _get_text(self, root: ET.Element, tag: str, required: bool = True, default: str = "") -> str:
        """Extract text from XML element."""
        elem = root.find(tag)
        if elem is not None and elem.text:
            return elem.text.strip()
        if required:
            raise ValueError(f"Required tag '{tag}' not found or empty")
        return default
    
    def _get_int(self, root: ET.Element, tag: str, required: bool = True, default: Optional[int] = None) -> Optional[int]:
        """Extract integer from XML element."""
        elem = root.find(tag)
        if elem is not None and elem.text:
            return int(elem.text.strip())
        if required:
            raise ValueError(f"Required tag '{tag}' not found or empty")
        return default
