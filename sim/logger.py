"""
Module: logger.py
Provides centralized, structured activity logging for OS-SimBench.
Tracks process state transitions, context switches, page faults, and resource events.
"""

import logging
import os
import sys

_LOGGER = None

def setup_logger(log_file: str = None, verbose: bool = False) -> logging.Logger:
    """Configures and returns the central logger instance."""
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    logger = logging.getLogger("OS_SimBench")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)-7s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    if log_file:
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO if not verbose else logging.DEBUG)
    console_format = logging.Formatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    _LOGGER = logger
    return _LOGGER

def get_sim_logger() -> logging.Logger:
    """Returns existing logger or initializes a default logger."""
    global _LOGGER
    if _LOGGER is None:
        default_log = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "reports", "logs", "sim_activity.log"
        )
        return setup_logger(log_file=default_log, verbose=False)
    return _LOGGER
