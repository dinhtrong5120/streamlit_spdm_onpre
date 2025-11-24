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
#telema-kyaw rfl_update 8/22
from queries.r_tree import rfl_primary_tree as primary_tree_query,rfl_secondary_tree as secondary_tree_query,rfl_third_tree as third_tree_query
from queries.f_tree import rfl_primary_tree as primary_f_tree_query,rfl_secondary_tree as secondary_f_tree_query,rfl_third_tree as third_f_tree_query
from queries.l_tree import l_tree
from queries.grid import rfl_grid 

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

    # @staticmethod
    # def update_rfl(project_id,rfl_id,phase_id,diff_col,diff_value):
    #     """編集値をupdate

    #     Args:
    #         project_id (int): 複合主キー1
    #         rfl_id (int): 複合主キー2
    #         phase_id (int): 複合主キー3
    #         diff_col (string): 変更対象列
    #         diff_value (string/int): 編集値
    #     """
    #     if diff_col == 'req':
    #         diff_col = 'requirement'
    #     if diff_col == 'func':
    #         diff_col = 'function'    
    #     project_id = (project_id,)
    #     rfl_id = (rfl_id,)
    #     phase_id = (phase_id,)
    #     diff_value = (diff_value,)

    #     lock_query = rfl_select_query.get_select_query('lock_prj_rfl_for_update')
    #     update_query = rfl_update_query.get_update_query('update_edited_prj_rfl').format(diff_col)

    #     with DBCon(False) as connection:
    #         cur = connection.cursor()
    #         # 排他制御
    #         cur.execute(lock_query,(project_id,rfl_id,phase_id))
    #         # update
    #         cur.execute(update_query,(diff_value,project_id,rfl_id,phase_id))

    #telema-kyaw rfl_update 8/22
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

        # noteの場合、単独Update
        if diff_col =='note':
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
                return

        # 要求値更新の場合、同項目の値を全更新
        get_rfl_query = rfl_select_query.get_select_query('get_rfl')
        result = ''
        with DBCon() as connection:
            result = pd.read_sql_query(get_rfl_query,connection,params=(rfl_id,))
        rfl_col = ''
        print('diff_col:',diff_col)
        if diff_col == 'req':
            diff_col = 'requirement'
            rfl_col = 'requirement_s_id'
        if diff_col == 'func':
            diff_col = 'function'
            rfl_col = 'function_id'
        if diff_col == 'logic':
            rfl_col = 'logic_s_id'

        rfl_element_id = int(result.loc[0,rfl_col])
        update_bulk_query = rfl_update_query.get_update_query('bulk_update_edited_prj_rfl').format(rfl_col,diff_col)
        project_id = (project_id,)
        rfl_id = (rfl_id,)
        phase_id = (phase_id,)
        diff_value = (diff_value,)

        lock_query = rfl_select_query.get_select_query('lock_prj_rfl_for_update')
        update_query = rfl_update_query.get_update_query('update_edited_prj_rfl')

        with DBCon(False) as connection:
            cur = connection.cursor()
            # 排他制御
            cur.execute(lock_query,(project_id,rfl_id,phase_id))
            cur.execute(update_bulk_query,(rfl_element_id,diff_value))

    #telema-kyaw rfl_update 8/22
    @staticmethod
    def get_r_tree_from_lower_hr(wp,project_code,hierarchy):
        print('hierarchy: ',hierarchy)
        print('wp: ',wp)
        print('project_code: ',project_code)
        if hierarchy == 'システム':
            query = rfl_select_query.get_select_query('get_r_tree_from_hr2')
            print('system hr2 query: ',query)
        if hierarchy == 'ユニット':
            query = rfl_select_query.get_select_query('get_r_tree_from_hr3')
        with DBCon(False) as connection:
            df = pd.read_sql_query(query,connection,params=(wp,project_code,))
            df = df.convert_dtypes()
            return df
        
    #telema-kyaw rfl_update 8/22
    #  --------------------------------------------- for excel ------------------------------------------------------
    @staticmethod
    def get_hierarchical_rfl_grid(project_code,phase,wp):
        query = rfl_grid.get_rfl_historical_grid()
        with DBCon(False) as connection:
            df = pd.read_sql_query(query,connection,params=(project_code,phase,wp,))
            df = df.convert_dtypes()

            return df

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

