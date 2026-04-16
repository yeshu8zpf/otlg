from __future__ import annotations

import copy
from collections import Counter
from typing import Any, Dict, Iterable, List


def _prepare_elements(elements: Iterable[Any], *, name_based: bool) -> List[Any]:
    prepared = []
    for el in elements:
        x = copy.deepcopy(el)
        if hasattr(x, "set_eq_strategy"):
            try:
                x.set_eq_strategy(name_based=name_based)
            except TypeError:
                pass
        prepared.append(x)
    return prepared


def _compare_one_category(
    reference_elements: Iterable[Any],
    prediction_elements: Iterable[Any],
    *,
    name_based: bool,
) -> Dict[str, Any]:
    ref_elems = _prepare_elements(reference_elements, name_based=name_based)
    pred_elems = _prepare_elements(prediction_elements, name_based=name_based)

    ref_counter = Counter(ref_elems)
    pred_counter = Counter(pred_elems)

    matched_counts: Dict[Any, int] = {}
    for key, ref_count in ref_counter.items():
        if key in pred_counter:
            matched_counts[key] = min(ref_count, pred_counter[key])

    missing_counter = ref_counter - pred_counter
    extra_counter = pred_counter - ref_counter

    matched_items: List[str] = []
    for key, cnt in matched_counts.items():
        matched_items.extend([repr(key)] * cnt)

    missing_items: List[str] = []
    for key, cnt in missing_counter.items():
        missing_items.extend([repr(key)] * cnt)

    extra_items: List[str] = []
    for key, cnt in extra_counter.items():
        extra_items.extend([repr(key)] * cnt)

    return {
        "num_reference": sum(ref_counter.values()),
        "num_prediction": sum(pred_counter.values()),
        "num_matched": sum(matched_counts.values()),
        "num_missing_in_prediction": sum(missing_counter.values()),
        "num_extra_in_prediction": sum(extra_counter.values()),
        "matched": matched_items,
        "missing_in_prediction": missing_items,
        "extra_in_prediction": extra_items,
    }


def build_mismatch_details(reference_mapping: Any, prediction_mapping: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {}

    for mode_name, name_based in [("mapping_based", False), ("name_based", True)]:
        result[mode_name] = {
            "classes": _compare_one_category(
                reference_mapping.get_classes(),
                prediction_mapping.get_classes(),
                name_based=name_based,
            ),
            "relations": _compare_one_category(
                reference_mapping.get_relations(),
                prediction_mapping.get_relations(),
                name_based=name_based,
            ),
            "attributes": _compare_one_category(
                reference_mapping.get_attributes(),
                prediction_mapping.get_attributes(),
                name_based=name_based,
            ),
        }

    return result
