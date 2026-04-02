from burr_evaluator.mapping_parser.sql_elements import SQLAttribute, Join
from burr_evaluator.utils.get_jinja_env import get_jinja_env
from burr_evaluator.mapping_parser.utils import parse_condition, parse_pattern
from collections import Counter

import re

class ClassMap:
    mapping_id: str
    uriPattern: str
    join: str
    class_uri: str
    condition: str
    def __init__(self, mapping_id, uriPattern, class_uri, join, parent_classes, condition, prefix, bNodeIdColumns, datastorage, translate_with, confidence=None, cot_prob=None, combined_prob=None) -> None:
        self.uriPattern = uriPattern
        self.mapping_id = mapping_id
        self.class_uri = class_uri
        self.prefix = prefix
        self.datastorage = datastorage
        self.condition = condition
        self.confidence = confidence
        self.cot_prob = cot_prob
        self.combined_prob = combined_prob
        self.sql_bNodeIdColumns = self.parse_bNodeIdColumns(bNodeIdColumns)
        self.join = join
        self.set_eq_strategy()
        self.parent_classes = parent_classes
        self.translate_with = translate_with
        if isinstance(join, list):
            self.sql_join = [self.parse_join(j) for j in join]
        else:
            self.sql_join = [self.parse_join(join)] if self.join is not None else None
        if isinstance(condition, list):
            self.sql_condition = [self.parse_condition(s) for s in condition]
        else:
            self.sql_condition = [self.parse_condition(condition)] if self.condition is not None else None
        self.sql_uri_pattern: SQLAttribute = self.parse_uri_pattern(uriPattern)
        self.uri_pattern = uriPattern

    def parse_condition(self, condition):
        return parse_condition(condition)

    def parse_bNodeIdColumns(self, bNodeIdColumns):
        if isinstance(bNodeIdColumns, list):
            return [SQLAttribute(table=pattern.split(".")[0].lower(), attribute=pattern.split(".")[1].lower()) for pattern in bNodeIdColumns]
        else:
            if bNodeIdColumns is not None:
                bNodeIdColumns = bNodeIdColumns.split(",")
                return [SQLAttribute(table=pattern.split(".")[0].lower(), attribute=pattern.split(".")[1].lower()) for pattern in bNodeIdColumns]

    def parse_uri_pattern(self, uri_pattern):
        return parse_pattern(uri_pattern)

    def parse_join(self, join):
        join = join.replace(" ", "").replace(">", "").replace("<", "")
        join = join.split("=")
        left = join[0].split(".")
        right = join[1].split(".")
        return Join(SQLAttribute(left[0], left[1].lower()), SQLAttribute(right[0], right[1].lower()))
    
    def get_d2rq_mapping(self):
        renders = []
        if self.parent_classes is not None:
            for parent in self.parent_classes:
                renders.append(get_jinja_env() \
                    .get_template('subclass.j2') \
                    .render(
                        mapping_name=self.mapping_id,
                        parent_class = parent,
                        class_name = self.mapping_id,
                        prefix = self.prefix
                    ))
                
        bNodeIdColumns = process_bNodeIdColumns(self.sql_bNodeIdColumns) if self.sql_bNodeIdColumns is not None else None
        classmap_render = get_jinja_env() \
                .get_template('classmap.j2') \
                .render(
                    class_name=self.class_uri,
                    mapping_name = self.mapping_id,
                    uri_patterns=self.uri_pattern,
                    bNodeIdColumns = bNodeIdColumns,
                    #additional_property=self.additional_property,
                    conditions=self.sql_condition,
                    parent_classes=self.parent_classes,
                    joins = self.sql_join,
                    datastorage=self.datastorage,
                    prefix = self.prefix,
                    translate_with=self.translate_with
                )
        return renders + [classmap_render]
    
    def __eq__(self, other):
        if not isinstance(other, ClassMap):
            return False
        return self._eq_strategy(self, other)
    
    def __hash__(self) -> int:
        return self._hash_strategy(self)
        
    def set_eq_strategy(self, name_based=False):
        self._hash_strategy = hash_by_property_name if name_based else hash_by_edge_query_and_classes
        self._eq_strategy = name_based_equality if name_based else concept_based_equality

    def get_ttl_string(self):
        class_maps = self.get_d2rq_mapping()
        return "\n".join(class_maps)       

    def __repr__(self):
        return f"ClassMap(uriPattern={self.uriPattern}, class_uri={self.class_uri}, eq_strategy={self._eq_strategy})"

def concept_based_equality(c1: ClassMap, c2: ClassMap) -> bool:
    condition_not_none = c1.sql_condition is not None and c2.sql_condition is not None
    conidition_is_none = c1.sql_condition is None and c2.sql_condition is None
    pattern_not_none = c1.sql_uri_pattern is not None and c2.sql_uri_pattern is not None
    pattern_is_none = c1.sql_uri_pattern is None and c2.sql_uri_pattern is None
    join_not_none = c1.sql_join is not None and c2.sql_join is not None
    join_is_none = c1.sql_join is None and c2.sql_join is None

    if condition_not_none:
        same_condition = set(c1.sql_condition) == set(c2.sql_condition)
    elif conidition_is_none:
        same_condition = True
    else:
        return False
    
    if pattern_not_none:
        same_pattern = set(c1.sql_uri_pattern) == set(c2.sql_uri_pattern)
    elif pattern_is_none:
        same_pattern = True
    else:
        return False
    
    if join_not_none:
        same_join = set(c1.sql_join) == set(c2.sql_join)
    elif join_is_none:
        same_join = True
    else:
        return False
    return same_condition and same_pattern and same_join

def hash_by_edge_query_and_classes(c: ClassMap) -> int:
    return hash((
        frozenset(c.sql_condition) if c.sql_condition is not None else frozenset(),
        frozenset(c.sql_uri_pattern) if c.sql_uri_pattern is not None else frozenset(),
        frozenset(c.sql_join) if c.sql_join is not None else frozenset()
    ))

def name_based_equality(concept1: ClassMap, concept2: ClassMap) -> bool:
    if type(concept1) != ClassMap or type(concept2) != ClassMap:
        print("WARNING - At least one concept is not of type ClassMap", concept1, concept2)
        return concept1 == concept2
    same_name = concept1.class_uri.strip().lower() == concept2.class_uri.strip().lower()
    return same_name

from collections import Counter
from collections.abc import Iterable

def _atom_key(x):
    try:
        return (x.__class__.__name__, x.key())  # falls .key() existiert
    except Exception:
        return (x.__class__.__name__, repr(x))

def freeze(x):
    if x is None:
        return ("__NONE__",)
    if isinstance(x, (int, float, bool, bytes, str)):
        return ("__ATOM__", x)
    if isinstance(x, dict):
        return ("__DICT__", frozenset((freeze(k), freeze(v)) for k, v in x.items()))
    if isinstance(x, Iterable):
        frozen_elems = [freeze(e) for e in x]
        counts = Counter(frozen_elems)
        return ("__MULTISET__", frozenset(counts.items()))
    return ("__ATOM__", _atom_key(x))

def hash_by_property_name(concept: ClassMap) -> int:
    return hash(concept.class_uri.strip().lower())

def process_bNodeIdColumns(columns):
    res = ""
    for col in columns:
        res += f"{col},"
    #remove whitespaces
    res = re.sub(r'\s+', '', res)
    return res[:-1]