#telema-kyaw rfl_update 9/2
# --------------------------------------------- r_tree ------------------------------------------------------

    @staticmethod
    def get_r_primary_wps(hierarchy,wp,project_code):
        print('wp in r_primary_wps: ',wp)
        print('project_code in r_primary_wps: ',project_code)
        print('hierarchy in r_primary_wps: ',hierarchy)

        if hierarchy == '車両':
            query = primary_tree_query.get_select_query('get_primary_wps_from_hr1')

        if hierarchy == 'システム':
            query = primary_tree_query.get_select_query('get_primary_wps_from_hr2')
            if not st.session_state.third_tree_flag:
                wp = (wp,)

        if hierarchy == 'ユニット':
            query = primary_tree_query.get_select_query('get_primary_wps_from_hr3')

        if hierarchy == 'f_s':
            query = primary_tree_query.get_select_query('get_primary_wps_from_hr2')
            wp = (wp,)

        with DBCon(False) as connection:
            df = pd.read_sql_query(query,connection,params=(wp,project_code,))
            df = df.convert_dtypes()

        return df

    @staticmethod
    def get_r_secondary_wps(hierarchy,wp,project_code):
        if hierarchy == '車両':
            query = secondary_tree_query.get_select_query('get_secondary_wps_from_hr1')
        if hierarchy == 'システム':
            query = secondary_tree_query.get_select_query('get_secondary_wps_from_hr2')
        if hierarchy == 'ユニット':
            query = secondary_tree_query.get_select_query('get_secondary_wps_from_hr3')

        with DBCon(False) as connection:
            df = pd.read_sql_query(query,connection,params=(wp,project_code,))
            df = df.convert_dtypes()

        return df

    @staticmethod
    def get_r_third_wps(hierarchy,wp,project_code):
        if hierarchy == '車両':
            query = third_tree_query.get_select_query('get_third_wps_from_hr1')
        # if hierarchy == 'システム':
        #     query = third_tree_query.get_select_query('get_third_wps_from_hr2')
        if hierarchy == 'ユニット':
            query = third_tree_query.get_select_query('get_third_wps_from_hr3')

        with DBCon(False) as connection:
            df = pd.read_sql_query(query,connection,params=(wp,project_code,))
            df = df.convert_dtypes()

        return df

#telema-kyaw rfl_update 9/2
#  --------------------------------------------- f_tree ------------------------------------------------------

    @staticmethod
    def get_f_primary_wps(hierarchy,wp,project_code):
        if hierarchy == '車両':
            query = primary_f_tree_query.get_select_query('get_primary_function_from_hr1')
        if hierarchy == 'システム':
            query = primary_f_tree_query.get_select_query('get_primary_function_from_hr2')
            if not st.session_state.third_tree_flag:
                wp = (wp,)
        if hierarchy == 'ユニット':
            query = primary_f_tree_query.get_select_query('get_primary_function_from_hr3')

        if hierarchy == 'f_s':
            query = primary_f_tree_query.get_select_query('get_primary_function_from_hr2')


        with DBCon(False) as connection:
            df = pd.read_sql_query(query,connection,params=(wp,project_code,))
            df = df.convert_dtypes()

        return df


    @staticmethod
    def get_f_secondary_wps(hierarchy,wp,project_code):
        if hierarchy == '車両':
            query = secondary_f_tree_query.get_select_query('get_secondary_function_from_hr1')
        if hierarchy == 'システム':
            query = secondary_f_tree_query.get_select_query('get_secondary_function_from_hr2')
        if hierarchy == 'ユニット':
            query = secondary_f_tree_query.get_select_query('get_secondary_function_from_hr3')

        with DBCon(False) as connection:
            df = pd.read_sql_query(query,connection,params=(wp,project_code,))
            df = df.convert_dtypes()

        return df


    @staticmethod
    def get_f_third_wps(hierarchy,wp,project_code):
        if hierarchy == '車両':
            query = third_f_tree_query.get_select_query('get_third_function_from_hr1')
        if hierarchy == 'システム':
            query = secondary_f_tree_query.get_select_query('get_secondary_function_from_hr2')
        if hierarchy == 'ユニット':
            query = third_f_tree_query.get_select_query('get_third_function_from_hr3')

        with DBCon(False) as connection:
            df = pd.read_sql_query(query,connection,params=(wp,project_code,))
            df = df.convert_dtypes()

        return df

