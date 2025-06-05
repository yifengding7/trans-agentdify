"""State management for the video subtitle processing workflow."""

from typing import Dict, List, Optional, Any, TypedDict
from pathlib import Path
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ProcessingStatus(str, Enum):
    """Processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepResult(BaseModel):
    """Result of a processing step."""
    step_name: str
    status: ProcessingStatus
    output_path: Optional[Path] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_time: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ProcessingState(TypedDict):
    """State structure for the video subtitle processing workflow."""
    
    # Input files
    input_video_path: str
    working_directory: str
    
    # Configuration
    config: Dict[str, Any]
    
    # Processing steps results
    audio_extraction_result: Optional[StepResult]
    speech_to_text_result: Optional[StepResult]
    translation_result: Optional[StepResult] 
    term_processing_result: Optional[StepResult]
    subtitle_merge_result: Optional[StepResult]
    text_to_speech_result: Optional[StepResult]
    video_muxing_result: Optional[StepResult]
    
    # File paths
    extracted_audio_path: Optional[str]
    english_srt_path: Optional[str]
    chinese_srt_path: Optional[str]
    merged_srt_path: Optional[str]
    final_video_path: Optional[str]
    
    # Metadata
    errors: List[str]
    warnings: List[str]
    processing_started_at: Optional[str]
    processing_completed_at: Optional[str]
    
    # State control
    should_continue: bool
    retry_count: int
    current_step: Optional[str]


class ConfigModel(BaseModel):
    """Configuration model with validation."""
    
    # Device settings
    device: str = "auto"  # auto, cpu, mps, cuda
    
    # Model settings
    stt_model: str = "seamlessM4T_v2_large"
    translation_model: str = "seamlessM4T_v2_large" 
    tts_model: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    
    # Audio settings
    audio_sample_rate: int = 16000
    audio_channels: int = 1
    
    # Language settings
    source_language: str = "eng"
    target_language: str = "cmn"
    tts_language: str = "zh-cn"
    tts_speaker: str = "zh-CN-XiaoxiaoNeural"
    
    # Processing options
    enable_tts: bool = False
    enable_term_processing: bool = True
    term_dictionary_path: Optional[str] = None
    
    # Output settings
    output_format: str = "mp4"
    subtitle_format: str = "srt"
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Cache settings
    enable_cache: bool = True
    cache_directory: str = "~/.video_subtitle_cache"
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None


def create_initial_state(
    input_video_path: str,
    working_directory: str,
    config: Optional[Dict[str, Any]] = None
) -> ProcessingState:
    """Create initial processing state."""
    
    return ProcessingState(
        # Input
        input_video_path=input_video_path,
        working_directory=working_directory,
        
        # Configuration
        config=config or {},
        
        # Results - all None initially
        audio_extraction_result=None,
        speech_to_text_result=None,
        translation_result=None,
        term_processing_result=None,
        subtitle_merge_result=None,
        text_to_speech_result=None,
        video_muxing_result=None,
        
        # Paths - all None initially
        extracted_audio_path=None,
        english_srt_path=None,
        chinese_srt_path=None,
        merged_srt_path=None,
        final_video_path=None,
        
        # Metadata
        errors=[],
        warnings=[],
        processing_started_at=datetime.now().isoformat(),
        processing_completed_at=None,
        
        # Control
        should_continue=True,
        retry_count=0,
        current_step=None,
    ) 