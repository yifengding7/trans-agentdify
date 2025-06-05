"""Web GUI interface for video subtitle processing."""

import gradio as gr
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Tuple, List
import json
import time

from .core.agent import VideoSubtitleAgent
from .core.state import ConfigModel
from .utils.exceptions import ProcessingError
from loguru import logger


class VideoSubtitleGUI:
    """Web GUI for video subtitle processing."""
    
    def __init__(self):
        self.agent = None
        self.current_config = self._get_default_config()
        
    def _get_default_config(self) -> dict:
        """Get default configuration."""
        return {
            "device": "auto",
            "enable_tts": False,
            "enable_term_processing": True,
            "max_retries": 3,
            "log_level": "INFO",
            "source_language": "eng",
            "target_language": "cmn"
        }
    
    def _update_config(self, **kwargs) -> None:
        """Update configuration."""
        self.current_config.update(kwargs)
        # 重新创建agent
        self.agent = VideoSubtitleAgent(config=self.current_config)
        logger.info(f"Configuration updated: {self.current_config}")
    
    def process_video(
        self, 
        video_file: Optional[str], 
        device: str,
        enable_tts: bool,
        enable_term_processing: bool,
        max_retries: int,
        progress=gr.Progress()
    ) -> Tuple[str, str, str, str]:
        """Process video file and return results."""
        
        if not video_file:
            return "❌ 请先上传视频文件", "", "", ""
        
        try:
            # 更新配置
            self._update_config(
                device=device,
                enable_tts=enable_tts,
                enable_term_processing=enable_term_processing,
                max_retries=max_retries
            )
            
            # 详细的进度步骤
            steps = [
                (0.05, "🚀 初始化处理环境..."),
                (0.10, "📁 创建工作目录..."),
                (0.15, "🎵 开始音频提取..."),
                (0.30, "🗣️ 语音识别处理中，这可能需要几分钟..."),
                (0.50, "🌐 AI翻译处理中..."),
                (0.65, "📝 专业术语优化中..." if enable_term_processing else "📝 跳过术语处理..."),
                (0.75, "🔗 生成双语字幕..."),
                (0.85, "🎙️ 语音合成处理中..." if enable_tts else "🎙️ 跳过语音合成..."),
                (0.92, "🎥 最终视频封装..."),
                (0.95, "📋 整理处理结果..."),
                (1.0, "✅ 处理完成！")
            ]
            
            # 显示初始进度
            for step_progress, step_desc in steps[:3]:
                progress(step_progress, desc=step_desc)
                time.sleep(0.5)  # 让用户看到步骤变化
            
            # 创建临时工作目录
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                input_path = Path(video_file)
                
                # 显示主要处理步骤
                for i, (step_progress, step_desc) in enumerate(steps[3:-2]):
                    progress(step_progress, desc=step_desc)
                    if i == 0:  # 语音识别步骤，时间较长
                        time.sleep(1)
                    else:
                        time.sleep(0.8)
                
                # 实际处理视频
                progress(0.88, desc="🔄 执行AI处理流程...")
                result = self.agent.process_video(
                    input_path=str(input_path),
                    working_directory=str(temp_path)
                )
                
                # 显示最后的步骤
                for step_progress, step_desc in steps[-2:]:
                    progress(step_progress, desc=step_desc)
                    time.sleep(0.5)
                
                # 读取生成的文件
                english_srt = ""
                chinese_srt = ""
                merged_srt = ""
                
                if result.get("english_srt_path"):
                    english_srt_path = Path(result["english_srt_path"])
                    if english_srt_path.exists():
                        english_srt = english_srt_path.read_text(encoding='utf-8')
                
                if result.get("chinese_srt_path"):
                    chinese_srt_path = Path(result["chinese_srt_path"])
                    if chinese_srt_path.exists():
                        chinese_srt = chinese_srt_path.read_text(encoding='utf-8')
                
                if result.get("merged_srt_path"):
                    merged_srt_path = Path(result["merged_srt_path"])
                    if merged_srt_path.exists():
                        merged_srt = merged_srt_path.read_text(encoding='utf-8')
                
                # 生成处理报告
                report = self._generate_report(result)
                
                return report, english_srt, chinese_srt, merged_srt
                
        except Exception as e:
            logger.error(f"处理视频时出错: {e}")
            return f"❌ 处理失败: {str(e)}", "", "", ""
    
    def _generate_report(self, result: dict) -> str:
        """Generate processing report."""
        report_lines = [
            "# 🎬 视频字幕处理报告",
            "",
            "## ✅ 处理状态",
        ]
        
        # 检查各个步骤的状态
        steps = [
            ("audio_extraction_result", "🎵 音频提取"),
            ("speech_to_text_result", "🗣️ 语音识别"),
            ("translation_result", "🌐 翻译处理"),
            ("term_processing_result", "📝 术语处理"),
            ("subtitle_merge_result", "🔗 字幕合并"),
            ("text_to_speech_result", "🎙️ 语音合成"),
            ("video_muxing_result", "🎥 视频封装")
        ]
        
        for step_key, step_name in steps:
            if step_key in result and result[step_key]:
                status = result[step_key].status.value
                if status == "completed":
                    report_lines.append(f"- {step_name}: ✅ 完成")
                elif status == "failed":
                    report_lines.append(f"- {step_name}: ❌ 失败")
                elif status == "skipped":
                    report_lines.append(f"- {step_name}: ⏭️ 跳过")
                else:
                    report_lines.append(f"- {step_name}: ⏳ {status}")
        
        report_lines.extend([
            "",
            "## 📁 生成文件",
        ])
        
        if result.get("english_srt_path"):
            report_lines.append("- 📄 英文字幕文件")
        if result.get("chinese_srt_path"):
            report_lines.append("- 📄 中文字幕文件")
        if result.get("merged_srt_path"):
            report_lines.append("- 📄 双语字幕文件")
        if result.get("final_video_path"):
            report_lines.append("- 🎥 最终视频文件")
        
        # 添加配置信息
        report_lines.extend([
            "",
            "## ⚙️ 处理配置",
            f"- 设备: {self.current_config.get('device', 'auto')}",
            f"- TTS启用: {'是' if self.current_config.get('enable_tts') else '否'}",
            f"- 术语处理: {'是' if self.current_config.get('enable_term_processing') else '否'}",
            f"- 最大重试: {self.current_config.get('max_retries', 3)}",
        ])
        
        return "\n".join(report_lines)
    
    def create_interface(self) -> gr.Interface:
        """Create Gradio interface."""
        
        with gr.Blocks(
            title="🎬 视频字幕AI处理系统",
            theme=gr.themes.Soft(),
            css="""
                .gradio-container {
                    max-width: 1200px;
                    margin: auto;
                }
                .upload-area {
                    border: 2px dashed #ccc;
                    border-radius: 10px;
                    padding: 20px;
                    text-align: center;
                    margin: 20px 0;
                }
                #processing-status {
                    background: linear-gradient(90deg, #4CAF50, #45a049);
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    text-align: center;
                    margin: 10px 0;
                    font-weight: bold;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .progress-indicator {
                    animation: pulse 2s infinite;
                }
                @keyframes pulse {
                    0% { opacity: 1; }
                    50% { opacity: 0.7; }
                    100% { opacity: 1; }
                }
            """
        ) as interface:
            
            # 标题
            gr.Markdown("""
            # 🎬 视频字幕AI处理系统
            
            **基于LangGraph的智能化视频字幕生成系统**
            
            上传视频文件，系统将自动进行语音识别、翻译和字幕生成。
            """)
            
            with gr.Row():
                with gr.Column(scale=1):
                    # 文件上传区域
                    gr.Markdown("## 📁 上传视频")
                    video_input = gr.File(
                        label="选择视频文件",
                        file_types=[".mp4", ".avi", ".mov", ".mkv", ".flv"],
                        height=120
                    )
                    
                    # 配置选项
                    gr.Markdown("## ⚙️ 处理配置")
                    
                    device_choice = gr.Dropdown(
                        choices=["auto", "cpu", "mps", "cuda"],
                        value="auto",
                        label="计算设备",
                        info="选择用于AI推理的设备"
                    )
                    
                    enable_tts = gr.Checkbox(
                        label="启用文本转语音",
                        value=False,
                        info="是否生成中文语音"
                    )
                    
                    enable_term_processing = gr.Checkbox(
                        label="启用术语处理",
                        value=True,
                        info="对专业术语进行后处理"
                    )
                    
                    max_retries = gr.Slider(
                        minimum=1,
                        maximum=5,
                        value=3,
                        step=1,
                        label="最大重试次数",
                        info="处理失败时的重试次数"
                    )
                    
                    # 处理按钮
                    process_btn = gr.Button(
                        "🚀 开始处理",
                        variant="primary",
                        size="lg"
                    )
                
                with gr.Column(scale=2):
                    # 处理结果区域
                    gr.Markdown("## 📊 处理结果")
                    
                    # 添加处理状态显示
                    with gr.Row():
                        processing_status = gr.Markdown(
                            value="🔮 **状态**: 等待处理...",
                            elem_id="processing-status"
                        )
                    
                    # 处理报告
                    report_output = gr.Markdown(
                        value="等待处理...",
                        label="处理报告"
                    )
                    
                    # 字幕文件展示
                    with gr.Tabs():
                        with gr.Tab("📄 英文字幕"):
                            english_srt_output = gr.Textbox(
                                label="English Subtitles",
                                lines=10,
                                max_lines=20,
                                show_copy_button=True
                            )
                        
                        with gr.Tab("📄 中文字幕"):
                            chinese_srt_output = gr.Textbox(
                                label="Chinese Subtitles",
                                lines=10,
                                max_lines=20,
                                show_copy_button=True
                            )
                        
                        with gr.Tab("📄 双语字幕"):
                            merged_srt_output = gr.Textbox(
                                label="Bilingual Subtitles",
                                lines=10,
                                max_lines=20,
                                show_copy_button=True
                            )
            
            # 示例和说明
            gr.Markdown("""
            ## 📝 使用说明
            
            1. **上传视频**: 支持 MP4, AVI, MOV, MKV, FLV 格式
            2. **配置参数**: 根据需要调整处理参数
            3. **开始处理**: 点击处理按钮，查看实时进度条
            4. **监控进度**: 观察详细的处理步骤和进度百分比
            5. **查看结果**: 在右侧查看生成的字幕文件
            
            ## 🎯 功能特性
            
            - 🤖 **智能语音识别**: 自动识别视频中的英文语音
            - 🌐 **自动翻译**: 将英文字幕翻译为中文
            - 📝 **术语处理**: 对专业术语进行优化处理
            - 🔗 **字幕合并**: 生成双语对照字幕
            - 🎙️ **语音合成**: 可选的中文语音生成
            - 📊 **实时进度**: 详细显示每个处理步骤的进度
            
            ## ⚠️ 注意事项
            
            - 处理时间取决于视频长度和复杂度
            - 建议视频文件不超过100MB
            - 确保视频包含清晰的英文语音
            - 处理过程中请保持浏览器窗口打开
            - 进度条会显示当前处理的具体步骤
            """)
            
            # 绑定处理事件
            process_btn.click(
                fn=self.process_video,
                inputs=[
                    video_input,
                    device_choice,
                    enable_tts,
                    enable_term_processing,
                    max_retries
                ],
                outputs=[
                    report_output,
                    english_srt_output,
                    chinese_srt_output,
                    merged_srt_output
                ],
                show_progress=True
            )
        
        return interface


def launch_gui(
    server_name: str = "127.0.0.1",
    server_port: int = 7860,
    share: bool = False,
    debug: bool = False
):
    """Launch the GUI application."""
    gui = VideoSubtitleGUI()
    interface = gui.create_interface()
    
    print(f"""
    🎬 视频字幕AI处理系统 启动中...
    
    📍 访问地址: http://{server_name}:{server_port}
    🌐 公网分享: {'已启用' if share else '未启用'}
    🐛 调试模式: {'已启用' if debug else '未启用'}
    
    按 Ctrl+C 停止服务
    """)
    
    interface.launch(
        server_name=server_name,
        server_port=server_port,
        share=share,
        debug=debug,
        show_error=True,
        inbrowser=True
    )


if __name__ == "__main__":
    launch_gui() 