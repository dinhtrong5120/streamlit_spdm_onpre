# import streamlit as st
# import pandas as pd
# from st_aggrid import AgGrid, GridUpdateMode

# # Example DataFrame
# df = pd.DataFrame({
#     "A": [1, 2, 3],
#     "B": [4, 5, 6],
#     "C": [7, 8, 9]
# })

# # Initialize session_state
# if 'rfl_pj_response' not in st.session_state:
#     st.session_state['rfl_pj_response'] = df.copy()

# # Define editable columns
# column_defs = [{"headerName": col, "field": col, "editable": True} for col in df.columns]

# # Render editable AgGrid
# grid_response = AgGrid(
#     df,
#     gridOptions={"columnDefs": column_defs, "defaultColDef": {"resizable": True}},
#     update_mode=GridUpdateMode.VALUE_CHANGED,
#     height=400,
#     key='grid1'
# )

# # Get updated DataFrame
# updated_df = pd.DataFrame(grid_response['data'])

# # Reset index to align with original DataFrame
# updated_df.reset_index(drop=True, inplace=True)
# original_df = st.session_state['rfl_pj_response'].reset_index(drop=True)

# # Compare cell by cell ignoring index
# mask = updated_df.ne(original_df)  # ne = not equal
# changed_rows = updated_df[mask.any(axis=1)]

# st.write("Changed rows (only rows with edits):")
# st.dataframe(changed_rows)



# import streamlit as st
# import pandas as pd
# from st_aggrid import AgGrid, GridUpdateMode

# # --- Mock data ---
# df = pd.DataFrame({
#     "A": [1, 2, 3],
#     "B": [4, 5, 6],
#     "C": [7, 8, 9]
# })

# # --- Initialize session state ---
# if "org_df" not in st.session_state:
#     st.session_state["org_df"] = df.copy()
# if "current_df" not in st.session_state:
#     st.session_state["current_df"] = df.copy()

# # --- Render AgGrid ---
# grid_response = AgGrid(
#     st.session_state["current_df"],
#     gridOptions={"defaultColDef": {"editable": True, "resizable": True}},
#     update_mode=GridUpdateMode.VALUE_CHANGED,
#     theme="alpine",
#     height=300,
#     key="grid_test"
# )

# # --- Capture latest edited data ---
# updated_df = pd.DataFrame(grid_response["data"])

# # --- Get previous snapshot ---
# previous_df = st.session_state["current_df"].copy()

# # --- Normalize (AgGrid can cast numbers as float/str) ---
# previous_norm = previous_df.astype(str)
# updated_norm = updated_df.astype(str)

# # --- Compare and detect changed rows ---
# mask = updated_norm.ne(previous_norm)
# changed_rows = updated_df[mask.any(axis=1)]

# # --- Display results ---
# st.write("Changed rows (since last edit):")
# st.dataframe(changed_rows)

# # --- Update session state only if changes detected ---
# if not changed_rows.empty:
#     st.session_state["current_df"] = updated_df.copy()



# @st.dialog("RFL編集終了確認", width="large")
# def off_rfl_edit():

#     st.write('編集モードを終了します　')
#     st.write('編集内容を確定しますか？')

#     import re

#     # ============================================
#     # Detect all i such that rfl_pj_response_i exists
#     # ============================================
#     indices = sorted([
#         int(k.split('_')[-1])
#         for k in st.session_state.keys()
#         if k.startswith('rfl_pj_response_')
#     ])

#     all_changed_rows = []  # collect results for all indices

#     # ============================================
#     # Loop over each index
#     # ============================================
#     for i in indices:

#         # ============================================================
#         # Step 1: Data Preparation
#         # ============================================================
#         original_df = st.session_state[f'org_rfl_pj_{i}'].reset_index(drop=True)
#         response_df = st.session_state[f'rfl_pj_response_{i}'].reset_index(drop=True)

#         original_df = original_df.drop(columns=['rfl_id', 'phase'], errors='ignore')
#         response_df = response_df.drop(columns=['rfl_id', 'phase'], errors='ignore')

#         # ============================================================
#         # Step 2: Configuration Definition
#         # ============================================================
#         prefixes = ['c_', 's_', 'u_']

