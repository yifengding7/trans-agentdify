"""File handling utilities for video subtitle processing."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Generator
from loguru import logger


def create_temp_directory(prefix: str = "video_subtitle_") -> str:
    """Create a temporary directory for processing.
    
    Args:
        prefix: Prefix for the temporary directory name
        
    Returns:
        Path to the created temporary directory
    """
    temp_dir = tempfile.mkdtemp(prefix=prefix)
    logger.debug(f"Created temporary directory: {temp_dir}")
    return temp_dir


def cleanup_temp_files(directory: str) -> None:
    """Clean up temporary files and directories.
    
    Args:
        directory: Directory to clean up
    """
    try:
        if os.path.exists(directory):
            shutil.rmtree(directory)
            logger.debug(f"Cleaned up temporary directory: {directory}")
    except Exception as e:
        logger.warning(f"Failed to cleanup {directory}: {e}")


def ensure_directory_exists(path: str) -> Path:
    """Ensure that a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        Path object for the directory
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_video_files(directory: str, recursive: bool = False) -> List[str]:
    """Get all video files from a directory.
    
    Args:
        directory: Directory to search
        recursive: Whether to search recursively
        
    Returns:
        List of video file paths
    """
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v'}
    
    directory = Path(directory)
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return []
    
    video_files = []
    
    if recursive:
        pattern = "**/*"
    else:
        pattern = "*"
    
    for file_path in directory.glob(pattern):
        if file_path.is_file() and file_path.suffix.lower() in video_extensions:
            video_files.append(str(file_path))
    
    logger.info(f"Found {len(video_files)} video files in {directory}")
    return sorted(video_files)


def validate_video_file(file_path: str) -> bool:
    """Validate that a file is a video file and exists.
    
    Args:
        file_path: Path to the video file
        
    Returns:
        True if valid, False otherwise
    """
    path = Path(file_path)
    
    if not path.exists():
        logger.error(f"Video file does not exist: {file_path}")
        return False
    
    if not path.is_file():
        logger.error(f"Path is not a file: {file_path}")
        return False
    
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v'}
    if path.suffix.lower() not in video_extensions:
        logger.warning(f"File does not have a recognized video extension: {file_path}")
        return False
    
    # Check file size (should be larger than 1KB)
    if path.stat().st_size < 1024:
        logger.error(f"Video file is too small: {file_path}")
        return False
    
    return True


def get_safe_filename(filename: str) -> str:
    """Generate a safe filename by removing/replacing problematic characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename
    """
    import re
    
    # Remove or replace problematic characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove multiple consecutive underscores
    safe_name = re.sub(r'_+', '_', safe_name)
    
    # Remove leading/trailing underscores and dots
    safe_name = safe_name.strip('_.')
    
    # Ensure the filename is not empty
    if not safe_name:
        safe_name = "untitled"
    
    return safe_name


def get_unique_filename(directory: str, filename: str) -> str:
    """Get a unique filename in the specified directory.
    
    Args:
        directory: Target directory
        filename: Desired filename
        
    Returns:
        Unique filename (may have suffix added)
    """
    directory = Path(directory)
    path = directory / filename
    
    if not path.exists():
        return filename
    
    # Extract name and extension
    stem = path.stem
    suffix = path.suffix
    
    # Find a unique name
    counter = 1
    while True:
        new_filename = f"{stem}_{counter}{suffix}"
        new_path = directory / new_filename
        if not new_path.exists():
            return new_filename
        counter += 1


def copy_file_with_progress(src: str, dst: str) -> None:
    """Copy a file with progress logging.
    
    Args:
        src: Source file path
        dst: Destination file path
    """
    src_path = Path(src)
    dst_path = Path(dst)
    
    # Ensure destination directory exists
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_size = src_path.stat().st_size
    logger.info(f"Copying {src} to {dst} ({file_size / 1024 / 1024:.1f} MB)")
    
    try:
        shutil.copy2(src, dst)
        logger.success(f"Successfully copied file to {dst}")
    except Exception as e:
        logger.error(f"Failed to copy file: {e}")
        raise


def get_file_info(file_path: str) -> dict:
    """Get detailed information about a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information
    """
    path = Path(file_path)
    
    if not path.exists():
        return {"exists": False}
    
    stat = path.stat()
    
    return {
        "exists": True,
        "size_bytes": stat.st_size,
        "size_mb": stat.st_size / 1024 / 1024,
        "modified_time": stat.st_mtime,
        "is_file": path.is_file(),
        "is_directory": path.is_dir(),
        "extension": path.suffix.lower(),
        "stem": path.stem,
        "name": path.name,
    }


def disk_usage_check(directory: str, required_gb: float = 1.0) -> bool:
    """Check if there's sufficient disk space in the directory.
    
    Args:
        directory: Directory to check
        required_gb: Required space in GB
        
    Returns:
        True if sufficient space is available
    """
    try:
        free_bytes = shutil.disk_usage(directory).free
        free_gb = free_bytes / (1024 ** 3)
        
        if free_gb >= required_gb:
            logger.debug(f"Sufficient disk space: {free_gb:.1f} GB available")
            return True
        else:
            logger.warning(f"Insufficient disk space: {free_gb:.1f} GB available, {required_gb} GB required")
            return False
            
    except Exception as e:
        logger.error(f"Failed to check disk usage: {e}")
        return False


def find_files_by_pattern(directory: str, pattern: str, recursive: bool = True) -> List[str]:
    """Find files matching a pattern.
    
    Args:
        directory: Directory to search
        pattern: Glob pattern to match
        recursive: Whether to search recursively
        
    Returns:
        List of matching file paths
    """
    directory = Path(directory)
    
    if recursive:
        search_pattern = f"**/{pattern}"
    else:
        search_pattern = pattern
    
    matching_files = []
    for path in directory.glob(search_pattern):
        if path.is_file():
            matching_files.append(str(path))
    
    return sorted(matching_files)


class TempFileManager:
    """Context manager for temporary file handling."""
    
    def __init__(self, prefix: str = "video_subtitle_"):
        self.prefix = prefix
        self.temp_dir: Optional[str] = None
        self.temp_files: List[str] = []
    
    def __enter__(self) -> "TempFileManager":
        self.temp_dir = create_temp_directory(self.prefix)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir:
            cleanup_temp_files(self.temp_dir)
    
    def create_temp_file(self, suffix: str = "", prefix: str = "") -> str:
        """Create a temporary file within the managed directory.
        
        Args:
            suffix: File suffix/extension
            prefix: File prefix
            
        Returns:
            Path to the temporary file
        """
        if not self.temp_dir:
            raise RuntimeError("TempFileManager not properly initialized")
        
        fd, temp_path = tempfile.mkstemp(
            suffix=suffix,
            prefix=prefix,
            dir=self.temp_dir
        )
        os.close(fd)  # Close the file descriptor
        
        self.temp_files.append(temp_path)
        return temp_path
    
    def get_temp_path(self, filename: str) -> str:
        """Get a path within the temporary directory.
        
        Args:
            filename: Name of the file
            
        Returns:
            Full path within the temporary directory
        """
        if not self.temp_dir:
            raise RuntimeError("TempFileManager not properly initialized")
        
        return os.path.join(self.temp_dir, filename) 