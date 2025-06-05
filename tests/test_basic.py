"""Basic tests for Video Subtitle Agent."""

import pytest
from pathlib import Path
import tempfile
import os

from video_subtitle_agent.core.state import create_initial_state, ConfigModel
from video_subtitle_agent.core.agent import VideoSubtitleAgent
from video_subtitle_agent.utils.device import detect_device
from video_subtitle_agent.utils.file_utils import create_temp_directory, cleanup_temp_files


class TestConfiguration:
    """Test configuration and state management."""
    
    def test_config_model_defaults(self):
        """Test that ConfigModel has reasonable defaults."""
        config = ConfigModel()
        
        assert config.device == "auto"
        assert config.stt_model == "seamlessM4T_v2_large"
        assert config.audio_sample_rate == 16000
        assert config.max_retries == 3
    
    def test_config_model_validation(self):
        """Test configuration validation."""
        # Test valid configuration
        config = ConfigModel(
            device="mps",
            audio_sample_rate=22050,
            max_retries=5
        )
        
        assert config.device == "mps"
        assert config.audio_sample_rate == 22050
        assert config.max_retries == 5
    
    def test_initial_state_creation(self):
        """Test initial state creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            state = create_initial_state(
                input_video_path="/path/to/video.mp4",
                working_directory=temp_dir,
                config={"device": "cpu"}
            )
            
            assert state["input_video_path"] == "/path/to/video.mp4"
            assert state["working_directory"] == temp_dir
            assert state["config"]["device"] == "cpu"
            assert state["should_continue"] is True
            assert state["errors"] == []


class TestDeviceDetection:
    """Test device detection functionality."""
    
    def test_detect_device(self):
        """Test device detection returns valid device."""
        device = detect_device()
        valid_devices = ["cpu", "mps", "cuda"]
        assert device in valid_devices
    
    def test_device_detection_deterministic(self):
        """Test that device detection is deterministic."""
        device1 = detect_device()
        device2 = detect_device()
        assert device1 == device2


class TestFileUtils:
    """Test file utility functions."""
    
    def test_temp_directory_creation(self):
        """Test temporary directory creation and cleanup."""
        temp_dir = create_temp_directory("test_")
        
        assert os.path.exists(temp_dir)
        assert os.path.isdir(temp_dir)
        assert "test_" in os.path.basename(temp_dir)
        
        # Cleanup
        cleanup_temp_files(temp_dir)
        assert not os.path.exists(temp_dir)
    
    def test_temp_directory_cleanup_nonexistent(self):
        """Test cleanup of non-existent directory doesn't raise error."""
        # Should not raise an exception
        cleanup_temp_files("/path/that/does/not/exist")


class TestAgent:
    """Test the main VideoSubtitleAgent class."""
    
    def test_agent_initialization(self):
        """Test agent initialization with default config."""
        agent = VideoSubtitleAgent()
        
        assert agent.config is not None
        assert agent.workflow is not None
    
    def test_agent_initialization_with_config(self):
        """Test agent initialization with custom config."""
        config = {
            "device": "cpu",
            "max_retries": 2,
            "log_level": "DEBUG"
        }
        
        agent = VideoSubtitleAgent(config=config)
        
        assert agent.config.device == "cpu"
        assert agent.config.max_retries == 2
        assert agent.config.log_level == "DEBUG"
    
    def test_workflow_graph_generation(self):
        """Test workflow graph generation."""
        agent = VideoSubtitleAgent()
        graph = agent.get_workflow_graph()
        
        assert isinstance(graph, str)
        assert "graph TD" in graph
        assert "Audio Extraction" in graph


class TestWorkflowLogic:
    """Test workflow conditional logic."""
    
    def test_should_process_terms_enabled(self):
        """Test term processing decision when enabled."""
        agent = VideoSubtitleAgent()
        
        state = create_initial_state(
            input_video_path="/test/video.mp4",
            working_directory="/tmp",
            config={
                "enable_term_processing": True,
                "term_dictionary_path": "/path/to/terms.csv"
            }
        )
        
        result = agent._should_process_terms(state)
        assert result == "process_terms"
    
    def test_should_process_terms_disabled(self):
        """Test term processing decision when disabled."""
        agent = VideoSubtitleAgent()
        
        state = create_initial_state(
            input_video_path="/test/video.mp4",
            working_directory="/tmp",
            config={"enable_term_processing": False}
        )
        
        result = agent._should_process_terms(state)
        assert result == "skip_terms"
    
    def test_should_generate_tts_enabled(self):
        """Test TTS generation decision when enabled."""
        agent = VideoSubtitleAgent()
        
        state = create_initial_state(
            input_video_path="/test/video.mp4",
            working_directory="/tmp",
            config={"enable_tts": True}
        )
        
        result = agent._should_generate_tts(state)
        assert result == "generate_tts"
    
    def test_should_generate_tts_disabled(self):
        """Test TTS generation decision when disabled."""
        agent = VideoSubtitleAgent()
        
        state = create_initial_state(
            input_video_path="/test/video.mp4",
            working_directory="/tmp",
            config={"enable_tts": False}
        )
        
        result = agent._should_generate_tts(state)
        assert result == "skip_tts"


@pytest.mark.integration
class TestIntegrationBasic:
    """Basic integration tests."""
    
    def test_agent_process_video_file_not_found(self):
        """Test agent behavior with non-existent video file."""
        agent = VideoSubtitleAgent()
        
        with pytest.raises(FileNotFoundError):
            agent.process_video("/path/that/does/not/exist.mp4")
    
    def test_batch_processing_empty_list(self):
        """Test batch processing with empty file list."""
        agent = VideoSubtitleAgent()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            results = agent.process_batch(
                input_paths=[],
                output_dir=temp_dir
            )
            
            assert results == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 