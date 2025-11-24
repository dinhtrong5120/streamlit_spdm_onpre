import re
import os
import sys
from typing import Dict, List, Tuple, Set

import pandas as pd


def read_sql_text(sql_path: str) -> str:
    """Read the SQL file with best-effort encoding handling."""
    for enc in ("utf-8", "utf-16", "cp932", "utf-8-sig"):
        try:
            with open(sql_path, "r", encoding=enc, errors="ignore") as f:
                return f.read()
        except Exception:
            continue
    # Fallback: binary then decode ignoring errors
    with open(sql_path, "rb") as f:
        data = f.read()
    return data.decode("utf-8", errors="ignore")


def parse_create_tables(sql: str) -> Dict[str, List[Tuple[str, str]]]:
    """Parse CREATE TABLE blocks to extract columns and types.

    Returns dict: table_name -> list of (column_name, data_type)
    """
    tables: Dict[str, List[Tuple[str, str]]] = {}

    # Regex to match CREATE TABLE public.table_name ( ... ); blocks (tolerate spaces/newlines)
    create_table_pattern = re.compile(
        r"CREATE\s+TABLE\s+public\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\);",
        re.IGNORECASE | re.DOTALL,
    )

    # Rough patterns to skip table-level constraints
    table_constraint_keywords = (
        "CONSTRAINT ",
        "PRIMARY KEY",
        "UNIQUE ",
        "FOREIGN KEY",
        "CHECK ",
    )

    for match in create_table_pattern.finditer(sql):
        table = match.group(1)
        body = match.group(2)
        cols: List[Tuple[str, str]] = []

        # Split by commas but respect parentheses nesting (simple approach)
        items: List[str] = []
        buf = []
        depth = 0
        for ch in body:
            if ch == "(":
                depth += 1
            elif ch == ")" and depth > 0:
                depth -= 1
            if ch == "," and depth == 0:
                items.append("".join(buf).strip())
                buf = []
            else:
                buf.append(ch)
        last = "".join(buf).strip()
        if last:
            items.append(last)

        for line in items:
            line_clean = re.sub(r"\s+", " ", line.strip())
            if not line_clean:
                continue
            up = line_clean.upper()
            if any(k in up for k in table_constraint_keywords):
                continue
            # Column definition: name type ...
            parts = line_clean.split(" ", 2)
            if len(parts) >= 2:
                col = parts[0].strip().strip('"')
                dtype = parts[1].strip()
                cols.append((col, dtype))

        tables[table] = cols

    return tables


def parse_foreign_keys(sql: str) -> List[Tuple[str, str, str, str, str]]:
    """Parse ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY ... REFERENCES ... statements.

    Returns list of tuples: (table, column, ref_table, ref_column, constraint_name)
    """
    fks: List[Tuple[str, str, str, str, str]] = []

    # Typical form:
    # ALTER TABLE ONLY public.bookmark
    #     ADD CONSTRAINT bookmark_employee_number_fkey FOREIGN KEY (employee_number)
    #     REFERENCES public.user_table(employee_number);
    alter_fk_pattern = re.compile(
        r"ALTER\s+TABLE\s+ONLY\s+public\.([a-zA-Z_][a-zA-Z0-9_]*)\s+ADD\s+CONSTRAINT\s+([a-zA-Z0-9_]+)\s+FOREIGN\s+KEY\s*\(([^\)]+)\)\s+REFERENCES\s+public\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^\)]+)\)",
        re.IGNORECASE,
    )

    for m in alter_fk_pattern.finditer(sql):
        table = m.group(1)
        constraint_name = m.group(2)
        col = m.group(3).strip().strip('"')
        ref_table = m.group(4)
        ref_col = m.group(5).strip().strip('"')
        fks.append((table, col, ref_table, ref_col, constraint_name))

    return fks


