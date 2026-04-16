from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Tuple


def _ensure_path(path: Path) -> None:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def _install_wandb_stub() -> None:
    try:
        import wandb  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    class _WandbStub:
        def __getattr__(self, name):
            def _noop(*args, **kwargs):
                return None
            return _noop

    sys.modules["wandb"] = _WandbStub()


def _install_evaluator_alias() -> None:
    """
    Some local Burr copies import with `from evaluator...`,
    while your repo keeps the folder name as `burr_evaluator`.
    This alias lets both styles work without modifying Burr source.
    """
    if "evaluator" in sys.modules:
        return

    try:
        burr_eval = importlib.import_module("burr_evaluator")
        sys.modules["evaluator"] = burr_eval
    except ModuleNotFoundError:
        # Fine if a real `evaluator` package already exists or Burr copy uses that name.
        pass


def import_burr_modules(project_root: Path) -> Tuple[object, object, object]:
    """
    Import the locally copied Burr evaluator without modifying Burr code.
    """
    _ensure_path(project_root)
    _install_wandb_stub()
    _install_evaluator_alias()

    try:
        from burr_evaluator.mapping_parser.mapping.JsonMapping import JsonMapping
        from burr_evaluator.mapping_parser.mapping.D2RQMapping import D2RQMapping
        from burr_evaluator.metrics.caclulate_metrics import calculate_metrics
        return JsonMapping, D2RQMapping, calculate_metrics
    except ModuleNotFoundError:
        # Fallback: some copies may expose package as `evaluator`
        from evaluator.mapping_parser.mapping.JsonMapping import JsonMapping
        from evaluator.mapping_parser.mapping.D2RQMapping import D2RQMapping
        from evaluator.metrics.caclulate_metrics import calculate_metrics
        return JsonMapping, D2RQMapping, calculate_metrics