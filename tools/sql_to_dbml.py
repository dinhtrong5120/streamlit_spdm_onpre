import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set

STOP_TOKENS = {
    'not', 'null', 'default', 'constraint', 'primary', 'unique', 'references',
    'check', 'generated', 'as', 'identity', 'collate'
}

def map_type(sql_type: str) -> str:
    t = sql_type.strip().lower()
    if t.startswith('character varying'):
        return 'varchar' + t[len('character varying'):]
    if t.startswith('character('):
        return 'char' + t[len('character'):]
    if t.startswith('timestamp'):
        return 'timestamp'
    if t == 'integer':
        return 'int'
    if t == 'bigint':
        return 'bigint'
    if t == 'text':
        return 'text'
    if t == 'boolean':
        return 'boolean'
    if t.startswith('numeric'):
        return 'numeric' + t[len('numeric'):]
    if t.startswith('double precision'):
        return 'double'
    if t == 'real':
        return 'float'
    return t


def parse_columns(table_body: str) -> List[Tuple[str, str, bool]]:
    """Return list of (column_name, dbml_type, explicit_not_null)."""
    lines = table_body.splitlines()
    result: List[Tuple[str, str, bool]] = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith('--'):
            continue
        # drop trailing comma
        if line.endswith(','):
            line = line[:-1]
        # Skip table-level constraints
        if line.lower().startswith(('constraint ', 'primary key', 'unique ', 'check ', 'foreign key')):
            continue
        parts = line.split()
        if not parts:
            continue
        column_name = parts[0]
        rest = parts[1:]
        type_tokens: List[str] = []
        for tok in rest:
            tl = tok.lower()
            if tl in STOP_TOKENS:
                break
            type_tokens.append(tok)
        if not type_tokens:
            # skip lines without a clear type
            continue
        sql_type = ' '.join(type_tokens)
        dbml_type = map_type(sql_type)
        explicit_not_null = ' not null' in line.lower()
        result.append((column_name, dbml_type, explicit_not_null))
    return result


def parse_tables(sql_text: str) -> Dict[str, List[Tuple[str, str, bool]]]:
    pattern = re.compile(r"CREATE\s+TABLE\s+public\.([A-Za-z0-9_]+)\s*\((.*?)\);", re.S | re.I)
    tables: Dict[str, List[Tuple[str, str, bool]]] = {}
    for match in pattern.finditer(sql_text):
        table_name = match.group(1)
        body = match.group(2)
        tables[table_name] = parse_columns(body)
    return tables


def parse_primary_keys(sql_text: str) -> Dict[str, List[str]]:
    """Return mapping: table -> list of PK columns (ordered)."""
    pk_pattern = re.compile(
        r"ALTER\s+TABLE\s+ONLY\s+public\.([A-Za-z0-9_]+)\s+ADD\s+CONSTRAINT\s+[A-Za-z0-9_\"]+\s+PRIMARY\s+KEY\s*\(([^\)]+)\)\s*;",
        re.I
    )
    table_to_pk: Dict[str, List[str]] = {}
    for m in pk_pattern.finditer(sql_text):
        table = m.group(1)
        cols = [c.strip().strip('"') for c in m.group(2).split(',')]
        table_to_pk[table] = cols
    return table_to_pk


def parse_foreign_keys(sql_text: str) -> List[Tuple[str, List[str], str, List[str]]]:
    """Return list of (src_table, src_cols, dst_table, dst_cols)."""
    fk_pattern = re.compile(
        r"ALTER\s+TABLE\s+ONLY\s+public\.([A-Za-z0-9_]+)\s+ADD\s+CONSTRAINT\s+[A-Za-z0-9_\"]+\s+FOREIGN\s+KEY\s*\(([^\)]*)\)\s+REFERENCES\s+public\.([A-Za-z0-9_]+)\s*\(([^\)]*)\)",
        re.I
    )
    fks: List[Tuple[str, List[str], str, List[str]]] = []
    for m in fk_pattern.finditer(sql_text):
        src_table = m.group(1)
        src_cols = [c.strip().strip('"') for c in m.group(2).split(',')]
        dst_table = m.group(3)
        dst_cols = [c.strip().strip('"') for c in m.group(4).split(',')]
        if len(src_cols) == len(dst_cols) and len(src_cols) > 0:
            fks.append((src_table, src_cols, dst_table, dst_cols))
    return fks


def build_dbml(tables: Dict[str, List[Tuple[str, str, bool]]],
               table_to_pk: Dict[str, List[str]],
               fks: List[Tuple[str, List[str], str, List[str]]]) -> str:
    lines: List[str] = []

    # Tables with columns and pk/not null flags
    for table_name in sorted(tables.keys()):
        lines.append(f"Table {table_name} {{")
        col_defs = tables[table_name]
        pk_cols: Set[str] = set(table_to_pk.get(table_name, []))
        for column_name, dbml_type, explicit_not_null in col_defs:
            attrs: List[str] = []
            if column_name in pk_cols:
                attrs.append('pk')
                # pk implies not null
                if not explicit_not_null:
                    attrs.append('not null')
            else:
                if explicit_not_null:
                    attrs.append('not null')
            attr_str = f" [{', '.join(attrs)}]" if attrs else ''
            lines.append(f"  {column_name} {dbml_type}{attr_str}")
        lines.append("}")
        lines.append("")

    # Relationships
    for src_table, src_cols, dst_table, dst_cols in fks:
        for s, d in zip(src_cols, dst_cols):
            lines.append(f"Ref: {src_table}.{s} > {dst_table}.{d}")

    return "\n".join(lines).rstrip() + "\n"


def convert_sql_to_dbml(sql_text: str) -> str:
    tables = parse_tables(sql_text)
    table_to_pk = parse_primary_keys(sql_text)
    fks = parse_foreign_keys(sql_text)
    return build_dbml(tables, table_to_pk, fks)


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python tools/sql_to_dbml.py <input_sql> <output_dbml>")
        sys.exit(1)
    input_sql = Path(sys.argv[1])
    output_dbml = Path(sys.argv[2])

    sql_text = input_sql.read_text(encoding='utf-8')
    dbml_text = convert_sql_to_dbml(sql_text)

    output_dbml.parent.mkdir(parents=True, exist_ok=True)
    output_dbml.write_text(dbml_text, encoding='utf-8')


if __name__ == '__main__':
    main()