#telema-kyaw rfl_update 9/2
#  --------------------------------------------- l_tree ------------------------------------------------------

    @staticmethod
    def get_l_tree(project_code):
        query = l_tree.get_select_query('get_l_tree_in_pj')
        print('query in get_l_tree: ',query)
        with DBCon(False) as connection:
            df = pd.read_sql_query(query,connection,params=(project_code,))
            df = df.convert_dtypes()

            return df    

# -------------------------------------------------------------------------------------------------------------

    #Retrieve the data for rfl_download function #Kyaw 10/07
    #Params: 階層、領域
    def get_rfl_download_data(hierarchy_list = [], wp_list = []):

        with DBCon() as connection:
            # リストの要素をシングルクォートで囲んでカンマで結合
            hierarchy_list_str = ', '.join(f"'{item}'" for item in hierarchy_list)
            wp_list_str = ', '.join(f"'{item}'" for item in wp_list)
            if hierarchy_list_str and wp_list_str:
                
                #選択されたＷＰの車両の情報を取得
                df1_query = f"""
                    SELECT 
                        pj_id, 
                        pj_code, 
                        drivetrain, 
                        hierarchy, 
                        hierarchy_id, 
                        r_wp_id, 
                        r_wp AS wp, 
                        r_wp_summary_index, 
                        rfl_id, 
                        r_s_id, 
                        l_s_id, 
                        r_item, 
                        r_item_2, 
                        prfl_r AS req, 
                        r_unit, 
                        r_uc_id, 
                        r_uc AS r_scene, 
                        f_id, 
                        f_item, 
                        prfl_f AS func, 
                        f_unit, 
                        l_id, 
                        l_item, 
                        allocation, 
                        l_wp, 
                        l_wp_id, 
                        prfl_l AS logic, 
                        l_unit, 
                        l_uc_id, 
                        l_uc AS l_scene, 
                        prfl_note AS note, 
                        n_r_s_id, 
                        ph_id, 
                        phase_id, 
                        phase, 
                        n_wp, 
                        flag_display_on_summary_logic, 
                        flag_to, 
                        index AS rfl_index, 
                        l_r_s_p_i, 
                        sender_judge, 
                        sender_name, 
                        sender_date, 
                        sender_comment, 
                        receiver_judge, 
                        receiver_name, 
                        receiver_date, 
                        receiver_comment, 
                        to_solving_value, 
                        log_condition
                    FROM 
                        rfl_view_tlm
                    WHERE pj_id = 14 AND phase_id = 3 AND hierarchy_id = 1 AND r_wp = {(wp_list_str)}
                    ORDER BY index
                """
                #選択されたＷＰのシステムの情報を取得
                df2_query = f"""
                    SELECT 
                        pj_id, 
                        pj_code, 
                        drivetrain, 
                        hierarchy, 
                        hierarchy_id, 
                        r_wp_id, 
                        r_wp AS wp, 
                        r_wp_summary_index, 
                        rfl_id, 
                        r_s_id, 
                        l_s_id, 
                        r_item, 
                        r_item_2, 
                        prfl_r AS req, 
                        r_unit, 
                        r_uc_id, 
                        r_uc AS r_scene, 
                        f_id, 
                        f_item, 
                        prfl_f AS func, 
                        f_unit, 
                        l_id, 
                        l_item, 
                        allocation, 
                        l_wp, 
                        l_wp_id, 
                        prfl_l AS logic, 
                        l_unit, 
                        l_uc_id, 
                        l_uc AS l_scene, 
                        prfl_note AS note, 
                        n_r_s_id, 
                        ph_id, 
                        phase_id, 
                        phase, 
                        n_wp, 
                        flag_display_on_summary_logic, 
                        flag_to, 
                        index AS rfl_index, 
                        l_r_s_p_i, 
                        sender_judge, 
                        sender_name, 
                        sender_date, 
                        sender_comment, 
                        receiver_judge, 
                        receiver_name, 
                        receiver_date, 
                        receiver_comment, 
                        to_solving_value, 
                        log_condition
                    FROM 
                        rfl_view_tlm
                    WHERE pj_id = 14 AND phase_id = 3 AND hierarchy_id = 2 AND r_wp = {(wp_list_str)}
                    ORDER BY index
                """
                #選択されたＷＰのユニットの情報を取得
                df3_query = f"""
                    SELECT 
                        pj_id, 
                        pj_code, 
                        drivetrain, 
                        hierarchy, 
                        hierarchy_id, 
                        r_wp_id, 
                        r_wp AS wp, 
                        r_wp_summary_index, 
                        rfl_id, 
                        r_s_id, 
                        l_s_id, 
                        r_item, 
                        r_item_2, 
                        prfl_r AS req, 
                        r_unit, 
                        r_uc_id, 
                        r_uc AS r_scene, 
                        f_id, 
                        f_item, 
                        prfl_f AS func, 
                        f_unit, 
                        l_id, 
                        l_item, 
                        allocation, 
                        l_wp, 
                        l_wp_id, 
                        prfl_l AS logic, 
                        l_unit, 
                        l_uc_id, 
                        l_uc AS l_scene, 
                        prfl_note AS note, 
                        n_r_s_id, 
                        ph_id, 
                        phase_id, 
                        phase, 
                        n_wp, 
                        flag_display_on_summary_logic, 
                        flag_to, 
                        index AS rfl_index, 
                        l_r_s_p_i, 
                        sender_judge, 
                        sender_name, 
                        sender_date, 
                        sender_comment, 
                        receiver_judge, 
                        receiver_name, 
                        receiver_date, 
                        receiver_comment, 
                        to_solving_value, 
                        log_condition
                    FROM 
                        rfl_view_tlm
                    WHERE pj_id = 14 AND phase_id = 3 AND hierarchy_id = 3 AND r_wp = {(wp_list_str)}
                    ORDER BY index
                """
                df1 = pd.read_sql(df1_query, connection)
                df2 = pd.read_sql(df2_query, connection)
                df3 = pd.read_sql(df3_query, connection)

                def append_missing_df3_rows(hierarchy_res: pd.DataFrame, df3: pd.DataFrame) -> pd.DataFrame:
                    df3_ids = set(df3['r_s_id'])
                    existing_hr3_ids = set(hierarchy_res['hr3_r_s_id'].dropna())

                    missing_ids = df3_ids - existing_hr3_ids

                    if not missing_ids:
                        return hierarchy_res  # all df3 IDs are already present

                    # Get missing rows
                    missing_rows = df3[df3['r_s_id'].isin(missing_ids)]
                    missing_rows_prefixed = missing_rows.rename(columns=lambda col: f'hr3_{col}')

                    # ✅ Add hr3_index column explicitly with None (if it's in final DataFrame structure)
                    if 'hr3_index' in hierarchy_res.columns:
                        missing_rows_prefixed['hr3_index'] = None

                    # Fill hr1_ and hr2_ columns with None
                    hr1_cols = [col for col in hierarchy_res.columns if col.startswith('hr1_')]
                    hr2_cols = [col for col in hierarchy_res.columns if col.startswith('hr2_')]

                    for col in hr1_cols + hr2_cols:
                        missing_rows_prefixed[col] = None

                    # Reorder columns
                    final_columns = hierarchy_res.columns
                    missing_rows_prefixed = missing_rows_prefixed[final_columns]

                    # Append and return
                    return pd.concat([hierarchy_res, missing_rows_prefixed], ignore_index=True)
            
                def conditional_sort_hierarchical_df(df):
                    sort_cols = ['hr1_index', 'hr2_index', 'hr3_index']
                    existing_cols = [col for col in sort_cols if col in df.columns]
                    return df.sort_values(by=existing_cols, ascending=True).reset_index(drop=True)

                def build_full_hierarchical_dataframe(df1, df2, df3):
                    rows = []

                    def prefix_dict(row, prefix):
                        return {f"{prefix}_{col}": row[col] for col in row.index}

                    # Build column names for each level even if empty
                    hr1_cols = [f"hr1_{col}" for col in df1.columns]
                    hr2_cols = [f"hr2_{col}" for col in df2.columns]
                    hr3_cols = [f"hr3_{col}" for col in df3.columns]

                    # Case 1: All df1, df2, df3 are available
                    if not df1.empty and not df2.empty and not df3.empty:
                        for _, row1 in df1.iterrows():
                            df1_data = prefix_dict(row1, 'hr1')
                            df2_matches = df2[df2['r_s_id'] == row1['n_r_s_id']]
                            if df2_matches.empty:
                                row_data = {**df1_data}
                                for col in hr2_cols + hr3_cols:
                                    row_data[col] = None
                                rows.append(row_data)
                            else:
                                for _, row2 in df2_matches.iterrows():
                                    df2_data = prefix_dict(row2, 'hr2')
                                    df3_matches = df3[df3['r_s_id'] == row2['n_r_s_id']]
                                    if df3_matches.empty:
                                        row_data = {**df1_data, **df2_data}
                                        for col in hr3_cols:
                                            row_data[col] = None
                                        rows.append(row_data)
                                    else:
                                        for _, row3 in df3_matches.iterrows():
                                            df3_data = prefix_dict(row3, 'hr3')
                                            rows.append({**df1_data, **df2_data, **df3_data})

                    # Case 2: df1 + df2 only (df3 is empty)
                    elif not df1.empty and not df2.empty:
                        for _, row1 in df1.iterrows():
                            df1_data = prefix_dict(row1, 'hr1')
                            df2_matches = df2[df2['r_s_id'] == row1['n_r_s_id']]
                            if df2_matches.empty:
                                row_data = {**df1_data}
                                for col in hr2_cols + hr3_cols:
                                    row_data[col] = None
                                rows.append(row_data)
                            else:
                                for _, row2 in df2_matches.iterrows():
                                    df2_data = prefix_dict(row2, 'hr2')
                                    row_data = {**df1_data, **df2_data}
                                    for col in hr3_cols:
                                        row_data[col] = None
                                    rows.append(row_data)

                    # Case 3: df1 + df3 only (df2 is empty)
                    elif not df1.empty and not df3.empty:
                        for _, row1 in df1.iterrows():
                            df1_data = prefix_dict(row1, 'hr1')
                            df3_matches = df3[df3['r_s_id'] == row1['n_r_s_id']]
                            if df3_matches.empty:
                                row_data = {**df1_data}
                                for col in hr2_cols + hr3_cols:
                                    row_data[col] = None
                                rows.append(row_data)
                            else:
                                for _, row3 in df3_matches.iterrows():
                                    df3_data = prefix_dict(row3, 'hr3')
                                    row_data = {**df1_data, **df3_data}
                                    for col in hr2_cols:
                                        row_data[col] = None
                                    rows.append(row_data)

                    # Case 4: df2 + df3 only (df1 is empty)
                    elif not df2.empty and not df3.empty:
                        for _, row2 in df2.iterrows():
                            df2_data = prefix_dict(row2, 'hr2')
                            df3_matches = df3[df3['r_s_id'] == row2['n_r_s_id']]
                            if df3_matches.empty:
                                row_data = {**df2_data}
                                for col in hr1_cols + hr3_cols:
                                    row_data[col] = None
                                rows.append(row_data)
                            else:
                                for _, row3 in df3_matches.iterrows():
                                    df3_data = prefix_dict(row3, 'hr3')
                                    row_data = {**df2_data, **df3_data}
                                    for col in hr1_cols:
                                        row_data[col] = None
                                    rows.append(row_data)

                    # Case 5: df1 only
                    elif not df1.empty:
                        for _, row1 in df1.iterrows():
                            row_data = prefix_dict(row1, 'hr1')
                            for col in hr2_cols + hr3_cols:
                                row_data[col] = None
                            rows.append(row_data)

                    # Case 6: df2 only
                    elif not df2.empty:
                        for _, row2 in df2.iterrows():
                            row_data = prefix_dict(row2, 'hr2')
                            for col in hr1_cols + hr3_cols:
                                row_data[col] = None
                            rows.append(row_data)

                    # Case 7: df3 only
                    elif not df3.empty:
                        for _, row3 in df3.iterrows():
                            row_data = prefix_dict(row3, 'hr3')
                            for col in hr1_cols + hr2_cols:
                                row_data[col] = None
                            rows.append(row_data)

                    return pd.DataFrame(rows)

                hierarchy_res = build_full_hierarchical_dataframe(df1,df2,df3)
                if not df3.empty:
                    hierarchy_res = append_missing_df3_rows(hierarchy_res, df3)
                sorted_hierarchy_res = conditional_sort_hierarchical_df(hierarchy_res)

                return sorted_hierarchy_res

            else:
                return []

