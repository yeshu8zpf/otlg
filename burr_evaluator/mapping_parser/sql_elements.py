from dataclasses import dataclass
from collections.abc import Iterable
@dataclass(frozen=True)
class SQLAttribute:
    table: str
    attribute: str

    def __post_init__(self):
        # Convert table and attribute to lowercase
        object.__setattr__(self, 'table', self.table.lower())
        object.__setattr__(self, 'attribute', self.attribute.lower())

    def __eq__(self, other):
        return isinstance(other, SQLAttribute) and self.table == other.table and self.attribute == other.attribute

    def __hash__(self):
        return hash((self.table, self.attribute))
    
    def __str__(self):
        return f"{self.table.lower()}.{self.attribute.lower()}"
def _canon_op(op):
    op = op.strip().upper()
    if op == "<>":
        return "!="
    if op == "==":
        return "="
    return op

def _strip_quotes(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s

def _canon_scalar(v):
    if v is None:
        return None
    if isinstance(v, str):
        s = v.strip()
        if s.upper() == "NULL":
            return None
        core = _strip_quotes(s)
        if core.lower() in ("true", "false"):
            return core.upper()
        try:
            if core.isdigit() or (core.startswith("-") and core[1:].isdigit()):
                return int(core)
            if "." in core:
                return float(core)
        except ValueError:
            pass
        return core
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    return v

def _canon_list(lst):
    canon = tuple(_canon_scalar(x) for x in lst)
    return tuple(sorted(canon, key=repr))

def _canon_value(op,value):
    op_u = _canon_op(op)
    if op_u in ("IN", "NOT IN"):
        return _canon_list(value if isinstance(value, Iterable) and not isinstance(value, (str, bytes)) else [value])
    if op_u in ("BETWEEN", "NOT BETWEEN"):
        lo, hi = value
        return (_canon_scalar(lo), _canon_scalar(hi))
    if op_u in ("IS NULL", "IS NOT NULL"):
        return None
    return _canon_scalar(value)

def _canon_name(x) -> str:
    name = getattr(x, "name", x)
    return str(name).strip().lower()

class Condition:
    def __init__(self, sql_attribute: SQLAttribute, operator: str, value):
        self.sql_attribute = sql_attribute
        self.operator = operator
        self.value = value
        self._canon = (
            _canon_name(self.sql_attribute.table),
            _canon_name(self.sql_attribute.attribute),
            _canon_op(self.operator),
            _canon_value(self.operator, self.value)
        )
    
    def __eq__(self, condition):
        if condition is None:
            return False
        return self._canon == condition._canon
    def __hash__(self):
        return hash(self._canon)
    
    def __str__(self):
        return f"{self.sql_attribute} {self.operator} {self.value}"


@dataclass(frozen=True)
class Join:
    left_attribute: SQLAttribute
    right_attribute: SQLAttribute

    def __eq__(self, other):
        if not isinstance(other, Join):
            return False
        return (self.left_attribute == other.left_attribute and self.right_attribute == other.right_attribute) or \
               (self.left_attribute == other.right_attribute and self.right_attribute == other.left_attribute)

    def __hash__(self):
        return hash(frozenset([self.left_attribute, self.right_attribute]))
    
    def __str__(self):
        return f"{self.left_attribute} = {self.right_attribute}"
@dataclass(frozen=True)
class Query:
    content: set