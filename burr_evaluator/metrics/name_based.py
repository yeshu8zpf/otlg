from burr_evaluator.metrics.metric import Metric

class NameBasedPrecision(Metric):
    def __init__(self):
        super(NameBasedPrecision, self).__init__()

    def score(self, el1, el2) -> float:
        for el in el1:
            el.set_eq_strategy(name_based=True)
        for el in el2:
            el.set_eq_strategy(name_based=True)
        el1 = list(set(el1))
        el2 = list(set(el2))
        shared_elements = [x for x in el2 if x in el1]
        if len(el1) == 0 and len(el2) == 0:
            return 1.0
        return len(shared_elements) / len(el2) if len(el2) > 0 else 0.0

    def __str__(self):
        return "NameBasedPrecision"


class NameBasedRecall(Metric):
    def __init__(self):
        super(NameBasedRecall, self).__init__()

    def score(self, el1, el2) -> float:
        for el in el1:
            el.set_eq_strategy(name_based=True)
        for el in el2:
            el.set_eq_strategy(name_based=True)
        el1 = list(set(el1))
        el2 = list(set(el2))

        shared_elements = [x for x in el2 if x in el1]
        if len(el1) == 0 and len(el2) == 0:
            return 1.0
        return len(shared_elements) / len(el1) if len(el1) > 0 else 0.0

    def __str__(self):
        return "NameBasedRecall"