#         base_columns = {
#             'req', 'func', 'logic', 'note', 'r_item', 'f_item', 'l_item',
#             'r_unit', 'f_unit', 'l_unit', 'r_scene', 'l_scene',
#             'req_condition', 'log_condition',
#             'sender_judge', 'sender_name', 'sender_date', 'sender_comment',
#             'receiver_judge', 'receiver_name', 'receiver_date', 'receiver_comment',
#             'l_wp'
#         }

#         key_base_names = ['r_pj_id', 'phase_id', 'rfl_id', 'r_s_id', 'l_s_id', 'f_id']
#         date_base_names = ['sender_date', 'receiver_date']

#         consolidated_rows = []

#         # ============================================================
#         # Step 3: Detect Changes for Each Hierarchy
#         # ============================================================
#         for prefix in prefixes:

#             prefix_cols = []

#             # prefix base columns
#             for base_col in base_columns:
#                 prefixed_col = f'{prefix}{base_col}'
#                 if prefixed_col in original_df.columns:
#                     prefix_cols.append(prefixed_col)

#                 prefixed_id_col = f'{prefix}{base_col}_id'
#                 if prefixed_id_col in original_df.columns:
#                     prefix_cols.append(prefixed_id_col)

#             # key columns
#             for key_base in key_base_names:
#                 prefixed_key = f'{prefix}{key_base}'
#                 if prefixed_key in original_df.columns:
#                     prefix_cols.append(prefixed_key)

#             if not prefix_cols:
#                 continue

#             prefix_original = original_df[prefix_cols].copy()
#             prefix_response = response_df[prefix_cols].copy()

#             # date processing
#             for date_base in date_base_names:
#                 date_col = f'{prefix}{date_base}'
#                 if date_col in prefix_original.columns:
#                     prefix_original[date_col] = pd.to_datetime(prefix_original[date_col], errors='coerce')
#                     prefix_response[date_col] = pd.to_datetime(prefix_response[date_col], errors='coerce')
#                     prefix_original[date_col] = prefix_original[date_col].fillna(pd.Timestamp('1700-01-01'))
#                     prefix_response[date_col] = prefix_response[date_col].fillna(pd.Timestamp('1700-01-01'))

#             # convert non-date to string
#             for col in prefix_original.columns:
#                 if col not in [f'{prefix}{d}' for d in date_base_names]:
#                     prefix_original[col] = prefix_original[col].astype(str)
#                     prefix_response[col] = prefix_response[col].astype(str)

#             prefix_diff_cells = prefix_original != prefix_response
#             prefix_diff_rows = prefix_diff_cells.any(axis=1)

#             if not prefix_diff_rows.any():
#                 continue

#             prefix_changed_cols = prefix_diff_cells.any(axis=0)
#             prefix_changed_cols_list = list(prefix_changed_cols[prefix_changed_cols].index)

#             for key_base in key_base_names:
#                 prefixed_key = f'{prefix}{key_base}'
#                 if prefixed_key in prefix_response.columns and prefixed_key not in prefix_changed_cols_list:
#                     prefix_changed_cols_list.insert(0, prefixed_key)

#             prefix_changed_cols_list = [col for col in prefix_changed_cols_list if col in prefix_response.columns]

#             prefix_changed_df = prefix_response.loc[prefix_diff_rows, prefix_changed_cols_list].copy()

#             for col in prefix_changed_df.columns:
#                 if col not in [f'{prefix}{k}' for k in key_base_names]:
#                     mask = prefix_diff_cells.loc[prefix_changed_df.index, col]
#                     prefix_changed_df.loc[~mask, col] = None

#             for idx2, row in prefix_changed_df.iterrows():

#                 prefixed_r_pj_id = f'{prefix}r_pj_id'
#                 prefixed_phase_id = f'{prefix}phase_id'
#                 prefixed_rfl_id = f'{prefix}rfl_id'

#                 def is_empty(value):
#                     return (
#                         value is None or
#                         pd.isna(value) or
#                         (isinstance(value, str) and value.strip().lower() in ['', 'none', 'null', 'nan'])
#                     )

#                 if (prefixed_r_pj_id not in row.index or is_empty(row[prefixed_r_pj_id])):
#                     continue

#                 if (prefixed_phase_id not in row.index or is_empty(row[prefixed_phase_id])):
#                     continue

#                 if prefixed_rfl_id not in row.index or pd.isna(row[prefixed_rfl_id]):
#                     continue

#                 consolidated_row = {}