def parse_primary_keys_from_alter(sql: str) -> Dict[str, Set[str]]:
    """Parse PRIMARY KEY constraints from ALTER TABLE statements.

    Returns dict: table_name -> set(pk_columns)
    """
    pks: Dict[str, Set[str]] = {}
    pattern = re.compile(
        r"ALTER\s+TABLE\s+ONLY\s+public\.([a-zA-Z_][a-zA-Z0-9_]*)\s+ADD\s+CONSTRAINT\s+[a-zA-Z0-9_]+\s+PRIMARY\s+KEY\s*\(([^\)]+)\)",
        re.IGNORECASE,
    )
    for m in pattern.finditer(sql):
        table = m.group(1)
        cols = [c.strip().strip('"') for c in m.group(2).split(',')]
        pks.setdefault(table, set()).update(cols)
    return pks


def parse_primary_keys_from_create(sql: str) -> Dict[str, Set[str]]:
    """Parse PRIMARY KEY constraints inside CREATE TABLE blocks."""
    pks: Dict[str, Set[str]] = {}
    create_table_pattern = re.compile(
        r"CREATE\s+TABLE\s+public\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\);",
        re.IGNORECASE | re.DOTALL,
    )
    for match in create_table_pattern.finditer(sql):
        table = match.group(1)
        body = match.group(2)
        for pm in re.finditer(r"PRIMARY\s+KEY\s*\(([^\)]+)\)", body, flags=re.IGNORECASE):
            cols = [c.strip().strip('"') for c in pm.group(1).split(',')]
            pks.setdefault(table, set()).update(cols)
    return pks


def normalize_fk_list(
    fk_relations: List[Tuple[str, str, str, str, str]]
) -> List[Tuple[str, List[str], str, List[str], str]]:
    """Split multi-column FK definitions into lists for easier mapping."""
    result: List[Tuple[str, List[str], str, List[str], str]] = []
    for table, col_str, ref_table, ref_col_str, cname in fk_relations:
        cols = [c.strip().strip('"') for c in col_str.split(',')]
        ref_cols = [c.strip().strip('"') for c in ref_col_str.split(',')]
        result.append((table, cols, ref_table, ref_cols, cname))
    return result


def parse_create_views(sql: str) -> Dict[str, Dict[str, Set[str]]]:
    """Parse CREATE VIEW blocks and return view metadata.

    Returns dict: view_name -> {
        'columns': set of output column aliases (best-effort),
        'sources': set of base tables/views referenced in FROM/JOIN (best-effort)
    }
    """
    views: Dict[str, Dict[str, Set[str]]] = {}
    # Match CREATE VIEW public.name AS ... ;
    view_pattern = re.compile(
        r"CREATE\s+VIEW\s+public\.([a-zA-Z_][a-zA-Z0-9_]*)\s+AS\s+SELECT\s+(.*?)\sFROM\s+(.*?);",
        re.IGNORECASE | re.DOTALL,
    )

    def split_top_level_commas(text: str) -> List[str]:
        parts: List[str] = []
        buf: List[str] = []
        depth = 0
        in_sq = False
        in_dq = False
        for ch in text:
            if ch == "'" and not in_dq:
                in_sq = not in_sq
            elif ch == '"' and not in_sq:
                in_dq = not in_dq
            elif ch == "(" and not in_sq and not in_dq:
                depth += 1
            elif ch == ")" and not in_sq and not in_dq and depth > 0:
                depth -= 1
            if ch == "," and depth == 0 and not in_sq and not in_dq:
                parts.append("".join(buf).strip())
                buf = []
            else:
                buf.append(ch)
        last = "".join(buf).strip()
        if last:
            parts.append(last)
        return parts

    for m in view_pattern.finditer(sql):
        view_name = m.group(1)
        select_list = m.group(2)
        from_part = m.group(3)
        cols: Set[str] = set()
        sources: Set[str] = set()

        # Extract column aliases (best-effort): prefer "AS alias", else trailing token
        for item in split_top_level_commas(select_list):
            item_clean = re.sub(r"\s+", " ", item)
            as_m = re.search(r"\sAS\s([a-zA-Z_][a-zA-Z0-9_\"]*)", item_clean, flags=re.IGNORECASE)
            if as_m:
                alias = as_m.group(1).strip('"')
                cols.add(alias)
            else:
                # Try to use last dotted name
                tail = item_clean.split(" ")[-1]
                tail = tail.split(".")[-1].strip('"')
                if tail:
                    cols.add(tail)

        # Extract source table/view names referenced after FROM/JOIN public.xxx
        for src in re.findall(r"(?:FROM|JOIN)\s+public\.([a-zA-Z_][a-zA-Z0-9_]*)", from_part, flags=re.IGNORECASE):
            sources.add(src)

        views[view_name] = {"columns": cols, "sources": sources}

    return views


