from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set
import re
import sqlite3


# ============================================================
# Result objects
# ============================================================

@dataclass
class VerificationIssue:
    level: str          # "error" | "warning" | "info"
    code: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationReport:
    ok: bool
    errors: List[VerificationIssue] = field(default_factory=list)
    warnings: List[VerificationIssue] = field(default_factory=list)
    infos: List[VerificationIssue] = field(default_factory=list)

    def add(self, level: str, code: str, message: str, **context: Any) -> None:
        issue = VerificationIssue(level=level, code=code, message=message, context=context)
        if level == "error":
            self.errors.append(issue)
        elif level == "warning":
            self.warnings.append(issue)
        else:
            self.infos.append(issue)

    def finalize(self) -> "VerificationReport":
        self.ok = len(self.errors) == 0
        return self

    def summary(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "num_errors": len(self.errors),
            "num_warnings": len(self.warnings),
            "num_infos": len(self.infos),
        }


# ============================================================
# Database schema snapshot
# ============================================================

@dataclass
class DatabaseSchema:
    tables: Dict[str, Set[str]] = field(default_factory=dict)  # table -> set(columns)

    def has_table(self, table: str) -> bool:
        return table in self.tables

    def has_column(self, table: str, column: str) -> bool:
        return table in self.tables and column in self.tables[table]

    @classmethod
    def from_sqlite(cls, conn: sqlite3.Connection) -> "DatabaseSchema":
        schema = cls()
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall() if not row[0].startswith("sqlite_")]
        for t in tables:
            cur.execute(f"PRAGMA table_info({quote_ident(t)})")
            cols = {row[1] for row in cur.fetchall()}
            schema.tables[t] = cols
        return schema


# ============================================================
# Helpers
# ============================================================

IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
QUALIFIED_COL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)$")
TEMPLATE_FIELD_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*)\}")
BURR_TEMPLATE_FIELD_RE = re.compile(r"@@([A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*)@@")


def quote_ident(x: str) -> str:
    return '"' + x.replace('"', '""') + '"'


def parse_qualified_column(s: str) -> Optional[Tuple[str, str]]:
    m = QUALIFIED_COL_RE.match(s.strip())
    if not m:
        return None
    return m.group(1), m.group(2)


def extract_template_columns(template: str) -> List[str]:
    cols = TEMPLATE_FIELD_RE.findall(template)
    cols += BURR_TEMPLATE_FIELD_RE.findall(template)
    # 去重但保序
    seen = set()
    out = []
    for c in cols:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def normalize_join_tokens(join_tokens: List[str]) -> Optional[Tuple[str, str, str]]:
    """
    Expect ["table1.col1", "=", "table2.col2"] or similar.
    """
    if len(join_tokens) != 3:
        return None
    left, op, right = join_tokens
    if op not in {"=", "!=", "<>", ">", "<", ">=", "<="}:
        return None
    return left.strip(), op.strip(), right.strip()


def column_belongs_to_any_table(col: str, tables: List[str]) -> bool:
    parsed = parse_qualified_column(col)
    if not parsed:
        return False
    t, _ = parsed
    return t in tables


# ============================================================
# MappingVerifier
# ============================================================

