"""
Summary: 
    rfl_df加工用関数
Functions:
    get_dataframes : sessionのdataframeを取得
    compare_dataframes : 編集したデータの差分を検出
Author:
    Telema Tanaka
Created:
    2025-02-13
"""

import streamlit as st
from  module.utils import get_matching_key

class RFLDataProcesser:

    @classmethod
    def get_dataframe(cls,key):
        df = st.session_state[key]
        return df
    
    @classmethod
    def compare_dataframes(cls,org_key,edit_key):
        rfl_df_org = cls.get_dataframe(org_key)
        rfl_df_edit = cls.get_dataframe(edit_key)
        
        changes = (rfl_df_org != rfl_df_edit).stack()
        # true だけ取得
        diff_bool = changes[changes]
        
        # 差分のあるインデックスとカラムを取得
        diff_cells = [(idx,col) for idx,col in diff_bool.index]
        return diff_cells
        
        