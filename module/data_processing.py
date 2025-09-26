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
        # 各セルの差分を取得
        for col in rfl_df_org:

            for idx in range(len(rfl_df_org)):
                org_value = rfl_df_org.at[idx,col]
                edit_value = rfl_df_edit.at[idx,col]

                if org_value != edit_value:
                    project_id = int(rfl_df_org.loc[idx,project])
                    rfl_id = int(rfl_df_org.loc[idx,'rfl_id'])
                    phase_id = int(rfl_df_org.loc[idx,'ph_id'])
                    edit_value = str(edit_value)
                    db_col = re.sub(r'^._',"",col)
                    diff.append(DiffData(project_id,rfl_id,phase_id,db_col,edit_value).data)

        return diff