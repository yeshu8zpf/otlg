
import re
import sqlparse
from sqlparse.sql import Where, Comparison, Parenthesis, Identifier
from sqlparse.tokens import Whitespace,Operator, Keyword, Punctuation, Literal, Name,Comparison as Comp

from burr_evaluator.mapping_parser.sql_elements import SQLAttribute, Join, Condition

def parse_sql_where_clause(condition):
    print("Parsing SQL codition:", condition)
    stmt  = sqlparse.parse(f"SELECT * FROM dummy WHERE {condition}")[0]
    where = next(tok for tok in stmt.tokens if isinstance(tok, Where))
    parsed = []
    for comp in filter(lambda t: isinstance(t, Comparison), where.tokens):
        toks = [t for t in comp.tokens if t.ttype is not Whitespace]
        op_idx = next(
            i for i, t in enumerate(toks)
            if (t.ttype is Comp or t.ttype is Operator)
               or (t.value in ("=", "!=", "<>", "<", ">", "<=", ">="))
        )

        left  = toks[op_idx - 1].value
        op    = toks[op_idx].value.upper()
        right = ''.join(t.value for t in toks[op_idx + 1:]).strip()
        parsed.append((left, op, right))#
    if not parsed:
        tokens = [t for t in where.tokens if t.ttype is not Whitespace]
        for i in range(len(tokens) - 2):
            if (tokens[i].ttype in (Name, None) or isinstance(tokens[i], Identifier)):
                if tokens[i+1].ttype in (Operator, Comp) or tokens[i+1].value in ("=", "!=", "<>", "<", ">", "<=", ">="):
                    left  = tokens[i].value
                    op    = tokens[i+1].value.upper()
                    right = tokens[i+2].value
                    parsed.append((left, op, right))
    tokens = [t for t in where.tokens if t.ttype is not Whitespace]
    for i, tok in enumerate(tokens):
        if tok.ttype is Keyword and tok.value.upper() == "IS":
            nxt = tokens[i+1].value.upper() if i+1 < len(tokens) else ""
            if nxt.startswith("NOT"):
                left = tokens[i-1].value
                parsed.append((left, "IS NOT NULL", None))
            else:
                left = tokens[i-1].value
                parsed.append((left, "IS NULL", None))
    for i, tok in enumerate(tokens):
        if (tok.ttype is Name or isinstance(tok, Identifier)) and i+2 < len(tokens):
            if tokens[i+1].ttype is Keyword and tokens[i+1].value.upper().endswith("LIKE"):
                parsed.append((tok.value,
                               tokens[i+1].value.upper(),
                               tokens[i+2].value))

    for i, tok in enumerate(tokens):
        if (tok.ttype is Name or isinstance(tok, Identifier)):
            if (i+3 < len(tokens)
                and tokens[i+1].ttype is Keyword and tokens[i+1].value.upper()=="NOT"
                and tokens[i+2].ttype is Keyword and tokens[i+2].value.upper()=="IN"
                and isinstance(tokens[i+3], Parenthesis)):
                items = tokens[i+3].value.strip("()")
                lst = [item.strip() for item in items.split(",")]
                parsed.append((tok.value, "NOT IN", lst))
            elif (i+2 < len(tokens)
                  and tokens[i+1].ttype is Keyword and tokens[i+1].value.upper()=="IN"
                  and isinstance(tokens[i+2], Parenthesis)):
                items = tokens[i+2].value.strip("()")
                lst = [item.strip() for item in items.split(",")]
                parsed.append((tok.value, "IN", lst))
    for i, tok in enumerate(tokens):
        if (tok.ttype is Name or isinstance(tok, Identifier)):
            if (i+5 < len(tokens)
                and tokens[i+1].ttype is Keyword and tokens[i+1].value.upper()=="NOT"
                and tokens[i+2].ttype is Keyword and tokens[i+2].value.upper()=="BETWEEN"
                and tokens[i+4].ttype is Keyword and tokens[i+4].value.upper()=="AND"):
                low  = tokens[i+3].value
                high = tokens[i+5].value
                parsed.append((tok.value, "NOT BETWEEN", (low, high)))
            elif (i+4 < len(tokens)
                  and tokens[i+1].ttype is Keyword and tokens[i+1].value.upper()=="BETWEEN"
                  and tokens[i+3].ttype is Keyword and tokens[i+3].value.upper()=="AND"):
                low  = tokens[i+2].value
                high = tokens[i+4].value
                parsed.append((tok.value, "BETWEEN", (low, high)))
    assert len(parsed) > 0, f"Could not parse condition: {condition}. Make sure to wrap the condition in single quotes."
    return parsed

def parse_condition(condition):
    print("Parsing condition:", condition)
    conditions = parse_sql_where_clause(condition)
    for condition in conditions:
        if len(condition) == 3:
            left, operator, right = condition
            if "." in left:
                sql_attr = SQLAttribute(table=left.split(".")[0].lower(), attribute=left.split(".")[1].lower())
            else:
                sql_attr = SQLAttribute(attribute=left.lower())
            try:
                right = right.lower() if isinstance(right, str) else right
            except:
                right = right
            return Condition(sql_attr, operator, right)

def parse_pattern(uri_pattern):
    if uri_pattern is None:
            return None
    uri_pattern = uri_pattern[0] if isinstance(uri_pattern, list) else uri_pattern # !TODO This is quickfix for the book scenario
    uri_patterns = re.findall('@@(.*?)@@', uri_pattern)#.group(1).split(".") #!TODO This does not work when having more than one database access
    uri_patterns = [pattern.replace("|urlify", "") for pattern in uri_patterns]
    uri_patterns = [pattern.replace("|encode", "") for pattern in uri_patterns]
    uri_patterns = [pattern.replace("|urlencode", "") for pattern in uri_patterns]
    return [SQLAttribute(table=pattern.split(".")[0].lower(), attribute=pattern.split(".")[1].lower()) for pattern in uri_patterns]