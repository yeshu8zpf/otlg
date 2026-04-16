from .json_mapping import preprocess_gt_json, preprocess_prediction_json
from .ttl_mapping import preprocess_gt_ttl

__all__ = [
    "preprocess_gt_json",
    "preprocess_prediction_json",
    "preprocess_gt_ttl",
]