#                 for key_base in key_base_names:
#                     prefixed_key = f'{prefix}{key_base}'
#                     if prefixed_key in row.index and pd.notna(row[prefixed_key]):
#                         consolidated_row[key_base] = row[prefixed_key]

#                 has_data = False

#                 for col in prefix_changed_cols_list:
#                     if col.startswith(prefix):
#                         base_col = col[len(prefix):]

#                         if base_col in base_columns or base_col.endswith('_id'):
#                             value = row[col]

#                             if base_col.endswith('_id'):
#                                 if pd.notna(value) and str(value) not in ['nan', 'None']:
#                                     consolidated_row[base_col] = value
#                                     has_data = True
#                             else:
#                                 consolidated_row[base_col] = value
#                                 has_data = True

#                 if has_data:
#                     consolidated_rows.append(consolidated_row)

#         if consolidated_rows:
#             changed_columns_df = pd.DataFrame(consolidated_rows)
#         else:
#             changed_columns_df = pd.DataFrame()

#         # Step 5: Convert Units
#         unit_columns = ['f_unit', 'l_unit']
#         units_dict = rflq.get_units_dict()

#         for unit_col in unit_columns:
#             if unit_col in changed_columns_df.columns:
#                 unit_id_col = f'{unit_col}_id'
#                 changed_columns_df[unit_id_col] = changed_columns_df[unit_col].apply(
#                     lambda x: units_dict.get(x) if x not in [None, 'nan'] and pd.notna(x) else None
#                 )
#                 changed_columns_df.loc[changed_columns_df[unit_col].isna(), unit_id_col] = None

#         # Step 6: Convert WP
#         if 'l_wp' in changed_columns_df.columns:
#             wp_dict = rflq.get_wp_dict()
#             changed_columns_df['l_wp_id'] = changed_columns_df['l_wp'].apply(
#                 lambda x: wp_dict.get(x) if x not in [None, 'nan'] and pd.notna(x) else None
#             )

#         # add this index result
#         if not changed_columns_df.empty:
#             all_changed_rows.append(changed_columns_df)

#     # ============================================================
#     # Merge all results across all indices
#     # ============================================================
#     if all_changed_rows:
#         final_df = pd.concat(all_changed_rows, ignore_index=True)
#     else:
#         final_df = pd.DataFrame()

#     st.write("final_df:", final_df)

#     # ============================================================
#     # Final update
#     # ============================================================
#     if st.button("確定する"):
#         if final_df.empty:
#             st.error("編集内容がありません。")
#         else:
#             id_columns = [col for col in final_df.columns if col.endswith('_id')]
#             for id_col in id_columns:
#                 final_df[id_col] = final_df[id_col].apply(
#                     lambda x: int(float(x)) if pd.notna(x) and str(x) != 'nan' else None
#                 )

#             sql.update_rfl_infos(final_df)
#             st.session_state.rfl_edit_state = False



import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import pandas as pd

df = pd.DataFrame({
    "id": [1, 2, 3, 4,5],
    "s_id": [1, 1, 1, 2,3],
    "name": ["AAA", "", "", "BBB","AAA"],
    "address": ["Address1", "Address2", "Address3", "Address1","Address2"],
})

# Mark the first row of each s_id
first_indexes = df.groupby("s_id").head(1).index
df["is_first"] = df.index.isin(first_indexes)

gb = GridOptionsBuilder.from_dataframe(df)

# ------------------------------------
# 1. Set ALL columns not editable first
# ------------------------------------
for col in df.columns:
    gb.configure_column(col, editable=False)

# ------------------------------------
# 2. Override only the ones allowed
# ------------------------------------
for col in ["name"]:
    gb.configure_column(
        col,
        editable=True,
        cellEditor="agTextCellEditor",
    )

# Hide helper column
gb.configure_column("is_first", hide=True)

grid_options = gb.build()

# Modify columnDefs to add editable function after building
# This is needed because GridOptionsBuilder doesn't support editableFunction parameter
# In AG Grid, editable can be a function that returns boolean
# Use JsCode wrapper to properly pass JavaScript functions to AG Grid
for col_def in grid_options["columnDefs"]:
    if col_def.get("field") in ["name"]:
        # Set editable as a JavaScript function using JsCode wrapper
        col_def["editable"] = JsCode("""
            function(params) {
                console.log('Editable check - field:', params.colDef.field);
                console.log('Editable check - data:', params.data);
                var isFirst = params.data.is_first;
                console.log('is_first value:', isFirst, 'type:', typeof isFirst);
                var result = isFirst === true || isFirst === "True" || isFirst === 1 || String(isFirst).toLowerCase() === "true";
                console.log('Editable result:', result);
                return result;
            }
        """)

