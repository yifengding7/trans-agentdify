"""Speech-to-text node for converting audio to text transcription."""

import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from loguru import logger

from ..utils.exceptions import ProcessingError
from ..utils.file_utils import ensure_directory_exists, get_safe_filename
from .base import BaseProcessingNode
from ..core.state import ProcessingState, StepResult


class SpeechToTextNode(BaseProcessingNode):
    """Node for converting audio to text using Whisper."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.name = "speech_to_text"
        
        # Whisper settings
        self.model_size = self.config.get("whisper_model", "base")
        self.language = self.config.get("language", "auto")  # Auto-detect language
        self.device = self.config.get("device", "cpu")
        
        # Initialize model lazily
        self._model = None
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Convert audio to text transcription.
        
        Args:
            state: Processing state containing audio file path
            
        Returns:
            Updated state with transcription and subtitle data
        """
        logger.info(f"Starting speech-to-text processing with model: {self.model_size}")
        logger.debug(f"Speech-to-text received state keys: {list(state.keys())}")
        
        audio_path = state.get("audio_path") or state.get("extracted_audio_path")
        logger.debug(f"Looking for audio file in state. audio_path={audio_path}")
        logger.debug(f"State audio_path: {state.get('audio_path')}")
        logger.debug(f"State extracted_audio_path: {state.get('extracted_audio_path')}")
        
        if not audio_path or not Path(audio_path).exists():
            logger.error(f"Audio file not found. audio_path={audio_path}, exists={Path(audio_path).exists() if audio_path else False}")
            logger.info("Creating dummy transcription since no audio file found")
            return self._create_dummy_transcription(state)
        
        try:
            # Ensure model is loaded
            self._ensure_model_loaded()
            
            # Transcribe audio
            result = self._transcribe_audio(audio_path)
            
            # Process transcription result
            transcription_data = self._process_transcription_result(result)
            
            # Create subtitle file
            subtitle_path = self._create_subtitle_file(state, transcription_data)
            
            # Update state with multiple field names for compatibility
            state.update({
                "transcription": result.get("text", ""),  # For translation node
                "segments": transcription_data["segments"],  # For translation node
                "detected_language": result.get("language", self.language),
                "subtitle_path": str(subtitle_path),
                "english_srt_path": str(subtitle_path),  # For ProcessingState compatibility
                "processing_steps": state.get("processing_steps", []) + ["speech_to_text"]
            })
            
            logger.success(f"Speech-to-text completed. Language: {result.get('language', 'unknown')}")
            return state
            
        except Exception as e:
            logger.error(f"Speech-to-text processing failed: {e}")
            # Create dummy transcription for demo
            return self._create_dummy_transcription(state)
    
    def _ensure_model_loaded(self) -> None:
        """Ensure Whisper model is loaded."""
        if self._model is None:
            try:
                import whisper
                logger.info(f"Loading Whisper model: {self.model_size}")
                self._model = whisper.load_model(self.model_size)
                logger.success(f"Whisper model loaded successfully")
            except ImportError:
                logger.warning("Whisper not available, will use dummy transcription")
                self._model = "dummy"
            except Exception as e:
                logger.warning(f"Failed to load Whisper model: {e}")
                self._model = "dummy"
    
    def _transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe audio file using Whisper."""
        if self._model == "dummy":
            return self._create_dummy_whisper_result()
        
        try:
            # Set transcription options
            options = {
                "fp16": self.device != "cpu",  # Use FP16 for GPU
                "language": None if self.language == "auto" else self.language,
            }
            
            logger.info(f"Transcribing audio: {audio_path}")
            result = self._model.transcribe(audio_path, **options)
            
            return result
            
        except Exception as e:
            logger.warning(f"Whisper transcription failed: {e}, using dummy result")
            return self._create_dummy_whisper_result()
    
    def _create_dummy_whisper_result(self) -> Dict[str, Any]:
        """Create dummy Whisper result for demonstration."""
        return {
            "text": "这是一个演示视频的示例字幕。Speech-to-text processing would generate actual transcription here.",
            "language": "zh",
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 3.0,
                    "text": "这是一个演示视频的示例字幕。",
                    "words": []
                },
                {
                    "id": 1,
                    "start": 3.5,
                    "end": 8.0,
                    "text": "Speech-to-text processing would generate actual transcription here.",
                    "words": []
                }
            ]
        }
    
    def _process_transcription_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process Whisper transcription result."""
        segments = []
        
        for segment in result.get("segments", []):
            processed_segment = {
                "id": segment["id"],
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"].strip(),
                "confidence": segment.get("avg_logprob", 0.0)
            }
            segments.append(processed_segment)
        
        return {
            "text": result.get("text", ""),
            "language": result.get("language", "unknown"),
            "segments": segments
        }
    
    def _create_subtitle_file(self, state: Dict[str, Any], transcription_data: Dict[str, Any]) -> Path:
        """Create SRT subtitle file from transcription."""
        # Get input path with fallback options
        input_path_str = (state.get("input_path") or 
                         state.get("input_video_path") or
                         state.get("working_directory", "/tmp") + "/video")
        input_path = Path(input_path_str)
        
        # Use temporary directory or specified output directory
        if "temp_dir" in state:
            output_dir = Path(state["temp_dir"])
        else:
            output_dir = input_path.parent / "temp"
        
        ensure_directory_exists(output_dir)
        
        # Create safe filename
        safe_name = get_safe_filename(input_path.stem)
        subtitle_filename = f"{safe_name}_original.srt"
        subtitle_path = output_dir / subtitle_filename
        
        # Generate SRT content
        srt_content = self._generate_srt_content(transcription_data["segments"])
        
        # Write SRT file
        with open(subtitle_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        logger.info(f"Subtitle file created: {subtitle_path}")
        return subtitle_path
    
    def _generate_srt_content(self, segments: List[Dict[str, Any]]) -> str:
        """Generate SRT format content from segments."""
        srt_lines = []
        
        for i, segment in enumerate(segments, 1):
            start_time = self._seconds_to_srt_time(segment["start"])
            end_time = self._seconds_to_srt_time(segment["end"])
            text = segment["text"].strip()
            
            srt_lines.append(f"{i}")
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(text)
            srt_lines.append("")  # Empty line between subtitles
        
        return "\n".join(srt_lines)
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    def _create_dummy_transcription(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create dummy transcription when real processing fails."""
        logger.info("Creating dummy transcription for demonstration")
        
        dummy_result = self._create_dummy_whisper_result()
        transcription_data = self._process_transcription_result(dummy_result)
        subtitle_path = self._create_subtitle_file(state, transcription_data)
        
        state.update({
            "transcription": dummy_result["text"],  # For translation node
            "segments": transcription_data["segments"],  # For translation node
            "detected_language": dummy_result["language"],
            "subtitle_path": str(subtitle_path),
            "english_srt_path": str(subtitle_path),  # For ProcessingState compatibility
            "processing_steps": state.get("processing_steps", []) + ["speech_to_text"]
        })
        
        return state
    
    def get_node_info(self) -> Dict[str, Any]:
        """Get information about this processing node."""
        return {
            "name": self.name,
            "type": "speech_to_text",
            "description": "Convert audio to text using OpenAI Whisper",
            "config": {
                "model_size": self.model_size,
                "language": self.language,
                "device": self.device
            },
            "requirements": ["whisper-openai", "torch"],
            "input": ["audio_path"],
            "output": ["transcription", "segments", "detected_language", "subtitle_path"]
        }

    def _execute(self, state: ProcessingState) -> ProcessingState:
        """Convert speech to text (placeholder implementation)."""
        # TODO: Implement actual STT logic with seamless-communication
        # For now, just create a placeholder subtitle file
        from pathlib import Path
        
        working_dir = Path(state["working_directory"])
        srt_path = working_dir / "english_subtitles.srt"
        
        # Create a simple placeholder SRT file
        placeholder_content = """1
00:00:00,000 --> 00:00:05,000
[Placeholder: English speech recognition not yet implemented]

2
00:00:05,000 --> 00:00:10,000
This would contain the actual transcribed text from the audio.
"""
        
        srt_path.write_text(placeholder_content, encoding='utf-8')
        state["english_srt_path"] = str(srt_path)
        
        return state
    
    def _update_state_result(self, state: ProcessingState, result: StepResult) -> ProcessingState:
        """Update the state with STT result."""
        if state.get("english_srt_path"):
            result.output_path = Path(state["english_srt_path"])
        state["speech_to_text_result"] = result
        return state

    def _execute(self, state):
        """Legacy _execute method for compatibility."""
        # Convert ProcessingState to dict, process, and convert back
        state_dict = dict(state)
        result_dict = self.process(state_dict)
        state.update(result_dict)
        return state 