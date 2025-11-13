import streamlit as st
import re
from typing import Tuple
from st_aggrid import JsCode
from config.config import RFLGridConfig

def create_gridop():
    #チョー　#11/25
    st.session_state['grid_field'] = [None] * len(st.session_state.prj_info_list)
    for i, row in st.session_state.prj_info_list.iterrows(): 
        prj_number = row['z_prj_number']
        scene = row['modified_string']
        # field = row['z_wp_name_get_str']
        # pe = row['z_class_name_get_str'][0] + row['z_class_name_get_str'][-1]
        field = str(row['variation_id']) #10/29 merge#3 merge#4
        pe = str(row['phase_id']) #10/29 merge#3 merge#4
        phase = row['z_class_name_get_str']
        st.session_state['grid_field'][i] = prj_number + ';z_request_median;' +pe+ field
    
    header_stuck = st.session_state['grid_field']
    if 'compare_click' not in st.session_state:
        st.session_state['compare_click'] = False
   
    # BGcolorRenderer = JsCode(f"""
    # function (params) {{
    #     console.log("params data: ", params.data);
    #     const compare_btn_clicked = {str(st.session_state['compare_click']).lower()};
    #     if (params.data === undefined) {{
    #         return {{
    #             'background-color': '#C0C0C0',
    #             'wordBreak': 'normal',
    #             'whiteSpace': 'pre-line'
    #         }};
    #     }} else if (params.value === null) {{
    #         return {{
    #             'background-color': '#EFEFEF',
    #             'wordBreak': 'normal',
    #             'whiteSpace': 'pre-line'
    #         }};                         
    #     }} else if (compare_btn_clicked) {{
    #         // Convert header_stuck to a JavaScript array
    #         const headerStuck = {header_stuck};  
    #         const headerStuckLength = headerStuck.length;  // Get the length of header_stuck

    #         const valueA = params.data[headerStuck[0]];  // Access the first header value

    #         // let occurrenceCount = 0;
    #         // Loop through the header_stuck array starting from index 1
    #         for (let i = 1; i < headerStuckLength; i++) {{
    #             const valueB = params.data[headerStuck[i]];  // Access each subsequent header value
    #             // Check if the values are not equal
    #             if (valueA !== undefined && valueB !== undefined && valueA !== valueB) {{
    #                 return {{
    #                     'background-color': '#ffcccc',
    #                     'wordBreak': 'normal',
    #                     'whiteSpace': 'pre-line'
    #                 }};
    #             }}
    #         }}
    #     }}              
    #     return null; // Default style
    # }}
    # """)#山口加筆

    #Kyaw #CompareSE Upd #10/29 merge#3 merge#4
    BGcolorRenderer = JsCode(f"""
    function (params) {{
        console.log("params data: ", params.data);
        const compare_btn_clicked = {str(st.session_state['compare_click']).lower()};
        if (params.data === undefined) {{
            return {{
                'background-color': '#C0C0C0',
                'wordBreak': 'normal',
                'whiteSpace': 'pre-line'
            }};
        }} else if (params.value === null || params.value === '') {{
            return {{
                'background-color': '#EFEFEF',
                'wordBreak': 'normal',
                'whiteSpace': 'pre-line'
            }};                         
        }} else if (compare_btn_clicked) {{
            // Convert header_stuck to a JavaScript array
            const headerStuck = {header_stuck};  
            const valueA = params.data[headerStuck[0]];
            const currentField = params.colDef.field;
            const idx = headerStuck.indexOf(currentField);
            // Only compare if this is one of the columns in headerStuck (and not the first one)
            if (idx > 0) {{
                const valueB = params.data[currentField];
                if (valueA !== undefined && valueB !== undefined && valueA !== null && valueB !== null && valueA !== '' && valueB !== '' && valueA !== valueB) {{
                    return {{
                        'background-color': '#ffcccc',
                        'wordBreak': 'normal',
                        'whiteSpace': 'pre-line'
                    }};
                }}
            }}
        }}              
        return null; // Default style
    }}
    """)


    ChangeHighlight = JsCode(
        """
    function(e) {
        let api = e.api;
        let rowIndex = e.rowIndex;
        let col = e.column.colId;
        
        console.log(e);
        let rowNode = api.getDisplayedRowAtIndex(rowIndex);
        api.flashCells({
          rowNodes: [rowNode],
          columns: [col],
          flashDelay: 10000000000
        });

    };
    """
    )
    # test=JsCode("""
    # class CustomTooltip {
    #     eGui;

    # init(params) {
    #     const eGui = (this.eGui = document.createElement('div'));
    #     const tooltipField = params.colDef.tooltipField;
    #     // 取得したデータに「test」という文字列を結合して、eGuiのテキスト内容に設定します。
    #     const originalText = params.data[tooltipField];
    #     const truncatedText = originalText.slice(0, 10); // 最初の10文字を取得
    #     this.eGui.innerText = "更新日: " + truncatedText;        
    #     eGui.style['background-color'] = 'white'; // バックグラウンドカラーを白に設定
    #     eGui.style['color'] = 'black'; // 文字色を黒に設定
    #     eGui.style['padding'] = '10px'; // パディングを設定
    #     eGui.style['font-size'] = '16px'; // 文字サイズを少し大きく設定
    #     eGui.style['border-radius'] = '10px'; // 角を丸くする
    #     eGui.style['border'] = '1px solid black'; // 枠線を追加
    #     eGui.style['box-shadow'] = '0px 0px 10px rgba(0, 0, 0, 0.1)';
    # }

    # getGui() {
    #     return this.eGui;
    # }
    # }
    # """)

    edit_state = st.session_state.button_edit_state
    PJLOTjoho = {"z_name":"フェーズ","z_class_name_get_str":"ロット","z_drive_system":"駆動方式", "z_destination":"仕向け", "project_code":"プロジェクト",} #チョー　11/06 山口 ロットとフェーズの順番を入れ替えた　11/7
    # tooltip_joho = {"z_vehicle_type": "車種", "lot_name": "ロット"}#,"z_class_name_get_str":"階層"}
    # PJLOTjoho = {
    #     k: v for k, v in PJLOTjoho.items()
    #     if k in set([
    #         k2 for prj in st.session_state.prj_info for k2 in prj.keys()
    #         if prj[k2] != ''
    #     ])
    # }
    # col_scene = [
    #     col
    #     for col in st.session_state.se_data_stuck.columns
    #     if ';z_wp_name_get_str' in col
    # ]

    # col_scene = list(set(col_scene))
    # val_scene = [
    #     tuple(col.split(';')) if len(col.split(';'))>2
    #     else tuple(col.split(';') +  [''])
    #     for col in col_scene
    # ]
    # def extract_number(s: str) -> Tuple[bool, int]:
    #     """ 文字列から数字を抽出し、その数値と、数字があったかどうかのフラグを返す """
    #     match = re.search(r'\d+', s)
    #     if match:
    #         return (True, int(match.group(0)))
    #     return (False, float('inf'))  # 数字がない場合は無限大を返す
    # # ソートの実行
    # val_scene = sorted(val_scene, key=lambda x: (x[0], extract_number(x[2]), x[2]))
    
    
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
            'headerName': 'パラメータ名',
            'pinned': 'left',
            'width': 350,
            'wrapText': True,
            'headerClass': 'title_green'
        },
        'columnDefs': [],
        'treeData': True,
        'pagination': False,#山口　ページ折り返しが不便なので無効か7/30
        'groupDefaultExpanded': -1,
        'rowSelection': 'multiple',
        'suppressRowClickSelection': True,
        'groupSelectsChildren': True,
        'enableRangeSelection':True,
        'enableBrowserTooltips':True,#山口
        'onCellValueChanged':ChangeHighlight,#山口 11/4 値が変わったセルのハイライト
        'suppressMultiRangeSelection':True,
        # 'domLayout':'autoHeight',
        'sideBar': {
            'toolPanels': [
            {
                'id': 'columns',
                'labelDefault': 'Columns',
                'labelKey': 'columns',
                'iconKey': 'columns',
                'toolPanel': 'agColumnsToolPanel',
                'toolPanelParams': {
                'suppressRowGroups': True,
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
    }
    # 単位列のデフォルトオプション
    prj_info_list = st.session_state.prj_info_list
    prj = prj_info_list.iloc[0]['z_prj_number']
    ph_id = str(prj_info_list.iloc[0]['phase_id'])
    var_id = str(prj_info_list.iloc[0]['variation_id'])
    # sce = prj_info_list.iloc[0]['z_wp_name_get_str']
    # unit = prj_info_list.iloc[0]['z_class_name_get_str'][0] + prj_info_list.iloc[0]['z_class_name_get_str'][-1]
    go_add = {
        # 'field': prj+';z_unit_copy;'+unit+sce, 'headerName': '単位',
        'field': prj+';z_unit_copy;'+ph_id+var_id, 'headerName': '単位',
        'pinned': 'left', 'filter': True, 'width': 110,
        'headerClass': 'title_green'
    }
    for v in PJLOTjoho.values():
        go_add = {
            'headerName': v,
            'headerClass': 'group_title_green',
            'children': [
                go_add
            ]
        }
    
    go['columnDefs'].append(go_add)
    # パラメータ値列のデフォルトオプション
    go_scene = []
    go_phase = []
    # go_add = {}
    _prj_number = ''
    _phase = ''
    # info_list_count = 0
    header_coler = 'green'
    header_group_coler = 'group_green'
    # prj = st.session_state.prj_info[info_list_count]
    # for prj_number, _, scene in val_scene:
    row_count = len(prj_info_list)
    for i, row in prj_info_list.iterrows(): 
        # プロジェクトが切り替わったら、前回までのシーンをGridOptionへ追加
        prj_number = row['z_prj_number']
        scene = row['modified_string']
        field = row['variation_id']
        pe = row['phase_id']#山口 列名にくっつけたふぇーずようそ11/6
        phase = row['z_class_name_get_str']

        #チョー 11/25
        st.session_state['grid_field'][i] = prj_number + ';z_request_median;' +str(pe)+ str(field)

        cell_style = BGcolorRenderer  # Default style
        if(
            (
                prj_info_list.iloc[i]['project_id'] == 6 and
                prj_info_list.iloc[i]['phase_id'] == 7 and
                prj_info_list.iloc[i]['z_name'] == 'Pre-Pro' and
                prj_info_list.iloc[i]['z_destination'] == 'JPN' and
                prj_info_list.iloc[i]['z_drive_system'] == '2WD'
            )
            and st.session_state['compare_click'] is False
        ):
            edit_state = False
            st.session_state.se_data_stuck[prj_number + ';selected;'+str(pe)+ str(field)] = None
            cell_style = {'background-color': '#F5F5F5', 'wordBreak': 'normal', 'whiteSpace': 'pre-line'} 
        elif st.session_state['compare_click'] is True:
            edit_state = False
        else:
            st.session_state.se_data_stuck[prj_number + ';selected;' +str(pe)+ str(field)] = False
            edit_state = st.session_state.button_edit_state
        #中間確認会#1をロックする #チョー　04/14
        if prj_info_list.iloc[i]['project_id'] == 14 and prj_info_list.iloc[i]['phase_id'] == 15:
            edit_state = False

        #st.markdown(prj_number + scene + field)#山口デバック用
        col_detail = "ロット:" + row['z_name'] + " フェーズ:" + row['z_class_name_get_str'] #チョー　11/01　フェーズと車種→ロットとフェーズ
        if prj_number != _prj_number or i == row_count:# and _prj_number != '':山口編集、実行条件に最終行であることを追加
            #st.markdown("first if passed")
            #col_detail = ''#山口　用途不明のためコメントアウト
            # for k, v in reversed(tooltip_joho.items()):
            #     col_detail += str(v) + ':' + str(prj[k]) + '    '
            if _prj_number != '':
                #st.markdown("second if passed")
                go_phase.append({
                    'headerName': _row['z_class_name_get_str'],
                    'headerClass': header_group_coler,
                    'children': go_scene
                })
                go_add = {'headerName': _row['z_name'], 'headerClass': header_group_coler, 'children':go_phase } #チョー　11/06
                for k, v in PJLOTjoho.items():
                    if k!= 'z_name' and k != 'z_class_name_get_str': #チョー　11/06
                        #st.markdown("third if passed")
                        go_add = {
                            'headerName': _row[k],
                            'headerClass': header_group_coler,
                            'children': [go_add]
                        }
                go['columnDefs'].append(go_add)
                # info_list_count =+ 1
                # prj = st.session_state.prj_info[info_list_count]
                go_scene = []
                go_phase = []
                go_add = {}
                if header_coler == 'darkgreen':
                    #st.markdown("forth if passed")
                    header_coler = 'green'
                    header_group_coler = 'group_green'
                elif header_coler == 'green':
                    header_coler = 'darkgreen'
                    header_group_coler = 'group_darkgreen'
        _row = row#山口編集　Prj変わったタイミングで前の行のPrj情報を参照するためストックしておく
        _field = field
        _pe = pe
        if prj_number == _prj_number and phase != _phase:
            go_phase.append({
                'headerName': _phase,
                'headerClass': header_group_coler,
                'children': go_scene
            })
            go_scene = []
        go_scene.append({ #山口　選択列の追加 10/25
            'field': prj_number + ';selected;' +str(pe)+ str(field),#山口　フェーズ要素くっつけた 11/6
            'headerName': '編集',
            'suppressMovable': True,
            'wrapText': True,
            'minWidth': 40,
            'maxWidth': 40,
            'editable': edit_state,
            'cellStyle': cell_style,
            'headerTooltip': col_detail,
            'tooltipField':prj_number + ';edited_info;' +str(pe)+ str(field),#山口　フェーズ要素くっつけた 11/6
            'cellRenderer': 'agCheckboxCellRenderer',
            # 'tooltipComponent': test,
            'headerClass': header_coler,
            'tooltipShowDelay': 0
        }
         )
                      
        go_scene.append({
            'field': prj_number + ';z_request_median;' +str(pe)+ str(field),#山口　フェーズ要素くっつけた 11/6
            'headerName': scene,
            'suppressMovable': True,
            'wrapText': True,
            'minWidth': 70,
            'editable': edit_state,
            'cellStyle': cell_style,
            'headerTooltip': col_detail,
            'tooltipField':prj_number + ';edited_info;' +str(pe)+ str(field),#山口　フェーズ要素くっつけた 11/6
            # 'tooltipComponent': test,
            'headerClass': header_coler,
            'tooltipShowDelay': 0
        }
         )
        go_scene.append({#山口　ステータスも外に出したいという追加要望10/28
            'field': prj_number + ';state_name;' +str(pe)+ str(field),#山口　フェーズ要素くっつけた 11/6
            'headerName': 'ステータス',#山口　れつめいかえた
            'suppressMovable': True,
            'wrapText': True,
            'minWidth': 130,
            'editable':edit_state,
            "cellEditor":'agSelectCellEditor',
            "cellEditorParams":{
                "values": ['0.机上設計値(フィジカルデータ無し)', '1.設計値(一部フィジカルデータ含む机上検討値)', '2.設計値(フィジカルデータ)', "3.スペック", '4.名称', '5.対象外', ' ']# 山口　設定書き換え 3/27書き換え
            },
            'cellStyle': cell_style,
            'headerTooltip': col_detail,
            'tooltipField':prj_number + ';edited_info;' +str(pe)+ str(field),#山口　フェーズ要素くっつけた 11/6
            # 'tooltipComponent': test,
            'headerClass': header_coler,
            'tooltipShowDelay': 0,
            'hide': True
        }
         )
        go_scene.append({ #山口　メモ列の追加 10/30
            'field': prj_number + ';user_memo;' +str(pe)+ str(field),#山口　フェーズ要素くっつけた 11/6
            'headerName': 'メモ',
            'suppressMovable': True,
            'wrapText': True,
            'minWidth': 100,
            'editable': edit_state,
            'cellStyle': cell_style,
            'headerTooltip': col_detail,
            'tooltipField':prj_number + ';edited_info;' +str(pe)+ str(field),#山口　フェーズ要素くっつけた 11/6
            # 'tooltipComponent': test,
            'headerClass': header_coler,
            'tooltipShowDelay': 0,
            'hide': True
        }
         )
        go_scene.append({
            'field': prj_number + ';z_note;' +str(pe)+ str(field),  #10/23 #課題リスト＃23番 山口　フェーズ情報足りていなかったため追加　11/7 各行へ担当者列を追加するため移動11/7
            'headerName': '担当者',
            'suppressMovable': True,
            'wrapText': True,
            'minWidth': 100,
            'editable': edit_state,
            'cellStyle': cell_style,        
            'headerTooltip': col_detail,
            'headerClass': header_coler,
            'tooltipShowDelay': 0,
            'hide': True
        })
        if st.session_state['compare_click'] is True: #Kyaw #CompareSE Upd #10/29 merge#3 merge#4
            go_scene.append({
                'field': prj_number + ';compared_result;' +str(pe)+ str(field),  
                'headerName': '比較結果',
                'suppressMovable': True,
                'wrapText': True,
                'minWidth': 100,
                'maxWidth':130,
                'editable': edit_state,
                'cellStyle': cell_style,        
                'headerTooltip': col_detail,
                'headerClass': header_coler,
                'tooltipShowDelay': 0,
                # 'hide': True
            })
        _prj_number = prj_number
        _phase = phase
        #st.markdown(go)#山口デバック用

    # go['columnDefs'] += [{'headerName': prj['z_model_code'], 'headerClass': header_group_coler, 'children':go_prj }]
    # go_scene.append({　#山口　各行追加するため不要になった11/7
    #     'field': prj_number + ';z_note;' +pe+ field,#山口　フェーズ要素くっつけた 11/6
    #     'headerName': '担当者',
    #     'suppressMovable': True,
    #     'wrapText': True,
    #     'minWidth': 100,
    #     'editable': True,
    #     'cellStyle': BGcolorRenderer,        
    #     'headerTooltip': col_detail,
    #     'headerClass': header_coler,
    #     'tooltipShowDelay': 0
    # })

    # if len(prj_info_list)>1 and st.session_state['compare_click'] is True:
    #     prj_compare1 = prj_info_list.iloc[0]['z_prj_number']
    #     prj_compare2 = prj_info_list.iloc[1]['z_prj_number']
        
    #     fi1= prj_info_list.iloc[0]['z_wp_name_get_str']
    #     fi2 = prj_info_list.iloc[1]['z_wp_name_get_str']
    #     pi1 = prj_info_list.iloc[0]['z_class_name_get_str'][0] + prj_info_list.iloc[0]['z_class_name_get_str'][-1]
    #     pi2 = prj_info_list.iloc[1]['z_class_name_get_str'][0] + prj_info_list.iloc[1]['z_class_name_get_str'][-1]
    #     key1 = f'{prj_compare1};z_request_median;{pi1}{fi1}'
    #     key2 = f'{prj_compare2};z_request_median;{pi2}{fi2}'
    #     data_stuck_first = st.session_state.se_data_stuck[key1]
    #     data_stuck_second = st.session_state.se_data_stuck[key2]

    #     for k in range(len(data_stuck_first)):
    #         first_value = data_stuck_first.iloc[k]
    #         compare_value = data_stuck_second.iloc[k]
    #         # Compare values for cell styling
    #         if first_value != compare_value:
    #             st.session_state.se_data_stuck.loc[k, f'{prj_compare1};selected;{pi1}{fi1}'] = False
    #             st.session_state.se_data_stuck.loc[k, f'{prj_compare2};selected;{pi2}{fi2}'] = False
    #         else:
    #             st.session_state.se_data_stuck.loc[k, f'{prj_compare1};selected;{pi1}{fi1}'] = None
    #             st.session_state.se_data_stuck.loc[k, f'{prj_compare2};selected;{pi2}{fi2}'] = None

    #10/29 merge#3 merge#4
    if len(prj_info_list)>1 and st.session_state['compare_click'] is True:
        num_projects = len(prj_info_list)
        for k in range(len(st.session_state.se_data_stuck)):  # for each row
            for j in range(1, num_projects):
                prj_compare1 = prj_info_list.iloc[0]['z_prj_number']
                prj_compare2 = prj_info_list.iloc[j]['z_prj_number']
                fi1 = str(prj_info_list.iloc[0]['variation_id'])
                fi2 = str(prj_info_list.iloc[j]['variation_id'])
                pi1 = str(prj_info_list.iloc[0]['phase_id'])
                pi2 = str(prj_info_list.iloc[j]['phase_id'])
                key1 = f'{prj_compare1};z_request_median;{pi1}{fi1}'
                key2 = f'{prj_compare2};z_request_median;{pi2}{fi2}'
                data_stuck_first = st.session_state.se_data_stuck[key1]
                data_stuck_second = st.session_state.se_data_stuck[key2]

                first_value = data_stuck_first.iloc[k]
                compare_value = data_stuck_second.iloc[k]

                # ❶ Both not empty
                if (first_value is not None and first_value != '') and (compare_value is not None and compare_value != ''):
                    if first_value != compare_value:
                        st.session_state.se_data_stuck.loc[k, f'{prj_compare1};compared_result;{pi1}{fi1}'] = '！'
                        st.session_state.se_data_stuck.loc[k, f'{prj_compare2};compared_result;{pi2}{fi2}'] = '！'
                    else:
                        st.session_state.se_data_stuck.loc[k, f'{prj_compare2};compared_result;{pi2}{fi2}'] = ''

                # ❷ Both empty
                elif (first_value is None or first_value == '') and (compare_value is None or compare_value == ''):
                    st.session_state.se_data_stuck.loc[k, f'{prj_compare1};compared_result;{pi1}{fi1}'] = 'N/A'
                    st.session_state.se_data_stuck.loc[k, f'{prj_compare2};compared_result;{pi2}{fi2}'] = 'N/A'

                # ❸ prj1 not empty, prj2 empty
                elif (first_value is not None and first_value != '') and (compare_value is None or compare_value == ''):
                    # Only set prj2 to 比較不可, prj1 will be set after all comparisons
                    st.session_state.se_data_stuck.loc[k, f'{prj_compare2};compared_result;{pi2}{fi2}'] = 'N/A'

                # ❹ prj1 empty, prj2 not empty
                elif (first_value is None or first_value == '') and (compare_value is not None and compare_value != ''):
                    st.session_state.se_data_stuck.loc[k, f'{prj_compare1};compared_result;{pi1}{fi1}'] = 'N/A'
                    st.session_state.se_data_stuck.loc[k, f'{prj_compare2};compared_result;{pi2}{fi2}'] = 'N/A'

            # After all pairwise comparisons for this row, set prj1's compared_result for ❸
            prj_compare1 = prj_info_list.iloc[0]['z_prj_number']
            fi1 = str(prj_info_list.iloc[0]['variation_id'])
            pi1 = str(prj_info_list.iloc[0]['phase_id'])
            key1 = f'{prj_compare1};compared_result;{pi1}{fi1}'
            # Collect all compared_results for this row for prj1, except 比較不可 from empty comparisons
            results = []
            for j in range(1, num_projects):
                prj_compare2 = prj_info_list.iloc[j]['z_prj_number']
                fi2 = str(prj_info_list.iloc[j]['variation_id'])
                pi2 = str(prj_info_list.iloc[j]['phase_id'])
                key2 = f'{prj_compare2};compared_result;{pi2}{fi2}'
                val = st.session_state.se_data_stuck.loc[k, key2]
                if val != 'N/A':
                    results.append(val)
            # Decide prj1's compared_result
            if not results:
                # All were 比較不可
                st.session_state.se_data_stuck.loc[k, key1] = 'N/A'
            elif any(r == '！' for r in results):
                st.session_state.se_data_stuck.loc[k, key1] = '！'
            elif all(r == '' for r in results):
                st.session_state.se_data_stuck.loc[k, key1] = ''
            else:
                # If there's a mix of 一致 and 不一致, treat as 不一致
                st.session_state.se_data_stuck.loc[k, key1] = '！'


    go_phase.append({
        'headerName': row['z_class_name_get_str'],
        'headerClass': header_group_coler,
        'children': go_scene
    })
    go_add = {'headerName': row['z_name'], 'headerClass': header_group_coler, 'children':go_phase } #チョー　11/06
    for k, v in PJLOTjoho.items():
        if k != 'z_name' and k != 'z_class_name_get_str': #チョー　11/06
            go_add = {
                'headerName': row[k],
                'headerClass': header_group_coler,
                'children': [go_add]
            }
    go['columnDefs'].append(go_add)
    go['getDataPath'] = JsCode('''
                function(data) {
                    return data.params0p;
                }
                
            ''').js_code
    return go

def create_gridopsim(pages):#山口　sim用gridoption 12/2
    BGcolorRenderer=JsCode("""
    function (params) {
        if (params.data === undefined) {
            return {
                'background-color': '#C0C0C0',
                'wordBreak':'normal',
                'whiteSpace':'pre-line'
            };
        } else if (params.value === null) {
            return {
                'background-color': '#EFEFEF',
                'wordBreak':'normal',
                'whiteSpace':'pre-line'
            };                           
        } 
        return null;
    }
    """)#山口加筆
    ChangeHighlight = JsCode(
        """
    function(e) {
        let api = e.api;
        let rowIndex = e.rowIndex;
        let col = e.column.colId;
        
        console.log(e);
        let rowNode = api.getDisplayedRowAtIndex(rowIndex);
        api.flashCells({
          rowNodes: [rowNode],
          columns: [col],
          flashDelay: 10000000000
        });

    };
    """
    )

    edit_state = st.session_state.button_edit_state
    PJLOTjoho = {"variation":"バリエーション", "lot":"フェーズ","phase":"ロット","drivetrain":"駆動方式", "destination":"仕向け", "project_code":"プロジェクト",} #チョー　11/06 山口 ロットとフェーズの順番を入れ替えた　11/7

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
            'headerName': 'パラメータ名',
            'pinned': 'left',
            'width': 350,
            'wrapText': True,
            'headerClass': 'title_green'
        },
        'columnDefs': [],
        'treeData': True,
        'pagination': True,
        'groupDefaultExpanded': -1,
        'rowSelection': 'multiple',
        'suppressRowClickSelection': True,
        'groupSelectsChildren': True,
        'enableRangeSelection':True,
        'enableBrowserTooltips':True,#山口
        'onCellValueChanged':ChangeHighlight,#山口 11/4 値が変わったセルのハイライト
        'suppressMultiRangeSelection':True,
        # 'domLayout':'autoHeight',
        'sideBar': {
            'toolPanels': [
            {
                'id': 'columns',
                'labelDefault': 'Columns',
                'labelKey': 'columns',
                'iconKey': 'columns',
                'toolPanel': 'agColumnsToolPanel',
                'toolPanelParams': {
                'suppressRowGroups': True,
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
    }
    # 単位列のデフォルトオプション
    sim_prj_info_list = st.session_state.sim_prj_info_list
    prj = sim_prj_info_list.iloc[0]['project_id']
    sce = sim_prj_info_list.iloc[0]['variation']
    unit = sim_prj_info_list.iloc[0]['phase'][0] + sim_prj_info_list.iloc[0]['phase'][-1]
    study = sim_prj_info_list.iloc[0]['study_id']
    go_add = {
        'field': str(prj)+';parameter_unit;'+unit+sce+study, 'headerName': '単位',
        'pinned': 'left', 'filter': True, 'width': 110,
        'headerClass': 'title_green'
    }
    for v in PJLOTjoho.values():
        go_add = {
            'headerName': v,
            'headerClass': 'group_title_green',
            'children': [
                go_add
            ]
        }
    
    go['columnDefs'].append(go_add)
    # パラメータ値列のデフォルトオプション
    go_scene = []
    go_phase = []
    # go_add = {}
    _prj_number = ''
    _phase = ''
    # info_list_count = 0
    header_coler = 'green'
    header_group_coler = 'group_green'
    # prj = st.session_state.prj_info[info_list_count]
    # for prj_number, _, scene in val_scene:
    row_count = len(sim_prj_info_list)
    for i, row in sim_prj_info_list.iterrows(): 
        flag_hide_column = (row['overall_value'] is not None and (int(row['overall_value'])=='無効'))  #山口　検討に使用しないシナリオは1となっているため、非表示用のフラグを立てる　1/23 1と0を入れ替える2/3 有効or無効に切り替える2/9
        print('hide flag :' + str(flag_hide_column) + 'overall_value' + str(row['overall_value']))
        # プロジェクトが切り替わったら、前回までのシーンをGridOptionへ追加
        prj_number = row['project_id']
        study = row['study_id']
        field = row['variation']
        pe = row['phase'][0] + row['phase'][-1]#山口 列名にくっつけたふぇーずようそ11/6
        phase = row['phase']
        #st.markdown(prj_number + scene + field)#山口デバック用
        col_detail = "ロット:" + row['lot'] + " フェーズ:" + row['phase'] #チョー　11/01　フェーズと車種→ロットとフェーズ
        
   
        
        
        if prj_number != _prj_number or i == row_count:# and _prj_number != '':山口編集、実行条件に最終行であることを追加
            #st.markdown("first if passed")
            #col_detail = ''#山口　用途不明のためコメントアウト
            # for k, v in reversed(tooltip_joho.items()):
            #     col_detail += str(v) + ':' + str(prj[k]) + '    '
            if _prj_number != '':
                #st.markdown("second if passed")
                go_phase.append({
                    'headerName': _row['variation'],
                    'headerClass': header_group_coler,
                    'children': go_scene
                })
                go_add = {'headerName': _row['phase'], 'headerClass': header_group_coler, 'children':go_phase } #チョー　11/06
                for k, v in PJLOTjoho.items():
                    if k!= 'variation' and k != 'phase': #チョー　11/06
                        #st.markdown("third if passed")
                        go_add = {
                            'headerName': _row[k],
                            'headerClass': header_group_coler,
                            'children': [go_add]
                        }
                go['columnDefs'].append(go_add)
                # info_list_count =+ 1
                # prj = st.session_state.prj_info[info_list_count]
                go_scene = []
                go_phase = []
                go_add = {}
                if header_coler == 'darkgreen':
                    #st.markdown("forth if passed")
                    header_coler = 'green'
                    header_group_coler = 'group_green'
                elif header_coler == 'green':
                    header_coler = 'darkgreen'
                    header_group_coler = 'group_darkgreen'
        

        _row = row#山口編集　Prj変わったタイミングで前の行のPrj情報を参照するためストックしておく
        
        _pe = pe
        if prj_number == _prj_number and phase != _phase:
            #flag_hide_column = 
            go_phase.append({
                'headerName': _phase,
                'headerClass': header_group_coler,
                'children': go_scene,

            })
            go_scene = []
            
             #SEオリジナル情報乗っけるべきはここ
        if i == 0 or prj_number != _prj_number or phase != _phase or field != _field:
            go_scene.append({ 
            'field': str(prj_number) + ';original_value;' +pe+ field+study,#山口　フェーズ要素くっつけた 11/6
            'headerName': 'SEリストの値',
            'suppressMovable': True,
            'wrapText': True,
            'minWidth': 130,
            
            'editable': False,
            'cellStyle': BGcolorRenderer,
            'headerTooltip': col_detail,
            'tooltipField':str(prj_number) + ';edited_info;' +pe+ field+study,#山口　フェーズ要素くっつけた 11/6
            # 'tooltipComponent': test,
            'headerClass': header_coler,
            'tooltipShowDelay': 0
            }
             )
            go_scene.append({ 
            'field': str(prj_number) + ';target_value;' +pe+ field+study,# 山口　目標値情報も載せたいので列追加
            'headerName': 'Rリスト目標値',
            'suppressMovable': True,
            'wrapText': True,
            'minWidth': 130,
            
            'editable': False,
            'cellStyle': BGcolorRenderer,
            'headerTooltip': col_detail,
            'tooltipField':str(prj_number) + ';edited_info;' +pe+ field+study,#山口　フェーズ要素くっつけた 11/6
            # 'tooltipComponent': test,
            'headerClass': header_coler,
            'tooltipShowDelay': 0
            })
             
        
        go_scene.append({ #山口　選択列の追加 10/25
            'field': str(prj_number) + ';selected;' +pe+ field+study,#山口　フェーズ要素くっつけた 11/6
            'headerName': '編集',
            'suppressMovable': True,
            'wrapText': True,
            'minWidth': 40,
            'maxWidth': 40,
            'editable': True,
            'cellStyle': BGcolorRenderer,
            'headerTooltip': col_detail,
            'tooltipField':str(prj_number) + ';edited_info;' +pe+ field+study,#山口　フェーズ要素くっつけた 11/6
            # 'tooltipComponent': test,
            'headerClass': header_coler,
            'tooltipShowDelay': 0,
            'hide' : flag_hide_column| (pages =='初期仕様')
        }
         )
                      
        go_scene.append({
            'field': str(prj_number) + ';value;' +pe+ field+study,#山口　フェーズ要素くっつけた 11/6
            'headerName': study,
            'suppressMovable': True,
            'wrapText': True,
            'minWidth': 130,
            'editable': edit_state,
            'cellStyle': BGcolorRenderer,
            'headerTooltip': col_detail,
            'tooltipField':str(prj_number) + ';edited_info;' +pe+ field+study,#山口　フェーズ要素くっつけた 11/6
            # 'tooltipComponent': test,
            'headerClass': header_coler,
            'tooltipShowDelay': 0,
            'hide' : flag_hide_column| (pages =='初期仕様')
        }
         )
        
        go_scene.append({ #山口　メモ列の追加 10/30
            'field': str(prj_number) + ';user_memo;' +pe+ field+study,#山口　フェーズ要素くっつけた 11/6
            'headerName': 'メモ',
            'suppressMovable': True,
            'wrapText': True,
            'minWidth': 130,	
            'editable': True,
            'cellStyle': BGcolorRenderer,
            'headerTooltip': col_detail,
            'tooltipField':str(prj_number) + ';edited_info;' +pe+ field+study,#山口　フェーズ要素くっつけた 11/6
            # 'tooltipComponent': test,
            'headerClass': header_coler,
            'tooltipShowDelay': 0,
            'hide' : True
        }
         )
        
        _prj_number = prj_number
        _phase = phase
        _field = field
        #st.markdown(go)#山口デバック用

    # go['columnDefs'] += [{'headerName': prj['z_model_code'], 'headerClass': header_group_coler, 'children':go_prj }]
    # go_scene.append({　#山口　各行追加するため不要になった11/7
    #     'field': prj_number + ';z_note;' +pe+ field,#山口　フェーズ要素くっつけた 11/6
    #     'headerName': '担当者',
    #     'suppressMovable': True,
    #     'wrapText': True,
    #     'minWidth': 100,
    #     'editable': True,
    #     'cellStyle': BGcolorRenderer,        
    #     'headerTooltip': col_detail,
    #     'headerClass': header_coler,
    #     'tooltipShowDelay': 0
    # })
    go_phase.append({
        'headerName': row['variation'],
        'headerClass': header_group_coler,
        'children': go_scene
    })
    go_add = {'headerName': row['phase'], 'headerClass': header_group_coler, 'children':go_phase } #チョー　11/06
    for k, v in PJLOTjoho.items():
        if k != 'variation' and k != 'phase': #チョー　11/06
            go_add = {
                'headerName': row[k],
                'headerClass': header_group_coler,
                'children': [go_add]
            }
    go['columnDefs'].append(go_add)
    go['getDataPath'] = JsCode('''
                function(data) {
                    return data.params0p;
                }
                
            ''').js_code
    return go

# #チョー　01/08　Rリスト処理追加  
# def create_gridop_rlist():
#     #チョー　#11/25
#     BGcolorRenderer=JsCode("""
#     function (params) {
#         if (params.data === undefined) {
#             return {
#                 'background-color': '#C0C0C0',
#                 'wordBreak':'normal',
#                 'whiteSpace':'pre-line'
#             };
#         } else if (params.value === null) {
#             return {
#                 'background-color': '#EFEFEF',
#                 'wordBreak':'normal',
#                 'whiteSpace':'pre-line'
#             };                           
#         } 
#         return null;
#     }
#     """)
#     ChangeHighlight = JsCode(
#         """
#     function(e) {
#         let api = e.api;
#         let rowIndex = e.rowIndex;
#         let col = e.column.colId;
        
#         console.log(e);
#         let rowNode = api.getDisplayedRowAtIndex(rowIndex);
#         api.flashCells({
#           rowNodes: [rowNode],
#           columns: [col],
#           flashDelay: 10000000000
#         });

#     };
#     """
#     )


#     edit_state = st.session_state.button_edit_state

#     go = {
#         'defaultColDef': {
#             'flex':1,
#             'resizable': True,
#             'wrapHeaderText': True,
#             'suppressMovable': True,
#             'allowDragFromColumnsToolPanel': True,
#             'filter': True,
#         },

#         'columnDefs': [],
#         'treeData': False,
#         'pagination': True,
#         'groupDefaultExpanded': -1,
#         'rowSelection': 'multiple',
#         'suppressRowClickSelection': True,
#         'groupSelectsChildren': True,
#         'enableRangeSelection':True,
#         'enableBrowserTooltips':True,
#         'onCellValueChanged':ChangeHighlight,
#         'suppressMultiRangeSelection':True,
#         'alwaysShowHorizontalScroll': True,  # Ensure horizontal scroll bar is always visible
#         # 'domLayout':'autoHeight',
#         'sideBar': {
#             'toolPanels': [
#             {
#                 'id': 'columns',
#                 'labelDefault': 'Columns',
#                 'labelKey': 'columns',
#                 'iconKey': 'columns',
#                 'toolPanel': 'agColumnsToolPanel',
#                 'toolPanelParams': {
#                 # 'suppressRowGroups': True,
#                 'suppressValues': True,
#                 'suppressPivots': True,
#                 'suppressPivotMode': True,
#                 'suppressColumnFilter': True,
#                 'suppressColumnSelectAll': True,
#                 'suppressColumnExpandAll': True,
#                 },
#             },
#             ],
#         },
#     }

#     rList_info = {
#         "design_item_1": "設計項目",
#         "design_item_2": "設計項目",
#         "design_item_3": "目標性能",
#         "target": "target",
#         "spec_to_study": "車両仕様",
#         "r_unit": "Unit",
#     }
#     # # # 単位列のデフォルトオプション
#     r_prj_info_list = st.session_state.r_prj_info_list
      

#     # print('r stuck:', st.session_state.rlist_data_stuck[['performance', 'employee_number','parameter_name']].head())
  
    
#     go_add = []

#     # Add date column separately
#     performance_column = {
#         'headerName': '性能',
#         'field': 'performance',
#         'filter': True,
#         'headerClass': 'title_green',
#         'minWidth':100,
#     }

#     go_add.append(performance_column)

#     # Group for Performance and related columns
#     performance_group = {
#         'headerName': '担当',
#         'headerClass': 'group_title_green',
#         'children': [
#             {
#                 'headerName': '部署',
#                 'field': 'section_code',
#                 'filter': True,
#                 'headerClass': 'title_green',
#                 'minWidth':100,
#             },
#             {
#                 'headerName': '担当',
#                 'field': 'employee_name',
#                 'filter': True,
#                 'headerClass': 'title_green',
#                 'minWidth':100,
#             },
#             {
#                 'headerName': 'ステータス',
#                 'field': 'status',
#                 'filter': True,
#                 'headerClass': 'title_green',
#                 'minWidth':100,
#                 'editable':False,
#                 "cellEditor":'agSelectCellEditor',
#                 "cellEditorParams":{
#                     "values": ['1.項目検討中', '2.設定完了']#設定書き換え
#                 },
#             },
#             {
#                 'headerName': '入力日',
#                 'field': 'date',
#                 'filter': True,
#                 'headerClass': 'title_green',
#                 'minWidth':100,
#                 # 'editable':True,
#             }
#         ]
#     }

#     # Add the performance group to go_add
#     go_add.append(performance_group)

#     # Add remaining columns
#     for key, value in rList_info.items():
#         # Skip columns already added
#         if key in ['design_item_1', 'design_item_2']:
#             design_item_group = {
#                 'headerName': value,
#                 'field': key,
#                 'filter': True,
#                 'headerClass': 'title_green',
#                 'minWidth':100,
#             }
#             # Add the design item group to go_add
#             go_add.append(design_item_group)
#             continue
#         if key in ['design_item_3']:
#             design_item_group3 = {
#                 'headerName': '目標性能',
#                 'headerClass': 'group_title_green',
#                 'children': [
#                     {
#                         'headerName': '(Requitrement)',
#                         'field': key,
#                         'filter': True,
#                         'headerClass': 'title_green',
#                         'minWidth':100,
#                     }
#                 ]
#             }
#             # Add the design item group to go_add
#             go_add.append(design_item_group3)
#             continue
#         column_definition = {
#             'headerName': value,
#             'field': key,
#             'filter': True,
#             'headerClass': 'title_green',
#             'minWidth':100,
#         }
#         go_add.append(column_definition)

#     # st.write('para ee: ', len(st.session_state.rlist_data_stuck))

#     # itemLen = len(r_prj_info_list['parameter_name'])
#     # # st.write('itemlen: ', itemLen)
#     # listt = list(set(r_prj_info_list['parameter_name']))
#     seen = set()
#     unique_list = []
#     for item in r_prj_info_list['parameter_name']:
#         if item not in seen:
#             unique_list.append(item)
#             seen.add(item)
#     # st.write('list : ', unique_list)
#     # key = 0
#     for key in range(len(unique_list)):
#         value = unique_list[key]
#         parameter_columns = {
#             'headerName': r_prj_info_list.iloc[key]['parameter_name'],
#             'headerClass': 'group_title_green',
#             'children': [
#                 {
#                     'headerName': r_prj_info_list.iloc[key]['usecase_unit'],
#                     'field': r_prj_info_list.iloc[key]['parameter_name'],
#                     'filter': True,
#                     'headerClass': 'title_green',
#                     'minWidth':100,
#                 }
#             ]
#         }
#         go_add.append(parameter_columns)

#     rList_info2 = {
#         "priority": "優先度",
#         "detail_and_output": "検討内容と必要なOutput",
#         "tool": "必要なOutputの計算方法(ツール)",
#         "responsible": "必要なOutputの責任者",
#         "period": "期日",
#     }

#     for key, value in rList_info2.items():
#         if key in ['responsible']:
#             responsible_group = {
#                 'headerName': value,
#                 'headerClass': 'group_title_green',
#                 'children': [
#                     {
#                         'headerName': '責任者/実行者',
#                         'field': key,
#                         'filter': True,
#                         'headerClass': 'title_green',
#                         'minWidth':100,
#                     }
#                 ]
#             }
#             # Add the design item group to go_add
#             go_add.append(responsible_group)
#             continue
#         column_definition2 = {
#             'headerName': value,
#             'field': key,
#             'filter': True,
#             'headerClass': 'title_green',
#             'minWidth':100,
#         }
#         go_add.append(column_definition2)
    
#     go['columnDefs'].extend(go_add)
#     go['getDataPath'] = JsCode('''
#                 function(data) {
#                     return data.params0p;
#                 }
                
#             ''').js_code
#     return go


#チョー　01/08　Rリスト処理追加　01/30Grid表示変更
def create_gridop_rlist():
    #チョー　#11/25
    BGcolorRenderer=JsCode("""
    function (params) {
        if (params.data === undefined) {
            return {
                'background-color': '#C0C0C0',
                'wordBreak':'normal',
                'whiteSpace':'pre-line'
            };
        } else if (params.value === null) {
            return {
                'background-color': '#EFEFEF',
                'wordBreak':'normal',
                'whiteSpace':'pre-line'
            };                           
        } 
        return null;
    }
    """)
    # Function that used in create_gridop_rlist to determine row style based on the judge column value 3/23
    style_by_judge = JsCode("""
    function(params) {
        console.log(params);
        
        if (params.data != undefined) {
            const judgeColumn = Object.keys(params.data).find(key => key.includes(';judge;'));
            if (judgeColumn) {
                const judgeValue = params.data[judgeColumn];
                console.log(judgeValue);
                if (judgeValue === 'NG') {
                    return { backgroundColor: 'lightcoral' };  // Red for NG
                }
            }
        }
        return {'background-color': '#ffffcc'};  // Default style
    }
    """)
    ChangeHighlight = JsCode(
        """
    function(e) {
        let api = e.api;
        let rowIndex = e.rowIndex;
        let col = e.column.colId;
        console.log(e);
        let rowNode = api.getDisplayedRowAtIndex(rowIndex);
        api.flashCells({
          rowNodes: [rowNode],
          columns: [col],
          flashDelay: 10000000000
        });
        
        let rowData = rowNode.data;
        if (col.includes('auto_judge_type')) {
        let target = rowData[col.replace('auto_judge_type', 'target')];
        let design = rowData[col.replace('auto_judge_type', 'design')];
        console.log(target, design);
        let newValue = e.newValue;
        let result = "";
        if (target !== undefined && design !== undefined) {
            target = parseFloat(target);
            design = parseFloat(design);
            if (!isNaN(target) && !isNaN(design)) {
                if (newValue === "未定") {
                    result = "";
                } else if (newValue === "以上") {
                    if (design >= target) {
                        result = "OK"
                    } else {
                        result = "NG"
                    }
                } else if (newValue === "以下") {
                    if (design <= target) {
                        result = "OK"
                    } else {
                        result = "NG"
                    }
                } else if (newValue === "同等") {
                    if (design === target) {
                        result = "OK"
                    } else {
                        result = "NG"
                    }
                }
            }
        }
        let auto_judge_result_id = col.replace('auto_judge_type', 'auto_judge_result');
        api.applyTransaction({ update: [{ ...rowData, [auto_judge_result_id]: result }] });
        api.flashCells({
          rowNodes: [rowNode],
          columns: [auto_judge_result_id],
          flashDelay: 10000000000
        });
    }
    };
    """
    )


    edit_state = st.session_state.button_edit_state

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
        'enableRangeSelection':True,
        'enableBrowserTooltips':True,
        'enableCharts':True,
        'onCellValueChanged':ChangeHighlight,
        'suppressMultiRangeSelection':True,
        'alwaysShowHorizontalScroll': True,  # Ensure horizontal scroll bar is always visible
        # 'domLayout':'autoHeight',
        'sideBar': {
            'toolPanels': [
            {
                'id': 'columns',
                'labelDefault': 'Columns',
                'labelKey': 'columns',
                'iconKey': 'columns',
                'toolPanel': 'agColumnsToolPanel',
                'toolPanelParams': {
                # 'suppressRowGroups': True,
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
    }

    rList_info = {
        "design_item_1": "設計項目（大）",
        "design_item_2": "設計項目（小）",
        "design_item_3": "目標性能",
        "r_unit": "Unit", #山口　単位の順番変えた 4/16
        "target": "target",
        "spec_to_study": "車両仕様",

    }
    # # # 単位列のデフォルトオプション
    r_prj_info_list = st.session_state.r_prj_info_list
    df_selects = st.session_state.df_selects
    # st.write('df_select: ', df_selects)

    # print('r stuck:', st.session_state.rlist_data_stuck[['performance', 'employee_number','parameter_name']].head())
  
    
    go_add = []


    #山口　性能もグループ化1/31
    # Add date column separately
    performance_column = {
        'headerName': '性能',
        'field': 'performance',
        'filter': True,
        'rowGroup' : True,
        'hide' : True,
        'headerClass': 'title_white', #チョー　01/30　色変更
    }
        #山口　flag_primaryによる主要性能のグループ化を行う 1/27
    primary_column = {
        'headerName':'主要性能',
        'field': 'flag_primary',
        'headerClass': 'title_white', #チョー　01/30　色変更
        'rowGroup' : True,
        'hide' : True
    }
    

    go_add.append(performance_column)
    go_add.append(primary_column)
    for index, row in df_selects.iterrows():
        project_id = row['project_id']
        phase_id = row['phase_id']
        variation_id = row['variation_id']
        drivetrain = row['drivetrain']
        phase = row['phase']
        variation = row['variation']
        
        #チョー　01/30　「担当」項目をGroupingする
        performance_group = {
            'headerName': '担当_'+ drivetrain +'_'+phase+'_'+variation,
            'headerClass': 'group_title_cyan', #チョー　01/30　色変更
            'hide':True, #山口　Rリストの初期表示列を絞る 1/27
            'children': [
                { 
                    'headerName': '部署',
                    'field': str(project_id) + ';section_code;' + str(phase_id) + str(variation_id),
                    'cellStyle': {'background-color': '#CCFFFF'}, #チョー　01/30　色変更
                    'filter': True,
                    'hide':True, #山口　Rリストの初期表示列を絞る 1/27
                    'headerClass': 'title_cyan', #チョー　01/30　色変更
                    'minWidth':100,
                },
                { 
                    'headerName': '担当',
                    'field': str(project_id) + ';employee_name;' + str(phase_id) + str(variation_id),
                    'cellStyle': {'background-color': '#CCFFFF'}, #チョー　01/30　色変更
                    'filter': True,
                    'hide':True, #山口　Rリストの初期表示列を絞る 1/27
                    'headerClass': 'title_cyan', #チョー　01/30　色変更
                    'minWidth':100,
                },
                { 
                    'headerName': 'ステータス',
                    'field': str(project_id) + ';status;' + str(phase_id) + str(variation_id),
                    'cellStyle': {'background-color': '#CCFFFF'}, #チョー　01/30　色変更
                    'filter': True,
                    'hide':True, #山口　Rリストの初期表示列を絞る 1/27
                    'headerClass': 'title_cyan', #チョー　01/30　色変更
                    'minWidth':100,
                    'editable':True,
                    "cellEditor":'agSelectCellEditor',
                    "cellEditorParams":{
                        "values": ['1.項目検討中', '2.設定完了','']#設定書き換え
                    },
                },
                { 
                    'headerName': '入力日',
                    'field': str(project_id) + ';date;' + str(phase_id) + str(variation_id),
                    'cellStyle': {'background-color': '#CCFFFF'}, #チョー　01/30　色変更
                    'filter': True,
                    'hide':True, #山口　Rリストの初期表示列を絞る 1/27
                    'headerClass': 'title_cyan', #チョー　01/30　色変更
                    'minWidth':100,
                    # 'editable':True,
                }
            ]
        }

        #チョー　01/30　Groupingした「担当」を追加する
        go_add.append(performance_group)

    design_items = []

    for key, value in rList_info.items():
        if key in ['design_item_1', 'design_item_2']:
            design_item_group = {
                    'headerName': value,
                    'field': key,
                    'filter': True,
                    'headerClass': 'title_white', #チョー　01/30　色変更
                    'minWidth':100,
            }
            design_items.append(design_item_group)
            continue

        
        if key in ['design_item_3']:
            #チョー　01/30 「'設計項目（大）', '設計項目（小）'」をGroupingする
            design_item_gp = {
                        'headerName': '設計項目',
                        'headerClass': 'group_title_white',  #チョー　01/30　色変更
                        'children': design_items
                    }
             #チョー　01/30　Groupingした「'設計項目（大）', '設計項目（小）'」を追加する
            go_add.append(design_item_gp)

            design_item_group3 = {
                'headerName': '目標性能',
                'headerClass': 'group_title_white',  #チョー　01/30　色変更
                'children': [
                    {
                        'headerName': '(Requitrement)',
                        'field': key,
                        'filter': True,
                        # 'cellStyle': {'background-color': '#FFFFCC'}, #チョー　01/30　色変更
                        'headerClass': 'title_white', #チョー　01/30　色変更
                        'minWidth':50,
                    }
                ]
            }
            #チョー　01/30 「目標性能」を追加する
            go_add.append(design_item_group3)
            continue
        #山口　単位情報を左に持ってきたいという要望　4/16
        if key in ['r_unit']:
            design_item_unit = {
                    'headerName': value,
                    'field': key,
                    'filter': True,
                    'headerClass': 'title_white', #チョー　01/30　色変更
                    'minWidth':50,
            }
            go_add.append(design_item_unit)
            continue
        if key in ['target']: #ターゲット列を複数表示できるように

            targets = []
            for index, row in df_selects.iterrows():
                #チョー 05/07 Index：row[0]をHeader名：row['project_id']に変更する
                project_id=row['project_id']
                phase_id=row['phase_id']
                variation_id=row['variation_id']
                drivetrain = row['drivetrain']
                phase = row['phase']
                variation = row['variation']
                target_selected = {
                            'headerName': '編集',
                            'field': str(project_id) + ';target_selected;' + str(phase_id) + str(variation_id),
                            'filter': True,
                            'cellStyle': {'background-color': '#FFFFCC'},  #チョー　01/30　色変更
                            'headerClass': 'title_yellow',  #チョー　01/30　色変更
                            'editable':True, #山口　編集可能に 1/29
                            'minWidth':40,
                            'maxWidth':40
                        }
                target = {
                            'headerName': 'target', #チョー　02/10　文字変更
                            'field': str(project_id) + ';target;' + str(phase_id) + str(variation_id),
                            'filter': True,
                            'cellStyle': {'background-color': '#FFFFCC'},  #チョー　01/30　色変更
                            'headerClass': 'title_yellow',  #チョー　01/30　色変更
                            'editable':True, #山口　編集可能に 1/29
                            'minWidth':50,
                        }
                adjusted_target = { # 山口　妥協地表示 8/1
                            'headerName': '妥協値',
                            'field': str(project_id) + ';adjusted_target;' + str(phase_id) + str(variation_id),
                            'filter': True,
                            'cellStyle': {'background-color': '#FFFFCC'},  
                            'headerClass': 'title_yellow', 
                            'editable':True, 
                            'minWidth':50,
                        }
                auto_judge_type = {
                            'headerName': '条件',
                            'field': str(project_id) + ';auto_judge_type;' + str(phase_id) + str(variation_id),
                            'filter': True,
                            'cellStyle': {'background-color': '#FFFFCC'},  #チョー　01/30　色変更
                            'headerClass': 'title_yellow',  #チョー　01/30　色変更
                            'editable':True, #山口　編集可能に 1/29
                            'cellEditor': 'agSelectCellEditor',
                            'cellEditorParams': {
                                'values': ["未定", "以上", "以下", "同等"]
                            },
                            'minWidth': 50,
                            'maxWidth': 80
                        }
                spec_to_study = {
                            'headerName': '車両仕様',
                            'field': str(project_id) + ';spec_to_study;' + str(phase_id) + str(variation_id),
                            'filter': True,
                            'hide': True,
                            'cellStyle': {'background-color': '#FFFFCC'},  #チョー　01/30　色変更
                            'headerClass': 'title_yellow',  #チョー　01/30　色変更
                            'minWidth':50,
                        }
                # memo_col = {
                #             'headerName': '考え方',
                #             'field': str(project_id) + ';note;' + str(phase_id) + str(variation_id),
                #             'filter': True,
                #             # 'hide': True,
                #             'cellStyle': {'background-color': '#FFFFCC'},  #チョー　01/30　色変更
                #             'headerClass': 'title_yellow',  #チョー　01/30　色変更
                #             'minWidth':100,
                #         }
                
                #02/12 チョー　リンクで表示する
                memo_col = {
                            'headerName': '考え方',
                            'field': str(project_id) + ';note;' + str(phase_id) + str(variation_id),
                            'filter': True,
                            'cellStyle': {'background-color': '#FFFFCC'},  # Background color change (yellow)
                            'headerClass': 'title_yellow',  # Header color change (yellow)
                            'minWidth': 100,
                            'editable': True,
                            'cellRenderer': JsCode("""
                                class MemoCellRenderer {
                                init(params) {
                                    this.eGui = document.createElement('a');
                                    var value = params.value;
                                    if (value) {
                                        // Ensure the URL has the correct protocol
                                        this.eGui.setAttribute('href', value.startsWith('http') ? value : 'https://' + value);
                                        this.eGui.setAttribute('target', '_blank');
                                        this.eGui.innerText = value; // Display the URL as the link text
                                        this.eGui.setAttribute('style', 'color:blue; text-decoration:underline;');
                                    } else {
                                        this.eGui.innerText = ''; // Handle null or empty values
                                    }
                                }
                                getGui() {
                                    return this.eGui;
                                }
                                }
                            """),
                        }
                design = {
                            'headerName': '設計値',
                            'field': str(project_id) + ';design;' + str(phase_id) + str(variation_id),
                            'filter': True,
                            'cellStyle': {'background-color': '#FFFFCC'},  #チョー　01/30　色変更
                            'headerClass': 'title_yellow',  #チョー　01/30　色変更
                            'editable':True, #山口　編集可能に 1/29
                            'minWidth':50,
                        }
                auto_judge_result = {
                            'headerName': '自動判定',#山口　列名変更4/17
                            'field': str(project_id) + ';auto_judge_result;' + str(phase_id) + str(variation_id),
                            'filter': True,
                            #'cellStyle': {'background-color': '#FFFFCC'},  #チョー　01/30　色変更
                            'headerClass': 'title_white',  #チョー　01/30　色変更 山口　ここは白らしい4/17
                            'editable':False, #山口　編集可能に 1/29
                            'minWidth': 50,
                            'maxWidth': 80
                        }

                judge = {
                            'headerName': '判断',
                            'field': str(project_id) + ';judge;' + str(phase_id) + str(variation_id),
                            'filter': True,
                            'cellStyle': style_by_judge, # 
                            'headerClass': 'title_yellow',  #チョー　01/30　色変更
                            'editable':True, #山口　編集可能に 1/29
                            'minWidth':100,
                        }
                judge_evidence = { #山口　判断資料リンク格納場所を作る 3/24
                            'headerName': '判断エビデンス資料',
                            'field': str(project_id) + ';judge_evidence;' + str(phase_id) + str(variation_id),
                            'filter': True,
                            'headerClass': 'title_yellow',  #チョー　01/30　色変更
                            'cellStyle':style_by_judge,  #チョー　01/30　色変更
                            'cellRenderer': JsCode("""
                                class MemoCellRenderer {
                                init(params) {
                                    this.eGui = document.createElement('a');
                                    var value = params.value;
                                    if (value) {
                                        // Ensure the URL has the correct protocol
                                        this.eGui.setAttribute('href', value.startsWith('http') ? value : 'https://' + value);
                                        this.eGui.setAttribute('target', '_blank');
                                        this.eGui.innerText = value; // Display the URL as the link text
                                        this.eGui.setAttribute('style', 'color:blue; text-decoration:underline;');
                                    } else {
                                        this.eGui.innerText = ''; // Handle null or empty values
                                    }
                                }
                                getGui() {
                                    return this.eGui;
                                }
                                }"""),
 
                            'editable':True, #山口　編集可能に 1/29
                            'minWidth':100,
                        }
                manager_approval = { #山口 主管承認用の列を用意する3/22
                            'headerName': '主管承認',
                            'field': str(project_id) + ';manager_approval;' + str(phase_id) + str(variation_id),
                            'filter': True,
                            'cellStyle': {'background-color': '#FFFFCC'},  
                            'headerClass': 'title_yellow',  
                            'editable':True, 
                            'minWidth':50,                           
                }
                manager_approval_comment = { #山口　主管承認時コメントようの列を用意する
                            'headerName': '主管承認コメント',
                            'field': str(project_id) + ';manager_approval_comment;' + str(phase_id) + str(variation_id),
                            'filter': True,
                            'cellStyle': {'background-color': '#FFFFCC'},  
                            'headerClass': 'title_yellow',  
                            'editable':True, 
                            'minWidth':100,                           
                }               
                targets.append(target_selected)
                targets.append(target) #チョー　01/30 「target」を追加する
                targets.append(adjusted_target) # 山口　妥協地追加 8/1
                targets.append(auto_judge_type)
                targets.append(spec_to_study) #チョー　01/30 「車両仕様」を追加する
                targets.append(memo_col) #チョー　02/07
                targets.append(design)
                targets.append(auto_judge_result)
                targets.append(judge)
                targets.append(judge_evidence)
                targets.append(manager_approval)
                targets.append(manager_approval_comment)
                target_group = {
                    'headerName': drivetrain +'_'+phase+'_'+variation,
                    'headerClass': 'group_title_yellow', #チョー　01/30　色変更
                    'children': targets
                }
                go_add.append(target_group) #チョー　01/30 「'target', '車両仕様'」をGroupingする
                targets = []
                continue
        # if key != 'target' and key != 'spec_to_study': #山口 もはやこの分はいらなくなる
        #     column_definition = {
        #         'headerName': value,
        #         'field': key,
        #         'filter': True,
        #         'headerClass': 'title_yellow', #チョー　01/30　色変更
        #         'cellStyle': {'background-color': '#FFFFCC'}, #チョー　01/30　色変更
        #         'minWidth':100,
        #     }
        #     go_add.append(column_definition)

    # st.write('para ee: ', len(st.session_state.rlist_data_stuck))

    # itemLen = len(r_prj_info_list['parameter_name'])
    # # st.write('itemlen: ', itemLen)
    # listt = list(set(r_prj_info_list['parameter_name']))
    #山口　時系列表示用のセレクトボックスをここに挿入　1/30
    timeseries_selected = {
            'headerName': '時系列選択',
            'field': 'timeseries_selected' ,
            'filter': True,
            'headerClass': 'title_white',
            'editable':True, #山口　編集可能に 1/29
            'minWidth':40,
            'maxWidth':40
        }
    go_add.append(timeseries_selected)
    seen = set()
    unique_list = []
    for item in r_prj_info_list['parameter_name']:
        if item not in seen and item is not None:
            unique_list.append(item)
            seen.add(item)
    # st.write('list : ', unique_list)
    group_list = []
    # key = 0
    for key in range(len(unique_list)):
        val = unique_list[key]
        
        if val != '走行パターン':
            # print('val: ', val)
            parameter_columns = {
                        'headerName': r_prj_info_list.iloc[key]['parameter_name'],
                        'headerClass': 'group_title_white', #チョー　01/30　色変更
                        'hide': True,
                        'children': [
                            {
                                'headerName': r_prj_info_list.iloc[key]['usecase_unit'],
                                'field': r_prj_info_list.iloc[key]['parameter_name'],
                                'filter': True,
                                'hide': True,
                                'headerClass': 'title_white', #チョー　01/30　色変更
                                'minWidth':100,
                            }
                        ]
                    }
            #チョー　01/30 「走行パターン」以外のユースケース項目を追加する
            group_list.append(parameter_columns)
        else:
            usecase_col = {
                'headerName': r_prj_info_list.iloc[key]['parameter_name'],
                'headerClass': 'group_title_white', #チョー　01/30　色変更
                'children': [
                    {
                        'headerName': r_prj_info_list.iloc[key]['usecase_unit'],
                        'field': r_prj_info_list.iloc[key]['parameter_name'],
                        'filter': True,
                        'headerClass': 'title_white', #チョー　01/30　色変更
                        'minWidth':100,
                    }
                ]
            }
            #チョー　01/30 ユースケース項目「走行パターン」を追加する
            go_add.append(usecase_col)

    #チョー　01/30 ユースケース項目をGroupingする
    group_list_header = {
        'headerName': 'ユースケース詳細項目',
        'headerClass': 'group_title_white', #チョー　01/30　色変更
        'hide':True, 
        'children': group_list
    }
    #チョー　01/30 ユースケース項目を追加する
    go_add.append(group_list_header)

    rList_info2 = {
        "priority": "優先度",
        "detail_and_output": "検討内容と必要なOutput",
        "tool": "必要なOutputの計算方法(ツール)",
        "responsible": "必要なOutputの責任者",
        "period": "期日",
        # 'note': 'メモ' #山口　note 列を表示させたかったので追加 1/27
    }
    project_item_gp = []
    for index, row in df_selects.iterrows():
        project_id = row['project_id']
        phase_id = row['phase_id']
        variation_id = row['variation_id']
        drivetrain = row['drivetrain']
        phase = row['phase']
        variation = row['variation']

        for key, value in rList_info2.items():
            if key in ['responsible']:
                responsible_group = {
                    'headerName': value,
                    'headerClass': 'group_title_yellow', #チョー　01/30　色変更
                    'children': [
                        {
                            'headerName': '責任者/実行者', 
                            'field': str(project_id) + ';' + key + ';' + str(phase_id) + str(variation_id),
                            'filter': True,
                            'cellStyle': {'background-color': '#FFFFCC'}, #チョー　01/30　色変更
                            'hide': True, # 山口　note以外は隠す 1/27
                            'editable' : True, #山口　黄色列はすべてeditableに 2/3
                            'headerClass': 'title_yellow', #チョー　01/30　色変更
                            'minWidth':100,
                        }
                    ]
                }
                project_item_gp.append(responsible_group)
                continue

            column_definition2 = {
                'headerName': value,
                'field': str(project_id) + ';' + key + ';' + str(phase_id) + str(variation_id),
                'filter': True,
                'hide': (value!='メモ'), # 山口　note以外は隠す 1/27
                'editable' : True, #山口　黄色列はすべてeditableに 2/3
                'cellStyle': {'background-color': '#FFFFCC'}, #チョー　01/30　色変更
                'headerClass': 'title_yellow', #チョー　01/30　色変更
                'minWidth':100,
            }
            project_item_gp.append(column_definition2)

        # Group for Performance and related columns
        project_list_dis = {
            'headerName': drivetrain +'_'+phase+'_'+variation, 
            'headerClass': 'group_title_yellow', #チョー　01/30　色変更
            'hide':True, #山口　Rリストの初期表示列を絞る 1/27
            'children': project_item_gp
        }
        go_add.append(project_list_dis)
        project_item_gp = []

    #チョー　01/30　ヘッダーの厚さを調整する
    go['headerHeight'] = 40
    go['columnDefs'].extend(go_add)

    #Kyaw 07/23 change the retrieved resized columns value to the grid->(minwidth and hide) #10/29 merge#5
    if (
        "resize_column_result" in st.session_state
        and not st.session_state.resize_column_result.empty
    ):
        df = st.session_state.resize_column_result

        saved_widths = df.set_index("edit_column")["column_width"].to_dict()
        saved_hides = df.set_index("edit_column")["is_hide"].to_dict()

        for col_def in go_add:
            # Top-level column
            if isinstance(col_def, dict) and "field" in col_def:
                field = col_def["field"]
                if field in saved_widths:
                    col_def["minWidth"] = int(saved_widths[field])
                    col_def["hide"] = bool(saved_hides.get(field, False))  # Default to False

            # Grouped/child columns
            elif isinstance(col_def, dict) and "children" in col_def:
                for child in col_def["children"]:
                    if "field" in child:
                        field = child["field"]
                        if field in saved_widths:
                            child["minWidth"] = int(saved_widths[field])
                            child["hide"] = bool(saved_hides.get(field, False))  # Default to False

    go['getDataPath'] = JsCode('''
                function(data) {
                    return data.params0p;
                }
            ''').js_code
    return go

#r_summary style #チョー　04/03
style_rsummary_by_judge = JsCode("""
    function(params) {
        //console.log('summary rlist: ',params);
        
        if (params.data != undefined) {
            return {'font-size':'25px','display':'flex','align-items':'center','justify-content':'center'};
        }
        //return {'font-size':'1px','display':'flex','align-items':'center','justify-content':'center','align-content':'space-around'};  // Default style
    }
    """)

style_link_format = JsCode("""
        class MemoCellRenderer {
            init(params) {
                this.eGui = document.createElement('a');
                var value = params.value;
                if (value) {
                    // Ensure the URL has the correct protocol
                    this.eGui.setAttribute('href', value.startsWith('http') ? value : 'https://' + value);
                    this.eGui.setAttribute('target', '_blank');
                    this.eGui.innerText = value; // Display the URL as the link text
                    this.eGui.setAttribute('style', 'color:blue; text-decoration:underline;');
                } else {
                    this.eGui.innerText = ''; // Handle null or empty values
                }
            }
            getGui() {
                return this.eGui;
            }
        }
    """)



#チョー　04/04　RサマリーGrid処理追加　01/30Grid表示変更
def create_rlist_summary_grid():

    go = {
        'defaultColDef': {
            'flex':1,
            'resizable': True,
            'wrapHeaderText': True,
            'suppressMovable': False,
            'allowDragFromColumnsToolPanel': True,
            'filter': True,
            'sortable': False,
        },
        'columnDefs': [],
        'treeData': False,
        'pagination': True,
        'groupDefaultExpanded': -1,
        'rowSelection': 'multiple',
        'suppressRowClickSelection': True,
        'groupSelectsChildren': True,
        'enableRangeSelection':True,
        'enableBrowserTooltips':True,
        'enableCharts':True,
        'suppressMultiRangeSelection':True,
        'alwaysShowHorizontalScroll': True,  # Ensure horizontal scroll bar is always visible
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
        'enableQuickFilter': True,
        'rowHeight': 70,
    }

    rList_info = {
        "performance": "性能",
        "judge_emoji":"判断",
        "manager_approval":"承認",
        "manager_approval_comment":"コメント",
    }

    # df_selects = st.session_state.df_selects

    go_add = []
     
    for key, value in rList_info.items():

        design_item_group = {
            'headerName': value,
            'headerClass': 'rsummary_title_yellow', #チョー　04/03　色変更
            'field': f'{key}',
            'filter': True,
            'wrapText': True,
            'autoHeight':True,
            'cellStyle': {'font-size':'25px'},
            'minWidth':200,
        }

        if key == 'judge_emoji':
            design_item_group['cellStyle'] = style_rsummary_by_judge
        if key == 'manager_approval' or key == 'manager_approval_comment':
            design_item_group['editable'] = True  
            design_item_group['flex'] = 2  
        if key == 'judge_emoji' or key == 'performance':
            design_item_group['minWidth'] = 200
        if key == 'manager_approval' :
            design_item_group['minWidth'] = 110
        else:
            design_item_group['minWidth'] = 210
        
        go_add.append(design_item_group)
     

    #チョー　04/03　ヘッダーの厚さを調整する
    go['headerHeight'] = 100
    go['columnDefs'].extend(go_add)
    go['getDataPath'] = JsCode('''
                function(data) {
                    return data.params0p;
                }
            ''').js_code
    return go


def fixed_sim():
    grid_options = {
    "defaultColDef": {
        "filter": True,
        # "suppressMovable": True,
        # "autoHeaderHeight": True,
        "flex": 1,
        "minWidth": 80,
        "editable": True,
        # "resizable": True
    },
    "rowSelection": "multiple",
    # "groupDisplayType": "multipleColumns",
    "suppressRowClickSelection": True,
    
    "columnDefs": [
        {
            "headerName": "更新",
            "checkboxSelection": True,   
        },
        {
            "headerName": "パラメータ_1",
            "field": "parameter_name_1",
            'editable': False,
        },
        {
            "headerName": "パラメータ_2",
            "field": "parameter_name_2",
            'editable': False,
        },
        {
            "headerName": "スタディID",
            "field": "study_id",
            'editable': False,
        },
        {
            "headerName": "Overall_Value",
            "field": "overall_value_3",
            'editable': False,
        },
        {
            "headerName": "値",
            "field": "overall_value_10001",
            'editable': False,
        }
    ],
    
    }
    return grid_options

def file_download_agop():
    grid_options = {
    "columnDefs": [
        {
            "headerName": "☑",
            "checkboxSelection": True
            
        },
        {
            "headerName": "大項目",
            "field": "z_parent_paraitem",
        },
        {
            "headerName": "小項目",
            "field": "z_child_paraitem"
        },
        {
            "headerName": "ファイル名",
            "field": "MAP"
        }
    ],
    "defaultColDef": {
        "flex": 1,
        "minWidth": 100,
        "editable": True,
        "resizable": True
    }
    }
    return grid_options

def update_conf_go():
    grid_options = {
    "defaultColDef": {
        "filter": True,
        # "suppressMovable": True,
        # "autoHeaderHeight": True,
        "flex": 1,
        "minWidth": 80,
        "editable": True,
        # "resizable": True
    },
    "rowSelection": "multiple",
    # "groupDisplayType": "multipleColumns",
    "suppressRowClickSelection": True,
    

    "columnDefs": [
        #チョー　01/14
        # {
        #     "headerName": "更新",
        #     "checkboxSelection": True,
            
        # },
        {
            "headerName": "大項目",
            "field": "z_parent_paraitem",
            'editable': False,
        },
        {
            "headerName": "小項目",
            "field": "z_child_paraitem",
            'editable': False,
        },
        {
            "headerName": "値",
            "field": "z_request_median"
        },
        {
            "headerName": "担当者",
            "field": "z_note"
        },
        {
            "headerName": "ステータス",
            "field": "state_name",
            "cellEditor":'agSelectCellEditor',
            "cellEditorParams":{
                "values": ['0.机上設計値(フィジカルデータ無し)', '1.設計値(一部フィジカルデータ含む机上検討値)', '2.設計値(フィジカルデータ)', "3.スペック", '4.名称', '5.対象外', ' ']# 山口　設定書き換え
            },
            # editable=True
        },
        {
            "headerName": "メモ",
            "field": "user_memo"
        }
    ],
    
    }
    return grid_options

def update_conf_go_rlist():#山口　R 用　1/29
    grid_options = {
    "defaultColDef": {
        "filter": True,
        # "suppressMovable": True,
        # "autoHeaderHeight": True,
        "flex": 1,
        "minWidth": 80,
        "editable": True,
        # "resizable": True
    },
    "rowSelection": "multiple",
    # "groupDisplayType": "multipleColumns",
    "suppressRowClickSelection": True,
    
    "columnDefs": [
        #02/07 チョー　チェックボックス非表示
        # {
        #     "headerName": "更新",
        #     "checkboxSelection": True,
            
        # },
        {
            "headerName": "設計項目",
            "field": "design_item_1",
            'editable': False,
        },
        {
            "headerName": "設計項目",
            "field": "design_item_2",
            'editable': False,
        },
        {
            "headerName": "目標性能",
            "field": "design_item_3",
            'editable': False,
        },
        {
            "headerName": "目標値",
            "field": "target"
        },
        {
            "headerName": "妥協値",
            "field": "adjusted_target"
        },
        {
            "headerName": "条件",
            "field": "auto_judge_type"
        },
        {
            "headerName": "設計値",
            "field": "design"
        },
        {
            "headerName": "判断",
            "field": "judge"
        },
        {
            "headerName": "判断エビデンス資料",
            "field": "judge_evidence"
        },       
        {
            "headerName": "主管承認",
            "field": "manager_approval"
        },
        {
            "headerName": "主管承認コメント",
            "field": "manager_approval_comment"
        },
        {

            "headerName": "メモ",
            "field": "note"
        }
    ],
    
    }
    return grid_options

def update_conf_go_sim():#山口　sim 用　12/2
    grid_options = {
    "defaultColDef": {
        "filter": True,
        # "suppressMovable": True,
        # "autoHeaderHeight": True,
        "flex": 1,
        "minWidth": 80,
        "editable": True,
        # "resizable": True
    },
    "rowSelection": "multiple",
    # "groupDisplayType": "multipleColumns",
    "suppressRowClickSelection": True,

    
    "columnDefs": [
        {
            "headerName": "更新",
            "checkboxSelection": True,
            
        },
        {
            "headerName": "大項目",
            "field": "parameter_name_1",
            'editable': False,
        },
        {
            "headerName": "小項目",
            "field": "parameter_name_2",
            'editable': False,
        },
        {
            "headerName": "値",
            "field": "value"
        },

        {
            "headerName": "メモ",
            "field": "user_memo"
        }
    ],
    
    }
    return grid_options

defOP={
    "pagination":True,
    "defaultColDef": {
        "filter": True,
        "resizable": True,
        "suppressMovable": True,
        "autoHeaderHeight": True,
    },
    "columnDefs":[]}

defOP={
    "pagination":True,
    "defaultColDef": {
        "filter": True,
        "resizable": True,
        "suppressMovable": True,
        "autoHeaderHeight": True,
    },
    "columnDefs":[]}

def update_conf_go_rfl_by_to_summary():#山口
    grid_options = {
    "defaultColDef": {
        "filter": True,
        # "suppressMovable": True,
        # "autoHeaderHeight": True,
        "flex": 1,
        "minWidth": 80,
        "editable": True,
        # "resizable": True
    },
    "rowSelection": "multiple",
    # "groupDisplayType": "multipleColumns",
    "suppressRowClickSelection": True,
    'enableRangeSelection':True,
    
    "columnDefs": [
        {
            "headerName": "項目",
            "field": "se_parameter",
            'editable': False,
        },
        {
            "headerName":"性能",
            "field": "performance"
        },
        {
            "headerName":"値",
            "field": "value"
        }    ],
    
    }
    return grid_options
def create_field(header_name, 
                 width, 
                 show_row_group=None, 
                 cell_renderer=None, 
                 cell_renderer_params=None, 
                 row_group=False, 
                 hide=False, 
                 cell_style=None,
                 editable=None,
                 cellEditorParams=None):
    
    field = {
        "headerName": header_name,
        "width": width,
        "autoHeight": True,
        "wrapText": True
    }
    if not cell_renderer is None:
        field.update({
            "showRowGroup": show_row_group,
            "cellRenderer": cell_renderer,
            "cellRendererParams": cell_renderer_params
        })
    if not show_row_group is None and cell_renderer is None:
        field.update({'field':header_name})
    if row_group:
        field.update({"rowGroup": True, "hide": hide})
    if cell_style:
        field.update({"cellStyle": cell_style})
    if editable:
        if editable == "True":
            field.update({"editable": True})
        else:
            field.update({"editable": editable})
    if cellEditorParams:
        field.update({"cellEditor": "agSelectCellEditor", "cellEditorParams": cellEditorParams})
    return field


def makeAGGOP_RFLop1(sections):
    
    RFLop1=defOP.copy()
    RFLop1['groupDisplayType'] = 'custom'
    RFLop1["groupHideOpenParents"]=True
    RFLop1["animateRows"]=True
    RFLop1["groupDefaultExpanded"]= -1
    RFLop1["configure_default_column"]=True

    for header, fields in sections:
        children = [create_field(*field) for field in fields]
        RFLop1["columnDefs"].append({"headerName": header, "children": children})

    return RFLop1

##########################
def makeAGGOP(jisho={},Grlen=0):
    PJgridop=defOP.copy()
    PJgridop["autoGroupColumnDef"]={"columnGroupShow": 'open'}
    PJgridop["groupDisplayType"]='multipleColumns'
    PJgridop["groupHideOpenParents"]="True"
    PJgridop["animateRows"]="true"
    # PJgridop["groupIncludeFooter"]="false"
    PJgridop["groupDefaultExpanded"]= -1
    PJgridop["columnDefs"]=[]
    PJgridop["rowSelection"] = "multiple"
    PJgridop['defaultColDef']['suppressMovable'] = True
    i=1
    Grlen=len(jisho) if Grlen==0 else Grlen
    for k,v in jisho.items():
        
        PJgridop["columnDefs"].append({
            "headerName":v,
			# "children":[
				# {
                "field":k,
				# "width": 300,
                # "headerName": v,
                "rowGroup": "true" if i<Grlen else "false",
                "hide": False if i==Grlen else True,
                "checkboxSelection": True if i==Grlen else False
                # }],
            })
        i+=1
    return PJgridop

def make_mapop():
    defo={
    "pagination":True,
    "defaultColDef": {
        "filter": True,
        "resizable": True,
        "suppressMovable": True,
        "autoHeaderHeight": True,
    },
    "columnDefs":[]}
    mapop=defOP.copy()
    #mapop['groupDisplayType'] = 'custom'
    #mapop["groupHideOpenParents"]=True
    mapop["animateRows"]=True
    #mapop["groupDefaultExpanded"]= -1
    mapop["editable"]=True
    mapop["configure_default_column"]=True

    for i in range(100):
        mapop["columnDefs"].append({"headerName": str(i), "field":str(i)})
    return mapop



# 2025/01/29 Telema RFL

# カラム共通オプション
def create_rfl_common_col(header_name,field,headerClass,filter=True,minWidth=300,editable = False, valueFormatter=None):
    """_summary_
        共通カラムオプションを作成
    Args:
        header_name (string): 列名
        field (string): dfの列名
        headerClass (string): color設定
        filter (bool): _description_. Defaults to True.
        minWidth (int): _description_. Defaults to 100.
        editable (bool): 変更
    Returns:
        dictionary: 基本列オプション
    """
    col_def = {
        'headerName': header_name,
        'field': field,
        'filter': filter,
        'headerClass': headerClass,
        'minWidth': minWidth,
        'editable': editable,
    }
    #日付のフォーマットを変わる　チョー　04/14
    if valueFormatter:
        col_def['valueFormatter'] = JsCode("""
            function(params) {
                return params.value ? new Date(params.value).toISOString().split('T')[0] : '';
            }
        """)

    return col_def

# グループ共通オプション
def create_rfl_group(header_name,field,headerClass):
    """_summary_
        共通グループオプションを作成
    Args:
        header_name (string): 列名
        field (string): dfの列名
        headerClass (string): color設定
    Returns:
        dictionary: 共通グループオプション
    """
    return {
            'headerName': header_name,
            'field': field,            
            'pinned': 'left',
            'wrapText': True,
            'headerClass': headerClass,
            'rowGroup': True,
            'hide': True,
    }

    
# 共通階層構造
def create_rfl_option(hierarchy):
    """_summary_
        各列のオプションを作成
        
    Args:
        hierarchy (string): _description_
        'car','system','unit'
        階層を指定

    Returns:
        dictionary: 1階層のオプション
    """
    
    # column = クエリで取得したdf列名を指定
    # r=requirements,f=function,l=logic
    
    
    # r_cols = {
    #     'wp': {
    #         'title': 'WP',
    #         'col': 'r_wp'
    #     },            
    #     'wp_id': {
    #         'title': 'WP_ID',
    #         'col': 'r_wp_id'
    #     }, 
    #     'pj': {
    #         'title': 'PJ_ID',
    #         'col': 'r_pj_id'
    #     },
    #     'item': {
    #         'title': '要求項目',
    #         'col': 'r_item'
    #     },
    #     'value': {
    #         'title': '要求値',
    #         'col': 'req'
    #     },
    #     'unit': {
    #         'title': '単位',
    #         'col': 'r_unit'
    #     },
    #     'scene': {
    #         'title': '環境・運転条件',
    #         'col': 'r_scene'
    #     }
    # }
    
    # f_cols = {
    #     'item': {
    #         'title': '機能',
    #         'col': 'f_item'
    #     },
    #     'value': {
    #         'title': '機能目標',
    #         'col': 'func'
    #     },
    #     'unit': {
    #         'title': '単位',
    #         'col': 'f_unit'
    #     },            
    # }
    
    # l_cols = {
    #     'item' :{
    #         'title' : '要求',
    #         'col' : 'l_item'
    #     },
    #     'value' :{
    #         'title' : '要求値',
    #         'col' : 'logic'
    #     },
    #     'unit' :{
    #         'title' : '単位',
    #         'col' : 'l_unit'
    #     },
    #     'scene' :{
    #         'title' : '環境・運転条件',
    #         'col' : 'l_scene'
    #     },
    #     'note' :{
    #         'title' : 'Note',
    #         'col' : 'note'
    #     },
    #     'allocation' :{
    #         'title' : 'Allocation',
    #         'col' : 'allocation'
    #     },            
    # }
    
    # 表示列情報を取得
    r_cols = RFLGridConfig.cols['r_cols']
    f_cols = RFLGridConfig.cols['f_cols']
    l_cols = RFLGridConfig.cols['l_cols']
    approve_cols = RFLGridConfig.cols['approve_cols']

    # 階層でオプションを変更
    if hierarchy == 'car':
        prefix = 'c_'
        color = 'car'
        header_name = '車両'
        
    elif hierarchy == 'system':
        prefix = 's_'
        color = 'system'
        header_name = 'システム'
        
    elif hierarchy == 'unit':
        prefix = 'u_'  
        color = 'unit'          
        header_name = 'Unit'

    # 階層単位でオプションを作成
    group = {
        'headerName': header_name,
        'headerClass': color,
        'children': [
            {
                'headerName': 'Requirements',
                'headerClass': 'group_req',
                'children': [
                        # create_rfl_common_col(r_cols['pj']['title'],prefix + r_cols['pj']['col'],'req'),       # relation test
                        # create_rfl_common_col(r_cols['wp']['title'],prefix + r_cols['wp']['col'],'req'),       # relation test
                        # create_rfl_common_col(r_cols['wp_id']['title'],prefix + r_cols['wp_id']['col'],'req'), # relation test
                        create_rfl_common_col(r_cols['item']['title'],prefix + r_cols['item']['col'],'req',minWidth=140),
                        create_rfl_common_col(r_cols['value']['title'],prefix + r_cols['value']['col'],'req',minWidth=200),
                        create_rfl_common_col(r_cols['unit']['title'],prefix + r_cols['unit']['col'],'req',minWidth=100),
                        create_rfl_common_col(r_cols['scene']['title'],prefix + r_cols['scene']['col'],'req',minWidth=400),                        
                ]
            },
            {
                
                'headerName': 'Function',
                'headerClass': 'group_func',
                'children': [
                        create_rfl_common_col(f_cols['item']['title'],prefix + f_cols['item']['col'],'func'),
                        create_rfl_common_col(f_cols['value']['title'],prefix + f_cols['value']['col'],'func',editable = True),
                        create_rfl_common_col(f_cols['unit']['title'],prefix + f_cols['unit']['col'],'func',minWidth=100),                        
                ]
            },
            {
                'headerName': 'Logic',
                'headerClass': 'group_logic',
                'children': [
                        create_rfl_common_col(l_cols['item']['title'],prefix + l_cols['item']['col'],'logic'),
                        create_rfl_common_col(l_cols['value']['title'],prefix + l_cols['value']['col'],'logic'),
                        create_rfl_common_col(l_cols['unit']['title'],prefix + l_cols['unit']['col'],'logic',minWidth=100),                        
                        create_rfl_common_col(l_cols['scene']['title'],prefix + l_cols['scene']['col'],'logic',minWidth=450),
                        create_rfl_common_col(l_cols['note']['title'],prefix + l_cols['note']['col'],'logic',minWidth=400),
                        # create_rfl_common_col(l_cols['allocation']['title'],prefix + l_cols['allocation']['col'],'logic') debug用
                ]
            },
            {
                'headerName': '出し手',
                'headerClass': 'group_req',
                'children': [
                    create_rfl_common_col(approve_cols['sender_selected']['title'],prefix + approve_cols['sender_selected']['col'],'req',minWidth=70,editable = True),
                    create_rfl_common_col(approve_cols['sender_judge']['title'],prefix + approve_cols['sender_judge']['col'],'req',minWidth=140,editable = False),
                    create_rfl_common_col(approve_cols['sender_name']['title'],prefix + approve_cols['sender_name']['col'],'req',minWidth=140,editable = False),
                    create_rfl_common_col(approve_cols['sender_date']['title'],prefix + approve_cols['sender_date']['col'],'req',minWidth=140,editable = False,valueFormatter=True),
                    create_rfl_common_col(approve_cols['sender_comment']['title'],prefix + approve_cols['sender_comment']['col'],'req',minWidth=140,editable = True),
                ]
            },
            {
                'headerName': '受け手',
                'headerClass': 'group_req',
                'children': [
                    create_rfl_common_col(approve_cols['receiver_selected']['title'],prefix + approve_cols['receiver_selected']['col'],'req',minWidth=70,editable = True),
                    create_rfl_common_col(approve_cols['receiver_judge']['title'],prefix + approve_cols['receiver_judge']['col'],'req',minWidth=140,editable = False),
                    create_rfl_common_col(approve_cols['receiver_name']['title'],prefix + approve_cols['receiver_name']['col'],'req',minWidth=140,editable = False),
                    create_rfl_common_col(approve_cols['receiver_date']['title'],prefix + approve_cols['receiver_date']['col'],'req',minWidth=140,editable = False,valueFormatter=True),
                    create_rfl_common_col(approve_cols['receiver_comment']['title'],prefix + approve_cols['receiver_comment']['col'],'req',minWidth=140,editable = True),
                ]
            },
        ]
    }
    return group

# 2025/01/28 Telema RFL TEST
def create_gridop_rfl_list():
    
    BGcolorRenderer=JsCode("""
    function (params) {
        if (params.data === undefined) {
            return {
                'background-color': '#C0C0C0',
                'wordBreak':'normal',
                'whiteSpace':'pre-line'
            };
        } else if (params.value === null) {
            return {
                'background-color': '#EFEFEF',
                'wordBreak':'normal',
                'whiteSpace':'pre-line'
            };                           
        } 
        return null;
    }
    """)

    ChangeHighlight = JsCode(
        """
    function(e) {
        let api = e.api;
        let rowIndex = e.rowIndex;
        let col = e.column.colId;
        
        console.log(e);
        let rowNode = api.getDisplayedRowAtIndex(rowIndex);
        api.flashCells({
          rowNodes: [rowNode],
          columns: [col],
          flashDelay: 10000000000
        });

    };
    """
    )

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
            'headerName': 'PJ/性能',
            'pinned': 'left',
            'width': 350,
            'wrapText': True,
            'headerClass': 'title_green'
        },
        'columnDefs': [],
        'treeData': False,
        # 'pagination': True, 山口　ページ切り替えし表示を無効化 必要性を確認したい
        'groupDisplayType': 'groupRows',
        # 'groupDisplayType': 'singleColumn',Pattern1
        # 'groupDisplayType': 'groupRows',Pattern2
        'groupDefaultExpanded': -1,
        'rowSelection': 'multiple',
        'suppressRowClickSelection': True,
        'groupSelectsChildren': True,
        'enableRangeSelection':True,
        'enableBrowserTooltips':True,
        'onCellValueChanged':ChangeHighlight,
        'suppressMultiRangeSelection':True,
        'alwaysShowHorizontalScroll': True,  # Ensure horizontal scroll bar is always visible
        # 'domLayout':'autoHeight',
        'sideBar': {
            'toolPanels': [
            {
                'id': 'columns',
                'labelDefault': 'Columns',
                'labelKey': 'columns',
                'iconKey': 'columns',
                'toolPanel': 'agColumnsToolPanel',
                'toolPanelParams': {
                # 'suppressRowGroups': True,
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
        "groupMultiAutoColumn": True
    }
    
    go_add = []    
    # プロジェクトコード、性能列を追加
    # containers = {
    #     'pj': {
    #         'title': 'PJ',
    #         'col': 'project_code'
    #     },
    #     'wp' : {
    #         'title': '性能',
    #         'col':  'c_r_wp'
    #     },
    #     'lot' : {
    #         'title': 'lot',
    #         'col':  'lot'
    #     }        
    # }
    
    containers = RFLGridConfig.cols['containers']

    # Pattern 1~2
    # pj_column = create_rfl_group(containers['pj']['title'],containers['pj']['col'],'title_green')
    # wp_column = create_rfl_group(containers['wp']['title'],containers['wp']['col'],'title_green')
    # lot_column = create_rfl_group(containers['lot']['title'],containers['lot']['col'],'title_green')

    # go_group = []
    # go_group.append(pj_column)
    # go_group.append(wp_column)
    # go_group.append(lot_column)
    # go['columnDefs'].extend(go_group)    

    # Pattern 3
    # pj_column = create_rfl_common_col(containers['pj']['title'],containers['pj']['col'],'title_green')
    # wp_column = create_rfl_common_col(containers['wp']['title'],containers['wp']['col'],'title_green')
    
    # go_add.append(pj_column)
    # go_add.append(wp_column)
    
    pj_column = create_rfl_common_col(containers['pj']['title'],containers['pj']['col'],'title_green')
    
    # debug用PJ_CODE出力
    # go_add.append(pj_column)
    
    # 各階層列を作成    
    car_group = create_rfl_option('car')
    system_group = create_rfl_option('system')
    unit_group = create_rfl_option('unit')
    
    go_add.append(car_group)
    go_add.append(system_group)
    go_add.append(unit_group)
    
    go['columnDefs'].extend(go_add)

    go['getDataPath'] = JsCode('''
                function(data) {
                    return data.params0p;
                }
                
            ''').js_code
    return go

# 03/18
def update_to_grid(grid_name):
    grid_options = {
        "defaultColDef": {
            "filter": True,
            # "suppressMovable": True,
            # "autoHeaderHeight": True,
            "flex": 1,
            "minWidth": 80,
            "editable": True,
            # "resizable": True
        },
        "rowSelection": "multiple",
        # "groupDisplayType": "multipleColumns",
        "suppressRowClickSelection": True,
        

        "columnDefs": [
            {
                "headerName": 'R要求',
                "field": f'{grid_name}_r_item',
                'editable': False,
            },
            {
                "headerName": 'R Usecase',
                "field": f'{grid_name}_r_scene',
                'editable': False,
            },
            {
                "headerName": 'L要求',
                "field": f'{grid_name}_l_item',
                'editable': False,
            },
            {
                "headerName": '要求値',
                "field": f'{grid_name}_logic',
                'editable': False,
            },
            {
                "headerName": 'T/Oフラグ',
                "field": f'{grid_name}_flag_to',
                'editable': False,
            },
            {
                "headerName": "メモ",
                "field": f'{grid_name}_user_memo',
                'editable': True,
            }
        ],
    }
    return grid_options


def update_rfl_sender_receiver_info(sender_or_receiver):

    header_name = '出し手'
    if sender_or_receiver == 'receiver':
        header_name = '受け手'
    grid_options = {
    "defaultColDef": {
        "filter": False,
        # "suppressMovable": True,
        # "autoHeaderHeight": True,
        "flex": 1,
        "minWidth": 80,
        "editable": True,
        "sortable": False
        # "resizable": True
    },
    "rowSelection": "multiple",
    # "groupDisplayType": "multipleColumns",
    "suppressRowClickSelection": True,
    # 'alwaysShowHorizontalScroll': True,
    

    "columnDefs": [
        {
            "headerName": "性能",
            "field": "r_wp",
            "minWidth": 70,
            'editable': False,
        },
        {
            "headerName": "Requirements",
            "children": [
                {
                    "headerName": "要求項目",
                    "field": f'{sender_or_receiver}_r_item',
                    "minWidth": 150,
                    'editable': False,
                },
                {
                    "headerName": "要求値",
                    "field": f'{sender_or_receiver}_req',
                    "minWidth": 200,
                    'editable': False,
                },
            ]
        },
        {
            "headerName": "Logic",
            "children": [
                {
                    "headerName": "要求",
                    "field": f'{sender_or_receiver}_l_item',
                    "minWidth": 150,
                    'editable': False,
                },
                {
                    "headerName": "要求値",
                    "field": f'{sender_or_receiver}_logic',
                    "minWidth": 100,
                    'editable': False,
                },
            ]
        },
    ],
    
    }
    return grid_options

#チョー　04/04　RサマリーGrid処理追加　01/30Grid表示変更
def update_rlist_summary_grid():

    grid_options = {
        "defaultColDef": {
            "filter": False,
            "flex": 1,
            "minWidth": 80,
            "editable": True,
            "sortable": False
        },
        "rowSelection": "multiple",
        "suppressRowClickSelection": True,

        "columnDefs": [
            {
                "headerName": "性能",
                "field": "performance",
                "minWidth": 70,
                'editable': False,
            },
            {
                "headerName": "判断",
                "field": "judge_emoji",
                "minWidth": 30,
                'editable': False,
            },
            {
                "headerName": "承認",
                "field": "manager_approval",
                "minWidth": 70,
                'editable': True,
            },
            {
                "headerName": "コメント",
                "field": "manager_approval_comment",
                "minWidth": 250,
                'editable': True,
            },
        ],
    }
    return grid_options


def create_judge_columns(prefix: str, header_class: str) -> list:
    return [
        {
            "headerName": "承認数",
            "headerClass": header_class,
            "field": f"{prefix}_judge_count",
            "minWidth": 30,
            "editable": False,
        },
        {
            "headerName": "承認率",
            "headerClass": header_class,
            "field": f"{prefix}_percentage",
            "minWidth": 30,
            "editable": False,
        },
    ]

def create_judge_group(header_name: str, prefix_base: str, group_class: str, cell_class: str) -> dict:
    return {
        "headerName": header_name,
        "headerClass": group_class,
        "children": create_judge_columns(prefix_base, cell_class)
    }

def update_rfl_dashboard_grid():
    grid_options = {
        "defaultColDef": {
            "filter": False,
            "flex": 1,
            "minWidth": 80,
            "editable": True,
            "sortable": False
        },
        "rowSelection": "multiple",
        "suppressRowClickSelection": True,
        "rowHeight": 40,
        "headerHeight": 40,
        "columnDefs": [
            {
                "headerName": "性能",
                "headerClass": "dashboard_performance",
                "field": "group_performance",
                "minWidth": 30,
                "editable": False,
                "cellStyle": {
                    "backgroundColor": "#C1E5F5",
                },
            },
            {
                "headerName": "車両toシステム",
                "headerClass": "group_dashboard_car",
                "children": [
                    create_judge_group("出し手", "c_sender", "group_dashboard_car", "dashboard_car"),
                    create_judge_group("受け手", "c_receiver", "group_dashboard_car", "dashboard_car"),
                ]
            },
            {
                "headerName": "システムtoユニット",
                "headerClass": "group_dashboard_system",
                "children": [
                    create_judge_group("出し手", "s_sender", "group_dashboard_system", "dashboard_system"),
                    create_judge_group("受け手", "s_receiver", "group_dashboard_system", "dashboard_system"),
                ]
            },
        ],
        "domLayout": "autoHeight"
    }

    return grid_options

def go_dialog_cost_info():

    go = {
        'columnDefs':[
            {
                'headerName':'プロジェクト',
                'field':'project_info_str_wo_phase'
            },
            {
                'headerName':'アイテム',
                'field':'part_name',
                #こっからした必要？？？
                # 'editable': True,
                # 'cellStyle':{
                #     'background-color':'#FFFFCC'
                # }, 
                # 'cellEditor': 'agSelectCellEditor',
                # 'cellEditorParams': {
                #     'values': df_cost_item['item_name_4'].tolist()
                #     },
                    
                # 'onCellValueChanged': callback_part_name
            },
            {
                'headerName':'単価',
                'field':'original_cost',
                'editable': False,
            },
            {
                'headerName':'レートID',
                'field':'cost_rate_id'
            },
            {
                'headerName':'換算レート',
                'field':'cost_rate'
            },
            {
                'headerName':'レート名',
                'field':'cost_rate_name',
                'editable': False,
            },
            {
                'headerName':'効果',
                'field':'parameter_change_amount',
                'editable': False,

            },
            {
                'headerName':'カテゴリ',
                'field':'parameter_name',
                'editable': False,
            },
        ],
        'defaultColDef':{
            'resizable': True,
            'headerClass': 'cost'
        },
    }
    return go

#PRJ新規作成のダイアログで使うベースプロジェクト一覧のGrid
def base_project_grid():
    # Build column definitions list
    column_defs = []
    
    # Only add checkbox column when chosen_id is not 4
    if int(st.session_state['chosen_id']) != 4:
        column_defs.append({
            "headerName": "",
            "checkboxSelection": True,
            'headerClass': 'title_green',
            "minWidth": 40,
        })
    
    # Add all other columns
    column_defs.extend([
        {
            "headerName": 'プロジェクト',
            "field": f'project_code',
            'headerClass': 'title_green'
        },
        {
            "headerName": '仕向け',
            "field": f'destination',
            'headerClass': 'title_green'
        },
        {
            "headerName": '駆動方式',
            "field": f'drivetrain',
            'headerClass': 'title_green'
        },
        {
            "headerName": 'ロット',
            "field": f'lot',
            'headerClass': 'title_green'
        },
        {
            "headerName": 'フェーズ',
            "field": f'phase',
            'headerClass': 'title_green'
        },
    ])
    
    grid_options = {
        "defaultColDef": {
            "filter": False,
            # "suppressMovable": True,
            # "autoHeaderHeight": True,
            "flex": 1,
            "minWidth": 80,
            "editable": False,
            # "resizable": True
        },
        "rowSelection": "multiple",
        # "groupDisplayType": "multipleColumns",
        "suppressRowClickSelection": True,
        
        "columnDefs": column_defs,
    }

    

    if not int(st.session_state['chosen_id']) == 4:
        go_add = []
        variation_list = {
            "headerName": 'バリエーション',
            "field": f'variation',
            'headerClass': 'title_green'
        }
        go_add.append(variation_list)
        grid_options['columnDefs'].extend(go_add)
        
    return grid_options