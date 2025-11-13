import pandas as pd
import streamlit as st
import const.constpara as co
import extra_streamlit_components as stx
# from st_aggrid import AgGrid
# from st_aggrid.shared import JsCode
from st_aggrid import AgGrid, JsCode
import datetime
import json
import module.dialog as dia
import module.grid_option as gop
import module.utils as utl
from module.PsqlModule import psql_class
import time
from st_aggrid.grid_options_builder import GridOptionsBuilder

# CSSファイルの内容を読み込む
with open(co.css, encoding='utf-8') as f:
    css = f.read()

with open(co.css_ag, encoding='utf-8') as f:
    css_ag = json.load(f)

sql = psql_class()
# CSSをStreamlitに適用
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

cell_highlight = JsCode("""
function(params) {
	if(params.node.rowIndex() === 0){
		return{
			"backgroundColor":"#000000"
		}
	};
	return null;
}
""")

# 列のスタイルを決定する関数
def get_column_style(df, column_name):
    # 各列の値を取得
    column_values = df[column_name].dropna().tolist()
    # 列内の値が異なる場合
    if len(set(column_values)) > 1:
        return {'backgroundColor': 'lightcoral'}
    return {}

def back_to_SPDM_LIST():
    st.switch_page("./pages/SPDM_LIST.py")


tredeOffBGcolor = JsCode(f"""
    function(params) {{
        // console.log('Params:', params.node);
        
        // Get the aggregated data from the row node
        let aggData = params.node.aggData;
        let rowGroupIndex = params.node.rowGroupIndex;
        // console.log('aggData:' , aggData);
        // Check if aggData exists
        if (aggData) {{
            // Collect all values from aggData
            let values = [];

            // Iterate over all keys in aggData
            for (let key in aggData) {{
                if (aggData.hasOwnProperty(key)) {{
                    let value = aggData[key];

                    // Check if value is not null and add to values array
                    if (value !== null && value !== undefined && value !== '') {{
                        values.push(value);
                    }}
                }}
            }}

            // Check if there are different values
            let uniqueValues = [...new Set(values)];  // Get unique values

            // If there are more than one unique value, apply a different style
            if (rowGroupIndex != 0 && uniqueValues.length > 1) {{
                //console.log('Different values found:', uniqueValues);
                return {{ backgroundColor: 'lightyellow' }};  // Apply different background color if values are different
            }}
        }}

        // Default style if all values are the same or null
        return {{ backgroundColor: 'white' }}; 
    }}
""")

#チョー　05/19　TO自動判定して、TOになる行を黄色に変更する
tredeOffBGcolor1 = JsCode("""
    function(params) {
        // Only apply style to first-level children (they have a parent, but not a grandparent)
        const node = params.node;
        // console.log('node:', node);
        const parent = node.parent;

        if (!parent || !node.childrenAfterSort) {
            return null;  // Not a first-level node or no children
        }

        // Check if any second-level (child of this node) has to_result === true
        for (let grandchild of node.childrenAfterSort) {
            if (grandchild.data && grandchild.data.to_result === true) {
                return { backgroundColor: 'lightyellow' };
            }
        }

        return null;
    }
""")


# Ha-san 0221: add aggregation function logic
agg_function = {
    'firstNotNull': JsCode("""function(params) {
        //console.log('agg-function: ', params);
        const pivotKeysFoldStatus = params?.pivotResultColumn?.colDef?.pivotKeys?.length > 1 ? false : true;
        //console.log('pivotKeysFoldStatus: ', pivotKeysFoldStatus);
        const rowNodeLevel = params?.rowNode?.level;
        
        let aggResult = '';
        let aggValuesList = [];
        for (var i = 0; i < params.values.length; i++) {
            const itemValue = params.values[i];
            if (itemValue !== null && itemValue !== '') {
                    //if (itemValue == 1516) {console.log(params);}
                    
                    if (!pivotKeysFoldStatus) {
                        return itemValue;
                    }
                    
                    if (!aggValuesList.includes(itemValue)){
                        aggValuesList.push(itemValue);
                        if (aggResult == '') {
                            aggResult = params.values[i];
                        } else {
                            aggResult += ` | ${params.values[i]}`;
                        }
                    }
            }
        }
        return aggResult;
    }"""),
}
# ==========

def filter_items(df,item_name):
    logic = f"{item_name}_logic"
    l_wp = f"{item_name}_l_wp" 
    l_item = f"{item_name}_l_item"
    # Filter out rows where 'logic' is None or null
    # Filter out rows where 'logic' is None or an empty string
    df_non_null_logic = df[df[logic].notna() & (df[logic] != '')]
    # st.write("df1_non_null_logic: ",df_non_null_logic)
    # Group by 'l_wp' and 'l_item', and check if there are multiple unique 'logic' values
    grouped = df_non_null_logic.groupby([l_wp, l_item])[logic].nunique()
    # st.write("grouped",grouped)
    # Find groups with more than 1 unique 'logic'
    invalid_groups = grouped[grouped > 1].index

    # Filter rows where the combination of l_wp' and 'l_item' is in the invalid groups
    df_invalid = df[df.set_index([l_wp, l_item]).index.isin(invalid_groups)]

    # Optionally, reset the index of the resulting DataFrame
    df_invalid = df_invalid.reset_index(drop=True)

    # st.write("df invalid: ",df_invalid)
    # st.write("after set: ",df1)
    return df_invalid


#チョー　05/19 Helper to check if value is valid number 数字のみチェックする
def is_valid_number(value):
    if value is None:
        return False
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False

