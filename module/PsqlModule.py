import pandas as pd
import psycopg2
from psycopg2 import OperationalError, InterfaceError, sql
import re
import const.constpara as co
from sqlalchemy import create_engine, text
import datetime
import streamlit as st
import itertools #山口　DFの処理を楽にしたく追加 1/28
class psql_class:

    def __init__(self) -> None:
        self.engine = create_engine(co.psql)
        self.conn = self.create_connection()

    def create_connection(self):
        try:
            connection = psycopg2.connect(
                dbname="SPDM_2",
                user="postgres",
                password="SQL123456",
                host="localhost",
                port="5432"
            )
            
            return connection
        except OperationalError as e:
            return None
        # self.cursor = self.conn.cursor()

    def __del__(self):
        # オブジェクトが破棄される際にデータベース接続を閉じる
        if self.conn:
            self.conn.close()
    
    def table_insert(self,df,table_name):
        engine = self.engine
        connection = self.conn
        with connection as conn:
            with conn.cursor() as cur:
                cur.execute(f'delete from {table_name}')

        # データフレームをテーブルに挿入
        df.to_sql(table_name, engine, if_exists='append', index=False)

    def detail_data_update(self):
        now = datetime.datetime.now()
        connection = self.conn
        query = f"""
        INSERT INTO detail_data (z_paravalueid,employee_number,update_day,approval_status,user_memo)
       
        SELECT t1.z_paravalueid, 'N194000', '{now}', 0, 'ここにメモを挿入できます'
        FROM se_project_record t1
        LEFT JOIN detail_data t2 ON t1.z_paravalueid = t2.z_paravalueid
        WHERE t2.z_paravalueid IS NULL;"""
        with connection as conn:
            with conn.cursor() as cur:
                cur.execute(query)

    #def detail_data_update(self):
    #    now = datetime.datetime.now()
    #    connection = self.conn
    #    # cur = self.conn.cursor()
    #    # getdata =[]
    #    query = f""" 
    #    SELECT t1.z_paravalueid
    #    FROM se_project_record t1;
    #    """
    #    # # INSERT INTO detail_data (z_paravalueid,employee_number,update_day,approval_status,user_memo)
    #    with connection as conn:
    #        with conn.cursor() as cur:
    #            cur.execute(query)
    #            rows = cur.fetchall()
                # result_list = [row[0] for row in rows]
                # print(rows)

        # query = "select z_destination,z_drive_system,z_model_code,z_number,z_vehicle_type from dialog_list;"
        # query = "select * from detail_data;"
        # cur.execute(query)


    def update_record(self,df):
        cur = None
        for index, row in df.iterrows():
            try:
                cur = self.conn.cursor()
                # SQLクエリを準備 山口　update文でなく、Insert文を実行する用に変更を加える 10/09
                #query = sql.SQL("""
                #    UPDATE detail_data
                #    SET
                #        employee_number = %s,
                #        update_day = %s,
                #        approval_status = %s,
                #        user_memo = %s
                #    WHERE z_paravalueid = %s
                #""")
                #cur.execute(query, (row['employee_number'], row['update_day'], row['state_name'], row['user_memo'], row['z_paravalueid']))
                query = sql.SQL("""
                    INSERT INTO detail_data VALUES(%s, %s, %s, %s, %s,%s)
                """)
                cur.execute(query, (row['z_paravalueid'], row['employee_number'], row['update_day'], row['state_name'], row['user_memo'], row['z_request_median']))#山口　Valueも追加した 11/1
                #山口　テーブル分割に伴い編集10/22
                query = sql.SQL("""
                    UPDATE project_parameter
                    SET 
                        value = %s,
                        z_note = %s
                       
                    WHERE project_id = %s and se_parameter_id = %s and phase_id = %s and variation_id = %s;
                """)
                print(query)
                cur.execute(query, (row['z_request_median'], row['z_note'], row['project_id'], row['se_parameter_id'], row['phase_id'], row['variation_id'])) #値の編集　山口 %arasidだよりで編集加えていたことで大災害発生、、idベースの変更に切り替え 8/4
                query = sql.SQL("""
                    UPDATE aras_meta
                    SET 
                        z_note = %s
                       
                    WHERE arasid = %s
                """)
                query
                cur.execute(query, (row['z_note'], row['z_paravalueid'])) #担当者の編集　山口
            
            except InterfaceError as e:
                raise e
                # 接続が閉じられている場合、再接続を試みる
                self.conn = self.create_connection()
                if self.conn:
                    return self.column_to_list(query)
                else:
                    return None
            except psycopg2.Error as e:
                
                # エラー発生時にロールバック
                self.conn.rollback()
                raise e
                return None
            
        self.conn.commit()
        if cur:
                cur.close()      
    
    def update_record_rlist(self,df):#山口　Rテーブル更新 1/29 職制承認情報のアップデート対応 3/22 妥協地返照でき量に 8/1
        cur = None
        for index, row in df.iterrows():
            try:
                cur = self.conn.cursor()
                #山口　ログも後でやる
                # query = sql.SQL("""
                #     INSERT INTO detail_data_sim VALUES(%s, %s, %s, %s, %s)
                # """)
                # cur.execute(query, (row['id'], row['employee_number'], row['update_day'], row['user_memo'], row['value'])) 
                
                auto_judge_type_dict = {
                "未定": 1,
                "以上": 2,
                "以下": 3,
                "同等": 4,
                }

                auto_judge_type = row['auto_judge_type']
                if auto_judge_type in auto_judge_type_dict.keys():
                    auto_judge_type_id = auto_judge_type_dict[auto_judge_type]
                else:
                    auto_judge_type_id = 1

                query = sql.SQL("""
                    UPDATE project_r_parameter
                    SET 
                        target = %s,
                        adjusted_target = %s,
                        design = %s,
                        priority = %s,
                        detail_and_output = %s,
                        responsible = %s,
                        period = %s, 
                        note = %s,
                        auto_judge_id = %s,
                        judge = %s, -- 山口 judge のupdate が抜けていたため追加
                        judge_evidence = %s, -- 山口 判断資料アップデートに対応3/24 
                        manager_approval = %s,
                        manager_approval_comment = %s
                       
                    WHERE project_id = %s and phase_id =%s and variation_id = %s and r_parameter_id = %s;
                """)
                print(query)
                cur.execute(query, (row['target'], row['adjusted_target'], row['design'], row['priority'], row['detail_and_output'], row['responsible'], row['period'], row['note'], auto_judge_type_id, row['judge'], row['judge_evidence'], row['manager_approval'], row['manager_approval_comment'], row['project_id'], row['phase_id'], row['variation_id'], row['r_parameter_id']), ) 
                value_list = ['target', 'adjusted_target','design','priority','detail_and_output','responsible','period', 'judge', 'manager_approval', 'manager_approval_comment', 'judge_evidence']#山口　R要素増えた分もログ残すように
                query = sql.SQL("""
                        insert into detail_data_rlist values(%s, %s, %s, %s, %s, %s, %s, %s);
                    """)
                for value in value_list:
                    cur.execute(query,(row['project_id'],row['r_parameter_id'], row['phase_id'], row['variation_id'], row['employee_number'], row['update_day'], row['note'], row[value]))
                                   
                
            except psycopg2.Error as e:

                # エラー発生時にロールバック
                self.conn.rollback()
                raise e
                return None
            
        self.conn.commit()
        if cur:
                cur.close()        

    def update_record_sim(self,df):#山口　simテーブル交信用 12/3
        cur = None
        for index, row in df.iterrows():
            try:
                cur = self.conn.cursor()

                query = sql.SQL("""
                    INSERT INTO detail_data_sim VALUES(%s, %s, %s, %s, %s)
                """)
                cur.execute(query, (row['id'], row['employee_number'], row['update_day'], row['user_memo'], row['value']))
                #山口　テーブル分割に伴い編集10/22
                query = sql.SQL("""
                    UPDATE test_project_senario_parameter
                    SET 
                        updated_value = %s
                       
                    WHERE id = %s
                """)
                print(query)
                cur.execute(query, (row['value'], row['id'])) #値の編集　山口

            
            except InterfaceError as e:
                raise e
                # 接続が閉じられている場合、再接続を試みる
                self.conn = self.create_connection()
                if self.conn:
                    return self.column_to_list(query)
                else:
                    return None
            except psycopg2.Error as e:
                
                # エラー発生時にロールバック
                self.conn.rollback()
                raise e
                return None
            
        self.conn.commit()
        if cur:
                cur.close()        
        

    def column_to_list(self,query):
        cur = None
        try:
            cur = self.conn.cursor()
            # クエリを実行
            cur.execute(query)
            # データを取得
            rows = cur.fetchall()
            # リストに変換
            result_list = [row[0] for row in rows]
            return result_list
            # カーソルと接続を閉じる
        except InterfaceError as e:
            # 接続が閉じられている場合、再接続を試みる
            self.conn = self.create_connection()
            if self.conn:
                return self.column_to_list(query)
            else:
                return None
        except psycopg2.Error as e:
            # エラー発生時にロールバック
            self.conn.rollback()
            return None
        finally:
            # カーソルを閉じる
            if cur:
                cur.close()

    def get_project(self, query_type, select_list = [], select_list2 = [], select_list3 = [],select_list4 = []):
        
        if query_type == "architecture_name":
            query = "select distinct(architecturename) from architecture;"
            result = self.column_to_list(query)
            return result
        
        if query_type == "z_model_code":
            if select_list:
                select_list_str = ', '.join(f"'{item}'" for item in select_list)
                # クエリを作成
                query = f"""
                        SELECT DISTINCT pjf.project_code
                        FROM architecture AS ar
                        JOIN setup AS stp ON ar.id = stp.architecture_id
                        JOIN project_info AS pjf ON stp.id = pjf.setup_id
                        WHERE ar.architecturename IN ({select_list_str});
                        """
                result = self.column_to_list(query)
                return result
            else:
                return []

        elif query_type == "destination":
            if select_list:
                # リストの要素をシングルクォートで囲んでカンマで結合
                select_list_str = ', '.join(f"'{item}'" for item in select_list)

                query = f"""
                        SELECT DISTINCT dest.destination
                        FROM project_info AS pjf
                        JOIN setup AS stp ON pjf.setup_id = stp.id
                        JOIN destination AS dest ON stp.destination_id = dest.id
                        WHERE pjf.project_code IN ({select_list_str});
                        """
                result = self.column_to_list(query)
                
                return result
            else:
                return []

        elif query_type == "drive_system":
            if select_list and select_list2:
                # リストの要素をシングルクォートで囲んでカンマで結合
                select_list_str = ', '.join(f"'{item}'" for item in select_list)
                select_list_str2 = ', '.join(f"'{item}'" for item in select_list2)

                query = f"""
                        SELECT DISTINCT dt.drivetrain
                        FROM project_info AS pjf
                        JOIN setup AS stp ON pjf.setup_id = stp.id
                        JOIN destination AS dest ON dest.id = stp.destination_id
                        JOIN drivetrain AS dt ON stp.drivetrain_id = dt.id
                        WHERE pjf.project_code IN ({select_list_str})
                        AND dest.destination IN ({select_list_str2});
                        """
                result = self.column_to_list(query)
                return result
            else:
                return []
        elif query_type == "project_number":
            if select_list and select_list2 and select_list3:
                # リストの要素をシングルクォートで囲んでカンマで結合
                select_list_str = ', '.join(f"'{item}'" for item in select_list)
                select_list_str2 = ', '.join(f"'{item}'" for item in select_list2)
                select_list_str3 = ', '.join(f"'{item}'" for item in select_list3)

                # クエリを作成
                query = f"""select distinct(z_number) from dialog_list
                        where z_model_code in ({select_list_str}) and
                              z_destination in ({select_list_str2}) and
                              z_drive_system in ({select_list_str3}) ;"""
                result = self.column_to_list(query)
                return result
            else:
                return []
        elif query_type == "project_lot":
            if select_list and select_list2 and select_list3:
                # リストの要素をシングルクォートで囲んでカンマで結合
                select_list_str = ', '.join(f"'{item}'" for item in select_list)
                select_list_str2 = ', '.join(f"'{item}'" for item in select_list2)
                select_list_str3 = ', '.join(f"'{item}'" for item in select_list3)

                query = f"""
                        SELECT DISTINCT lt.lot
                        FROM project_info AS pjf
                        JOIN setup AS stp ON pjf.setup_id = stp.id
                        JOIN destination AS dest ON dest.id = stp.destination_id
                        JOIN drivetrain AS dt ON stp.drivetrain_id = dt.id
                        JOIN lot AS lt ON pjf.lot_id = lt.id
                        WHERE pjf.project_code IN ({select_list_str})
                        AND dest.destination IN ({select_list_str2})
                        AND dt.drivetrain IN ({select_list_str3});
                        """
                result = self.column_to_list(query)
                return result
            else:
                return []
        elif query_type == "phase_list":
            if select_list and select_list2 and select_list3 and select_list4:
                # リストの要素をシングルクォートで囲んでカンマで結合
                select_list_str = ', '.join(f"'{item}'" for item in select_list)
                select_list_str2 = ', '.join(f"'{item}'" for item in select_list2)
                select_list_str3 = ', '.join(f"'{item}'" for item in select_list3)
                select_list_str4 = ', '.join(f"'{item}'" for item in select_list4)

                query = f"""
                        SELECT DISTINCT ph.phase
                        FROM project_info AS pjf
                        JOIN setup AS stp ON pjf.setup_id = stp.id
                        JOIN destination AS dest ON dest.id = stp.destination_id
                        JOIN drivetrain AS dt ON stp.drivetrain_id = dt.id
                        JOIN lot AS lt ON pjf.lot_id = lt.id
                        JOIN project_parameter AS pjp on pjp.project_id = pjf.id
                        JOIN phase as ph on ph.id = pjp.phase_id
                        WHERE pjf.project_code IN ({select_list_str})
                        AND dest.destination IN ({select_list_str2})
                        AND dt.drivetrain IN ({select_list_str3})
                        AND lt.lot IN ({select_list_str4});
                        """
                result = self.column_to_list(query)
                return result
            else:
                return []
        # #山口　sim表用にVariationListを返す機能 12/1
        # elif query_type == "variation_list":
        #     if select_list and select_list2:
        #         select_list_str = ', '.join(f"'{item}'" for item in select_list)
        #         select_list_str2 = ', '.join(f"'{item}'" for item in select_list2)
        #         select_list_str3 = ', '.join(f"'{item}'" for item in select_list3)
        #         query = f"""select distinct(z_wp_name_get_str) from se_project_record_plz
        #                 where z_prj_number in ({select_list_str}) and 
        #                       z_name in ({select_list_str2}) and
        #                       z_class_name_get_str in ({select_list_str3}) and
        #                       z_wp_name_get_str IS NOT NULL AND z_wp_name_get_str <> '';"""
        #         print('var query: ', query)
        #         result = self.column_to_list(query)
        #         return result
        #     else:
        #         return []

        #山口　sim表用にVariationListを返す機能 12/1
        elif query_type == "variation_list":
            if select_list and select_list2:
                select_list_str = ', '.join(f"'{item}'" for item in select_list)
                select_list_str2 = ', '.join(f"'{item}'" for item in select_list2)
                select_list_str3 = ', '.join(f"'{item}'" for item in select_list3)
                select_list_str4 = ', '.join(f"'{item}'" for item in select_list4)
                print("PHASE"+select_list_str4)
                query = f"""select distinct(z_wp_name_get_str) from se_project_record_plz
                        where project_code in ({select_list_str}) and 
                              z_drive_system in ({select_list_str2}) and 
                              z_name in ({select_list_str3}) and
                              z_class_name_get_str in ({select_list_str4}) and
                              z_wp_name_get_str IS NOT NULL AND z_wp_name_get_str <> '';"""
                print(query)
                result = self.column_to_list(query)
                return result
            else:
                return []
        else:
            return []
        
    #07/07 Kyaw
    def get_se_proj_info_query(self,select_list_str,select_list_str2,select_list_str3,select_list_str4,select_list_str5):
        connection = self.conn
        query = f"""
                SELECT DISTINCT on (se.z_prj_number,
					se.z_name,
					se.z_class_name_get_str,
					se.z_wp_name_get_str,
                   	se.z_destination,
					se.z_drive_system,
					wp_order, modified_string)
					se.z_prj_number,
					se.z_name,
					se.z_class_name_get_str,
					se.project_id,                                                                      
                    se.se_parameter_id,    
                    se.phase_id,         
                    se.variation_id,
                    va.variation,
					se.z_wp_name_get_str,
                   	se.z_destination,
					se.z_drive_system,
                    pjf.project_code,
					CASE 
	                    WHEN detail.update_day IS NOT NULL THEN LEFT(CAST(detail.update_day AS VARCHAR), 10) 
	                    ELSE NULL 
	                END as update_day,
	                CONCAT(user_table.section_code, ' ', user_table.contac_person_first_name, ' ',user_table.contac_person_last_name) as edited_user,
	                approve.state_name,
	                detail.user_memo,
                    CASE 
						WHEN se.z_wp_name_get_str ~ '\d' THEN CAST(regexp_replace(se.z_wp_name_get_str, '\D', '', 'g') AS INTEGER)
					END AS wp_order,
                    replace(se.z_wp_name_get_str,'Variation#', '') AS modified_string
                FROM se_project_record_plz as se
                INNER JOIN project_info AS pjf on se.project_id = pjf.id
                INNER JOIN phase as ph on ph.id = se.phase_id
                INNER JOIN variation va on va.id = se.variation_id
				inner join
					(select distinct on (z_paravalueid) * from detail_data order by z_paravalueid, update_day desc) as detail
                on 
                    se.z_paravalueid = detail.z_paravalueid
                left outer join
	                user_table 
	            on
	                detail.employee_number = user_table.employee_number
	            inner join
	                approval_status_table as approve
	            on
	                detail.approval_status = approve.state_key
                WHERE pjf.project_code IN ({select_list_str})
                AND se.z_destination IN ({select_list_str2})
                AND se.z_drive_system IN ({select_list_str3})
                AND se.z_name IN ({select_list_str4})
                AND ph.phase IN ({select_list_str5})
                AND se.z_class_name_get_str IS NOT NULL
                AND se.z_class_name_get_str <> ''
                ORDER BY se.z_prj_number, se.z_class_name_get_str, wp_order;"""

        prj_info_list = pd.read_sql_query(query, connection)
        variation_unique = prj_info_list['variation'].drop_duplicates().tolist() 
        st.session_state['selectoption6'] = variation_unique
        print('query::', query)
        return prj_info_list
        

# # CAST(REPLACE(SUBSTRING(se.z_wp_name_get_str FROM POSITION('#' IN se.z_wp_name_get_str) + 1), '-', '') AS INTEGER) 
#     def posgre_get_date(self, select_list = [], select_list2 = [], select_list3 = [],select_list4 = [],select_list5 = []):#山口 ログ残し追加 12/3
#         connection = self.conn
#         select_list_str = ', '.join(f"'{item}'" for item in select_list)
#         select_list_str2 = ', '.join(f"'{item}'" for item in select_list2)
#         select_list_str3 = ', '.join(f"'{item}'" for item in select_list3)
#         select_list_str4 = ', '.join(f"'{item}'" for item in select_list4)
#         select_list_str5 = ', '.join(f"'{item}'" for item in select_list5)
#         self.set_condition_log(select_list_str, select_list_str2, select_list_str3, 'Null', st.session_state.username)
#         #山口　ロット情報ほしいためここで追加10/09
#         #山口　日付、更新者、ステータスも欲しい10/10
#         #山口　テーブル分割に伴い編集10/21
#         #山口　z_lot必要なし？
#         #山口　新しいUIでほぼ確実に最初はこの関数でのデータ取得を行うようになった、なのでこの中でVariationもsession_stateに記録しておく
#         # query = f"""
#         #         SELECT DISTINCT on (se.z_prj_number,
# 		# 			se.z_name,
# 		# 			se.z_class_name_get_str,
# 		# 			se.z_wp_name_get_str,
#         #            	se.z_destination,
# 		# 			se.z_drive_system,
# 		# 			wp_order, modified_string)
# 		# 			se.z_prj_number,
# 		# 			se.z_name,
# 		# 			se.z_class_name_get_str,
# 		# 			se.project_id,                                                                      
#         #             se.se_parameter_id,    
#         #             se.phase_id,         
#         #             se.variation_id,
#         #             va.variation,
# 		# 			se.z_wp_name_get_str,
#         #            	se.z_destination,
# 		# 			se.z_drive_system,
#         #             pjf.project_code,
# 		# 			CASE 
# 	    #                 WHEN detail.update_day IS NOT NULL THEN LEFT(CAST(detail.update_day AS VARCHAR), 10) 
# 	    #                 ELSE NULL 
# 	    #             END as update_day,
# 	    #             CONCAT(user_table.section_code, ' ', user_table.contac_person_first_name, ' ',user_table.contac_person_last_name) as edited_user,
# 	    #             approve.state_name,
# 	    #             detail.user_memo,
#         #             CASE 
# 		# 				WHEN se.z_wp_name_get_str ~ '\d' THEN CAST(regexp_replace(se.z_wp_name_get_str, '\D', '', 'g') AS INTEGER)
# 		# 			END AS wp_order,
#         #             replace(se.z_wp_name_get_str,'Variation#', '') AS modified_string
#         #         FROM se_project_record_plz as se
#         #         INNER JOIN project_info AS pjf on se.project_id = pjf.id
#         #         INNER JOIN phase as ph on ph.id = se.phase_id
#         #         INNER JOIN variation va on va.id = se.variation_id
# 		# 		inner join
# 		# 			(select distinct on (z_paravalueid) * from detail_data order by z_paravalueid, update_day desc) as detail
#         #         on 
#         #             se.z_paravalueid = detail.z_paravalueid
#         #         left outer join
# 	    #             user_table 
# 	    #         on
# 	    #             detail.employee_number = user_table.employee_number
# 	    #         inner join
# 	    #             approval_status_table as approve
# 	    #         on
# 	    #             detail.approval_status = approve.state_key
#         #         WHERE pjf.project_code IN ({select_list_str})
#         #         AND se.z_destination IN ({select_list_str2})
#         #         AND se.z_drive_system IN ({select_list_str3})
#         #         AND se.z_name IN ({select_list_str4})
#         #         AND ph.phase IN ({select_list_str5})
#         #         AND se.z_class_name_get_str IS NOT NULL
#         #         AND se.z_class_name_get_str <> ''
#         #         ORDER BY se.z_prj_number, se.z_class_name_get_str, wp_order;"""

#         # prj_info_list = pd.read_sql_query(query, connection)
#         prj_info_list = self.get_se_proj_info_query(select_list_str,select_list_str2,select_list_str3,select_list_str4,select_list_str5) #07/07 Kyaw
#         # print(query)
#         #posgre_get_rlistのdf_selectsの設定をこの関数内でもやりたい5/1
#         df_selects = prj_info_list[['project_id','phase_id','variation_id','z_drive_system', 'z_class_name_get_str', 'z_wp_name_get_str']].drop_duplicates()
#         df_selects.columns = ['project_id','phase_id','variation_id','drivetrain', 'phase', 'variation']
#         if len(df_selects) >1:
#             df_selects = df_selects.head(1)
#         st.session_state.df_selects = df_selects
        
#         # サブクエリのテンプレート
#         # サブクエリのテンプレート 山口　detail_dataとの内部結合までに、各IDについての最新の交信データのみを整理するように変更 更新情報を返すように変更10/11 _を;に変更　10/25
#         #山口　テーブル分割に伴い編集10/21
#         #山口　マップURLを拾う 11/1
#         #山口 各IDを拾いたい 11/13 request median参照方法も変える
#         #山口　order by a.z_paravalueidを追記した 12/6
#         subquery_template = """
#             (select
#                 a.z_paravalueid                                                                   AS "{column1};z_paravalueid;{co}{var}",
#                 a.project_id                                                                      AS "{column1};project_id;{co}{var}",
#                 a.se_parameter_id                                                                 AS "{column1};se_parameter_id;{co}{var}",
#                 a.phase_id                                                                        AS "{column1};phase_id;{co}{var}",
#                 a.variation_id                                                                    AS "{column1};variation_id;{co}{var}",
#                 a.z_prj_number                                                                    AS "{column1};z_prj_number;{co}{var}",
#                 a.z_parent_paraitem                                                               AS "{column1};z_parent_paraitem;{co}{var}",
#                 a.z_child_paraitem                                                                AS "{column1};z_child_paraitem;{co}{var}",
#                 a.z_unit                                                                          AS "{column1};z_unit;{co}{var}",
#                 replace(a.z_unit, 'm#00B2', '²')                                                  AS "{column1};z_unit_copy;{co}{var}",
#                 a.z_wp_name_get_str                                                               AS "{column1};z_wp_name_get_str;{co}{var}",
#                 a.z_request_median                                                                AS "{column1};z_request_median;{co}{var}",
#                 CONCAT(c.section_code, ' ', 
#                     c.contac_person_first_name, ' ',
#                     c.contac_person_last_name)                                                    AS "{column1};contac_user;{co}{var}",
#                 CONCAT(c.section_code, ' ', 
#                     c.contac_person_first_name, ' ',
#                     c.contac_person_last_name)                                                    AS "{column1};edited_user;{co}{var}",
#                 CASE 
#                     WHEN b.update_day IS NOT NULL THEN LEFT(CAST(b.update_day AS VARCHAR), 10) 
#                     ELSE NULL 
#                 END                                                                               AS "{column1};update_day;{co}{var}",
#                 a.z_note                                                                          AS "{column1};z_note;{co}{var}",
#                 d.state_name                                                                      AS "{column1};state_name;{co}{var}",
#                 b.employee_number                                                                 AS "{column1};employee_number;{co}{var}",
#                 b.user_memo                                                                       AS "{column1};user_memo;{co}{var}",
#                 a.URL                                                                             AS "{column1};URL;{co}{var}",
#                 ARRAY[
#                     COALESCE(a.z_parent_paraitem, ''),
#                     COALESCE(a.z_child_paraitem, '')
#                 ]::TEXT[]                                                                         AS "param{alias}"
   
