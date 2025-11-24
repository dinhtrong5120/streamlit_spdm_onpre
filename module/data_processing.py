"""
Summary:
    RFLデータ操作関数
Attributes:
    DiffData : -
    RFLDataProcesser: 編集差分検出クラス
Author:
    Telema Tanaka
Created:
    2025-02-13
"""

import streamlit as st
from  module.utils import get_matching_key
import numpy as np
import math
import re
import pandas as pd #telema-kyaw rfl_update 8/22
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Alignment, Font
from st_aggrid import AgGrid, GridOptionsBuilder
import module.excel.excel_hierarchical_style as hr_styles
from module.excel.excel_hierarchical_export import create_hierarchical_excel_data
from db.rfl_repository import RFLRepository as rflq

class DiffData:
    def __init__(self,project_id,rfl_id,phase_id,diff_col,diff_value):
        self.data = {
            'project_id': project_id,
            'rfl_id': rfl_id,
            'phase_id': phase_id,
            'diff_col': diff_col,
            'diff_value': diff_value
        }

class RFLDataProcesser:

    @classmethod
    def get_dataframe(cls,key):
        """sessionのdataframeを取得

        Args:
            key (string): session Key

        Returns:
            _type_: DataFrame
        """
        df = st.session_state[key]
        return df

    @classmethod
    def compare_dataframes(cls,org_key,edit_key):
        """編集したデータの差分を検出

        Args:
            org_key (string): 元データキー
            edit_key (string): 編集データキー

        Returns:
            _type_: DataFrame
        """
        diff = []

        # df読み込み
        rfl_df_org = cls.get_dataframe(org_key)
        rfl_df_edit = cls.get_dataframe(edit_key)

        # indexリセット
        rfl_df_org = rfl_df_org.reset_index(drop=True)
        rfl_df_edit = rfl_df_edit.reset_index(drop=True)

        # NaNを削除
        rfl_df_org = rfl_df_org.fillna("")
        rfl_df_edit = rfl_df_edit.fillna("")

        # 階層毎のPJIDを正規表現で取得
        # indexが返るが、PJIDは1グリッドに1つもつという前提の為、スカラー値を指定
        project = rfl_df_org.filter(regex=r'^[a-zA-Z]+_r_pj_id$').columns[0]

        #telema-kyaw rfl_update 8/22
        datetime_suffixes = ['sender_date', 'receiver_date']  # Add more if needed

        # 各セルの差分を取得
        for col in rfl_df_org:

            for idx in range(len(rfl_df_org)):
                org_value = rfl_df_org.at[idx,col]
                edit_value = rfl_df_edit.at[idx,col]

                #telema-kyaw rfl_update 8/22
                if any(col.endswith(suffix) for suffix in datetime_suffixes):
                    # Convert both values to datetime.date or None
                    org_dt = pd.to_datetime(str(org_value), errors='coerce')
                    edit_dt = pd.to_datetime(str(edit_value), errors='coerce')

                    org_value = org_dt.date() if pd.notna(org_dt) else None
                    edit_value = edit_dt.date() if pd.notna(edit_dt) else None

                    print(f"  org_value: {org_value} (type: {type(org_value)})")
                    print(f"  edit_value: {edit_value} (type: {type(edit_value)})")

                if org_value != edit_value:
                    project_id = int(rfl_df_org.loc[idx,project])
                    rfl_id = int(rfl_df_org.loc[idx,'rfl_id'])
                    phase_id = int(rfl_df_org.loc[idx,'ph_id'])
                    edit_value = str(edit_value)
                    db_col = re.sub(r'^._',"",col)
                    diff.append(DiffData(project_id,rfl_id,phase_id,db_col,edit_value).data)

        return diff
    
#telema-kyaw rfl_update 8/22
def strip_prefix(name):
    for prefix in ['c_', 's_', 'u_']:
        if name.startswith(prefix):
            return name[len(prefix):]
    return name

