#!/usr/bin/env python3
"""
🎬 Video Subtitle Processing Demo
==================================

This script demonstrates the complete video subtitle processing workflow
using our LangGraph-based AI agent system.
"""

import tempfile
import shutil
from pathlib import Path
from video_subtitle_agent import VideoSubtitleAgent
from loguru import logger
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich import print as rprint
from rich.markdown import Markdown
import time

console = Console()

def create_demo_video(output_path: str, duration: int = 10) -> None:
    """Create a demo video with test pattern and audio."""
    
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi",
        "-i", f"testsrc2=duration={duration}:size=640x480:rate=30",
        "-f", "lavfi", 
        "-i", f"sine=frequency=1000:duration={duration}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to create demo video: {result.stderr}")

def show_step_result(step_name: str, success: bool, duration: float, details: str = ""):
    """Display step result in formatted table."""
    
    status = "✅ SUCCESS" if success else "❌ FAILED"
    color = "green" if success else "red"
    
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Field", style="bold cyan", width=15)
    table.add_column("Value", width=50)
    
    table.add_row("Step", step_name)
    table.add_row("Status", f"[{color}]{status}[/{color}]")
    table.add_row("Duration", f"{duration:.2f}s")
    if details:
        table.add_row("Details", details)
    
    console.print(table)
    console.print()

def show_file_info(file_path: str, description: str):
    """Show information about generated files."""
    path = Path(file_path)
    if path.exists():
        size = path.stat().st_size
        size_mb = size / 1024 / 1024
        rprint(f"📄 [green]{description}[/green]: {path.name} ({size_mb:.2f} MB)")
        
        # Show first few lines if it's a text file
        if path.suffix in ['.srt', '.txt']:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:5]
                    if lines:
                        rprint(f"[dim]Preview:[/dim]")
                        for line in lines:
                            rprint(f"[dim]  {line.rstrip()}[/dim]")
                        if len(lines) == 5:
                            rprint(f"[dim]  ...[/dim]")
                        rprint()
            except Exception:
                pass
    else:
        rprint(f"📄 [red]{description}[/red]: Not found")

