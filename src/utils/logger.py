"""Structured logging utility for the Walmart Retail Intelligence platform."""

import logging
import sys
from pathlib import Path


def setup_logger(name: str = "retail_intelligence", level: str = "INFO") -> logging.Logger:
    """Configure and return a structured console and file logger."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger(name)
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Avoid adding duplicate handlers if logger was already created
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        ch.setLevel(numeric_level)
        logger.addHandler(ch)

        # File handler
        fh = logging.FileHandler(log_dir / "pipeline.log", encoding="utf-8")
        fh.setFormatter(formatter)
        fh.setLevel(numeric_level)
        logger.addHandler(fh)

    return logger


logger = setup_logger()