def build_ui_mapping() -> List[Dict[str, str]]:
    """Known UI usages mapped to table/column based on the codebase."""
    rows: List[Dict[str, str]] = []

    def add(table: str, column: str, usage: str):
        rows.append({"table": table, "column": column, "usage": usage})

    # Selection filters
    add("project_info", "project_code", "プロジェクト選択リスト")
    add("destination", "destination", "仕向け 選択リスト")
    add("drivetrain", "drivetrain", "駆動方式 選択リスト")
    add("lot", "lot", "ロット 選択リスト")
    add("phase", "phase", "フェーズ 選択リスト")

    # User info displayed with edits
    add("user_table", "section_code", "編集者表示 (セクションコード)")
    add("user_table", "contac_person_first_name", "編集者表示 (氏名)")
    add("user_table", "contac_person_last_name", "編集者表示 (氏名)")

    # SE list / matrix (via se_project_record_plz view)
    add("se_project_record_plz", "z_parent_paraitem", "SEリスト/マトリクス: 親項目")
    add("se_project_record_plz", "z_child_paraitem", "SEリスト/マトリクス: 子項目")
    add("se_project_record_plz", "z_unit", "SEリスト/マトリクス: 単位")
    add("se_project_record_plz", "z_request_median", "SEリスト/マトリクス: 値")
    add("se_project_record_plz", "z_note", "SEリスト/マトリクス: メモ")
    add("se_project_record_plz", "z_paravalueid", "SEリスト/マトリクス: 識別子")
    add("se_project_record_plz", "URL", "MAP画面リンク")

    # R List
    add("r_project_record", "performance", "Rリスト: 性能/項目名")
    add("r_project_record", "design_item_1", "Rリスト: 設計項目1")
    add("r_project_record", "design_item_2", "Rリスト: 設計項目2")
    add("r_project_record", "design_item_3", "Rリスト: 設計項目3")
    add("r_project_record", "r_unit", "Rリスト: 単位")
    add("r_project_record", "target", "Rリスト: 目標")
    add("r_project_record", "adjusted_target", "Rリスト: 調整目標")
    add("r_project_record", "design", "Rリスト: 設計値")
    add("r_project_record", "judge", "Rリスト: 判定")
    add("r_project_record", "judge_evidence", "Rリスト: 判断資料")
    add("r_project_record", "manager_approval", "Rリスト: 職制承認")
    add("r_project_record", "manager_approval_comment", "Rリスト: 職制承認コメント")

    # R Summary approvals
    add("wp_statement", "manager_approval", "Rサマリー: 承認状態")
    add("wp_statement", "manager_approval_comment", "Rサマリー: 承認コメント")

    # MAP
    add("map_variable", "variable_name", "MAP: 変数名")
    add("map_variable", "unit", "MAP: 単位")
    add("parameter_map_relation", "value", "MAP: 値")

    # Login
    add("user_table", "employee_number", "ログイン (社員番号)")

    # RFL Tree (TLM view)
    add("rfl_view_tlm", "r_wp", "RFLツリー: R領域")
    add("rfl_view_tlm", "l_wp", "RFLツリー: L領域")
    add("rfl_view_tlm", "allocation", "RFLツリー: 割付")
    add("rfl_view_tlm", "sender_judge", "RFLツリー: 送信側判定")
    add("rfl_view_tlm", "receiver_judge", "RFLツリー: 受信側判定")

    return rows


