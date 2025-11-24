import re
import os
import sys
from typing import Dict, List, Tuple, Set

import pandas as pd


def read_sql_text(sql_path: str) -> str:
    for enc in ("utf-8", "utf-16", "cp932", "utf-8-sig"):
        try:
            with open(sql_path, "r", encoding=enc, errors="ignore") as f:
                return f.read()
        except Exception:
            continue
    with open(sql_path, "rb") as f:
        data = f.read()
    return data.decode("utf-8", errors="ignore")


def parse_create_tables(sql: str) -> Dict[str, List[Tuple[str, str]]]:
    tables: Dict[str, List[Tuple[str, str]]] = {}
    create_table_pattern = re.compile(
        r"CREATE\s+TABLE\s+public\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\);",
        re.IGNORECASE | re.DOTALL,
    )
    skip_keywords = ("CONSTRAINT ", "PRIMARY KEY", "UNIQUE ", "FOREIGN KEY", "CHECK ")

    for m in create_table_pattern.finditer(sql):
        name = m.group(1)
        body = m.group(2)
        cols: List[Tuple[str, str]] = []
        items: List[str] = []
        buf: List[str] = []
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
            s = re.sub(r"\s+", " ", line.strip())
            if not s:
                continue
            if any(k in s.upper() for k in skip_keywords):
                continue
            parts = s.split(" ", 2)
            if len(parts) >= 2:
                col = parts[0].strip().strip('"')
                dtype = parts[1].strip()
                cols.append((col, dtype))
        tables[name] = cols
    return tables


def parse_primary_keys(sql: str) -> Dict[str, Set[str]]:
    pks: Dict[str, Set[str]] = {}
    # From ALTER TABLE
    alter_pat = re.compile(
        r"ALTER\s+TABLE\s+ONLY\s+public\.([a-zA-Z_][a-zA-Z0-9_]*)\s+ADD\s+CONSTRAINT\s+[a-zA-Z0-9_]+\s+PRIMARY\s+KEY\s*\(([^\)]+)\)",
        re.IGNORECASE,
    )
    for m in alter_pat.finditer(sql):
        t = m.group(1)
        cols = [c.strip().strip('"') for c in m.group(2).split(',')]
        pks.setdefault(t, set()).update(cols)
    # From CREATE TABLE
    create_table_pattern = re.compile(
        r"CREATE\s+TABLE\s+public\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\);",
        re.IGNORECASE | re.DOTALL,
    )
    for m in create_table_pattern.finditer(sql):
        t = m.group(1)
        body = m.group(2)
        for pm in re.finditer(r"PRIMARY\s+KEY\s*\(([^\)]+)\)", body, flags=re.IGNORECASE):
            cols = [c.strip().strip('"') for c in pm.group(1).split(',')]
            pks.setdefault(t, set()).update(cols)
    return pks


def parse_foreign_keys(sql: str) -> List[Tuple[str, List[str], str, List[str], str]]:
    fks: List[Tuple[str, List[str], str, List[str], str]] = []
    pat = re.compile(
        r"ALTER\s+TABLE\s+ONLY\s+public\.([a-zA-Z_][a-zA-Z0-9_]*)\s+ADD\s+CONSTRAINT\s+([a-zA-Z0-9_]+)\s+FOREIGN\s+KEY\s*\(([^\)]+)\)\s+REFERENCES\s+public\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^\)]+)\)",
        re.IGNORECASE,
    )
    for m in pat.finditer(sql):
        table = m.group(1)
        cname = m.group(2)
        cols = [c.strip().strip('"') for c in m.group(3).split(',')]
        ref_table = m.group(4)
        ref_cols = [c.strip().strip('"') for c in m.group(5).split(',')]
        fks.append((table, cols, ref_table, ref_cols, cname))
    return fks


def parse_views(sql: str) -> Dict[str, Dict[str, Set[str]]]:
    views: Dict[str, Dict[str, Set[str]]] = {}
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
        name = m.group(1)
        select_list = m.group(2)
        from_part = m.group(3)
        cols: Set[str] = set()
        sources: Set[str] = set()
        for item in split_top_level_commas(select_list):
            s = re.sub(r"\s+", " ", item)
            am = re.search(r"\sAS\s([a-zA-Z_][a-zA-Z0-9_\"]*)", s, flags=re.IGNORECASE)
            if am:
                alias = am.group(1).strip('"')
                cols.add(alias)
            else:
                tail = s.split(" ")[-1]
                tail = tail.split(".")[-1].strip('"')
                if tail:
                    cols.add(tail)
        for src in re.findall(r"(?:FROM|JOIN)\s+public\.([a-zA-Z_][a-zA-Z0-9_]*)", from_part, flags=re.IGNORECASE):
            sources.add(src)
        views[name] = {"columns": cols, "sources": sources}
    return views


