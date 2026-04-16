import sys
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from compare.burr_compare import gt_resolution, runner

pred_path = ROOT / "outputs" / "mondial" / "mapping.json"
scenario_dir = ROOT / "burr_benchmark" / "real-world" / "iswc"
mappings_dir = scenario_dir / "mappings"
merged_gt_path = ROOT / "debug" / "mondial_gt_merged.json"
compare_out_path = ROOT / "debug" / "mondial_compare_result.json"

print("pred_path:", pred_path, pred_path.exists())
print("scenario_dir:", scenario_dir, scenario_dir.exists())
print("mappings_dir:", mappings_dir, mappings_dir.exists())

# 1) merge GT json fragments
json_parts = sorted(
    p for p in mappings_dir.glob("*.json")
    if p.name != "meta.json"
)
print("json parts:", len(json_parts))

merged_gt = gt_resolution.merge_mapping_json_files(json_parts)
with open(merged_gt_path, "w", encoding="utf-8") as f:
    json.dump(merged_gt, f, indent=2, ensure_ascii=False)
print("merged_gt written to:", merged_gt_path)

# 2) build compare config
config = runner.CompareConfig(
    project_root=ROOT,
    scenario_dir=scenario_dir,
    prediction_path=pred_path,
    output_path=compare_out_path,
    gt_path=merged_gt_path,
    gt_kind="json",
)

print("running compare...")
result = runner.run_compare(config)

print("\n=== compare finished ===")
print("result type:", type(result).__name__)
if isinstance(result, dict):
    print("top-level result keys:", list(result.keys()))
    print(json.dumps(result, indent=2, ensure_ascii=False)[:4000])

print("\noutput file exists:", compare_out_path.exists(), compare_out_path)