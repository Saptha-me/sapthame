"""Base phase class with common structure."""


from abc import ABC, abstractmethod
from typing import Callable


class BasePhase(ABC):
    """Abstract base class for all phases."""
    
    def __init__(
        self,
        llm_client: Callable,
        prompt_loader: Callable
    ):
        """Initialize phase.
        
        Args:
            llm_client: Function to call LLM
            prompt_loader: Function to load phase-specific prompt
        """
        self.llm_client = llm_client
        self.prompt_loader = prompt_loader
    
    def execute(self, *args, **kwargs) -> str:
        """Execute phase with logging and common flow.
        
        Returns:
            Phase output text
        """
        logger.info(f"{self.get_emoji()} {self.get_phase_name()}: {self.get_start_message()}...")
        
        # Load system prompt
        system_prompt = self.prompt_loader()
        
        # Build user message (phase-specific)
        user_message = self._build_user_message(*args, **kwargs)
        
        # Get LLM response
        output = self.llm_client(user_message, system_prompt)
        
        logger.info(f"{self.get_emoji()} {self.get_phase_name()}: {self.get_complete_message()}")
        logger.debug(f"{self.get_phase_name()} output: {output[:200]}...")
        
        return output
    
    @abstractmethod
    def _build_user_message(self, *args, **kwargs) -> str:
        """Build user message for this phase.
        
        Must be implemented by subclasses.
        
        Returns:
            Formatted user message
        """
        pass
    
    @abstractmethod
    def get_phase_name(self) -> str:
        """Get the name of this phase."""
        pass
    
    @abstractmethod
    def get_emoji(self) -> str:
        """Get the emoji for this phase."""
        pass
    
    @abstractmethod
    def get_start_message(self) -> str:
        """Get the start message for this phase."""
        pass
    
    @abstractmethod
    def get_complete_message(self) -> str:
        """Get the completion message for this phase."""
        pass
    
    def _build_sections(self, *sections: tuple[str, str]) -> str:
        """Helper to build formatted message sections.
        
        Args:
            sections: Tuples of (header, content)
            
        Returns:
            Formatted message with sections
        """
        parts = []
        for header, content in sections:
            parts.append(f"## {header}")
            parts.append(content)
            parts.append("")
        return "\n".join(parts)
