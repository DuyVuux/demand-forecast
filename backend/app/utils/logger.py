from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logging(log_file: Optional[Path] = None) -> None:
    """Configure logging to write both to console and logs/app.log with rotation."""
    base_dir = Path(__file__).resolve().parents[2]  # points to backend/
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    if log_file is None:
        log_file = logs_dir / "app.log"

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # avoid duplicate handlers if reloaded
    for h in list(root.handlers):
        root.removeHandler(h)

    file_handler = RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    root.addHandler(file_handler)
    root.addHandler(stream_handler)

    # Align uvicorn loggers with root handlers
    logging.getLogger("uvicorn").handlers = root.handlers
    logging.getLogger("uvicorn.access").handlers = root.handlers
    logging.getLogger("uvicorn.error").handlers = root.handlers


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