def infer_ui_usage(table: str, column: str, dtype: str) -> Tuple[bool, str]:
    """Heuristically infer whether a column appears in UI and how."""
    t = table.lower()
    c = column.lower()
    d = (dtype or '').lower()

    # Strong includes
    if t == 'project_info' and c == 'project_code':
        return True, 'プロジェクト選択リスト (Project dropdown)'

    # Likely selection lists / filters
    if c in ('destination', 'drivetrain', 'lot', 'phase', 'variation') or c.endswith('_name') and 'usecase' in t:
        return True, '選択リスト/フィルタ (Selection filter)'

    # Common display fields
    if any(k in c for k in ['name', 'title']):
        return True, '名称の表示 (Display label)'

    # Text notes/comments
    if any(k in c for k in ['note', 'comment', 'description', 'memo']):
        return True, 'メモ/説明の表示・入力 (Notes)'

    # Status/flags/approvals
    if any(k in c for k in ['status', 'state', 'flag', 'approval', 'judge']):
        return True, 'ステータス/承認 (Status/flag)'

    # Dates
    if any(k in c for k in ['created', 'updated', 'modified', 'update_day', 'date']):
        return False, 'メタデータ (Metadata)'

    # Identifiers
    if c == 'id' or c.endswith('_id'):
        return False, '内部識別子 (Internal ID)'

    # URLs/paths
    if any(k in c for k in ['url', 'path', 'file']):
        return True, 'リンク/ファイルパス (Link/Path)'

    # Units
    if 'unit' in c:
        return True, '単位の表示 (Unit label)'

    # Values/targets
    if any(k in c for k in ['value', 'target', 'design', 'adjusted']):
        return True, '数値の表示/入力 (Value)'

    # User info
    if any(k in c for k in ['user', 'email', 'login']):
        return True, 'ユーザ情報の表示 (User info)'

    # Default: unknown, assume not visible
    return False, ''