def infer_ui_usage(table: str, column: str, dtype: str) -> Tuple[bool, str]:
    t = table.lower()
    c = column.lower()
    d = (dtype or '').lower()
    # Specific, high-confidence mappings
    if t == 'project_info' and c == 'project_code':
        return True, 'プロジェクト選択リスト (Project selection dropdown)'
    if t == 'architecture' and c == 'architecturename':
        return True, 'PTシステムタイプの選択リスト (PT system type)'
    if t == 'destination' and c == 'destination':
        return True, '仕向けの選択リスト (Destination selection)'
    if t == 'phase' and c == 'phase':
        return True, 'フェーズの選択リスト (Phase selection)'
    if t == 'drivetrain' and c == 'drivetrain':
        return True, '駆動方式の選択リスト (Drivetrain selection)'
    if t == 'lot' and c == 'lot':
        return True, 'ロットの選択リスト (Lot selection)'
    if t == 'variation' and c == 'variation':
        return True, 'バリエーションの選択リスト (Variation selection)'
    if t == 'approval_status_table' and c == 'state_key':
        return True, 'ステータスコードキー。承認・状態管理画面で利用 (Status code key, used in approval/status screens)'
    if t == 'approval_status_table' and c == 'state_name':
        return True, 'ステータス表示ラベル。承認画面や一覧で表示 (Status display label)'
    if t == 'aras_meta' and c == 'aras_project_name':
        return True, 'プロジェクト名の表示。見出し/ラベルで使用 (Project name label)'
    if t == 'aras_meta' and c == 'z_note':
        return True, 'メモ/説明欄として表示 (Notes/description)'
    if t == 'aras_meta' and c in ('arasid', 'modified_on'):
        return False, '内部ID/メタデータ。画面では非表示 (Internal identifier/metadata)'
    if c in ('destination', 'drivetrain', 'lot', 'phase', 'variation'):
        return True, '選択リスト/フィルタ (Selection filter)'
    if any(k in c for k in ['name', 'title']):
        return True, '名称の表示 (Display label)'
    if any(k in c for k in ['note', 'comment', 'description', 'memo']):
        return True, 'メモ/説明 (Notes)'
    if any(k in c for k in ['status', 'state', 'flag', 'approval', 'judge']):
        return True, 'ステータス/承認 (Status)'
    if any(k in c for k in ['created', 'updated', 'modified', 'update_day', 'date']):
        return False, 'メタデータ (Metadata)'
    if c == 'id' or c.endswith('_id'):
        return False, '内部識別子 (Internal ID)'
    if any(k in c for k in ['url', 'path', 'file']):
        return True, 'リンク/ファイルパス (Link/Path)'
    if 'unit' in c:
        return True, '単位の表示 (Unit label)'
    if any(k in c for k in ['value', 'target', 'design', 'adjusted']):
        return True, '数値の表示/入力 (Value)'
    if any(k in c for k in ['user', 'email', 'login']):
        return True, 'ユーザ情報の表示 (User info)'
    return False, ''


