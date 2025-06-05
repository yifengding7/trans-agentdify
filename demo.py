#!/usr/bin/env python3
"""
Video Subtitle Agent - 演示脚本

这个脚本展示了基于LangGraph构建的现代化视频字幕处理系统的核心功能。
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

# 添加项目路径到sys.path以便导入
sys.path.insert(0, str(Path(__file__).parent))

try:
    from video_subtitle_agent.core.agent import VideoSubtitleAgent
    from video_subtitle_agent.core.state import ConfigModel, create_initial_state
    from video_subtitle_agent.utils.device import log_system_info, detect_device
    from video_subtitle_agent.utils.cache import CacheManager
    from video_subtitle_agent.utils.file_utils import get_video_files
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装所有依赖包")
    sys.exit(1)

console = Console()


def show_banner():
    """显示项目横幅"""
    banner = """
    🎬 视频字幕AI处理系统
    ━━━━━━━━━━━━━━━━━━━━━━━
    基于LangGraph的智能化工作流
    """
    console.print(Panel(banner, style="bold blue"))


def show_architecture():
    """展示系统架构"""
    console.print("\n🏗️ [bold]系统架构[/bold]")
    
    architecture_code = '''
# LangGraph工作流节点
nodes = {
    "audio_extraction": AudioExtractionNode(),     # 音频提取
    "speech_to_text": SpeechToTextNode(),          # 语音转文本
    "translation": TranslationNode(),              # 翻译
    "term_processing": TermProcessingNode(),       # 术语处理
    "subtitle_merge": SubtitleMergeNode(),         # 字幕合并
    "text_to_speech": TextToSpeechNode(),          # 文本转语音
    "video_muxing": VideoMuxingNode(),             # 视频封装
}

# 条件分支逻辑
workflow.add_conditional_edges(
    "translation",
    self._should_process_terms,
    {"process_terms": "term_processing", "skip_terms": "subtitle_merge"}
)
    '''
    
    syntax = Syntax(architecture_code, "python", theme="monokai", line_numbers=True)
    console.print(syntax)


def show_features():
    """展示系统特性"""
    console.print("\n✨ [bold]核心特性[/bold]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("特性", style="cyan", width=20)
    table.add_column("描述", style="white")
    table.add_column("技术栈", style="green")
    
    table.add_row(
        "🤖 智能工作流", 
        "基于LangGraph的状态管理和错误恢复", 
        "LangGraph + LangChain"
    )
    table.add_row(
        "🎯 端到端处理", 
        "从视频到双语字幕的完整流水线", 
        "FFmpeg + AI Models"
    )
    table.add_row(
        "🚀 硬件加速", 
        "支持Apple Silicon MPS加速", 
        "PyTorch MPS/CUDA"
    )
    table.add_row(
        "🐳 容器化开发", 
        "完整的Dev Container环境", 
        "Docker + OrbStack"
    )
    table.add_row(
        "🧪 测试完备", 
        "单元测试和集成测试", 
        "pytest + coverage"
    )
    table.add_row(
        "📦 现代化", 
        "使用pyproject.toml和现代Python工具链", 
        "Python 3.10+"
    )
    
    console.print(table)


def show_workflow():
    """展示工作流程图"""
    console.print("\n🔄 [bold]处理工作流[/bold]")
    
    try:
        agent = VideoSubtitleAgent()
        workflow_diagram = agent.get_workflow_graph()
        console.print(workflow_diagram)
    except Exception as e:
        console.print(f"[red]无法生成工作流图: {e}[/red]")


def show_configuration_example():
    """展示配置示例"""
    console.print("\n⚙️ [bold]配置示例[/bold]")
    
    config_code = '''
from video_subtitle_agent import VideoSubtitleAgent

# 基础配置
agent = VideoSubtitleAgent(config={
    "device": "auto",                    # 自动检测设备
    "enable_tts": True,                  # 启用文本转语音
    "enable_term_processing": True,      # 启用术语处理
    "term_dictionary_path": "terms.csv", # 术语词典路径
    "max_retries": 3,                    # 最大重试次数
    "log_level": "INFO"                  # 日志级别
})

# 处理单个视频
result = agent.process_video(
    input_path="input.mp4",
    output_path="output_with_subtitles.mp4"
)

# 批量处理
results = agent.process_batch(
    input_paths=["video1.mp4", "video2.mp4"],
    output_dir="./outputs/"
)
    '''
    
    syntax = Syntax(config_code, "python", theme="monokai", line_numbers=True)
    console.print(syntax)


def show_cli_examples():
    """展示CLI使用示例"""
    console.print("\n💻 [bold]命令行使用示例[/bold]")
    
    cli_code = '''
# 处理单个视频
video-subtitle process input.mp4 --output output.mp4 --enable-tts

# 批量处理
video-subtitle batch ./videos/ ./outputs/ --recursive --device mps

# 仅生成字幕
video-subtitle subtitles input.mp4 --output subtitles.srt

# 查看系统信息
video-subtitle info

# 显示工作流程图
video-subtitle workflow
    '''
    
    syntax = Syntax(cli_code, "bash", theme="monokai", line_numbers=True)
    console.print(syntax)


def demo_system_info():
    """演示系统信息检测"""
    console.print("\n🔍 [bold]系统信息检测[/bold]")
    
    try:
        # 检测设备
        device = detect_device()
        console.print(f"🎯 检测到设备: [green]{device}[/green]")
        
        # 显示详细系统信息
        log_system_info()
        
    except Exception as e:
        console.print(f"[red]系统信息检测失败: {e}[/red]")


def demo_cache_management():
    """演示缓存管理"""
    console.print("\n💾 [bold]缓存管理演示[/bold]")
    
    try:
        cache = CacheManager()
        cache_info = cache.get_cache_info()
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("属性", style="white")
        table.add_column("值", style="green")
        
        table.add_row("缓存目录", cache_info["cache_dir"])
        table.add_row("缓存文件数", str(cache_info["num_files"]))
        table.add_row("总大小 (MB)", f"{cache_info['total_size_mb']:.2f}")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]缓存管理演示失败: {e}[/red]")


def demo_configuration():
    """演示配置管理"""
    console.print("\n⚙️ [bold]配置管理演示[/bold]")
    
    try:
        # 创建配置
        config = ConfigModel(
            device="mps",
            enable_tts=True,
            max_retries=5,
            log_level="DEBUG"
        )
        
        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("配置项", style="white")
        table.add_column("值", style="green")
        table.add_column("类型", style="cyan")
        
        table.add_row("设备", config.device, type(config.device).__name__)
        table.add_row("TTS启用", str(config.enable_tts), type(config.enable_tts).__name__)
        table.add_row("最大重试", str(config.max_retries), type(config.max_retries).__name__)
        table.add_row("日志级别", config.log_level, type(config.log_level).__name__)
        table.add_row("音频采样率", str(config.audio_sample_rate), type(config.audio_sample_rate).__name__)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]配置管理演示失败: {e}[/red]")


def main():
    """主演示函数"""
    show_banner()
    
    console.print("🚀 [bold green]欢迎来到视频字幕AI处理系统演示！[/bold green]\n")
    
    # 系统架构展示
    show_architecture()
    
    # 特性展示
    show_features()
    
    # 工作流展示
    show_workflow()
    
    # 配置示例
    show_configuration_example()
    
    # CLI示例
    show_cli_examples()
    
    # 系统信息
    demo_system_info()
    
    # 缓存管理
    demo_cache_management()
    
    # 配置管理
    demo_configuration()
    
    # 总结
    console.print("\n" + "="*60)
    console.print("🎉 [bold green]演示完成！[/bold green]")
    console.print("\n📋 [bold]下一步操作建议：[/bold]")
    console.print("  1. 安装依赖: [cyan]pip install -e .[/cyan]")
    console.print("  2. 运行测试: [cyan]pytest tests/[/cyan]")
    console.print("  3. 处理视频: [cyan]video-subtitle process your_video.mp4[/cyan]")
    console.print("  4. 查看帮助: [cyan]video-subtitle --help[/cyan]")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--dev-container":
        console.print("\n🐳 [bold]Dev Container 模式：[/bold]")
        console.print("  在VSCode中按 [cyan]Ctrl+Shift+P[/cyan]")
        console.print("  执行: [cyan]Dev Containers: Reopen in Container[/cyan]")


if __name__ == "__main__":
    main() 