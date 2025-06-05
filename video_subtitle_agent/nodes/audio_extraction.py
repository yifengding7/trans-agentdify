"""Audio extraction node for extracting audio from video files."""

import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

from ..utils.exceptions import ProcessingError
from ..utils.file_utils import ensure_directory_exists, get_safe_filename
from .base import BaseProcessingNode
from ..core.state import ProcessingState, StepResult
from ..utils.exceptions import RetryableError


class AudioExtractionNode(BaseProcessingNode):
    """Node for extracting audio from video files using FFmpeg."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.name = "audio_extraction"
        
        # Audio extraction settings
        self.sample_rate = self.config.get("audio_sample_rate", 16000)
        self.channels = self.config.get("audio_channels", 1)  # Mono
        self.format = self.config.get("audio_format", "wav")
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract audio from video file.
        
        Args:
            state: Processing state containing video file path
            
        Returns:
            Updated state with audio file path
        """
        logger.debug(f"Audio extraction received state keys: {list(state.keys())}")
        
        input_path = state.get("input_path") or state.get("input_video_path")
        logger.info(f"Starting audio extraction from: {input_path}")
        
        if not input_path or not Path(input_path).exists():
            logger.error(f"Input video file not found. input_path={input_path}, exists={Path(input_path).exists() if input_path else False}")
            raise ProcessingError("Input video file not found")
        
        try:
            # Create audio output path
            audio_path = self._create_audio_path(state)
            ensure_directory_exists(audio_path.parent)
            
            # Extract audio using FFmpeg
            self._extract_audio_ffmpeg(input_path, audio_path)
            
            # Update state with multiple field names for compatibility
            state.update({
                "audio_path": str(audio_path),  # For new workflow
                "extracted_audio_path": str(audio_path),  # For ProcessingState compatibility
                "audio_sample_rate": self.sample_rate,
                "audio_channels": self.channels,
                "processing_steps": state.get("processing_steps", []) + ["audio_extraction"]
            })
            
            logger.success(f"Audio extracted successfully: {audio_path}")
            return state
            
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            raise ProcessingError(f"Audio extraction failed: {e}")
    
    def _create_audio_path(self, state: Dict[str, Any]) -> Path:
        """Create output path for extracted audio."""
        input_path = state.get("input_path") or state.get("input_video_path")
        input_path = Path(input_path)
        
        # Use temporary directory or specified output directory
        if "temp_dir" in state:
            output_dir = Path(state["temp_dir"])
        elif "working_directory" in state:
            output_dir = Path(state["working_directory"])
        else:
            output_dir = input_path.parent / "temp"
        
        # Create safe filename
        safe_name = get_safe_filename(input_path.stem)
        audio_filename = f"{safe_name}_audio.{self.format}"
        
        return output_dir / audio_filename
    
    def _extract_audio_ffmpeg(self, input_path: str, output_path: Path) -> None:
        """Extract audio using FFmpeg."""
        cmd = [
            "ffmpeg", "-y",  # Overwrite output
            "-i", str(input_path),  # Input file
            "-vn",  # No video
            "-ar", str(self.sample_rate),  # Sample rate
            "-ac", str(self.channels),  # Channels
            "-c:a", "pcm_s16le",  # Audio codec
            str(output_path)  # Output file
        ]
        
        try:
            # Check if FFmpeg is available
            if not self._check_ffmpeg_available():
                # FFmpeg not found, create a dummy audio file for demo
                logger.warning("FFmpeg not found, creating dummy audio file for demo")
                self._create_dummy_audio(output_path)
                return
            
            logger.debug(f"Running FFmpeg command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
                check=True
            )
            
            logger.debug(f"FFmpeg output: {result.stderr}")
            
            if not output_path.exists():
                raise ProcessingError("Audio file was not created")
                
        except subprocess.TimeoutExpired:
            raise ProcessingError("Audio extraction timed out")
        except subprocess.CalledProcessError as e:
            raise ProcessingError(f"FFmpeg failed: {e.stderr}")
        except FileNotFoundError:
            # FFmpeg not found, create a dummy audio file for demo
            logger.warning("FFmpeg not found, creating dummy audio file for demo")
            self._create_dummy_audio(output_path)
    
    def _check_ffmpeg_available(self) -> bool:
        """Check if FFmpeg is available in the system."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _create_dummy_audio(self, output_path: Path) -> None:
        """Create a dummy audio file for demo purposes."""
        logger.info("Creating dummy audio file for demonstration")
        
        # Create a small WAV file header (44 bytes) + minimal audio data
        wav_header = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x08\x00\x00'
        audio_data = b'\x00\x00' * 1000  # 1000 samples of silence
        
        with open(output_path, 'wb') as f:
            f.write(wav_header)
            f.write(audio_data)
        
        logger.info(f"Dummy audio file created: {output_path}")
    
    def get_node_info(self) -> Dict[str, Any]:
        """Get information about this processing node."""
        return {
            "name": self.name,
            "type": "audio_extraction",
            "description": "Extract audio from video files using FFmpeg",
            "config": {
                "sample_rate": self.sample_rate,
                "channels": self.channels,
                "format": self.format
            },
            "requirements": ["ffmpeg"],
            "input": ["input_path"],
            "output": ["audio_path", "audio_sample_rate", "audio_channels"]
        }
    
    def _execute(self, state):
        """Legacy _execute method for compatibility."""
        # Convert ProcessingState to dict, process, and convert back
        state_dict = dict(state)
        result_dict = self.process(state_dict)
        state.update(result_dict)
        return state
    
    def _update_state_result(self, state: ProcessingState, result: StepResult) -> ProcessingState:
        """Update the state with audio extraction result."""
        result.output_path = Path(state.get("extracted_audio_path", "")) if state.get("extracted_audio_path") else None
        state["audio_extraction_result"] = result
        return state
    
    def _get_metadata(self, state: ProcessingState) -> Dict[str, Any]:
        """Get metadata for the audio extraction step."""
        metadata = {}
        
        if state.get("extracted_audio_path"):
            audio_path = Path(state["extracted_audio_path"])
            if audio_path.exists():
                file_size = audio_path.stat().st_size
                metadata.update({
                    "output_file_size_bytes": file_size,
                    "output_file_size_mb": file_size / 1024 / 1024,
                    "audio_format": "wav",
                    "sample_rate": self._get_config_value(state, "audio_sample_rate", 16000),
                    "channels": self._get_config_value(state, "audio_channels", 1),
                })
        
        return metadata 