#チョー　05/19 TO自動判定機能
def check_overlap(v1, op1, v2, op2):
    print(f'in fun: {v1},{op1} and {v2},{op2}')
    v1 = float(v1)
    v2 = float(v2)
    if v1 == v2:
        conflicting_pairs = {
            '<': {'>', '=', '≧'},
            '>': {'<', '=', '≦'},
            '=': {'<', '>'},
            '≦': {'>'},
            '≧': {'<'},
        }
        return op2 in conflicting_pairs.get(op1, set())
    
    if op1 == op2 and '=' not in (op1, op2):
        return False
    if v1 > v2:
        return op1 in {'>', '=', '≧'} and op2 in {'<', '=', '≦'}
    if v1 < v2:
        return op1 in {'<', '=', '≦'} and op2 in {'>', '=', '≧'}
    return False

#チョー　TOになる行の「to_result」にTrueを入れる
def update_overlap_df(df,df_name):
    # Prepare result column
    df['to_result'] = False
    # Group and compare within groups
    group_df = df.groupby([f'{df_name}_r_wp', f'{df_name}_l_wp', f'{df_name}_l_item'], dropna=False)

    for name, group in group_df:
        # if df_name == 's':
        #     if group.iloc[0][f'{df_name}_r_wp'] == '4WD' and group.iloc[0][f'{df_name}_l_wp'] == 'Unit(ePT)' and (group.iloc[0][f'{df_name}_l_item'] == 'FR MOT_Max_Speed_力行_車両要求' or group.iloc[0][f'{df_name}_l_item'] == 'RR MOT_Max_Speed_力行_車両要求'):
        #         st.write(f'df data in {df_name}:', group)
        # elif df_name == 'c':
        #     if group.iloc[0][f'{df_name}_r_wp'] == '4WD' and group.iloc[0][f'{df_name}_l_wp'] == 'PWT(4WD)' and (group.iloc[0][f'{df_name}_l_item'] == 'DS駆動 FR トルク' or group.iloc[0][f'{df_name}_l_item'] == 'DS駆動 RR トルク'):
        #         st.write(f'df data in {df_name}:', group)
        indices = group.index.tolist()
        n = len(group)
        conflict_found = False  # Flag to track if conflict was found
        for i in range(n):
            if conflict_found:  # Stop processing once if conflict was found
                break
            row_i = group.iloc[i]
            val_i = row_i[f'{df_name}_logic']
            op_i = row_i[f'{df_name}_log_condition']
            # Check validity
            if not is_valid_number(val_i) or pd.isna(op_i) or op_i.strip() not in ('<','>','=','≧','≦'):
                continue

            for j in range(i + 1, n):
                row_j = group.iloc[j]
                val_j = row_j[f'{df_name}_logic']
                op_j = row_j[f'{df_name}_log_condition']

                # Check validity
                if not is_valid_number(val_j) or pd.isna(op_j) or op_j.strip() not in ('<','>','=','≧','≦'):
                    continue

                if check_overlap(val_i, op_i, val_j, op_j):
                    print(f'match result-> val1: {val_i}{op_i} and val2: {val_j}{op_j}')
                    # Mark both rows as True for conflict
                    df.at[indices[i], 'to_result'] = True
                    df.at[indices[j], 'to_result'] = True
                    conflict_found = True  # Stop further checks for this group
                    break
    return df

def c_grid(filter):
    
    # print('c df before: ', datetime.datetime.now())
    df = st.session_state.rfl_list
    # print('c df after: ', datetime.datetime.now())
    # df1 = df[['c_r_wp','c_r_item_2', 'c_l_item', 'c_l_wp', 'c_logic','c_r_scene','c_l_scene']]
    df1 = df[['c_r_wp','c_r_item_2', 'c_l_item', 'c_l_wp', 'c_logic','c_r_scene','c_l_scene','c_log_condition']] #チョー 05/19
    df1 = df1[df1['c_r_wp'].notna()]
    df1['c_logic_c_condition'] = df1['c_log_condition'].replace('', None).fillna('') +  df1['c_logic'].replace('', None).fillna('')#チョー 05/19 c_logic,c_log_conditionをs_logic_s_conditionに入れる

    df1 = update_overlap_df(df1,'c') #チョー 05/19

    # st.write('c: ', df1)
    # # Sort the DataFrame by 'c_l_wp' and 'c_l_item'
    # df1_sorted = df1.sort_values(by=['c_l_wp', 'c_l_item'])
    # st.write('sorted: ', df1_sorted)
    # # If you want to reset the index after sorting
    # df1_sorted = df1_sorted.reset_index(drop=True)
    # st.write('reset sorted: ', df1_sorted)
    # print('filter: ', filter)
    # print('filter_c: ', st.session_state.filter_c)
    if st.session_state.filter_c is True and filter is True:
        df1 = filter_items(df1,'c')

    column_defs = [
        {'field': 'c_r_wp', 'pivot': True, 'suppressMovable': True},
        {'field': 'c_r_item_2', 'pivot': True, 'suppressMovable': True},
        {'field': 'c_r_scene', 'pivot': True, 'suppressMovable': True},
        {'field': 'c_l_wp', 'rowGroup': True, 'suppressMovable': True, 'columnGroupShow': 'never' },
        {'field': 'c_l_item', 'rowGroup': True, 'suppressMovable': True, 'columnGroupShow': 'never'}, 
        # {'field': 'c_logic', 'headerName':'Value','aggFunc': 'firstNotNull', 'suppressMovable': True}, #Ha-san 0221: add aggregation function as default
        {'field': 'c_logic_c_condition', 'headerName':'Value','aggFunc': 'firstNotNull', 'suppressMovable': True}, #チョー 05/19

    ]


    grid_options = {
        'columnDefs': column_defs,
        'suppressAggFuncInHeader': 'true',
        'aggFuncs': agg_function,
        'defaultColDef': {
            'resizable': True,
            # 'pivot': True,
            "enableValue": True,
            'enableRowGroup': True, 
            'enablePivot': True,
            # 'suppressMovable': True,  # Prevent dragging and dropping of columns
            # 'onCellValueChanged':valueChange,
            'value': True,
            'sortable': False
        },
        'pivotMode': True,  # デフォルトでピボットモードを有効にする
        'getRowStyle': tredeOffBGcolor1,
        # 'getCellStyle': BGcolorRenderer11,
        'sideBar': "columns",
        'rowData': df1.to_dict('records'),
        # 'domLayout': 'autoHeight',
        # 'pagination': True,  # Enable pagination to avoid rendering too many rows at once
        # 'paginationPageSize': 100,  # Display 100 rows per page
        # 'infiniteInitialRowCount': 100,  # Initial row count for infinite scrolling
        # 'cacheBlockSize': 100,  # Number of rows per block
        # 'maxBlocksInCache': 10  # Maximum blocks to keep in cache (adjust as necessary)
    }

    # GridOptionsBuilderを使用してオプションを設定
    AgGrid(df1, gridOptions=grid_options, height=800, allow_unsafe_jscode=True, key='c_grid')


