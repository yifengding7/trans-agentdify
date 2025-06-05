"""Main Video Subtitle Agent using LangGraph workflow."""

import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from loguru import logger

from .state import ProcessingState, ConfigModel, create_initial_state
from ..nodes import (
    AudioExtractionNode,
    SpeechToTextNode, 
    TranslationNode,
    TermProcessingNode,
    SubtitleMergeNode,
    TextToSpeechNode,
    VideoMuxingNode,
)
from ..utils.device import detect_device
from ..utils.file_utils import create_temp_directory, cleanup_temp_files


class VideoSubtitleAgent:
    """Main agent for video subtitle processing using LangGraph."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Video Subtitle Agent.
        
        Args:
            config: Configuration dictionary
        """
        # Validate and set configuration
        self.config = ConfigModel(**(config or {}))
        
        # Auto-detect device if set to "auto"
        if self.config.device == "auto":
            self.config.device = detect_device()
            
        # Setup logging
        self._setup_logging()
        
        # Initialize workflow
        self.workflow = self._build_workflow()
        
        logger.info(f"VideoSubtitleAgent initialized with device: {self.config.device}")
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        logger.remove()  # Remove default handler
        
        # Console logging
        logger.add(
            sink=lambda msg: print(msg, end=""),
            level=self.config.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True
        )
        
        # File logging if specified
        if self.config.log_file:
            logger.add(
                self.config.log_file,
                level=self.config.log_level,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                rotation="10 MB",
                retention="1 week"
            )
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        
        # Create workflow graph
        workflow = StateGraph(ProcessingState)
        
        # Initialize nodes
        nodes = {
            "audio_extraction": AudioExtractionNode(),
            "speech_to_text": SpeechToTextNode(),
            "translation": TranslationNode(),
            "term_processing": TermProcessingNode(),
            "subtitle_merge": SubtitleMergeNode(),
            "text_to_speech": TextToSpeechNode(),
            "video_muxing": VideoMuxingNode(),
        }
        
        # Add nodes to workflow
        for name, node in nodes.items():
            workflow.add_node(name, node)
        
        # Set entry point
        workflow.set_entry_point("audio_extraction")
        
        # Define the workflow edges
        workflow.add_edge("audio_extraction", "speech_to_text")
        workflow.add_edge("speech_to_text", "translation")
        
        # Conditional edge for term processing
        workflow.add_conditional_edges(
            "translation",
            self._should_process_terms,
            {
                "process_terms": "term_processing",
                "skip_terms": "subtitle_merge"
            }
        )
        
        workflow.add_edge("term_processing", "subtitle_merge")
        
        # Conditional edge for TTS
        workflow.add_conditional_edges(
            "subtitle_merge", 
            self._should_generate_tts,
            {
                "generate_tts": "text_to_speech",
                "skip_tts": "video_muxing"
            }
        )
        
        workflow.add_edge("text_to_speech", "video_muxing")
        workflow.add_edge("video_muxing", END)
        
        # Compile workflow
        return workflow.compile()
    
    def _should_process_terms(self, state: ProcessingState) -> str:
        """Determine if term processing should be performed."""
        config = state["config"]
        if config.get("enable_term_processing", True) and config.get("term_dictionary_path"):
            return "process_terms"
        return "skip_terms"
    
    def _should_generate_tts(self, state: ProcessingState) -> str:
        """Determine if TTS should be generated."""
        config = state["config"]
        if config.get("enable_tts", False):
            return "generate_tts"
        return "skip_tts"
    
    def process_video(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        working_dir: Optional[str] = None,
        **kwargs
    ) -> ProcessingState:
        """Process a video file to generate subtitles.
        
        Args:
            input_path: Path to input video file
            output_path: Path for output video file (optional)
            working_dir: Working directory for temporary files (optional)
            **kwargs: Additional configuration options
            
        Returns:
            Final processing state with results
        """
        
        # Validate input
        input_path = Path(input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Input video not found: {input_path}")
        
        # Setup working directory
        if working_dir is None:
            working_dir = tempfile.mkdtemp(prefix="video_subtitle_")
        else:
            Path(working_dir).mkdir(parents=True, exist_ok=True)
        
        # Setup output path
        if output_path is None:
            output_path = str(input_path.parent / f"{input_path.stem}_subtitled{input_path.suffix}")
        
        # Merge configuration
        config = {**self.config.dict(), **kwargs}
        
        # Create initial state
        initial_state = create_initial_state(
            input_video_path=str(input_path),
            working_directory=working_dir,
            config=config
        )
        
        # Add additional state fields for new workflow
        initial_state.update({
            "input_path": str(input_path),  # Add input_path for new nodes
            "output_path": output_path,
            "temp_dir": working_dir
        })
        
        logger.info(f"Starting video processing: {input_path}")
        logger.info(f"Working directory: {working_dir}")
        logger.info(f"Output path: {output_path}")
        
        try:
            # Run the workflow
            final_state = self.workflow.invoke(
                initial_state,
                config=RunnableConfig(
                    configurable={
                        "thread_id": f"video_processing_{datetime.now().isoformat()}"
                    }
                )
            )
            
            # Update completion time
            final_state["processing_completed_at"] = datetime.now().isoformat()
            
            # Log results
            if final_state["should_continue"] and not final_state["errors"]:
                logger.success(f"Video processing completed successfully")
                logger.success(f"Output: {final_state.get('final_video_path', output_path)}")
            else:
                logger.error(f"Video processing failed with {len(final_state['errors'])} errors")
                for error in final_state["errors"]:
                    logger.error(f"  - {error}")
            
            return final_state
            
        except Exception as e:
            logger.exception(f"Unexpected error during video processing: {e}")
            raise
        
        finally:
            # Cleanup temporary files if needed
            if working_dir and working_dir.startswith(tempfile.gettempdir()):
                try:
                    cleanup_temp_files(working_dir)
                    logger.debug(f"Cleaned up temporary directory: {working_dir}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temporary directory {working_dir}: {e}")
    
    def process_batch(
        self,
        input_paths: List[str],
        output_dir: str,
        **kwargs
    ) -> List[ProcessingState]:
        """Process multiple video files.
        
        Args:
            input_paths: List of input video file paths
            output_dir: Directory for output files
            **kwargs: Additional configuration options
            
        Returns:
            List of processing states for each video
        """
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        
        logger.info(f"Starting batch processing of {len(input_paths)} videos")
        
        for i, input_path in enumerate(input_paths, 1):
            logger.info(f"Processing video {i}/{len(input_paths)}: {input_path}")
            
            try:
                input_path = Path(input_path)
                output_path = output_dir / f"{input_path.stem}_subtitled{input_path.suffix}"
                
                result = self.process_video(
                    input_path=str(input_path),
                    output_path=str(output_path),
                    **kwargs
                )
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to process {input_path}: {e}")
                # Create a failed state
                failed_state = create_initial_state(
                    input_video_path=str(input_path),
                    working_directory="",
                    config=kwargs
                )
                failed_state["should_continue"] = False
                failed_state["errors"] = [str(e)]
                results.append(failed_state)
        
        # Summary
        successful = sum(1 for r in results if r["should_continue"] and not r["errors"])
        logger.info(f"Batch processing completed: {successful}/{len(input_paths)} successful")
        
        return results
    
    def get_workflow_graph(self) -> str:
        """Get a visual representation of the workflow graph.
        
        Returns:
            Mermaid diagram representation
        """
        return """
        graph TD
            A[Audio Extraction] --> B[Speech to Text]
            B --> C[Translation]
            C --> D{Enable Term Processing?}
            D -->|Yes| E[Term Processing]
            D -->|No| F[Subtitle Merge]
            E --> F
            F --> G{Enable TTS?}
            G -->|Yes| H[Text to Speech]
            G -->|No| I[Video Muxing]
            H --> I
            I --> J[Complete]
            
            style A fill:#e1f5fe
            style J fill:#e8f5e8
            style B,C,E,F,H,I fill:#fff3e0
            style D,G fill:#f3e5f5
        """ 