AgGrid(
    df,
    gridOptions=grid_options,
    allow_unsafe_jscode=True,
)




# import streamlit as st
# from st_aggrid import AgGrid, GridOptionsBuilder
# import pandas as pd

# df = pd.DataFrame({
#     "id": [1, 2, 3, 4],
#     "s_id": [1, 1, 1, 2],
#     "name": ["AAA", "", "", "BBB"],
#     "address": ["Address1", "Address2", "Address3", "Address1"],
# })

# # mark first row of each s_id
# first_indexes = df.groupby("s_id").head(1).index
# df['is_first'] = df.index.isin(first_indexes)

# gb = GridOptionsBuilder.from_dataframe(df)

# # ALL columns editable FALSE at start
# for col in df.columns:
#     gb.configure_column(col, editable=False)

# # Only name/address use rule
# for col in ["name", "address"]:
#     gb.configure_column(
#         col,
#         editable=True,
#         cellEditor="agTextCellEditor",
#         cellStyle="""
#             function(params) {
#                 if (params.data.is_first === true) {
#                     return {};              // editable
#                 } else {
#                     return {                // lock cell
#                         pointerEvents: 'none',
#                         backgroundColor: '#f0f0f0'
#                     };
#                 }
#             }
#         """
#     )

# # hide helper
# gb.configure_column("is_first", hide=True)

# grid_options = gb.build()

# AgGrid(df, gridOptions=grid_options, allow_unsafe_jscode=True)




# import streamlit as st
# import pandas as pd
# import io
# from st_aggrid import AgGrid, GridOptionsBuilder

# # Sample data
# df = pd.DataFrame({
#     "Name": ["Alice", "Bob", "Carol"],
#     "Age": [22, 25, 19],
#     "Score": [88, 92, 79]
# })

# st.title("AgGrid → Excel export example (corrected)")

# # Display editable grid
# gb = GridOptionsBuilder.from_dataframe(df)
# gb.configure_default_column(editable=True)
# grid_options = gb.build()

# grid_response = AgGrid(df, gridOptions=grid_options,
#                       enable_enterprise_modules=False,
#                       fit_columns_on_grid_load=True)
# out_df = pd.DataFrame(grid_response["data"])

# st.write("Edited data:")
# st.dataframe(out_df)

# def to_excel_with_style(df: pd.DataFrame) -> bytes:
#     output = io.BytesIO()
#     # Use context manager — ensures file is closed properly
#     with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
#         df.to_excel(writer, index=False, sheet_name="Sheet1")
#         workbook  = writer.book
#         worksheet = writer.sheets["Sheet1"]

#         # Style: bold header + grey background
#         header_fmt = workbook.add_format({
#             "bold": True,
#             "bg_color": "#D3D3D3",
#             "border": 1
#         })
#         for col_num, value in enumerate(df.columns.values):
#             worksheet.write(0, col_num, value, header_fmt)

#         # Conditional highlight: Score < 80 → red fill
#         highlight_fmt = workbook.add_format({"bg_color": "#FFC7CE"})
#         for row, score in enumerate(df["Score"], start=1):
#             if score < 80:
#                 worksheet.set_row(row, None, highlight_fmt)

#     return output.getvalue()

# excel_data = to_excel_with_style(out_df)
# st.download_button(
#     label="Download Excel with style",
#     data=excel_data,
#     file_name="styled_export.xlsx",
#     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
# )



#this work.

# import streamlit as st
# import pandas as pd
# from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

# # --------------------------------------------------
# # 1. Normalize 全角 → 半角 on INITIAL LOAD (Python)
# # --------------------------------------------------
# def zenkaku_to_hankaku(text):
#     if not isinstance(text, str):
#         return text

#     return text.translate(
#         str.maketrans({
#             chr(i): chr(i - 0xFEE0)
#             for i in range(0xFF01, 0xFF5F)  # Full-width ASCII
#         })
#     )

