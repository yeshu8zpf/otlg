import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from compare.burr_compare.burr_imports import import_burr_modules
from pathlib import Path

JsonMapping, D2RQMapping, calculate_metrics = import_burr_modules(Path("/root/ontology"))
print(JsonMapping, D2RQMapping, calculate_metrics)