"""Custom exceptions for the video subtitle agent."""


class VideoSubtitleAgentError(Exception):
    """Base exception for all video subtitle agent errors."""
    pass


class ProcessingError(VideoSubtitleAgentError):
    """Exception raised for non-retryable processing errors."""
    pass


class RetryableError(VideoSubtitleAgentError):
    """Exception raised for retryable processing errors."""
    pass


class ConfigurationError(VideoSubtitleAgentError):
    """Exception raised for configuration-related errors."""
    pass


class ModelLoadError(VideoSubtitleAgentError):
    """Exception raised when models fail to load."""
    pass


class FileNotFoundError(ProcessingError):
    """Exception raised when required files are not found."""
    pass


class UnsupportedFormatError(ProcessingError):
    """Exception raised for unsupported file formats."""
    pass 