# # Sample data (contains 全角)
# df = pd.DataFrame({
#     "price": [100, 200, 300],
#     "about": ["商品Ａ", "テスト１２３", "ｈｅｌｌｏ！"]
# })

# # Normalize once BEFORE grid renders
# df["about"] = df["about"].apply(zenkaku_to_hankaku)

# # --------------------------------------------------
# # 2. Build AgGrid options
# # --------------------------------------------------
# gb = GridOptionsBuilder.from_dataframe(df)

# # price: numeric only
# gb.configure_column(
#     "price",
#     editable=True,
#     cellEditor="agNumericCellEditor",
#     valueParser=JsCode("Number(newValue)")
# )

# # about: text column, 全角 → 半角 ON EDIT
# about_setter = JsCode("""
# function(params) {
#     if (params.newValue == null) {
#         params.data.about = "";
#         return true;
#     }

#     params.data.about = params.newValue.toString()
#         .replace(/[！-～]/g, function(c) {
#             return String.fromCharCode(c.charCodeAt(0) - 0xFEE0);
#         });

#     return true;
# }
# """)

# gb.configure_column(
#     "about",
#     editable=True,
#     valueSetter=about_setter
# )

# gridOptions = gb.build()

# # --------------------------------------------------
# # 3. Render grid
# # --------------------------------------------------
# grid_response = AgGrid(
#     df,
#     gridOptions=gridOptions,
#     editable=True,
#     allow_unsafe_jscode=True,
#     fit_columns_on_grid_load=True
# )

# # --------------------------------------------------
# # 4. Show updated data
# # --------------------------------------------------
# st.subheader("Updated Data")
# st.dataframe(grid_response["data"])






# import streamlit as st
# import pandas as pd
# from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

# # -------------------------------
# # 1. Normalize 全角 → 半角 on load
# # -------------------------------
# def zenkaku_to_hankaku(text):
#     if not isinstance(text, str):
#         return text
#     return text.translate(
#         str.maketrans({
#             chr(i): chr(i - 0xFEE0) 
#             for i in range(0xFF01, 0xFF5F)
#         })
#     )

# df = pd.DataFrame({
#     "price": [100, 200, 300],
#     "about": ["商品Ａ", "テスト１２３", "ｈｅｌｌｏ！"]
# })

# df["about"] = df["about"].apply(zenkaku_to_hankaku)

# # -------------------------------
# # 2. Build AgGrid options
# # -------------------------------
# gb = GridOptionsBuilder.from_dataframe(df)

# # price: numeric only, aligned with cell
# numeric_editor = JsCode("""
# class NumericEditor {
#     init(params) {
#         this.params = params;
#         this.eInput = document.createElement('input');
#         this.eInput.type = 'text';
#         this.eInput.value = params.value;
        
#         // Match grid cell style
#         this.eInput.style.width = '100%';
#         this.eInput.style.height = '100%';
#         this.eInput.style.boxSizing = 'border-box';
#         this.eInput.style.border = 'none';
#         this.eInput.style.padding = '0 2px';
#         this.eInput.style.fontSize = 'inherit';
#         this.eInput.style.fontFamily = 'inherit';
        
#         // Only digits
#         this.eInput.addEventListener('keypress', function(e) {
#             const char = String.fromCharCode(e.which);
#             if (!/[0-9]/.test(char)) {
#                 e.preventDefault();
#             }
#         });
#     }

#     getGui() {
#         return this.eInput;
#     }

#     afterGuiAttached() {
#         this.eInput.focus();
#         this.eInput.select();
#     }

#     getValue() {
#         return Number(this.eInput.value);
#     }

#     destroy() {}
#     isPopup() { return false; } // important: makes it inline, not floating
# }
# """)


# # # -------------------------------
# # # Custom IME-safe numeric editor for price
# # # -------------------------------
# # numeric_editor = JsCode("""
# # class NumericEditor {
# #     init(params) {
# #         this.params = params;
# #         this.composing = false;

# #         this.eInput = document.createElement('input');
# #         this.eInput.type = 'text';
# #         this.eInput.value = params.value;

# #         // Style to match grid cell
# #         this.eInput.style.width = '100%';
# #         this.eInput.style.height = '100%';
# #         this.eInput.style.boxSizing = 'border-box';
# #         this.eInput.style.border = 'none';
# #         this.eInput.style.padding = '0 2px';
# #         this.eInput.style.fontSize = 'inherit';
# #         this.eInput.style.fontFamily = 'inherit';

