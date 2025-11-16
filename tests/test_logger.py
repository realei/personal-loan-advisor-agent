"""Unit tests for logging system."""

import pytest
import logging
import tempfile
from pathlib import Path

from src.utils.logger import get_logger, setup_logger


class TestLogger:
    """Test suite for logging utilities."""

    def test_get_logger_basic(self):
        """Test basic logger creation."""
        logger = get_logger("test_module")

        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_with_level(self):
        """Test logger with custom level."""
        logger = get_logger("test_module_debug", level="DEBUG")

        assert logger.level == logging.DEBUG

    def test_setup_logger_with_file(self):
        """Test logger with file output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"

            logger = setup_logger(
                name="test_file_logger",
                level="INFO",
                log_file=str(log_file),
                console_output=False
            )

            # Log a message
            logger.info("Test message")

            # Check file was created and contains message
            assert log_file.exists()
            content = log_file.read_text()
            assert "Test message" in content

    def test_setup_logger_console_only(self):
        """Test logger with console output only."""
        logger = setup_logger(
            name="test_console_logger",
            level="WARNING",
            console_output=True
        )

        assert logger is not None
        assert len(logger.handlers) == 1  # Only console handler

    def test_logger_levels(self):
        """Test different log levels."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "levels.log"

            logger = setup_logger(
                name="test_levels",
                level="DEBUG",
                log_file=str(log_file),
                console_output=False
            )

            # Log different levels
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

            content = log_file.read_text()
            assert "Debug message" in content
            assert "Info message" in content
            assert "Warning message" in content
            assert "Error message" in content

    def test_logger_no_duplicate_handlers(self):
        """Test that getting same logger doesn't create duplicate handlers."""
        logger1 = get_logger("test_no_dup")
        handler_count_1 = len(logger1.handlers)

        logger2 = get_logger("test_no_dup")
        handler_count_2 = len(logger2.handlers)

        # Should be the same logger instance
        assert logger1 is logger2
        assert handler_count_1 == handler_count_2

    def test_colored_formatter(self):
        """Test colored output (basic check)."""
        logger = setup_logger(
            name="test_colored",
            level="INFO",
            console_output=True,
            colored=True
        )

        # Should not raise exception
        logger.info("Colored message")

    def test_uncolored_formatter(self):
        """Test uncolored output."""
        logger = setup_logger(
            name="test_uncolored",
            level="INFO",
            console_output=True,
            colored=False
        )

        # Should not raise exception
        logger.info("Uncolored message")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
