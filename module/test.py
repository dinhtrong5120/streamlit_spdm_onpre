# import streamlit as st
# import pandas as pd
# from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

# st.title("🔗 AgGrid Clickable Link Example (DOM-based, fully working)")

# # Example IDs
# project_id = 1
# phase_id = 101
# variation_id = "A"

# # --- Sample Data ---
# data = [
#     {
#         f"{project_id};note;{phase_id}{variation_id}": "Design Doc",
#         f"{project_id};url;{phase_id}{variation_id}": "https://google.com",
#     },
#     {
#         f"{project_id};note;{phase_id}{variation_id}": "Specification Sheet",
#         f"{project_id};url;{phase_id}{variation_id}": "example.com/spec",
#     },
#     {
#         f"{project_id};note;{phase_id}{variation_id}": "No Link Yet",
#         f"{project_id};url;{phase_id}{variation_id}": "",
#     },
# ]

# df = pd.DataFrame(data)

# # --- ✅ JS cell renderer: creates a clickable <a> element ---
# memo_cell_renderer = JsCode(f"""
# class LinkCellRenderer {{
#     init(params) {{
#         const displayText = params.value || '';
#         const urlField = '{project_id};url;{phase_id}{variation_id}';
#         const url = params.data[urlField];
#         this.eGui = document.createElement('a');
#         this.eGui.innerText = displayText;
#         if (url) {{
#             const finalUrl = url.startsWith('http') ? url : 'https://' + url;
#             this.eGui.setAttribute('href', finalUrl);
#             this.eGui.setAttribute('target', '_blank');
#             this.eGui.style.color = 'blue';
#             this.eGui.style.textDecoration = 'underline';
#             this.eGui.style.cursor = 'pointer';
#         }} else {{
#             this.eGui.style.color = 'gray';
#             this.eGui.style.textDecoration = 'none';
#             this.eGui.style.cursor = 'default';
#         }}
#     }}
#     getGui() {{
#         return this.eGui;
#     }}
# }}
# """)

# # --- Configure AgGrid ---
# gb = GridOptionsBuilder.from_dataframe(df)
# gb.configure_column(
#     f"{project_id};note;{phase_id}{variation_id}",
#     header_name="考え方",
#     cellRenderer=memo_cell_renderer,
#     cellStyle={"background-color": "#FFFFCC"},
# )
# gb.configure_column(f"{project_id};url;{phase_id}{variation_id}", hide=True)

# gridOptions = gb.build()

# # --- Display grid ---
# AgGrid(
#     df,
#     gridOptions=gridOptions,
#     allow_unsafe_jscode=True,  # required for JsCode
#     fit_columns_on_grid_load=True,
#     height=200,
# )



import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

# -----------------------------
# Sample data
# -----------------------------
project_id = 1
phase_id = 101
variation_id = "A"

data = [
    {
        f"{project_id};note;{phase_id}{variation_id}": "Design Doc",
        f"{project_id};url;{phase_id}{variation_id}": "https://example.com/design",
        "performance": "High",
        "params0p": ["Group 1"]
    },
    {
        f"{project_id};note;{phase_id}{variation_id}": "Specification Sheet",
        f"{project_id};url;{phase_id}{variation_id}": "example.com/spec",
        "performance": "Medium",
        "params0p": ["Group 1"]
    },
    {
        f"{project_id};note;{phase_id}{variation_id}": "No Link Yet",
        f"{project_id};url;{phase_id}{variation_id}": "",
        "performance": "Low",
        "params0p": ["Group 2"]
    },
]

df = pd.DataFrame(data)

# -----------------------------
# Custom JsCode renderer for clickable links
# -----------------------------
memo_cell_renderer = JsCode(f"""
class LinkCellRenderer {{
    init(params) {{
        const displayText = params.value || '';
        const urlField = '{project_id};url;{phase_id}{variation_id}';
        const url = params.data[urlField];
        this.eGui = document.createElement('a');
        this.eGui.innerText = displayText;
        if (url) {{
            const finalUrl = url.startsWith('http') ? url : 'https://' + url;
            this.eGui.setAttribute('href', finalUrl);
            this.eGui.setAttribute('target', '_blank');
            this.eGui.style.color = 'blue';
            this.eGui.style.textDecoration = 'underline';
            this.eGui.style.cursor = 'pointer';
        }} else {{
            this.eGui.style.color = 'gray';
            this.eGui.style.textDecoration = 'none';
            this.eGui.style.cursor = 'default';
        }}
    }}
    getGui() {{
        return this.eGui;
    }}
}}
""")

# -----------------------------
# Your grid function
# -----------------------------
def grid_fun():
    go = {
        'defaultColDef': {
            'flex':1,
            'resizable': True,
            'wrapHeaderText': True,
            'suppressMovable': True,
            'allowDragFromColumnsToolPanel': True,
            'filter': True,
        },
        'autoGroupColumnDef': {
            'headerName': '性能',
            'field': 'performance',
            'pinned': 'left',
            'width': 200,
            'wrapText': True,
            'headerClass': 'title_white'
        },
        'columnDefs': [],
        'treeData': False,
        'pagination': True,
        'groupDefaultExpanded': -1,
        'rowSelection': 'multiple',
        'suppressRowClickSelection': True,
        'groupSelectsChildren': True,
        'enableRangeSelection': True,
        'enableBrowserTooltips': True,
        'enableCharts': True,
        'suppressMultiRangeSelection': True,
        'alwaysShowHorizontalScroll': True,
        'sideBar': {
            'toolPanels': [
                {
                    'id': 'columns',
                    'labelDefault': 'Columns',
                    'labelKey': 'columns',
                    'iconKey': 'columns',
                    'toolPanel': 'agColumnsToolPanel',
                    'toolPanelParams': {
                        'suppressValues': True,
                        'suppressPivots': True,
                        'suppressPivotMode': True,
                        'suppressColumnFilter': True,
                        'suppressColumnSelectAll': True,
                        'suppressColumnExpandAll': True,
                    },
                },
            ],
        },
        'getDataPath': JsCode('''
            function(data) {
                return data.params0p;
            }
        ''').js_code
    }

    # -----------------------------
    # Add custom columns
    # -----------------------------
    go_add = []

    # Clickable note column
    go_add.append({
        "headerName": "TEST",
        "field": f"{project_id};note;{phase_id}{variation_id}",
        "cellRenderer": memo_cell_renderer,
        "cellStyle": {"background-color": "#FFFFCC"},
        "editable": False,
        "minWidth": 180,
    })

    # # Hidden URL column
    # go_add.append({
    #     "headerName": "URL (hidden)",
    #     "field": f"{project_id};url;{phase_id}{variation_id}",
    #     "hide": True,
    # })

    go['columnDefs'].extend(go_add)
    return go

# -----------------------------
# Render the grid
# -----------------------------
gridOptions = grid_fun()
AgGrid(
    df,
    gridOptions=gridOptions,
    allow_unsafe_jscode=True,
    fit_columns_on_grid_load=True,
    height=300,
)
