import streamlit as st
from module.PsqlModule import psql_class
import datetime
import pandas as pd
import numpy as np
from Aras_connect.Middle import IFtoARAS
import const.constpara as co
noData = ["-","－","﹣","‐","⁃­","‑","−","˗","‒","–","—","﹘","―","⎯","⏤","─","ｰ","ー","一"]
now = datetime.datetime.now()
sql = psql_class()
username = st.session_state.username
password = st.session_state.password
index_list = ['z_parent_paraitem', 'z_child_paraitem', 'z_unit']
aras = IFtoARAS("GWE00199", "GWE00199", co.ARASURL, co.ARASDB)

def get_design_file(design_id):
    if isinstance(design_id, dict) :#and design_id != "":
        tmp = aras.get_file_id(design_id)
    elif np.isnan(design_id):
        tmp = {}
    else:
        tmp = {}
    return tmp


def get_data():
    for i, prj in enumerate(st.session_state.prj_info):
        # 要求元WPが基本設計情報である前提パラメータだけに絞り込み
        prj_number = prj['z_number']
        df = pd.DataFrame(st.session_state.para_list)
        tbname_tb = sql.table_date()

        df = pd.merge(
                    df,
                    tbname_tb,
                    how='inner',
                    on=['z_paravalueid'])

        Existence = sql.updated_data_Existence(now)

        if not Existence.empty:
            # df['update_time'] = pd.to_datetime(df['update_time'])

            # update_time列で遅い時刻順に並び替え
            Existence = Existence.sort_values(by='update_day', ascending=False)
            combined_df = pd.concat([Existence, df])
            # 重複削除（上のレコードを優先）
            combined_df = combined_df.drop_duplicates(subset='z_paravalueid', keep='first')
            combined_df['numeric_part'] = combined_df['z_paravalueid'].str.extract('(\d+)', expand=False).astype(int)
            df = combined_df.sort_values(by='numeric_part').drop(columns='numeric_part')

        para = df.loc[df['z_prj_number'] == prj_number]
        para.loc[para['z_wp_name_get_str'].isin(noData),'z_wp_name_get_str'] = noData[0]
        val_scene = para['z_wp_name_get_str'].unique()
        val_scene = np.delete(val_scene, np.where(np.isin(val_scene, noData)))
        val_scene = np.sort(val_scene)

        if len(val_scene) == 0:
            para2 = para
            para2.columns = [
                prj_number + ';' + col + ';'
                if col not in index_list else col
                for col in para2.columns
            ]
        for j, val_sc in enumerate(val_scene):
            _para = para.loc[para['z_wp_name_get_str'].isin([val_sc, noData[0]])]
            _para.columns = [
                prj_number + ';' + col + ';' + val_sc
                if col not in index_list else col
                for col in _para.columns
            ]
            if j == 0:
                para2 = _para
            else:
                para2 = pd.merge(
                    para2,
                    _para,
                    how='outer',
                    on=index_list
                )

        if i == 0:
            st.session_state.se_data_stuck = para2
        else:
            st.session_state.se_data_stuck = pd.merge(
                st.session_state.se_data_stuck,
                para2,
                how = 'outer',
                on=index_list
            )