#             from
#                 se_project_record_plz as a
#             inner join
#                 (select distinct on (z_paravalueid) * from detail_data order by z_paravalueid, update_day desc) as b
#                 on 
#                     a.z_paravalueid = b.z_paravalueid
#             inner join
#                 user_table as c
#                 on
#                     b.employee_number = c.employee_number
#             inner join
#                 approval_status_table as d
#                 on
#                     b.approval_status = d.state_key
#             where a.z_wp_name_get_str = '{var}'
#                 and a.z_prj_number = '{column1}'
#                 and a.z_name = '{column2}'
#                 and a.z_class_name_get_str = '{column3}'

#             order by a.z_paravalueid
#             ) as {alias} 
#         """
#         join_template = """
#         on s0p."{column1};z_parent_paraitem;{co1}{var1}" = {alias}."{column2};z_parent_paraitem;{co2}{var2}" and
#         s0p."{column1};z_child_paraitem;{co1}{var1}" = {alias}."{column2};z_child_paraitem;{co2}{var2}" and
#         s0p."{column1};z_unit;{co1}{var1}" = {alias}."{column2};z_unit;{co2}{var2}"
#         """
#         join_template = """
#         on s0p."{column1};z_parent_paraitem;{co1}{var1}" = {alias}."{column2};z_parent_paraitem;{co2}{var2}" and
#         s0p."{column1};z_child_paraitem;{co1}{var1}" = {alias}."{column2};z_child_paraitem;{co2}{var2}" and
#         s0p."{column1};z_unit;{co1}{var1}" = {alias}."{column2};z_unit;{co2}{var2}"
#         """

#         # サブクエリの生成
#         subqueries = []				

#         for i, row in prj_info_list.iterrows():
#             if i == 0:
#                 subqueries = r"select * from"
#             if i > 0:
#                 subqueries += "FULL OUTER JOIN"

#             subqueries+=subquery_template.format(
#                 column1=row['z_prj_number'],
#                 column2=row['z_name'],
#                 column3=row['z_class_name_get_str'],
#                 co=row['z_class_name_get_str'][0] + row['z_class_name_get_str'][-1], #山口　列名に追加する文字列、フェーズ名をそのまま貼り付けると長さ制限にかかり機能しなくなるため、暫定的に最初と最後の文字のみをくっつける　11/6
#                 var=row['z_wp_name_get_str'],
#                 alias='s'+str(i)+'p')

#             if i > 0:
#                 subqueries+=join_template.format(
#                     column1=prj_info_list['z_prj_number'][0],
#                     column2=prj_info_list['z_prj_number'][i],
#                     co1=prj_info_list['z_class_name_get_str'][0][0] + prj_info_list['z_class_name_get_str'][0][-1], #山口　列名に追加する文字列、フェーズ名をそのまま貼り付けると長さ制限にかかり機能しなくなるため、暫定的に最初と最後の文字のみをくっつける　11/6
#                     co2=prj_info_list['z_class_name_get_str'][i][0] + prj_info_list['z_class_name_get_str'][i][-1], #山口　列名に追加する文字列、フェーズ名をそのまま貼り付けると長さ制限にかかり機能しなくなるため、暫定的に最初と最後の文字のみをくっつける　11/6
#                     var1=prj_info_list['z_wp_name_get_str'][0],
#                     var2=prj_info_list['z_wp_name_get_str'][i],
#                     alias='s'+str(i)+'p'
#                     )
#         # print('subb:: ',subqueries)#山口デバック用
#         print(subqueries)
#         se_data_stuck = pd.read_sql_query(subqueries, connection)
        
#         print(prj_info_list)
#         #山口　取得したDFから編集情報を列にまとめる 10/25 _->;に変更
#         for i, row in prj_info_list.iterrows():
#             column1=row['z_prj_number']
#             var=row['z_wp_name_get_str']
#             co=row['z_class_name_get_str'][0] + row['z_class_name_get_str'][-1] #山口　列名に追加する文字列、フェーズ名をそのまま貼り付けると長さ制限にかかり機能しなくなるため、暫定的に最初と最後の文字のみをくっつける　11/6
#             print(column1)
#             se_data_stuck[column1 + ';edited_info;' +co+ var] = "更新日：" + se_data_stuck[column1 + ';update_day;' +co+ var] + "\n更新者：" + se_data_stuck[column1 + ';edited_user;' +co+ var] + "\nメモ：" + se_data_stuck[column1 + ';user_memo;'+co + var]
#             se_data_stuck[column1 + ';selected;' +co+ var] = False #山口　選択された項目を表すためのBooleanれつ追加　10/25
#         #山口　Variationをselectoption6に入れることを忘れない
#         # variation_unique = prj_info_list['variation'].drop_duplicates().tolist() 
#         # st.session_state['selectoption6'] = variation_unique  #07/07 Kyaw: Move to shared function
        
