from burr_evaluator.metrics.metric import Metric
from burr_evaluator.mapping_parser.mapping import D2RQMapping
from collections import Counter

class MappingBasedPrecision(Metric):
    def __init__(self):
        super(MappingBasedPrecision, self).__init__()

    def score(self, el1: D2RQMapping, el2: D2RQMapping) -> float:
        for el in el1:
            el.set_eq_strategy(name_based=False)
        for el in el2:
            el.set_eq_strategy(name_based=False)
        
        c1 = Counter(el1) 
        c2 = Counter(el2)  
        intersection_sum = sum(min(c1[x], c2[x]) for x in (c1.keys() & c2.keys()))
        total_pred = sum(c2.values())
        if total_pred == 0:
            return 1.0 if len(c1) == 0 else 0.0
        
        precision = intersection_sum / total_pred
        return precision

    def __str__(self):
        return "MappingBasedPrecision (Bag-based)"


class MappingBasedRecall(Metric):
    def __init__(self):
        super(MappingBasedRecall, self).__init__()

    def score(self, el1: D2RQMapping, el2: D2RQMapping):
        for el in el1:
            el.set_eq_strategy(name_based=False)
        for el in el2:
            el.set_eq_strategy(name_based=False)

        c1 = Counter(el1)
        c2 = Counter(el2)

        tp_counter = c1 & c2
        fn_counter = Counter()
        for x in c1:
            miss = c1[x] - tp_counter[x]
            if miss > 0:
                fn_counter[x] = miss
        total_true = sum(c1.values())

        if total_true == 0:
            recall = 1.0 if sum(c2.values()) == 0 else 0.0
        else:
            recall = sum(tp_counter.values()) / total_true

        
        return recall
    def __str__(self):
        return "MappingBasedRecall (Bag-based)"