def create_rfl_common_col(header_name,field,headerClass,filter=True,minWidth=300,editable = False, valueFormatter=None):
    """共通カラムオプションを作成
    Args:
        header_name (string): 列名
        field (string): dfの列名
        headerClass (string): color設定
        filter (bool): _description_. Defaults to True.
        minWidth (int): _description_. Defaults to 100.
        edit_state (bool): _description_. editableStatus : R~L値、Noteのみ動的に決定

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

def format_grid(base_df):

    for i in range(1,4):
        prefix = f'hr{i}_'
        base_df.loc[base_df[f'{prefix}wp'] == base_df[f'{prefix}wp'].shift(),f'{prefix}wp'] = ''
        base_df.loc[base_df[f'{prefix}r_item'] == base_df[f'{prefix}r_item'].shift(),f'{prefix}r_item'] = ''
        base_df.loc[base_df[f'{prefix}req'] == base_df[f'{prefix}req'].shift(),f'{prefix}req'] = ''
        mask_r_scene = base_df[f'{prefix}r_scene'] == base_df[f'{prefix}r_scene'].shift()

        base_df.loc[
            (base_df[f'{prefix}r_item'].isna() | (base_df[f'{prefix}r_item'] == '')) & mask_r_scene,
            f'{prefix}r_scene'
        ] = ''

        base_df.loc[base_df[f'{prefix}f_item'] == base_df[f'{prefix}f_item'].shift(),f'{prefix}f_item'] = ''
        base_df.loc[base_df[f'{prefix}func'] == base_df[f'{prefix}func'].shift(),f'{prefix}func'] = ''

        base_df.loc[base_df[f'{prefix}l_item'] == base_df[f'{prefix}l_item'].shift(),f'{prefix}l_item'] = ''
        base_df.loc[base_df[f'{prefix}logic'] == base_df[f'{prefix}logic'].shift(),f'{prefix}logic'] = ''

        mask_l_scene = base_df[f'{prefix}l_scene'] == base_df[f'{prefix}l_scene'].shift()

        # Check if l_item is not None (or NaN) and both masks are True
        base_df.loc[
            (base_df[f'{prefix}l_item'].isna() | (base_df[f'{prefix}l_item'] == '')) & mask_l_scene,
            f'{prefix}l_scene'
        ] = ''

        # 承認の重複を削除
        check_cols = [f'{prefix}r_item',f'{prefix}f_item',f'{prefix}l_item']
        target_cols = [f'{prefix}sender_judge',f'{prefix}sender_name',f'{prefix}sender_date',f'{prefix}sender_comment',
                       f'{prefix}receiver_judge',f'{prefix}receiver_name',f'{prefix}receiver_date',f'{prefix}receiver_comment',
                       f'{prefix}note']
        mask = (base_df[check_cols] == '').all(axis=1)

        # 対象の列に一括代入
        base_df.loc[mask, target_cols] = ''

    base_df =base_df.sort_values(by=['hr1_rfl_index'])


    return base_df

def create_rfl_grid_excel_data():
    hr = st.session_state.selected_hr[0]
    wp = st.session_state.wp[0]
    project = st.session_state.selectoption1[0]
    phase = st.session_state.selectoption5[0]
    print('hr: ',hr)
    print('wp: ',wp)
    print('project: ',project)
    print('phase: ',phase)
    # # 車両性能抽出
    # if hr == 'システム' or hr == 'ユニット':
    #     wp_para = rflq.get_r_tree_from_lower_hr(wp,project,hr)
    #     # st.write('wp_para: ',wp_para)
    #     wp_para = tuple(wp_para['hr1_wp'].drop_duplicates().tolist())
    #     # 下位階層からWPが見つからない場合、選択中WPで実行して空のIN()を回避
    #     if len(wp_para) == 0:
    #         wp_para = (wp,)
    # else:
    #     wp_para = (wp,)

    # base_df = rflq.get_hierarchical_rfl_grid(project,phase,wp_para)

    #Kyaw 10/07 Add start
    download_data_result = rflq.get_rfl_download_data(st.session_state.hierarchy,st.session_state.wp)
    # List of suffixes you want to kee
    suffixes = [
        'wp', 'r_item', 'req', 'r_unit', 'r_scene',
        'f_item', 'func', 'f_unit',
        'l_item', 'logic', 'l_unit', 'l_scene', 'note',
        'sender_judge', 'sender_name', 'sender_date', 'sender_comment',
        'receiver_judge', 'receiver_name', 'receiver_date', 'receiver_comment',
        'rfl_index'
    ]
    # Construct the list of desired columns
    desired_cols = []

    for prefix in ['hr1_', 'hr2_', 'hr3_']:
        for suffix in suffixes:
            col_name = prefix + suffix
            if col_name in download_data_result.columns:
                desired_cols.append(col_name)

    # Create new DataFrame with just those columns
    excel_export_df = download_data_result[desired_cols].copy()
    #Kyaw 10/07 Add end

    # base_df = format_grid(base_df)
    base_df = format_grid(excel_export_df)
    bef_idx = 0
    dfs = []
    for i in range(1,4):
        end_idx = base_df.columns.get_loc(f'hr{i}_rfl_index')
        df_part = base_df.iloc[:, bef_idx:end_idx + 1]
        dfs.append(df_part)
        bef_idx = end_idx + 1

    def column_replace(col_name, dict):
        for old, new in dict.items():
            col_name = col_name.replace(old,new)
        return col_name

    replace_dict = {
        'hr1': 'c',
        'hr2': 's',
        'hr3': 'u'
    }

    df1,df2,df3 = dfs
    df1.rename(columns=lambda x: column_replace(x,replace_dict),inplace=True)
    df2.rename(columns=lambda x: column_replace(x,replace_dict),inplace=True)
    df3.rename(columns=lambda x: column_replace(x,replace_dict),inplace=True)

    df_all = pd.concat([df1, df2,df3], axis=1)
    meta_info = {
        'PROJECT' : st.session_state.selectoption1[0],
        'PT_TYPE' : st.session_state.architecture_name[0],
        'Lot' : st.session_state.selectoption4[0],
        'Phase' : st.session_state.selectoption5[0],
    }
    df1 = df1.drop(columns='hr1_prj_rfl',errors='ignore')
    df1 = df1.drop(columns='c_rfl_index',errors='ignore')
    df2 = df2.drop(columns='s_rfl_index',errors='ignore')
    df3 = df3.drop(columns='u_rfl_index',errors='ignore')

    df1 = df1.astype('object')
    df1 = df1.where(pd.notna(df1), None)

    df2 = df2.astype('object')
    df2 = df2.where(pd.notna(df2), None)

    df3 = df3.astype('object')
    df3 = df3.where(pd.notna(df3), None)


    grid_margin = hr_styles.MARGIN_COL
    init_col = hr_styles.INITIAL_COL

    system_col_loc = init_col + df1.shape[1]+ grid_margin
    unit_col_loc = system_col_loc + df2.shape[1] + grid_margin
    df1_grid = hr_styles.GridBlock(init_col)
    df2_grid = hr_styles.GridBlock(system_col_loc)
    df3_grid = hr_styles.GridBlock(unit_col_loc)

    excel_data1 = create_hierarchical_excel_data(df1,df1_grid,meta_info=meta_info,wp=wp)
    excel_data2 = create_hierarchical_excel_data(df2,df2_grid,wb=BytesIO(excel_data1),meta_info=None)
    excel_data3 = create_hierarchical_excel_data(df3,df3_grid,wb=BytesIO(excel_data2),meta_info=None)

    return excel_data3