class MappingVerifier:
    """
    Verifier for OntologyDraft mapping quality.

    Expected draft API:
      - draft.validate() -> (bool, List[str])
      - draft.classes
      - draft.data_properties
      - draft.object_properties
      - draft.subclass_relations
      - draft.class_mappings
      - draft.data_property_mappings
      - draft.object_property_mappings
      - lookup helpers:
          draft.class_index()
          draft.data_property_index()
          draft.object_property_index()
          draft.class_mapping_index()
          draft.data_property_mapping_index()
          draft.object_property_mapping_index()
    """

    def __init__(
        self,
        draft: Any,
        db_schema: Optional[DatabaseSchema] = None,
        sqlite_conn: Optional[sqlite3.Connection] = None,
        uniqueness_sample_limit: int = 10000,
    ) -> None:
        self.draft = draft
        self.db_schema = db_schema
        self.sqlite_conn = sqlite_conn
        self.uniqueness_sample_limit = uniqueness_sample_limit

        if self.db_schema is None and self.sqlite_conn is not None:
            self.db_schema = DatabaseSchema.from_sqlite(self.sqlite_conn)

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------

    def verify(self) -> VerificationReport:
        report = VerificationReport(ok=False)

        self._verify_draft_level(report)
        self._verify_static_mappings(report)

        if self.db_schema is not None:
            self._verify_against_schema(report)

        if self.sqlite_conn is not None:
            self._verify_against_sqlite_execution(report)

        return report.finalize()

    # --------------------------------------------------------
    # Layer 1: draft-level validation
    # --------------------------------------------------------

    def _verify_draft_level(self, report: VerificationReport) -> None:
        ok, errors = self.draft.validate()
        if ok:
            report.add("info", "DRAFT_VALIDATE_OK", "Draft-level validate() passed.")
        else:
            for e in errors:
                report.add("error", "DRAFT_VALIDATE_ERROR", e)

    # --------------------------------------------------------
    # Layer 2: static mapping checks (no DB required)
    # --------------------------------------------------------

    def _verify_static_mappings(self, report: VerificationReport) -> None:
        class_idx = self.draft.class_index()
        dp_idx = self.draft.data_property_index()
        op_idx = self.draft.object_property_index()

        class_map_idx = self.draft.class_mapping_index()
        dp_map_idx = self.draft.data_property_mapping_index()
        op_map_idx = self.draft.object_property_mapping_index()

        # 1) Class mappings
        for cm in self.draft.class_mappings:
            self._check_class_mapping_static(cm, class_idx, report)

        # 2) Data property mappings
        for dm in self.draft.data_property_mappings:
            self._check_data_property_mapping_static(dm, class_idx, dp_idx, class_map_idx, report)

        # 3) Object property mappings
        for om in self.draft.object_property_mappings:
            self._check_object_property_mapping_static(
                om, class_idx, op_idx, class_map_idx, report
            )

        # 4) Accepted ontology elements should have mappings
        for c in self.draft.classes:
            if getattr(c, "status", "accepted") == "accepted" and c.id not in class_map_idx:
                report.add(
                    "error",
                    "MISSING_CLASS_MAPPING",
                    f"Accepted class {c.id} has no class mapping.",
                    class_id=c.id,
                )

        for p in self.draft.data_properties:
            if getattr(p, "status", "accepted") == "accepted" and p.id not in dp_map_idx:
                report.add(
                    "error",
                    "MISSING_DATA_PROPERTY_MAPPING",
                    f"Accepted data property {p.id} has no data property mapping.",
                    property_id=p.id,
                )

        for p in self.draft.object_properties:
            if getattr(p, "status", "accepted") == "accepted" and p.id not in op_map_idx:
                report.add(
                    "error",
                    "MISSING_OBJECT_PROPERTY_MAPPING",
                    f"Accepted object property {p.id} has no object property mapping.",
                    property_id=p.id,
                )

        # 5) subclass evidence quality
        self._check_subclass_static(report)

    def _check_class_mapping_static(
        self,
        cm: Any,
        class_idx: Dict[str, Any],
        report: VerificationReport,
    ) -> None:
        if cm.class_id not in class_idx:
            report.add(
                "error",
                "CLASS_MAPPING_UNKNOWN_CLASS",
                f"Class mapping references unknown class {cm.class_id}.",
                class_id=cm.class_id,
            )
            return

        if not cm.instance_id_template:
            report.add(
                "error",
                "EMPTY_INSTANCE_ID_TEMPLATE",
                f"Class mapping for {cm.class_id} has empty instance_id_template.",
                class_id=cm.class_id,
            )

        if not cm.from_tables:
            report.add(
                "error",
                "EMPTY_FROM_TABLES",
                f"Class mapping for {cm.class_id} has no from_tables.",
                class_id=cm.class_id,
            )

        # template columns should be parseable
        template_cols = extract_template_columns(cm.instance_id_template)
        if not template_cols:
            report.add(
                "warning",
                "NO_TEMPLATE_COLUMNS",
                f"Class mapping for {cm.class_id} has no explicit template columns. "
                f"This may be okay if IDs are synthetic, but is unusual.",
                class_id=cm.class_id,
                template=cm.instance_id_template,
            )

        for col in template_cols:
            parsed = parse_qualified_column(col)
            if not parsed:
                report.add(
                    "error",
                    "BAD_TEMPLATE_COLUMN",
                    f"Class mapping for {cm.class_id} contains malformed template column {col}.",
                    class_id=cm.class_id,
                    column=col,
                )
                continue
            table, _ = parsed
            if cm.from_tables and table not in cm.from_tables:
                report.add(
                    "warning",
                    "TEMPLATE_TABLE_NOT_IN_FROM_TABLES",
                    f"Template column {col} uses table {table}, not listed in from_tables of class {cm.class_id}.",
                    class_id=cm.class_id,
                    column=col,
                    table=table,
                    from_tables=cm.from_tables,
                )

        # joins format
        for j in getattr(cm, "joins", []) or []:
            if normalize_join_tokens(j) is None:
                report.add(
                    "error",
                    "BAD_CLASS_JOIN",
                    f"Class mapping for {cm.class_id} has malformed join tokens: {j}",
                    class_id=cm.class_id,
                    join=j,
                )

    def _check_data_property_mapping_static(
        self,
        dm: Any,
        class_idx: Dict[str, Any],
        dp_idx: Dict[str, Any],
        class_map_idx: Dict[str, Any],
        report: VerificationReport,
    ) -> None:
        if dm.property_id not in dp_idx:
            report.add(
                "error",
                "DATA_PROPERTY_MAPPING_UNKNOWN_PROPERTY",
                f"Data property mapping references unknown property {dm.property_id}.",
                property_id=dm.property_id,
            )
            return

        if dm.from_class not in class_idx:
            report.add(
                "error",
                "DATA_PROPERTY_MAPPING_UNKNOWN_CLASS",
                f"Data property mapping {dm.property_id} references unknown class {dm.from_class}.",
                property_id=dm.property_id,
                from_class=dm.from_class,
            )
            return

        prop = dp_idx[dm.property_id]
        if prop.domain_class != dm.from_class:
            report.add(
                "error",
                "DATA_PROPERTY_DOMAIN_MISMATCH",
                f"Data property mapping {dm.property_id} uses from_class={dm.from_class}, "
                f"but property domain is {prop.domain_class}.",
                property_id=dm.property_id,
                mapping_from_class=dm.from_class,
                property_domain=prop.domain_class,
            )

        parsed = parse_qualified_column(dm.column)
        if not parsed:
            report.add(
                "error",
                "BAD_DATA_PROPERTY_COLUMN",
                f"Data property mapping {dm.property_id} has malformed column {dm.column}.",
                property_id=dm.property_id,
                column=dm.column,
            )
            return

        table, _ = parsed
        cm = class_map_idx.get(dm.from_class)
        if cm is not None and cm.from_tables and table not in cm.from_tables:
            report.add(
                "warning",
                "DATA_PROPERTY_COLUMN_OUTSIDE_CLASS_TABLES",
                f"Data property {dm.property_id} uses column {dm.column}, "
                f"whose table is not in class {dm.from_class}'s from_tables.",
                property_id=dm.property_id,
                column=dm.column,
                class_tables=cm.from_tables,
            )

    def _check_object_property_mapping_static(
        self,
        om: Any,
        class_idx: Dict[str, Any],
        op_idx: Dict[str, Any],
        class_map_idx: Dict[str, Any],
        report: VerificationReport,
    ) -> None:
        if om.property_id not in op_idx:
            report.add(
                "error",
                "OBJECT_PROPERTY_MAPPING_UNKNOWN_PROPERTY",
                f"Object property mapping references unknown property {om.property_id}.",
                property_id=om.property_id,
            )
            return

        if om.from_class not in class_idx:
            report.add(
                "error",
                "OBJECT_PROPERTY_MAPPING_UNKNOWN_FROM_CLASS",
                f"Object property mapping {om.property_id} references unknown from_class {om.from_class}.",
                property_id=om.property_id,
            )
            return

        if om.to_class not in class_idx:
            report.add(
                "error",
                "OBJECT_PROPERTY_MAPPING_UNKNOWN_TO_CLASS",
                f"Object property mapping {om.property_id} references unknown to_class {om.to_class}.",
                property_id=om.property_id,
            )
            return

        prop = op_idx[om.property_id]
        if prop.domain_class != om.from_class:
            report.add(
                "error",
                "OBJECT_PROPERTY_DOMAIN_MISMATCH",
                f"Object property mapping {om.property_id} uses from_class={om.from_class}, "
                f"but property domain is {prop.domain_class}.",
                property_id=om.property_id,
                mapping_from_class=om.from_class,
                property_domain=prop.domain_class,
            )

        if prop.range_class != om.to_class:
            report.add(
                "error",
                "OBJECT_PROPERTY_RANGE_MISMATCH",
                f"Object property mapping {om.property_id} uses to_class={om.to_class}, "
                f"but property range is {prop.range_class}.",
                property_id=om.property_id,
                mapping_to_class=om.to_class,
                property_range=prop.range_class,
            )

        if not om.joins:
            report.add(
                "error",
                "EMPTY_OBJECT_PROPERTY_JOINS",
                f"Object property mapping {om.property_id} has no joins.",
                property_id=om.property_id,
            )

        from_cm = class_map_idx.get(om.from_class)
        to_cm = class_map_idx.get(om.to_class)
        allowed_tables = set()
        if from_cm:
            allowed_tables.update(from_cm.from_tables)
        if to_cm:
            allowed_tables.update(to_cm.from_tables)

        for j in om.joins:
            norm = normalize_join_tokens(j)
            if norm is None:
                report.add(
                    "error",
                    "BAD_OBJECT_PROPERTY_JOIN",
                    f"Object property mapping {om.property_id} has malformed join tokens: {j}",
                    property_id=om.property_id,
                    join=j,
                )
                continue

            left, _, right = norm
            left_parsed = parse_qualified_column(left)
            right_parsed = parse_qualified_column(right)

            if left_parsed is None or right_parsed is None:
                report.add(
                    "error",
                    "BAD_OBJECT_PROPERTY_JOIN_COLUMN",
                    f"Object property mapping {om.property_id} has malformed qualified columns in join {j}.",
                    property_id=om.property_id,
                    join=j,
                )
                continue

            lt, _ = left_parsed
            rt, _ = right_parsed
            for t in (lt, rt):
                if allowed_tables and t not in allowed_tables:
                    report.add(
                        "warning",
                        "JOIN_TABLE_OUTSIDE_CLASS_TABLES",
                        f"Join for property {om.property_id} touches table {t}, "
                        f"which is not in from/to class tables.",
                        property_id=om.property_id,
                        table=t,
                        allowed_tables=sorted(allowed_tables),
                    )

    def _check_subclass_static(self, report: VerificationReport) -> None:
        class_idx = self.draft.class_index()
        class_map_idx = self.draft.class_mapping_index()

        for s in getattr(self.draft, "subclass_relations", []):
            if s.child_class not in class_idx or s.parent_class not in class_idx:
                continue

            child_map = class_map_idx.get(s.child_class)
            parent_map = class_map_idx.get(s.parent_class)

            if child_map and parent_map:
                child_tables = set(child_map.from_tables)
                parent_tables = set(parent_map.from_tables)

                if child_tables and parent_tables and child_tables.isdisjoint(parent_tables):
                    report.add(
                        "warning",
                        "SUBCLASS_TABLE_DISJOINT",
                        f"Subclass relation {s.id} has child and parent classes sourced from disjoint tables. "
                        f"This may be valid, but often indicates missing hierarchy evidence.",
                        subclass_id=s.id,
                        child_tables=sorted(child_tables),
                        parent_tables=sorted(parent_tables),
                    )

            if not getattr(s, "evidence", {}):
                report.add(
                    "warning",
                    "SUBCLASS_NO_EVIDENCE",
                    f"Subclass relation {s.id} has no evidence payload.",
                    subclass_id=s.id,
                )

    # --------------------------------------------------------
    # Layer 3: schema-aware checks (table/column existence)
    # --------------------------------------------------------

    def _verify_against_schema(self, report: VerificationReport) -> None:
        schema = self.db_schema
        assert schema is not None

        # Class mappings
        for cm in self.draft.class_mappings:
            for t in cm.from_tables:
                if not schema.has_table(t):
                    report.add(
                        "error",
                        "UNKNOWN_TABLE_IN_CLASS_MAPPING",
                        f"Class mapping for {cm.class_id} references unknown table {t}.",
                        class_id=cm.class_id,
                        table=t,
                    )

            for col in extract_template_columns(cm.instance_id_template):
                parsed = parse_qualified_column(col)
                if parsed is None:
                    continue
                t, c = parsed
                if not schema.has_table(t):
                    report.add(
                        "error",
                        "UNKNOWN_TEMPLATE_TABLE",
                        f"Instance template for {cm.class_id} references unknown table {t}.",
                        class_id=cm.class_id,
                        table=t,
                    )
                elif not schema.has_column(t, c):
                    report.add(
                        "error",
                        "UNKNOWN_TEMPLATE_COLUMN",
                        f"Instance template for {cm.class_id} references unknown column {col}.",
                        class_id=cm.class_id,
                        column=col,
                    )

            for j in cm.joins:
                norm = normalize_join_tokens(j)
                if norm is None:
                    continue
                self._check_join_columns_exist(norm, report, owner_kind="class_mapping", owner_id=cm.class_id)

        # Data property mappings
        for dm in self.draft.data_property_mappings:
            parsed = parse_qualified_column(dm.column)
            if parsed is None:
                continue
            t, c = parsed
            if not schema.has_table(t):
                report.add(
                    "error",
                    "UNKNOWN_DATA_PROPERTY_TABLE",
                    f"Data property mapping {dm.property_id} references unknown table {t}.",
                    property_id=dm.property_id,
                    table=t,
                )
            elif not schema.has_column(t, c):
                report.add(
                    "error",
                    "UNKNOWN_DATA_PROPERTY_COLUMN",
                    f"Data property mapping {dm.property_id} references unknown column {dm.column}.",
                    property_id=dm.property_id,
                    column=dm.column,
                )

        # Object property mappings
        for om in self.draft.object_property_mappings:
            for j in om.joins:
                norm = normalize_join_tokens(j)
                if norm is None:
                    continue
                self._check_join_columns_exist(norm, report, owner_kind="object_property", owner_id=om.property_id)

    def _check_join_columns_exist(
        self,
        norm_join: Tuple[str, str, str],
        report: VerificationReport,
        owner_kind: str,
        owner_id: str,
    ) -> None:
        schema = self.db_schema
        assert schema is not None

        left, _, right = norm_join
        for col in (left, right):
            parsed = parse_qualified_column(col)
            if parsed is None:
                report.add(
                    "error",
                    "BAD_QUALIFIED_COLUMN",
                    f"{owner_kind} {owner_id} has malformed qualified column {col}.",
                    owner_kind=owner_kind,
                    owner_id=owner_id,
                    column=col,
                )
                continue

            t, c = parsed
            if not schema.has_table(t):
                report.add(
                    "error",
                    "UNKNOWN_JOIN_TABLE",
                    f"{owner_kind} {owner_id} references unknown join table {t}.",
                    owner_kind=owner_kind,
                    owner_id=owner_id,
                    table=t,
                )
            elif not schema.has_column(t, c):
                report.add(
                    "error",
                    "UNKNOWN_JOIN_COLUMN",
                    f"{owner_kind} {owner_id} references unknown join column {col}.",
                    owner_kind=owner_kind,
                    owner_id=owner_id,
                    column=col,
                )

    # --------------------------------------------------------
    # Layer 4: sqlite execution checks
    # --------------------------------------------------------

    def _verify_against_sqlite_execution(self, report: VerificationReport) -> None:
        conn = self.sqlite_conn
        assert conn is not None

        # 1) Can class mappings produce rows?
        for cm in self.draft.class_mappings:
            self._execute_class_mapping_probe(cm, report)

        # 2) Are identifier columns close to unique?
        for cm in self.draft.class_mappings:
            self._check_identifier_uniqueness_sqlite(cm, report)

        # 3) Can object property joins execute?
        for om in self.draft.object_property_mappings:
            self._execute_object_property_probe(om, report)

    def _execute_class_mapping_probe(self, cm: Any, report: VerificationReport) -> None:
        conn = self.sqlite_conn
        assert conn is not None

        if not cm.from_tables:
            return

        try:
            sql = self._build_simple_from_where_sql(
                tables=cm.from_tables,
                joins=cm.joins,
                where=cm.where,
                limit=1,
                select_expr="1"
            )
            cur = conn.cursor()
            cur.execute(sql)
            cur.fetchone()
            report.add(
                "info",
                "CLASS_MAPPING_EXEC_OK",
                f"Class mapping {cm.class_id} executable probe passed.",
                class_id=cm.class_id,
                sql=sql,
            )
        except Exception as e:
            report.add(
                "error",
                "CLASS_MAPPING_EXEC_FAIL",
                f"Class mapping {cm.class_id} executable probe failed: {e}",
                class_id=cm.class_id,
            )

    def _check_identifier_uniqueness_sqlite(self, cm: Any, report: VerificationReport) -> None:
        conn = self.sqlite_conn
        assert conn is not None

        if not cm.identifier_columns:
            report.add(
                "warning",
                "NO_IDENTIFIER_COLUMNS",
                f"Class mapping {cm.class_id} has no identifier columns; uniqueness cannot be checked.",
                class_id=cm.class_id,
            )
            return

        # identifier columns should come from reachable tables
        bad_cols = [c for c in cm.identifier_columns if parse_qualified_column(c) is None]
        if bad_cols:
            report.add(
                "error",
                "BAD_IDENTIFIER_COLUMNS",
                f"Class mapping {cm.class_id} has malformed identifier columns.",
                class_id=cm.class_id,
                bad_columns=bad_cols,
            )
            return

        try:
            cols_sql = ", ".join(cm.identifier_columns)
            sql = self._build_simple_from_where_sql(
                tables=cm.from_tables,
                joins=cm.joins,
                where=cm.where,
                limit=self.uniqueness_sample_limit,
                select_expr=cols_sql,
            )
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()

            if not rows:
                report.add(
                    "warning",
                    "EMPTY_CLASS_MAPPING_RESULT",
                    f"Class mapping {cm.class_id} returned no rows during uniqueness check.",
                    class_id=cm.class_id,
                )
                return

            unique_rows = {tuple(r) for r in rows}
            ratio = len(unique_rows) / max(1, len(rows))
            if ratio < 0.95:
                report.add(
                    "warning",
                    "LOW_IDENTIFIER_UNIQUENESS",
                    f"Class mapping {cm.class_id} identifier columns do not appear unique in sample "
                    f"(ratio={ratio:.3f}).",
                    class_id=cm.class_id,
                    uniqueness_ratio=ratio,
                    num_rows=len(rows),
                    num_unique=len(unique_rows),
                )
            else:
                report.add(
                    "info",
                    "IDENTIFIER_UNIQUENESS_OK",
                    f"Class mapping {cm.class_id} identifier columns appear unique in sample "
                    f"(ratio={ratio:.3f}).",
                    class_id=cm.class_id,
                    uniqueness_ratio=ratio,
                )

        except Exception as e:
            report.add(
                "warning",
                "IDENTIFIER_UNIQUENESS_CHECK_FAIL",
                f"Class mapping {cm.class_id} uniqueness check failed: {e}",
                class_id=cm.class_id,
            )

    def _execute_object_property_probe(self, om: Any, report: VerificationReport) -> None:
        conn = self.sqlite_conn
        assert conn is not None

        class_map_idx = self.draft.class_mapping_index()
        from_cm = class_map_idx.get(om.from_class)
        to_cm = class_map_idx.get(om.to_class)

        if from_cm is None or to_cm is None:
            report.add(
                "warning",
                "OBJECT_PROPERTY_MISSING_CLASS_MAPPING",
                f"Object property {om.property_id} cannot be execution-checked because from/to class mapping is missing.",
                property_id=om.property_id,
            )
            return

        tables = []
        for t in from_cm.from_tables + to_cm.from_tables:
            if t not in tables:
                tables.append(t)

        joins = []
        joins.extend(from_cm.joins or [])
        joins.extend(to_cm.joins or [])
        joins.extend(om.joins or [])

        where = []
        where.extend(from_cm.where or [])
        where.extend(to_cm.where or [])
        where.extend(om.where or [])

        try:
            sql = self._build_simple_from_where_sql(
                tables=tables,
                joins=joins,
                where=where,
                limit=1,
                select_expr="1"
            )
            cur = conn.cursor()
            cur.execute(sql)
            cur.fetchone()
            report.add(
                "info",
                "OBJECT_PROPERTY_EXEC_OK",
                f"Object property mapping {om.property_id} executable probe passed.",
                property_id=om.property_id,
                sql=sql,
            )
        except Exception as e:
            report.add(
                "error",
                "OBJECT_PROPERTY_EXEC_FAIL",
                f"Object property mapping {om.property_id} executable probe failed: {e}",
                property_id=om.property_id,
            )

    # --------------------------------------------------------
    # SQL builder (simple, conservative)
    # --------------------------------------------------------

    def _build_simple_from_where_sql(
        self,
        tables: List[str],
        joins: List[List[str]],
        where: List[str],
        limit: int,
        select_expr: str,
    ) -> str:
        """
        Conservative SQL builder.
        Uses:
          SELECT <expr>
          FROM t1, t2, ...
          WHERE join1 AND join2 AND ...
          LIMIT n

        This is simple and works well enough for verification probes.
        """
        if not tables:
            raise ValueError("No tables provided.")

        from_clause = ", ".join(quote_ident(t) for t in tables)

        predicates = []
        for j in joins or []:
            norm = normalize_join_tokens(j)
            if norm is None:
                raise ValueError(f"Malformed join tokens: {j}")
            left, op, right = norm
            predicates.append(f"{left} {op} {right}")

        for w in where or []:
            predicates.append(f"({w})")

        sql = f"SELECT {select_expr} FROM {from_clause}"
        if predicates:
            sql += " WHERE " + " AND ".join(predicates)
        sql += f" LIMIT {int(limit)}"
        return sql