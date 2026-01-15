from typing import Any
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
from module.PsqlModule import psql_class
sql = psql_class()

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
        print('hierarchy in get_wp: ', hierarchy)
        project_code = tuple(project_code)
        phase = tuple(phase)
        hierarchy = tuple(hierarchy)
        print('hierarchy tuple in get_wp: ', hierarchy)
       
        query = rfl_select_query.get_select_query('get_r_wp')
        
        # Format query with proper placeholders for IN clauses
        # pd.read_sql_query doesn't expand tuples for IN clauses, so we need to create placeholders
        project_placeholders = ','.join(['%s'] * len(project_code))
        phase_placeholders = ','.join(['%s'] * len(phase))
        hierarchy_placeholders = ','.join(['%s'] * len(hierarchy))
        
        query = query.replace('pj_code IN (%s)', f'pj_code IN ({project_placeholders})')
        query = query.replace('phase IN (%s)', f'phase IN ({phase_placeholders})')
        query = query.replace('hierarchy IN (%s)', f'hierarchy IN ({hierarchy_placeholders})')
        
        # Flatten tuples for params - all values in order
        params = tuple(project_code) + tuple(phase) + tuple(hierarchy)

        print('Query:', query)
        print('Params:', params)

        with DBCon() as connection:
            result = pd.read_sql_query(query, connection, params=params)

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
    def get_units_dict():
        """Get units as a dictionary mapping unit value to unit ID
        
        Returns:
            dict: Dictionary with unit values as keys and unit IDs as values
        """
        query = rfl_select_query.get_select_query('get_units')
        with DBCon() as connection:
            df = pd.read_sql_query(query, connection)
            # Create dictionary mapping unit value to unit ID
            # Filter out NaN values to avoid issues
            df_clean = df.dropna(subset=['unit'])
            units_dict = dict(zip(df_clean['unit'], df_clean['id']))
            return units_dict

    @staticmethod
    def get_r_parameter_units_list():
        """Get distinct units from r_parameter table for r_cols unit dropdown
        
        Returns:
            list: List of distinct unit strings from r_parameter
        """
        query = rfl_select_query.get_select_query('get_r_parameter_units')
        with DBCon() as connection:
            df = pd.read_sql_query(query, connection)
            # Return list of distinct unit values
            units_list = df['unit'].dropna().tolist()
            return units_list

    @staticmethod
    def get_wp_dict():
        """Get WP as a dictionary mapping WP value to WP ID
        
        Returns:
            dict: Dictionary with WP values as keys and WP IDs as values
        """
        query = rfl_select_query.get_select_query('get_wp_list')
        with DBCon() as connection:
            df = pd.read_sql_query(query, connection)
            # Create dictionary mapping WP value to WP ID
            df_clean = df.dropna(subset=['wp'])
            wp_dict = dict(zip(df_clean['wp'], df_clean['id']))
            return wp_dict

    @staticmethod
    def get_l_tree(project_code):
        query = l_tree.get_select_query('get_l_tree_in_pj')
        print('query in get_l_tree: ',query)
        with DBCon(False) as connection:
            df = pd.read_sql_query(query,connection,params=(project_code,))
            df = df.convert_dtypes()

            return df    

    #Retrieve the data for rfl func #Kyaw 10/07
    #Params: 階層、領域
    def get_rfl_all_hierarchy_levels( select_list1 = None, select_list2 = None, select_list3 = None, select_list4 = None, select_list5 = None, wp_list = None, get_list_to_display = False):
        select_list1 = select_list1 or []
        select_list2 = select_list2 or []
        select_list3 = select_list3 or []
        select_list4 = select_list4 or []
        select_list5 = select_list5 or []
        wp_list = wp_list or []
        if not wp_list:
            print('no wp list')
            return []
        
        with DBCon() as connection:
            # リストの要素をシングルクォートで囲んでカンマで結合
            select_list_str1 = ', '.join(f"'{item}'" for item in select_list1)
            select_list_str2 = ', '.join(f"'{item}'" for item in select_list2)
            select_list_str3 = ', '.join(f"'{item}'" for item in select_list3)
            select_list_str4 = ', '.join(f"'{item}'" for item in select_list4)
            select_list_str5 = ', '.join(f"'{item}'" for item in select_list5)
            wp_list_str = ', '.join(f"'{item}'" for item in wp_list)

            prj_list = sql.get_se_proj_info_query(select_list_str1,select_list_str2,select_list_str3,select_list_str4,select_list_str5)
            print('prj_list: ', prj_list)
            st.session_state.prj_info_list = prj_list

            # Extract unique project_id and phase_id from prj_list
            if isinstance(prj_list, pd.DataFrame) and not prj_list.empty:
                project_ids = prj_list['project_id'].dropna().unique().tolist()
                phase_ids = prj_list['phase_id'].dropna().unique().tolist()
                
                # Create comma-separated strings for SQL IN clause
                project_ids_str = ', '.join(str(int(pid)) for pid in project_ids)
                phase_ids_str = ', '.join(str(int(phid)) for phid in phase_ids)
            else:
                project_ids_str = ''
                phase_ids_str = ''

            print('project_ids_str: ', project_ids_str)
            print('phase_ids_str: ', phase_ids_str)
            print('wp_list_str: ', wp_list_str)
            
            if project_ids_str and phase_ids_str:
                # Build WHERE clause conditionally - only add r_wp filter if wp_list_str is not empty
                wp_filter = f" AND r_wp IN ({wp_list_str})" if wp_list_str else ""

                query_template = f"""
                    SELECT 
                        pj_id as r_pj_id, 
                        pj_code as project_code, 
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
                        archi,
                        lot,
                        phase, 
                        n_wp, 
                        flag_display_on_summary_logic, 
                        flag_to, 
                        r_index,
                        f_index,
                        l_index, 
                        index,
                        l_r_s_p_i as related_se_parameter_id, 
                        sender_judge, 
                        sender_name, 
                        DATE(sender_date) as sender_date, 
                        sender_comment, 
                        receiver_judge, 
                        receiver_name, 
                        DATE(receiver_date) as receiver_date, 
                        receiver_comment, 
                        to_solving_value, 
                        req_condition,
                        log_condition,
                        is_to as is_to,
                        to_pattern as to_pattern,
                        perf_is_to as perf_is_to,
                        perf_to_pattern as perf_to_pattern
                    FROM 
                        rfl_view_tlm
                    WHERE pj_id IN ({project_ids_str}) AND phase_id IN ({phase_ids_str}) AND hierarchy_id IN (1,2,3){wp_filter}
                    ORDER BY r_pj_id,phase_id,hierarchy_id,r_index,f_index,l_index;
                """


                df = pd.read_sql(query_template, connection)

                df1 = df[df['hierarchy_id'] == 1]
                print('rfl df1: ', df1)
                df2 = df[df['hierarchy_id'] == 2]
                print('rfl df2: ', df2)
                df3 = df[df['hierarchy_id'] == 3]
                print('rfl df3: ', df3)

                group_keys = pd.concat(
                    [
                        df1[['r_pj_id', 'phase_id', 'wp']] if not df1.empty else pd.DataFrame(),
                        df2[['r_pj_id', 'phase_id', 'wp']] if not df2.empty else pd.DataFrame(),
                        df3[['r_pj_id', 'phase_id', 'wp']] if not df3.empty else pd.DataFrame(),
                    ],
                    ignore_index=True
                ).drop_duplicates()

                # Ensure correct columns even if everything is empty
                if group_keys.empty:
                    group_keys = pd.DataFrame(columns=['r_pj_id', 'phase_id', 'wp'])


                # List to store results from each group
                all_hierarchy_results = []
                # sorted_hierarchy_res = pd.DataFrame()

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

                # Process each group separately
                for _, group_key in group_keys.iterrows():
                    r_pj_id_val = group_key['r_pj_id']
                    phase_id_val = group_key['phase_id']
                    wp_val = group_key['wp']

                    # Filter each DataFrame by the group key
                    # If DataFrame is empty (no rows), return empty DataFrame with same columns
                    if df1.empty:
                        df1_group = pd.DataFrame(columns=df1.columns)
                    else:
                        df1_group = df1[(df1['r_pj_id'] == r_pj_id_val) & 
                                        (df1['phase_id'] == phase_id_val) & 
                                        (df1['wp'] == wp_val)].copy()
                    
                    if df2.empty:
                        df2_group = pd.DataFrame(columns=df2.columns)
                    else:
                        df2_group = df2[(df2['r_pj_id'] == r_pj_id_val) & 
                                        (df2['phase_id'] == phase_id_val) & 
                                        (df2['wp'] == wp_val)].copy()
                    
                    if df3.empty:
                        df3_group = pd.DataFrame(columns=df3.columns)
                    else:
                        df3_group = df3[(df3['r_pj_id'] == r_pj_id_val) & 
                                        (df3['phase_id'] == phase_id_val) & 
                                        (df3['wp'] == wp_val)].copy()

                    # Process this group through the functions
                    hierarchy_res = build_full_hierarchical_dataframe(df1_group, df2_group, df3_group)
                    if not df3_group.empty:
                        hierarchy_res = append_missing_df3_rows(hierarchy_res, df3_group)
                    sorted_hierarchy_res = conditional_sort_hierarchical_df(hierarchy_res)
                    
                    # Append to results list
                    if not sorted_hierarchy_res.empty:
                        all_hierarchy_results.append(sorted_hierarchy_res)
                
                # Combine all group results
                if all_hierarchy_results:
                    sorted_hierarchy_res = pd.concat(all_hierarchy_results, ignore_index=True)
                else:
                    # sorted_hierarchy_res = pd.DataFrame()
                    return []


                if get_list_to_display:
                    # Rename columns: hr1_ -> c_, hr2_ -> s_, hr3_ -> u_
                    sorted_hierarchy_res.columns = sorted_hierarchy_res.columns.str.replace('hr1_', 'c_', regex=False)
                    sorted_hierarchy_res.columns = sorted_hierarchy_res.columns.str.replace('hr2_', 's_', regex=False)
                    sorted_hierarchy_res.columns = sorted_hierarchy_res.columns.str.replace('hr3_', 'u_', regex=False)

                    # Base mapping (no prefix)
                    base_map = {
                        "project_code": "project_code",
                        "phase": "phase",
                        "archi": "archi",
                        "lot": "lot",
                        "wp": "r_wp",
                        "l_wp_id": "allocation"
                        # Add more base mappings here if needed
                    }

                    prefixes = ["c_", "s_", "u_"]

                    # Columns to propagate
                    cols_to_propagate = ['project_code', 'phase', 'archi', 'lot'] #add this cols to where its null. eg; if null for c_, add s_ value to c_ or add u_ value to c_.
                    # prefixes = ['c_', 's_', 'u_']

                    # Build the full prefixed column groups
                    for col in cols_to_propagate:
                        col_group = [prefix + col for prefix in prefixes]
                        
                        # Apply row-wise propagation
                        def propagate_row(row):
                            # Get non-null values
                            values = row[col_group].dropna().unique()
                            for c in col_group:
                                if pd.isna(row[c]) and len(values) > 0:
                                    row[c] = values[0]  # fill with first non-null value
                            return row
                        
                        sorted_hierarchy_res = sorted_hierarchy_res.apply(propagate_row, axis=1)

                    # Build the full mapping
                    full_map = {}

                    for prefix in prefixes:
                        for base_col, mapped_col in base_map.items():
                            old_name = prefix + base_col
                            if base_col in ['project_code', 'phase', 'archi', 'lot']:
                                new_name = mapped_col
                            else:
                                new_name = prefix + mapped_col
                            full_map[old_name] = new_name
                            

                    # ✅ Apply renaming to your DataFrame
                    sorted_hierarchy_res = sorted_hierarchy_res.rename(columns=full_map)
                    sorted_hierarchy_res = sorted_hierarchy_res.loc[:, ~sorted_hierarchy_res.columns.duplicated()]

                    # Initialize sender_selected and receiver_selected columns for each prefix (c_, s_, u_)
                    prefixes = ['c_', 's_', 'u_']
                    for prefix in prefixes:
                        sender_col = f'{prefix}sender_selected'
                        receiver_col = f'{prefix}receiver_selected'
                        if sender_col not in sorted_hierarchy_res.columns:
                            sorted_hierarchy_res[sender_col] = False
                        else:
                            # Ensure boolean type
                            sorted_hierarchy_res[sender_col] = sorted_hierarchy_res[sender_col].fillna(False).astype(bool)
                        if receiver_col not in sorted_hierarchy_res.columns:
                            sorted_hierarchy_res[receiver_col] = False
                        else:
                            # Ensure boolean type
                            sorted_hierarchy_res[receiver_col] = sorted_hierarchy_res[receiver_col].fillna(False).astype(bool)

                return sorted_hierarchy_res

            else:
                return []