def get_explicit_rules() -> Dict[Tuple[str, str], Tuple[str, str]]:
    """Return explicit UI tab + description overrides for well-known columns.

    Mapping: (object, column) -> (UI Tab, UI Usage Description)
    """
    rules: Dict[Tuple[str, str], Tuple[str, str]] = {}
    # Dialog/Bookmark
    rules[("bookmark", "employee_number")] = ("SEリスト", "ダイアログのブックマーク (条件保存/復元) のユーザー識別")
    rules[("bookmark", "bookmark_number")] = ("SEリスト", "ダイアログのブックマーク識別子")
    rules[("bookmark", "category")] = ("SEリスト", "ダイアログで保存する条件の種類 (アーキ/プロジェクト/仕向け等)")
    rules[("bookmark", "value")] = ("SEリスト", "ダイアログの選択条件の値の保存/復元に使用")

    # SEリスト
    rules[("project_parameter", "value")] = ("SEリスト", "SEリストの値として表示")
    rules[("project_parameter", "z_note")] = ("SEリスト", "SEリストの担当者として表示")
    rules[("detail_data", "user_memo")] = ("SEリスト", "SEリストのメモとして表示/編集")
    rules[("detail_data", "approval_status")] = ("SEリスト", "承認状態の表示/管理に使用")
    # View-based SE list
    rules[("se_project_record_plz", "z_request_median")] = ("SEリスト", "SEリストの値として表示")
    rules[("se_project_record_plz", "z_unit")] = ("SEリスト", "SEリストの単位ラベル")
    rules[("se_project_record_plz", "z_note")] = ("SEリスト", "SEリストの担当者として表示")
    rules[("se_project_record_plz", "URL")] = ("SEリスト", "MAPへのリンクとして表示")

    # R リスト
    rules[("project_r_parameter", "target")] = ("R リスト", "Rリストの目標として表示/編集")
    rules[("project_r_parameter", "adjusted_target")] = ("R リスト", "Rリストの調整目標として表示/編集")
    rules[("project_r_parameter", "design")] = ("R リスト", "Rリストの設計値として表示/編集")
    rules[("project_r_parameter", "judge")] = ("R リスト", "Rリストの判定として表示")
    rules[("project_r_parameter", "judge_evidence")] = ("R リスト", "Rリストの判断資料として表示")
    rules[("project_r_parameter", "manager_approval")] = ("R リスト", "Rリストの職制承認ステータス")
    rules[("project_r_parameter", "manager_approval_comment")] = ("R リスト", "Rリストの職制承認コメント")
    # R summary by WP
    rules[("wp_statement", "manager_approval")] = ("R リスト", "Rサマリーの承認欄 (WP単位)")
    rules[("wp_statement", "manager_approval_comment")] = ("R リスト", "Rサマリーの承認コメント (WP単位)")

    # SIM 管理表
    rules[("test_senario_project_record", "overall_value")] = ("SIM 管理表", "SIM管理表の値として表示")
    rules[("test_senario_project_record", "parameter_unit")] = ("SIM 管理表", "SIM管理表の単位ラベル")
    rules[("detail_data_sim", "user_memo")] = ("SIM 管理表", "SIM管理表のメモとして表示/編集")

    # RFL
    for col in ("r_item", "f_item", "l_item", "req", "func", "logic", "r_unit", "f_unit", "l_unit"):
        rules[("rfl_view_tlm", col)] = ("RFL", "RFLツリーの項目として表示")
    for col in ("sender_judge", "sender_name", "sender_date", "sender_comment", "receiver_judge", "receiver_name", "receiver_date", "receiver_comment"):
        rules[("rfl_view_tlm", col)] = ("RFL", "RFLツリーの承認情報として表示")

    return rules
