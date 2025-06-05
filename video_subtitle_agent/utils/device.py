"""Device detection and configuration utilities."""

import platform
import subprocess
from typing import Dict, Any
from loguru import logger


def detect_device() -> str:
    """Automatically detect the best available device for AI processing.
    
    Returns:
        Device string: "mps", "cuda", or "cpu"
    """
    
    # Check for Apple Silicon MPS
    if platform.system() == "Darwin":
        try:
            import torch
            if torch.backends.mps.is_available():
                logger.info("MPS (Apple Silicon acceleration) detected")
                return "mps"
        except ImportError:
            logger.warning("PyTorch not available, falling back to CPU")
    
    # Check for CUDA
    try:
        import torch
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0)
            logger.info(f"CUDA detected: {device_count} device(s), primary: {device_name}")
            return "cuda"
    except ImportError:
        pass
    
    # Fallback to CPU
    logger.info("Using CPU for AI processing")
    return "cpu"


def get_device_config(device: str) -> Dict[str, Any]:
    """Get device-specific configuration.
    
    Args:
        device: Device string ("mps", "cuda", "cpu", or "auto")
        
    Returns:
        Configuration dictionary for the device
    """
    
    if device == "auto":
        device = detect_device()
    
    config = {
        "device": device,
        "torch_dtype": "float32",
        "enable_memory_efficient_attention": False,
        "use_cache": True,
    }
    
    if device == "mps":
        config.update({
            "torch_dtype": "float16",
            "enable_memory_efficient_attention": True,
            "fallback_to_cpu": True,
        })
    
    elif device == "cuda":
        config.update({
            "torch_dtype": "float16",
            "enable_memory_efficient_attention": True,
            "use_flash_attention": True,
        })
    
    elif device == "cpu":
        config.update({
            "torch_dtype": "float32",
            "num_threads": _get_optimal_cpu_threads(),
        })
    
    return config


def _get_optimal_cpu_threads() -> int:
    """Get optimal number of CPU threads for processing."""
    try:
        import os
        # Use half of available CPU cores
        return max(1, os.cpu_count() // 2)
    except:
        return 2


def check_system_requirements() -> Dict[str, bool]:
    """Check system requirements for video processing.
    
    Returns:
        Dictionary with requirement check results
    """
    
    requirements = {
        "python": False,
        "ffmpeg": False,
        "torch": False,
        "sufficient_memory": False,
        "sufficient_disk": False,
    }
    
    # Check Python version
    try:
        import sys
        if sys.version_info >= (3, 10):
            requirements["python"] = True
    except:
        pass
    
    # Check FFmpeg
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            capture_output=True, 
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            requirements["ffmpeg"] = True
    except:
        pass
    
    # Check PyTorch
    try:
        import torch
        requirements["torch"] = True
    except ImportError:
        pass
    
    # Check memory (require at least 4GB available)
    try:
        import psutil
        available_memory_gb = psutil.virtual_memory().available / (1024**3)
        if available_memory_gb >= 4:
            requirements["sufficient_memory"] = True
    except ImportError:
        # Assume sufficient if we can't check
        requirements["sufficient_memory"] = True
    
    # Check disk space (require at least 1GB free)
    try:
        import shutil
        free_space_gb = shutil.disk_usage("/").free / (1024**3)
        if free_space_gb >= 1:
            requirements["sufficient_disk"] = True
    except:
        # Assume sufficient if we can't check
        requirements["sufficient_disk"] = True
    
    return requirements


def log_system_info() -> None:
    """Log comprehensive system information."""
    
    logger.info("=== System Information ===")
    
    # Platform info
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Python: {platform.python_version()}")
    
    # Hardware info
    try:
        import psutil
        logger.info(f"CPU: {psutil.cpu_count()} cores")
        memory_gb = psutil.virtual_memory().total / (1024**3)
        logger.info(f"Memory: {memory_gb:.1f} GB")
    except ImportError:
        logger.info("Hardware info not available (psutil not installed)")
    
    # AI hardware
    device = detect_device()
    logger.info(f"AI Device: {device}")
    
    # Requirements check
    reqs = check_system_requirements()
    logger.info("Requirements check:")
    for req, status in reqs.items():
        status_str = "✓" if status else "✗"
        logger.info(f"  {status_str} {req}")
    
    logger.info("=== End System Information ===")


if __name__ == "__main__":
    log_system_info() 