#         return prj_info_list, se_data_stuck


    def posgre_get_date(self, select_list = [], select_list2 = [], select_list3 = [],select_list4 = [],select_list5 = []):#山口 ログ残し追加 12/3
        connection = self.conn
        select_list_str = ', '.join(f"'{item}'" for item in select_list)
        select_list_str2 = ', '.join(f"'{item}'" for item in select_list2)
        select_list_str3 = ', '.join(f"'{item}'" for item in select_list3)
        select_list_str4 = ', '.join(f"'{item}'" for item in select_list4)
        select_list_str5 = ', '.join(f"'{item}'" for item in select_list5)
        self.set_condition_log(select_list_str, select_list_str2, select_list_str3, 'Null', st.session_state.username)
        #山口　ロット情報ほしいためここで追加10/09
        #山口　日付、更新者、ステータスも欲しい10/10
        #山口　テーブル分割に伴い編集10/21
        #山口　z_lot必要なし？
        #山口　新しいUIでほぼ確実に最初はこの関数でのデータ取得を行うようになった、なのでこの中でVariationもsession_stateに記録しておく
        # query = f"""
        #         SELECT DISTINCT on (se.z_prj_number,
		# 			se.z_name,
		# 			se.z_class_name_get_str,
		# 			se.z_wp_name_get_str,
        #            	se.z_destination,
		# 			se.z_drive_system,
		# 			wp_order, modified_string)
		# 			se.z_prj_number,
		# 			se.z_name,
		# 			se.z_class_name_get_str,
		# 			se.project_id,                                                                      
        #             se.se_parameter_id,    
        #             se.phase_id,         
        #             se.variation_id,
        #             va.variation,
		# 			se.z_wp_name_get_str,
        #            	se.z_destination,
		# 			se.z_drive_system,
        #             pjf.project_code,
		# 			CASE 
	    #                 WHEN detail.update_day IS NOT NULL THEN LEFT(CAST(detail.update_day AS VARCHAR), 10) 
	    #                 ELSE NULL 
	    #             END as update_day,
	    #             CONCAT(user_table.section_code, ' ', user_table.contac_person_first_name, ' ',user_table.contac_person_last_name) as edited_user,
	    #             approve.state_name,
	    #             detail.user_memo,
        #             CASE 
		# 				WHEN se.z_wp_name_get_str ~ '\d' THEN CAST(regexp_replace(se.z_wp_name_get_str, '\D', '', 'g') AS INTEGER)
		# 			END AS wp_order,
        #             replace(se.z_wp_name_get_str,'Variation#', '') AS modified_string
        #         FROM se_project_record_plz as se
        #         INNER JOIN project_info AS pjf on se.project_id = pjf.id
        #         INNER JOIN phase as ph on ph.id = se.phase_id
        #         INNER JOIN variation va on va.id = se.variation_id
		# 		inner join
		# 			(select distinct on (z_paravalueid) * from detail_data order by z_paravalueid, update_day desc) as detail
        #         on 
        #             se.z_paravalueid = detail.z_paravalueid
        #         left outer join
	    #             user_table 
	    #         on
	    #             detail.employee_number = user_table.employee_number
	    #         inner join
	    #             approval_status_table as approve
	    #         on
	    #             detail.approval_status = approve.state_key
        #         WHERE pjf.project_code IN ({select_list_str})
        #         AND se.z_destination IN ({select_list_str2})
        #         AND se.z_drive_system IN ({select_list_str3})
        #         AND se.z_name IN ({select_list_str4})
        #         AND ph.phase IN ({select_list_str5})
        #         AND se.z_class_name_get_str IS NOT NULL
        #         AND se.z_class_name_get_str <> ''
        #         ORDER BY se.z_prj_number, se.z_class_name_get_str, wp_order;"""

        # prj_info_list = pd.read_sql_query(query, connection)
        # print(query)
        prj_info_list = self.get_se_proj_info_query(select_list_str,select_list_str2,select_list_str3,select_list_str4,select_list_str5) #07/07 Kyaw
        #posgre_get_rlistのdf_selectsの設定をこの関数内でもやりたい5/1
        df_selects = prj_info_list[['project_id','phase_id','variation_id','z_drive_system', 'z_class_name_get_str', 'z_wp_name_get_str']].drop_duplicates()
        df_selects.columns = ['project_id','phase_id','variation_id','drivetrain', 'phase', 'variation']
        if len(df_selects) >1:
            df_selects = df_selects.head(1)
        st.session_state.df_selects = df_selects
        
        # サブクエリのテンプレート
        # サブクエリのテンプレート 山口　detail_dataとの内部結合までに、各IDについての最新の交信データのみを整理するように変更 更新情報を返すように変更10/11 _を;に変更　10/25
        #山口　テーブル分割に伴い編集10/21
        #山口　マップURLを拾う 11/1
        #山口 各IDを拾いたい 11/13 request median参照方法も変える
        #山口　order by a.z_paravalueidを追記した 12/6
        subquery_template = """
            (select
                a.z_paravalueid                                                                   AS "{column1};z_paravalueid;{co}{var}",
                a.project_id                                                                      AS "{column1};project_id;{co}{var}",
                a.se_parameter_id                                                                 AS "{column1};se_parameter_id;{co}{var}",
                a.phase_id                                                                        AS "{column1};phase_id;{co}{var}",
                a.variation_id                                                                    AS "{column1};variation_id;{co}{var}",
                a.z_prj_number                                                                    AS "{column1};z_prj_number;{co}{var}",
                a.z_parent_paraitem                                                               AS "{column1};z_parent_paraitem;{co}{var}",
                a.z_child_paraitem                                                                AS "{column1};z_child_paraitem;{co}{var}",
                a.z_unit                                                                          AS "{column1};z_unit;{co}{var}",
                replace(a.z_unit, 'm#00B2', '²')                                                  AS "{column1};z_unit_copy;{co}{var}",
                a.z_wp_name_get_str                                                               AS "{column1};z_wp_name_get_str;{co}{var}",
                a.z_request_median                                                                AS "{column1};z_request_median;{co}{var}",
                CONCAT(c.section_code, ' ', 
                    c.contac_person_first_name, ' ',
                    c.contac_person_last_name)                                                    AS "{column1};contac_user;{co}{var}",
                CONCAT(c.section_code, ' ', 
                    c.contac_person_first_name, ' ',
                    c.contac_person_last_name)                                                    AS "{column1};edited_user;{co}{var}",
                CASE 
                    WHEN b.update_day IS NOT NULL THEN LEFT(CAST(b.update_day AS VARCHAR), 10) 
                    ELSE NULL 
                END                                                                               AS "{column1};update_day;{co}{var}",
                a.z_note                                                                          AS "{column1};z_note;{co}{var}",
                d.state_name                                                                      AS "{column1};state_name;{co}{var}",
                b.employee_number                                                                 AS "{column1};employee_number;{co}{var}",
                b.user_memo                                                                       AS "{column1};user_memo;{co}{var}",
                a.URL                                                                             AS "{column1};URL;{co}{var}",
                ARRAY[
                    COALESCE(a.z_parent_paraitem, ''),
                    COALESCE(a.z_child_paraitem, '')
                ]::TEXT[]                                                                         AS "param{alias}"
   
            from
                se_project_record_plz as a
            inner join
                (select distinct on (z_paravalueid) * from detail_data order by z_paravalueid, update_day desc) as b
                on 
                    a.z_paravalueid = b.z_paravalueid
            inner join
                user_table as c
                on
                    b.employee_number = c.employee_number
            inner join
                approval_status_table as d
                on
                    b.approval_status = d.state_key
            where a.variation_id = '{var}' --バリエーション名からIDに変えた
                and a.z_prj_number = '{column1}'
                and a.z_name = '{column2}'
                and a.z_class_name_get_str = '{column3}'

            order by a.z_paravalueid
            ) as {alias} 
        """
        join_template = """
        on s0p."{column1};z_parent_paraitem;{co1}{var1}" = {alias}."{column2};z_parent_paraitem;{co2}{var2}" and
        s0p."{column1};z_child_paraitem;{co1}{var1}" = {alias}."{column2};z_child_paraitem;{co2}{var2}" and
        s0p."{column1};z_unit;{co1}{var1}" = {alias}."{column2};z_unit;{co2}{var2}"
        """
        join_template = """
        on s0p."{column1};z_parent_paraitem;{co1}{var1}" = {alias}."{column2};z_parent_paraitem;{co2}{var2}" and
        s0p."{column1};z_child_paraitem;{co1}{var1}" = {alias}."{column2};z_child_paraitem;{co2}{var2}" and
        s0p."{column1};z_unit;{co1}{var1}" = {alias}."{column2};z_unit;{co2}{var2}"
        """

        # サブクエリの生成
        subqueries = []				

        for i, row in prj_info_list.iterrows():
            if i == 0:
                subqueries = r"select * from"
            if i > 0:
                subqueries += "FULL OUTER JOIN"

            subqueries+=subquery_template.format(
                column1=row['z_prj_number'],
                column2=row['z_name'],
                column3=row['z_class_name_get_str'],
                co=row['phase_id'], #山口　列名に追加する文字列、フェーズ名をそのまま貼り付けると長さ制限にかかり機能しなくなるため、暫定的に最初と最後の文字のみをくっつける　11/6　ここPhaseID_Variation_idでよくない？？
                var=row['variation_id'],
                alias='s'+str(i)+'p')

            if i > 0:
                subqueries+=join_template.format(
                    column1=prj_info_list['z_prj_number'][0],
                    column2=prj_info_list['z_prj_number'][i],
                    co1=prj_info_list['phase_id'][0], #山口　列名に追加する文字列、フェーズ名をそのまま貼り付けると長さ制限にかかり機能しなくなるため、暫定的に最初と最後の文字のみをくっつける　11/6
                    co2=prj_info_list['phase_id'][i], #山口　列名に追加する文字列、フェーズ名をそのまま貼り付けると長さ制限にかかり機能しなくなるため、暫定的に最初と最後の文字のみをくっつける　11/6
                    var1=prj_info_list['variation_id'][0],
                    var2=prj_info_list['variation_id'][i],
                    alias='s'+str(i)+'p'
                    )
        # print('subb:: ',subqueries)#山口デバック用
        print(subqueries)
        se_data_stuck = pd.read_sql_query(subqueries, connection)
        
        print(prj_info_list)
        #山口　取得したDFから編集情報を列にまとめる 10/25 _->;に変更
        for i, row in prj_info_list.iterrows():
            column1=row['z_prj_number']
            var=row['variation_id']
            co=row['phase_id'] #山口　列名に追加する文字列、フェーズ名をそのまま貼り付けると長さ制限にかかり機能しなくなるため、暫定的に最初と最後の文字のみをくっつける　11/6
            print(column1)
            se_data_stuck[column1 + ';edited_info;' +str(co)+ str(var)] = "更新日：" + se_data_stuck[column1 + ';update_day;' +str(co)+ str(var)] + "\n更新者：" + se_data_stuck[column1 + ';edited_user;' +str(co)+ str(var)] + "\nメモ：" + se_data_stuck[column1 + ';user_memo;'+str(co) + str(var)]
            se_data_stuck[column1 + ';selected;' +str(co)+ str(var)] = False #山口　選択された項目を表すためのBooleanれつ追加　10/25
        #山口　Variationをselectoption6に入れることを忘れない
        # variation_unique = prj_info_list['variation'].drop_duplicates().tolist() 
        # st.session_state['selectoption6'] = variation_unique   #07/07 Kyaw: Move to shared function
        
        return prj_info_list, se_data_stuck
    
    #山口　simデータ取得用　12/2 仕向け、駆動方式含め絞り込むように 2/13
    def posgre_get_data_sim(self, select_list = [], select_list2 = [], select_list3 = [], select_list4 = [], select_list5 = []): #チョー　select_list6を消した 03/10
        connection = self.conn
        select_list_str = ', '.join(f"'{item}'" for item in select_list)#プロジェクト
        select_list_str2 = ', '.join(f"'{item}'" for item in select_list2)#仕向け
        select_list_str3 = ', '.join(f"'{item}'" for item in select_list3)#駆動方式
        select_list_str4 = ', '.join(f"'{item}'" for item in select_list4)#lot
        select_list_str5 = ', '.join(f"'{item}'" for item in select_list5)#phase
        # select_list_str6 = ', '.join(f"'{item}'" for item in select_list6)#valiation
        
        query = f"""
                SELECT DISTINCT on (se.project_id,
					se.lot,
					se.phase,
					se.variation,
					se.study_id)
					se.project_id,
					se.lot,
					se.phase,
                    se.phase_id,
					se.study_id,
					se.variation,
                    se.variation_id,
                   	se.destination,
					se.drivetrain,
					se.project_code,
                    se.overall_value,
					CASE 
	                    WHEN detail.update_day IS NOT NULL THEN LEFT(CAST(detail.update_day AS VARCHAR), 10) 
	                    ELSE NULL 
	                END as update_day,
	                CONCAT(user_table.section_code, ' ', user_table.contac_person_first_name, ' ',user_table.contac_person_last_name) as edited_user,
	               
	                detail.user_memo,
                    CASE 
						WHEN se.variation ~ '\d' THEN CAST(regexp_replace(se.variation, '\D', '', 'g') AS INTEGER)
					END AS wp_order,
                    replace(se.variation,'Variation#', '') AS modified_string
                FROM test_senario_project_record as se
				
				left outer join
					(select distinct on (id) * from detail_data_sim order by id, update_day desc) as detail
                on 
                    se.id = detail.id
                left outer join
	                user_table 
	            on
	                detail.employee_number = user_table.employee_number
	        
                WHERE se.project_code IN ({select_list_str})
                AND se.destination IN ({select_list_str2})
                AND se.drivetrain IN ({select_list_str3})
                AND se.lot IN ({select_list_str4})
                AND se.phase IN ({select_list_str5})
                AND se.phase IS NOT NULL
                AND se.phase <> ''
                AND se.senario_parameter_id=99
                ORDER BY se.project_id, se.lot,  se.phase, se.variation, se.study_id;"""
        print(str(query)) #山口デバック用
        prj_info_list = pd.read_sql_query(query, connection)
        if len(prj_info_list)==0:
            self.get_se_proj_info_query(select_list_str,select_list_str2,select_list_str3,select_list_str4,select_list_str5) #07/07 Kyaw
            return [], []
        print(prj_info_list)
        # サブクエリのテンプレート
        #山口　z_prj_numberは使いたくないためproject_idで代替する, z_noteはなくした12/2
        #山口　元となったSEパラメータ情報も取得する 12/4
        
        
        subquery_template = """
            (select
                a.id                                                                  AS "{column1};id;{co}{var}{study}",
                a.project_id                                                                      AS "{column1};project_id;{co}{var}{study}",
                a.senario_parameter_id                                                                      AS "{column1};senario_parameter_id;{co}{var}{study}",
                a.phase_id                                                                      AS "{column1};phase_id;{co}{var}{study}",
                a.phase                                                                             AS "{column1};phase;{co}{var}{study}",
                a.variation_id                                                                      AS "{column1};variation_id;{co}{var}{study}",
                a.variation                                                                         AS "{column1};variation;{co}{var}{study}",
                a.study_id                                                                        AS "{column1};study_id;{co}{var}{study}",
                a.parameter_name_1                                                               AS "{column1};parameter_name_1;{co}{var}{study}",
                a.parameter_name_2                                                                AS "{column1};parameter_name_2;{co}{var}{study}",
                a.rflcategory                                                                AS "{column1};rflcategory;{co}{var}{study}",
                a.rflid                                                                AS "{column1};rflid;{co}{var}{study}",
                a.parameter_unit                                                                          AS "{column1};parameter_unit;{co}{var}{study}",
                replace(a.parameter_unit, 'm#00B2', '²')                                                  AS "{column1};parameter_unit_copy;{co}{var}{study}",
                a.original_value                                                                AS "{column1};original_value;{co}{var}{study}",
                a.overall_value                                                                AS "{column1};value;{co}{var}{study}",
                CONCAT(c.section_code, ' ', 
                    c.contac_person_first_name, ' ',
                    c.contac_person_last_name)                                                    AS "{column1};contac_user;{co}{var}{study}",
                CONCAT(c.section_code, ' ', 
                    c.contac_person_first_name, ' ',
                    c.contac_person_last_name)                                                    AS "{column1};edited_user;{co}{var}{study}",
                CASE 
                    WHEN b.update_day IS NOT NULL THEN LEFT(CAST(b.update_day AS VARCHAR), 10) 
                    ELSE NULL 
                END                                                                               AS "{column1};update_day;{co}{var}{study}",
                
                
                b.employee_number                                                                 AS "{column1};employee_number;{co}{var}{study}",
                b.user_memo                                                                       AS "{column1};user_memo;{co}{var}{study}",
                ARRAY[
                    COALESCE(a.parameter_name_1, ''),
                    COALESCE(a.rflcategory, ''),
                    COALESCE(a.parameter_name_2, '')
                ]::TEXT[]                                                                         AS "param{alias}"
   
            from
                test_senario_project_record as a
            left outer join
                (select distinct on (id) * from detail_data_sim order by id, update_day desc) as b
                on 
                    a.id = b.id
            left outer join
                user_table as c
                on
                    b.employee_number = c.employee_number
            
            where a.variation = '{var}'
                and a.project_id = '{column1}'
                and a.lot = '{column2}'
                and a.phase = '{column3}'
                and a.variation = '{column4}'
                and a.study_id = '{study}'
            order by a.senario_parameter_id
            ) as {alias} 
        """
        join_template = """
        on s0p."{column1};senario_parameter_id;{co1}{var1}{study1}" = {alias}."{column2};senario_parameter_id;{co2}{var2}{study2}" 
        """
        
        # サブクエリの生成
        subqueries = []				

        for i, row in prj_info_list.iterrows():
            if i == 0:
                subqueries = r"select * from"
            if i > 0:
                subqueries += "FULL OUTER JOIN"

            subqueries+=subquery_template.format(
                column1=row['project_id'],
                column2=row['lot'],
                column3=row['phase'],
                column4=row['variation'],
                study=row['study_id'],
                co=row['phase'][0] + row['phase'][-1], #山口　列名に追加する文字列、フェーズ名をそのまま貼り付けると長さ制限にかかり機能しなくなるため、暫定的に最初と最後の文字のみをくっつける　11/6
                var=row['variation'],
                alias='s'+str(i)+'p')

            if i > 0:
                subqueries+=join_template.format(
                    column1=prj_info_list['project_id'][0],
                    column2=prj_info_list['project_id'][i],
                    co1=prj_info_list['phase'][0][0] + prj_info_list['phase'][0][-1], #山口　列名に追加する文字列、フェーズ名をそのまま貼り付けると長さ制限にかかり機能しなくなるため、暫定的に最初と最後の文字のみをくっつける　11/6
                    co2=prj_info_list['phase'][i][0] + prj_info_list['phase'][i][-1], #山口　列名に追加する文字列、フェーズ名をそのまま貼り付けると長さ制限にかかり機能しなくなるため、暫定的に最初と最後の文字のみをくっつける　11/6
                    var1=prj_info_list['variation'][0],
                    var2=prj_info_list['variation'][i],
                    study1=prj_info_list['study_id'][0],
                    study2=prj_info_list['study_id'][i],
                    alias='s'+str(i)+'p'
                    )
        print(subqueries)#山口デバック用
        se_data_stuck = pd.read_sql_query(subqueries, connection)
        print(se_data_stuck)
        #山口　取得したDFから編集情報を列にまとめる 10/25 _->;に変更
        for i, row in prj_info_list.iterrows():
            column1=row['project_id']
            var=row['variation']
            co=row['phase'][0] + row['phase'][-1] #山口　列名に追加する文字列、フェーズ名をそのまま貼り付けると長さ制限にかかり機能しなくなるため、暫定的に最初と最後の文字のみをくっつける　11/6
            study=row['study_id']
            print(co)
            se_data_stuck[str(column1) + ';edited_info;' +co+ var+study] = "更新日：" + se_data_stuck[str(column1)  + ';update_day;' +co+ var+study] + "\n更新者：" + se_data_stuck[str(column1) + ';edited_user;' +co+ var+study] + "\nメモ：" + se_data_stuck[str(column1)  + ';user_memo;'+co + var+study]
            se_data_stuck[str(column1)  + ';selected;' +co+ var+study] = False #山口　選択された項目を表すためのBooleanれつ追加　10/25
        #params0pはグリッドでのぐるーぴんぐで使用されるが、ほかのスタディでのグルーピングを無視してしまう、そのためparams0pに全スタディの情報を乗っける 3/19
        df_params = se_data_stuck.loc[:,se_data_stuck.columns.str.contains('params')]
        df_params_merged = se_data_stuck['params0p']
        for col in df_params.columns:
            df_params_merged = df_params_merged.fillna(df_params[col])
        #st.write(df_params_merged)
        se_data_stuck['params0p']=df_params_merged

        #新規UIでのPrj選択ではvariationの選択をしなくなったため、selectoption6は空白のリストとなってしまい、新規作成処理でのエラーになった。存在するこの時点でprj_info_list内に存在しているvariationの一覧をselectoption6として代替する　山口 3/21
        variation_unique = prj_info_list['variation'].drop_duplicates().tolist()
        print("==============================")
        print("==============================: ", variation_unique)
        st.session_state['selectoption6'] = variation_unique
        
        return prj_info_list, se_data_stuck
    
    #12/11 #チョー
    def get_td_senario(self, project_id, phase_id, variation_id, study_id, senario_submodel, tdname_list = [], ):
        connection = self.conn
        tdname_value_list = ', '.join(f"'{item}'" for item in tdname_list)
        query = f"""
                    SELECT 
                        tdv.td, 
                        tdv.scope, 
                        tdv.submodel, 
                        tdv.variable_name, 
                        spr.overall_value,
                        spr.parameter_unit,
                        spr.project_id,
                        spr.phase_id,
                        spr.variation_id,
                        spr.study_id
                    FROM 
                        td_variable AS tdv
                    JOIN 
                        test_senario_project_record AS spr 
                    ON 
                        tdv.category = 'SENARIO'
                    AND 
                        tdv.parameter_id = spr.senario_parameter_id
                    AND
                       tdv.scope = spr.scope 
                    WHERE 
                        tdv.td IN ({tdname_value_list})
                    AND
                        spr.project_id = {project_id}
                    AND
                        spr.phase_id = {phase_id}
                    AND
                        spr.variation_id={variation_id}
                    AND
                        spr.study_id='{study_id}';
                """#山口　カテゴリ定義の変更により問い合わせ変えた　12/16
        
        
        print(query)
        td_variable_list = pd.read_sql_query(query, connection)#山口　ここまではSEパラメータのみ、ここからシナリオ系もつけないといけない12/25

        query = f"""
                    select {tdname_value_list} as td, 'Scenarios' as scope,submodel, variable_name, overall_value, parameter_unit, project_id, phase_id, variation_id, study_id
                    FROM
                        parameter_submodel_relation
                    JOIN
                        test_senario_project_record
                    ON
                        parameter_submodel_relation.category = 'SENARIO'
                    AND
                        parameter_submodel_relation.parameter_id = test_senario_project_record.senario_parameter_id
                    WHERE
                        test_senario_project_record.project_id = {project_id}
                    AND
                        test_senario_project_record.phase_id = {phase_id}
                    AND
                        test_senario_project_record.variation_id={variation_id}
                    AND
                        test_senario_project_record.study_id='{study_id}'
                    AND
                        parameter_submodel_relation.submodel='{senario_submodel}';

        """
        print(query)
        senario_variable_list = pd.read_sql_query(query, connection)
        td_variable_list = pd.concat([td_variable_list, senario_variable_list])
        return td_variable_list
    
    #11/25 チョー
    def posgre_get_compare_data(self, select_list = [], select_list2 = [], select_list3 = [], select_list4 = [], select_list5 = [], select_list6 = []):
        connection = self.conn
        select_list_str = ', '.join(f"'{item}'" for item in select_list)
        select_list_str2 = ', '.join(f"'{item}'" for item in select_list2)
        select_list_str3 = ', '.join(f"'{item}'" for item in select_list3)
        select_list_str4 = ', '.join(f"'{item}'" for item in select_list4)
        select_list_str5 = ', '.join(f"'{item}'" for item in select_list5)
        select_list_str6 = ', '.join(f"'{item}'" for item in select_list6)
        
        query = f"""
                SELECT DISTINCT on (se.z_prj_number,
					se.z_name,
					se.z_class_name_get_str,
					se.z_wp_name_get_str,
                   	se.z_destination,
					se.z_drive_system,
					wp_order, modified_string)
					se.z_prj_number,
					se.z_name,
					se.z_class_name_get_str,
					se.project_id,                                                                      
                    se.se_parameter_id,    
                    se.phase_id,         
                    se.variation_id,
					se.z_wp_name_get_str,
                   	se.z_destination,
					se.z_drive_system,
                    pjf.project_code,
					CASE 
	                    WHEN detail.update_day IS NOT NULL THEN LEFT(CAST(detail.update_day AS VARCHAR), 10) 
	                    ELSE NULL 
	                END as update_day,
	                CONCAT(user_table.section_code, ' ', user_table.contac_person_first_name, ' ',user_table.contac_person_last_name) as edited_user,
	                approve.state_name,
	                detail.user_memo,
                    CASE 
						WHEN se.z_wp_name_get_str ~ '\d' THEN CAST(regexp_replace(se.z_wp_name_get_str, '\D', '', 'g') AS INTEGER)
					END AS wp_order,
                    replace(se.z_wp_name_get_str,'Variation#', '') AS modified_string
                FROM se_project_record_plz as se
                INNER JOIN project_info AS pjf on se.project_id = pjf.id
                INNER JOIN phase as ph on ph.id = se.phase_id
				inner join
					(select distinct on (z_paravalueid) * from detail_data order by z_paravalueid, update_day desc) as detail
                on 
                    se.z_paravalueid = detail.z_paravalueid
                left outer join
	                user_table 
	            on
	                detail.employee_number = user_table.employee_number
	            inner join
	                approval_status_table as approve
	            on
	                detail.approval_status = approve.state_key
                WHERE pjf.project_code IN ({select_list_str})
                AND se.z_destination IN ({select_list_str2})
                AND se.z_drive_system IN ({select_list_str3})
                AND se.z_name IN ({select_list_str4})
                AND ph.phase IN ({select_list_str5})
                AND se.z_wp_name_get_str IN ({select_list_str6})
                AND se.z_class_name_get_str IS NOT NULL
                AND se.z_class_name_get_str <> ''
                ORDER BY se.z_prj_number, se.z_class_name_get_str, wp_order;"""
        # print('compare query::',query) #山口デバック用
        prj_info_list = pd.read_sql_query(query, connection)
        
        if len(st.session_state['compare_option6']) > 1:
            if len(st.session_state['compare_option6']) == len(set(st.session_state['compare_option6'])):
                print('condition 1')
                # Set the categorical type and order for z_wp_name_get_str
                prj_info_list['z_wp_name_get_str'] = pd.Categorical(
                    prj_info_list['z_wp_name_get_str'],
                    categories=st.session_state['compare_option6'],  # Use the original order
                    ordered=True
                )
                # Sort by z_wp_name_get_str
                prj_info_list = prj_info_list.sort_values('z_wp_name_get_str').reset_index(drop=True)

            # Check for compare_option5
            elif len(st.session_state['compare_option5']) == len(set(st.session_state['compare_option5'])):
                print('condition 2')
                # Set the categorical type and order for z_class_name_get_str
                prj_info_list['z_class_name_get_str'] = pd.Categorical(
                    prj_info_list['z_class_name_get_str'],
                    categories=st.session_state['compare_option5'],  # Use the original order
                    ordered=True
                )
                # Sort by z_class_name_get_str
                prj_info_list = prj_info_list.sort_values('z_class_name_get_str').reset_index(drop=True)

            # Check for compare_option4
            elif len(st.session_state['compare_option4']) == len(set(st.session_state['compare_option4'])):
                print('condition 3')
                # Set the categorical type and order for z_name
                prj_info_list['z_name'] = pd.Categorical(
                    prj_info_list['z_name'],
                    categories=st.session_state['compare_option4'],  # Use the original order
                    ordered=True
                )
                # Sort by z_name
                prj_info_list = prj_info_list.sort_values('z_name').reset_index(drop=True)

            # Check for compare_option3
            elif len(st.session_state['compare_option3']) == len(set(st.session_state['compare_option3'])):
                print('condition 4')
                # Set the categorical type and order for z_drive_system
                prj_info_list['z_drive_system'] = pd.Categorical(
                    prj_info_list['z_drive_system'],
                    categories=st.session_state['compare_option3'],  # Use the original order
                    ordered=True
                )
                # Sort by z_drive_system
                prj_info_list = prj_info_list.sort_values('z_drive_system').reset_index(drop=True)

            # Check for compare_option2
            elif len(st.session_state['compare_option2']) == len(set(st.session_state['compare_option2'])):
                print('condition 5')
                # Set the categorical type and order for z_destination
                prj_info_list['z_destination'] = pd.Categorical(
                    prj_info_list['z_destination'],
                    categories=st.session_state['compare_option2'],  # Use the original order
                    ordered=True
                )
                # Sort by z_destination
                prj_info_list = prj_info_list.sort_values('z_destination').reset_index(drop=True)

            # Check for compare_option1
            elif len(st.session_state['compare_option1']) == len(set(st.session_state['compare_option1'])):
                print('condition 6')
                # Set the categorical type and order for project_code
                prj_info_list['project_code'] = pd.Categorical(
                    prj_info_list['project_code'],
                    categories=st.session_state['compare_option1'],  # Use the original order
                    ordered=True
                )
                # Sort by project_code
                prj_info_list = prj_info_list.sort_values('project_code').reset_index(drop=True)
        # サブクエリのテンプレート
        # サブクエリのテンプレート 山口　detail_dataとの内部結合までに、各IDについての最新の交信データのみを整理するように変更 更新情報を返すように変更10/11 _を;に変更　10/25
        #山口　テーブル分割に伴い編集10/21
        #山口　マップURLを拾う 11/1
        #山口 各IDを拾いたい 11/13 request median参照方法も変える
        
        # subquery_template = """
        #     (select
        #         a.z_paravalueid                                                                   AS "{column1};z_paravalueid;{co}{var}",
        #         a.project_id                                                                      AS "{column1};project_id;{co}{var}",
        #         a.se_parameter_id                                                                      AS "{column1};se_parameter_id;{co}{var}",
        #         a.phase_id                                                                      AS "{column1};phase_id;{co}{var}",
        #         a.variation_id                                                                      AS "{column1};variation_id;{co}{var}",
        #         a.z_prj_number                                                                    AS "{column1};z_prj_number;{co}{var}",
        #         a.z_parent_paraitem                                                               AS "{column1};z_parent_paraitem;{co}{var}",
        #         a.z_child_paraitem                                                                AS "{column1};z_child_paraitem;{co}{var}",
        #         a.z_unit                                                                          AS "{column1};z_unit;{co}{var}",
        #         replace(a.z_unit, 'm#00B2', '²')                                                  AS "{column1};z_unit_copy;{co}{var}",
        #         a.z_wp_name_get_str                                                               AS "{column1};z_wp_name_get_str;{co}{var}",
        #         a.z_request_median                                                                AS "{column1};z_request_median;{co}{var}",
        #         CONCAT(c.section_code, ' ', 
        #             c.contac_person_first_name, ' ',
        #             c.contac_person_last_name)                                                    AS "{column1};contac_user;{co}{var}",
        #         CONCAT(c.section_code, ' ', 
        #             c.contac_person_first_name, ' ',
        #             c.contac_person_last_name)                                                    AS "{column1};edited_user;{co}{var}",
        #         CASE 
        #             WHEN b.update_day IS NOT NULL THEN LEFT(CAST(b.update_day AS VARCHAR), 10) 
        #             ELSE NULL 
        #         END                                                                               AS "{column1};update_day;{co}{var}",
        #         a.z_note                                                                          AS "{column1};z_note;{co}{var}",
        #         d.state_name                                                                      AS "{column1};state_name;{co}{var}",
        #         b.employee_number                                                                 AS "{column1};employee_number;{co}{var}",
        #         b.user_memo                                                                       AS "{column1};user_memo;{co}{var}",
        #         a.URL                                                                             AS "{column1};URL;{co}{var}",
        #         ARRAY[
        #             COALESCE(a.z_parent_paraitem, ''),
        #             COALESCE(a.z_child_paraitem, '')
        #         ]::TEXT[]                                                                         AS "param{alias}"
   
        #     from
        #         se_project_record_plz as a
        #     inner join
        #         (select distinct on (z_paravalueid) * from detail_data order by z_paravalueid, update_day desc) as b
        #         on 
        #             a.z_paravalueid = b.z_paravalueid
        #     inner join
        #         user_table as c
        #         on
        #             b.employee_number = c.employee_number
        #     inner join
        #         approval_status_table as d
        #         on
        #             b.approval_status = d.state_key
        #     where a.z_wp_name_get_str = '{var}'
        #         and a.z_prj_number = '{column1}'
        #         and a.z_name = '{column2}'
        #         and a.z_class_name_get_str = '{column3}'
        #     order by a.z_paravalueid
        #     ) as {alias} 
        # """
        # join_template = """
        # on s0p."{column1};z_parent_paraitem;{co1}{var1}" = {alias}."{column2};z_parent_paraitem;{co2}{var2}" and
        # s0p."{column1};z_child_paraitem;{co1}{var1}" = {alias}."{column2};z_child_paraitem;{co2}{var2}" and
        # s0p."{column1};z_unit;{co1}{var1}" = {alias}."{column2};z_unit;{co2}{var2}"
        # """
        # join_template = """
        # on s0p."{column1};z_parent_paraitem;{co1}{var1}" = {alias}."{column2};z_parent_paraitem;{co2}{var2}" and
        # s0p."{column1};z_child_paraitem;{co1}{var1}" = {alias}."{column2};z_child_paraitem;{co2}{var2}" and
        # s0p."{column1};z_unit;{co1}{var1}" = {alias}."{column2};z_unit;{co2}{var2}"
        # """

        # # サブクエリの生成
        # subqueries = []				

        # for i, row in prj_info_list.iterrows():
        #     if i == 0:
        #         subqueries = r"select * from"
        #     if i > 0:
        #         subqueries += "FULL OUTER JOIN"

        #     subqueries+=subquery_template.format(
        #         column1=row['z_prj_number'],
        #         column2=row['z_name'],
        #         column3=row['z_class_name_get_str'],
        #         co=row['z_class_name_get_str'][0] + row['z_class_name_get_str'][-1], #山口　列名に追加する文字列、フェーズ名をそのまま貼り付けると長さ制限にかかり機能しなくなるため、暫定的に最初と最後の文字のみをくっつける　11/6
        #         var=row['z_wp_name_get_str'],
        #         alias='s'+str(i)+'p')

        #     if i > 0:
        #         subqueries+=join_template.format(
        #             column1=prj_info_list['z_prj_number'][0],
        #             column2=prj_info_list['z_prj_number'][i],
        #             co1=prj_info_list['z_class_name_get_str'][0][0] + prj_info_list['z_class_name_get_str'][0][-1], #山口　列名に追加する文字列、フェーズ名をそのまま貼り付けると長さ制限にかかり機能しなくなるため、暫定的に最初と最後の文字のみをくっつける　11/6
        #             co2=prj_info_list['z_class_name_get_str'][i][0] + prj_info_list['z_class_name_get_str'][i][-1], #山口　列名に追加する文字列、フェーズ名をそのまま貼り付けると長さ制限にかかり機能しなくなるため、暫定的に最初と最後の文字のみをくっつける　11/6
        #             var1=prj_info_list['z_wp_name_get_str'][0],
        #             var2=prj_info_list['z_wp_name_get_str'][i],
        #             alias='s'+str(i)+'p'
        #             )
        # # print(subqueries)#山口デバック用
        # se_data_stuck = pd.read_sql_query(subqueries, connection)
        # # print(se_data_stuck)
        # #山口　取得したDFから編集情報を列にまとめる 10/25 _->;に変更
        # for i, row in prj_info_list.iterrows():
        #     column1=row['z_prj_number']
        #     var=row['z_wp_name_get_str']
        #     co=row['z_class_name_get_str'][0] + row['z_class_name_get_str'][-1] #山口　列名に追加する文字列、フェーズ名をそのまま貼り付けると長さ制限にかかり機能しなくなるため、暫定的に最初と最後の文字のみをくっつける　11/6
        #     # print(co)
        #     se_data_stuck[column1 + ';edited_info;' +co+ var] = "更新日：" + se_data_stuck[column1 + ';update_day;' +co+ var] + "\n更新者：" + se_data_stuck[column1 + ';edited_user;' +co+ var] + "\nメモ：" + se_data_stuck[column1 + ';user_memo;'+co + var]
        #     se_data_stuck[column1 + ';selected;' +co+ var] = None #山口　選択された項目を表すためのBooleanれつ追加　10/25

        subquery_template = """
            (select
                a.z_paravalueid                                                                   AS "{column1};z_paravalueid;{co}{var}",
                a.project_id                                                                      AS "{column1};project_id;{co}{var}",
                a.se_parameter_id                                                                 AS "{column1};se_parameter_id;{co}{var}",
                a.phase_id                                                                        AS "{column1};phase_id;{co}{var}",
                a.variation_id                                                                    AS "{column1};variation_id;{co}{var}",
                a.z_prj_number                                                                    AS "{column1};z_prj_number;{co}{var}",
                a.z_parent_paraitem                                                               AS "{column1};z_parent_paraitem;{co}{var}",
                a.z_child_paraitem                                                                AS "{column1};z_child_paraitem;{co}{var}",
                a.z_unit                                                                          AS "{column1};z_unit;{co}{var}",
                replace(a.z_unit, 'm#00B2', '²')                                                  AS "{column1};z_unit_copy;{co}{var}",
                a.z_wp_name_get_str                                                               AS "{column1};z_wp_name_get_str;{co}{var}",
                a.z_request_median                                                                AS "{column1};z_request_median;{co}{var}",
                CONCAT(c.section_code, ' ', 
                    c.contac_person_first_name, ' ',
                    c.contac_person_last_name)                                                    AS "{column1};contac_user;{co}{var}",
                CONCAT(c.section_code, ' ', 
                    c.contac_person_first_name, ' ',
                    c.contac_person_last_name)                                                    AS "{column1};edited_user;{co}{var}",
                CASE 
                    WHEN b.update_day IS NOT NULL THEN LEFT(CAST(b.update_day AS VARCHAR), 10) 
                    ELSE NULL 
                END                                                                               AS "{column1};update_day;{co}{var}",
                a.z_note                                                                          AS "{column1};z_note;{co}{var}",
                d.state_name                                                                      AS "{column1};state_name;{co}{var}",
                b.employee_number                                                                 AS "{column1};employee_number;{co}{var}",
                b.user_memo                                                                       AS "{column1};user_memo;{co}{var}",
                a.URL                                                                             AS "{column1};URL;{co}{var}",
                ARRAY[
                    COALESCE(a.z_parent_paraitem, ''),
                    COALESCE(a.z_child_paraitem, '')
                ]::TEXT[]                                                                         AS "param{alias}"
   
            from
                se_project_record_plz as a
            inner join
                (select distinct on (z_paravalueid) * from detail_data order by z_paravalueid, update_day desc) as b
                on 
                    a.z_paravalueid = b.z_paravalueid
            inner join
                user_table as c
                on
                    b.employee_number = c.employee_number
            inner join
                approval_status_table as d
                on
                    b.approval_status = d.state_key
            where a.variation_id = '{var}' --バリエーション名からIDに変えた
                and a.z_prj_number = '{column1}'
                and a.z_name = '{column2}'
                and a.z_class_name_get_str = '{column3}'

            order by a.z_paravalueid
            ) as {alias} 
        """
        join_template = """
        on s0p."{column1};z_parent_paraitem;{co1}{var1}" = {alias}."{column2};z_parent_paraitem;{co2}{var2}" and
        s0p."{column1};z_child_paraitem;{co1}{var1}" = {alias}."{column2};z_child_paraitem;{co2}{var2}" and
        s0p."{column1};z_unit;{co1}{var1}" = {alias}."{column2};z_unit;{co2}{var2}"
        """
        join_template = """
        on s0p."{column1};z_parent_paraitem;{co1}{var1}" = {alias}."{column2};z_parent_paraitem;{co2}{var2}" and
        s0p."{column1};z_child_paraitem;{co1}{var1}" = {alias}."{column2};z_child_paraitem;{co2}{var2}" and
        s0p."{column1};z_unit;{co1}{var1}" = {alias}."{column2};z_unit;{co2}{var2}"
        """

        # サブクエリの生成
        subqueries = []				

        for i, row in prj_info_list.iterrows():
            if i == 0:
                subqueries = r"select * from"
            if i > 0:
                subqueries += "FULL OUTER JOIN"

            subqueries+=subquery_template.format(
                column1=row['z_prj_number'],
                column2=row['z_name'],
                column3=row['z_class_name_get_str'],
                co=row['phase_id'], #山口　列名に追加する文字列、フェーズ名をそのまま貼り付けると長さ制限にかかり機能しなくなるため、暫定的に最初と最後の文字のみをくっつける　11/6　ここPhaseID_Variation_idでよくない？？
                var=row['variation_id'],
                alias='s'+str(i)+'p')

            if i > 0:
                subqueries+=join_template.format(
                    column1=prj_info_list['z_prj_number'][0],
                    column2=prj_info_list['z_prj_number'][i],
                    co1=prj_info_list['phase_id'][0], #山口　列名に追加する文字列、フェーズ名をそのまま貼り付けると長さ制限にかかり機能しなくなるため、暫定的に最初と最後の文字のみをくっつける　11/6
                    co2=prj_info_list['phase_id'][i], #山口　列名に追加する文字列、フェーズ名をそのまま貼り付けると長さ制限にかかり機能しなくなるため、暫定的に最初と最後の文字のみをくっつける　11/6
                    var1=prj_info_list['variation_id'][0],
                    var2=prj_info_list['variation_id'][i],
                    alias='s'+str(i)+'p'
                    )
        # print('subb:: ',subqueries)#山口デバック用
        print(subqueries)
        se_data_stuck = pd.read_sql_query(subqueries, connection)
        
        print(prj_info_list)
        #山口　取得したDFから編集情報を列にまとめる 10/25 _->;に変更
        for i, row in prj_info_list.iterrows():
            column1=row['z_prj_number']
            var=row['variation_id']
            co=row['phase_id'] #山口　列名に追加する文字列、フェーズ名をそのまま貼り付けると長さ制限にかかり機能しなくなるため、暫定的に最初と最後の文字のみをくっつける　11/6
            print(column1)
            se_data_stuck[column1 + ';edited_info;' +str(co)+ str(var)] = "更新日：" + se_data_stuck[column1 + ';update_day;' +str(co)+ str(var)] + "\n更新者：" + se_data_stuck[column1 + ';edited_user;' +str(co)+ str(var)] + "\nメモ：" + se_data_stuck[column1 + ';user_memo;'+str(co) + str(var)]
            se_data_stuck[column1 + ';selected;' +str(co)+ str(var)] = False #山口　選択された項目を表すためのBooleanれつ追加　10/25
        
        return prj_info_list, se_data_stuck
    
    #11/25 #チョー
    def get_varation(self, select_list = [], select_list2 = [], select_list3 = [],select_list4 = [],select_list5 = []):
        connection = self.conn
        select_list_str = ', '.join(f"'{item}'" for item in select_list)
        select_list_str2 = ', '.join(f"'{item}'" for item in select_list2)
        select_list_str3 = ', '.join(f"'{item}'" for item in select_list3)
        select_list_str4 = ', '.join(f"'{item}'" for item in select_list4)
        select_list_str5 = ', '.join(f"'{item}'" for item in select_list5)

        query = f"""
                SELECT DISTINCT ON (
                    subquery.z_wp_name_get_str, subquery.wp_order, subquery.modified_string
                )
                    subquery.z_wp_name_get_str,
                    subquery.wp_order,
                    subquery.modified_string
                FROM (
                    SELECT 
                        se.z_wp_name_get_str,
                        CASE 
                            WHEN se.z_wp_name_get_str ~ '\d' THEN CAST(regexp_replace(se.z_wp_name_get_str, '\D', '', 'g') AS INTEGER)
                        END AS wp_order,
                        replace(se.z_wp_name_get_str, 'Variation#', '') AS modified_string
                    FROM se_project_record_plz as se
                    INNER JOIN project_info AS pjf on se.project_id = pjf.id
                    INNER JOIN phase as ph on ph.id = se.phase_id
                    WHERE pjf.project_code IN ({select_list_str})
                    AND se.z_destination IN ({select_list_str2})
                    AND se.z_drive_system IN ({select_list_str3})
                    AND se.z_name IN ({select_list_str4})
                    AND ph.phase IN ({select_list_str5})
                    AND se.z_class_name_get_str IS NOT NULL
                    AND se.z_class_name_get_str <> ''
                ) subquery
                ORDER BY subquery.z_wp_name_get_str, subquery.wp_order, subquery.modified_string;"""
        varation_list = pd.read_sql_query(query, connection)
        
        return varation_list
    
    
    def posgre_copy_data(self, select_list = [], select_list2 = [], select_list3 = [], select_list4 = [],select_list5 = []):
        connection = self.conn
        select_list_str = ', '.join(f"'{item}'" for item in select_list)
        select_list_str2 = ', '.join(f"'{item}'" for item in select_list2)
        select_list_str3 = ', '.join(f"'{item}'" for item in select_list3)
        select_list_str4 = ', '.join(f"'{item}'" for item in select_list4)
        select_list_str5 = ', '.join(f"'{item}'" for item in select_list5)

        query = f"""
                SELECT DISTINCT on (se.z_prj_number,
					se.z_name,
					se.z_class_name_get_str,
					se.z_wp_name_get_str,
                   	se.z_destination,
					se.z_drive_system,
					wp_order, modified_string)
					se.z_prj_number,
					se.z_name,
					se.z_class_name_get_str,
					se.project_id,                                                                      
                    se.se_parameter_id,    
                    se.phase_id,         
                    se.variation_id,
					se.z_wp_name_get_str,
                   	se.z_destination,
					se.z_drive_system,
                    pjf.project_code,
					CASE 
	                    WHEN detail.update_day IS NOT NULL THEN LEFT(CAST(detail.update_day AS VARCHAR), 10) 
	                    ELSE NULL 
	                END as update_day,
	                CONCAT(user_table.section_code, ' ', user_table.contac_person_first_name, ' ',user_table.contac_person_last_name) as edited_user,
	                approve.state_name,
	                detail.user_memo,
                    CASE 
						WHEN se.z_wp_name_get_str ~ '\d' THEN CAST(regexp_replace(se.z_wp_name_get_str, '\D', '', 'g') AS INTEGER)
					END AS wp_order,
                    replace(se.z_wp_name_get_str,'Variation#', '') AS modified_string
                FROM se_project_record_plz as se
                INNER JOIN project_info AS pjf on se.project_id = pjf.id
                INNER JOIN phase as ph on ph.id = se.phase_id
				inner join
					(select distinct on (z_paravalueid) * from detail_data order by z_paravalueid, update_day desc) as detail
                on 
                    se.z_paravalueid = detail.z_paravalueid
                left outer join
	                user_table 
	            on
	                detail.employee_number = user_table.employee_number
	            inner join
	                approval_status_table as approve
	            on
	                detail.approval_status = approve.state_key
                WHERE pjf.project_code IN ({select_list_str})
                AND se.z_destination IN ({select_list_str2})
                AND se.z_drive_system IN ({select_list_str3})
                AND se.z_name IN ({select_list_str4})
                AND ph.phase IN ({select_list_str5})
                AND se.z_class_name_get_str IS NOT NULL
                AND se.z_class_name_get_str <> ''
                ORDER BY se.z_prj_number, se.z_class_name_get_str, wp_order;"""

        prj_info_list = pd.read_sql_query(query, connection)

        
        # Initialize an empty list to hold subqueries
        subqueries = []
        for index,row in prj_info_list.iterrows():
            subquery = f"""
                SELECT
                    a.project_id,
                    a.se_parameter_id,
                    a.phase_id,
                    a.variation_id,
                    a.z_paravalueid AS "arasid",
                    a.z_request_median AS "value",
                    b.employee_number,
                    a.z_note,
                    a.z_prj_number
                FROM
                    se_project_record_plz AS a
                INNER JOIN
                    (SELECT DISTINCT ON (z_paravalueid) * FROM detail_data ORDER BY z_paravalueid, update_day DESC) AS b
                    ON a.z_paravalueid = b.z_paravalueid
                INNER JOIN
                    user_table AS c
                    ON b.employee_number = c.employee_number
                INNER JOIN
                    approval_status_table AS d
                    ON b.approval_status = d.state_key
                WHERE
                    a.z_wp_name_get_str = '{row['z_wp_name_get_str']}'
                    AND a.z_prj_number = '{row['z_prj_number']}'
                    AND a.z_name = '{row['z_name']}'
                    AND a.z_class_name_get_str = '{row['z_class_name_get_str']}'
            """
            subqueries.append(subquery)
        stuck_query = " UNION ALL ".join(subqueries)
        se_data_stuck = pd.read_sql_query(stuck_query, connection)

        # st.write('pj info list: ', prj_info_list)
        return se_data_stuck

    def swap_df(self, df):
        prev_cols = None
        pre_df = pd.DataFrame()
        new_df = pd.DataFrame()
        # 列名から数字を取得して列が変わるまで横に結合し、数字が変わったタイミングで縦結合 山口　ここ数値が変わったタイミングである必要はない、単に；で分割した最後を見るのみ　11/1
        for col_name, data in df.items():
            #match = re.findall(r'\d+', col_name)
            match = col_name.split(';')[0] + col_name.split(';')[-1]#；で分割し、最後を見て判断 11/1　最後だけじゃ足りない、最初も見る　`11/1
            if match and prev_cols is not None and match != prev_cols or col_name == 'INDEX':
                new_df = pd.concat([new_df, pd.DataFrame(pre_df)])
                pre_df = pd.DataFrame()
            col_nm_str = col_name.split(";")
            col_nm = col_nm_str[1] if len(col_nm_str) > 1 else col_nm_str[0]
            pre_df[col_nm] = data.tolist()
            if match:
                prev_cols = match
        new_df = pd.concat([new_df, pd.DataFrame(pre_df)])#山口　最後にもう一回追加しないといけないため　10/25
        return new_df

    def db_update(self, df_mold_org, df_mold, date, username):
        df1 = self.swap_df(df_mold_org)
        df2 = self.swap_df(df_mold)
        df1['combined_key'] = df1['z_paravalueid'].astype(str) + '_' + df1['z_request_median'].astype(str) + '_' + df1['z_note'].astype(str)
        df2['combined_key'] = df2['z_paravalueid'].astype(str) + '_' + df2['z_request_median'].astype(str) + '_' + df2['z_note'].astype(str)
        # df2にのみ存在するレコードを検出する
        mask = ~df2['combined_key'].isin(df1['combined_key'])
        unique_in_df2 = df2[mask].copy()        
        unique_in_df2.drop('combined_key', axis=1, inplace=True) 
        unique_in_df2['employee_number'] = username
        unique_in_df2['update_day'] = date
        unique_in_df2 = unique_in_df2.loc[:, ~unique_in_df2.columns.str.startswith('params')]
        return unique_in_df2
    
    # def db_update_selected(self,  df_mold, date, username):#山口　selector列による変更

    #     df2 = df_mold
    #     df2_selected=df2.loc[:, df2.columns.str.contains('selected')]#selected列のみ抽出
    #     df2 =df2.loc[:, ~df2.columns.str.contains('selected')]#データ側からは不必要な列を取り除く
    #     df2 = df2.loc[:, ~df2.columns.str.contains('edited_info')]
    #     df2 = df2.loc[:, ~df2.columns.str.contains('params')]
    #     df2_selected = df2_selected.T.values.flatten()
    #     df2 = self.swap_df(df2)
    #     mask = df2_selected

    #     unique_in_df2 = df2[mask].copy()
    #     # print(unique_in_df2)
    #     unique_in_df2['employee_number'] = username
    #     unique_in_df2['update_day'] = date
    #     unique_in_df2 = unique_in_df2.loc[:, ~unique_in_df2.columns.str.startswith('params')]
    #     return unique_in_df2

    #チョー　01/16
    def db_update_selected(self, df_mold, date, username):

        # Extract columns with 'selected' in the name and remove unnecessary ones in a single operation
        selected_cols = [col for col in df_mold.columns if 'selected' in col and 'timeseries' not in col]#山口 Rリストではtimeseriesを含む列を省きたいため条件追加2/3
        non_selected_cols = [col for col in df_mold.columns if 'selected' not in col and 'edited_info' not in col and 'params' not in col and ';' in col] #山口 Rリストでは;を含まない列を省きたいため条件追加2/3
        print(selected_cols)
        
        df2_selected = df_mold[selected_cols]  # Only 'selected' columns
        df2 = df_mold[non_selected_cols]  # Columns without 'selected', 'edited_info', and 'params'

        # Convert the selected columns to a 1D array (flatten)
        mask = df2_selected.T.values.flatten()  # This should correspond to a selection mask
        # Perform transformation (ensure `swap_df` is optimized)
        df2 = self.swap_df(df2)
        # Apply the mask and create a new DataFrame of selected rows
        unique_in_df2 = df2[mask].copy()
        # Add necessary metadata columns
        unique_in_df2['employee_number'] = username
        unique_in_df2['update_day'] = date
        # Drop any columns starting with 'params' if they exist
        unique_in_df2 = unique_in_df2.loc[:, ~unique_in_df2.columns.str.startswith('params')]

        return unique_in_df2

    #山口　選択された条件をテーブるに挿入する 10/28
    def insert_bookmark(self, selected_archi, selection1, selection2, selection3, selection4, selection5, username, bookmark_number): #チョー　selected_archi追加　03/10
        query_text = ""
        table_dict ={
                2:'destination',
                3:'drivetrain',
                4:'lot',
                5:'phase'
                }
        dict = {
                0:selected_archi, #チョー　追加　03/10
                1:selection1,
                2:selection2,
                3:selection3,
                4:selection4,
                5:selection5
                }#use dictionary to insert all information in one for loop for the sake of make it cooler
        
        for key, value in dict.items():
            # print(key)
            for i, v in enumerate(value):#values are list and could have multiple items 
                if key in table_dict:#that mean value has to be convert to id
                    query = f"""
                        select id from {table_dict[key]} where {table_dict[key]}='{v}';
                    """
                    result = self.column_to_list(query)
                    # print(query)
                    # print(result)
                else:
                    result = ["'" +v + "'"]
                query_text = query_text + "insert into bookmark values('{}', {}, {}, {});".format(username, bookmark_number, key, result[0])
            
        try:
            cur = self.conn.cursor()
            
            cur.execute(query_text) #
            
        except InterfaceError as e:
            raise e
            # 接続が閉じられている場合、再接続を試みる
            self.conn = self.create_connection()
            if self.conn:
                return self.column_to_list(query)
            else:
                return None
        except psycopg2.Error as e:
            
            # エラー発生時にロールバック
            self.conn.rollback()
            raise e #raise分の位置を帰る　山口　10/25
            return None
        
        self.conn.commit()
        if cur:
            cur.close()      
                
                
    def get_bookmarks(self, username):#function to get bookmarks by user 10/29 山口
        connection = self.conn
        #チョー　取得条件を追加　03/10
        subqueries = f"""select bookmark.employee_number, bookmark_number, category, coalesce(destination.destination, drivetrain.drivetrain, lot.lot, phase.phase, case when bookmark.category=0 or bookmark.category=1 then bookmark.value end) as value 
                    from bookmark
                    left join destination on bookmark.category=2 and case when bookmark.value ~ '^\d+$' then cast(bookmark.value as integer) end =destination.id
                    left join drivetrain on bookmark.category=3 and case when bookmark.value ~ '^\d+$' then cast(bookmark.value as integer) end =drivetrain.id
                    left join lot on bookmark.category=4 and case when bookmark.value ~ '^\d+$' then cast(bookmark.value as integer) end =lot.id
                    left join phase on bookmark.category=5 and case when bookmark.value ~ '^\d+$' then cast(bookmark.value as integer) end =phase.id
                    where employee_number='{username}';
                    """
        df_bookmarks = pd.read_sql_query(subqueries, connection)
        # print(df_bookmarks.columns)
        df_default = pd.DataFrame([[0,0,0,'選択されていません']], columns=df_bookmarks.columns)#山口　初期値の定義 11/5
        # print(df_default)
        df_bookmarks =pd.concat([df_default, df_bookmarks])
        return df_bookmarks
        
    def delete_bookmark(self, bookmark_number, employee_number):#山口　ブックマーク削除 11/5
        try:
            cur = self.conn.cursor()
            
            query_text = "delete from bookmark where employee_number='{}' and bookmark_number={}".format(employee_number,bookmark_number)
            
            cur.execute(query_text) #
            
        except InterfaceError as e:
            raise e
            # 接続が閉じられている場合、再接続を試みる
            self.conn = self.create_connection()
            if self.conn:
                return self.column_to_list(query)
            else:
                return None
        except psycopg2.Error as e:
            
            # エラー発生時にロールバック
            self.conn.rollback()
            raise e #raise分の位置を帰る　山口　10/25
            return None
        
        self.conn.commit()
        if cur:
            cur.close()      
            
    def get_map_variables(self, project_id, se_parameter_id, phase_id, variation_id):#山口　マップ情報を問い合わせる 11/13
        df_map_variables = pd.DataFrame([])
        connection = self.conn
        subqueries = f"""
                    select project_id, se_parameter_id, phase_id, variation_id, map_variable_id, variable_name, unit, axis, parameter_map_relation.value as value
                    from parameter_map_relation inner join map_variable on parameter_map_relation.map_variable_id=map_variable.id
                    where project_id={project_id} and se_parameter_id={se_parameter_id} and phase_id={phase_id} and variation_id={variation_id};
        """
        
        df_map_variables = pd.read_sql_query(subqueries, connection)
        return df_map_variables
    
    def get_senario_map_variables(self, project_id, senario_parameter_id, phase_id, variation_id, study_id):#山口　simマップ情報を問い合わせる 12/8
        df_map_variables = pd.DataFrame([])
        connection = self.conn
        subqueries = f"""
                    select project_id, senario_parameter_id, phase_id, variation_id, study_id, map_variable_id, variable_name, unit, axis, test_senario_parameter_map_relation.value as value
                    from test_senario_parameter_map_relation inner join map_variable on test_senario_parameter_map_relation.map_variable_id=map_variable.id
                    where project_id={project_id} and senario_parameter_id={senario_parameter_id} and phase_id={phase_id} and variation_id={variation_id} and study_id='{study_id}';
        """
        print(subqueries)
        df_map_variables = pd.read_sql_query(subqueries, connection)
        return df_map_variables
        
    def get_map_variables_by_name(self, map_name):#山口　マップ情報をマップ名から問い合わせる 12/13
        try:
            cur = self.conn.cursor()
            
            cur.execute("""
                    select map_name, map_variable_id, variable_name, unit, axis, map_structure.value as value
                    from map_structure inner join map_variable on map_structure.map_variable_id=map_variable.id
                    where map_name=%s;
        """ , (map_name, ))
            result = cur.fetchall()
            df_map_variables = pd.DataFrame(result, columns=['map_name', 'map_variable_id', 'variable_name', 'unit', 'axis', 'value'])
            print(df_map_variables)
            if len(result)>=1:
            
                return df_map_variables
            else:
                return None

        except psycopg2.Error as e:
            
            # エラー発生時にロールバック
            self.conn.rollback()
            raise e #raise分の位置を帰る　山口　10/25
            return None
        
        self.conn.commit()
        if cur:
            cur.close()  

    def get_usecase_timeseries(self, usecase_id):
        try:
            cur = self.conn.cursor()
            cur.execute("""
                    select usecase_id, usecase, usecase_parameter_id, parameter_name, unit, value
                    from usecase_overall
                    where usecase_id=%s and usecase_parameter_id in (5,6,7,8);
            """, (usecase_id, ))
            result = cur.fetchall()
            df_timeseries_variables = pd.DataFrame(result, columns=['usecase_id','usecase','usecase_parameter_id','parameter_name','unit','value'])
            self.conn.commit()
            if cur:
                cur.close()  
            if len(result)>=1:
                return df_timeseries_variables
            else:
                return None
            
        except psycopg2.Error as e:
            
            # エラー発生時にロールバック
            self.conn.rollback()
            raise e 
            return None
            
    def update_RFL_by_senario(self, selected_performance, selected_requirement, selected_usecase, project_id, phase_id, variation_id, df_send_info, username, now):
        try:
            cur = self.conn.cursor()
            #選択された性能とユースケース名を元に、編集する必要のあるRFLIDを特定する
            cur.execute("""
                select prj_rfl.project_info_id, rfl.id as rfl_id, phase_id, r_parameter.id, setup_r_relation.usecase_id,  performance, requirement,   function_id, function, l_parameter_id, logic from prj_rfl
                inner join rfl on prj_rfl.rfl_id=rfl.id
                inner join setup_r_relation on setup_r_relation.id = rfl.requirement_s_id
                inner join r_parameter on r_parameter.id = setup_r_relation.r_parameter_id
                inner join setup_l_relation on setup_l_relation.id = rfl.logic_s_id
                inner join l_parameter on l_parameter.id = setup_l_relation.l_parameter_id
                inner join usecase on usecase.id = setup_r_relation.usecase_id
                where project_info_id=%s
                and phase_id=%s
                and performance like %s
                and usecase=%s;
            """, (project_id, phase_id, selected_performance+"%", selected_usecase))
            result = cur.fetchall()
            
            df_RFL_to_edit = pd.DataFrame(result, columns=['project_id','rfl_id','phase_id','requirement_id','usecase_id','performance','requirement', 'function_id', 'function' , 'logic_id', 'logic'])
            
            st.write(df_RFL_to_edit)
            if len(df_RFL_to_edit)==0:
                st.error('指定されたプロジェクト、フェーズ、性能、ユースケースに該当するRFLが見つかりませんでした。')
                return
            for i, row in df_send_info.iterrows():
                rflcategory = row[3]
                targetid = row[4]#山口　ここのIDはRFLテーブルのIDではなくｒ、ｆ、ｌいずれかのテーブルのＩＤ

                value = row[2]
                if rflcategory =='R':
                    print(df_RFL_to_edit[df_RFL_to_edit['requirement_id']==targetid])
                    print(df_RFL_to_edit[df_RFL_to_edit['requirement_id']==targetid]['rfl_id'].values.tolist() )
                    rflids = df_RFL_to_edit[df_RFL_to_edit['requirement_id']==targetid]['rfl_id'].values.tolist() 

                    ids_str = ', '.join('%s' for _ in rflids)
                    print(rflids)
                    print(ids_str)
                    print((value, *rflids))
                    query = f"update prj_rfl set requirement = %s where project_info_id = %s and phase_id = %s and rfl_id in ({ids_str});"
                        
                    print(query)
                    cur.execute(query,(value, project_id, phase_id,  *rflids))
                    
                elif rflcategory=='F':
                    rflids = df_RFL_to_edit[df_RFL_to_edit['function_id']==targetid]['rfl_id'].values.tolist() 
                    ids_str = ', '.join('%s' for _ in rflids)
                    query = f"update prj_rfl set function = %s where project_info_id = %s and phase_id = %s and rfl_id in ({ids_str});"
                    print(query)
                    cur.execute(query,(value, project_id, phase_id, *rflids))
                elif rflcategory =='L':
                    rflids = df_RFL_to_edit[df_RFL_to_edit['logic_id']==targetid]['rfl_id'].values.tolist() 
                    ids_str = ', '.join('%s' for _ in rflids)
                    query = f"update prj_rfl set logic = %s where project_info_id = %s and phase_id = %s and rfl_id in ({ids_str});"
                    print(query)
                    cur.execute(query,(value, project_id, phase_id, *rflids))
                else:
                    st.error('unexpected error:rflcategory not match')
                    continue
                #st.write(query.format(value, project_id, phase_id, *rflids))
                #st.write(value)
                #st.write('for')
                #st.write(rflids)
                query = f"insert into detail_data_rfl values (%s, %s, %s, %s, %s, null, %s, %s)"
                
                for rflid in rflids:
                    cur.execute(query, (project_id, rflid, phase_id, username, now, rflcategory, value ))


            
            self.conn.commit()
            if cur:
                cur.close()  
            
        except psycopg2.Error as e:
            
            # エラー発生時にロールバック
            self.conn.rollback()
            raise e 
            return None
        
    #山口　TOサマリー経由RFL編集
    def update_RFL_by_to_summary(self, df_selecteds):
        now = datetime.datetime.now()
        username = st.session_state.username
        for index, row in df_selecteds.iterrows():
            project_id = row['project_id']
            phase_id = row['phase_id']
            rfl_id = row['rfl_id']
            value = row['value']
            #山口 value_urlの内容をここでくっつける
            if row['value_url'] is not None:
                value = value+ ' ' + row ['value_url']
            try:
                cur = self.conn.cursor()
                #変更対象のLに紐づくRFL_idを、l_r_relationを使って取得する
                query = f"""select distinct child_prj_rfl.rfl_id from prj_rfl --山口　泊まりはしないけど、rfl_idがphase違いで複数来ることがあるので対処 4/23
                            join rfl on rfl_id=rfl.id
                            join l_r_relation on l_s_id = rfl.logic_s_id
                            join setup_r_relation as child_setup_r_relation on child_setup_r_relation.id = r_s_id
                            join rfl as child_rfl on child_rfl.requirement_s_id = child_setup_r_relation.id
                            join prj_rfl as child_prj_rfl on child_prj_rfl.rfl_id = child_rfl.id
                            where prj_rfl.project_info_id = %s
                            and prj_rfl.phase_id = %s
                            and prj_rfl.rfl_id = %s 
                """
                df_child_rfl = pd.read_sql_query(query, self.conn, params=[project_id, phase_id, rfl_id])
                #編集対象はdf_seledtedsのrfl_id+それに紐づくdf_child_rfls 、rfl_idはLに、child_rfl_idはRに
                
                query = f"""update prj_rfl set logic = %s where project_info_id = %s and phase_id=%s and rfl_id = %s;
                """
                print(query)
                cur.execute(query,(value, project_id, phase_id,rfl_id))
                query = f"insert into detail_data_rfl values(%s, %s, %s, %s, %s, null, 'L', %s);"
                cur.execute(query, (project_id, rfl_id, phase_id, username, now, value))

                if len(df_child_rfl)>=1:
                    child_rfl_ids_list = df_child_rfl['rfl_id'].tolist() 
                    child_rfl_ids = ', '.join(str(x) for x in child_rfl_ids_list)
                    query = f"""update prj_rfl set requirement = %s where project_info_id =%s and phase_id = %s and rfl_id in ({child_rfl_ids});
                    """
                    print(query)
                    cur.execute(query,(value, project_id, phase_id))
                    query = f"insert into detail_data_rfl values(%s, %s, %s, %s, %s, null, 'R', %s);"
                    for rflid in child_rfl_ids_list:
                        cur.execute(query, (project_id, rflid, phase_id, username, now, value))
            
            
            except psycopg2.Error as e:
                
                # エラー発生時にロールバック
                self.conn.rollback()
                raise e 
                return None
        
        self.conn.commit()
        if cur:
            cur.close()  
    

    def update_map_variables(self, project_id, se_parameter_id, phase_id, variation_id, z_paravalueid, username, now, map_name, Xid=None, Xval=None, Yid=None, Yval=None, MAPid=None, MAPval=None, TABLEids=None, TABLEvals=None):#山口　11/13 マップ名の追加12/9
        try:
            cur = self.conn.cursor()
            
            if (Xid is not None) & (Yid is not None) & (MAPid is not None) & (Xval is not None) & (Yval is not None) & (MAPval is not None):#MAPデータが渡されたとき
                ids=[Xid, Yid,MAPid]
                vals=[Xval, Yval, MAPval]
                
            elif (Xid is not None) & (TABLEids is not None) & (Xval is not None) & (TABLEvals is not None):#TABLEデータが渡されたとき
                ids = [Xid]+TABLEids
                vals=[Xval]+TABLEvals
            print(ids)
            print(vals)
            for i in range(len(ids)):
                print(i)
                query_text = sql.SQL("update parameter_map_relation set value=%s where project_id=%s and se_parameter_id=%s and phase_id=%s and variation_id=%s and map_variable_id=%s;")
                cur.execute(query_text,(vals[i], project_id, se_parameter_id, phase_id, variation_id, ids[i])) 
                query_text = sql.SQL("insert into detail_data_map values(%s, %s, %s, %s, Null, %s);")
                cur.execute(query_text,(z_paravalueid, username, now, vals[i], map_name))
            
        except InterfaceError as e:
            raise e
            # 接続が閉じられている場合、再接続を試みる
            self.conn = self.create_connection()
            if self.conn:
                return self.column_to_list(query)
            else:
                return None
        except psycopg2.Error as e:
            
            # エラー発生時にロールバック
            self.conn.rollback()
            raise e #raise分の位置を帰る　山口　10/25
            return None
        
        self.conn.commit()
        if cur:
            cur.close()      

    def update_map_variables_by_name(self, map_name, username, now, Xid=None, Xval=None, Yid=None, Yval=None, MAPid=None, MAPval=None, TABLEids=None, TABLEvals=None, Zid=None, Zval=None, CUBEid=None, CUBEval=None):#山口　マップを名前で更新12/5 cubeに対応 1/7
        try:
            cur = self.conn.cursor()
            
            if (Xid is not None) & (Yid is not None) & (MAPid is not None) & (Xval is not None) & (Yval is not None) & (MAPval is not None):#MAPデータが渡されたとき
                ids=[Xid, Yid,MAPid]
                vals=[Xval, Yval, MAPval]
                
            elif (Xid is not None) & (TABLEids is not None) & (Xval is not None) & (TABLEvals is not None):#TABLEデータが渡されたとき
                ids = [Xid]+TABLEids
                vals=[Xval]+TABLEvals
            
            elif (Xid is not None) & (Yid is not None) &(Zid is not None) & (CUBEid is not None) & (Xval is not None) & (Yval is not None) & (Zval is not None) &(CUBEval is not None):
                ids=[Xid, Yid, Zid, CUBEid]
                vals=[Xval, Yval, Zval, CUBEval]
            print(ids)
            print(vals)
            for i in range(len(ids)):
                print(i)
                query_text = sql.SQL("update map_structure set value=%s where map_name=%s and map_variable_id=%s;")
                cur.execute(query_text,(vals[i], map_name, ids[i])) 
                print('map value updated')
                query_text = sql.SQL("insert into detail_data_map_name values(%s, %s, %s, %s, %s);")
                cur.execute(query_text,(map_name, ids[i], username, now, vals[i]))
                print('logged')
            
        except psycopg2.Error as e:
            
            # エラー発生時にロールバック
            self.conn.rollback()
            raise e #raise分の位置を帰る　山口　10/25
            return None
        
        self.conn.commit()
        if cur:
            cur.close()      
    def update_senario_map_variables(self, project_id, senario_parameter_id, phase_id, variation_id, study_id, z_paravalueid, username, now, map_name, Xid=None, Xval=None, Yid=None, Yval=None, MAPid=None, MAPval=None, TABLEids=None, TABLEvals=None):#山口　11/13 マップ名をログとるように追加 12/09 Deprecated 1/8
        try:
            cur = self.conn.cursor()
            
            if (Xid is not None) & (Yid is not None) & (MAPid is not None) & (Xval is not None) & (Yval is not None) & (MAPval is not None):#MAPデータが渡されたとき
                ids=[Xid, Yid,MAPid]
                vals=[Xval, Yval, MAPval]
                
            elif (Xid is not None) & (TABLEids is not None) & (Xval is not None) & (TABLEvals is not None):#TABLEデータが渡されたとき
                ids = [Xid]+TABLEids
                vals=[Xval]+TABLEvals
            print(ids)
            print(vals)
            for i in range(len(ids)):
                print(i)
                query_text = sql.SQL("update test_senario_parameter_map_relation set value=%s where project_id=%s and senario_parameter_id=%s and phase_id=%s and variation_id=%s and study_id=%s and map_variable_id=%s;")
                cur.execute(query_text,(vals[i], project_id, senario_parameter_id, phase_id, variation_id, study_id, ids[i])) 
                query_text = sql.SQL("insert into detail_data_map values(%s, %s, %s, %s, Null, %s);")
                cur.execute(query_text,(z_paravalueid, username, now, vals[i], map_name))
            
        except InterfaceError as e:
            raise e
            # 接続が閉じられている場合、再接続を試みる
            self.conn = self.create_connection()
            if self.conn:
                return self.column_to_list(query)
            else:
                return None
        except psycopg2.Error as e:
            
            # エラー発生時にロールバック
            self.conn.rollback()
            raise e #raise分の位置を帰る　山口　10/25
            return None
        
        self.conn.commit()
        if cur:
            cur.close()      

    def get_all_phase(self, current_phase = [], filter = ""):
        # リストの要素をシングルクォートで囲んでカンマで結合
        phase_list_str = ', '.join(f"'{item}'" for item in current_phase)
        
        if filter == "NOT":
            # クエリを作成
            query = f"""select distinct(phase) from phase
                    where phase not in ({phase_list_str});"""
        elif filter == "ALL":
            query = f"""select distinct(phase) from phase;"""
            
        result = self.column_to_list(query)
        # print('phase result2: ', result)
        return result
    
    def get_phase_id(self, phase = ""):
        # print('phase ent: ', phase)
        new_phase = False
        query = f"""select distinct(id) from phase
                    where phase = '{phase}' ;"""
        # print('phase query: ', query)
        result = self.column_to_list(query)
        # print('p id: ', result)
        if len(result) <= 0:
            new_phase = True
            query = f"""select MAX(id)+1 from phase;"""
            result = self.column_to_list(query)
        # print('phase id: ', id)
        return result, new_phase
    
    def insert_phase(self, id, phase):
        
        connection = self.conn
        # print('connection: ', connection)
        query = f"""
            INSERT INTO phase (id,phase) VALUES({id},'{phase}')
            """
        with connection as conn:
            # print('conn: ', conn)
            with conn.cursor() as cur:
                try:
                    cur.execute(query)
                    return True
                except Exception as e:
                    # print(f'An error occurred while executing the query: {e}')
                    return False
            
    def insert_project_parameters(self, data_stuck):
        connection = self.conn
        # print('connection: ', connection)
        
        with connection as conn:
            # print('conn: ', conn)
            with conn.cursor() as cur:
                try:
                    for index, row in data_stuck.iterrows():
                        query = """
                            INSERT INTO project_parameter(
                                project_id, se_parameter_id, phase_id, variation_id, arasid, value, employee_number, z_note, z_prj_number
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        cur.execute(query, (
                            row['project_id'], row['se_parameter_id'], row['phase_id'], row['variation_id'], 
                            row['arasid'], row['value'], row['employee_number'], row['z_note'], row['z_prj_number']
                        ))
                    return True
                except Exception as e:
                    print(f'An error occurred while executing the query: {e}')
                    return False
                
    def set_login_log(self, username):#山口　ログインした日時を記録する　12/3
        now = datetime.datetime.now()
        try:
            cur = self.conn.cursor()
            query_text = sql.SQL("insert into login_log values(%s, %s);")
            cur.execute(query_text,(username, now))
            
        except InterfaceError as e:
            raise e
            # 接続が閉じられている場合、再接続を試みる
            self.conn = self.create_connection()
            if self.conn:
                return self.column_to_list(query)
            else:
                return None
        except psycopg2.Error as e:
            
            # エラー発生時にロールバック
            self.conn.rollback()
            raise e #raise分の位置を帰る　山口　10/25
            return None
        
        self.conn.commit()
        if cur:
            cur.close()

    def set_condition_log(self, select_list1, select_list2, select_list3, select_list4, username):#山口　条件で選んだログを残す 12/3
        now = datetime.datetime.now()
        try:
            cur = self.conn.cursor()
            query_text = sql.SQL("insert into condition_log values(%s, %s, %s, %s, %s, %s);")
            cur.execute(query_text,(select_list1, select_list2, select_list3, select_list4, username, now))
            
        except InterfaceError as e:
            raise e
            # 接続が閉じられている場合、再接続を試みる
            self.conn = self.create_connection()
            if self.conn:
                return self.column_to_list(query)
            else:
                return None
        except psycopg2.Error as e:
            
            # エラー発生時にロールバック
            self.conn.rollback()
            raise e #raise分の位置を帰る　山口　10/25
            return None
        
        self.conn.commit()
        if cur:
            cur.close()           
    def get_user(self, username):   #山口 現在はUserName=PASSWORDを前提 11/30
            try:
                cur = self.conn.cursor()
                
                cur.execute("SELECT * FROM user_table WHERE employee_number = %s;" , (username, ))
                result = cur.fetchall()
                user = pd.DataFrame(result)
                if len(user)>=1:
                    return username
                else:
                    return None
                    
            except InterfaceError as e:
                raise e
                # 接続が閉じられている場合、再接続を試みる
                self.conn = self.create_connection()
                if self.conn:
                    return self.column_to_list(query)
                else:
                    return None
            except psycopg2.Error as e:
                
                # エラー発生時にロールバック
                self.conn.rollback()
                raise e #raise分の位置を帰る　山口　10/25
                return None
            
            self.conn.commit()
            if cur:
                cur.close()

    def get_metas(self):#山口　メタ情報を全部持ってくる 12/5
        try:
            cur = self.conn.cursor()
            
            cur.execute("select distinct on (project_code, z_destination, z_drive_system, z_name, z_class_name_get_str, z_wp_name_get_str) project_id, project_code, z_destination as destination, z_drive_system as drivetrain, z_name as lot, phase_id, z_class_name_get_str as phase, variation_id,  z_wp_name_get_str as variation from se_project_record_plzz;")
            result = cur.fetchall()
            df_metas = pd.DataFrame(result,columns=['project_id', 'project_code', 'destination', 'drivetrain', 'lot', 'phase_id', 'phase', 'variation_id','variation'])
            
            return df_metas
                
        except InterfaceError as e:
            raise e
            # 接続が閉じられている場合、再接続を試みる
            self.conn = self.create_connection()
            if self.conn:
                return self.column_to_list(query)
            else:
                return None
        except psycopg2.Error as e:
            
            # エラー発生時にロールバック
            self.conn.rollback()
            raise e #raise分の位置を帰る　山口　10/25
            return None
        
        self.conn.commit()
        if cur:
            cur.close()  
        
    # def add_new_study(self, project_id, phase_id, variation_id, study_id, R, designItem, usecase, usecase_submodel, TD, submodels, variables):#山口　新規スタディの追加 12/5 マップが紐づいているものを引き継げるように12/9　詳細追加UIに対応12/12 ユースケースサブモデル追加12/25 Rに基づいてOutput　○○の必要項目を定めるようにする3/19

    #     now = datetime.datetime.now()
    #     username=st.session_state.username
    #     print(project_id)
    #     try: 
    #         cur = self.conn.cursor()

                        
    #         ## R(performance)名と一致するR_parameterレコード一覧を取得→一覧に登場するR_parameter.idに紐づくRFLからf_parameter.id, l_parameter.idを取得→それらがtest_senario_list_parameter.rflidに登場するtest_senario_list_parameter.id一覧を取得する
    #         Rids_all = []
    #         Fids_all = []
    #         Lids_all = []
    #         cur.execute(f"""select r_parameter.id as r_id, f_parameter.id as f_id, l_parameter.id as l_id
    #                         from r_parameter
    #                         join setup_r_relation on setup_r_Relation.r_parameter_id=r_parameter.id
    #                         join rfl on rfl.requirement_s_id = setup_r_Relation.id
    #                         join f_parameter on rfl.function_id = f_parameter.id
    #                         join setup_l_relation on setup_l_relation.id = rfl.logic_s_id
    #                         join l_parameter on l_parameter.id = setup_l_relation.l_parameter_id
    #                         where r_parameter.id in (
    #                             select id 
    #                             from r_parameter 
    #                             where performance = %s
    #                         ); """, (R,))
                        
    #         result = cur.fetchall()
    #         df_rflids = pd.DataFrame(result,columns = ['Rid','Fid','Lid'])
    #         Rids = df_rflids['Rid'].tolist()
    #         Fids = df_rflids['Fid'].tolist()
    #         Lids = df_rflids['Lid'].tolist()
    #         Rids_all+=Rids
    #         Fids_all+=Fids
    #         Lids_all+=Lids
    #         #この時点で取れているIDは車両階層のみ、システム、ユニットまでをとれるようにする
    #         while len(Lids)>=1:
    #             print(Lids)
    #             print('there must be more')
    #             Lids_str_previous = ', '.join(f"{item}" for item in Lids)
    #             cur.execute(f"""select r_parameter.id as rid, f_parameter.id as fid, child_l.id as lid
    #                         from l_r_relation
	# 						join setup_r_relation on setup_r_Relation.id=l_r_relation.r_s_id
    #                         join r_parameter on r_parameter.id  = setup_r_relation.r_parameter_id
                            
    #                         join rfl on rfl.requirement_s_id = setup_r_Relation.id
    #                         join f_parameter on rfl.function_id = f_parameter.id
    #                         join setup_l_relation as parent_l_s on parent_l_s.id = l_r_relation.l_s_id
	# 						join l_parameter as parent_l on parent_l.id= parent_l_s.l_parameter_id
	# 						join setup_l_relation as child_l_s on child_l_s.id = rfl.logic_s_id
    #                         join l_parameter as child_l on child_l.id = child_l_s.l_parameter_id
    #                         where parent_l.id in ({Lids_str_previous})

    #                         """)
    #             result = cur.fetchall()
    #             df_rflids = pd.DataFrame(result,columns = ['Rid','Fid', 'Lid'])
    #             print(df_rflids)
    #             print('how about that')
    #             Rids = df_rflids['Rid'].tolist()
    #             Fids = df_rflids['Fid'].tolist()
    #             Lids = df_rflids['Lid'].tolist()
    #             Rids_all+=Rids
    #             Fids_all+=Fids
    #             Lids_all+=Lids               
                

    #         Rids_str = ', '.join(f"{item}" for item in Rids_all)
    #         Fids_str = ', '.join(f"{item}" for item in Fids_all)
    #         Lids_str = ', '.join(f"{item}" for item in Lids_all)
    #         print(Rids_str)
           
    #         cur.execute(f"""select id 
    #                         from test_senario_list_parameter
    #                         where (rflcategory = 'R' and rflid in ({Rids_str}))
    #                         or (rflcategory = 'F' and rflid in ({Fids_str}))
    #                         or (rflcategory = 'L' and rflid in ({Lids_str}));
    #                     """)
    #         result = cur.fetchall()
    #         df_senario_output_ids= pd.DataFrame(result, columns=['id'])
    #         print(df_senario_output_ids)
    #         senario_output_ids = df_senario_output_ids['id'].tolist()
    #         senario_output_ids_str = ', '.join(f"{item}" for item  in senario_output_ids)
    #         st.write(senario_output_ids_str) 
    #         cur.execute(f"""insert into test_project_senario_parameter(project_id, senario_parameter_id, phase_id, variation_id, study_id, updated_value)
    #                        select distinct on (senario_parameter_id)%s, senario_parameter_id, %s, %s, %s, Null from test_project_senario_parameter where senario_parameter_id <= 10000;
    #                         """,(project_id, phase_id, variation_id, study_id))#今までtest_project_senario_parameterに追加実績のあるものしか追加しない ここでの追加は入力パラメータ限定に 3/19　山口
    #         ##Output項目の追加 3/19 山口
    #         print('new study inserted')
    #         cur.execute(f"""insert into test_project_senario_parameter(project_id, senario_parameter_id, phase_id, variation_id, study_id, updated_value)
    #                         select %s, test_senario_list_parameter.id, %s, %s, %s, Null 
    #                         from test_senario_list_parameter
    #                         where test_senario_list_parameter.id in ({senario_output_ids_str})
    #                         order by id;

    #                     """, (project_id, phase_id, variation_id, study_id))
    #         print('study output inserted')
    #         cur.execute("""
    #                        update test_project_senario_parameter set id=concat('sim',surid) where project_id=%s and phase_id=%s and variation_id=%s and study_id=%s;
    #                        """, (project_id, phase_id, variation_id, study_id))
    #         print('id updated')
            
    #         cur.execute("""
    #                        update test_project_senario_parameter set updated_value = %s where project_id=%s and phase_id=%s and variation_id=%s and study_id=%s and senario_parameter_id=3;
    #                     """, (designItem, project_id, phase_id, variation_id, study_id)) #性能行へのRアップデート
    #         cur.execute("""
    #                        update test_project_senario_parameter set updated_value = %s where project_id=%s and phase_id=%s and variation_id=%s and study_id=%s and senario_parameter_id=15;
    #                     """, (R, project_id, phase_id, variation_id, study_id)) #山口　性能領域もほしかったので転記する2/6
            
            
    #         print('R updated')
    #         cur.execute("""
    #                        update test_project_senario_parameter set updated_value = %s where project_id=%s and phase_id=%s and variation_id=%s and study_id=%s and senario_parameter_id=13;
    #                     """, (TD, project_id, phase_id, variation_id, study_id)) #性能行へのTDアップデート
    #         cur.execute("""
    #                        update test_project_senario_parameter set updated_value = %s where project_id=%s and phase_id=%s and variation_id=%s and study_id=%s and senario_parameter_id=14;
    #                     """, (usecase, project_id, phase_id, variation_id, study_id)) #性能行へのusecaseアップデ
    #         cur.execute("""
    #                        update test_project_senario_parameter set updated_value = %s where project_id=%s and phase_id=%s and variation_id=%s and study_id=%s and senario_parameter_id=70;
    #                     """, (usecase_submodel, project_id, phase_id, variation_id, study_id)) #性能行へのusecaseモデルアップデ
    #         print('usecase updated')
            
    #         #ここでサブモデル名も入れるべきだと思うが現状行がないためスキップ
            
    #         for variabledics in variables:
            
    #             for i,dic in enumerate(variabledics):
    #                 senario_parameter_id = list(dic.keys())[0]
    #                 value = list(dic.values())[0]
    #                 cur.execute("""
    #                            update test_project_senario_parameter set updated_value = %s where project_id=%s and phase_id=%s and variation_id=%s and study_id=%s and senario_parameter_id=%s;
    #                         """, (value, project_id, phase_id, variation_id, study_id, senario_parameter_id)) #性能行へのusecaseアップデート
                        

            
    #         cur.execute("""
    #                        insert into detail_data_sim(id, employee_number, update_day, user_memo, value)
    #                        select id, %s, %s, 'new study', Null from test_project_senario_parameter where project_id=%s and phase_id=%s and variation_id=%s and study_id=%s;
    #                        """, (username, now, project_id, phase_id, variation_id, study_id))
    #         print('logged')
                
    #     except InterfaceError as e:
    #         raise e
    #         # 接続が閉じられている場合、再接続を試みる
    #         self.conn = self.create_connection()
    #         if self.conn:
    #             return self.column_to_list(query)
    #         else:
    #             return None
    #     except psycopg2.Error as e:
            
    #         # エラー発生時にロールバック
    #         self.conn.rollback()
    #         raise e #raise分の位置を帰る　山口　10/25
    #         return None
        
    #     self.conn.commit()
    #     if cur:
    #         cur.close()  


    #Kyaw 07/04 Update
    def add_new_study(self, project_id, phase_id, variation_id, study_id, R, designItem, usecase, usecase_submodel, TD, submodels, variables):#山口 新規スタディの追加 12/5 マップが紐づいているものを引き継げるように12/9 詳細追加UIに対応12/12 ユースケースサブモデル追加12/25 Rに基づいてOutput ○○の必要項目を定めるようにする3/19

        now = datetime.datetime.now()
        username=st.session_state.username
        print(project_id)
        try: 
            cur = self.conn.cursor()

                        
            ## R(performance)名と一致するR_parameterレコード一覧を取得→一覧に登場するR_parameter.idに紐づくRFLからf_parameter.id, l_parameter.idを取得→それらがtest_senario_list_parameter.rflidに登場するtest_senario_list_parameter.id一覧を取得する
            Rids_all = []
            Fids_all = []
            Lids_all = []
            cur.execute(f"""select r_parameter.id as r_id, f_parameter.id as f_id, l_parameter.id as l_id
                            from r_parameter
                            join setup_r_relation on setup_r_Relation.r_parameter_id=r_parameter.id
                            join rfl on rfl.requirement_s_id = setup_r_Relation.id
                            join f_parameter on rfl.function_id = f_parameter.id
                            join setup_l_relation on setup_l_relation.id = rfl.logic_s_id
                            join l_parameter on l_parameter.id = setup_l_relation.l_parameter_id
                            where r_parameter.id in (
                                select id 
                                from r_parameter 
                                where performance = %s
                            ); """, (R,))
                        
            result = cur.fetchall()
            df_rflids = pd.DataFrame(result,columns = ['Rid','Fid','Lid'])
            Rids = df_rflids['Rid'].tolist()
            Fids = df_rflids['Fid'].tolist()
            Lids = df_rflids['Lid'].tolist()
            Rids_all+=Rids
            Fids_all+=Fids
            Lids_all+=Lids
            #この時点で取れているIDは車両階層のみ、システム、ユニットまでをとれるようにする
            # while len(Lids)>=1:
            #     print(Lids)
            #     print('there must be more')
            #     #山口 現状l_r_relationが階層間で無限ループになってしまっている。延々とクエリを投げることを防ぐため、明示的に階層を指定するように 6/24
            #     hierarchy_id = 2
            #     Lids_str_previous = ', '.join(f"{item}" for item in Lids)
            #     cur.execute(f"""select r_parameter.id as rid, f_parameter.id as fid, child_l.id as lid
            #                 from l_r_relation
            #     join setup_r_relation on setup_r_Relation.id=l_r_relation.r_s_id
            #                 join r_parameter on r_parameter.id  = setup_r_relation.r_parameter_id
                            
            #                 join rfl on rfl.requirement_s_id = setup_r_Relation.id
            #                 join f_parameter on rfl.function_id = f_parameter.id
            #                 join setup_l_relation as parent_l_s on parent_l_s.id = l_r_relation.l_s_id
            #     join l_parameter as parent_l on parent_l.id= parent_l_s.l_parameter_id
            #     join setup_l_relation as child_l_s on child_l_s.id = rfl.logic_s_id
            #                 join l_parameter as child_l on child_l.id = child_l_s.l_parameter_id
            #                 where parent_l.id in ({Lids_str_previous}) and hierarchy_id = {hierarchy_id}

            #                 """)
            #     result = cur.fetchall()
            #     df_rflids = pd.DataFrame(result,columns = ['Rid','Fid', 'Lid'])
            #     print(df_rflids)
            #     print('how about that')
            #     Rids = df_rflids['Rid'].tolist()
            #     Fids = df_rflids['Fid'].tolist()
            #     Lids = df_rflids['Lid'].tolist()
            #     Rids_all+=Rids
            #     Fids_all+=Fids
            #     Lids_all+=Lids               
            #     hierarchy_id += 1

            Rids_str = ', '.join(f"{item}" for item in Rids_all)
            Fids_str = ', '.join(f"{item}" for item in Fids_all)
            Lids_str = ', '.join(f"{item}" for item in Lids_all)
            print(Rids_str)
            #山口 input項目をRFLと紐づけると、以下のクエリでIDを拾ってくることになり、重複Insertをしようとすることでエラーにつながっていた。明示的にparameter_name_1が'Output'とつくものに限定することで防ぐ 4/3 
            cur.execute(f"""select id 
                            from test_senario_list_parameter
                            where (
                            (rflcategory = 'R' and rflid in ({Rids_str}))
                            or (rflcategory = 'F' and rflid in ({Fids_str}))
                            or (rflcategory = 'L' and rflid in ({Lids_str}))
                            )
                            and parameter_name_1 like 'Output %';
                        """)
            result = cur.fetchall()
            df_senario_output_ids= pd.DataFrame(result, columns=['id'])
            print(df_senario_output_ids)
            senario_output_ids = df_senario_output_ids['id'].tolist()
            senario_output_ids_str = ', '.join(f"{item}" for item  in senario_output_ids)
            st.write(senario_output_ids_str) 
            cur.execute(f"""insert into test_project_senario_parameter(project_id, senario_parameter_id, phase_id, variation_id, study_id, updated_value)
                           select distinct on (senario_parameter_id)%s, senario_parameter_id, %s, %s, %s, Null from test_project_senario_parameter where senario_parameter_id <= 10000;
                            """,(project_id, phase_id, variation_id, study_id))#今までtest_project_senario_parameterに追加実績のあるものしか追加しない ここでの追加は入力パラメータ限定に 3/19 山口
            ##Output項目の追加 3/19 山口 
            print('new study inserted')
            cur.execute(f"""insert into test_project_senario_parameter(project_id, senario_parameter_id, phase_id, variation_id, study_id, updated_value)
                            select %s, test_senario_list_parameter.id, %s, %s, %s, Null 
                            from test_senario_list_parameter
                            where test_senario_list_parameter.id in ({senario_output_ids_str})
                            order by id;

                        """, (project_id, phase_id, variation_id, study_id))
            print('study output inserted')
            cur.execute("""
                           update test_project_senario_parameter set id=concat('sim',surid) where project_id=%s and phase_id=%s and variation_id=%s and study_id=%s;
                           """, (project_id, phase_id, variation_id, study_id))
            print('id updated')
            
            cur.execute("""
                           update test_project_senario_parameter set updated_value = %s where project_id=%s and phase_id=%s and variation_id=%s and study_id=%s and senario_parameter_id=3;
                        """, (designItem, project_id, phase_id, variation_id, study_id)) #性能行へのRアップデート
            cur.execute("""
                           update test_project_senario_parameter set updated_value = %s where project_id=%s and phase_id=%s and variation_id=%s and study_id=%s and senario_parameter_id=15;
                        """, (R, project_id, phase_id, variation_id, study_id)) #山口 性能領域もほしかったので転記する2/6
            
            
            print('R updated')
            cur.execute("""
                           update test_project_senario_parameter set updated_value = %s where project_id=%s and phase_id=%s and variation_id=%s and study_id=%s and senario_parameter_id=13;
                        """, (TD, project_id, phase_id, variation_id, study_id)) #性能行へのTDアップデート
            cur.execute("""
                           update test_project_senario_parameter set updated_value = %s where project_id=%s and phase_id=%s and variation_id=%s and study_id=%s and senario_parameter_id=14;
                        """, (usecase, project_id, phase_id, variation_id, study_id)) #性能行へのusecaseアップデ
            cur.execute("""
                           update test_project_senario_parameter set updated_value = %s where project_id=%s and phase_id=%s and variation_id=%s and study_id=%s and senario_parameter_id=70;
                        """, (usecase_submodel, project_id, phase_id, variation_id, study_id)) #性能行へのusecaseモデルアップデ
            print('usecase updated')
            
            #ここでサブモデル名も入れるべきだと思うが現状行がないためスキップ
            
            for variabledics in variables:
            
                for i,dic in enumerate(variabledics):
                    senario_parameter_id = list(dic.keys())[0]
                    value = list(dic.values())[0]
                    cur.execute("""
                               update test_project_senario_parameter set updated_value = %s where project_id=%s and phase_id=%s and variation_id=%s and study_id=%s and senario_parameter_id=%s;
                            """, (value, project_id, phase_id, variation_id, study_id, senario_parameter_id)) #性能行へのusecaseアップデート
                        

            
            cur.execute("""
                           insert into detail_data_sim(id, employee_number, update_day, user_memo, value)
                           select id, %s, %s, 'new study', Null from test_project_senario_parameter where project_id=%s and phase_id=%s and variation_id=%s and study_id=%s;
                           """, (username, now, project_id, phase_id, variation_id, study_id))
            print('logged')
                
        except InterfaceError as e:
            raise e
            # 接続が閉じられている場合、再接続を試みる
            self.conn = self.create_connection()
            if self.conn:
                return self.column_to_list(query)
            else:
                return None
        except psycopg2.Error as e:
            
            # エラー発生時にロールバック
            self.conn.rollback()
            raise e #raise分の位置を帰る 山口 10/25
            return None
        
        self.conn.commit()
        if cur:
            cur.close() 


    def get_td_list(self):#使用できるTechnicalDefinitionの一覧を取得する
    
        try:
            cur = self.conn.cursor()
            
            cur.execute("select distinct td from td_variables;")
            result = cur.fetchall()
            df_tds= pd.DataFrame(result, columns=['td'])
            return df_tds['td'].tolist()
                
        except psycopg2.Error as e:
            
            # エラー発生時にロールバック
            self.conn.rollback()
            raise e #raise分の位置を帰る　山口　10/25
            return None
        
        self.conn.commit()
        if cur:
            cur.close()  
    

    def get_submodel_list(self, td, scope):#使用できるサブモデルの一覧を取得する
    
        try:
            cur = self.conn.cursor()
            
            cur.execute("select distinct submodel from td_variables where td = %s and scope = %s;", (td, scope))
            result = cur.fetchall()
            df_submodels = pd.DataFrame(result,columns=['submodel'])
            return df_submodels['submodel'].tolist()
                
        except psycopg2.Error as e:
            
            # エラー発生時にロールバック
            self.conn.rollback()
            raise e #raise分の位置を帰る　山口　10/25
            return None
        
        self.conn.commit()
        if cur:
            cur.close()  
    
    def get_senario_parameter(self, scope, project_id, phase_id, variation_id, mode, base_study_id = None):#各スコープごとのパラメータとその初期値を取得する
    
        try:
            cur = self.conn.cursor()
            query ="select distinct  on (senario_parameter_id, parameter_name_2, parameter_unit) senario_parameter_id, parameter_name_2, parameter_unit,"
            if base_study_id is not None:
                query = query + " overall_value,"
            else:
                query = query + " original_value,"
            
            query = query + " scope from test_senario_project_record where"
           
            

            # if scope=='Carbody':
            #     query = query + "  scope = 'Carbody'"
            # elif scope=='EM_Fr':
            #     query = query + "  scope = 'Electrical_Motor_Fr'"
            # elif scope=='Gearbox_Fr':
            #     query = query + "  scope = 'Gearbox_Fr'"
            # elif scope=='EM_Rr':
            #     query = query + "  scope = 'Electrical_Motor_Rr'"
            # elif scope=='Gearbox_Rr':
            #     query = query + "  scope = 'Gearbox_Rr'"
            # elif scope=='Battery':
            #     query = query + "  scope = 'Battery_High_Voltage'"
            query = query + " project_id = %s and phase_id = %s and variation_id = %s and scope = %s" #  山口　プロジェクト指定条件の追加　1/24
            
            if base_study_id is not None:
                query = query + " and study_id = %s"
                
            if mode=='SCALAR':
                query = query + " and parameter_unit not like 'Map';"
            elif mode=='MAP':
                query = query + " and parameter_unit like 'Map';"
            
            if base_study_id is not None:
                cur.execute(query, (project_id, phase_id, variation_id, scope, base_study_id))
            else:
                cur.execute(query, (project_id, phase_id, variation_id, scope))
            print(scope)
            print(query)
            
            result = cur.fetchall()
            print(result)
            df_parameters = pd.DataFrame(result,columns=['senario_parameter_id','parameter_name_2','parameter_unit', 'original_value', 'scope'])
            
            #選択されたメタ情報で新しくスタディが作成されたとき、何も帰ってこないため、original_valueを空白としたdf_parameter をtest_senario_list_parameterから作る
            if len(df_parameters)>0:
                return df_parameters
            else:
                # query ="select distinct  on (id, parameter_name_2, parameter_name) id, parameter_name_2, parameter_name,"

                # query = query + " scope from test_senario_list_parameter where"
                # query = query + "  scope = %s"
                # if mode=='SCALAR':
                #     query = query + " and parameter_name not like 'Map';"
                # elif mode=='MAP':
                #     query = query + " and parameter_name like 'Map';"
                # cur.execute(query, (scope,))
                # result = cur.fetchall()
                # print(result)
                # df_parameters = pd.DataFrame(result,columns=['senario_parameter_id','parameter_name_2','parameter_unit', 'scope'])
                # df_parameters['original_value'] = None
                # return df_parameters

                #Kyaw 07/04 Update
                query = """
                SELECT DISTINCT ON (tslp.id, tslp.parameter_name_2, tslp.parameter_name)
                    tslp.id AS senario_parameter_id,
                    tslp.parameter_name_2,
                    tslp.parameter_name AS parameter_unit,
                    tslp.scope AS scope,
                    pp.value AS original_value
                FROM test_senario_list_parameter tslp
                LEFT JOIN project_parameter pp 
                    ON tslp.parent_id = pp.se_parameter_id
                    AND pp.project_id = %s
                    AND pp.phase_id = %s
                    AND pp.variation_id = %s
                WHERE tslp.scope = %s
                AND tslp.category = %s
                """

                # Add parameter_name condition with hardcoded 'Map'
                if mode == 'SCALAR':
                    query += " AND tslp.parameter_name NOT LIKE 'Map'"
                elif mode == 'MAP':
                    query += " AND tslp.parameter_name LIKE 'Map'"

                query += """
                ORDER BY tslp.id;
                """

                params = (project_id, phase_id, variation_id, scope, 'SE')
                cur.execute(query, params)
                result = cur.fetchall()

                print(result)
                # Get column names from cursor
                columns = [desc[0] for desc in cur.description]

                # Create DataFrame
                df_parameters = pd.DataFrame(result, columns=columns)
                return df_parameters
                
        except psycopg2.Error as e:
            
            # エラー発生時にロールバック
            self.conn.rollback()
            raise e #raise分の位置を帰る　山口　10/25
            return None
        
        self.conn.commit()
        if cur:
            cur.close()  
    
    def get_map_list(self):#山口 map scopeを返すように12/26
        
        try:
            cur = self.conn.cursor()
            
            cur.execute("select distinct map_name, scope from map_structure;")
            result = cur.fetchall()
            df_MAPs = pd.DataFrame(result,columns=['map_name', 'scope'])
            return df_MAPs#山口　帰ってくるものはListではなくDFに
                
        except psycopg2.Error as e:
            
            # エラー発生時にロールバック
            self.conn.rollback()
            raise e #raise分の位置を帰る　山口　10/25
            return None
        


    def get_R_project_record(self, project_id, phase_id):  #山口 R_project_recordをプロジェクトに沿って表示

        try:
            cur = self.conn.cursor()
            # cur.execute("select * from R_project_record where project_id=%s and phase_id=%s;",(project_id, phase_id))
            
            # result = cur.fetchall()
            # df_R = pd.DataFrame(result,columns=['project_id', 'setup_id', 'destination_id', 'destination', 'drivetrain_id', 'drivetrain', 'architecture_id', 'architecturename', 'lot_id', 'lot', 'phase_id', 'phase', 'variation_id', 'variation', 'r_parameter_id', 'hierarchy_id', 'wp_id', 'performance', 'design_item_1', 'design_item_2', 'design_item_3', 'r_unit', 'spec_to_study', 'status', 'target', 'design', 'date', 'note', 'priority', 'employee_number', 'detail_and_output', 'tool', 'responsible', 'period', 'flag_primary', 'usecase_id', 'usecase', 'usecase_parameter_id', 'parameter_name', 'usecase_unit', 'category', 'value'])
            
            query = "select * from R_project_record where project_id=%s and phase_id=%s;"
            df_R = pd.read_sql_query(query, self.conn, params=[project_id, phase_id])
            return df_R
                
        except psycopg2.Error as e:
            
            # エラー発生時にロールバック
            self.conn.rollback()
            raise e #raise分の位置を帰る　山口　10/25
            return None

    def get_R_parameter(self):
        try:
            cur = self.conn.cursor()
            
            cur.execute("select * from r_parameter order by id;")
            
            result = cur.fetchall()
            df_R = pd.DataFrame(result,columns=['id','performance','design_item_1','design_item_2','design_item_3','unit','hierarchy_id','wp_id'])
            return df_R
                
        except psycopg2.Error as e:
            
            # エラー発生時にロールバック
            self.conn.rollback()
            raise e #raise分の位置を帰る　山口　10/25
            return None
    # # Rリスト取得 #チョー　01/08 
    # def posgre_get_rlist(self, select_list = [], select_list2 = [], select_list3 = [],select_list4 = [],select_list5 = []):
    #     connection = self.conn
    #     select_list_str = ', '.join(f"'{item}'" for item in select_list)
    #     select_list_str2 = ', '.join(f"'{item}'" for item in select_list2)
    #     select_list_str3 = ', '.join(f"'{item}'" for item in select_list3)
    #     select_list_str4 = ', '.join(f"'{item}'" for item in select_list4)
    #     select_list_str5 = ', '.join(f"'{item}'" for item in select_list5)
    #     self.set_condition_log(select_list_str, select_list_str2, select_list_str3, 'Null', st.session_state.username)
        
    #     print('query::')
    #     query1 = f"""
    #         SELECT DISTINCT ON (rpr.project_id, rpr.destination_id, rpr.drivetrain_id, rpr.lot_id, rpr.phase_id,rpr.r_parameter_id)
    #             rpr.project_id, rpr.destination_id, rpr.drivetrain_id, rpr.lot_id, rpr.phase_id,rpr.r_parameter_id
    #         FROM r_project_record AS rpr
    #         INNER JOIN project_info AS pjf ON rpr.project_id = pjf.id
    #         WHERE pjf.project_code IN ({select_list_str})
    #         AND rpr.destination IN ({select_list_str2})
    #         AND rpr.drivetrain IN ({select_list_str3})
    #         AND rpr.lot IN ({select_list_str4})
    #         AND rpr.phase IN ({select_list_str5})
    #         ORDER BY rpr.project_id, rpr.destination_id, rpr.drivetrain_id, rpr.lot_id, rpr.phase_id,rpr.r_parameter_id
    #     """
    #     print('Queryy: ', query1)
    #     df1 = pd.read_sql_query(query1, connection)

    #     #山口　複数条件のtargetを横に並べるため、各メタ情報ごとにクエリ分ける 1/27

    #     query2 = f"""
    #         SELECT rpr.project_id, rpr.setup_id, rpr.destination_id, rpr.destination, 
    #             rpr.drivetrain_id, rpr.drivetrain, rpr.architecture_id, rpr.architecturename, 
    #             rpr.lot_id, rpr.lot, rpr.phase_id, rpr.phase, rpr.r_parameter_id, 
    #             rpr.hierarchy_id, rpr.wp_id, rpr.performance, rpr.design_item_1, 
    #             rpr.design_item_2, rpr.design_item_3, rpr.r_unit, rpr.spec_to_study, 
    #             rpr.status, rpr.target, rpr.date, rpr.note, rpr.priority, 
    #             rpr.employee_number, rpr.detail_and_output, rpr.tool, rpr.responsible, 
    #             rpr.period, rpr.usecase_id, rpr.usecase, rpr.usecase_parameter_id, 
    #             rpr.parameter_name, rpr.usecase_unit, rpr.category, rpr.value,
    #             ut.section_code,CONCAT(ut.contac_person_first_name, ' ',ut.contac_person_last_name) AS employee_name
    #         FROM r_project_record as rpr
    #         INNER JOIN project_info AS pjf on rpr.project_id = pjf.id
    #         INNER JOIN user_table AS ut on ut.employee_number = rpr.employee_number    
    #         WHERE pjf.project_code IN ({select_list_str})
    #         AND rpr.destination IN ({select_list_str2})
    #         AND rpr.drivetrain IN ({select_list_str3})
    #         AND rpr.lot IN ({select_list_str4})
    #         AND rpr.phase IN ({select_list_str5}) 
    #         ORDER BY rpr.project_id, rpr.destination_id, rpr.drivetrain_id, rpr.lot_id, rpr.phase_id,rpr.r_parameter_id,usecase_parameter_id
    #     """
    #     print('Queryy: ', query2)
    #     df2 = pd.read_sql_query(query2, connection)

    #     df2_filtered = df2.drop_duplicates(subset=['project_id', 
    #                                             'destination_id', 
    #                                             'drivetrain_id', 
    #                                             'lot_id', 
    #                                             'phase_id', 
    #                                             'r_parameter_id']).reset_index(drop=True)
    #     for index, row in df1.iterrows():
    #         # print('index: ', index)
    #         for i, r in df2.iterrows():
    #             if (row['r_parameter_id'] == r['r_parameter_id'] and
    #             row['project_id'] == r['project_id'] and
    #             row['destination_id'] == r['destination_id'] and
    #             row['drivetrain_id'] == r['drivetrain_id'] and
    #             row['lot_id'] == r['lot_id'] and
    #             row['phase_id'] == r['phase_id']):
    #                 # Get the parameter name and value
    #                 parameter_name = r['parameter_name']
    #                 value = r['value']
                    
    #                 df2_filtered.at[index, parameter_name] = value
        
    #     return df2,df2_filtered



    # Rリスト取得 #チョー　01/08 
    def posgre_get_rlist(self, select_list = [], select_list2 = [], select_list3 = [],select_list4 = [],select_list5 = [],select_list6 = []):
        connection = self.conn
        select_list_str = ', '.join(f"'{item}'" for item in select_list)
        select_list_str2 = ', '.join(f"'{item}'" for item in select_list2)
        select_list_str3 = ', '.join(f"'{item}'" for item in select_list3)
        select_list_str4 = ', '.join(f"'{item}'" for item in select_list4)
        select_list_str5 = ', '.join(f"'{item}'" for item in select_list5)
        select_list_str6 = ', '.join(f"'{item}'" for item in select_list6)


        

        self.set_condition_log(select_list_str, select_list_str2, select_list_str3, 'Null', st.session_state.username)
        
        print('r query::')


        #チョー　03/10
        query1 = f"""
            SELECT DISTINCT ON (rpr.project_id, rpr.destination_id, rpr.drivetrain_id, rpr.lot_id, rpr.phase_id, rpr.r_parameter_id, rpr.variation_id)
                rpr.project_id, pjf.project_code, rpr.destination_id, rpr.destination, rpr.drivetrain_id, rpr.drivetrain, rpr.lot_id, rpr.lot, rpr.phase_id, rpr.phase, rpr.r_parameter_id, rpr.variation_id, rpr.variation, rpr.usecase_id
            FROM r_project_record AS rpr
            INNER JOIN project_info AS pjf ON rpr.project_id = pjf.id
            WHERE pjf.project_code IN ({select_list_str})
            AND rpr.destination IN ({select_list_str2})
            AND rpr.drivetrain IN ({select_list_str3})
            AND rpr.lot IN ({select_list_str4})
            AND rpr.phase IN ({select_list_str5})
        """
        #チョー　03/10　#Conditionally add the rpr.variation condition if select_list_str6 has values
        if select_list_str6:
            query1 += f"AND rpr.variation IN ({select_list_str6})\n"
        
        #チョー　03/10　#Final part of the query
        query1 += """
            ORDER BY rpr.project_id, rpr.destination_id, rpr.drivetrain_id, rpr.lot_id, rpr.phase_id, rpr.r_parameter_id
        """

        print('Queryy: ', query1)
        df1 = pd.read_sql_query(query1, connection)
        #山口 select_listの全組み合わせを取得1/28
        print(df1[['project_id', 'phase_id', 'variation_id']])
        df_selects = df1[['project_id','phase_id','variation_id','drivetrain_id','drivetrain', 'phase', 'variation']].drop_duplicates() #チョー　05/07
        drivetrain_selects = df1[['drivetrain_id', 'drivetrain']].drop_duplicates().sort_values(by='drivetrain_id') #チョー　05/07　サマリーのDrivetrainDropdownのため
        #チョー　03/10
        # df_pj_list = df_selects 
        df_pj_list = df1[['project_id', 'project_code','destination','phase_id','variation_id','drivetrain', 'phase', 'variation','lot']].drop_duplicates()
        
        # print('df_pj_list before:',df_pj_list)
        df_pj_list['r_selectbox_format'] = df_pj_list.apply(lambda row: f"{row['project_code']}; {row['destination']}; {row['drivetrain']}; {row['lot']}; {row['phase']}; {row['variation']}", axis=1)
        # print('df_pj_list after:',df_pj_list)
        
        if not select_list_str6:
            options = df_pj_list['r_selectbox_format'].tolist()
            options.insert(0, '選択してください。')
            st.session_state.total_selected_rlist = options
            st.session_state.selected_r_summary = df_selects #チョー　RサマリーListを取得するため　04/24
            #チョー　05/07　サマリーのDrivetrainDropdownのため
            dt_list = drivetrain_selects['drivetrain'].tolist()
            dt_list.insert(0, '選択してください。') 
            st.session_state.total_drivetrain_selected = dt_list
        if len(df_selects) >1:
            df_selects = df_selects.head(1)
        #     options = df_pj_list['variation'].tolist()
        #     options.insert(0, '選択してください。')
        #     st.session_state.total_selected_rlist = options
        # elif not select_list_str6 and not len(df_selects) >1:
        #     options = df_selects['variation'].tolist()
        #     options.insert(0, '選択してください。')
        #     st.session_state.total_selected_rlist = options

        

        st.session_state.df_selects = df_selects
        num_selects = len(df_selects)
        print('num_selects:' + str(num_selects))

        self.get_resized_column(df_selects) #Kyaw 07/23 Get the resized columns

        r_parameter_id_query = "COALESCE("
        performance_query = "COALESCE("
        design_item_1_query = "COALESCE("
        design_item_2_query = "COALESCE("
        design_item_3_query = "COALESCE("
        r_unit_query = "COALESCE("
        index_query = "COALESCE("
        usecase_id_query = "COALESCE("
        usecase_query = "COALESCE("
        usecase_parameter_query = "COALESCE("
        parameter_name_query = "COALESCE("
        usecase_unit_query = "COALESCE("
        category_query = "COALESCE("
        value_query = "COALESCE("
        select_queries = [["r_parameter_id", "performance", "design_item_1", "design_item_2", "design_item_3", "r_unit", "index", "usecase_id", "usecase", "usecase_parameter_id", "parameter_name", "usecase_unit", "category", "value"],
            [r_parameter_id_query, performance_query, design_item_1_query, design_item_2_query, design_item_3_query, r_unit_query, index_query, usecase_id_query, usecase_query, usecase_parameter_query, parameter_name_query, usecase_unit_query, category_query, value_query ]
            ]
        #山口　先に全体のselect分定義 
        query2 =f'''SELECT 
                '''
        for i in range(len(select_queries[0])):
            for num in range(num_selects):

                select_queries[1][i]=  select_queries[1][i] + 'selection' + str(num) + '.' + select_queries[0][i]
                if num==num_selects-1:
                    select_queries[1][i]=  select_queries[1][i] + ') AS ' + select_queries[0][i]
                    
                    select_queries[1][i]=  select_queries[1][i] + ','
                else:
                    select_queries[1][i]=  select_queries[1][i] + ', '
            query2=query2 + select_queries[1][i]
        print('query2: ',query2)
        
        i = 0
        for index, row in df_selects.iterrows():
            select_1 =row.iloc[0]
            select_2 =row.iloc[1]
            select_3 =row.iloc[2]
            #山口　新たにdesign列を追加 1/29 編集ダイアログで項目名を表示させるためには、それらの行もproject_id;○○;phase_idvariation_idの列名にする必要があると判明、ダイアログに表示したい項目だけ付け足すことに  職制承認、職制承認コメント列を追加した。 山口3/22
            query2 = query2 + f"""
            selection{i}."{select_1};project_id;{select_2}{select_3}", 
            selection{i}."{select_1};setup_id;{select_2}{select_3}", 
            selection{i}."{select_1};phase_id;{select_2}{select_3}", 
            selection{i}."{select_1};phase;{select_2}{select_3}", 
            selection{i}."{select_1};variation_id;{select_2}{select_3}", 
            selection{i}."{select_1};variation;{select_2}{select_3}",
            selection{i}."{select_1};wp_id;{select_2}{select_3}",
            selection{i}."{select_1};spec_to_study;{select_2}{select_3}", 
            selection{i}."{select_1};status;{select_2}{select_3}", 
            selection{i}."{select_1};target;{select_2}{select_3}", 
            selection{i}."{select_1};adjusted_target;{select_2}{select_3}", 
            selection{i}."{select_1};design;{select_2}{select_3}", 
            selection{i}."{select_1};judge;{select_2}{select_3}", 
            selection{i}."{select_1};judge_evidence;{select_2}{select_3}", 
            selection{i}."{select_1};auto_judge_id;{select_2}{select_3}", 
            selection{i}."{select_1};manager_approval;{select_2}{select_3}", 
            selection{i}."{select_1};manager_approval_comment;{select_2}{select_3}", 
            selection{i}."{select_1};date;{select_2}{select_3}", 
            selection{i}."{select_1};note;{select_2}{select_3}", 
            selection{i}."{select_1};priority;{select_2}{select_3}", 
            selection{i}."{select_1};employee_number;{select_2}{select_3}", 
            selection{i}."{select_1};detail_and_output;{select_2}{select_3}", 
            selection{i}."{select_1};tool;{select_2}{select_3}", 
            selection{i}."{select_1};responsible;{select_2}{select_3}", 
            selection{i}."{select_1};period;{select_2}{select_3}", 
            selection{i}."{select_1};flag_primary;{select_2}{select_3}",
            selection{i}."{select_1};section_code;{select_2}{select_3}",
            selection{i}."{select_1};employee_name;{select_2}{select_3}",
            selection{i}.r_parameter_id as "{select_1};r_parameter_id;{select_2}{select_3}",
            selection{i}.performance as "{select_1};performance;{select_2}{select_3}",
            selection{i}.design_item_1 as "{select_1};design_item_1;{select_2}{select_3}",
            selection{i}.design_item_2 as "{select_1};design_item_2;{select_2}{select_3}",
            selection{i}.design_item_3 as "{select_1};design_item_3;{select_2}{select_3}",
            selection{i}.r_unit as "{select_1};r_unit;{select_2}{select_3}"
            
            """
            if i != len(df_selects)-1:
                query2 = query2 + ","
            i+=1
        print(query2)
        query2 = query2 + 'FROM'


        #山口　各select_listの数クエリを結合イメージ
        i =0
        for index, row in df_selects.iterrows():
            select_1 =row.iloc[0]
            select_2 =row.iloc[1]
            select_3 =row.iloc[2]

            if i >0:
                query2 = query2 + 'FULL OUTER JOIN'
            #山口　新たにdesign列を追加 1/29
            query2 =  query2 + f"""
                    (
                    SELECT rpr.project_id as "{select_1};project_id;{select_2}{select_3}", 
                        rpr.setup_id as "{select_1};setup_id;{select_2}{select_3}", 
                        rpr.destination_id as "{select_1};destination_id;{select_2}{select_3}", 
                        rpr.destination as "{select_1};destination;{select_2}{select_3}", 
                        rpr.drivetrain_id as "{select_1};drivetrain_id;{select_2}{select_3}", 
                        rpr.drivetrain as "{select_1};drivetrain;{select_2}{select_3}", 
                        rpr.architecture_id as "{select_1};architecture_id;{select_2}{select_3}", 
                        rpr.architecturename as "{select_1};architecturename;{select_2}{select_3}", 
                        rpr.lot_id as "{select_1};lot_id;{select_2}{select_3}", 
                        rpr.lot as "{select_1};lot;{select_2}{select_3}", 
                        rpr.phase_id as "{select_1};phase_id;{select_2}{select_3}", 
                        rpr.phase as "{select_1};phase;{select_2}{select_3}", 
                        rpr.r_parameter_id as "r_parameter_id", 
                        rpr.variation_id as "{select_1};variation_id;{select_2}{select_3}", 
                        rpr.variation as "{select_1};variation;{select_2}{select_3}",
                        rpr.hierarchy_id as "{select_1};hierarchy_id;{select_2}{select_3}", 
                        rpr.wp_id as "{select_1};wp_id;{select_2}{select_3}", 
                        rpr.performance as "performance", 
                        rpr.design_item_1 as "design_item_1", 
                        rpr.design_item_2 as "design_item_2", 
                        rpr.design_item_3 as "design_item_3", 
                        rpr.r_unit as "r_unit", 
                        rpr.index as "index",
                        rpr.spec_to_study as "{select_1};spec_to_study;{select_2}{select_3}", 
                        rpr.status as "{select_1};status;{select_2}{select_3}", 
                        rpr.target as "{select_1};target;{select_2}{select_3}", 
                        rpr.adjusted_target as "{select_1};adjusted_target;{select_2}{select_3}", 
                        rpr.auto_judge_id as "{select_1};auto_judge_id;{select_2}{select_3}",
                        rpr.design as "{select_1};design;{select_2}{select_3}", 
                        rpr.judge as "{select_1};judge;{select_2}{select_3}", 
                        rpr.judge_evidence as "{select_1};judge_evidence;{select_2}{select_3}", 
                        rpr.manager_approval as "{select_1};manager_approval;{select_2}{select_3}", 
                        rpr.manager_approval_comment as "{select_1};manager_approval_comment;{select_2}{select_3}", 
                        COALESCE(TO_CHAR(rpr.date,'YYYY-MM-DD'),'') AS "{select_1};date;{select_2}{select_3}", 
                        rpr.note as "{select_1};note;{select_2}{select_3}", 
                        rpr.priority as "{select_1};priority;{select_2}{select_3}", 
                        rpr.employee_number as "{select_1};employee_number;{select_2}{select_3}", 
                        rpr.detail_and_output as "{select_1};detail_and_output;{select_2}{select_3}", 
                        rpr.tool as "{select_1};tool;{select_2}{select_3}", 
                        rpr.responsible as "{select_1};responsible;{select_2}{select_3}", 
                        rpr.period as "{select_1};period;{select_2}{select_3}", 
                        rpr.usecase_id as "usecase_id", 
                        rpr.usecase as "usecase", 
                        rpr.usecase_parameter_id as "usecase_parameter_id", 
                        rpr.parameter_name as "parameter_name", 
                        rpr.usecase_unit as "usecase_unit", 
                        rpr.category as "category", 
                        rpr.value as "value", 
                        rpr.flag_primary as "{select_1};flag_primary;{select_2}{select_3}",
                        ut.section_code as "{select_1};section_code;{select_2}{select_3}",
                        CONCAT(ut.contac_person_first_name, ' ',ut.contac_person_last_name) AS "{select_1};employee_name;{select_2}{select_3}"
                    FROM r_project_record as rpr
                    INNER JOIN project_info AS pjf on rpr.project_id = pjf.id
                    LEFT JOIN user_table AS ut on ut.employee_number = rpr.employee_number    
                    WHERE pjf.id ='{select_1}'
                    AND rpr.phase_id ='{select_2}'
                    AND rpr.variation_id ='{select_3}'
                    and rpr.usecase_parameter_id not in (5,6)
                    
                    ) as selection{str(i)}
                """#山口　主要性能、バリエーションの追加 1/27 時系列データ(5,6)は省く 1/29

            if i>0:
                query2 = query2 + f"""
                on selection0.r_parameter_id = selection{str(i)}.r_parameter_id
                AND selection0.usecase_id = selection{str(i)}.usecase_id
                """
            i = i + 1
        query2 = query2 + "ORDER BY index" #index列を追加
        print('Queryy: ', query2)
        df2 = pd.read_sql_query(query2, connection)
        def assign_value_auto_judge(current_row):
            row_judge_type = current_row[f"{select_1};auto_judge_id;{select_2}{select_3}"]

            try:
                row_target_value = float(current_row[f"{select_1};target;{select_2}{select_3}"])
                row_design_value = float(current_row[f"{select_1};design;{select_2}{select_3}"])
            except:
                return ""


            if row_judge_type == 1:
                # return row[f"{select_1};judge;{select_2}{select_3}"]
                return ""

            elif row_judge_type == 2:
                if row_design_value >= row_target_value:
                    return "OK"
                else:
                    return "NG"

            elif row_judge_type == 3:
                if row_design_value <= row_target_value:
                    return "OK"
                else:
                    return "NG"

            elif row_judge_type == 4:
                if row_design_value == row_target_value:
                    return "OK"
                else:
                    return "NG"

            else:
                return ""

        def assign_auto_judge_type(current_row):
            convert_dict = {
                1: "未定",
                2: "以上",
                3: "以下",
                4: "同等",
            }

            row_judge_type = current_row[f"{select_1};auto_judge_id;{select_2}{select_3}"]
            if row_judge_type in convert_dict.keys():
                return convert_dict[row_judge_type]
            else:
                return "未定"

        df2[f"{select_1};auto_judge_type;{select_2}{select_3}"] = df2.apply(assign_auto_judge_type, axis = 1)

        df2[f"{select_1};auto_judge_result;{select_2}{select_3}"] = df2.apply(assign_value_auto_judge, axis = 1)

        print('query asked')
        #山口　も各select_listごとに
        for index, row in df_selects.iterrows():
            select_1 =row.iloc[0]
            select_2 =row.iloc[1]
            select_3 =row.iloc[2]

            df2_filtered = df2.drop_duplicates(subset=[f"""{select_1};project_id;{select_2}{select_3}""", 
                    f"""{select_1};phase_id;{select_2}{select_3}""", 
                    f"""{select_1};variation_id;{select_2}{select_3}""", 
                    "r_parameter_id"]).reset_index(drop=True)
        print('filtered')
        #ユースケース情報の変換も　高速化のためusecase_id,usecase_detail_id,parameter_nameでうまいことやる
        df_usecase_parameters = df2[['usecase_parameter_id', 'parameter_name']].drop_duplicates().dropna(how='all')
        usecase_parameters_dict = {row['usecase_parameter_id']: row['parameter_name'] for index, row in df_usecase_parameters.iterrows()}
        print('got usecase_dict')
        print(usecase_parameters_dict)
        for index2, row2 in df_selects.iterrows():
            select_1 =row2.iloc[0]
            select_2 =row2.iloc[1]
            select_3 =row2.iloc[2]
            for index, row in df2_filtered.iterrows():
                #print(row)
                #print('index: ', index)
                project_id=row[f"""{select_1};project_id;{select_2}{select_3}"""]
                phase_id=row[f"""{select_1};phase_id;{select_2}{select_3}"""]
                variation_id=row[f"""{select_1};variation_id;{select_2}{select_3}"""]
                r_parameter_id=row['r_parameter_id']
                #print(project_id + phase_id + variation_id + r_parameter_id)
                for parameter_id, parameter_name in usecase_parameters_dict.items():
         
                    value = df2[(df2[f"""{select_1};project_id;{select_2}{select_3}"""]==project_id) & (df2[f"""{select_1};phase_id;{select_2}{select_3}"""]==phase_id) &
                                (df2[f"""{select_1};variation_id;{select_2}{select_3}"""]==variation_id) & (df2["r_parameter_id"]==r_parameter_id) &
                                 (df2["usecase_parameter_id"]==parameter_id)]#ここでユースケース詳細が定義されていないものはエラーになる
                    #print(value)
                    if not value.empty:
                        value = value.loc[:,'value'].iloc[0]
                        df2_filtered.at[index, parameter_name] =value


                # for i, r in df2.iterrows():
                

                #     if (row['usecase_id'] == r["usecase_id"] ):
                #         # Get the parameter name and value
                #         parameter_name = r["parameter_name"]
                #         value = r["value"]
                        
                #         df2_filtered.at[index, parameter_name] = value
                #         continue
        #山口　flag_primary列は各selectでの和をとって一つの列にする
        flag_columns = df2_filtered.filter(like='flag_primary').columns
        df2_filtered['flag_primary'] = df2_filtered[flag_columns].max(axis=1)
        df2_filtered['flag_primary']= df2_filtered['flag_primary'].replace({0:'詳細性能', 1:'主要性能'})#山口　主要性能フラグを置換1/27

        #
        #山口　編集機能追加のためselected列を追加する 1/29
        for index2, row2 in df_selects.iterrows():
            select_1 =row2.iloc[0]
            select_2 =row2.iloc[1]
            select_3 =row2.iloc[2]
            # print(co)
            df2_filtered[f"""{select_1};target_selected;{select_2}{select_3}"""] = False
        df2_filtered['timeseries_selected'] = False # 山口　時系列を選択するためのセレクタ

        #02/07　チョー　ステータスのMapping
        status_mapping = {
            1: '1.項目検討中',
            2: '2.設定完了',
            0: ''
        }
        status_columns = df2_filtered.filter(like='status').columns
        for status_column in status_columns:
            df2_filtered[status_column] = df2_filtered[status_column].replace(status_mapping)

        #山口　選択されたプロジェクトが変わったらグリッドオプションを再定義する必要があるため、session_state内のグリッドオプションを消す
        if 'rgo' in st.session_state:
            del st.session_state.ago

        return df2,df2_filtered
    

    # def get_sim_performance(self, study_list = []):
    #     connection = self.conn
    #     study_list_str = ', '.join(f"'{item}'" for item in study_list)
    #     query = f"""select * from test_senario_project_record
    #                 where study_id IN ({study_list_str}) and senario_parameter_id in (3) order by study_id asc;"""
        
    #     result = pd.read_sql_query(query, connection)
