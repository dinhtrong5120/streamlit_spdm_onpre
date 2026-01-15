import pandas as pd
from st_aggrid import AgGrid,GridOptionsBuilder,JsCode
import streamlit as st
import json
import const.constpara as co
# データを辞書形式で定義
st.set_page_config(layout="wide")
# サンプルデータの作成
data = {
    "SElist_[Kei]_JPN_2WD;z_parent_paraitem;Variation#1": ["Vehicle Weight", "Vehicle Weight", "Vehicle Weight"],
    "SElist_[Kei]_JPN_2WD;z_child_paraitem;Variation#1": ["Min.C.W.", "Max.C.W.", "スペアタイヤ&工具"],
    "SElist_[Kei]_JPN_2WD;z_unit;Variation#1": ["kg", "kg", "kg"],
    "SElist_[Kei]_JPN_2WD;z_request_median;Variation#1": [1102, 1116, 1.6],
    "SElist_[Kei]_JPN_2WD;z_request_median;Variation#2": [1102, 1116, 1.6],
    "SElist_[Kei]_JPN_2WD;z_request_median;Variation#3": [1102, 1116, 1.6],
    "SElist_[Kei]_JPN_2WD;z_request_median;Variation#4": [1102, 1116, 1.6]
}

# データフレームを作成
df = pd.DataFrame(data)

# カスタムCSSを読み込む
css_ag = {}
try:
    with open(co.css_ag, encoding='utf-8') as f:
        css_ag = json.load(f)
except Exception as e:
    st.error(f"CSSファイルの読み込みに失敗しました: {e}")

# GridOptionsBuilderを使用してオプションを設定
# gb = GridOptionsBuilder.from_dataframe(df)
# gb.configure_grid_options(treeData=True, animateRows=True)
# gb.configure_column('SElist_[Kei]_JPN_2WD;z_parent_paraitem;Variation#1', hide=True)  # 親列を隠す
# gb.configure_column('SElist_[Kei]_JPN_2WD;z_child_paraitem;Variation#1', headerName='パラメータ名', cellRenderer='agGroupCellRenderer')

# # gridOptionsの取得
# gridOptions = gb.build()

# カスタムのgridOptionsを追加
gridOptions = {
    "defaultColDef": {
        "flex": 1,
        "resizable": True,
        "wrapHeaderText": True,
        "suppressMovable": True,
        "allowDragFromColumnsToolPanel": True,
        "filter": True
    },
    "autoGroupColumnDef": {
        "headerName": "パラメータ名",
        "pinned": "left",
        "width": 350,
        "wrapText": True,
        "headerClass": "title_green"
    },
    "columnDefs": [
        {
            "headerName": "プロジェクト",
            "headerClass": "group_title_green",
            "children": [
                {
                    "headerName": "仕向け",
                    "headerClass": "group_title_green",
                    "children": [
                        {
                            "headerName": "駆動方式",
                            "headerClass": "group_title_green",
                            "children": [
                                {
                                    "field": "SElist_[Kei]_JPN_2WD;z_unit;Variation#1",
                                    "headerName": "単位",
                                    "pinned": "left",
                                    "filter": True,
                                    "width": 110,
                                    "headerClass": "title_green"
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "headerName": "[Kei]",
            "headerClass": "group_green",
            "children": [
                {
                    "headerName": "JPN",
                    "headerClass": "group_green",
                    "children": [
                        {
                            "headerName": "2WD",
                            "headerClass": "group_green",
                            "children": [
                                {
                                    "field": "SElist_[Kei]_JPN_2WD;z_request_median;Variation#1",
                                    "headerName": "Variation#1",
                                    "suppressMovable": True,
                                    "wrapText": True,
                                    "minWidth": 70,
                                    "editable": False,
                                    "headerTooltip": "",
                                    "tooltipField": "SElist_[Kei]_JPN_2WD;update_day;Variation#1",
                                    "headerClass": "green",
                                    "tooltipShowDelay": 0
                                },
                                {
                                    "field": "SElist_[Kei]_JPN_2WD;z_request_median;Variation#2",
                                    "headerName": "Variation#2",
                                    "suppressMovable": True,
                                    "wrapText": True,
                                    "minWidth": 70,
                                    "editable": False,
                                    "headerTooltip": "ロット:PT構想審査 車種:Slide",
                                    "tooltipField": "SElist_[Kei]_JPN_2WD;update_day;Variation#2",
                                    "headerClass": "green",
                                    "tooltipShowDelay": 0
                                },
                                {
                                    "field": "SElist_[Kei]_JPN_2WD;z_request_median;Variation#3",
                                    "headerName": "Variation#3",
                                    "suppressMovable": True,
                                    "wrapText": True,
                                    "minWidth": 70,
                                    "editable": False,
                                    "headerTooltip": "ロット:PT構想審査 車種:Slide",
                                    "tooltipField": "SElist_[Kei]_JPN_2WD;update_day;Variation#3",
                                    "headerClass": "green",
                                    "tooltipShowDelay": 0
                                },
                                {
                                    "field": "SElist_[Kei]_JPN_2WD;z_request_median;Variation#4",
                                    "headerName": "Variation#4",
                                    "suppressMovable": True,
                                    "wrapText": True,
                                    "minWidth": 70,
                                    "editable": False,
                                    "headerTooltip": "ロット:PT構想審査 車種:Slide",
                                    "tooltipField": "SElist_[Kei]_JPN_2WD;update_day;Variation#4",
                                    "headerClass": "green",
                                    "tooltipShowDelay": 0
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ],
    "treeData": True,
    "pagination": True,
    "groupDefaultExpanded": -1,
    "rowSelection": "multiple",
    "suppressRowClickSelection": True,
    "groupSelectsChildren": True,
    "enableRangeSelection": True,
    "suppressMultiRangeSelection": True,
    "sideBar": {
        "toolPanels": [
            {
                "id": "columns",
                "labelDefault": "Columns",
                "labelKey": "columns",
                "iconKey": "columns",
                "toolPanel": "agColumnsToolPanel",
                "toolPanelParams": {
                    "suppressRowGroups": True,
                    "suppressValues": True,
                    "suppressPivots": True,
                    "suppressPivotMode": True,
                    "suppressColumnFilter": True,
                    "suppressColumnSelectAll": True,
                    "suppressColumnExpandAll": True
                }
            }
        ]
    },
    # "getDataPath": "::JSCODE:: function(data) { return data.param; } ::JSCODE::"
}
# gridOptions['getDataPath'] = JsCode('''
#                 function(data) {
#                     return data.param;
#                 }
                
#             ''').js_code
    

# gridOptions['getDataPath'] = JsCode('''
# function(data) {
#     return [data['SElist_[Kei]_JPN_2WD;z_parent_paraitem;Variation#1'], data['SElist_[Kei]_JPN_2WD;z_child_paraitem;Variation#1']];
# }''').js_code

# AgGridの表示
AgGrid(df, 
       custom_css=css_ag, 
       gridOptions=gridOptions, 
       theme="alpine", 
       height=400)

st.write("test")