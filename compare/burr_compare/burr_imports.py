from __future__ import annotations

import sys
from pathlib import Path
from typing import Tuple


def import_burr_modules(project_root: Path) -> Tuple[object, object, object]:
    """Import the locally copied Burr evaluator without modifying Burr code."""
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    try:
        import wandb  # noqa: F401
    except ModuleNotFoundError:
        class _WandbStub:
            def __getattr__(self, name):
                def _noop(*args, **kwargs):
                    return None
                return _noop
        sys.modules["wandb"] = _WandbStub()

    from burr_evaluator.mapping_parser.mapping.JsonMapping import JsonMapping
    from burr_evaluator.mapping_parser.mapping.D2RQMapping import D2RQMapping
    from burr_evaluator.metrics.caclulate_metrics import calculate_metrics

    return JsonMapping, D2RQMapping, calculate_metrics