def s_grid(filter):

    df = st.session_state.rfl_list
    # st.write('s: ', df)
    # df2 = df[['s_r_wp','s_r_item_2', 's_l_item', 's_l_wp', 's_logic','s_r_scene','s_l_scene']]
    df2 = df[['s_r_wp','s_r_item_2', 's_l_item', 's_l_wp', 's_logic','s_r_scene','s_l_scene','s_log_condition']] #チョー 05/19
    df2 = df2[df2['s_r_wp'].notna()]
    df2['s_logic_s_condition'] = df2['s_log_condition'].replace('', None).fillna('') + df2['s_logic'].replace('', None).fillna('') #チョー 05/19 s_logic,s_log_conditionをs_logic_s_conditionに入れる

    df2 = update_overlap_df(df2,'s') #チョー 05/19
    # st.write('s1: ', df2)

    if st.session_state.filter_s is True and filter is True:
        df2 = filter_items(df2,'s')

    # Create column definitions for df1
    column_defs = [
        {
            'field': 's_r_wp', 
            'pivot': True, 
            'suppressMovable': True,
        },
        {'field': 's_r_item_2', 'pivot': True, 'suppressMovable': True},
        {'field': 's_r_scene', 'pivot': True, 'suppressMovable': True},
        {'field': 's_l_wp', 'rowGroup': True, 'suppressMovable': True},
        {'field': 's_l_item', 'rowGroup': True, 'suppressMovable': True}, 
        # {'field': 's_logic', 'headerName':'', 'aggFunc': 'first', 'suppressMovable': True}
        # {'field': 's_logic', 'headerName':'Value','aggFunc': 'firstNotNull', 'suppressMovable': True} #Ha-san 0221: add aggregation function as default
        {'field': 's_logic_s_condition', 'headerName':'Value','aggFunc': 'firstNotNull', 'suppressMovable': True}, #チョー 05/19
    ]
    
    grid_options = {     
        'columnDefs': column_defs,   
        'suppressAggFuncInHeader': 'true',
        'aggFuncs': agg_function,    
        'defaultColDef': {
            'resizable': True,
            # 'pivot': True,
            "enableValue": True,
            'enableRowGroup': True, 
            'enablePivot': True,
            #  'suppressMovable': True,  # Prevent dragging and dropping of columns
            'value': True,
            'sortable': False
        },
        'pivotMode': True,  # デフォルトでピボットモードを有効にする
        'getRowStyle': tredeOffBGcolor1, #チョー 05/19
        'sideBar': "columns",
        'rowData': df2.to_dict('records'),
    }

    # GridOptionsBuilderを使用してオプションを設定
    AgGrid(df2, gridOptions=grid_options, height=800, allow_unsafe_jscode=True, key='s_grid')


def u_grid(filter):

    df = st.session_state.rfl_list
    
    # df3 = df[['u_r_wp','u_r_item_2', 'u_l_item', 'u_l_wp', 'u_logic','u_r_scene','u_l_scene']].dropna()
    df3 = df[['u_r_wp','u_r_item_2', 'u_l_item', 'u_l_wp', 'u_logic','u_r_scene','u_l_scene','u_log_condition']]
 
    # st.write('u: ', df2)
    df3 = df3[df3['u_r_wp'].notna()]

    df3['u_logic_u_condition'] =  df3['u_log_condition'].replace('', None).fillna('') + df3['u_logic'].replace('', None).fillna('')
    df3 = update_overlap_df(df3,'u')

    if st.session_state.filter_u is True and filter is True:
        df3 = filter_items(df3,'u')
    # Create column definitions for df1
    column_defs = [
        {
            'field': 'u_r_wp', 
            'pivot': True, 
            'suppressMovable': True,
        },
        {'field': 'u_r_item_2', 'pivot': True, 'suppressMovable': True},
        {'field': 'u_r_scene', 'pivot': True, 'suppressMovable': True},
        {'field': 'u_l_wp', 'rowGroup': True, 'suppressMovable': True},
        {'field': 'u_l_item', 'rowGroup': True, 'suppressMovable': True}, 
        # {'field': 'u_logic', 'aggFunc': 'count', 'suppressMovable': True}
        # {'field': 'u_logic', 'headerName':'Value', 'aggFunc': 'firstNotNull', 'suppressMovable': True} #Ha-san 0221: add aggregation function as default
        {'field': 'u_logic_u_condition', 'headerName':'Value','aggFunc': 'firstNotNull', 'suppressMovable': True}, #チョー 05/19
    ]

    # df2
    
    grid_options = {
        'columnDefs': column_defs,
        'suppressAggFuncInHeader': 'true',
        'aggFuncs': agg_function,
        'defaultColDef': {
            'resizable': True,
            # 'pivot': True,
            "enableValue": True,
            'enableRowGroup': True, 
            'enablePivot': True,
            #  'suppressMovable': True,  # Prevent dragging and dropping of columns
            'value': True,
            'sortable': False
        },
        'pivotMode': True,  # デフォルトでピボットモードを有効にする
        
        'getRowStyle': tredeOffBGcolor1, #チョー 05/19
        'sideBar': "columns",
        'rowData': df3.to_dict('records')
    }

    # GridOptionsBuilderを使用してオプションを設定
    AgGrid(df3, gridOptions=grid_options, height=800, allow_unsafe_jscode=True, key='u_grid')



