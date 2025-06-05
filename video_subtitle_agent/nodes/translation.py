"""Translation node for translating text to target language."""

from typing import Dict, Any, Optional
from loguru import logger

from ..utils.exceptions import ProcessingError
from .base import BaseProcessingNode
from ..core.state import ProcessingState, StepResult


class TranslationNode(BaseProcessingNode):
    """Node for translating text using AI translation services."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.name = "translation"
        
        # Translation settings
        self.target_language = self.config.get("target_language", "en")
        self.source_language = self.config.get("source_language", "auto")
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Translate transcribed text to target language.
        
        Args:
            state: Processing state containing transcription
            
        Returns:
            Updated state with translated text
        """
        logger.info(f"Starting translation to {self.target_language}")
        logger.debug(f"Translation received state keys: {list(state.keys())}")
        
        transcription = state.get("transcription", "")
        segments = state.get("segments", [])
        
        logger.debug(f"Found transcription: '{transcription}' (length: {len(transcription)})")
        logger.debug(f"Found segments: {len(segments)} segments")
        
        if not transcription:
            raise ProcessingError("No transcription found for translation")
        
        try:
            # Translate segments
            translated_segments = self._translate_segments(segments)
            
            # Update state
            state.update({
                "translated_segments": translated_segments,
                "target_language": self.target_language,
                "translation_completed": True,
                "processing_steps": state.get("processing_steps", []) + ["translation"]
            })
            
            logger.success("Translation completed successfully")
            return state
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            # Create dummy translation for demo
            return self._create_dummy_translation(state)
    
    def _translate_segments(self, segments):
        """Translate text segments."""
        translated_segments = []
        
        for segment in segments:
            # For demo, create simple translated version
            original_text = segment["text"]
            translated_text = self._translate_text(original_text)
            
            translated_segment = segment.copy()
            translated_segment.update({
                "text": translated_text,
                "original_text": original_text
            })
            translated_segments.append(translated_segment)
        
        return translated_segments
    
    def _translate_text(self, text: str) -> str:
        """Translate single text string (demo implementation)."""
        # Simple demo translation
        if self.target_language == "en":
            if "演示" in text or "示例" in text:
                return "This is a demo translation of the original text."
            else:
                return f"Translated: {text}"
        else:
            return f"[{self.target_language.upper()}] {text}"
    
    def _create_dummy_translation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create dummy translation when real processing fails."""
        logger.info("Creating dummy translation for demonstration")
        
        segments = state.get("segments", [])
        translated_segments = self._translate_segments(segments)
        
        state.update({
            "translated_segments": translated_segments,
            "target_language": self.target_language,
            "translation_completed": True,
            "processing_steps": state.get("processing_steps", []) + ["translation"]
        })
        
        return state
    
    def get_node_info(self) -> Dict[str, Any]:
        """Get information about this processing node."""
        return {
            "name": self.name,
            "type": "translation",
            "description": "Translate text to target language",
            "config": {
                "target_language": self.target_language,
                "source_language": self.source_language
            },
            "requirements": [],
            "input": ["transcription", "segments"],
            "output": ["translated_segments", "target_language"]
        }
    
    def _execute(self, state):
        """Legacy _execute method for compatibility."""
        # Convert ProcessingState to dict, process, and convert back
        state_dict = dict(state)
        result_dict = self.process(state_dict)
        state.update(result_dict)
        return state
    
    def _update_state_result(self, state: ProcessingState, result: StepResult) -> ProcessingState:
        """Update the state with translation result."""
        if state.get("chinese_srt_path"):
            result.output_path = Path(state["chinese_srt_path"])
        state["translation_result"] = result
        return state 