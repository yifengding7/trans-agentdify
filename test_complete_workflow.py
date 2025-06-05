#!/usr/bin/env python3
"""Test the complete video subtitle workflow."""

import tempfile
import shutil
from pathlib import Path
from video_subtitle_agent import VideoSubtitleAgent
from loguru import logger

def create_test_video(output_path: str) -> None:
    """Create a 10-second test video using FFmpeg."""
    import subprocess
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "testsrc2=duration=10:size=320x240:rate=30",
        "-f", "lavfi", 
        "-i", "sine=frequency=1000:duration=10",
        "-c:v", "libx264", "-preset", "fast", "-crf", "30",
        "-c:a", "aac", "-b:a", "128k",
        output_path
    ]
    
    logger.info(f"Creating test video: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"FFmpeg failed: {result.stderr}")
        raise RuntimeError(f"Failed to create test video: {result.stderr}")
        
    logger.success(f"Test video created: {output_path}")

def main():
    """Run the complete workflow test."""
    
    # Setup working directory
    working_dir = tempfile.mkdtemp(prefix="workflow_test_")
    logger.info(f"Working directory: {working_dir}")
    
    try:
        # Create test video
        test_video = Path(working_dir) / "test_video.mp4"
        create_test_video(str(test_video))
        
        # Initialize agent with minimal config
        config = {
            "device": "mps",  # Use MPS acceleration
            "enable_tts": False,  # Disable TTS for quick testing
            "enable_term_processing": False,  # Disable term processing
            "source_language": "eng",
            "target_language": "cmn",
            "log_level": "DEBUG"
        }
        
        agent = VideoSubtitleAgent(config)
        
        # Log workflow structure
        logger.info("Workflow structure:")
        logger.info(agent.get_workflow_graph())
        
        # Process the video
        logger.info("Starting video processing...")
        result = agent.process_video(
            input_path=str(test_video),
            output_path=str(Path(working_dir) / "output_video.mp4"),
            working_dir=working_dir
        )
        
        # Check results
        logger.info("Processing Results:")
        logger.info(f"Should continue: {result['should_continue']}")
        logger.info(f"Errors: {result['errors']}")
        logger.info(f"Warnings: {result['warnings']}")
        
        # Check output files
        if result.get('extracted_audio_path'):
            audio_path = Path(result['extracted_audio_path'])
            logger.info(f"Audio extracted: {audio_path} (exists: {audio_path.exists()})")
            
        if result.get('english_srt_path'):
            srt_path = Path(result['english_srt_path'])
            logger.info(f"English SRT: {srt_path} (exists: {srt_path.exists()})")
            
        if result.get('chinese_srt_path'):
            srt_path = Path(result['chinese_srt_path'])
            logger.info(f"Chinese SRT: {srt_path} (exists: {srt_path.exists()})")
            
        if result.get('final_video_path'):
            video_path = Path(result['final_video_path'])
            logger.info(f"Final video: {video_path} (exists: {video_path.exists()})")
        
        # Show step results
        logger.info("\nStep Results:")
        for step_name in ['audio_extraction', 'speech_to_text', 'translation', 'subtitle_merge', 'video_muxing']:
            result_key = f"{step_name}_result"
            if result.get(result_key):
                step_result = result[result_key]
                time_str = f"{step_result.processing_time:.2f}s" if step_result.processing_time else "N/A"
                logger.info(f"  {step_name}: {step_result.status} ({time_str})")
                if step_result.error_message:
                    logger.error(f"    Error: {step_result.error_message}")
        
        if result['should_continue'] and not result['errors']:
            logger.success("🎉 Complete workflow test PASSED!")
        else:
            logger.error("❌ Complete workflow test FAILED")
            for error in result['errors']:
                logger.error(f"  - {error}")
                
    except Exception as e:
        logger.exception(f"Test failed with exception: {e}")
        
    finally:
        # Cleanup
        try:
            shutil.rmtree(working_dir)
            logger.info(f"Cleaned up working directory: {working_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {working_dir}: {e}")

if __name__ == "__main__":
    main() 