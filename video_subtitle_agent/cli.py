"""Command line interface for Video Subtitle Agent."""

import click
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

from .core.agent import VideoSubtitleAgent
from .utils.device import log_system_info
from .utils.file_utils import get_video_files, validate_video_file

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Video Subtitle Agent - AI-powered video subtitle generation system."""
    pass


@main.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output video path')
@click.option('--working-dir', help='Working directory for temporary files')
@click.option('--device', default='auto', help='Processing device (auto/cpu/mps/cuda)')
@click.option('--enable-tts', is_flag=True, help='Enable text-to-speech generation')
@click.option('--enable-term-processing', is_flag=True, default=True, help='Enable term processing')
@click.option('--term-dict', help='Path to term dictionary CSV file')
@click.option('--log-level', default='INFO', help='Log level (DEBUG/INFO/WARNING/ERROR)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def process(
    input_path: str,
    output: Optional[str],
    working_dir: Optional[str],
    device: str,
    enable_tts: bool,
    enable_term_processing: bool,
    term_dict: Optional[str],
    log_level: str,
    verbose: bool
):
    """Process a single video file to generate subtitles."""
    
    if verbose:
        console.print(Panel("🎬 Video Subtitle Agent", style="bold blue"))
        log_system_info()
    
    # Validate input
    if not validate_video_file(input_path):
        console.print("[red]❌ Invalid video file[/red]")
        raise click.Abort()
    
    # Configuration
    config = {
        'device': device,
        'enable_tts': enable_tts,
        'enable_term_processing': enable_term_processing,
        'term_dictionary_path': term_dict,
        'log_level': log_level,
    }
    
    console.print(f"📁 Input: {input_path}")
    if output:
        console.print(f"📤 Output: {output}")
    console.print(f"🎯 Device: {device}")
    
    try:
        # Create agent
        agent = VideoSubtitleAgent(config=config)
        
        # Process video
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Processing video...", total=None)
            
            result = agent.process_video(
                input_path=input_path,
                output_path=output,
                working_dir=working_dir
            )
        
        # Show results
        if result["should_continue"] and not result["errors"]:
            console.print("[green]✅ Processing completed successfully![/green]")
            if result.get("final_video_path"):
                console.print(f"📹 Output video: {result['final_video_path']}")
        else:
            console.print("[red]❌ Processing failed[/red]")
            for error in result["errors"]:
                console.print(f"[red]  • {error}[/red]")
            
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise click.Abort()


@main.command()
@click.argument('input_dir', type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path())
@click.option('--recursive', '-r', is_flag=True, help='Search recursively for videos')
@click.option('--device', default='auto', help='Processing device')
@click.option('--enable-tts', is_flag=True, help='Enable text-to-speech generation')
@click.option('--parallel', default=1, help='Number of parallel processes')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def batch(
    input_dir: str,
    output_dir: str,
    recursive: bool,
    device: str,
    enable_tts: bool,
    parallel: int,
    verbose: bool
):
    """Process multiple video files in batch."""
    
    if verbose:
        console.print(Panel("🎬 Video Subtitle Agent - Batch Processing", style="bold blue"))
    
    # Find video files
    video_files = get_video_files(input_dir, recursive=recursive)
    
    if not video_files:
        console.print("[yellow]⚠️  No video files found[/yellow]")
        return
    
    console.print(f"📁 Found {len(video_files)} video files")
    
    # Configuration
    config = {
        'device': device,
        'enable_tts': enable_tts,
    }
    
    try:
        # Create agent
        agent = VideoSubtitleAgent(config=config)
        
        # Process videos
        with Progress(console=console) as progress:
            task = progress.add_task("Processing videos...", total=len(video_files))
            
            results = agent.process_batch(
                input_paths=video_files,
                output_dir=output_dir
            )
            
            progress.update(task, completed=len(video_files))
        
        # Show summary
        successful = sum(1 for r in results if r["should_continue"] and not r["errors"])
        failed = len(results) - successful
        
        table = Table(title="Processing Summary")
        table.add_column("Status", style="bold")
        table.add_column("Count", justify="right")
        table.add_row("✅ Successful", str(successful), style="green")
        table.add_row("❌ Failed", str(failed), style="red")
        table.add_row("📊 Total", str(len(results)), style="blue")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise click.Abort()


@main.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output subtitle file path (.srt)')
@click.option('--device', default='auto', help='Processing device')
@click.option('--enable-term-processing', is_flag=True, default=True, help='Enable term processing')
@click.option('--term-dict', help='Path to term dictionary CSV file')
def subtitles(
    input_path: str,
    output: Optional[str],
    device: str,
    enable_term_processing: bool,
    term_dict: Optional[str]
):
    """Generate subtitles only (no video output)."""
    
    console.print("🎬 Generating subtitles...")
    
    # Validate input
    if not validate_video_file(input_path):
        console.print("[red]❌ Invalid video file[/red]")
        raise click.Abort()
    
    # Set output path if not provided
    if not output:
        input_path_obj = Path(input_path)
        output = str(input_path_obj.parent / f"{input_path_obj.stem}_subtitles.srt")
    
    console.print(f"📁 Input: {input_path}")
    console.print(f"📝 Output: {output}")
    
    # Configuration - disable TTS and video muxing for subtitle-only mode
    config = {
        'device': device,
        'enable_tts': False,
        'enable_term_processing': enable_term_processing,
        'term_dictionary_path': term_dict,
    }
    
    try:
        # Create agent
        agent = VideoSubtitleAgent(config=config)
        
        # Process video (will stop after subtitle generation)
        result = agent.process_video(
            input_path=input_path,
            output_path=output
        )
        
        # Show results
        if result.get("merged_srt_path"):
            console.print(f"[green]✅ Subtitles generated: {result['merged_srt_path']}[/green]")
        else:
            console.print("[red]❌ Subtitle generation failed[/red]")
            for error in result["errors"]:
                console.print(f"[red]  • {error}[/red]")
            
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise click.Abort()


@main.command()
def info():
    """Show system information and requirements."""
    
    console.print(Panel("🔍 System Information", style="bold blue"))
    log_system_info()


@main.command()
def workflow():
    """Show the processing workflow diagram."""
    
    agent = VideoSubtitleAgent()
    workflow_diagram = agent.get_workflow_graph()
    
    console.print(Panel("🔄 Processing Workflow", style="bold blue"))
    console.print(workflow_diagram)


@main.command()
@click.option("--host", default="127.0.0.1", help="服务器地址")
@click.option("--port", default=7860, help="服务器端口")
@click.option("--share", is_flag=True, help="启用公网分享")
@click.option("--debug", is_flag=True, help="启用调试模式")
def gui(host: str, port: int, share: bool, debug: bool):
    """Launch web GUI interface."""
    try:
        from .gui import launch_gui
        console.print(Panel("🚀 启动Web GUI界面", style="bold green"))
        console.print(f"🌐 访问地址: http://{host}:{port}")
        console.print(f"📤 公网分享: {'已启用' if share else '未启用'}")
        launch_gui(
            server_name=host,
            server_port=port,
            share=share,
            debug=debug
        )
    except ImportError:
        console.print("[bold red]❌ 缺少GUI依赖，请运行: pip install gradio[/bold red]")
        raise click.Abort()
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 GUI服务已停止[/yellow]")
    except Exception as e:
        console.print(f"[bold red]❌ 启动GUI失败: {e}[/bold red]")
        raise


if __name__ == "__main__":
    main() 