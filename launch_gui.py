#!/usr/bin/env python3
"""
🎬 视频字幕AI处理系统 - GUI启动器

这是一个独立的启动脚本，用于快速启动Web GUI界面。

使用方法:
    python launch_gui.py
    python launch_gui.py --host 0.0.0.0 --port 8080 --share
"""

import sys
import argparse
from pathlib import Path


def main():
    """Main entry point for GUI launcher."""
    
    parser = argparse.ArgumentParser(
        description="🎬 视频字幕AI处理系统 - Web GUI启动器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python launch_gui.py                        # 默认配置启动
    python launch_gui.py --host 0.0.0.0         # 监听所有网络接口
    python launch_gui.py --port 8080            # 使用8080端口
    python launch_gui.py --share                # 启用公网分享
    python launch_gui.py --debug                # 开启调试模式
        """
    )
    
    parser.add_argument(
        "--host", 
        default="127.0.0.1", 
        help="服务器地址 (默认: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=7860, 
        help="服务器端口 (默认: 7860)"
    )
    
    parser.add_argument(
        "--share", 
        action="store_true", 
        help="启用公网分享 (生成gradio.live链接)"
    )
    
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="启用调试模式"
    )
    
    args = parser.parse_args()
    
    # 检查依赖
    try:
        import gradio as gr
    except ImportError:
        print("❌ 缺少Gradio依赖，请安装:")
        print("   pip install gradio")
        sys.exit(1)
    
    try:
        from video_subtitle_agent.gui import launch_gui
    except ImportError as e:
        print(f"❌ 导入GUI模块失败: {e}")
        print("请确保已正确安装video_subtitle_agent包:")
        print("   pip install -e .")
        sys.exit(1)
    
    # 显示启动信息
    print("=" * 60)
    print("🎬 视频字幕AI处理系统")
    print("基于LangGraph的智能化视频字幕生成系统")
    print("=" * 60)
    print(f"🌐 服务器地址: {args.host}")
    print(f"🔌 端口号: {args.port}")
    print(f"📤 公网分享: {'已启用' if args.share else '未启用'}")
    print(f"🐛 调试模式: {'已启用' if args.debug else '未启用'}")
    print("=" * 60)
    print("🚀 正在启动GUI服务...")
    print("按 Ctrl+C 停止服务")
    print("=" * 60)
    
    try:
        # 启动GUI
        launch_gui(
            server_name=args.host,
            server_port=args.port,
            share=args.share,
            debug=args.debug
        )
    except KeyboardInterrupt:
        print("\n👋 GUI服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 