def scan_ui_code_usage(project_root: str, tables: Dict[str, List[Tuple[str, str]]], views: Dict[str, Dict[str, Set[str]]]) -> Tuple[Set[Tuple[str, str]], Dict[Tuple[str, str], List[str]], Dict[Tuple[str, str], Set[str]]]:
    """Scan Python files for occurrences of schema column names and extract precise UI usages.

    Strictly code-based: we only mark a column as used in UI when it appears near UI component calls.

    Returns:
      - set of (object, column) marked as used in UI
      - dict of (object, column) -> list of precise usage descriptions (component + label + context)
      - dict of (object, column) -> set of inferred UI tabs
    """
    # Build column name to owners mapping
    col_to_entities: Dict[str, Set[str]] = {}
    for t, cols in tables.items():
        for col, _ in cols:
            col_to_entities.setdefault(col, set()).add(t)
    for v, meta in views.items():
        for col in meta.get('columns', set()):
            col_to_entities.setdefault(col, set()).add(v)

    # Simple stoplist to avoid trivially generic terms
    stoplist = {"id", "name", "value", "date", "note"}

    # Tokens for fast pre-filtering
    token_to_desc = [
        ("st.selectbox", "selectbox"),
        ("st.multiselect", "multiselect"),
        ("st.radio", "radio"),
        ("st.checkbox", "checkbox"),
        ("st.text_input", "text_input"),
        ("st.number_input", "number_input"),
        ("st.slider", "slider"),
        ("st.date_input", "date_input"),
        ("st.sidebar", "sidebar"),
        ("st.dataframe", "dataframe"),
        ("AgGrid", "aggrid"),
        ("st.table", "table"),
        ("alt.Chart", "chart")
    ]

    # Regex patterns to capture component and label text (use stdlib re)
    comp_label_pat = re.compile(
        r"st\.(selectbox|multiselect|radio|checkbox|text_input|number_input|slider|date_input)\s*\(\s*(?:label\s*=\s*)?([\'\"])\s*([^\'\"]{0,200})\s*\2",
        flags=re.DOTALL,
    )
    aggrid_pat = re.compile(r"AgGrid\s*\(")
    table_pat = re.compile(r"st\.(dataframe|table)\s*\(")

    used: Set[Tuple[str, str]] = set()
    usage_map: Dict[Tuple[str, str], List[str]] = {}
    tabs_map: Dict[Tuple[str, str], Set[str]] = {}

    # Walk python files under app directories likely used in Streamlit
    for base in ("pages", "module", "db"):
        base_path = os.path.join(project_root, base)
        if not os.path.isdir(base_path):
            continue
        for root, _dirs, files in os.walk(base_path):
            for fn in files:
                if not fn.endswith('.py'):
                    continue
                fpath = os.path.join(root, fn)
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                except Exception:
                    continue
                text = ''.join(lines)
                # Precompute which tokens are present in file
                present_tokens = {desc for tok, desc in token_to_desc if tok in text}
                for col, owners in col_to_entities.items():
                    if col in stoplist:
                        continue
                    # search occurrences line by line to capture context keywords
                    for idx, line in enumerate(lines):
                        if col not in line:
                            continue
                        # Build context window
                        start = max(0, idx - 8)
                        end = min(len(lines), idx + 9)
                        ctx = ''.join(lines[start:end])
                        contexts_raw: List[str] = []
                        for tok, key in token_to_desc:
                            if tok in ctx:
                                contexts_raw.append(key)
                        # DF specific hints
                        df_col_ref = bool(re.search(rf"\b\[\s*['\"]{re.escape(col)}['\"]\s*\]", ctx))
                        if df_col_ref:
                            contexts_raw.append("dfcol")
                        if ".unique()" in ctx or "drop_duplicates()" in ctx:
                            contexts_raw.append("unique")
                        # Aggregate to owners
                        if contexts_raw:
                            for obj in owners:
                                used.add((obj, col))
                                usage_map.setdefault((obj, col), [])
                                # 画面（タブ）の推定（説明にも含める）
                                rel2 = os.path.relpath(fpath, project_root).lower()
                                tab_set: Set[str] = set()
                                if ('rfl_' in rel2) or ('rfl' in rel2 and 'pages' in rel2):
                                    tab_set.add('RFL')
                                elif ('sim' in rel2) or ('map_grid_page.py' in rel2) or ('senario' in rel2):
                                    tab_set.add('SIM 管理表')
                                elif ('spdm_list.py' in rel2):
                                    if obj in ('r_project_record','project_r_parameter','wp_statement','approval_status_table') or 'r_parameter' in obj:
                                        tab_set.add('R リスト')
                                    else:
                                        tab_set.add('SEリスト')
                                else:
                                    if obj.startswith('se_') or 'se_parameter' in obj or obj in ('project_parameter','detail_data'):
                                        tab_set.add('SEリスト')
                                    elif obj.startswith('r_') or 'project_r_' in obj:
                                        tab_set.add('R リスト')

                                # わかりやすい日本語の説明（低いレベルの表現、用途の説明）
                                desc_bits: List[str] = []
                                # 表示（テーブル/グリッド）
                                if "aggrid" in contexts_raw or any(k in contexts_raw for k in ("dataframe", "table", "dfcol")):
                                    desc_bits.append("この項目は、画面の表に並びます。人が見て内容を確かめたり、比べるために使います。")
                                # 選択系
                                if "selectbox" in contexts_raw and "multiselect" not in contexts_raw:
                                    desc_bits.append("この項目は、一覧から1つを選ぶときに使います。")
                                if "multiselect" in contexts_raw:
                                    desc_bits.append("この項目は、一覧から複数を選ぶときに使います。")
                                if "radio" in contexts_raw:
                                    desc_bits.append("この項目は、丸いボタンから1つを選ぶときに使います。")
                                if "checkbox" in contexts_raw:
                                    desc_bits.append("この項目は、チェックでON/OFFを示します。選んだ状態はあとで使えるように保たれます。")
                                # 入力系
                                if "text_input" in contexts_raw:
                                    desc_bits.append("この項目は、文字を書き込むための欄です。")
                                if "number_input" in contexts_raw:
                                    desc_bits.append("この項目は、数を入れるための欄です。")
                                if "slider" in contexts_raw:
                                    desc_bits.append("この項目は、つまみを動かして値を決めます。")
                                if "date_input" in contexts_raw:
                                    desc_bits.append("この項目は、カレンダーから日付を選びます。")
                                # 選択肢の作成
                                if "unique" in contexts_raw:
                                    desc_bits.append("また、この項目の重ならない値を集めて、えらべる項目のリストを作ります。")
                                if not desc_bits:
                                    desc_bits.append("この項目は、画面で見る・選ぶ・入力するために使います。")

                                # どの画面で使うかを追記
                                if tab_set:
                                    desc_bits.append(f"画面: {' / '.join(sorted(tab_set))}。")

                                usage_map[(obj, col)].append(" ".join(desc_bits))
                                # Map to UI tab categories
                                rel = os.path.relpath(fpath, project_root).lower()
                                tabs: Set[str] = tabs_map.setdefault((obj, col), set())
                                # Determine tab by file and entity
                                if ('rfl_' in rel) or ('rfl' in rel and 'pages' in rel):
                                    tabs.add('RFL')
                                elif ('sim' in rel) or ('map_grid_page.py' in rel) or ('senario' in rel):
                                    tabs.add('SIM 管理表')
                                elif ('spdm_list.py' in rel):
                                    # Disambiguate by entity
                                    if obj in ('r_project_record','project_r_parameter','wp_statement','approval_status_table') or 'r_parameter' in obj:
                                        tabs.add('R リスト')
                                    else:
                                        tabs.add('SEリスト')
                                else:
                                    # Fallback by entity/view naming
                                    if obj.startswith('se_') or 'se_parameter' in obj or obj in ('project_parameter','detail_data'):
                                        tabs.add('SEリスト')
                                    elif obj.startswith('r_') or 'project_r_' in obj:
                                        tabs.add('R リスト')
                        else:
                            # Avoid guessing: do not mark as UI-used without nearby UI component context
                            pass
    return used, usage_map, tabs_map


