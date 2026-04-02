from burr_evaluator.metrics.mapping_based import MappingBasedPrecision, MappingBasedRecall
from burr_evaluator.metrics.name_based import NameBasedPrecision, NameBasedRecall
from burr_evaluator.metrics.metric import F1Score
import wandb

def calculate_metrics(reference_mapping, learned_mapping):
    metrics = {
        "mapping_based": {"precision": MappingBasedPrecision, "recall": MappingBasedRecall},
        "name_based": {"precision": NameBasedPrecision, "recall": NameBasedRecall},
    }
    for key, metric_concept in metrics.items():
        values = calculate_local_metrics(reference_mapping, learned_mapping, metric_concept["precision"], metric_concept["recall"])
        metrics[key] = values
        wandb.log({key: values})
        print("Metrics for", key, ":", values)
    
    return metrics

def calculate_local_metrics(reference_mapping, learned_mapping, Precision, Recall):
    cls_precision = Precision()(reference_mapping.get_classes(), learned_mapping.get_classes())
    cls_recall = Recall()(reference_mapping.get_classes(), learned_mapping.get_classes())
    cls_f1 = F1Score()(cls_precision, cls_recall)

    rel_precision = Precision()(reference_mapping.get_relations(), learned_mapping.get_relations())
    rel_recall = Recall()(reference_mapping.get_relations(), learned_mapping.get_relations())
    rel_f1 = F1Score()(rel_precision, rel_recall)

    attr_precision = Precision()(reference_mapping.get_attributes(), learned_mapping.get_attributes())
    attr_recall = Recall()(reference_mapping.get_attributes(), learned_mapping.get_attributes())
    attr_f1 = F1Score()(attr_precision, attr_recall)

    return { "cls_precision": cls_precision, "cls_recall": cls_recall, "cls_f1": cls_f1, "rel_precision": rel_precision, "rel_recall": rel_recall, "rel_f1": rel_f1, "attr_precision": attr_precision, "attr_recall": attr_recall, "attr_f1": attr_f1 }

