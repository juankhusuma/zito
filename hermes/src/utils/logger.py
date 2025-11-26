import logging
import sys
from typing import Any, Dict, Optional

class HermesLogger:
    """Centralized logging utility for Hermes service.

    Provides structured logging with consistent formatting across all modules.
    Supports different log levels and context-aware logging.
    """

    def __init__(self, name: str):
        """Initialize logger for a specific module.

        Args:
            name: Module name (e.g., 'citation', 'search', 'retrieval')
        """
        self.logger = logging.getLogger(f"hermes.{name}")
        self.context = name.upper()

    def debug(self, message: str, **kwargs):
        """Log debug information.

        Args:
            message: Log message
            **kwargs: Additional context key-value pairs
        """
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log informational message.

        Args:
            message: Log message
            **kwargs: Additional context key-value pairs
        """
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message.

        Args:
            message: Log message
            **kwargs: Additional context key-value pairs
        """
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message.

        Args:
            message: Log message
            **kwargs: Additional context key-value pairs
        """
        self._log(logging.ERROR, message, **kwargs)

    def _log(self, level: int, message: str, **kwargs):
        """Internal method to format and log messages.

        Args:
            level: Logging level
            message: Log message
            **kwargs: Additional context key-value pairs
        """
        if kwargs:
            context_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
            formatted_message = f"[{self.context}] {message}: {context_str}"
        else:
            formatted_message = f"[{self.context}] {message}"

        self.logger.log(level, formatted_message)


def setup_logging(level: str = "INFO"):
    """Configure logging for the entire Hermes application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    logging.getLogger("hermes").setLevel(log_level)