def main():
    """Main demo function."""
    
    # Welcome message
    welcome = """
# 🎬 Video Subtitle Processing Demo

This demonstration shows the complete AI-powered video subtitle processing workflow:

1. **Audio Extraction** - Extract audio from video using FFmpeg
2. **Speech-to-Text** - Convert audio to text using OpenAI Whisper
3. **Translation** - Translate text to target language
4. **Subtitle Generation** - Create SRT subtitle files
5. **Video Muxing** - Embed subtitles back into video

The system uses **LangGraph** for workflow orchestration and **MPS acceleration** on Apple Silicon.
"""
    
    console.print(Panel(Markdown(welcome), title="🚀 AI Video Subtitle System", border_style="blue"))
    
    # Setup
    working_dir = tempfile.mkdtemp(prefix="subtitle_demo_")
    logger.info(f"Working directory: {working_dir}")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            # Task 1: Create demo video
            task1 = progress.add_task("Creating demo video...", total=1)
            test_video = Path(working_dir) / "demo_video.mp4"
            create_demo_video(str(test_video), duration=10)
            progress.advance(task1, 1)
            show_file_info(str(test_video), "Demo Video")
            
            # Task 2: Initialize AI agent
            task2 = progress.add_task("Initializing AI agent...", total=1)
            config = {
                "device": "mps",
                "enable_tts": False,
                "enable_term_processing": False,
                "source_language": "auto",
                "target_language": "cmn",
                "log_level": "INFO"
            }
            agent = VideoSubtitleAgent(config)
            progress.advance(task2, 1)
            
            console.print()
            console.print(Panel("🤖 AI Agent Initialized with MPS Acceleration", style="green"))
            console.print()
            
            # Display workflow
            rprint("[bold blue]📋 Processing Workflow:[/bold blue]")
            workflow_info = agent.get_workflow_graph()
            console.print(Panel(workflow_info, title="Workflow Structure", border_style="cyan"))
            
            # Task 3: Process video step by step
            console.print()
            console.print(Panel("🎯 Starting Video Processing", style="yellow"))
            console.print()
            
            # Start processing
            start_time = time.time()
            result = agent.process_video(
                input_path=str(test_video),
                output_path=str(Path(working_dir) / "output_video.mp4"),
                working_dir=working_dir
            )
            total_time = time.time() - start_time
            
            # Display step results
            console.print()
            console.print(Panel("📊 Processing Results", style="magenta"))
            console.print()
            
            step_names = ['audio_extraction', 'speech_to_text', 'translation', 'subtitle_merge', 'video_muxing']
            for step_name in step_names:
                result_key = f"{step_name}_result"
                if result.get(result_key):
                    step_result = result[result_key]
                    duration = step_result.processing_time or 0
                    success = step_result.status.value == "completed"
                    details = step_result.error_message if step_result.error_message else ""
                    show_step_result(step_name.replace('_', ' ').title(), success, duration, details)
            
            # Show generated files
            console.print()
            console.print(Panel("📁 Generated Files", style="cyan"))
            console.print()
            
            if result.get('extracted_audio_path'):
                show_file_info(result['extracted_audio_path'], "Extracted Audio")
            
            if result.get('english_srt_path'):
                show_file_info(result['english_srt_path'], "English Subtitles")
            
            if result.get('chinese_srt_path'):
                show_file_info(result['chinese_srt_path'], "Chinese Subtitles")
            
            if result.get('final_video_path'):
                show_file_info(result['final_video_path'], "Final Video with Subtitles")
            
            # Summary
            console.print()
            if result['should_continue'] and not result['errors']:
                console.print(Panel(
                    f"🎉 [green]SUCCESS![/green] Video processing completed in {total_time:.2f} seconds\n\n"
                    f"✅ All processing steps completed successfully\n"
                    f"📊 {len([s for s in step_names if result.get(f'{s}_result') and result[f'{s}_result'].status.value == 'completed'])} out of {len(step_names)} steps succeeded",
                    title="🏆 Demo Complete",
                    style="green"
                ))
            else:
                error_count = len(result['errors'])
                console.print(Panel(
                    f"⚠️  [yellow]PARTIAL SUCCESS[/yellow] - Some steps completed\n\n"
                    f"❌ {error_count} error(s) encountered:\n" + 
                    "\n".join(f"   • {error}" for error in result['errors']),
                    title="⚠️  Demo Results",
                    style="yellow"
                ))
                
                # Show what did work
                successful_steps = [s for s in step_names if result.get(f'{s}_result') and result[f'{s}_result'].status.value == 'completed']
                if successful_steps:
                    console.print()
                    console.print(f"✅ [green]Successful steps:[/green] {', '.join(s.replace('_', ' ').title() for s in successful_steps)}")
            
            # Keep files for inspection
            console.print()
            console.print(f"🔍 [dim]Files available for inspection in: {working_dir}[/dim]")
            console.print(f"🔍 [dim]Run: ls -la {working_dir}[/dim]")
            
    except Exception as e:
        console.print()
        console.print(Panel(
            f"💥 [red]DEMO FAILED[/red]\n\nError: {str(e)}",
            title="❌ Error",
            style="red"
        ))
        logger.exception("Demo failed")
        
    finally:
        # Ask user if they want to keep files
        console.print()
        keep_files = console.input("🗑️  Keep demo files for inspection? [y/N]: ").lower().startswith('y')
        
        if not keep_files:
            try:
                shutil.rmtree(working_dir)
                console.print(f"🗑️  Cleaned up: {working_dir}")
            except Exception as e:
                console.print(f"⚠️  Failed to cleanup: {e}")

if __name__ == "__main__":
    main() 