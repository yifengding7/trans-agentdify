"""Video Subtitle Agent - AI-powered video subtitle generation system."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .core.agent import VideoSubtitleAgent
from .core.state import ProcessingState, ConfigModel, create_initial_state

# GUI module is optional
try:
    from .gui import VideoSubtitleGUI, launch_gui
    __all__ = ["VideoSubtitleAgent", "ProcessingState", "ConfigModel", "create_initial_state", "VideoSubtitleGUI", "launch_gui"]
except ImportError:
    __all__ = ["VideoSubtitleAgent", "ProcessingState", "ConfigModel", "create_initial_state"] 