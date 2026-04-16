"""Thin wrapper library around Burr evaluator with pre-processing hooks.

This package is meant to replace a long single-file ``burr_compare.py``.
It keeps Burr's original compare/parser/metrics code untouched and only
handles:
- path resolution
- GT / prediction pre-processing
- meta compatibility
- orchestration
"""

from .runner import CompareConfig, run_compare

__all__ = ["CompareConfig", "run_compare"]