def main():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    # Prefer newer BK_DBQuery.sql if present, else fallback to DB_BK.sql
    primary_sql = os.path.join(project_root, "BK_DBQuery.sql")
    fallback_sql = os.path.join(project_root, "DB_BK.sql")
    sql_path = primary_sql if os.path.exists(primary_sql) else fallback_sql
    out_dir = os.path.join(project_root, "docs")
    os.makedirs(out_dir, exist_ok=True)
    out_xlsx = os.path.join(out_dir, "ui_db_mapping.xlsx")
    out_per_table_xlsx = os.path.join(out_dir, "ui_db_per_table.xlsx")
    out_er_mmd = os.path.join(out_dir, "er_diagram.mmd")

    sql_text = read_sql_text(sql_path)

    # Extract tables/columns and relations
    table_columns = parse_create_tables(sql_text)
    fk_relations = parse_foreign_keys(sql_text)
    view_meta = parse_create_views(sql_text)
    # Primary keys from ALTER and CREATE
    pk_from_alter = parse_primary_keys_from_alter(sql_text)
    pk_from_create = parse_primary_keys_from_create(sql_text)
    pk_map: Dict[str, Set[str]] = {}
    for t, cols in pk_from_alter.items():
        pk_map.setdefault(t, set()).update(cols)
    for t, cols in pk_from_create.items():
        pk_map.setdefault(t, set()).update(cols)
    fk_list = normalize_fk_list(fk_relations)

    # Build DataFrames
    tables_rows: List[Dict[str, str]] = []
    for tbl, cols in sorted(table_columns.items()):
        for col, dtype in cols:
            tables_rows.append({
                "table": tbl,
                "column": col,
                "data_type": dtype,
            })
    df_tables = pd.DataFrame(tables_rows).sort_values(["table", "column"]).reset_index(drop=True)

    fk_rows: List[Dict[str, str]] = []
    for table, col, ref_table, ref_col, cname in fk_relations:
        fk_rows.append({
            "table": table,
            "column": col,
            "ref_table": ref_table,
            "ref_column": ref_col,
            "constraint": cname,
        })
    df_rel = pd.DataFrame(fk_rows).sort_values(["table", "column"]).reset_index(drop=True)

    # UI mapping
    df_ui = pd.DataFrame(build_ui_mapping()).sort_values(["table", "column"]).reset_index(drop=True)

    # Write Excel
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        df_tables.to_excel(writer, sheet_name="Tables", index=False)
        df_rel.to_excel(writer, sheet_name="Relations", index=False)
        df_ui.to_excel(writer, sheet_name="UI_Mapping", index=False)

    # Per-entity workbook: one sheet per table and per view
    def sanitize_sheet_name(name: str) -> str:
        invalid = set('[]:*?/\\')
        cleaned = ''.join(ch if ch not in invalid else '_' for ch in name)
        return cleaned[:31] if len(cleaned) > 31 else cleaned

    # Build inbound/outbound relation maps
    inbound: Dict[str, List[Tuple[str, str, str]]] = {}
    for t, c, rt, rc, _ in fk_relations:
        inbound.setdefault(rt, []).append((t, c, rt))

    outbound: Dict[str, List[Tuple[str, str, str]]] = {}
    for t, c, rt, rc, _ in fk_relations:
        outbound.setdefault(t, []).append((rt, rc, t))

    try:
        with pd.ExcelWriter(out_per_table_xlsx, engine="openpyxl") as writer:
            # Index sheet
            index_rows: List[Dict[str, str]] = []
            for name in sorted(set(list(table_columns.keys()) + list(view_meta.keys()))):
                index_rows.append({"name": name, "type": "view" if name in view_meta else "table"})
            pd.DataFrame(index_rows).to_excel(writer, sheet_name="Index", index=False)

            # Table sheets
            for tbl, cols in sorted(table_columns.items()):
                rows: List[Dict[str, str]] = []
                for col, dtype in cols:
                    rows.append({
                        "column": col,
                        "data_type": dtype,
                        "fk_out": ", ".join(sorted({f"{rt}" for (rt, _rc, _t) in outbound.get(tbl, [])})),
                        "fk_in": ", ".join(sorted({f"{t}" for (t, _c, _rt) in inbound.get(tbl, [])})),
                        "ui_usage": ", ".join(pd.unique(df_ui[df_ui.table == tbl]["usage"]))
                    })
                pd.DataFrame(rows).to_excel(writer, sheet_name=sanitize_sheet_name(tbl), index=False)

            # View sheets
            for vname, meta in sorted(view_meta.items()):
                rows: List[Dict[str, str]] = []
                vcols = sorted(meta.get("columns", set())) or ["(derived)"]
                for col in vcols:
                    rows.append({
                        "column": col,
                        "data_type": "",
                        "sources": ", ".join(sorted(meta.get("sources", set()))),
                        "ui_usage": ", ".join(pd.unique(df_ui[df_ui.table == vname]["usage"]))
                    })
                pd.DataFrame(rows).to_excel(writer, sheet_name=sanitize_sheet_name(vname), index=False)
    except PermissionError:
        print(f"Warning: Could not write {out_per_table_xlsx} (file may be open). Skipping per-table workbook.")

    # Mermaid ER diagram (.mmd)
    entities = sorted(set([t for (t, c, rt, rc, cn) in fk_relations] + [rt for (t, c, rt, rc, cn) in fk_relations]))
    er_lines: List[str] = ["erDiagram"]
    for ent in entities:
        er_lines.append(f"  {ent} {{}}")
    for t, c, rt, rc, _ in fk_relations:
        # Use doubled closing brace to emit a single literal '}' in an f-string
        er_lines.append(f"  {t} }}o--|| {rt} : {c} to {rc}")
    with open(out_er_mmd, "w", encoding="utf-8") as f:
        f.write("\n".join(er_lines))

    # Build requested Excel UI_DB_Mapping.xlsx with full schema (tables + views)
    out_req_xlsx = os.path.join(out_dir, "UI_DB_Mapping.xlsx")
    # Prepare FK lookup mapping (table,col) -> list of (ref_table, ref_col)
    fk_lookup: Dict[Tuple[str, str], List[Tuple[str, str]]] = {}
    for table, cols, ref_table, ref_cols, _ in fk_list:
        if len(ref_cols) == len(cols):
            pairs = zip(cols, ref_cols)
        else:
            pairs = [(c, ref_cols[0] if ref_cols else '') for c in cols]
        for c, rc in pairs:
            fk_lookup.setdefault((table, c), []).append((ref_table, rc))

    rows_req: List[Dict[str, str]] = []
    ui_usage_overrides = {('project_info', 'project_code'): 'プロジェクト選択リスト (Project dropdown)'}

    # Tables
    for tbl, cols in sorted(table_columns.items()):
        pk_cols = pk_map.get(tbl, set())
        for col, dtype in cols:
            key = (tbl, col)
            fk_pairs = fk_lookup.get(key, [])
            in_ui, ui_desc = infer_ui_usage(tbl, col, dtype)
            if key in ui_usage_overrides:
                in_ui = True
                ui_desc = ui_usage_overrides[key]
            rows_req.append({
                'Object Type': 'Table',
                'Table/View Name': tbl,
                'Column Name': col,
                'Data Type': dtype,
                'Is Primary Key': 'Yes' if col in pk_cols else 'No',
                'Is Foreign Key': 'Yes' if fk_pairs else 'No',
                'Related Table': '; '.join(sorted({rt for (rt, _rc) in fk_pairs})) if fk_pairs else '',
                'Related Column': '; '.join(sorted({rc for (_rt, rc) in fk_pairs})) if fk_pairs else '',
                'In UI? (Yes/No)': 'Yes' if in_ui else 'No',
                'UI Usage Description': ui_desc,
            })

    # Views
    for vname, meta in sorted(view_meta.items()):
        vcols = sorted(meta.get('columns', set())) or ['(derived)']
        for col in vcols:
            in_ui, ui_desc = infer_ui_usage(vname, col, '')
            rows_req.append({
                'Object Type': 'View',
                'Table/View Name': vname,
                'Column Name': col,
                'Data Type': '',
                'Is Primary Key': 'No',
                'Is Foreign Key': 'No',
                'Related Table': '',
                'Related Column': '',
                'In UI? (Yes/No)': 'Yes' if in_ui else 'No',
                'UI Usage Description': ui_desc,
            })
    pd.DataFrame(rows_req).sort_values(['Object Type', 'Table/View Name', 'Column Name']).to_excel(out_req_xlsx, index=False)

    # Generate ERAlchemy-compatible .er (Graphviz DOT) file
    out_er_dot = os.path.join(out_dir, 'er_diagram.er')
    dot_lines: List[str] = ["digraph ER {", "  rankdir=LR;"]
    # Nodes with columns
    for tbl, cols in sorted(table_columns.items()):
        label_cols = "|".join([f"{col} : {dtype}" for (col, dtype) in cols])
        label = f"{{{tbl}|{label_cols}}}" if label_cols else f"{{{tbl}}}"
        dot_lines.append(f"  \"{tbl}\" [shape=record, label=\"{label}\"];\n")
    # Edges
    for table, cols, ref_table, ref_cols, _ in fk_list:
        if len(ref_cols) == len(cols):
            pairs = zip(cols, ref_cols)
        else:
            pairs = [(c, ref_cols[0] if ref_cols else '') for c in cols]
        for c, rc in pairs:
            dot_lines.append(f"  \"{table}\" -> \"{ref_table}\" [label=\"{c} -> {rc}\"];\n")
    dot_lines.append("}")
    with open(out_er_dot, 'w', encoding='utf-8') as f:
        f.write("\n".join(dot_lines))

    print(f"Generated: {out_xlsx}")
    print(f"Generated: {out_per_table_xlsx}")
    print(f"Generated: {out_er_mmd}")
    print(f"Generated: {out_req_xlsx}")
    print(f"Generated: {out_er_dot}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