# #         // Handle IME composition
# #         this.eInput.addEventListener('compositionstart', () => {
# #             this.composing = true;
# #         });
# #         this.eInput.addEventListener('compositionend', (e) => {
# #             this.composing = false;
# #             this.eInput.value = this.eInput.value.replace(/[^0-9]/g,''); // sanitize after IME commit
# #         });

# #         // Sanitize input for normal typing / paste
# #         this.eInput.addEventListener('input', () => {
# #             if (!this.composing) {
# #                 this.eInput.value = this.eInput.value.replace(/[^0-9]/g,'');
# #             }
# #         });
# #     }

# #     getGui() {
# #         return this.eInput;
# #     }

# #     afterGuiAttached() {
# #         this.eInput.focus();
# #         this.eInput.select();
# #     }

# #     getValue() {
# #         return this.eInput.value === '' ? None : Number(this.eInput.value);
# #     }

# #     destroy() {}

# #     isPopup() { return false; }  // inline editor
# # }
# # """)


# gb.configure_column(
#     "price",
#     editable=True,
#     cellEditor=numeric_editor
# )

# # about: text column, 全角 → 半角
# about_setter = JsCode("""
# function(params) {
#     if (params.newValue == null) {
#         params.data.about = "";
#         return true;
#     }

#     params.data.about = params.newValue.toString()
#         .replace(/[！-～]/g, function(c) {
#             return String.fromCharCode(c.charCodeAt(0) - 0xFEE0);
#         });

#     return true;
# }
# """)
# gb.configure_column(
#     "about",
#     editable=True,
#     valueSetter=about_setter
# )

# gridOptions = gb.build()

# # -------------------------------
# # 3. Render AgGrid
# # -------------------------------
# grid_response = AgGrid(
#     df,
#     gridOptions=gridOptions,
#     editable=True,
#     allow_unsafe_jscode=True,
#     fit_columns_on_grid_load=True
# )

# # -------------------------------
# # 4. Display updated data
# # -------------------------------
# st.subheader("Updated Data")
# st.dataframe(grid_response["data"])




import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

# -------------------------------
# 1. Normalize 全角 → 半角 on initial load
# -------------------------------
def zenkaku_to_hankaku(text):
    if not isinstance(text, str):
        return text
    return text.translate(
        str.maketrans({
            chr(i): chr(i - 0xFEE0) 
            for i in range(0xFF01, 0xFF5F)
        })
    )

df = pd.DataFrame({
    "price": [100, 200, 300],
    "about": ["商品Ａ", "テスト１２３", "ｈｅｌｌｏ！"]
})

df["about"] = df["about"].apply(zenkaku_to_hankaku)

# -------------------------------
# 2. Build AgGrid options
# -------------------------------
gb = GridOptionsBuilder.from_dataframe(df)

# -------------------------------
# Price column: allow typing anything
# Only update if input is all digits
# -------------------------------
price_setter = JsCode("""
function(params) {
    if (params.newValue == null) return true;

    // If newValue is digits only, update value
    if (/^[0-9]+$/.test(params.newValue.toString())) {
        params.data.price = parseInt(params.newValue, 10);
    }
    // Else: do nothing, keep previous value
    return true;
}
""")
gb.configure_column(
    "price",
    editable=True,
    cellEditor='agTextCellEditor',  # force text input
    valueSetter=price_setter
)

# -------------------------------
# About column: 全角 → 半角 on edit
# -------------------------------
about_setter = JsCode("""
function(params) {
    if (params.newValue == null) {
        params.data.about = "";
        return true;
    }
    params.data.about = params.newValue.toString()
        .replace(/[！-～]/g, c => String.fromCharCode(c.charCodeAt(0) - 0xFEE0));
    return true;
}
""")
gb.configure_column(
    "about",
    editable=True,
    valueSetter=about_setter
)

gridOptions = gb.build()

# -------------------------------
# 3. Render AgGrid
# -------------------------------
grid_response = AgGrid(
    df,
    gridOptions=gridOptions,
    editable=True,
    allow_unsafe_jscode=True,
    fit_columns_on_grid_load=True
)

# -------------------------------
# 4. Display updated data
# -------------------------------
st.subheader("Updated Data")
st.dataframe(grid_response["data"])