def main():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    # Prefer the user's latest file if present
    for candidate in ('splittabletest_bk.sql', 'BK_DBQuery.sql', 'DB_BK.sql'):
        sql_path = os.path.join(project_root, candidate)
        if os.path.exists(sql_path):
            break
    out_dir = os.path.join(project_root, 'docs')
    os.makedirs(out_dir, exist_ok=True)
    out_excel = os.path.join(out_dir, 'Mapping_DB_AND_UI_Gen.xlsx')
    out_er = os.path.join(out_dir, 'er_diagram.er')
    out_mmd = os.path.join(out_dir, 'er_diagram.mmd')
    out_drawio = os.path.join(out_dir, 'er_diagram.drawio')
    # Also keep legacy-named copies if needed later
    out_excel_named = out_excel
    out_drawio_named = out_drawio

    sql_text = read_sql_text(sql_path)
    tables = parse_create_tables(sql_text)
    pks = parse_primary_keys(sql_text)
    fk_list = parse_foreign_keys(sql_text)
    views = parse_views(sql_text)

    # Exclude requested temporary tables from mapping
    EXCLUDED = {
        'l_parameter_temp_input',
        'se_parameter_temp_input',
        'temp_input_rfl',
        'temp_se_parameter_updates',
        'temp_to_change_rfl_index',
    }
    tables = {k: v for k, v in tables.items() if k not in EXCLUDED}
    pks = {k: v for k, v in pks.items() if k not in EXCLUDED}
    fk_list = [fk for fk in fk_list if fk[0] not in EXCLUDED and fk[2] not in EXCLUDED]
    # Scan codebase for UI usage
    ui_used, usage_map, tabs_map = scan_ui_code_usage(project_root, tables, views)
    # For this precise report we avoid heuristic or hard-coded overrides
    explicit = {}

    # FK lookup
    fk_lookup: Dict[Tuple[str, str], List[Tuple[str, str]]] = {}
    for table, cols, ref_table, ref_cols, _ in fk_list:
        if len(ref_cols) == len(cols):
            pairs = zip(cols, ref_cols)
        else:
            pairs = [(c, ref_cols[0] if ref_cols else '') for c in cols]
        for c, rc in pairs:
            fk_lookup.setdefault((table, c), []).append((ref_table, rc))

    # Overview rows
    overview_rows: List[Dict[str, str]] = []
    # Tables
    for tbl, cols in sorted(tables.items()):
        pk_cols = pks.get(tbl, set())
        for col, dtype in cols:
            # Column is in UI only if referenced in code
            in_ui = (tbl, col) in ui_used
            if in_ui and (tbl, col) in usage_map:
                ui_desc = '; '.join(sorted(set(usage_map[(tbl, col)])))
            else:
                ui_desc = ''
            ui_tab = ' / '.join(sorted(tabs_map.get((tbl, col), set()))) if in_ui else ''
            # Apply explicit overrides if present
            # No explicit overrides for precise mapping
            fk_pairs = fk_lookup.get((tbl, col), [])
            overview_rows.append({
                'Object Type': 'Table',
                'Table/View Name': tbl,
                'Column Name': col,
                'Data Type': dtype,
                'Is Primary Key': 'Yes' if col in pk_cols else 'No',
                'Is Foreign Key': 'Yes' if fk_pairs else 'No',
                'Related Table': '; '.join(sorted({rt for (rt, _rc) in fk_pairs})) if fk_pairs else '',
                'Related Column': '; '.join(sorted({rc for (_rt, rc) in fk_pairs})) if fk_pairs else '',
                'In UI? (Yes/No)': 'Yes' if in_ui else 'No',
                'UI Tab': ui_tab,
                'UI Usage Description': ui_desc,
            })
    # Views
    for vname, meta in sorted(views.items()):
        vcols = sorted(meta.get('columns', set())) or ['(derived)']
        for col in vcols:
            in_ui = (vname, col) in ui_used
            if in_ui and (vname, col) in usage_map:
                ui_desc = '; '.join(sorted(set(usage_map[(vname, col)])))
            else:
                ui_desc = ''
            ui_tab = ' / '.join(sorted(tabs_map.get((vname, col), set()))) if in_ui else ''
            # No explicit overrides for precise mapping
            overview_rows.append({
                'Object Type': 'View',
                'Table/View Name': vname,
                'Column Name': col,
                'Data Type': '',
                'Is Primary Key': 'No',
                'Is Foreign Key': 'No',
                'Related Table': ', '.join(sorted(meta.get('sources', set()))),
                'Related Column': '',
                'In UI? (Yes/No)': 'Yes' if in_ui else 'No',
                'UI Tab': ui_tab,
                'UI Usage Description': ui_desc,
            })

    # Write Excel (fallback to timestamped if locked)
    excel_written_path = out_excel
    try:
        with pd.ExcelWriter(out_excel, engine='openpyxl') as writer:
            pd.DataFrame(overview_rows).sort_values(['Object Type','Table/View Name','Column Name']).to_excel(writer, sheet_name='Overview', index=False)
            # Per entity sheets
            def sheet(name: str) -> str:
                invalid = set('[]:*?/\\')
                cleaned = ''.join(ch if ch not in invalid else '_' for ch in name)
                return cleaned[:31] if len(cleaned) > 31 else cleaned
            # Tables
            for tbl, cols in sorted(tables.items()):
                pk_cols = pks.get(tbl, set())
                rows: List[Dict[str, str]] = []
                for col, dtype in cols:
                    fk_pairs = fk_lookup.get((tbl, col), [])
                    in_ui = (tbl, col) in ui_used
                    if in_ui and (tbl, col) in usage_map:
                        ui_desc = '; '.join(sorted(set(usage_map[(tbl, col)])))
                    else:
                        ui_desc = ''
                    ui_tab = ' / '.join(sorted(tabs_map.get((tbl, col), set()))) if in_ui else ''
                    # No explicit overrides for precise mapping
                    rows.append({
                        'Column Name': col,
                        'Data Type': dtype,
                        'Is Primary Key': 'Yes' if col in pk_cols else 'No',
                        'Is Foreign Key': 'Yes' if fk_pairs else 'No',
                        'Related Table': '; '.join(sorted({rt for (rt, _rc) in fk_pairs})) if fk_pairs else '',
                        'Related Column': '; '.join(sorted({rc for (_rt, rc) in fk_pairs})) if fk_pairs else '',
                        'In UI?': 'Yes' if in_ui else 'No',
                        'UI Tab': ui_tab,
                        'UI Usage Description': ui_desc,
                    })
                pd.DataFrame(rows).to_excel(writer, sheet_name=sheet(tbl), index=False)
            # Views
            for vname, meta in sorted(views.items()):
                vcols = sorted(meta.get('columns', set())) or ['(derived)']
                rows: List[Dict[str, str]] = []
                for col in vcols:
                    in_ui = (vname, col) in ui_used
                    if in_ui and (vname, col) in usage_map:
                        ui_desc = '; '.join(sorted(set(usage_map[(vname, col)])))
                    else:
                        ui_desc = ''
                    ui_tab = ' / '.join(sorted(tabs_map.get((vname, col), set()))) if in_ui else ''
                    # No explicit overrides for precise mapping
                    rows.append({
                        'Column Name': col,
                        'Data Type': '',
                        'Is Primary Key': 'No',
                        'Is Foreign Key': 'No',
                        'Related Table': ', '.join(sorted(meta.get('sources', set()))),
                        'Related Column': '',
                        'In UI?': 'Yes' if in_ui else 'No',
                        'UI Tab': ui_tab,
                        'UI Usage Description': ui_desc,
                    })
                pd.DataFrame(rows).to_excel(writer, sheet_name=sheet(vname), index=False)
    except PermissionError:
        import datetime as _dt
        ts = _dt.datetime.now().strftime('%Y%m%d_%H%M%S')
        excel_written_path = os.path.join(out_dir, f'UI_DB_Mapping_{ts}.xlsx')
        with pd.ExcelWriter(excel_written_path, engine='openpyxl') as writer:
            pd.DataFrame(overview_rows).sort_values(['Object Type','Table/View Name','Column Name']).to_excel(writer, sheet_name='Overview', index=False)
            def sheet(name: str) -> str:
                invalid = set('[]:*?/\\')
                cleaned = ''.join(ch if ch not in invalid else '_' for ch in name)
                return cleaned[:31] if len(cleaned) > 31 else cleaned
            for tbl, cols in sorted(tables.items()):
                pk_cols = pks.get(tbl, set())
                rows: List[Dict[str, str]] = []
                for col, dtype in cols:
                    fk_pairs = fk_lookup.get((tbl, col), [])
                    in_ui = (tbl, col) in ui_used
                    if in_ui and (tbl, col) in usage_map:
                        ui_desc = '; '.join(sorted(set(usage_map[(tbl, col)])))
                    else:
                        ui_desc = ''
                    rows.append({
                        'Column Name': col,
                        'Data Type': dtype,
                        'Is Primary Key': 'Yes' if col in pk_cols else 'No',
                        'Is Foreign Key': 'Yes' if fk_pairs else 'No',
                        'Related Table': '; '.join(sorted({rt for (rt, _rc) in fk_pairs})) if fk_pairs else '',
                        'Related Column': '; '.join(sorted({rc for (_rt, rc) in fk_pairs})) if fk_pairs else '',
                        'In UI?': 'Yes' if in_ui else 'No',
                        'UI Usage Description': ui_desc,
                    })
                pd.DataFrame(rows).to_excel(writer, sheet_name=sheet(tbl), index=False)
            for vname, meta in sorted(views.items()):
                vcols = sorted(meta.get('columns', set())) or ['(derived)']
                rows: List[Dict[str, str]] = []
                for col in vcols:
                    in_ui = (vname, col) in ui_used
                    if in_ui and (vname, col) in usage_map:
                        ui_desc = '; '.join(sorted(set(usage_map[(vname, col)])))
                    else:
                        ui_desc = ''
                    rows.append({
                        'Column Name': col,
                        'Data Type': '',
                        'Is Primary Key': 'No',
                        'Is Foreign Key': 'No',
                        'Related Table': ', '.join(sorted(meta.get('sources', set()))),
                        'Related Column': '',
                        'In UI?': 'Yes' if in_ui else 'No',
                        'UI Usage Description': ui_desc,
                    })
                pd.DataFrame(rows).to_excel(writer, sheet_name=sheet(vname), index=False)

    # ER Mermaid
    ents = sorted(set(list(tables.keys()) + list(views.keys())))
    mmd: List[str] = ["erDiagram"]
    for ent in ents:
        mmd.append(f"  {ent} {{}}")
    # FK relationships
    for table, cols, ref_table, ref_cols, _ in fk_list:
        pairs = zip(cols, ref_cols) if len(cols) == len(ref_cols) else [(c, ref_cols[0] if ref_cols else '') for c in cols]
        for c, rc in pairs:
            mmd.append(f"  {table} }}o--|| {ref_table} : {c} to {rc}")
    with open(out_mmd, 'w', encoding='utf-8') as f:
        f.write("\n".join(mmd))

    # ERAlchemy/DOT
    dot: List[str] = ["digraph ER {", "  rankdir=LR;"]
    for tbl, cols in sorted(tables.items()):
        label_cols = "|".join([f"{c} : {t}" for (c, t) in cols])
        label = f"{{{tbl}|{label_cols}}}" if label_cols else f"{{{tbl}}}"
        dot.append(f"  \"{tbl}\" [shape=record, label=\"{label}\"];\n")
    for vname, meta in sorted(views.items()):
        vcols = sorted(meta.get('columns', set()))
        label_cols = "|".join([f"{c}" for c in vcols])
        label = f"{{{vname}|{label_cols}}}" if label_cols else f"{{{vname}}}"
        dot.append(f"  \"{vname}\" [shape=record, style=dashed, label=\"{label}\"];\n")
    for table, cols, ref_table, ref_cols, _ in fk_list:
        pairs = zip(cols, ref_cols) if len(cols) == len(ref_cols) else [(c, ref_cols[0] if ref_cols else '') for c in cols]
        for c, rc in pairs:
            dot.append(f"  \"{table}\" -> \"{ref_table}\" [label=\"{c} -> {rc}\"];\n")
    dot.append("}")
    with open(out_er, 'w', encoding='utf-8') as f:
        f.write("\n".join(dot))

    # Draw.io (.drawio) basic XML export
    try:
        import xml.etree.ElementTree as ET

        mxfile = ET.Element('mxfile', host='app.diagrams.net')
        diagram = ET.SubElement(mxfile, 'diagram', name='ER Diagram')
        model = ET.SubElement(diagram, 'mxGraphModel')
        root = ET.SubElement(model, 'root')

        # required base cells
        ET.SubElement(root, 'mxCell', id='0')
        ET.SubElement(root, 'mxCell', id='1', parent='0')

        # layout parameters
        node_w = 240
        base_h = 40
        row_h = 18
        pad_h = 10
        x_gap = 60
        y_gap = 60
        per_row = 4

        # Create entity cells (tables + views)
        id_map: Dict[str, str] = {}
        entities = list(tables.keys()) + list(views.keys())
        for idx, ent in enumerate(sorted(set(entities))):
            eid = f"n{idx+2}"
            id_map[ent] = eid
            cols = tables.get(ent, [])
            if not cols and ent in views:
                vcols = sorted(views[ent].get('columns', set()))
                cols = [(c, '') for c in vcols]
            # build label
            lines = [f"<b>{ent}</b>"] + [f"{c}: {t}".strip() for (c, t) in cols]
            value = "<br/>".join(lines)

            # size and position
            rows = max(1, len(lines))
            height = base_h + max(0, (rows - 1)) * row_h + pad_h
            row = idx // per_row
            col = idx % per_row
            x = col * (node_w + x_gap)
            y = row * (height + y_gap)

            cell = ET.SubElement(root, 'mxCell', id=eid, value=value, style='shape=rectangle;whiteSpace=wrap;html=1;rounded=0;align=left;verticalAlign=top;', vertex='1', parent='1')
            geo = ET.SubElement(cell, 'mxGeometry', x=str(x), y=str(y), width=str(node_w), height=str(height))
            geo.set('as', 'geometry')

        # Create edges for FKs
        edge_id = 100000
        for table, cols, ref_table, ref_cols, _ in fk_list:
            if table not in id_map or ref_table not in id_map:
                continue
            pairs = zip(cols, ref_cols) if len(cols) == len(ref_cols) else [(c, ref_cols[0] if ref_cols else '') for c in cols]
            for c, rc in pairs:
                edge_id += 1
                e = ET.SubElement(root, 'mxCell', id=str(edge_id), value=f"{c}→{rc}", edge='1', parent='1', source=id_map[table], target=id_map[ref_table], style='endArrow=block;endFill=1;')
                geo = ET.SubElement(e, 'mxGeometry', relative='1')
                geo.set('as', 'geometry')

        # write file
        ET.ElementTree(mxfile).write(out_drawio, encoding='utf-8', xml_declaration=True)
    except Exception as _e:
        # Best-effort; ignore if something goes wrong
        pass

    print(f"Generated: {excel_written_path}")
    print(f"Generated: {out_er}")
    print(f"Generated: {out_mmd}")
    if os.path.exists(out_drawio):
        print(f"Generated: {out_drawio}")
    # Also write requested filenames (already matched)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)