def set_filter_state(filter_keys, grid_functions, button_txt, label_txt):
    """Sets the filter state and calls the corresponding grid functions with Japanese button label."""
    filter_btn = st.button(button_txt)
    st.write(f'{label_txt}：')
    if filter_btn:
        for filter_key in filter_keys:
            st.session_state[filter_key] = True
        # Iterate over grid_functions list and call each function with True
        for grid_function in grid_functions:
            grid_function(True)
    else:
        # If button is not clicked, call each function with False
        for grid_function in grid_functions:
            grid_function(False)

def main():
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1, 2, 2, 2, 1, 7, 2, 2])
    
    # Initialize session state variables if they don't exist
    if 'to_display_onload' not in st.session_state:
        st.session_state['to_display_onload'] = 1
    #山口　サマリー機能を実装する3/27
    if 'flag_summary' not in st.session_state:
        st.session_state.flag_summary = False
    if 'flag_summary_before' not in st.session_state:
        st.session_state.flag_summary_before = False
    filter_keys = ['filter_c', 'filter_s', 'filter_u']

    # Ensure all necessary filter keys exist in session_state
    for key in filter_keys:
        if key not in st.session_state:
            st.session_state[key] = False

    with col1:
        if st.button("戻る"):
            for key in filter_keys + ['to_display_onload']:
                if key in st.session_state:
                    del st.session_state[key]
                if 'df_display_on_summary' in st.session_state:#サマリーモードでのみ使用するsession_stateは戻る押したら削除する
                    del st.session_state.df_display_on_summary
                    del st.session_state.selected_variation
            back_to_SPDM_LIST()
    with col8:
        st.session_state.flag_summary=st.toggle('サマリーモード', key='summary_toggle', value=st.session_state.flag_summary_before)
    if not st.session_state.flag_summary:
        if 'df_display_on_summary' in st.session_state:#サマリーモードでのみ使用するsession_stateは詳細に戻ったら削除する
            del st.session_state.df_display_on_summary
            del st.session_state.selected_variation

        with col2:
            if st.button("車両→システム"):
                st.session_state['to_display_onload'] = 1

        with col3:
            if st.button("システム→ユニット"):
                st.session_state['to_display_onload'] = 2

        with col4:
            if st.button("ユニット→コンポ"):
                st.session_state['to_display_onload'] = 3

        with col5:
            if st.button("全て"):
                st.session_state['to_display_onload'] = 4

        # Logic to display respective filters based on `to_display_onload`
        if st.session_state['to_display_onload'] == 1:
            set_filter_state(['filter_c'], [c_grid], 'Filter(車両→システム)','車両→システム') 
        elif st.session_state['to_display_onload'] == 2:
            set_filter_state(['filter_s'], [s_grid], 'Filter(システム→ユニット)','システム→ユニット') 
        elif st.session_state['to_display_onload'] == 3:  
            set_filter_state(['filter_u'], [u_grid], 'Filter(ユニット→コンポ)','ユニット→コンポ') 
        elif st.session_state['to_display_onload'] == 4:
            set_filter_state(filter_keys, [c_grid, s_grid, u_grid], 'Filter(全て)','全て')
    else: #山口　サマリーモード
        #山口　ステートメントの表示をしよう5/1
        df_selects = st.session_state.df_selects
        df_to_statement = sql.get_r_statement(list(set(df_selects['project_id'])), list(set(df_selects['phase_id'])), 'TO') #名称がRステートメント専用のように見えるけどそれいがいもつかえるよね
        st.session_state.df_to_statement = df_to_statement




        #必要なSE情報の取得,postgre_get_dateが使えるかな、そもそもdatastuck持ってる？持っていないときもあるのかじゃあ絶対必要だね
        variations = st.session_state['selectoption6']
        
        #variationを選択させるselectboxを設置する 4/4 se_data_stuck でつける列名がバリエーション名からIDに変わったことにより、ここでも名前そのものでなく番号変換が必要になる 8/5
        
        with col7:
            selected_variation = st.session_state.prj_info_list[st.session_state.prj_info_list['variation']==st.selectbox('', options=variations, key='select_variation')]['variation_id'].tolist()[0]
        if 'selected_variation' not in st.session_state or selected_variation != st.session_state.selected_variation:
            st.session_state.selected_variation = selected_variation
            if 'df_display_on_summary' in st.session_state :
                del st.session_state.df_display_on_summary
        if 'df_display_on_summary' not in st.session_state :

            df1,df2 = sql.posgre_get_date(st.session_state['selectoption1'],
                                            st.session_state['selectoption2'],
                                            st.session_state['selectoption3'],
                                            st.session_state['selectoption4'],
                                            st.session_state['selectoption5'])
            st.session_state.prj_info_list = df1
            st.session_state.se_data_stuck = df2
            df_se_data = st.session_state.se_data_stuck#この一文がないからずっと最初の一回が古いセレクションで起きていた
            # st.write(st.session_state.se_data_stuck)
        df_se_data = st.session_state.se_data_stuck.copy()
        #TODO when update and rerun get rfl_list again
        if 'rfl_list' not in st.session_state:
            df1=sql.posgre_get_rfl(
                    st.session_state['selectoption1'],
                    st.session_state['selectoption2'],
                    st.session_state['selectoption3'],
                    st.session_state['selectoption4'],
                    st.session_state['selectoption5']
                )
                
            st.session_state.rfl_list = df1
        df_rfl_data = st.session_state.rfl_list.copy()
        df_rfl_performance_c = df_rfl_data.loc[:, 'c_r_wp']
        df_rfl_performance_s = df_rfl_data.loc[:, 's_r_wp']
        df_rfl_performance = pd.concat([df_rfl_performance_c, df_rfl_performance_s])
        performance_list = df_rfl_performance.drop_duplicates().dropna().values.tolist()
        performance_list = [x for x in performance_list if x not in ['PWT(燃費電費)','PWT']]
        if 'df_display_on_summary' not in st.session_state:
            #必要なRFLの情報取得 けどここにいる時点でrfl_listは絶対にある
            # st.write(st.session_state.rfl_list)

            #se_data_stuckを必要なデータだけに加工
            
            #ここで複数プロジェクトとか複数フェーズある場合は一度対応しない
            # st.write('aaaa')
            project_cols =df_se_data.loc[:, df_se_data.columns.str.contains(';project_id;') ].columns 
            df_project_cols = df_se_data.loc[0,project_cols].values
            phase_cols =df_se_data.loc[:, df_se_data.columns.str.contains(';phase_id;') ].columns 
            df_phase_cols = df_se_data.loc[0,phase_cols].values
            # st.write(st.session_state['selectoption1'])
            # st.write(st.session_state['selectoption2'])
            # st.write(st.session_state['selectoption3'])
            # st.write(df_se_data)
            # st.write(phase_cols)
            # st.write(df_phase_cols)
            # st.write(df_project_cols)
            df_project_phase_combine = df_project_cols.astype(str) + "_" + df_phase_cols.astype(str)
            # st.write(df_project_phase_combine)
            if len(set(df_project_phase_combine.tolist())) >= 2:
                st.error('サマリーモードは単一プロジェクト、単一フェーズまでしか対応させていません')
                return
            #SEのパラメータ情報を取得、一列あればよい
            se_parameter_id_col = df_se_data.loc[:, df_se_data.columns.str.contains(';se_parameter_id;')].columns
            se_parent_col = df_se_data.loc[:, df_se_data.columns.str.contains(';z_parent_paraitem;')].columns
            se_child_col = df_se_data.loc[:, df_se_data.columns.str.contains(';z_child_paraitem;')].columns
            se_unit_col = df_se_data.loc[:, df_se_data.columns.str.contains(';z_unit;')].columns
            df_se_parameter_id = df_se_data.loc[:, se_parameter_id_col[0]]
            df_se_parent = df_se_data.loc[:, se_parent_col[0]]
            df_se_child = df_se_data.loc[:, se_child_col[0]]
            df_se_unit  = df_se_data.loc[:, se_unit_col[0]]
            #各バリエーションごとの列を取得
            #山口　全Veriationではなく、ユーザー選択で列を選ばせる
            
            se_variation_col = df_se_data.loc[:, df_se_data.columns.str.contains(';z_wp_name_get_str;') & df_se_data.columns.str.contains(str(selected_variation), regex=False) ].columns #
            se_value_col = df_se_data.loc[:, df_se_data.columns.str.contains(';z_request_median;') & df_se_data.columns.str.contains(str(selected_variation), regex=False)].columns #山口　regex=Falseにしないと、Variation名に正規表現記号が入ってきたときに正しく判定できない。4/10
            
            df_se_variation = df_se_data.loc[:, se_variation_col]
            df_se_value = df_se_data.loc[:, se_value_col]
            # st.write(df_se_data.loc[:, df_se_data.columns.str.contains(selected_variation)])
            # st.write("G仕様(BAT88)")
            # st.write(pd.DataFrame(['aaa'], columns=["G仕様(BAT88)"]).columns)
            # st.write(pd.DataFrame(['aaa'], columns=["G仕様(BAT88)"]).columns.str.contains("G仕様(BAT88)", regex=False)) im mad
            # st.write(df_se_variation)
            # st.write(df_se_value)
            df_se_info = pd.concat([df_se_parameter_id, df_se_parent, df_se_child, df_se_unit, df_se_variation, df_se_value], axis=1)
            
            df_se_info.rename(columns={df_se_info.columns[0]:'se_parameter_id', df_se_info.columns[1]:'parameter_name_1', df_se_info.columns[2]:'parameter_name_2', df_se_info.columns[3]:'parameter_unit'}, inplace=True)
            #variationごとのz_request_median列も改名
            for i, variation in enumerate(variations):
                # st.write(variations)
                df_se_info.rename(columns={df_se_info.columns[4+i]:variation,df_se_info.columns[4+len(variations)+i]:variation + '_value'}, inplace=True)
            
            #山口　縦軸のunitが離れて表示されていることを防ぐため、parameter_name_1で並べ替える 4/16
            parameter_name_1s = df_se_info['parameter_name_1'].drop_duplicates().tolist()
            parameter_name_map = {}
            for i, v in enumerate(parameter_name_1s):
                parameter_name_map[v] = i

            df_se_info['index_by_parameter_name_1'] = df_se_info['parameter_name_1'].map(parameter_name_map)
            df_se_info = df_se_info.sort_values(by='index_by_parameter_name_1')



            #rfl_listを必要なデータだけに加工 まずハ車両まで　　　システムも観ないと何も表示されない 
            # st.write(performance_list)
            # 性能リストの数横連結しないと
            df_rfl_info = None
            for i, performance in enumerate(performance_list):
                #TODO ほんとに全部c_r_wpでいいんだっけ？確認する
                df_rfl_by_performance_c = df_rfl_data[df_rfl_data['c_r_wp']==performance].loc[:, ['c_r_pj_id', 'c_phase_id', 'c_rfl_id','c_r_wp', 'c_related_se_parameter_id', 'c_logic', 'c_l_scene', 'c_flag_to', 'c_to_solving_value', 'c_flag_display_on_summary_logic' ]]
                df_rfl_by_performance_s = df_rfl_data[df_rfl_data['c_r_wp']==performance].loc[:, ['s_r_pj_id', 's_phase_id', 's_rfl_id','c_r_wp', 's_related_se_parameter_id', 's_logic', 's_l_scene', 's_flag_to', 's_to_solving_value', 's_flag_display_on_summary_logic']]
                df_rfl_by_performance_u = df_rfl_data[df_rfl_data['c_r_wp']==performance].loc[:, ['u_r_pj_id', 'u_phase_id', 'u_rfl_id','c_r_wp', 'u_related_se_parameter_id', 'u_logic', 'u_l_scene', 'u_flag_to', 'u_to_solving_value', 'u_flag_display_on_summary_logic']]
                df_rfl_by_performance_c.columns = ['project_id', 'phase_id', 'rfl_id','performance', 'related_se_parameter_id', 'logic', 'scene', 'flag_to', 'to_solving_value', 'flag_display_on_summary_value']
                df_rfl_by_performance_s.columns = ['project_id', 'phase_id', 'rfl_id','performance', 'related_se_parameter_id', 'logic', 'scene', 'flag_to', 'to_solving_value', 'flag_display_on_summary_value']
                df_rfl_by_performance_u.columns = ['project_id', 'phase_id', 'rfl_id','performance', 'related_se_parameter_id', 'logic', 'scene', 'flag_to', 'to_solving_value', 'flag_display_on_summary_value']
                df_rfl_by_performance = pd.concat([df_rfl_by_performance_c,df_rfl_by_performance_s,df_rfl_by_performance_u])
                
                
                # st.write(len(df_rfl_by_performance_c))
                if len(df_rfl_by_performance_c)==0:#車両階層のないRFLはこのループに入る
                    df_rfl_by_performance_s = df_rfl_data[df_rfl_data['s_r_wp']==performance].loc[:, ['s_r_pj_id', 's_phase_id', 's_rfl_id','s_r_wp', 's_related_se_parameter_id', 's_logic', 's_l_scene', 's_flag_to', 's_to_solving_value', 's_flag_display_on_summary_logic']]
                    df_rfl_by_performance_u = df_rfl_data[df_rfl_data['s_r_wp']==performance].loc[:, ['u_r_pj_id', 'u_phase_id', 'u_rfl_id','s_r_wp', 'u_related_se_parameter_id', 'u_logic', 'u_l_scene', 'u_flag_to', 'u_to_solving_value', 'u_flag_display_on_summary_logic']]
                    df_rfl_by_performance_s.columns = ['project_id', 'phase_id', 'rfl_id','performance', 'related_se_parameter_id', 'logic', 'scene', 'flag_to', 'to_solving_value', 'flag_display_on_summary_value']
                    df_rfl_by_performance_u.columns = ['project_id', 'phase_id', 'rfl_id','performance', 'related_se_parameter_id', 'logic', 'scene', 'flag_to', 'to_solving_value', 'flag_display_on_summary_value']
                    df_rfl_by_performance = pd.concat([df_rfl_by_performance_s,df_rfl_by_performance_u])
                    
                
                df_rfl_by_performance.columns = df_rfl_by_performance.columns + '_' + performance# st.write(df_rfl_by_performance_c)
                

                #山口　URLがあった時の処理、httpから始まる文字列がある場合にそれを分割して新規列に格納する 4/17
                df_logic_url_split = df_rfl_by_performance['logic_' + performance].str.split('http', expand=True)
                if len(df_logic_url_split.iloc[0])>=2:
                    df_rfl_by_performance['logic_url_' + performance] = 'http' + df_logic_url_split.iloc[:,1]
                else :
                    df_rfl_by_performance['logic_url_' + performance] = None
                df_rfl_by_performance['logic_' + performance] = df_logic_url_split.iloc[:,0]

                df_se_info = pd.merge(df_se_info, df_rfl_by_performance, how='left',left_on='se_parameter_id', right_on='related_se_parameter_id_'+performance)
                #山口　TOサマリ経由実行のため,選択用のふらぐ列を追加する 4/14 logicが入っていない場合はNoneを入れたい 4/14
                df_se_info['flag_selected_' + performance] = df_se_info['logic_' + performance].isna()
                df_se_info['flag_selected_' + performance] = df_se_info['flag_selected_' + performance].replace(True,None)

                #下記valueが同じものをまとめる操作のため,各性能のlogicをまとめた行を用意しておく
                if i==0:
                    df_se_info['logic_concat_' + performance] = df_se_info['logic_'+performance].fillna('')
                else:
                    df_se_info['logic_concat_' + performance] = df_se_info['logic_concat_' + performance_list[i-1]] + '_' + df_se_info['logic_'+performance].fillna('')
                    df_se_info.drop('logic_concat_'+ performance_list[i-1], inplace=True, axis=1)
                if i == len(performance_list) - 1: #ループの最終出会った場合、その時点のlogic_concatを改名する
                    # st.write('final_row')
                    df_se_info['logic_concat'] = df_se_info['logic_concat_' + performance ]
                    df_se_info.drop('logic_concat_'+ performance, inplace=True, axis=1)

            #上記Forが終わるともうSEとRFLの結合できている
            # st.write(df_se_info)
            #まとめに欲しい行だけにまとめる　まとめるだけでなく、このIDの順番に並べ替えたい4/18
            summary_ids = [576, 577, 597, 598, 603,604, 613, 614, 615, 616, 762, 624,625, 626,630,637,636,651, 658, 657, 672, 707, 697 ]
            df_se_info = df_se_info[df_se_info['se_parameter_id'].isin(summary_ids)]
            summary_ids_map = {}
            for i, v in enumerate(summary_ids):
                summary_ids_map[v] = i
            df_se_info['index_by_se_parameter_id'] = df_se_info['se_parameter_id'].map(summary_ids_map)
            df_se_info = df_se_info.sort_values(by='index_by_se_parameter_id')

            #ほしい行に絞っても、複数シーンから割りつけられているなどのケースで、複数行同じSE項目が表示されてしまうことがある。
            #logicが複数行で同じであるなら、まとめて表示でよい
            #logicが違うのであればflag_display_on_summary_logicが1となっているものをDFに残す
            #ここでまとめられる前のDFは残しておく

            #df_se_infoに合算版flag_display_on_symmaryを追加する
            df_se_info['summary_selected'] = df_se_info.iloc[:, df_se_info.columns.str.contains('project_id')].isna().all(axis=1) | df_se_info.iloc[:,df_se_info.columns.str.contains('flag_display_on_summary')].fillna(True).all(axis=1) # 山口　もともと各行で一つでもTrueがあればTrueであったが、それだとほかの行をTrueにしたかったときに比もずれてしまうため、全部Ｔｒｕｅだった時に変更 4/21
            # st.write(df_se_info['summary_selected'])
            st.session_state.df_display_on_summary = df_se_info 
        else:
            df_se_info = st.session_state.df_display_on_summary
        df_to_summary = df_se_info.copy()
        df_to_summary.drop_duplicates(subset=['se_parameter_id', 'logic_concat'], inplace=True)
        # st.write(df_rfl_data)
        #山口 サマリ専用昨日たちの整列 4/14
        summary_col1, summary_col2, summary_col3 = st.columns([1,1,10])
        #サマリー表示行を編集さセルための機能追加
        with summary_col1:
                #dia.select_display_on_summary() 山口　ここに置くとAggridに通す前のDFを対象に変更をかけてしまう。ここではフラグを立てるにとどめてグリッド表示後に実行する
            flag_summary_edit_display = st.button('サマリー表示行選択')
        with summary_col2:#山口　サマリーからRFL編集機能を作る4/14
            flag_edit_rfl_by_to_summary = st.button('RFL更新',help='TOサマリーからRFLの内容を書き換えます')
        with summary_col3:
            if st.button('ステートメント記入'):
                dia.insert_to_statement()
        #
        #summary_selectedフラグFalseをのぞく DONE Falseでも、その大項目、小項目内で一つもTrueがないとき、一番上の行を強制的に残す
        df_check_flag = df_to_summary.loc[:, ['se_parameter_id', 'parameter_name_2', 'summary_selected']].copy()
        df_check_flag = df_check_flag.groupby(['se_parameter_id', 'summary_selected'], as_index=False).count()    
        id_flag_false_list = df_check_flag[df_check_flag['summary_selected']==False]['se_parameter_id'].tolist()
        id_flag_true_list = df_check_flag[df_check_flag['summary_selected']==True]['se_parameter_id'].tolist()
        id_not_in_true = set(id_flag_false_list) - set(id_flag_true_list) # これがTrueが一つもないse_parameter_idの一覧になる
        for se_id in id_not_in_true:
            df_to_summary.loc[df_to_summary[df_to_summary['se_parameter_id']==se_id].index[0], 'summary_selected'] = True 
        
        df_to_summary = df_to_summary[df_to_summary['summary_selected']]
        
        #st-aggridでspanningできないので、df_to_summaryを直接いじる
        df_to_summary.loc[df_to_summary['parameter_name_1'] == df_to_summary['parameter_name_1'].shift(),'parameter_name_1'] = ''

        #########
        #ステートメントの表示をする
        if not st.session_state.df_to_statement.empty:
            to_statement = st.session_state.df_to_statement.iloc[0]['statement']
            update_day = st.session_state.df_to_statement.iloc[0]['update_day']
            statement_with_line_breaks = to_statement.replace('\n', '<br>')
            if statement_with_line_breaks:
                st.markdown(
                    f'<div style="font-size:25px; line-height:1.6; font-weight:bold; text-decoration:underline;">ステートメント ({update_day}時点) </div>',
                    unsafe_allow_html=True
                )
                st.markdown(
                    f'<div style="font-size:25px; line-height:1.6;">{statement_with_line_breaks}</div>',
                    unsafe_allow_html=True
                )
        


        # st.write(df_to_summary)
        BGcolorRenderer=JsCode("""
            function (params) {
            const performance = params.column.colDef.headerName;
            const flag_to = params.data['flag_to_' + performance];
            const to_solving_value = params.data['to_solving_value_' + performance];
                               
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
            } else if (flag_to === 1){
                console.log('flag is one');
                if (to_solving_value === null){
                    console.log('not solved');
                    return { backgroundColor: 'lightcoral', "font-size": '150%', 'font-family': 'Verdana, sans-serif' };        
                } else {
                    return { backgroundColor: 'rag-green-outer', "font-size": '150%', 'font-family': 'Verdana, sans-serif'};               
                }
            } 
            return {"font-size": '150%', 'font-family': 'Verdana, sans-serif'};
        }
        """)
        BorderRenderer=JsCode("""
            function (params) {
            return {'color': ''}                  
            }
        """)
        #4/15 値がNull=RFL項目のないセルは編集させない
        EditableValue=JsCode("""
            function (params){
                console.log(params.data);
                if (params.data === null){
                    return false;
                } else{
                    return true;
                }
            }
        """)
        #gridoption作って表示
        go_to_summary = {
            'columnDefs': [
                # {'field': 'se_parameter_id' },
                {
                 'headerName':'大項目',
                 'field': 'parameter_name_1',
                 'headerClass':'logic_to_summary',
                 'cellStyle':{"background-color": "#FFCCFF"},
                 'width': '140',
                 'pinned':'left'
                 }, #spanRows:大項目を'セルを結合'するイメージ
                {
                 'headerName':'小項目',
                 'field': 'parameter_name_2',
                 'headerClass':'logic_to_summary',
                 'cellStyle':{"background-color": "#FFCCFF"},
                 'pinned':'left'
                 },
                {
                 'headerName':'単位',
                 'field': 'parameter_unit',
                 'headerClass':'logic_to_summary',
                 'cellStyle':{"background-color": "#FFCCFF"}, 
                 'pinned':'left',
                 'width': 100
                 }
            ],
            'defaultColDef': {
                'resizable': True,
                "enableValue": True,
                'rowBorder': BorderRenderer,
                
                'cellStyle':{"font-size": '25px', 'font-weight': 'normal', 'font-family': 'Verdana, sans-serif'},
                'autoHeight': True,
                "filter": True
                
            },
            'rowHeight': 50,
            'headerHeight':50,
            'enableRangeSelection':True,

        }
        #seのvariationごとにcolumnDefs追加
        for variation in variations:
            se_column_def  = {'headerName':variation,
                              'field':variation + '_value',
                            'headerClass':'se_to_summary',
                            'pinned':'left'
                            }
            
        go_to_summary['columnDefs'].append(se_column_def)
        #R性能ごとにcolumnDefs追加
        for performance in performance_list:
            # st.write(performance)
            rfl_column_def = {'headerName':performance,
                              'field':'logic_'+performance, 
                              'headerClass':'requirements_to_summary', 
                              'cellStyle':BGcolorRenderer,
                              'editable': EditableValue,  
                              'wrapText': True}
            rfl_flag_to_column_def = {
                              'headerName':'flag_to_' + performance,
                              'field':'flag_to_' + performance, 
                              'headerClass':'requirements_to_summary', 
                              'cellStyle':BGcolorRenderer,
                              'hide':True,
                              'wrapText': True}
            rfl_to_solving_value_column_def = {
                              'headerName':'to_solving_value_' + performance,
                              'field':'to_solving_value_' + performance, 
                              'headerClass':'requirements_to_summary', 
                              'cellStyle':BGcolorRenderer,
                              'hide':True,
                              'wrapText': True}
            #山口 選択用フラグ列をここで表示させる 4/15
            rfl_flag_select_def = {
                              'headerName':'編集_' + performance,
                              'field':'flag_selected_' + performance, 
                              'headerClass':'requirements_to_summary', 
                              'cellStyle':BGcolorRenderer,
                              'wrapText': True,
                              'editable': True,         
                              'cellRenderer': 'agCheckboxCellRenderer',
                              'cellEditor': 'agCheckboxCellEditor', 
                              'width':40}
            go_to_summary['columnDefs'].append(rfl_flag_select_def)
            go_to_summary['columnDefs'].append(rfl_column_def)
            go_to_summary['columnDefs'].append(rfl_flag_to_column_def)
            go_to_summary['columnDefs'].append(rfl_to_solving_value_column_def)

        #テスト用
        # df_to_summary['flag_to_動力'] = 1    
        # st.write(df_to_summary)
        ag_edited = AgGrid(df_to_summary,go_to_summary,
                custom_css=css_ag,
                height=1000,
                allow_unsafe_jscode=True,
                update_on='GridUpdateMode.VALUE_CHANGED'
                )
        df_edited = ag_edited['data']
        # st.write(df_edited)
        # st.write(st.session_state.df_display_on_summary)
        if flag_summary_edit_display:
            dia.select_display_on_summary()
        if flag_edit_rfl_by_to_summary:#山口　更新機能4/14
            #選択された性能とindexを取得
            df_flag_selecteds = df_edited.loc[:, df_edited.columns.str.contains('flag_selected_')]
            selected_pos = [[index, col] for index in df_flag_selecteds.index for col in df_flag_selecteds.columns if df_flag_selecteds.at[index, col]]

            #選択されたセルのproject_id, phase_id, rflid, 更新値をまとめる
            df_selecteds = None
            for pos in selected_pos:
                index = pos[0]
                column = pos[1]
                se_parameter = df_edited.at[index, 'parameter_name_2']
                performance = column.replace('flag_selected_', '')
                project_id = df_edited.at[index, 'project_id_'+performance]
                phase_id = df_edited.at[index, 'phase_id_'+performance]
                rfl_id = df_edited.at[index, 'rfl_id_'+performance]
                value = df_edited.at[index, 'logic_'+performance]
                value_url = df_edited.at[index, 'logic_url_'+performance] #山口 分割したURL情報はupdate時にくっつけるため　
                df_selected = pd.DataFrame([[se_parameter, performance, project_id, phase_id, rfl_id, value,  value_url]], columns=['se_parameter', 'performance', 'project_id', 'phase_id', 'rfl_id', 'value', 'value_url'])
                if df_selecteds is None:
                    df_selecteds = df_selected.copy()
                else:
                    df_selecteds = pd.concat([df_selecteds,df_selected])
            if df_selecteds is not None:
                dia.update_rfl_by_to_summary(df_selecteds)
            
            







        

     
if __name__ == "__main__":
    main()