#     return result
    def get_usecase_list(self): #山口 ただユースケース一覧を持ってくるだけ 1/31
        try:
            cur = self.conn.cursor()
            cur.execute("""
                    select * from usecase_overall;
            """)
            result = cur.fetchall()
            df_usecase = pd.DataFrame(result, columns=['usecase_id','usecase', 'usecase_parameter_id', 'parameter_name','unit','category','value'])
            self.conn.commit()
            if cur:
                cur.close()  
            if len(result)>=1:
                return df_usecase
            else:
                return None
            
        except psycopg2.Error as e:
            
            # エラー発生時にロールバック
            self.conn.rollback()
            raise e 
            return None
        
    def getr_value_to_sim(self, project_ids , destinations, drivetrains, phase_ids, variation_ids, selected_perf_list = []):

        connection = self.conn
        project_ids_str = ', '.join(f"'{item}'" for item in project_ids)
        destinations_str = ', '.join(f"'{item}'" for item in destinations)
        drivetrains_str = ', '.join(f"'{item}'" for item in drivetrains)
        phase_ids_str = ', '.join(f"'{item}'" for item in phase_ids)
        variation_ids_str = ', '.join(f"'{item}'" for item in variation_ids)
        selected_perf_list_str = ', '.join(f"'{item}'" for item in selected_perf_list)
        # SQL query to execute
        query = f"""
            WITH study_id_values AS (
                -- Common subquery to get dynamic study_id values based on senario_parameter_id = 14
                SELECT DISTINCT tspr2.study_id, tspr2.overall_value
                FROM public.test_senario_project_record tspr2
                WHERE tspr2.senario_parameter_id = 14
                AND tspr2.study_id IN (
                    -- Query 1: Get the dynamic study_id values from the first query
                    SELECT DISTINCT tspr1.study_id
                    FROM public.test_senario_project_record tspr1
                    WHERE tspr1.senario_parameter_id = 3 
                    AND tspr1.overall_value IN ({selected_perf_list_str})
                )
                AND tspr2.project_id IN ({project_ids_str})
                AND tspr2.destination IN ({destinations_str})
                AND tspr2.drivetrain IN ({drivetrains_str})
                AND tspr2.phase_id IN ({phase_ids_str})
                AND tspr2.variation_id IN ({variation_ids_str})
            )
            SELECT 
                DISTINCT ON (rpr.usecase) rpr.design_item_2
            FROM 
                public.test_senario_project_record tspr
            JOIN 
                public.r_project_record rpr
                ON tspr.project_id = rpr.project_id 
                AND tspr.phase = rpr.phase
                AND tspr.variation = rpr.variation
            JOIN 
                study_id_values siv
                ON tspr.study_id = siv.study_id
            WHERE 
                tspr.senario_parameter_id = 3 
                AND tspr.overall_value IN ({selected_perf_list_str})
                AND rpr.project_id IN ({project_ids_str})
                AND rpr.destination IN ({destinations_str})
                AND rpr.drivetrain IN ({drivetrains_str})
                AND rpr.phase_id IN ({phase_ids_str})
                AND rpr.variation_id IN ({variation_ids_str})
                AND tspr.overall_value =  rpr.design_item_1
                AND rpr.usecase = siv.overall_value  -- Match usecase with tspr2.overall_value
            ORDER BY 
                rpr.usecase, rpr.project_id, rpr.phase, rpr.variation;
            """

        result = pd.read_sql_query(query, connection)

        return result
    

    def get_sim_fix_list(self, project_ids , destinations, drivetrains, phase_ids, variation_ids, selected_fix_list1 = [], selected_fix_list2 = []):
        connection = self.conn
        project_ids_str = ', '.join(f"'{item}'" for item in project_ids)
        destinations_str = ', '.join(f"'{item}'" for item in destinations)
        drivetrains_str = ', '.join(f"'{item}'" for item in drivetrains)
        phase_ids_str = ', '.join(f"'{item}'" for item in phase_ids)
        variation_ids_str = ', '.join(f"'{item}'" for item in variation_ids)
        selected_fix_list1_str = ', '.join(f"'{item}'" for item in selected_fix_list1)

        query = f"""
            WITH study_ids AS (
                SELECT project_id, phase_id, variation_id, study_id
                FROM test_senario_project_record
                WHERE senario_parameter_id = 3
                AND overall_value IN ({selected_fix_list1_str})
                ORDER BY project_id, phase_id, variation_id, study_id
            ),
            valid_study_ids1 AS (
                SELECT project_id, phase_id, variation_id, study_id
                FROM test_senario_project_record
                WHERE senario_parameter_id = 96
                AND project_id IN (SELECT project_id FROM study_ids)
                AND phase_id IN (SELECT phase_id FROM study_ids)
                AND variation_id IN (SELECT variation_id FROM study_ids)
                AND overall_value = '有効'
                AND study_id IN (SELECT study_id FROM study_ids)
                ORDER BY project_id, phase_id, variation_id, study_id
            ),
            valid_study_ids2 AS (
                SELECT v.project_id, v.phase_id, v.variation_id, v.study_id
                FROM valid_study_ids1 v
                JOIN test_senario_project_record t
                    ON v.project_id = t.project_id
                    AND v.phase_id = t.phase_id
                    AND v.variation_id = t.variation_id
                    AND v.study_id = t.study_id
                WHERE t.senario_parameter_id = 98
                AND (overall_value = 'UNFIXED' OR overall_value IS NULL)
                ORDER BY v.project_id, v.phase_id, v.variation_id, v.study_id
            )
            SELECT project_id, phase_id, variation_id, study_id,
                MAX(CASE WHEN senario_parameter_id = 3 THEN parameter_name_1 END) AS parameter_name_1,
                MAX(CASE WHEN senario_parameter_id = 3 THEN parameter_name_2 END) AS parameter_name_2,
                MAX(CASE WHEN senario_parameter_id = 3 THEN overall_value END) AS overall_value_3,
                MAX(CASE WHEN senario_parameter_id = 10001 THEN overall_value END) AS overall_value_10001,
                MAX(CASE WHEN senario_parameter_id = 10001 THEN rflcategory END) AS rflcategory,
                MAX(CASE WHEN senario_parameter_id = 10001 THEN rflid END) AS rflid
            FROM test_senario_project_record
            WHERE (project_id, phase_id, variation_id, study_id) IN (SELECT project_id, phase_id, variation_id, study_id FROM valid_study_ids2)
                AND senario_parameter_id IN (3, 10001, 98)  -- Filter the relevant parameter IDs
                AND project_id IN ({project_ids_str})
                AND destination IN ({destinations_str})
                AND drivetrain IN ({drivetrains_str})
                AND phase_id IN ({phase_ids_str})
                AND variation_id IN ({variation_ids_str})
            GROUP BY project_id, phase_id, variation_id, study_id
            ORDER BY project_id ASC, phase_id ASC, variation_id ASC, study_id ASC;
        """
        # Execute the query and load the results into a pandas DataFrame
        result = pd.read_sql_query(query, connection)
        return result
    

    def update_fixed_r_record(self,df):#山口　simテーブル交信用 12/3
        cur = None
        for index, row in df.iterrows():
            ove = row['overall_value_10001']
            print('ove: ', ove)
            try:
                cur = self.conn.cursor()

                # query = f"""
                #     UPDATE project_r_parameter SET design = '{row['overall_value_10001']}' WHERE project_id = {row['project_id']} AND phase_id = {row['phase_id']} AND variation_id = {row['variation_id']} AND r_parameter_id = {row['rflid']}
                # """
                # cur.execute(query) #値の編集　山口
                query = sql.SQL("""
                    UPDATE project_r_parameter
                    SET design = %s
                    WHERE project_id = %s AND phase_id = %s AND variation_id = %s AND r_parameter_id = %s
                """)

                cur.execute(query, (row['overall_value_10001'], row['project_id'], row['phase_id'], row['variation_id'], row['rflid']))
                print('updated: ',query)

                query1 = sql.SQL("""
                    UPDATE test_project_senario_parameter
                    SET updated_value = %s
                    WHERE project_id = %s AND phase_id = %s AND variation_id = %s AND senario_parameter_id = %s AND study_id = %s
                """)
                
                cur.execute(query1, ('FIXED', row['project_id'], row['phase_id'], row['variation_id'], 98, row['study_id']))
                print('updated1: ',query1)
            
            except InterfaceError as e:
                raise e
                # 接続が閉じられている場合、再接続を試みる
                self.conn = self.create_connection()
                if self.conn:
                    return self.column_to_list(query)
                else:
                    return None
            except psycopg2.Error as e:
                
                # エラー発生時にロールバック
                self.conn.rollback()
                raise e
                return None
            
        self.conn.commit()
        if cur:
            cur.close()
        return True
    
    # # -----Telema-----
    # def posgre_get_rfl(self, select_list = [], select_list2 = [], select_list3 = [],select_list4 = []):
    #     """階層で連結させたPRJ_RFLを取得
    #     Args:
    #         args (string,string,string,string): ダイアログ選択メタ情報
    #     Returns:
    #         dataframe: クエリ取得結果
    #     Author:
    #         Telema Tanaka
    #     Created:
    #         2025/01/28
    #     """

    #     connection = self.conn
    #     select_list_str = ', '.join(f"'{item}'" for item in select_list)
    #     select_list_str2 = ', '.join(f"'{item}'" for item in select_list2)
    #     select_list_str3 = ', '.join(f"'{item}'" for item in select_list3)
    #     select_list_str4 = ', '.join(f"'{item}'" for item in select_list4)
    #     self.set_condition_log(select_list_str, select_list_str2, select_list_str3, 'Null', st.session_state.username)

    #     if select_list and select_list2 and select_list3  and select_list4:
    #         # リストの要素をシングルクォートで囲んでカンマで結合
    #         select_list_str = ', '.join(f"'{item}'" for item in select_list)
    #         select_list_str2 = ', '.join(f"'{item}'" for item in select_list2)
    #         select_list_str3 = ', '.join(f"'{item}'" for item in select_list3)
    #         select_list_str4 = ', '.join(f"'{item}'" for item in select_list4)

    #         query = f"""
    #                 WITH pj AS(
    #                     SELECT 
    #                         pjf.id AS project_id,
    #                         pjf.project_code AS project_code,
    #                         lt.lot As lot
    #                     FROM
    #                         project_info AS pjf
    #                         JOIN setup AS stp ON pjf.setup_id = stp.id
    #                         JOIN destination AS dest ON dest.id = stp.destination_id
    #                         JOIN drivetrain AS dt ON stp.drivetrain_id = dt.id
    #                         JOIN lot AS lt ON pjf.lot_id = lt.id
    #                         WHERE pjf.project_code IN ({select_list_str})
    #                         AND dest.destination IN ({select_list_str2})
    #                         AND dt.drivetrain IN ({select_list_str3})
    #                         AND lt.lot IN ({select_list_str4})
    #                 ), l_r_table AS(
    #                     select r_s_id, l_s_id
	#                     from l_r_relation
    #                 ),vehicle_table AS(
    #                     SELECT
    #                         rfl_view.pj_id as c_r_pj_id,
    #                         rfl_view.r_wp as c_r_wp,
    #                         CASE
    #                             WHEN rfl_view.r_wp = '燃費電費' THEN 1
    #                             WHEN rfl_view.r_wp = '動力' THEN 2
    #                             WHEN rfl_view.r_wp = '4WD' THEN 4
    #                             WHEN rfl_view.r_wp = '熱性能' THEN 5
    #                             WHEN rfl_view.r_wp = '運転性' THEN 6
    #                         END as c_l_wp_id,
    #                         rfl_view.l_wp as c_l_wp,
    #                         pj.project_code as project_code,
    #                         r_s_id as c_r_s_id,
    #                         l_s_id as c_l_s_id,
    #                         r_item as c_r_item,
    #                         r_item_2 as c_r_item_2,
    #                         prfl_r as c_req,
    #                         r_unit as c_r_unit,
    #                         r_uc as c_r_scene,
    #                         f_id as c_f_id,
    #                         f_item as c_f_item,
    #                         prfl_f as c_func,
    #                         f_unit as c_f_unit,
    #                         l_item as c_l_item,
    #                         prfl_l as c_logic,
    #                         l_unit as c_l_unit,
    #                         l_uc as c_l_scene,
    #                         prfl_note as c_note,
    #                         allocation as c_allocation
    #                     FROM
    #                         rfl_view
    #                         INNER JOIN pj on rfl_view.pj_id = pj.project_id                            
    #                         where hierarchy_id = 1
    #                     )
    #                     ,system_table AS(
    #                     SELECT
    #                         rfl_view.pj_id as s_r_pj_id,
    #                         rfl_view.r_wp as s_r_wp,
    #                         rfl_view.l_wp as s_l_wp,
    #                         r_s_id as s_r_s_id,
    #                         l_s_id as s_l_s_id,
    #                         r_item as s_r_item,
    #                         r_item_2 as s_r_item_2,
    #                         prfl_r as s_req,
    #                         r_unit as s_r_unit,
    #                         r_uc as s_r_scene,
    #                         f_id as s_f_id,
    #                         f_item as s_f_item,
    #                         prfl_f as s_func,
    #                         f_unit as s_f_unit,
    #                         l_item as s_l_item,
    #                         prfl_l as s_logic,
    #                         l_unit as s_l_unit,
    #                         l_uc as s_l_scene,
    #                         prfl_note as s_note,
    #                         allocation as s_allocation
    #                     FROM
    #                         rfl_view
    #                     INNER JOIN pj on rfl_view.pj_id = pj.project_id                            
    #                     where hierarchy_id = 2
    #                     )
    #                     ,unit_table AS(
    #                     SELECT
    #                         rfl_view.pj_id as u_r_pj_id,
    #                         rfl_view.r_wp as u_r_wp,
    #                         rfl_view.l_wp as u_l_wp,
    #                         r_s_id as u_r_s_id,
    #                         l_s_id as u_l_s_id,
    #                         r_item as u_r_item,
    #                         r_item_2 as u_r_item_2,
    #                         prfl_r as u_req,
    #                         r_unit as u_r_unit,
    #                         r_uc as u_r_scene,
    #                         f_id as u_f_id,
    #                         f_item as u_f_item,
    #                         prfl_f as u_func,
    #                         f_unit as u_f_unit,
    #                         l_item as u_l_item,
    #                         prfl_l as u_logic,
    #                         l_unit as u_l_unit,
    #                         l_uc as u_l_scene,
    #                         prfl_note as u_note,
    #                         allocation as u_allocation
    #                     FROM
    #                         rfl_view
    #                     INNER JOIN pj on rfl_view.pj_id = pj.project_id                            
    #                     where hierarchy_id = 3
    #                     )
    #                     SELECT
    #                         v.*,
    #                         s.*,
    #                         u.*,
    #                         {select_list_str4} AS lot
    #                     FROM  vehicle_table as v
    #                     -- LEFT JOIN system_table as s on v.c_allocation = s.s_r_s_id
    #                     -- LEFT JOIN unit_table as u on s.s_allocation = u.u_r_s_id      
    #                     LEFT JOIN l_r_table as l_r on v.c_l_s_id = l_r.l_s_id
    #                     FULL OUTER JOIN system_table as s on s.s_r_s_id = l_r.r_s_id   
    #                     FULL OUTER JOIN unit_table as u on s.s_allocation = u.u_r_s_id
    #                     --WHERE l_r.r_s_id IS NOT NULL AND l_r.l_s_id IS NOT NULL           
    #                     ORDER BY c_r_s_id, c_f_id, c_l_s_id, s_r_s_id, s_f_id, s_l_s_id;--v.c_l_wp_id,c_l_s_id,s_l_s_id;
    #                 """
            
    #         print('rfl query: ', query) 
    #         result = pd.read_sql_query(query,connection)
    #         # print('rfl result: ', result)
    #         return result
    #     else:
    #         return []
    # # -----Telema-----

    # -----Telema-----
    def posgre_get_rfl(self, select_list = [], select_list2 = [], select_list3 = [],select_list4 = [], select_list5 = []): #山口 フェーズを指定するようにクエリ編集を加える 4/14
        """階層で連結させたPRJ_RFLを取得
        Args:
            args (string,string,string,string): ダイアログ選択メタ情報
        Returns:
            dataframe: クエリ取得結果
        Author:
            Telema Tanaka
        Created:
            2025/01/28
        """

        connection = self.conn
        select_list_str = ', '.join(f"'{item}'" for item in select_list)
        select_list_str2 = ', '.join(f"'{item}'" for item in select_list2)
        select_list_str3 = ', '.join(f"'{item}'" for item in select_list3)
        select_list_str4 = ', '.join(f"'{item}'" for item in select_list4)
        select_list_str5 =  ', '.join(f"'{item}'" for item in select_list5)
        self.set_condition_log(select_list_str, select_list_str2, select_list_str3, 'Null', st.session_state.username)

        if select_list and select_list2 and select_list3  and select_list4:
            # リストの要素をシングルクォートで囲んでカンマで結合
            select_list_str = ', '.join(f"'{item}'" for item in select_list)
            select_list_str2 = ', '.join(f"'{item}'" for item in select_list2)
            select_list_str3 = ', '.join(f"'{item}'" for item in select_list3)
            select_list_str4 = ', '.join(f"'{item}'" for item in select_list4)
            select_list_str5 = ', '.join(f"'{item}'" for item in select_list5)

            print(f'select_list_str2{select_list_str}')
            print(f'select_list_str2{select_list_str2}')
            print(f'select_list_str2{select_list_str3}')
            print(f'select_list_str2{select_list_str4}')
            print(f'select_list_str2{select_list_str5}')

            query = f""" --山口 related_se_parameterを追加3/27 ユニット階層が一切取れていないため修正
                    WITH pj AS(
                        SELECT 
                            pjf.id AS project_id,
                            pjf.project_code AS project_code,
                            lt.lot As lot
                        FROM
                            project_info AS pjf
                            JOIN setup AS stp ON pjf.setup_id = stp.id
                            JOIN destination AS dest ON dest.id = stp.destination_id
                            JOIN drivetrain AS dt ON stp.drivetrain_id = dt.id
                            JOIN lot AS lt ON pjf.lot_id = lt.id
                            WHERE pjf.project_code IN ({select_list_str})
                            AND dest.destination IN ({select_list_str2})
                            AND dt.drivetrain IN ({select_list_str3})
                            AND lt.lot IN ({select_list_str4})
                    ), l_r_table AS(
                        select r_s_id, l_s_id
	                    from l_r_relation
                    ),vehicle_table AS(
                        SELECT
                            rfl_view.pj_id as c_r_pj_id,
                            rfl_view.rfl_id as c_rfl_id,
                            rfl_view.phase_id as c_phase_id,
                            phase.phase as c_phase,
                            rfl_view.r_wp as c_r_wp,
                            rfl_view.r_wp_summary_index as c_r_wp_summary_index,  --チョー 05/12
                            rfl_view.flag_to as c_flag_to,
                            --CAST(rfl_view.flag_to AS TEXT) as c_flag_to,
                            rfl_view.to_solving_value as c_to_solving_value,
                            rfl_view.flag_display_on_summary_logic as c_flag_display_on_summary_logic,
                            --CASE
                            --    WHEN rfl_view.r_wp = '燃費電費' THEN 1
                            --    WHEN rfl_view.r_wp = '動力' THEN 2
                            --    WHEN rfl_view.r_wp = '4WD' THEN 4
                            --    WHEN rfl_view.r_wp = '熱性能' THEN 5
                            --    WHEN rfl_view.r_wp = '運転性' THEN 6
                            --    --ELSE NULL
                            --END as c_l_wp_id,
                            rfl_view.r_wp_ld as c_r_wp_id,
                            rfl_view.l_wp as c_l_wp,
                            pj.project_code as project_code,
                            r_s_id as c_r_s_id,
                            l_s_id as c_l_s_id,
                            r_item as c_r_item,
                            r_item_2 as c_r_item_2,
                            prfl_r as c_req,
                            r_unit as c_r_unit,
                            r_uc as c_r_scene,
                            f_id as c_f_id,
                            ddt.user_memo as c_user_memo,
                            f_item as c_f_item,
                            prfl_f as c_func,
                            f_unit as c_f_unit,
                            l_item as c_l_item,
                            prfl_l as c_logic,
                            l_unit as c_l_unit,
                            l_r_s_p_i as c_related_se_parameter_id,
                            prfl_note as c_note,
                            l_uc as c_l_scene,
                            allocation as c_allocation,
                            sender_judge as c_sender_judge,
                            sender_name as c_sender_name,
                            DATE(sender_date) as c_sender_date,
                            sender_comment as c_sender_comment,
                            receiver_judge as c_receiver_judge,
                            receiver_name as c_receiver_name,
                            DATE(receiver_date) as c_receiver_date,
                            receiver_comment as c_receiver_comment,
                            rfl_view.index as c_index,
                            rfl_view.req_condition as c_req_condition, -- ＃チョー 05/19
                            rfl_view.fun_condition as c_fun_condition, -- ＃チョー 05/19
                            rfl_view.log_condition as c_log_condition,  -- ＃チョー 05/19
                            rfl_view.is_to as c_is_to,
                            rfl_view.to_pattern as c_to_pattern
                        FROM rfl_view
                        INNER JOIN pj ON rfl_view.pj_id = pj.project_id
                        INNER JOIN phase on phase_id = phase.id
                        FULL OUTER JOIN (
                            SELECT DISTINCT ON (project_id, phase_id, rfl_id) *
                            FROM detail_data_to
                            ORDER BY project_id, phase_id, rfl_id, update_day DESC
                        ) AS ddt ON rfl_view.pj_id = ddt.project_id
                                    AND rfl_view.rfl_id = ddt.rfl_id
                                    AND rfl_view.phase_id = ddt.phase_id
                        WHERE rfl_view.hierarchy_id = 1
                        --AND rfl_view.r_wp_summary_index != 9999 
                        and phase.phase in ({select_list_str5})--山口　フェーズも選択に対応
                        )
                        ,system_table AS(
                        SELECT
                            pj.project_code as s_project_code, --project_codeを車両側以外でも表示する 山口 4/13 
                            rfl_view.pj_id as s_r_pj_id,
                            rfl_view.rfl_id as s_rfl_id,
                            rfl_view.phase_id as s_phase_id,
                            phase.phase as s_phase,
                            rfl_view.r_wp as s_r_wp,
                            rfl_view.l_wp as s_l_wp,
                            rfl_view.r_wp_summary_index as s_r_wp_summary_index,
                            rfl_view.flag_to as s_flag_to,
                            rfl_view.to_solving_value as s_to_solving_value,
                            rfl_view.flag_display_on_summary_logic as s_flag_display_on_summary_logic,  --チョー 05/12
                            r_s_id as s_r_s_id,
                            l_s_id as s_l_s_id,
                            r_item as s_r_item,
                            r_item_2 as s_r_item_2,
                            prfl_r as s_req,
                            r_unit as s_r_unit,
                            r_uc as s_r_scene,
                            f_id as s_f_id,
                            ddt.user_memo as s_user_memo,
                            f_item as s_f_item,
                            prfl_f as s_func,
                            f_unit as s_f_unit,
                            l_item as s_l_item,
                            prfl_l as s_logic,
                            l_unit as s_l_unit,
                            l_r_s_p_i as s_related_se_parameter_id,
                            l_uc as s_l_scene,
                            prfl_note as s_note,
                            allocation as s_allocation,
                            sender_judge as s_sender_judge,
                            sender_name as s_sender_name,
                            DATE(sender_date) as s_sender_date,
                            sender_comment as s_sender_comment,
                            receiver_judge as s_receiver_judge,
                            receiver_name as s_receiver_name,
                            DATE(receiver_date) as s_receiver_date,
                            receiver_comment as s_receiver_comment,
                            rfl_view.index as s_index,
                            rfl_view.req_condition as s_req_condition, -- ＃チョー 05/19
                            rfl_view.fun_condition as s_fun_condition, -- ＃チョー 05/19
                            rfl_view.log_condition as s_log_condition,  -- ＃チョー 05/19
                            rfl_view.is_to as s_is_to,
                            rfl_view.to_pattern as s_to_pattern
                        FROM
                            rfl_view
                        INNER JOIN pj on rfl_view.pj_id = pj.project_id  
                        INNER JOIN phase on phase_id = phase.id
                        FULL OUTER JOIN (
                            SELECT DISTINCT ON (project_id, phase_id, rfl_id) *
                            FROM detail_data_to
                            ORDER BY project_id, phase_id, rfl_id, update_day DESC
                        ) AS ddt ON rfl_view.pj_id = ddt.project_id
                                    AND rfl_view.rfl_id = ddt.rfl_id
                                    AND rfl_view.phase_id = ddt.phase_id                          
                        where hierarchy_id = 2
                        --AND rfl_view.r_wp_summary_index != 9999 --05/12 チョー
                        and phase.phase in ({select_list_str5})--山口　フェーズも選択に対応
                        )
                        ,unit_table AS(
                        SELECT
                            pj.project_code as u_project_code, --project_codeを車両側以外でも表示する 山口 4/13 
                            rfl_view.pj_id as u_r_pj_id,
                            rfl_view.rfl_id as u_rfl_id,
                            rfl_view.phase_id as u_phase_id,
                            phase.phase as u_phase,
                            rfl_view.r_wp_summary_index as u_r_wp_summary_index, --チョー 05/12
                            rfl_view.flag_to as u_flag_to,
                            --CAST(rfl_view.flag_to AS TEXT) as u_flag_to,
                            rfl_view.r_wp as u_r_wp,
                            rfl_view.l_wp as u_l_wp,
                            rfl_view.to_solving_value as u_to_solving_value,
                            rfl_view.flag_display_on_summary_logic as u_flag_display_on_summary_logic,
                            r_s_id as u_r_s_id,
                            l_s_id as u_l_s_id,
                            r_item as u_r_item,
                            r_item_2 as u_r_item_2,
                            prfl_r as u_req,
                            r_unit as u_r_unit,
                            r_uc as u_r_scene,
                            ddt.user_memo as u_user_memo,
                            f_id as u_f_id,
                            f_item as u_f_item,
                            prfl_f as u_func,
                            f_unit as u_f_unit,
                            l_item as u_l_item,
                            prfl_l as u_logic,
                            l_unit as u_l_unit,
                            l_r_s_p_i as u_related_se_parameter_id,
                            l_uc as u_l_scene,
                            prfl_note as u_note,
                            allocation as u_allocation,
                            sender_judge as u_sender_judge,
                            sender_name as u_sender_name,
                            DATE(sender_date) as u_sender_date,
                            sender_comment as u_sender_comment,
                            receiver_judge as u_receiver_judge,
                            receiver_name as u_receiver_name,
                            DATE(receiver_date) as u_receiver_date,
                            receiver_comment as u_receiver_comment,
                            rfl_view.index as u_index,
                            rfl_view.req_condition as u_req_condition, -- ＃チョー 05/19
                            rfl_view.fun_condition as u_fun_condition, -- ＃チョー 05/19
                            rfl_view.log_condition as u_log_condition,  -- ＃チョー 05/19
                            rfl_view.is_to as u_is_to,
                            rfl_view.to_pattern as u_to_pattern
                        FROM
                            rfl_view
                        INNER JOIN pj on rfl_view.pj_id = pj.project_id 
                        INNER JOIN phase on phase_id = phase.id 
                        FULL OUTER JOIN (
                            SELECT DISTINCT ON (project_id, phase_id, rfl_id) *
                            FROM detail_data_to
                            ORDER BY project_id, phase_id, rfl_id, update_day DESC
                        ) AS ddt ON rfl_view.pj_id = ddt.project_id
                                    AND rfl_view.rfl_id = ddt.rfl_id
                                    AND rfl_view.phase_id = ddt.phase_id                          
                        where hierarchy_id = 3
                        --AND rfl_view.r_wp_summary_index != 9999 --05/12 チョー
                        and phase.phase in ({select_list_str5})--山口　フェーズも洗濯に対応
                        )
                        SELECT
                            v.*,
                            s.*,
                            u.*,
                            {select_list_str4} AS lot
                        FROM  vehicle_table as v
                        -- LEFT JOIN system_table as s on v.c_allocation = s.s_r_s_id
                        -- LEFT JOIN unit_table as u on s.s_allocation = u.u_r_s_id      
                        LEFT JOIN l_r_table as cs_l_r on v.c_l_s_id = cs_l_r.l_s_id --山口　車両システム間のl_rをcs_l_rに改名 4/17
                        FULL OUTER JOIN system_table as s on s.s_r_s_id = cs_l_r.r_s_id   
                        --FULL OUTER JOIN unit_table as u on s.s_allocation = u.u_r_s_id 山口　ユニット階層の紐づけをWP_idではなくl_r_relationベースで行う4/17
                        LEFT JOIN l_r_table as su_l_r on s.s_l_s_id = su_l_r.l_s_id
                        FULL OUTER JOIN unit_table as u on u.u_r_s_id = su_l_r.r_s_id
                        --WHERE l_r.r_s_id IS NOT NULL AND l_r.l_s_id IS NOT NULL 
                        WHERE
                            (v.c_allocation IS NOT NULL AND s.s_r_s_id IS NOT NULL AND v.c_allocation = s.s_r_s_id)
                            OR
                            (v.c_allocation IS NULL OR s.s_r_s_id IS NULL)          
                        ORDER BY v.c_r_wp_id,c_l_s_id,s_l_s_id;
                    """
            
            #i wish i could make it simple that be able to leave "optimized sub-optimal code" like comment 

            print('rfl query: ', query) 
            # print('rfl query before retrieve: ', datetime.datetime.now())
            result = pd.read_sql_query(query,connection)
            # print('rfl query after retrieve: ', datetime.datetime.now())
            #st.write(result)
            # print('rfl result: ', result)
            #RFL承認に関係するチェックボックスの値 ＃チョー　04/14
            for prefix in ['c','s','u']:
                for role in ['sender','receiver']:
                    result[f'{prefix}_{role}_selected'] = False
            return result
        else:
            return []
    # -----Telema-----

    def alt_posgre_get_rfl(self, select_list = [], select_list2 = [], select_list3 = [],select_list4 = []):# 山口　wp表記を更新したalt_rfl_viewを取得する関数、効果検証次第消す3/4

            connection = self.conn
            select_list_str = ', '.join(f"'{item}'" for item in select_list)
            select_list_str2 = ', '.join(f"'{item}'" for item in select_list2)
            select_list_str3 = ', '.join(f"'{item}'" for item in select_list3)
            select_list_str4 = ', '.join(f"'{item}'" for item in select_list4)
            self.set_condition_log(select_list_str, select_list_str2, select_list_str3, 'Null', st.session_state.username)

            if select_list and select_list2 and select_list3  and select_list4:
                # リストの要素をシングルクォートで囲んでカンマで結合
                select_list_str = ', '.join(f"'{item}'" for item in select_list)
                select_list_str2 = ', '.join(f"'{item}'" for item in select_list2)
                select_list_str3 = ', '.join(f"'{item}'" for item in select_list3)
                select_list_str4 = ', '.join(f"'{item}'" for item in select_list4)

                query = f"""
                        WITH pj AS(
                            SELECT 
                                pjf.id AS project_id,
                                pjf.project_code AS project_code,
                                lt.lot As lot
                            FROM
                                project_info AS pjf
                                JOIN setup AS stp ON pjf.setup_id = stp.id
                                JOIN destination AS dest ON dest.id = stp.destination_id
                                JOIN drivetrain AS dt ON stp.drivetrain_id = dt.id
                                JOIN lot AS lt ON pjf.lot_id = lt.id
                                WHERE pjf.project_code IN ({select_list_str})
                                AND dest.destination IN ({select_list_str2})
                                AND dt.drivetrain IN ({select_list_str3})
                                AND lt.lot IN ({select_list_str4})
                        ), l_r_table AS(
                            select r_s_id, l_s_id
                            from l_r_relation
                        ),vehicle_table AS(
                            SELECT
                                alt_rfl_view.pj_id as c_r_pj_id,
                                alt_rfl_view.r_wp as c_r_wp,
                                CASE
                                    WHEN alt_rfl_view.r_wp = '燃費電費' THEN 1
                                    WHEN alt_rfl_view.r_wp = '動力' THEN 2
                                    WHEN alt_rfl_view.r_wp = '4WD' THEN 4
                                    WHEN alt_rfl_view.r_wp = '熱性能' THEN 5
                                    WHEN alt_rfl_view.r_wp = '運転性' THEN 6
                                    ELSE NULL
                                END as c_l_wp_id,
                                alt_rfl_view.l_wp as c_l_wp,
                                pj.project_code as project_code,
                                r_s_id as c_r_s_id,
                                l_s_id as c_l_s_id,
                                r_item as c_r_item,
                                r_item_2 as c_r_item_2,
                                prfl_r as c_req,
                                r_unit as c_r_unit,
                                r_uc as c_r_scene,
                                f_item as c_f_item,
                                prfl_f as c_func,
                                f_unit as c_f_unit,
                                l_item as c_l_item,
                                prfl_l as c_logic,
                                l_unit as c_l_unit,
                                l_uc as c_l_scene,
                                prfl_note as c_note,
                                allocation as c_allocation,
                                rfl_view.index as c_index
                            FROM
                                alt_rfl_view
                                INNER JOIN pj on alt_rfl_view.pj_id = pj.project_id                            
                                where hierarchy_id = 1
                            )
                            ,system_table AS(
                            SELECT
                                alt_rfl_view.pj_id as s_r_pj_id,
                                alt_rfl_view.r_wp as s_r_wp,
                                alt_rfl_view.l_wp as s_l_wp,
                                r_s_id as s_r_s_id,
                                l_s_id as s_l_s_id,
                                r_item as s_r_item,
                                r_item_2 as s_r_item_2,
                                prfl_r as s_req,
                                r_unit as s_r_unit,
                                r_uc as s_r_scene,
                                f_item as s_f_item,
                                prfl_f as s_func,
                                f_unit as s_f_unit,
                                l_item as s_l_item,
                                prfl_l as s_logic,
                                l_unit as s_l_unit,
                                l_uc as s_l_scene,
                                prfl_note as s_note,
                                allocation as s_allocation,
                                rfl_view.index as s_index
                            FROM
                                alt_rfl_view
                            INNER JOIN pj on alt_rfl_view.pj_id = pj.project_id                            
                            where hierarchy_id = 2
                            )
                            ,unit_table AS(
                            SELECT
                                alt_rfl_view.pj_id as u_r_pj_id,
                                alt_rfl_view.r_wp as u_r_wp,
                                alt_rfl_view.l_wp as u_l_wp,
                                r_s_id as u_r_s_id,
                                l_s_id as u_l_s_id,
                                r_item as u_r_item,
                                r_item_2 as u_r_item_2,
                                prfl_r as u_req,
                                r_unit as u_r_unit,
                                r_uc as u_r_scene,
                                f_item as u_f_item,
                                prfl_f as u_func,
                                f_unit as u_f_unit,
                                l_item as u_l_item,
                                prfl_l as u_logic,
                                l_unit as u_l_unit,
                                l_uc as u_l_scene,
                                prfl_note as u_note,
                                allocation as u_allocation,
                                rfl_view.index as u_index
                            FROM
                                alt_rfl_view
                            INNER JOIN pj on alt_rfl_view.pj_id = pj.project_id                            
                            where hierarchy_id = 3
                            )
                            SELECT
                                v.*,
                                s.*,
                                u.*,
                                {select_list_str4} AS lot
                            FROM  vehicle_table as v
                            -- LEFT JOIN system_table as s on v.c_allocation = s.s_r_s_id
                            -- LEFT JOIN unit_table as u on s.s_allocation = u.u_r_s_id      
                            LEFT JOIN l_r_table as l_r on v.c_l_s_id = l_r.l_s_id
                            FULL OUTER JOIN system_table as s on s.s_r_s_id = l_r.r_s_id   
                            FULL OUTER JOIN unit_table as u on s.s_allocation = u.u_r_s_id
                            --WHERE l_r.r_s_id IS NOT NULL AND l_r.l_s_id IS NOT NULL           
                            ORDER BY v.c_l_wp_id,c_l_s_id,s_l_s_id;
                        """
                
                print('rfl query: ', query) 
                result = pd.read_sql_query(query,connection)
                # print('rfl result: ', result)
                return result
            else:
                return []

    #山口 prj_rflのflag_display_on_summaryをupdateする
    def update_flag_display_on_summary(self,df_update_target):
        cur = self.conn.cursor()

        query ="update prj_rfl set flag_display_on_summary_logic = %s where project_info_id = %s and  phase_id = %s and rfl_id = %s"
        try:
            for i, row in df_update_target.iterrows():
                project_id = row['project_id']
                phase_id = row['phase_id']
                rfl_id = row['rfl_id']
                if row['summary_selected']:
                    flag_display_on_summary = 1
                else:
                    flag_display_on_summary = 0
                cur.execute(query,(flag_display_on_summary, project_id, phase_id, rfl_id))
        except psycopg2.Error as e:
                
            # エラー発生時にロールバック
            self.conn.rollback()
            raise e
            return None
            
        self.conn.commit()
        if cur:
            cur.close()        

    #RFL情報を変更する ＃チョー　04/14
    def update_rfl_approved_record(self,df,approver,sender_or_receiver):
        print('df rfl:',df)
        print('sender_or_receiver in DB:',sender_or_receiver)
        cur = None
        for index, row in df.iterrows():
            
            try:
                cur = self.conn.cursor()

                # Build the SET clause and params dynamically
                set_clauses = []
                params = []
                
                set_clauses += [
                    f'{sender_or_receiver}_judge = %s',
                    f'{sender_or_receiver}_name = %s',
                    f'{sender_or_receiver}_date = %s',
                    f'{sender_or_receiver}_comment = %s'
                ]
                params += [
                    row[f'{sender_or_receiver}_judge'],
                    approver,
                    None if approver is None else datetime.datetime.now(),
                    row[f'{sender_or_receiver}_comment']
                ]
                
                if set_clauses:
                    set_clause = ", ".join(set_clauses)
                    query = sql.SQL(f"""
                        UPDATE prj_rfl
                        SET {set_clause}
                        WHERE project_info_id = %s AND phase_id = %s AND rfl_id = %s;
                    """)

                    params += [row['prj_id'], row['phase_id'], row['rfl_id']]
                    cur.execute(query, params)
                    print('rfl approval updated:', query.as_string(cur))

            except InterfaceError as e:
                raise e
                # 接続が閉じられている場合、再接続を試みる
                self.conn = self.create_connection()
                if self.conn:
                    return self.column_to_list(query)
                else:
                    return None
            except psycopg2.Error as e:
                
                # エラー発生時にロールバック
                self.conn.rollback()
                raise e
                return None
            
        self.conn.commit()
        if cur:
            cur.close()
        return True    
    
    #ｒステートメントを取得する　＃チョー　04/16
    def get_r_statement(self, project_id, phase_id, category):
        project_id_list = ', '.join(f"{item}" for item in project_id)
        phase_id_list = ', '.join(f"{item}" for item in phase_id)

        connection = self.conn
        #チョー　03/10
        query1 = f"""
            SELECT DISTINCT ON (project_id,phase_id,category)
                project_id, phase_id, category, statement, to_char(update_day, 'YYYY-MM-DD HH24:MI') AS update_day
            FROM project_statement
            WHERE project_id in ({project_id_list})
            AND phase_id in ({phase_id_list})
            AND category = '{category}'
            ORDER BY project_id,phase_id,category
        """
        #print('Queryy: ', query1)
        df1 = pd.read_sql_query(query1, connection)
        return df1

    #ｒステートメントをInsert・Updateをする　＃チョー　04/16
    def insert_upd_r_statement(self,project_id, phase_id, category, statement):
        try:
            cur = self.conn.cursor()

            query = sql.SQL("""
                INSERT INTO project_statement (project_id, phase_id, category, statement,update_day)
                VALUES (%s, %s, %s, %s,%s)
                ON CONFLICT (project_id, phase_id, category)  -- specify the unique constraint
                DO UPDATE SET statement = %s, update_day = %s -- update the statement if there's a conflict
            """)
            cur.execute(query, (project_id, phase_id, category, statement,datetime.datetime.now(), statement,datetime.datetime.now()))
            # cur.execute(query, (statement, project_id,phase_id,category))
            #print('updated: ',query)

        except InterfaceError as e:
            raise e
            # 接続が閉じられている場合、再接続を試みる
            self.conn = self.create_connection()
            if self.conn:
                return self.column_to_list(query)
            else:
                return None
        except psycopg2.Error as e:
            
            # エラー発生時にロールバック
            self.conn.rollback()
            raise e
            return None
            
        self.conn.commit()
        if cur:
            cur.close()
        return True
    
    #ｒステートメントをInsert・Updateをする　＃チョー　04/16
    def insert_upd_r_statement(self,project_id, phase_id, category, statement):
        try:
            cur = self.conn.cursor()

            query = sql.SQL("""
                INSERT INTO project_statement (project_id, phase_id, category, statement,update_day)
                VALUES (%s, %s, %s, %s,%s)
                ON CONFLICT (project_id, phase_id, category)  -- specify the unique constraint
                DO UPDATE SET statement = %s, update_day = %s -- update the statement if there's a conflict
            """)
            cur.execute(query, (project_id, phase_id, category, statement,datetime.datetime.now(), statement,datetime.datetime.now()))
            # cur.execute(query, (statement, project_id,phase_id,category))
            #print('updated: ',query)

        except InterfaceError as e:
            raise e
            # 接続が閉じられている場合、再接続を試みる
            self.conn = self.create_connection()
            if self.conn:
                return self.column_to_list(query)
            else:
                return None
        except psycopg2.Error as e:
            
            # エラー発生時にロールバック
            self.conn.rollback()
            raise e
            return None
            
        self.conn.commit()
        if cur:
            cur.close()
        return True
    
    #r_summaryをproject_r_parameterから取得する　＃チョー　04/24
    def get_r_summary(self):
        connection = self.conn

        df1 = st.session_state.selected_r_summary #チョー　R-Listを取得する時のセッション　04/24

        df_select = df1[['project_id','phase_id','drivetrain_id','drivetrain']].drop_duplicates()
        # print('df_selects in r summary: ', df_selects)
        df_selects = df_select[df_select['drivetrain'] == st.session_state.dt_selected_option] #チョー　05/07　選択されたWDだけを表示する

        project_ids = df_selects['project_id'].tolist()
        phase_ids = df_selects['phase_id'].tolist()

        project_id_list = ', '.join(f"{item}" for item in project_ids)
        phase_id_list = ', '.join(f"{item}" for item in phase_ids)
        #チョー　03/10
        query1 = f"""
            SELECT prp.project_id,prp.phase_id,prp.variation_id,prp.r_parameter_id,rp.wp_id,rp.performance,prp.judge,prp.manager_approval, prp.manager_approval_comment, wp.summary_index
            FROM project_r_parameter AS prp
            INNER JOIN r_parameter AS rp on  prp.r_parameter_id = rp.id
            --left join wp_statement AS ws on  ws.project_id = prp.project_id and ws.phase_id = prp.phase_id and ws.wp_id = rp.wp_id
            INNER JOIN wp ON wp.id = rp.wp_id--山口 サマリーでの並び順をwp.summary_indexで指定するため 5/8
            where prp.project_id in ({project_id_list}) and prp.phase_id in ({phase_id_list}) and prp.judge is not null and prp.judge != ''
            order by prp.phase_id,rp.id asc
        """
        # print('Queryy2: ', query1)
        df2 = pd.read_sql_query(query1, connection)
        return df_selects,df2
    
    #wp_statementを取得する　＃チョー　04/24
    def get_wp_statement(self,project_id, phase_id, wp_id, category):
        connection = self.conn
        project_id_list = ', '.join(f"{item}" for item in project_id)
        phase_id_list = ', '.join(f"{item}" for item in phase_id)
        wp_id_list = ', '.join(f"{item}" for item in wp_id)
        #チョー　03/10
        query1 = f"""
            SELECT project_id, phase_id, wp_id, category, manager_approval, manager_approval_comment, to_char(update_day, 'YYYY-MM-DD HH24:MI') AS update_day
            FROM wp_statement
            WHERE project_id IN ({project_id_list})
            AND phase_id IN ({phase_id_list})
            AND wp_id IN ({wp_id_list})
            AND category = '{category}'
            ORDER BY project_id,phase_id,category, wp_id
        """
        print('Queryy: ', query1)
        df1 = pd.read_sql_query(query1, connection)
        return df1
    
    #ｒサマリーをInsert・Updateをする　＃チョー　04/24
    def insert_upd_r_summary(self,df):
        cur = None
        for index, row in df.iterrows():
            try:
                cur = self.conn.cursor()
                query = sql.SQL("""
                        INSERT INTO wp_statement (project_id, phase_id, wp_id, category, manager_approval, manager_approval_comment,update_day)
                        VALUES (%s, %s, %s, %s,%s, %s, %s)
                        ON CONFLICT (project_id, phase_id, wp_id, category)  -- specify the unique constraint
                        DO UPDATE SET manager_approval = %s, manager_approval_comment = %s, update_day = %s -- update the statement if there's a conflict
                    """)
                cur.execute(query, (row['project_id'], row['phase_id'], row['wp_id'], 'R',row['manager_approval'],row['manager_approval_comment'],datetime.datetime.now(), row['manager_approval'],row['manager_approval_comment'],datetime.datetime.now()))
            except psycopg2.Error as e:

                # エラー発生時にロールバック
                self.conn.rollback()
                raise e
                return None
            
        self.conn.commit()
        if cur:
            cur.close() 
            return True
        

    #kyaw-rfl
    def upd_rfl_summary_to_result(self,df):
        cur = None
        for index, row in df.iterrows():
            try:
                if row['to_pattern'] != 'TO':
                    row['is_to'] = False
                else:
                    row['is_to'] = True
                cur = self.conn.cursor()
                query = sql.SQL("""
                        UPDATE rfl SET is_to = %s, to_pattern = %s WHERE id = %s
                    """)
                print('query upd to result: ', query)
                cur.execute(query, (row['is_to'], row['to_pattern'], int(row['rfl_id'])))
            except psycopg2.Error as e:

                # エラー発生時にロールバック
                self.conn.rollback()
                raise e
                return None
            
        self.conn.commit()
        if cur:
            cur.close() 
            return True
        

    #Kyaw 07/23 #Get RList resized column
    def get_resized_column(self,df):
        connection = self.conn
        # Assuming df_selects has only one row
        row = df.iloc[0]
        resize_column_query = """
            SELECT *
            FROM column_resized_tbl
            WHERE project_info_id = %s
            AND phase_id = %s
            AND variation_id = %s
            AND employee_number = %s
            AND category = %s
            AND status = %s
        """

        resize_column_params = (
            int(row['project_id']),
            int(row['phase_id']),
            int(row['variation_id']),
            st.session_state.username,
            'R',
            'Personalモード'
        )

        resize_column_result = pd.read_sql_query(resize_column_query, connection, params=resize_column_params)
        print('resized column r:', resize_column_result)

        st.session_state.resize_column_result = resize_column_result

    #Kyaw 07/23 insert/Update the resized column of Rlist
    def insert_edit_column(self, project_info_id, phase_id, variation_id, employee_number, col_ids, widths, hides, toggle_on):
            print(f'col_ids: {col_ids} and widths: {widths}')
            cur = None
            try:
                cur = self.conn.cursor()

                category = 'R'
                status = 'Personalモード' if toggle_on else 'Defaultモード'
                print(f'status: {status}')

                #Special case: no col_ids and toggle is OFF → update all rows to Defaultモード
                if not col_ids and not toggle_on:
                    print('is that workkk')
                    update_all_query = sql.SQL("""
                        UPDATE column_resized_tbl
                        SET status = 'Defaultモード', is_hide = NULL
                        WHERE project_info_id = %s
                        AND phase_id = %s
                        AND variation_id = %s
                        AND employee_number = %s
                    """)
                    cur.execute(update_all_query, (int(project_info_id), int(phase_id), int(variation_id), str(employee_number)))
                    self.conn.commit()
                    return True

                if col_ids:
                    #Upsert current columns
                    upsert_query = sql.SQL("""
                        INSERT INTO column_resized_tbl (
                            project_info_id, phase_id, variation_id, employee_number, edit_column, column_width, category, status, is_hide
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (project_info_id, phase_id, variation_id, employee_number, edit_column)
                        DO UPDATE SET column_width = EXCLUDED.column_width, category = EXCLUDED.category, status = EXCLUDED.status, is_hide = EXCLUDED.is_hide
                    """)

                    data = [
                        (
                            int(project_info_id),
                            int(phase_id),
                            int(variation_id),
                            employee_number,
                            col_id,
                            int(width),
                            category,
                            status,
                            hides
                        )
                        for col_id, width,hides in zip(col_ids, widths,hides)
                    ]

                    cur.executemany(upsert_query, data)

                    # 2. Update rows not in col_ids → set status = 'Defaultモード'
                    if col_ids:
                        update_status_query = sql.SQL("""
                            UPDATE column_resized_tbl
                            SET status = 'Defaultモード',is_hide = NULL
                            WHERE project_info_id = %s
                            AND phase_id = %s
                            AND variation_id = %s
                            AND employee_number = %s
                            AND edit_column NOT IN ({})
                        """).format(
                            sql.SQL(',').join(sql.Placeholder() * len(col_ids))
                        )

                        update_params = [
                            int(project_info_id),
                            int(phase_id),
                            int(variation_id),
                            str(employee_number),
                            *[str(col) for col in col_ids]
                        ]

                        cur.execute(update_status_query, update_params)

                self.conn.commit()
                return True

            except psycopg2.Error as e:
                if self.conn:
                    self.conn.rollback()
                print(f"Database error: {e}")
                raise e

            finally:
                if cur:
                    cur.close()