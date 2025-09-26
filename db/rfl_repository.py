import pandas as pd
import psycopg2
from psycopg2 import OperationalError, InterfaceError, sql
import re
import const.constpara as co
from sqlalchemy import create_engine, text
import datetime
import streamlit as st
st.session_state.username = 'ELR00028'
from db.db_connection import DBConnection as DBCon
from queries import rfl_pj_select as pj_select_query
# from query_builder import QueryBuilder as qb
from queries import rfl_select as rfl_select_query,rfl_update as rfl_update_query

class RFLRepository:

    @staticmethod
    def get_data(query,params=None):
        conn = DBCon(autocommit=False)
        try:
            with conn.cursor() as cur:
                if params:
                    cur.execute(query,params)
                else:
                    cur.execute(query)
                return cur.fetchall()
        except Exception as e:
            print(e)

    @staticmethod
    def generate_query(query_key,*params):
        query = pj_select_query(query_key)
        result = RFLRepository.get_data(query,params)
        return result

    @staticmethod
    def posgre_get_rfl(select_list = [], select_list2 = [], select_list3 = [],select_list4 = [],select_list5 = [],select_list6 = [],select_list7 = []):
        """連結させたPRJ_RFLを取得

        Args:
            args (string,string,string,string): ダイアログ選択メタ情報
        Returns:
            dataframe: クエリ取得結果
        Author:
            Telema Tanaka
        Created:
            2025/01/28
        Updated:
            2025/02/14
                Phase追加
                階層連結から階層毎の表示に仕様変更
        """


        select_list_str6 = ', '.join(f"'{item}'" for item in select_list6)

        if select_list and select_list2 and select_list3  and select_list4 and select_list5 and select_list6 and select_list7:

            hierarchy = select_list_str6

            # 2025/02/18 Telema
            # 暫定で階層は単独選択に対応
            if hierarchy == "'車両'": prefix='v_'
            if hierarchy == "'システム'": prefix='s_'
            if hierarchy == "'ユニット'": prefix='u_'

            query = rfl_select_query.get_select_query('get_prj_rfl').format(prefix)

            with DBCon() as connection:
                result = pd.read_sql_query(query,connection,params=(
                            tuple(select_list),
                            tuple(select_list2),
                            tuple(select_list3),
                            tuple(select_list4),
                            tuple(select_list5),
                            tuple(select_list6),
                            tuple(select_list7))
                            )
                wp_column = f'{prefix}n_wp'
                next_wps = result[wp_column]
                st.session_state.wp_column = next_wps
                st.session_state.hierarchy = select_list_str6.strip("'")

                return result
        else:
            return []
    # -----Telema-----

    # -----Telema-----
    def posgre_get_rfl_tlm(select_list = [], select_list2 = [], select_list3 = [],select_list4 = [],select_list5 = [],select_list6 = [],select_list7 = []):
        """連結させたPRJ_RFLを取得

        Args:
            args (string,string,string,string): ダイアログ選択メタ情報
        Returns:
            dataframe: クエリ取得結果
        Author:
            Telema Tanaka
        Created:
            2025/05/19
        """

        with DBCon() as connection:
            # リストの要素をシングルクォートで囲んでカンマで結合
            select_list_str = ', '.join(f"'{item}'" for item in select_list)
            select_list_str2 = ', '.join(f"'{item}'" for item in select_list2)
            select_list_str3 = ', '.join(f"'{item}'" for item in select_list3)
            select_list_str4 = ', '.join(f"'{item}'" for item in select_list4)
            select_list_str5 = ', '.join(f"'{item}'" for item in select_list5)
            select_list_str6 = ', '.join(f"'{item}'" for item in select_list6)
            select_list_str7 = ', '.join(f"'{item}'" for item in select_list7)

            if select_list and select_list2 and select_list3  and select_list4 and select_list5 and select_list6 and select_list7:

                hierarchy = select_list_str6
                
                if hierarchy == "'車両'": prefix='c_'
                if hierarchy == "'システム'": prefix='s_'
                if hierarchy == "'ユニット'": prefix='u_'

                query = rfl_select_query.get_select_query('get_rfl_view_tlm').format(prefix)
                result = pd.read_sql_query(query,connection,params=(
                            tuple(select_list),
                            tuple(select_list2),
                            tuple(select_list3),
                            tuple(select_list4),
                            tuple(select_list5),
                            tuple(select_list6),
                            tuple(select_list7))
                            )
                wp_column = f'{prefix}n_wp'
                next_wps = result[wp_column]
                st.session_state.wp_column = next_wps
                st.session_state.tmp_hr = select_list_str6.strip("'")

                for role in ['sender','receiver']:
                    result[f'{prefix}{role}_selected'] = False

                return result

            else:
                return []
    # -----Telema-----

    @staticmethod
    def posgre_get_rfl_from_f(select_list = [], select_list2 = [], select_list3 = [],select_list4 = [],select_list5 = [],select_list6 = [],select_list7 = [],f_item = []):
            """Tree-Functionモードで、選択したノードのFunctionを連結させて取得

            Args:
                args (array,array,array,array,array,string): ダイアログ選択メタ情報
            Returns:
                dataframe: クエリ取得結果
            Author:
                Telema Tanaka
            Created:
                2025/03/12
            Updated:
            """

            # リストの要素をシングルクォートで囲んでカンマで結合
            select_list_str6 = ', '.join(f"'{item}'" for item in select_list6)


            if select_list and select_list2 and select_list3  and select_list4 and select_list5 and select_list6 and select_list7:

                hierarchy = select_list_str6

                if hierarchy == "'車両'": prefix='c_'
                if hierarchy == "'システム'": prefix='s_'
                if hierarchy == "'ユニット'": prefix='u_'
                query = rfl_select_query.get_select_query('get_rfl_view_tlm_from_f').format(prefix)

                with DBCon() as connection:
                    result = pd.read_sql_query(query,connection,params=(
                                tuple(select_list),
                                tuple(select_list2),
                                tuple(select_list3),
                                tuple(select_list4),
                                tuple(select_list5),
                                tuple(select_list6),
                                tuple(select_list7),
                                (f_item,))
                                )
                    wp_column = f'{prefix}n_wp'
                    next_wps = result[wp_column]
                    st.session_state.wp_column = next_wps
                    st.session_state.tmp_hr = select_list_str6.strip("'")

                    return result
            else:
                return []

    # -----Telema-----


    @staticmethod
    def get_hierarchy(project_code,phase):
        """階層を取得

        Args:
            project_code (int): プロジェクトコード
            phase (int): フェーズ
        Returns:
            list: 階層
        """
        if project_code == [] or phase == []:
            return None

        project_code = tuple(project_code)
        phase = tuple(phase)
        print(project_code)
        print(phase)
        query = rfl_select_query.get_select_query('get_hierarchy')
        print(query)
        with DBCon() as connection:
            result = pd.read_sql_query(query,connection,params=(project_code,phase))

            return result

    @staticmethod
    def get_wp(project_code,phase,hierarchy):
        """性能を取得

        Args:
            phase (int): フェーズ
            hierarchy (int): 階層
        Returns:
            list: 性能
        """

        project_code = tuple(project_code)
        phase = tuple(phase)
        hierarchy = tuple(hierarchy)
        query = rfl_select_query.get_select_query('get_r_wp')

        with DBCon() as connection:
            result = pd.read_sql_query(query,connection,params=(project_code,phase,hierarchy))

            return result

    @staticmethod
    def update_rfl(project_id,rfl_id,phase_id,diff_col,diff_value):
        """編集値をupdate

        Args:
            project_id (int): 複合主キー1
            rfl_id (int): 複合主キー2
            phase_id (int): 複合主キー3
            diff_col (string): 変更対象列
            diff_value (string/int): 編集値
        """
        if diff_col == 'req':
            diff_col = 'requirement'
        if diff_col == 'func':
            diff_col = 'function'    
        project_id = (project_id,)
        rfl_id = (rfl_id,)
        phase_id = (phase_id,)
        diff_value = (diff_value,)

        lock_query = rfl_select_query.get_select_query('lock_prj_rfl_for_update')
        update_query = rfl_update_query.get_update_query('update_edited_prj_rfl').format(diff_col)

        with DBCon(False) as connection:
            cur = connection.cursor()
            # 排他制御
            cur.execute(lock_query,(project_id,rfl_id,phase_id))
            # update
            cur.execute(update_query,(diff_value,project_id,rfl_id,phase_id))

    @staticmethod
    def get_wps(wp,hr):
        """階層繋がりの領域を取得

        Args:
            wp (_type_): 基準領域
            hr (_type_): 基準階層

        Returns:
            _type_: dataframe
        """
        if hr == '車両':
            query = rfl_select_query.get_select_query('get_wps_related_to_hr_from_hr1')
        if hr == 'システム':
            query = rfl_select_query.get_select_query('get_wps_related_to_hr_from_hr2')
        if hr == 'ユニット':
            query = rfl_select_query.get_select_query('get_wps_related_to_hr_from_hr3')
        with DBCon() as connection:
            result = pd.read_sql_query(query,connection,params=(wp,st.session_state.selectoption1[0]))
            return result

    @staticmethod
    def get_functions_on_related_wps(wp,hr):
        """階層繋がりの領域を取得

        Args:
            wp (str): 基準領域
            hr (str): 基準階層

        Returns:
            dataframe: dataframe
        """

        if hr == '車両':
            query = rfl_select_query.get_select_query('get_related_f_from_hr1')
        if hr == 'システム':
            query = rfl_select_query.get_select_query('get_related_f_from_hr2')
        if hr == 'ユニット':
            query = rfl_select_query.get_select_query('get_related_f_from_hr3')

        print(st.session_state.selectoption1[0])
        print(wp)
        with DBCon(False) as connection:
            result = pd.read_sql_query(query,connection,params=(wp,st.session_state.selectoption1[0]))
            print(wp)
            print(result)
            return result

    @staticmethod
    def get_all_wp_tree():
        query = rfl_select_query.get_select_query('get_all_wp_tree')

        with DBCon(False) as connection:
            df = pd.read_sql_query(query,connection)
            df = df.convert_dtypes()

            return df

    @staticmethod
    def get_all_vwp():
        query = rfl_select_query.get_select_query('get_all_vwp')

        with DBCon(False) as connection:
            df = pd.read_sql_query(query,connection)
            df = df.convert_dtypes()

            return df

    @staticmethod
    def get_wp_tree(vwp):
        query = rfl_select_query.get_select_query('get_wp_tree_s')

        with DBCon(False) as connection:
            df = pd.read_sql_query(query,connection,params=(vwp,))
            df = df.convert_dtypes()

            return df

    @staticmethod
    def get_selected_allocation(selected_vwp):
        placeholders = ','.join(['%s'] * len(selected_vwp))

        query = rfl_select_query.get_select_query('get_selected_vwp').format(placeholders)

        with DBCon(False) as connection:
            df = pd.read_sql_query(query,connection,params=selected_vwp)
            df = df.convert_dtypes()

            return df