# -*- coding: utf-8 -*-
"""
TurbineSysSim - Logging Configuration
------------------------------------

Author: Arildo Yank

Centralised logging configuration for the application.
Designed for engineering-grade diagnostics and traceability.
"""

import logging
import sys


def setup_logger(level: int = logging.INFO) -> None:
    """
    Configure application-wide logging.
    """

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers
    if not root_logger.handlers:
        root_logger.addHandler(handler)