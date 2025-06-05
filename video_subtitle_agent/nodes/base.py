"""Base class for all processing nodes."""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger

from ..core.state import ProcessingState, StepResult, ProcessingStatus
from ..utils.exceptions import ProcessingError, RetryableError


class BaseProcessingNode(ABC):
    """Base class for all processing nodes in the workflow."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, name: Optional[str] = None, max_retries: int = 3, retry_delay: float = 1.0):
        """Initialize the processing node.
        
        Args:
            config: Configuration dictionary for the node
            name: Name of the processing node (legacy parameter)
            max_retries: Maximum number of retries on failure
            retry_delay: Delay between retries in seconds
        """
        # Handle legacy constructor calls
        if isinstance(config, str):
            # Old constructor: BaseProcessingNode(name)
            self.name = config
            self.config = {}
        else:
            # New constructor: BaseProcessingNode(config)
            self.config = config or {}
            self.name = name or getattr(self, 'name', 'unknown_node')
        
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process method for simple dict-based workflow.
        
        This method should be implemented by subclasses for simple workflows.
        For complex workflows, use the _execute method instead.
        
        Args:
            state: Processing state as dictionary
            
        Returns:
            Updated processing state as dictionary
        """
        # Default implementation: convert to ProcessingState and use _execute
        processing_state = self._dict_to_processing_state(state)
        result_state = self._execute(processing_state)
        return self._processing_state_to_dict(result_state)
    
    def _dict_to_processing_state(self, state: Dict[str, Any]) -> ProcessingState:
        """Convert dictionary state to ProcessingState."""
        # Create a minimal ProcessingState structure
        return {
            "should_continue": state.get("should_continue", True),
            "current_step": state.get("current_step", ""),
            "errors": state.get("errors", []),
            "config": state.get("config", self.config),
            **state
        }
    
    def _processing_state_to_dict(self, state: ProcessingState) -> Dict[str, Any]:
        """Convert ProcessingState to dictionary."""
        # Return as regular dictionary
        return dict(state)
    
    def __call__(self, state: ProcessingState) -> ProcessingState:
        """Execute the processing node with error handling and retry logic."""
        
        if not state["should_continue"]:
            logger.info(f"Skipping {self.name} - processing stopped")
            return self._mark_skipped(state)
        
        state["current_step"] = self.name
        logger.info(f"Starting {self.name}")
        
        start_time = time.time()
        retries = 0
        
        while retries <= self.max_retries:
            try:
                # Execute the actual processing logic
                result_state = self._execute(state)
                
                # Calculate processing time
                processing_time = time.time() - start_time
                
                # Mark as completed
                result = StepResult(
                    step_name=self.name,
                    status=ProcessingStatus.COMPLETED,
                    processing_time=processing_time,
                    metadata=self._get_metadata(result_state)
                )
                
                result_state = self._update_state_result(result_state, result)
                logger.success(f"Completed {self.name} in {processing_time:.2f}s")
                
                return result_state
                
            except RetryableError as e:
                retries += 1
                if retries <= self.max_retries:
                    logger.warning(f"{self.name} failed (attempt {retries}/{self.max_retries + 1}): {e}")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    logger.error(f"{self.name} failed after {self.max_retries + 1} attempts")
                    return self._mark_failed(state, str(e))
                    
            except ProcessingError as e:
                logger.error(f"{self.name} failed with non-retryable error: {e}")
                return self._mark_failed(state, str(e))
                
            except Exception as e:
                logger.exception(f"Unexpected error in {self.name}: {e}")
                return self._mark_failed(state, f"Unexpected error: {e}")
        
        return self._mark_failed(state, "Max retries exceeded")
    
    def _execute(self, state: ProcessingState) -> ProcessingState:
        """Execute the actual processing logic.
        
        This method should be implemented by subclasses to perform the
        specific processing task.
        
        Args:
            state: Current processing state
            
        Returns:
            Updated processing state
            
        Raises:
            ProcessingError: For non-retryable errors
            RetryableError: For retryable errors
        """
        # Default implementation: use the new process method
        try:
            state_dict = dict(state)
            result_dict = self.process(state_dict)
            state.update(result_dict)
            return state
        except Exception as e:
            raise ProcessingError(f"Processing failed in {self.name}: {e}")
    
    def _get_metadata(self, state: ProcessingState) -> Dict[str, Any]:
        """Get metadata for the step result.
        
        Can be overridden by subclasses to provide specific metadata.
        """
        return {}
    
    def _update_state_result(self, state: ProcessingState, result: StepResult) -> ProcessingState:
        """Update the state with the step result.
        
        This method should be overridden by subclasses to update the appropriate
        field in the state.
        """
        return state
    
    def _mark_skipped(self, state: ProcessingState) -> ProcessingState:
        """Mark the step as skipped."""
        result = StepResult(
            step_name=self.name,
            status=ProcessingStatus.SKIPPED
        )
        return self._update_state_result(state, result)
    
    def _mark_failed(self, state: ProcessingState, error_message: str) -> ProcessingState:
        """Mark the step as failed and stop processing."""
        result = StepResult(
            step_name=self.name,
            status=ProcessingStatus.FAILED,
            error_message=error_message
        )
        
        state["should_continue"] = False
        state["errors"].append(f"{self.name}: {error_message}")
        
        return self._update_state_result(state, result)
    
    def _ensure_directory(self, path: Path) -> None:
        """Ensure that the directory for the given path exists."""
        path.parent.mkdir(parents=True, exist_ok=True)
    
    def _validate_input_file(self, file_path: str) -> Path:
        """Validate that input file exists and is readable."""
        path = Path(file_path)
        if not path.exists():
            raise ProcessingError(f"Input file does not exist: {file_path}")
        if not path.is_file():
            raise ProcessingError(f"Input path is not a file: {file_path}")
        return path
    
    def _get_config_value(self, state: ProcessingState, key: str, default: Any = None) -> Any:
        """Get configuration value from state."""
        return state["config"].get(key, default) 