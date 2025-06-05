"""Term processing node (placeholder implementation)."""

from .base import BaseProcessingNode
from ..core.state import ProcessingState, StepResult


class TermProcessingNode(BaseProcessingNode):
    """Node for processing terminology."""
    
    def __init__(self):
        super().__init__(name="term_processing")
    
    def _execute(self, state: ProcessingState) -> ProcessingState:
        """Process terminology in subtitles (placeholder implementation)."""
        # For now, just pass through the Chinese subtitles
        # TODO: Implement actual term processing logic
        return state
    
    def _update_state_result(self, state: ProcessingState, result: StepResult) -> ProcessingState:
        """Update the state with term processing result."""
        state["term_processing_result"] = result
        return state 