"""
Logging setup. File + console output.
"""

import logging
from pathlib import Path
from openclaw import config


def setup_logging():
    log_dir = Path(config.LOG_DIR)
    log_dir.mkdir(exist_ok=True)

    fmt = "%(asctime)s %(levelname)-8s %(name)s  %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
        format=fmt,
        datefmt=datefmt,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "openclaw.log"),
        ],
    )
