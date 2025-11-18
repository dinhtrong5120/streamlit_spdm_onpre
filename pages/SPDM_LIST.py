import pandas as pd
import streamlit as st
import const.constpara as co
import extra_streamlit_components as stx
from st_aggrid import AgGrid
import datetime
import json
from Aras_connect.Middle import IFtoARAS
import module.dialog as dia
#import module.get_data as gd
import module.grid_option as gop
from module.PsqlModule import psql_class
from module.utils import init_session_state
from config.config import RFLGridConfig
import streamlit.components.v1 as components
import module.Jcurb as Jcurb
import os 


sql = psql_class()

now = datetime.datetime.now()
 # アウトプットCSVのパスを指定

# CSSファイルの内容を読み込む
with open(co.css, encoding='utf-8') as f:
    css = f.read()

with open(co.css_ag, encoding='utf-8') as f:
    css_ag = json.load(f)

# CSSをStreamlitに適用
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

###################################################
############## メイン処理 ##########################
###################################################

########## ログイン処理 ##########

if 'username' not in st.session_state or 'password' not in st.session_state:
    st.switch_page("app.py")
else:
    username = st.session_state.username
    password = st.session_state.password

#aras = IFtoARAS(username, password, co.ARASURL, co.ARASDB)

########## プロジェクト・ロット取得 ############

if 'dialog_state' not in st.session_state:
    st.session_state['dialog_state'] = False

if 'update_flg' not in st.session_state:
    st.session_state.update_flg = False

#MAPボタンを押した後、リロード処理を行う    #チョー　10/31
if 'map_click' not in st.session_state:
    st.session_state.map_click = False

if 'chosen_id' not in st.session_state:
    st.session_state.chosen_id=1  #ここどうしようか、、、山口 12/3
else:
    st.session_state.chosen_id = st.session_state.chosen_id

#チョー 02/26
if 'rerun_rfl' not in st.session_state:
    st.session_state['rerun_rfl'] = False
#チョー 04/03
if 'summary_rlist_flag' not in st.session_state:
    st.session_state.summary_rlist_flag = False

#チョー #関数追加 #10/2
#MAPリンクを取得するため、選択されたプロジェクトに応じてプロジェクトを変更する
def get_map_link(project_name):
    return project_name.replace(' ', '_').replace('[', '').replace(']', '').replace('-', '_') + '_MAP'

#タブメニュー表示・処理    #チョー　10/31
def title_tab_bar():
    _chosen_id=st.session_state.chosen_id
    chosen_id  = stx.tab_bar(data=[
        stx.TabBarItemData(id=1, title="諸元リスト(SEリスト)", description=None),
        stx.TabBarItemData(id=2, title="要求リスト(Rリスト)", description=None),
        stx.TabBarItemData(id=3, title="SIM管理表", description=None),
         # Telema RFL用タブ作成 2025/01/28
        stx.TabBarItemData(id=4, title="RFL", description=None),
        stx.TabBarItemData(id=5, title="仮_計算用", description=None),

        ],default=st.session_state.chosen_id)
    st.session_state.chosen_id = chosen_id
    if _chosen_id!=chosen_id:#山口 タブバー押してもすぐ画面更新されないため強制リロードをかける12/3
        st.rerun()

# #編集ボタン処理・処理    #チョー　10/31
# def update_button():
#     update_btn = st.button("変更")
#     if update_btn and 'se_data_stuck' in st.session_state and int(st.session_state['chosen_id']) == 1:
#         # df_org = pd.DataFrame(st.session_state.para_list)
#         df_mold_org = pd.DataFrame(st.session_state.se_data_stuck)    #Aras情報
#         df_mold = pd.DataFrame(st.session_state.aggrid)
#         #result = sql.db_update(df_mold_org, df_mold, now, username)
#         result = sql.db_update_selected(df_mold, now,username)#selected列による編集に切り替え　山口　10/25
#         if result is None or result.empty: 
#             dia.data_none()#, background_color="#F9D46D")
#         else:
#             st.session_state.updata_conf_dia_result = result
#             #st.session_state.updata_conf_dia_result#山口てばっく
#             dia.updata_conf_dia()#, background_color="#F9D46D")
#     elif update_btn and 'sim_data_stuck' in st.session_state and int(st.session_state['chosen_id']) == 3:
#         df_mold = pd.DataFrame(st.session_state.aggrid)
#         #st.dataframe(df_mold)
#         result = sql.db_update_selected(df_mold,now,username)
#         #st.dataframe(result)
#         if result is None or result.empty:
#             st.dataframe(result)
#             dia.data_none()
#         else:
#             st.session_state.updata_conf_dia_result = result
#             dia.updata_conf_dia_sim()
#     elif update_btn and not 'se_data_stuck' in st.session_state:
#         dia.AGdata_none()

#02/07 チョー　変更ダイアログでチェックボックス無しで表示するようの処理
def update_reload_fun(df_mold,chk_column_name):
    # Find the column name that contains 'selected' (this works even if it contains dynamic characters)
    selected_column = [col for col in df_mold.columns if chk_column_name in col.lower()]
    # print('selected_column: ', selected_column)
    if selected_column:
        #チョー 02/03編集
        selected_rows = pd.DataFrame()
        result = pd.DataFrame()
        # Loop through each column to accumulate selected rows
        for key, selected_column_name in enumerate(selected_column):
            # Filter the rows where the current column is True
            current_selected_rows = df_mold[df_mold[selected_column_name] == True]
            # If there are any selected rows, append them to selected_rows
            if not current_selected_rows.empty:
                selected_rows = pd.concat([selected_rows, current_selected_rows], ignore_index=True)

        # Check for unhashable types and convert them to string (if needed)
        # If some columns contain lists or other unhashable types, convert them to strings
        selected_rows = selected_rows.applymap(lambda x: str(x) if isinstance(x, list) else x)

        # Remove duplicates from selected_rows to ensure no repeated rows
        selected_rows = selected_rows.drop_duplicates()

        # Call the database update function with all the selected rows accumulated
        if not selected_rows.empty:  # Ensure selected_rows isn't empty
            result = sql.db_update_selected(selected_rows, now, username)

        return result

#r_summaryをUpdateする処理    チョー　04/24    
def r_summary_update():
    # Reset index to ensure row alignment
    original_df = pd.DataFrame(st.session_state.summary_rlist).reset_index(drop=True)
    edited_df = pd.DataFrame(st.session_state.aggrid).reset_index(drop=True)
    # Get a boolean Series where any value in the row differs
    rows_changed_mask = ~original_df.fillna('').eq(edited_df.fillna('')).all(axis=1)
    # Use the mask to get the full changed rows from edited_df
    changed_rows = edited_df[rows_changed_mask]

    # Display or use the changed data as needed
    if not changed_rows.empty:
        dia.update_r_summary(changed_rows)
    else:
        dia.data_no_change()

#変更変更ボタン処理    #チョー　01/16
def update_button():
    update_btn = st.button("変更")
    if update_btn and 'se_data_stuck' in st.session_state and int(st.session_state['chosen_id']) == 1:

        df_mold = pd.DataFrame(st.session_state.aggrid)
        # # Find the column name that contains 'selected' (this works even if it contains dynamic characters)
        # selected_column = [col for col in df_mold.columns if 'selected' in col.lower()]
        # # print('selected_column: ', selected_column)
        # if selected_column:
        #     # # Extract the actual column name (assuming there is only one match)
        #     # selected_column_name = selected_column[0]
        #     # # Filter the rows where the dynamically named 'selected' column is True
        #     # selected_rows = df_mold[df_mold[selected_column_name] == True]
        #     # # Call the database update function with the selected rows
        #     # result = sql.db_update_selected(selected_rows, now, username)

        #     #チョー 02/03編集
        #     selected_rows = pd.DataFrame()
        #     result = pd.DataFrame()
        #     # Loop through each column to accumulate selected rows
        #     for key, selected_column_name in enumerate(selected_column):
        #         # Filter the rows where the current column is True
        #         current_selected_rows = df_mold[df_mold[selected_column_name] == True]
        #         # If there are any selected rows, append them to selected_rows
        #         if not current_selected_rows.empty:
        #             selected_rows = pd.concat([selected_rows, current_selected_rows], ignore_index=True)

        #     # Check for unhashable types and convert them to string (if needed)
        #     # If some columns contain lists or other unhashable types, convert them to strings
        #     selected_rows = selected_rows.applymap(lambda x: str(x) if isinstance(x, list) else x)

        #     # Remove duplicates from selected_rows to ensure no repeated rows
        #     selected_rows = selected_rows.drop_duplicates()

        #     # Call the database update function with all the selected rows accumulated
        #     if not selected_rows.empty:  # Ensure selected_rows isn't empty
        #         result = sql.db_update_selected(selected_rows, now, username)
            
        #     if result is None or result.empty: 
        #         dia.data_none()
        #     else:
        #         st.session_state.updata_conf_dia_result = result
        #         dia.updata_conf_dia()
        # else:
        #     st.error("No column with 'selected' found in the DataFrame.")

        #02/07 チョー　関数分ける、呼び出す
        se_update_info = update_reload_fun(df_mold,'select')
        if se_update_info is None or se_update_info.empty: 
            dia.data_none()
        else:
            st.session_state.updata_conf_dia_result = se_update_info
            dia.updata_conf_dia()
    
    elif update_btn and 'rlist_data_stuck' in st.session_state and int(st.session_state['chosen_id']) == 2: #山口 Rリストに対しての機能追加 1/29 
        #r_summaryのUpdateする処理を行う　チョー　04/24  
        if st.session_state.summary_rlist_flag is True:
            r_summary_update()
        else:
            df_mold = pd.DataFrame(st.session_state.aggrid)
            # result = sql.db_update_selected(df_mold,now,username)
            # if result is None or result.empty: 
            #     dia.data_none()
            # else:
            #     st.session_state.updata_conf_dia_result = result
            #     dia.updata_conf_dia_rlist()

            #02/07 チョー　ダイアログでチェックボックス無しで変更する
            r_update_info = update_reload_fun(df_mold,'target_selected')
            if r_update_info is None or r_update_info.empty: 
                dia.data_none()
            else:
                st.session_state.updata_conf_dia_result = r_update_info
                dia.updata_conf_dia_rlist()
    
    elif update_btn and 'sim_data_stuck' in st.session_state and int(st.session_state['chosen_id']) == 3:
        df_mold = pd.DataFrame(st.session_state.aggrid)
        # st.dataframe(df_mold)
        result = sql.db_update_selected(df_mold,now,username)
        # st.dataframe(result)
        if result is None or result.empty:
            # st.dataframe(result)
            dia.data_none()
        else:
            st.session_state.updata_conf_dia_result = result
            dia.updata_conf_dia_sim()
    elif update_btn and not 'se_data_stuck' in st.session_state:
        dia.AGdata_none()

#リロードボタン表示    #チョー　10/31
def reload_button():
    #複数プロジェクトを選択してMAPボタンを押下後、ダイアログでの確認ボタンを押してリロード処理を行う
    if st.session_state.map_click is True:
        reload_info()
    #リロードボタンを押下後、リロード処理を行う    
    elif st.button("リロード"):
        reload_info()
 
#リロードボタン処理    #チョー　10/31山口　simページ追加により条件分岐追加 12/9
def reload_info():
    st.session_state.map_click = False
    # 条件を選択された前、リロードボタンを押した場合
    if 'se_data_stuck' not in st.session_state or st.session_state.dialog_state:
        st.switch_page("pages/SPDM_LIST.py") # SEリストページへ移動する
    elif int(st.session_state.chosen_id)==1 and 'se_data_stuck' in st.session_state:
        # 更新された情報を取得する
        df1,df2 = sql.posgre_get_date(st.session_state['selectoption1'],
                                        st.session_state['selectoption2'],
                                        st.session_state['selectoption3'],
                                        st.session_state['selectoption4'],
                                        st.session_state['selectoption5'])
        st.session_state.prj_info_list = df1
        st.session_state.se_data_stuck = df2
        st.rerun()    #SEリストページをリロードする
    elif int(st.session_state.chosen_id)==3 and 'sim_data_stuck' in st.session_state:
        print('sim_update')
        # df1,df2=sql.posgre_get_data_sim(st.session_state['selectoption1'],st.session_state['selectoption4'],st.session_state['selectoption5'], st.session_state['selectoption6'])
        df1,df2=sql.posgre_get_data_sim(st.session_state['selectoption1'],
                            st.session_state['selectoption2'],
                            st.session_state['selectoption3'],
                            st.session_state['selectoption4'],
                            st.session_state['selectoption5']) #チョー 03/10 #山口　引数が古かったので1-5を渡すように設定
        st.session_state.sim_prj_info_list = df1
        st.session_state.sim_data_stuck = df2
    else:
        st.error('unexpected reload')

#条件ボタン表示・処理    #チョー　10/31
def condition_button():
    if st.button("PRJ選択") :#or st.session_state.dialog_state:
        # if int(st.session_state['chosen_id'])  == 1:
        #     #dia.choice_se()
        #     dia.choice_se_bookmark()#山口　ブックマーク機能付きダイアログ 11/5
        # if int(st.session_state['chosen_id'])  == 2:
        #     dia.choice_r_list()  #チョー　#01/08　Rリスト処理追加
        # if int(st.session_state['chosen_id'])  == 3:
        #     dia.choice_sim()  
        # if int(st.session_state['chosen_id'])  == 4:
        #     dia.choice_rfl()
        
        #チョー　共通ダイアログを使う 03/10
        if int(st.session_state['chosen_id'])  == 1 or int(st.session_state['chosen_id'])  == 5:
            dia.choice_se_bookmark('se_list')
        if int(st.session_state['chosen_id'])  == 2:
            dia.choice_se_bookmark('r_list')
        if int(st.session_state['chosen_id'])  == 3:
            dia.choice_se_bookmark('sim_list') 
        if int(st.session_state['chosen_id'])  == 4:
            dia.choice_se_bookmark('rfl_list')

#ログインボタン表示・処理    #チョー　10/31
def login_button():
    if st.button("Logout"):
        st.switch_page("app.py")    

#MAPボタン表示・処理    #チョー　10/31
def map_button():
    '''
    SEリスト、Sim管理表でMAPボタンが押されたときに動かす関数
    チェックマークがついたセルの値抽出
    値でマップ検索
    DB上にマップが見つかればmapgrid_by_name
    見つからなければmapgrid
    '''

    #山口　マップをグリッド表示するためのやつ `11/13
    if st.button("MAP"):           

        
        if "se_data_stuck" in st.session_state and int(st.session_state.chosen_id)==1 :#山口　chosen_idを条件に追加12/5
            df_mold = pd.DataFrame(st.session_state.aggrid)
            result = sql.db_update_selected(df_mold, now,username)#選択した項目入手
            
            if len(result)==1:#この機能は複数選択で動かすわけにいかない
                map_name = result['z_request_median'].tolist()[0]
                df_map_variables = sql.get_map_variables_by_name(map_name)
                
                project_id=result['project_id'].tolist()[0]
                phase_id=result['phase_id'].tolist()[0]
                parameter_id=result['se_parameter_id'].tolist()[0]
                variation_id=result['variation_id'].tolist()[0]
                URL = result['URL'].tolist()[0]
                df_map_variables2 = sql.get_map_variables(project_id, parameter_id, phase_id, variation_id)
                if df_map_variables is not None:#やりたいのは名前一致するものがなければ新規作成、だけどSEリストはまだデータ移行ができていないため、ない場合は従来のマップグリッドを使用する TODO
                    dia.mapgrid_by_name(result) 
                elif URL is not None or len(df_map_variables2)>1:
                    dia.mapgrid(result)#TODO こいつ実行前に判定機能つけれない？そうすればこっちで該当マップなければNAMEでつけることができるかららくちんちんになる
                else:
                    st.write('completely new map')
                    dia.mapgrid_by_name(result)
            else:
                    st.error("MAP表示は1項目選択時のみしか機能しません！！")
        elif "sim_data_stuck" in st.session_state and int(st.session_state.chosen_id)==3 :#山口　simMap用の追加 12/5
            df_mold = pd.DataFrame(st.session_state.aggrid)
            result = sql.db_update_selected(df_mold, now,username)#選択した項目入手
            
            if len(result)==1:#この機能は複数選択で動かすわけにいかない
                map_name = result['value'].tolist()[0]
                dia.mapgrid_by_name(result) #名前参照用に変更する
            else:
                st.error("MAP表示は1項目選択時のみしか機能しません！！")
        else:
            st.error("unexpected map func execution")

#山口　時系列表示機能用ボタン 1/29
def timeseries_button():
    if st.button('時系列表示'):
        if 'rlist_data_stuck' in st.session_state and int(st.session_state.chosen_id)==2 :
            df_mold = pd.DataFrame(st.session_state.aggrid)
            result = df_mold[df_mold['timeseries_selected']]#選択した項目入手
            
            if len(result)==1:#この機能は複数選択で動かすわけにいかない
                dia.timeseriesgrid(result)
            else:                                     
                st.write(result)
                st.error("MAP表示は1項目選択時のみしか機能しません！！")


#比較ボタン表示・処理    #チョー　11/25
def compare_button():
    if st.session_state['compare_click'] is False:
        if st.button("設計値比較"):
            dia.compare_se()
    else:
        if st.button("戻る"):
            st.session_state['compare_click'] = False
            st.rerun()


#Kyaw 10/16 PRJ新規作成 button
def create_new_button():
    if st.button('PRJ新規作成'):
        if int(st.session_state['chosen_id']) == 1:
            dia.create_new_se_prj()
        if int(st.session_state['chosen_id']) == 2:
            dia.create_new_r_and_rfl_prj()

def create_button():#山口　チョーさんのものにchosen_id分岐を追加 12/5
    if int(st.session_state.chosen_id)==1:
        if 'next_click' not in st.session_state:
            st.session_state['next_click'] = False
        if 'create_click' not in st.session_state:
            st.session_state['create_click'] = False
        if st.button("新規作成"):
            dia.create_project1()
        if st.session_state.next_click is True:
            st.session_state['next_click'] = False
            dia.create_project2()
        if st.session_state.create_click is True:
            st.session_state['create_click'] = False
            dia.create_success_dia()
    elif int(st.session_state.chosen_id)==3:
        if st.button("新規"):
            dia.create_new_study()

def sim_button():#山口　simボタン 12/6
    if st.button('sim実行'):
        if 'sim_data_stuck' in st.session_state:
           dia.sim()


def dashboard_button():#山口　simボタン 12/6
    if st.button('結果'):
        if 'sim_data_stuck' in st.session_state:
           dia.to_dashboard()

def send_to_RFL_button():
    if st.button('RFL転記'):
        if 'sim_data_stuck' in st.session_state:
            dia.send_to_RFL()

#02/10 チョー　確定ボタン処理
def fixed_button():
    if st.button('確定'):
        if 'sim_data_stuck' in st.session_state and 'sim_prj_info_list' in st.session_state:
            dia.choice_sim_fixed()

#02/10 チョー　有効ステータスのリストがある場合
if 'fix_sim_study_list' in st.session_state and st.session_state.fix_sim_study_list is True:
    if 'fixed_sim_info' in st.session_state:
        dia.fixed_dia_sim()
        st.session_state.fix_sim_study_list = False

# Ha-san added 0214:
def get_session_choices(choice_number):
    searching_input_keys = ['architecture_name']
    searching_input_values = []
    is_enough_input = True

    for selection_id in range(1, choice_number + 1):
        selection_name = f"selectoption{selection_id}"
        searching_input_keys.append(selection_name)

    for key in searching_input_keys:
        if key in st.session_state:
            # st.write(f" {key}: {st.session_state[key]}")
            searching_input_values.append(st.session_state[key])
        else:
            is_enough_input = False

    return searching_input_values, is_enough_input
# ==========


#チョー 03/25 #Rリスト以外のタブに移動されると、rlist_previous_selectedセッションを削除する　
if int(st.session_state['chosen_id'])  != 2 :
    # 05/07
    for key in ['rlist_previous_selected', 'dt_previous_selected','r_sum_reload_flag']:
        if key in st.session_state:
            del st.session_state[key]

#チョー　05/07 
if int(st.session_state['chosen_id']) == 2:
    keys_to_delete = ['dt_previous_selected', 'r_sum_reload_flag', 'summary_rlist']
    for key in keys_to_delete:
        if key in st.session_state and not st.session_state.summary_rlist_flag:
            del st.session_state[key]

def r_list_selected():
    options = st.session_state.total_selected_rlist
    selected_option = st.selectbox('選択', options, label_visibility = 'collapsed')
    #チョー 03/25 # Rリストの初期表示にセッション情報に設定する
    if 'rlist_previous_selected' not in st.session_state:
        st.session_state.rlist_previous_selected = options[0]
    
    if selected_option != '選択してください。':
        # print('rlist_previous_selected:',st.session_state.rlist_previous_selected)
        # print('selected:',selected_option)
        # st.session_state.rlist_display_flag = True
        if 'selectoption6' not in st.session_state or st.session_state.rlist_previous_selected != selected_option: #以前選択する値と現在選択する値が違うとDB処理を行う　 #チョー 03/25
            st.session_state.rlist_previous_selected = selected_option #チョー 03/25 #選択された情報をセッションに設定する

            # Split the selected option by ';' and remove any leading or trailing whitespace
            split_values = [value.strip() for value in selected_option.split(';')]
            # Ensure there are at least 6 elements in the split list before calling the function
            if len(split_values) >= 6:
                # Assuming the first 6 elements in split_values as arguments for the function
                project_code = split_values[0]
                destination = split_values[1]
                drivetrain = split_values[2]
                lot = split_values[3]
                phase = split_values[4]
                variation = split_values[5]

                df1,df2 = sql.posgre_get_rlist([project_code],[destination], [drivetrain], [lot], [phase], [variation])
                st.session_state.r_prj_info_list = df1
                st.session_state.rlist_data_stuck = df2
            # st.rerun()   
        else:
            df1 = st.session_state.r_prj_info_list
            df2 = st.session_state.rlist_data_stuck


#05/07　WD　Dropdown選択
def dt_list_selected():

    dt_list = st.session_state.total_drivetrain_selected
    dt_selected_option = st.selectbox('選択', dt_list, label_visibility = 'collapsed')
    if 'dt_previous_selected' not in st.session_state: #初期表示の場合
        st.session_state.dt_previous_selected = dt_list[0]
        st.session_state.dt_selected_option = dt_list[1]

    if dt_selected_option != '選択してください。':
        # print('prev: ', st.session_state.dt_previous_selected)
        # print('now: ', dt_selected_option)
        if st.session_state.dt_previous_selected != dt_selected_option:
            st.session_state.dt_previous_selected = dt_selected_option
            st.session_state.dt_selected_option = dt_selected_option
            st.session_state.r_sum_reload_flag = True
        else:
            st.session_state.r_sum_reload_flag = False

#「ステートメント記入」ボタン表示　＃チョー　04/16
def r_statement_button():
    if st.button('ステートメント記入'):
        dia.insert_r_statement()

#Kyaw 07/22 モード保存機能追加 #10/29 merge#5
def edit_column_width_button():
    if st.button('モード保存'):
        dia.confirm_resized_column_width()  

#チョー 03/10
if st.session_state.button_edit_state and not st.session_state.login_begin:
    if int(st.session_state['chosen_id']) == 1 and "prj_info_list" in st.session_state: #プロジェクトが選択された場合　＃チョー　10/31 山口　選ばれた帳票でボタンを変更するように条件追加 11/30    
        
        if 'compare_click' not in st.session_state:
            st.session_state['compare_click'] = False
        # col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([10,1,1,1,1,1,1,1])
        # with col1:
        #     title_tab_bar()     #タブメニュー表示関数を呼び出す  
        # with col2:
        #     create_button()   
        # with col3:
        #     condition_button()  #条件ボタン表示関数を呼び出す
        # with col4:
        #     compare_button()    #比較ボタン表示関数を呼び出す #11/25
        # with col5:
        #     update_button()     #編集ボタン表示関数を呼び出す
        # with col6:
        #     reload_button()     #リロードボタン示関数を呼び出す
        # with col7:
        #     map_button()        #MAPボタン表示関数を呼び出す
        # with col8:
        #     login_button()      #ログインボタン表示関数を呼び出す

        col1, col2, col3, col4, col5, col6 = st.columns([10,1.5,1.5,1,1,1.5])
        with col1:
            title_tab_bar()     #タブメニュー表示関数を呼び出す  
        with col2:
            condition_button()  #条件ボタン表示関数を呼び出す
        with col3:
            create_new_button()    #PRJ新規作成ボタンの関数を呼び出す #11/25
        with col4:
            update_button()     #編集ボタン表示関数を呼び出す        
        with col5:
            map_button()        #MAP示関数を呼び出す
        with col6:
            compare_button()    #比較ボタン表示関数を呼び出す #11/25

    elif int(st.session_state['chosen_id']) == 2 and "r_prj_info_list" in st.session_state:# 山口 Rリスト用表示ボタン 1/29

        col_def = [9,1.2,1.2,5,1,1.3,1.6] #チョー 04/24 #10/29 merge#5
        if st.session_state.summary_rlist_flag is True:
            col_def = [9,1,2,1,0.001,0.001,0.001] #チョー 選択リストなしで表示する 04/24 #10/29 merge#5
        col1, col2, col3, col4,col5,col6,col7 = st.columns(col_def)
        with col1:
            title_tab_bar()     #タブメニュー表示関数を呼び出す
        with col2:
            condition_button()      #条件ボタン表示関数を呼び出す 
        if st.session_state.summary_rlist_flag is False:
            with col3:
                create_new_button()    #新規作成ボタンの関数を呼び出す 
            with col4:
                r_list_selected() #チョー 追加　03/10
            with col5:
                update_button()     #編集ボタン表示関数を呼び出す
            with col6:
                timeseries_button()     #時系列ボタン
            with col7:
                edit_column_width_button() #Kyaw 07/23
        else:
            with col3:
                dt_list_selected() #チョー 追加　05/07
            with col4:
                update_button()     #編集ボタン表示関数を呼び出す
        
        # one for the left space, one for the right-aligned widget　＃チョー 04/03 サマリーモードを追加する
        col1, col2,col3,col4 = st.columns([8,1,1.5,1.5])
        with col4:
            on = st.toggle("サマリーモード", key="summary_rlist_flag")
        if st.session_state.summary_rlist_flag: #チョー　04/16
            with col3:
                r_statement_button() 

    elif int(st.session_state['chosen_id']) == 3 and "sim_prj_info_list" in st.session_state:# 山口　sim実行用ボタン追加　12/6
        col1, col2, col3, col4, col5, col6, col7, col8, col9, col10 = st.columns([7,1,1,1,1,1,1,1,1,1])#山口　列増やした12/5 また列増やした1/29 またまた列増やした2/6
        with col1:
            title_tab_bar()     #タブメニュー表示関数を呼び出す  
        with col2:
            condition_button()  #条件ボタン表示関数を呼び出す
        with col3:
            update_button()     #編集ボタン表示関数を呼び出す
        with col4:
            map_button()        #MAPボタン表示関数を呼び出す
        with col5:
            create_button()     #山口　新規Sim作成ボタン 12/5
        with col6:
            sim_button()
        with col7:
            dashboard_button() # 山口　ダッシュボード表示ボタン12/18
        with col8:
           send_to_RFL_button() #山口　RFL転記用ボタン2/6
        # with col9:
        #     pass #山口　シナリオのR比較するためreserve
        with col9:
            fixed_button() #02/10 チョー　確定ボタン処理を呼び出す
        with col10:
            reload_button()
    else:
        col1, col2, col3 = st.columns([10,1,1.5])
        with col1:
            title_tab_bar()     #タブメニュー表示関数を呼び出す
        # with col:
        #     condition_button()  #条件ボタン表示関数を呼び出す
        with col3:
            condition_button()      #条件ボタン表示関数を呼び出す
else: #チョー 追加 03/10
    col1, col2, col3, col4, col5 = st.columns([10,1,1,1,1])
    # with col1:
    #     # st.write('Nissan SPDX')     #タブメニュー表示関数を呼び出す  
    #     # st.write('Systems engineering for Powertrain Data Transformer') 
    #     st.markdown(
    #         """
    #         <h1 style="padding: 0px;">Nissan SPDX</h1>
    #         <h4 style="padding: 0px;">Systems engineering for Powertrain Data Transformer</h4></br>
    #         """,
    #         unsafe_allow_html=True
    #     )
    with col3:
        condition_button()
    with col4:
        st.button('About')       
    with col5:
        st.button('Contact') 

#チョー　01/16　変更完了後のメッセージ表示
def updated_success_msg():
    st.info('正常に変更が完了しました。')
    st.session_state.updated_msg = False

#チョー　01/16　リロード
def reload_updated():
    if int(st.session_state.chosen_id)==1 and 'se_data_stuck' in st.session_state:
        # 更新された情報を取得する
        df1,df2 = sql.posgre_get_date(st.session_state['selectoption1'],
                                        st.session_state['selectoption2'],
                                        st.session_state['selectoption3'],
                                        st.session_state['selectoption4'],
                                        st.session_state['selectoption5'])
        st.session_state.prj_info_list = df1
        st.session_state.se_data_stuck = df2
        # st.session_state.updated_selist = False
        st.session_state.updated_msg = True
        st.rerun()
        # dia.success_dia() 
     #02/07 チョー　Rリスト変更した後、リロード処理
    elif int(st.session_state.chosen_id)==2 and 'rlist_data_stuck' in st.session_state:
        
        #チョー03/10
        df1,df2=sql.posgre_get_rlist(st.session_state['selectoption1'],
                            st.session_state['selectoption2'],
                            st.session_state['selectoption3'],
                            st.session_state['selectoption4'],
                            st.session_state['selectoption5'])
        st.session_state.r_prj_info_list = df1
        st.session_state.rlist_data_stuck = df2
        st.session_state.updated_msg = True
        st.rerun()
    #02/12 チョー　Study新規追加後のリロード
    elif int(st.session_state.chosen_id)==3 and 'sim_data_stuck' in st.session_state:
        print('sim_update')
        #チョー03/10
        df1,df2=sql.posgre_get_data_sim(st.session_state['selectoption1'],
                            st.session_state['selectoption2'],
                            st.session_state['selectoption3'],
                            st.session_state['selectoption4'],
                            st.session_state['selectoption5'])
        st.session_state.sim_prj_info_list = df1
        st.session_state.sim_data_stuck = df2
        st.session_state.create_new_sim = False
        st.rerun()

    # elif int(st.session_state.chosen_id)==4 and 'sim_data_stuck' in st.session_state:
    #     print('sim_update')
    #     df1,df2=sql.posgre_get_data_sim(st.session_state['selectoption1'],st.session_state['selectoption4'],st.session_state['selectoption5'], st.session_state['selectoption6'])
    #     st.session_state.sim_prj_info_list = df1
    #     st.session_state.sim_data_stuck = df2

if 'create_new_sim' in st.session_state:
        if st.session_state.create_new_sim is True:
            # st.session_state.create_new_sim = False
            # reload_info_update()
            reload_updated()

#チョー　01/16
if 'updated_msg' in st.session_state and st.session_state.updated_msg is True:
    updated_success_msg()

#チョー　05/07
if 'r_sum_reload_flag' not in st.session_state:
    st.session_state.r_sum_reload_flag = True
    
#チョー　05/07
if 'summary_rlist' not in st.session_state:
    st.session_state.summary_rlist = None

#チョー 04/03 #rリストのサマリーGrid表示
def display_r_summary():

    #チョー　05/07
    if st.session_state.r_sum_reload_flag:
        r_df1,r_df2 = sql.get_r_summary()
        # st.write('db df1: ', r_df1)
        # st.write('db df2: ', r_df2)

        if not r_df1.empty: #10/29 merge#5
            #ｒステートメントを取得する　＃チョー　04/16
            r_statement_df = sql.get_r_statement(list(set(r_df1['project_id'])),list(set(r_df1['phase_id'])),'R')
            # r_statement_df = sql.get_r_statement(list(set(df1['project_id'])),list(set(df1['phase_id'])),'R')
            st.session_state.r_statement_df = r_statement_df

        #10/20 when all judge columns are blank, return False
        if r_df2.empty: #10/29 merge#5
            st.session_state.summary_rlist = pd.DataFrame()

            # st.session_state.summary_rlist = None
            # st.session_state.r_sum_reload_flag = False
            return

        # List of fixed parts of the column names
        get_column_from_rlist = [
            'r_parameter_id',
            'project_id',
            'phase_id',
            'variation_id',
            'wp_id',
            'performance', 
            'judge', 
            'manager_approval', 
            'manager_approval_comment',
            'summary_index' #山口　サマリーでの順番を指定するため 5/8
        ]

        df_selects = st.session_state.df_selects

        # Select the corresponding columns from r_df `山口　ドロップダウンで変更してもステートメントが変わらないため、先に＠ｄｆ１準備してget_r_statementもdf1から取得するように変更した5/8
        df1 = r_df2[get_column_from_rlist]

        # #ｒステートメントを取得する　＃チョー　04/16
        # r_statement_df = sql.get_r_statement(list(set(df1['project_id'])),list(set(df1['phase_id'])),'R')
        # st.session_state.r_statement_df = r_statement_df

        r_parameter_id_column = f'r_parameter_id'
        judge_column = f'judge'
        performance_column = f'performance'
        wp_id_column = f'wp_id'

        # Remove rows where the specific judge column is NaN or None or ''
        df1 = df1[df1[judge_column].notna() & (df1[judge_column] != '')] #04/08

        if not df1.empty:

            selected_rows = []

            # Drop rows where either column is NaN to avoid errors
            df1 = df1.dropna(subset=[performance_column, judge_column])

            # Group by performance
            def select_row(group):
                # st.write('group: ',group)
                if (group[judge_column] == 'NG').any():
                    return group[group[judge_column] == 'NG'].iloc[0]
                else:
                    # Not NG, check for any value that isn't 'OK'
                    non_ok_rows = group[group[judge_column] != 'OK']
                    if not non_ok_rows.empty:
                        return non_ok_rows.iloc[0]
                    else:
                        # Only OK values
                        return group[group[judge_column] == 'OK'].iloc[0]

            grouped = df1.groupby(performance_column, group_keys=False).apply(select_row)
            grouped = grouped.dropna(how='all')  # in case some groups returned None
            selected_rows.append(grouped)
            
            # Combine all selected rows
            df1 = pd.concat(selected_rows).sort_values(by='summary_index').reset_index(drop=True) #山口 サマリーの並べ替えを実装する 5/8

            df1[f'judge_emoji'] = df1[f'{judge_column}'].apply(
                lambda x: '🟢' if x == 'OK' else '🟠' if x == 'NG' else '🟡' #OK,NG以外は黄色にする #チョー　04/16
            )

            # st.write("df1 before result:", df1)

            df2 = sql.get_wp_statement(list(set(df1['project_id'])),list(set(df1['phase_id'])),df1[wp_id_column].dropna().astype(int),'R')
            #st.write("result_df in wp statement:", df2)
            
            # Perform a left merge on the keys project_id, phase_id, wp_id
            merged_df = df1.merge(
                df2[['project_id', 'phase_id', 'wp_id', 'manager_approval', 'manager_approval_comment']],
                on=['project_id', 'phase_id', 'wp_id'],
                how='left',
                suffixes=('', '_df2')  # This avoids overwriting columns directly
            )

            # Use the df2 values to original value
            merged_df['manager_approval'] = merged_df['manager_approval_df2']
            merged_df['manager_approval_comment'] = merged_df['manager_approval_comment_df2']

            # Drop the extra columns brought by the merge
            merged_df = merged_df.drop(columns=['manager_approval_df2', 'manager_approval_comment_df2'])

            # Now merged_df is your desired result
            result_df = merged_df
            # st.write("result_df df:", result_df)

            st.session_state.summary_rlist = result_df
            st.session_state.r_sum_reload_flag = False #チョー　05/07
        else:
            st.session_state.summary_rlist = None #チョー　05/07

        # # Add a text input for searching
        # # quick_filter_text = st.text_input("フリーワード検索:",key="rsummary_searching")
        # # Render the grid
        # go = gop.create_rlist_summary_grid()
        # # Pass the quick filter text to the grid options
        # # if quick_filter_text:
        # #     go['quickFilterText'] = quick_filter_text
        # def render_aggrid(go):
        #     edit = AgGrid(
        #         st.session_state.summary_rlist,
        #         custom_css=css_ag,
        #         allow_unsafe_jscode=True,
        #         gridOptions=go,
        #         reload_data=False,
        #         theme="alpine",
        #         enable_quicksearch=True,
        #         height=800,
        #         tree_data=True,
        #     )
        #     return edit['data']

        # st.session_state.aggrid = render_aggrid(go)


#Kyaw 07/23 #Check the columns that have resized or not! #10/29 merge#5
def resized_column_width(edit):
    #Get current column state
    column_state = edit.grid_response.get("columnsState")
    # st.write('column state: ',column_state)
    if column_state:
        #Extract current resized info
        current_widths = [
            {"colId": col["colId"], "width": round(col["width"], 2), "hide": col["hide"]}
            for col in column_state if "colId" in col and "width" in col and "hide" in col
        ]
        # st.write("Current column widths:", current_widths)

        #Initialize initial state only once
        if "initial_column_widths" not in st.session_state:
            st.session_state.initial_column_widths = current_widths
        # st.write("Initial widths stored.",st.session_state.initial_column_widths)

        #Compare current with initial
        changed_columns = []
        for current_col in current_widths:
            for initial_col in st.session_state.initial_column_widths:
                if current_col["colId"] == initial_col["colId"]:
                    if abs(current_col["width"] - initial_col["width"]) > 0.1 or current_col["hide"] != initial_col["hide"]:  # ignore tiny diffs
                        changed_columns.append(current_col)
                    break

        #Store changed info and show    
        if changed_columns:
            # st.warning("Changed column widths:")
            # st.json(changed_columns)
            st.session_state.changed_column_widths = changed_columns
        else:
            # st.success("No changes in column widths.")
            st.session_state.changed_column_widths = []      
    else:
        # st.info("Resize some columns to track changes.")
        print('Resize some columns to track changes.')


if 'create_new_prj_success' not in st.session_state:
    st.session_state.create_new_prj_success = False

if st.session_state.create_new_prj_success:
    st.success('プロジェクト新規作成に成功しました。')
    st.session_state.create_new_prj_success = False

#SEリストメニューが選択された場合
if int(st.session_state['chosen_id']) == 1:
    # Ha-san added 0214
    searching_input_selist_values, is_enough_selist_input = get_session_choices(5)
    is_re_render_selist = False
    # ==========
    if 'se_data_stuck' not in st.session_state or st.session_state.dialog_state:
        # Ha-san added 0214
        if is_enough_selist_input:
            try:
                df1_selist, df2_selist = sql.posgre_get_date(*searching_input_selist_values[1:])
                st.session_state.prj_info_list = df1_selist
                st.session_state.se_data_stuck = df2_selist
                st.session_state['compare_click'] = False
                is_re_render_selist = True
            except Exception as e:
                is_re_render_selist = False
                # st.write("error:", e)
        elif not st.session_state.login_begin: #チョー　追加 03/10
            # st.error(f'SEリスト条件から選んでください。')
            st.image(co.inf_img, use_column_width=True)
    else:
        is_re_render_selist = True
        # ==========    
    if is_re_render_selist and not st.session_state.login_begin: #チョー　追加 03/10
   
        # if 'prj_info_list' not in st.session_state:
        #     st.session_state.prj_info_list = []

        # info_df = pd.DataFrame(st.session_state.prj_info)
        # placeholder = st.empty()
        # ###### パラメータの取得 ######
        # index_list = ['z_parent_paraitem', 'z_child_paraitem', 'z_unit']
        # if 'se_data_stuck' not in st.session_state or info_df['z_number'].tolist() != st.session_state.prj_info_list or st.session_state.update_flg == True:
        #     # 表示データ情報がないとき、データを取得
        #     gd.get_data()
        #     st.session_state.update_flg = False

        # if 'se_data_stuck' not in st.session_state:
        #     placeholder.warning('パラメータを取得できませんでした')
        #     st.stop()
        st.session_state.create_click = False
        go = gop.create_gridop()
        # go
        # st.session_state.prj_info_list = info_df['z_number'].tolist()
        # paradf= pd.DataFrame(st.session_state.se_data_stuck)
        # para_key_list = [a for a in paradf.columns if 'z_paravalueid' in a]
        # para_key = para_key_list[0]
        # st.session_state.se_data_stuck["INDEX"]=st.session_state.se_data_stuck.index
        # srs=st.session_state.se_data_stuck[index_list[:2]].\
        #     apply(lambda x: [val for val in x if pd.notnull(val)], axis=1)
        # st.session_state.se_data_stuck["param"]=srs
        # st.session_state.se_data_stuck = st.session_state.se_data_stuck.sort_values(by=para_key)
        # st.session_state.se_data_stuck#　山口　デバック用
        # st.session_state.prj_info_list
  
        if st.session_state['compare_click'] is True:
            st.info("値を変更する場合は「戻る」ボタンを押してください。")
        def render_aggrid(go):
            edit=AgGrid(
                st.session_state.se_data_stuck,
                custom_css=css_ag,
                allow_unsafe_jscode=True,
                gridOptions=go,
                reload_data=False,
                theme="alpine",                                                                             
                enable_quicksearch=True,
                height=800,
                tree_data=True,
            )
            return edit['data']
        st.session_state.aggrid = render_aggrid(go)
        
        #go#山口デバック用
        #st.session_state.prj_info_list
        if "update_chk_conf" in  st.session_state:
            if st.session_state.update_chk_conf is not None:
                # st.session_state.update_chk_conf #デバック用　山口
                print("gonna update")
                sql.update_record(st.session_state.update_chk_conf)
                st.session_state.update_flg = True
                st.session_state.se_data_stuck = st.session_state.aggrid
                del st.session_state['update_chk_conf']
                # dia.success_dia()   
                reload_updated()    #チョー　01/16


#Rリストメニューが選択された場合 #チョー　01/08
if int(st.session_state['chosen_id']) == 2:
    # Ha-san added 0214
    searching_input_rlist_values, is_enough_rlist_input = get_session_choices(5) #チョー 03/10
    is_re_render_rlist = False
    # ==========
    if 'r_prj_info_list' not in st.session_state or st.session_state.r_prj_info_list.empty or st.session_state.dialog_state:
        # Ha-san added 0214
        if is_enough_rlist_input:
            try:
                df1_rlist, df2_rlist = sql.posgre_get_rlist(*searching_input_rlist_values[1:])
                if len(df1_rlist) == 0:
                    st.error('選択されたプロジェクトの要求リストは登録されていません。')
                else:
                    st.session_state.r_prj_info_list = df1_rlist
                    st.session_state.rlist_data_stuck = df2_rlist
                    st.session_state['compare_click'] = False
                    st.session_state['compare_back_click'] = False
                    is_re_render_rlist = True    
                    st.rerun() #チョー 03/10 

            except Exception as e:
                raise e #Rリストのロードが最初の一回目でできない件、Try内でエラーが起きているという仮説もと、raiseさせてみると、特にException表示もなくロードされた、正直意味わからない 5/10 山口
                is_re_render_rlist = False
        elif not st.session_state.login_begin: #チョー 03/10
            st.error(f'PRJを選択してください。')
            st.image(co.inf_img, use_column_width=True)
    else:
        is_re_render_rlist = True
        # ==========
    if is_re_render_rlist and not st.session_state.login_begin and not st.session_state.summary_rlist_flag: #チョー 03/10
        # st.write('THIS IS R LIST')
        # st.session_state.create_click = False

        go = gop.create_gridop_rlist()
        def render_aggrid(go):
            edit=AgGrid(
                st.session_state.rlist_data_stuck,
                custom_css=css_ag,
                allow_unsafe_jscode=True,
                gridOptions=go,
                reload_data=False,
                theme="alpine",
                enable_quicksearch=True,
                height=1000,
                tree_data=True,
                update_mode="GRID_CHANGED" #Kyaw 07/23 To get the resized columns' value when its changed #10/29 merge#5
            )
            resized_column_width(edit) #Kyaw 07/23 Call the function
            return edit['data']
        st.session_state.aggrid = render_aggrid(go)
        # st.write('aggrid session: ', st.session_state.aggrid)
        # if not st.session_state.r_prj_info_list.empty:
        #     # flattened_data = st.session_state.r_prj_info_list.apply(lambda x: ' | '.join(x.astype(str)), axis=1)
        #     # single_line_df = pd.DataFrame(flattened_data, columns=["All Data"])
        #     st.write('df1: ', st.session_state.r_prj_info_list)
        #     st.write('df2: ', st.session_state.rlist_data_stuck)
        #     # st.write("Displaying records in a single line:")
        #     # AgGrid(st.session_state.rlist_data_stuck)
        # else:
        #     st.write("No records found.")

        #st.session_state.prj_info_list
        if "update_chk_conf" in st.session_state:
            #st.write('update_chk_conf session: ', st.session_state.update_chk_conf)
            if st.session_state.update_chk_conf is not None:
                # st.session_state.update_chk_conf #デバック用　
                print("gonna update")
                sql.update_record_rlist(st.session_state.update_chk_conf)
                st.session_state.update_flg = True
                st.session_state.rlist_data_stuck = st.session_state.aggrid
                del st.session_state['update_chk_conf']
                # dia.success_dia()    
                reload_updated() #02/07 チョー　リロード関数を呼び出す  
    elif st.session_state.summary_rlist_flag:
        display_r_summary() 
        #ステートメント表示　＃チョー　04/16
        if not st.session_state.r_statement_df.empty:
            r_statement = st.session_state.r_statement_df.iloc[0]['statement']
            update_day = st.session_state.r_statement_df.iloc[0]['update_day']
            # Replace newline characters with <br> for proper display in Markdown
            statement_with_line_breaks = r_statement.replace('\n', '<br>')
            if statement_with_line_breaks:
                st.markdown(
                    f'<div style="font-size:25px; line-height:1.6;font-weight:bold;text-decoration: underline;">ステートメント（{update_day}時点）</div>',
                    unsafe_allow_html=True
                )
                # Wrap in a styled div to control size
                st.markdown(
                    f'<div style="font-size:25px; line-height:1.6;">{statement_with_line_breaks}</div>',
                    unsafe_allow_html=True
                )
        if 'summary_rlist' in st.session_state and st.session_state.summary_rlist is not None:
            go = gop.create_rlist_summary_grid()

            def render_aggrid(go):
                edit = AgGrid(
                    st.session_state.summary_rlist,
                    custom_css=css_ag,
                    allow_unsafe_jscode=True,
                    gridOptions=go,
                    reload_data=False,
                    theme="alpine",
                    enable_quicksearch=True,
                    height=800,
                    tree_data=True,
                )
                return edit['data']

            st.session_state.aggrid = render_aggrid(go)
        else:
            st.error('判断された情報がありません。')

#sim管理表のページによって表示行を変える関数 
def hide_rows_based_on_pages(df_sim, pages):
    id_col = df_sim.loc[:, df_sim.columns.str.contains(';senario_parameter_id;')].columns.tolist()[0]
    if pages =='初期仕様':
        senario_id_not_to_show = [
            0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 34, 36, 37, 38, 39, 42, 43, 45, 55, 70, 96, 97, 98, 99
        ]
        return df_sim[~df_sim[id_col].isin(senario_id_not_to_show)]

    if pages=='バリエーション表':
        senario_id_to_show = [
            400, 403, 410,
            600,602,
            10001,
            20046,20048,
            20021,20022,20025,
            20070,20026,
            25000,
            110008,110004,110005,
            300000,300001,300002,
            400000,400001,
            401000,401001
            
        ]
        return df_sim[df_sim[id_col].isin(senario_id_to_show)]
    return df_sim 


# def get_runner_status():
#     '''
#     SystemAnalysのステータスを取得する関数
#     '''
#     onedriveDirectory = r"C:\Users\BSN00147\OneDrive - Nissan Motor Corporation\simrequest_variables"
#     status_file_path = os.path.join(onedriveDirectory, 'runner_status.txt')
#     try:
#         with open(status_file_path, 'r') as f:
#             lines = f.readlines()
#
#             status = lines[0].replace('\n', '')
#             if status==str(0):
#                 return 'シミュレーション指示待機中'
#             elif status == str(1):
#                 study_id = lines[1].split(',')[3]
#                 return 'シミュレーション実行中：'+study_id
#             else:
#                 return 'unexpected status'
#
#     except Exception as e:
#         raise e


#SEリスト以外のタブを選択すると何も表示されない。　＃チョー　11/01
# #Rリストメニューが選択された場合
# if int(st.session_state['chosen_id'])  == 2:
#     st.error(f'Rリスト条件から選んでください。')
#     st.image(co.inf_img,use_column_width=True)
# #SIM管理表メニューが選択された場合
 #SIM管理表メニューが選択された場合 山口　機能実装のため有効化
if int(st.session_state['chosen_id'])  == 3 :
    # Ha-san added 0214
    searching_input_sim_values, is_enough_sim_input = get_session_choices(5) #チョー 03/10
    is_re_render_sim = False
    # ==========
    if 'sim_data_stuck' not in st.session_state or st.session_state.dialog_state:
        st.write('no sim_data_stuck in session_state')
        # Ha-san added 0214
        if is_enough_sim_input:
            try:
                df1, df2 = sql.posgre_get_data_sim(*searching_input_sim_values[1:])
                st.session_state.sim_prj_info_list = df1
                st.session_state.sim_data_stuck = df2
                is_re_render_sim = True
                st.rerun() #チョー 03/10
            except Exception as e:
                raise e #Rリストのロードが最初の一回目でできない件、Try内でエラーが起きているという仮説もと、raiseさせてみると、特にException表示もなくロードされた、正直意味わからない 5/10 山口
                is_re_render_sim = False
        elif not st.session_state.login_begin: #チョー 03/10
            st.error(f'PRJを選択してください。')
            st.image(co.inf_img, use_column_width=True)
    else:
        is_re_render_sim = True
        # ==========
    if is_re_render_sim and not st.session_state.login_begin: #チョー 03/10
        #st.session_state.sim_prj_info_list
        if len(st.session_state.sim_prj_info_list)==0:
             st.error('選択されたプロジェクトのスタディは一つもありません。上記「新規」ボタンから作成できます。')
        else:
            #山口　simリストのページ分け
            simcol1, simcol2, simcol3 = st.columns([1,6,2])
            with simcol1:
                pages = st.radio('',['sim','初期仕様', 'バリエーション表','最終仕様'])#st.session_state.sim_prj_info_list
            # with simcol3:
            #     st.write('runner_status:\n' + get_runner_status())
            go = gop.create_gridopsim(pages)#山口　pagesによって返すグリッドを切り替える
            def render_aggrid(go):
                edit=AgGrid(
                    hide_rows_based_on_pages(st.session_state.sim_data_stuck, pages),
                    custom_css=css_ag,
                    allow_unsafe_jscode=True,
                    gridOptions=go,
                    reload_data=False,
                    theme="alpine",
                    enable_quicksearch=True,
                    height=1500,
                    tree_data=True,
                )
                return edit['data']
            #go
            st.session_state.aggrid = render_aggrid(go)
            st.write(st.session_state.sim_data_stuck)
            if "update_chk_conf" in  st.session_state:
                if st.session_state.update_chk_conf is not None:
                    st.session_state.update_chk_conf #デバック用　山口
                    print("gonna update")
                    sql.update_record_sim(st.session_state.update_chk_conf)
                    st.session_state.update_flg = True
                    st.session_state.sim_data_stuck = st.session_state.aggrid
                    del st.session_state['update_chk_conf']
                    dia.success_dia()    


def render_aggrid_rfl(go,df,key):
    response = AgGrid(
        df,
        custom_css=css_ag,
        allow_unsafe_jscode=True,
        gridOptions=go,
        reload_data=False,
        theme="alpine",
        enable_quicksearch=True,
        height=900,
        tree_data=True,
        key=key,
    ) 
    return response['data']


# -----Telema-----
# ボタン:反映、編集、比較、ツリー
# Created: 2025/02/07

def rfl_update_button():
    if st.button("反映",type='secondary') :
        dia.choice_rfl()

init_session_state('button_color')
def change_edit_color():
    if st.session_state.button_color == 'red':
        st.session_state.button_color = 'black'
    else:
        st.session_state.button_color = 'red'



button_html = f"""
    <script>
    function changeColor() {{
        var btn = document.getElementById("custom_button");
        if (btn.style.backgroundColor === "red") {{
            btn.style.backgroundColor = "black";
        }} else {{
            btn.style.backgroundColor = "red";
        }}
        // Python 側にイベントを通知する
        fetch('/_stcore/post_message', {{
            method: 'POST',
            body: JSON.stringify({{"event": "button_clicked"}}),
            headers: {{"Content-Type": "application/json"}}
        }});
    }}
    </script>

    <button id="custom_button" 
            onclick="changeColor()" 
            style="background-color: {st.session_state.button_color}; 
                   color: white; 
                   font-size: 20px; 
                   padding: 10px 20px; 
                   border-radius: 5px; 
                   border: none;">
        Click me
    </button>
"""

def ChangeButtonColour(widget_label, font_color, background_color='transparent'):
    htmlstr = f"""
        <script>
            var elements = window.parent.document.querySelectorAll('button');
            for (var i = 0; i < elements.length; ++i) {{ 
                if (elements[i].innerText == '{widget_label}') {{ 
                    elements[i].style.color ='{font_color}';
                    elements[i].style.background = '{background_color}'
                }}
            }}
        </script>
        """
    components.html(f"{htmlstr}", height=0, width=0)

ChangeButtonColour('second button', 'red', 'blue') # button txt to find, colour to assign


def rfl_edit_button_on():
    if st.button('編集',type='secondary'):
        dia.on_rfl_edit()
        
def rfl_edit_button_off():
    if st.button('編集中',type='primary'):
        dia.off_rfl_edit()

def rfl_compare_button():
    if st.button("比較") :
        dia.compare_rfl()
            
def rfl_tree_button():
    if st.button("ツリー") :
        dia.choice_rfl()
# -----Telema-----

def rfl_matrix_button(): # 山口　マトリックス表示機能　必要な変数をsession_stateに格納しページ遷移 2/13
    if st.button("T/O"):
        st.switch_page("pages/RFL_matrix.py")

def rfl_update_approval():
    if st.button('承認/取り消し'):
        columns_to_check = [
            'c_sender_selected', 's_sender_selected', 'u_sender_selected',
            'c_receiver_selected', 's_receiver_selected', 'u_receiver_selected'
        ]

        # Filter items from session_state that are DataFrames and match the prefix
        filtered_items = {
            key: value for key, value in st.session_state.items()
            if key.startswith('rfl_pj_response_') and isinstance(value, pd.DataFrame)
        }

        # Keep only rows with at least one True in the columns_to_check
        valid_items = {}
        for key, df in filtered_items.items():
            if all(col in df.columns for col in columns_to_check):
                mask = df[columns_to_check].any(axis=1)
                filtered_df = df[mask]
                if not filtered_df.empty:
                    valid_items[key] = filtered_df

        # Define the selection columns with just the 'c', 's', 'u' prefixes
        selection_columns = ['c', 's', 'u']
        # Now sort the valid items by their key
        sorted_items = sorted(valid_items.items(), key=lambda x: x[0])
        output_rows = []
        sender_or_receiver = ''
        
        if sorted_items:
            for key, df in sorted_items:
                for _, row in df.iterrows():
                    for prefix in selection_columns:
                        if row[f'{prefix}_sender_selected'] and row[f'{prefix}_receiver_selected']:
                            print('first:')
                            return dia.approve_sender_receiver_error('selected_both')
                        # Dynamically check if any of the selected flags are True
                        if row[f'{prefix}_sender_selected'] or row[f'{prefix}_receiver_selected']:
                            
                            if row[f'{prefix}_sender_selected']:
                                sender_or_receiver = 'sender'
                            elif row[f'{prefix}_receiver_selected']:
                                sender_or_receiver = 'receiver'

                            # Check if prj_id, rfl_id, and phase_id are not None
                            prj_id = row[f'{prefix}_r_pj_id']
                            rfl_id = row[f'{prefix}_rfl_id']
                            phase_id = row[f'{prefix}_phase_id']
                            

                            if prj_id is not None and rfl_id is not None and phase_id is not None:
                                judge_value = row[f'{prefix}_{sender_or_receiver}_judge']
                                if judge_value is None:
                                    judge_value = '承認済み'
                                    name_value = row[f'{prefix}_{sender_or_receiver}_name']
                                    date_value = row[f'{prefix}_{sender_or_receiver}_date']
                                    comment_value = row[f'{prefix}_{sender_or_receiver}_comment']
                                elif judge_value == '承認済み':
                                    judge_value = None
                                    name_value = None
                                    date_value = None
                                    comment_value = None
                                output_rows.append({
                                    'prj_id': int(prj_id),
                                    'rfl_id': int(rfl_id),
                                    'phase_id': int(phase_id),
                                    'project_code': row['project_code'],
                                    'r_wp': row[f'{prefix}_r_wp'],
                                    f'{sender_or_receiver}_r_item': row[f'{prefix}_r_item'],
                                    f'{sender_or_receiver}_req': row[f'{prefix}_req'],
                                    f'{sender_or_receiver}_l_item': row[f'{prefix}_l_item'],
                                    f'{sender_or_receiver}_logic': row[f'{prefix}_logic'],
                                    f'{sender_or_receiver}_judge': judge_value,
                                    f'{sender_or_receiver}_name': name_value,
                                    f'{sender_or_receiver}_date': date_value,
                                    f'{sender_or_receiver}_comment': comment_value,
                                    f'{sender_or_receiver}_selected': row[f'{prefix}_{sender_or_receiver}_selected'],
                                })

            final_df = pd.DataFrame(output_rows)

            if not final_df.empty:
                has_sender = final_df.columns.str.contains('sender_judge').any()
                has_receiver = final_df.columns.str.contains('receiver_judge').any()
                print(f'has_sender {has_sender} and has_receiver {has_receiver}')

                if has_sender and has_receiver:
                    print('second:')
                    return dia.approve_sender_receiver_error('selected_both')
                
                judge_column = final_df.columns[final_df.columns.str.contains(f'{sender_or_receiver}_judge')].tolist()

                print(f'send_receive_column: {judge_column}')

                # all_values = final_df[judge_column].values.flatten()
                # print('all values: ', all_values)
                # all_same = pd.Series(all_values).nunique() == 1 #if equals 1, all values are the same
                # print('alll value len: ', len(all_values))
                # print('取り消し；',final_df[f'{sender_or_receiver}_judge'][0])
                # if not all_same:
                #     print('not same:')
                #     return dia.approve_sender_receiver_error('diff_approve_selected')

                all_values = list(set(final_df[judge_column].values.flatten()))
                print('all values: ', all_values)
                if len(all_values) >1:
                    return dia.approve_sender_receiver_error('diff_approve_selected')

                dia.rfl_approval_update_confirm(final_df,sender_or_receiver)
        else:
            dia.data_none()

# to extract the first non-null group identifier from preferred columns #チョー　05/09
def extract_group_identifier(row):
    for col in ['c_r_wp', 's_r_wp', 'u_r_wp']:
        if pd.notna(row[col]):
            return row[col]
    return None

# to count non-empty (non-null and non-blank) entries in a column #チョー　05/09
def count_non_empty(series):
    return series.replace('', pd.NA).notna().sum()

# to calculate percentage #チョー　05/09
def calculate_percent(count, total):
    return round((count / total * 100), 2) if total > 0 else 0

# to summarize a group dataframe #チョー　05/09
def summarize_group(gp_df, identifier):
    total = len(gp_df)#山口　このトータルハCSUごとに定めないとだめ 階層によって行数が変わるから
    
    # List of judge columns to evaluate
    fields = [
        'c_sender_judge', 'c_receiver_judge',
        's_sender_judge', 's_receiver_judge',
        'u_sender_judge', 'u_receiver_judge'
    ]
    
    summary = {
        "group_performance": identifier,
        "gp_df_total": total,
    }
    if identifier in ['OBD','排気','高電圧','EMC','エバポ','低周波','燃費電費']:
    # if identifier == 'OBD' or identifier == '排気' or identifier == '高電圧' or identifier == 'EMC' or identifier == 'エバポ' or identifier == '高周波':
        # Compute count and percentage for each judge column 
        for field in fields: 
            header = field.split('_')[0]
            # rfl_id_col = header + '_rfl_id'
            # total = len(gp_df[rfl_id_col].dropna())  
            count = count_non_empty(gp_df[field])
            summary[f"{field}_count"] = f"{total}/{total}"
            prefix = field.rsplit('_judge', 1)[0]
            summary[f"{prefix}_percentage"] = f"100.0%"
    elif identifier in ['高周波','運転性','4WD','燃費電費']:
        for field in fields: 
            header = field.split('_')[0]
            rfl_id_col = header + '_rfl_id'
            total = len(gp_df[rfl_id_col].dropna())  
            count = count_non_empty(gp_df[field])
            summary[f"{field}_count"] = f"{total}/{total}"
            prefix = field.rsplit('_judge', 1)[0]
            summary[f"{prefix}_percentage"] = f"100.0%"
    else:
        for field in fields: 
            header = field.split('_')[0]
            rfl_id_col = header + '_rfl_id'
            total = len(gp_df[rfl_id_col].dropna())  
            
            count = count_non_empty(gp_df[field])
            summary[f"{field}_count"] = f"{count}/{total}"
            prefix = field.rsplit('_judge', 1)[0]
            summary[f"{prefix}_percentage"] = f"{calculate_percent(count, total)}%"
    return summary


# -----Telema-----
# RFLグリッド表示
# Created: 2025/02/04
if int(st.session_state['chosen_id']) == 4:
    # Ha-san added 0214
    searching_input_rfl_values, is_enough_rfl_input = get_session_choices(5)#山口　フェーズ情報を持ってくるように
    is_re_render_rfl = False
    st.session_state.rerun_rfl = False
    # ==========

    if 'rfl_list' not in st.session_state or st.session_state.rfl_list.empty or st.session_state.dialog_state:
        # Ha-san added 0214
        if is_enough_rfl_input:
            try:
                df1_rfl = sql.posgre_get_rfl(*searching_input_rfl_values[1:])
                if df1_rfl is not None and not df1_rfl.empty: #チョー 03/10
                    st.session_state.rfl_list = df1_rfl
                    is_re_render_sim = True
                    st.session_state.rerun_rfl = True
                else:
                    st.error(f'PRJを選択してください。')
                    st.image(co.inf_img, use_column_width=True)
                # st.rerun()
            except Exception as e:
                raise e
                print('print exception',e)
                st.error(f'PRJを選択してください。')
                st.image(co.inf_img, use_column_width=True)
                is_re_render_rfl = False
        elif not st.session_state.login_begin: #チョー 03/10
            st.error(f'PRJを選択してください。')
            st.image(co.inf_img, use_column_width=True)
        
    else:
        is_re_render_rfl = True
        # ==========
    if is_re_render_rfl and not st.session_state.login_begin: #チョー 03/10
        init_session_state('rfl_edit_state')
        # Pattern 1~2
        base_df = st.session_state.rfl_list
        # go = gop.create_gridop_rfl_list()
        
        # pattern 1~2
        
        def render_aggrid(go,df):
            edit=AgGrid(
                df,
                # st.session_state.rfl_list,
                custom_css=css_ag,
                allow_unsafe_jscode=True,
                gridOptions=go,
                reload_data=False,
                theme="alpine",
                enable_quicksearch=True,
                height=800,
                tree_data=True,
            )
            return edit['data']

        init_session_state('compare_click')
        
        if st.session_state['compare_click'] is True:
            go = gop.create_gridop_rfl_list()
            df = st.session_state.rfl_list_comp
            group_df = df.groupby(['project_code','c_r_wp','lot'])
            data = []
            cols = st.columns([4,1,1,1,1,1]) #山口　マトリックス表示用のボタン追加 2/13

            with cols[1]:
                rfl_update_button()
            # with cols[2]:
                # rfl_edit_button()
            with cols[3]:
                rfl_compare_button()
            with cols[4]:
                rfl_tree_button()
            with cols[5]:
                rfl_matrix_button() #山口　マトリックス表示ファンクション 2/13
            # st.write('gp_df T: ', group_df)
            for i,(key, df) in enumerate(group_df):

                # go を使いまわすとバインドされたDFが表示されるため毎回作成
                go = gop.create_gridop_rfl_list()
                
                header_html = f"""
                <div style="width: 400px; height: 140px;margin-left: 0;">
                <style>
                        .custom-header {{
                            font-weight: bold;
                            # background-color: #FFFFFF;
                            background-color: #000000;
                            padding: 5px;
                            display: flex;
                            justify-content: left;
                        }}
                        .custom-header table {{
                            border-collapse: collapse;
                            table-layout: fixed;
                            # background-color: #FFFFFF;
                            # background-color: #e0ffff;
                            background-color: #000000;
                            
                        }}
                        .custom-header th,.custom-header td {{
                            border: 1px solid #ccc;
                            padding: 8px;
                            text-align: left;
                            font-size: 16px;
                            width: 200px;
                        }}
                </style>
                                        
                <div class="custom-header">
                    <table>
                        <colgroup>
                            <col style="width: 30%;">
                            <col style="width: 30%;">
                        </colgroup>                
                        <tr>
                            <th>Project Code</th>
                            <td>{key[0]}</td>
                        </tr>
                    </table>
                    <table>
                        <tr>
                            <th>lot</th>
                            <td>{key[2]}</td>
                        </tr>
                        <tr>
                            <th>性能</th>
                            <td>{key[1]}</td>
                        </tr>
                        </tr>            
                    </table>
                </div>
                """
                
                with st.container():
                    cols = st.columns([4])
                    with cols[0]:
                        st.markdown(header_html, unsafe_allow_html=True)
            grouped_dfs = {
                f'DF_{key1}_{key2}_{key3}': df for (key1,key2,key3),df in group_df
            }
            
            pd.set_option("display.max_rows", None)  # すべての行を表示
            pd.set_option("display.max_columns", None)  # すべての列を表示            
            # print(grouped_dfs)

            render_aggrid(go,df)
           
            
        elif st.session_state['compare_click'] is not True:
            # pattern 3
            base_df = base_df.sort_values(by=["project_code", "c_r_wp_id"])
            
            df_org = base_df.copy()
            prefixes = ['c_','s_','u_']
            # 関数化失敗
            cols = RFLGridConfig.get_value()
            #base_df
            # 後ほど関数化
            
            #to avoid same Ritems to appear in separated rows, sort them
            #just applied to car RFL only for now, further modifing could be needed idk
            #
            c_requirement_unique = base_df['c_r_item'].drop_duplicates().tolist()
            c_requirement_map = {}
            for i, req in enumerate(c_requirement_unique):
                c_requirement_map[req] = i
            base_df['c_r_item_index']=base_df['c_r_item'].map(c_requirement_map)
            
            s_requirement_unique = base_df['s_r_item'].drop_duplicates().tolist()
            s_requirement_map = {}
            for i, req in enumerate(s_requirement_unique):
                s_requirement_map[req] = i
            base_df['s_r_item_index']=base_df['s_r_item'].map(s_requirement_map)
            base_df = base_df.sort_values(by=['c_r_item_index','s_r_item_index'])#このならべかえっってなんだっけ
            #山口　グルーピング前に、全RFLを新規追加したIndex列で並び変える 4/18
            base_df =base_df.sort_values(by=['c_index','s_index','u_index'])
            for i in range(len(prefixes)):
                base_df.loc[base_df[f'{prefixes[i]}r_item'] == base_df[f'{prefixes[i]}r_item'].shift(),f'{prefixes[i]}r_item'] = ''
                base_df.loc[base_df[f'{prefixes[i]}r_unit'] == base_df[f'{prefixes[i]}r_unit'].shift(),f'{prefixes[i]}r_unit'] = ''

                # mask_r_item = base_df[f'{prefixes[i]}r_item'] == base_df[f'{prefixes[i]}r_item'].shift()
                mask_r_scene = base_df[f'{prefixes[i]}r_scene'] == base_df[f'{prefixes[i]}r_scene'].shift()
                # Set r_scene to '' if r_item is None (or empty) and both masks are true
                base_df.loc[
                    (base_df[f'{prefixes[i]}r_item'].isna() | (base_df[f'{prefixes[i]}r_item'] == '')) & mask_r_scene,
                    f'{prefixes[i]}r_scene'
                ] = ''
                

                base_df.loc[base_df[f'{prefixes[i]}f_item'] == base_df[f'{prefixes[i]}f_item'].shift(),f'{prefixes[i]}f_item'] = ''
                base_df.loc[base_df[f'{prefixes[i]}f_unit'] == base_df[f'{prefixes[i]}f_unit'].shift(),f'{prefixes[i]}f_unit'] = ''

                base_df.loc[base_df[f'{prefixes[i]}l_item'] == base_df[f'{prefixes[i]}l_item'].shift(),f'{prefixes[i]}l_item'] = ''
                base_df.loc[base_df[f'{prefixes[i]}l_unit'] == base_df[f'{prefixes[i]}l_unit'].shift(),f'{prefixes[i]}l_unit'] = ''
                
                # mask_l_item = base_df[f'{prefixes[i]}l_item'] == base_df[f'{prefixes[i]}l_item'].shift()
                mask_l_scene = base_df[f'{prefixes[i]}l_scene'] == base_df[f'{prefixes[i]}l_scene'].shift()
                
                # Check if l_item is not None (or NaN) and both masks are True
                base_df.loc[
                    (base_df[f'{prefixes[i]}l_item'].isna() | (base_df[f'{prefixes[i]}l_item'] == '')) & mask_l_scene,
                    f'{prefixes[i]}l_scene'
                ] = ''
            
            #山口　グルーピング前に、全RFLを新規追加したIndex列で並び変える 4/18
            base_df =base_df.sort_values(by=['c_index','s_index','u_index'])

            # Separate rows #05/12 チョー
            base_df_c = base_df[base_df["c_r_wp_summary_index"].notna()].copy()
            base_df_s = base_df[base_df["c_r_wp_summary_index"].isna()].copy()

            # Create a unified sort key column using available index #05/12 チョー
            base_df_c["sort_index"] = base_df_c["c_r_wp_summary_index"]
            base_df_s["sort_index"] = base_df_s["s_r_wp_summary_index"]

            # Combine both
            combined_df = pd.concat([base_df_c, base_df_s], ignore_index=True)

            #05/12 チョー
            combined_df = combined_df.sort_values(by=['sort_index','c_index','s_index','u_index'])
            base_df = combined_df

            for col in base_df.columns:#ここなんでループしているのかわからない
                group_df = base_df.groupby(['sort_index']) #05/12 チョー
            
            
            #ここでnanグループがあればさらに細分化する
            #単にc_r_wp列にNaNgがあるか判断すればいいじゃん
            group_df_wo_veh = None
            performances = base_df['c_r_wp'].drop_duplicates().values.tolist()
            if None in performances:#車両階層のないRFLを判定、あればさらにグルーピング
                                
                base_df_wo_veh = base_df[base_df['c_r_wp'].isnull()]
                # st.write(base_df_wo_veh)
                group_df_wo_veh = base_df_wo_veh.groupby(['s_project_code', 's_r_wp', 'lot'], dropna=False)
                # st.write(group_df_wo_veh.groups.keys())
            
            data = []
            cols = st.columns([4,1,1,1,1,1,1]) #山口　マトリックス表示用のボタン追加 2/13

            with cols[1]:
                rfl_update_button()
            with cols[2]:
                if st.session_state.rfl_edit_state is False or st.session_state.rfl_edit_state ==[]:
                    rfl_edit_button_on()
                elif st.session_state.rfl_edit_state:
                    rfl_edit_button_off()
            with cols[3]:
                rfl_compare_button()
            with cols[4]:
                rfl_tree_button()
            with cols[5]:
                rfl_matrix_button() #山口　マトリックス表示ファンクション 2/13
            with cols[6]:
                rfl_update_approval() #RFL承認 #チョー 04/14

        #チョー　05/09
        summary_data = []
        for key, gp_df in group_df:
            row = gp_df.iloc[0]
            group_identifier = extract_group_identifier(row)
            summary_data.append(summarize_group(gp_df, group_identifier))
        # #チョー　05/09
        # for key, gp_df in group_df_wo_veh:
        #     if key[1] not in ['排気', 'OBD', '高電圧']:
        #         continue
        #     # st.write('gp dfss:', gp_df)
        #     row = gp_df.iloc[0]
        #     group_identifier = extract_group_identifier(row)
        #     summary_data.append(summarize_group(gp_df, group_identifier))

        # Convert to DataFrame
        summary_df = pd.DataFrame(summary_data)
        # Display in Streamlit
        st.write('summary_df: ',summary_df)
        with st.expander("承認率状況​"):
            # st.write('summary_df: ',summary_df)
            go = gop.update_rfl_dashboard_grid()
            AgGrid(
                summary_df,
                custom_css=css_ag,
                gridOptions=go,
                reload_data=False,
                height=650,
            )
        # count_key = 0

        for i,(key, df) in enumerate(group_df):
            # Access the values from the first row of the group DataFrame #05/12 チョー
            lot = df.iloc[0]['lot']
            # Access the first row of the group #05/12 チョー
            c_r_wp = df.iloc[0]['c_r_wp']
            
            # Check if 'c_r_wp' is None or NaN #05/12 チョー
            if pd.isna(c_r_wp):  # This checks for both None and NaN
                project_code = df.iloc[0]['s_project_code']
                c_r_wp = df.iloc[0]['s_r_wp']  # If 'c_r_wp' is None or NaN, use 's_r_wp'
            # count_key = i

            # go を使いまわすとバインドされたDFが表示されるため毎回作成
            go = gop.create_gridop_rfl_list()
            
            header_html = f"""
            <div style="width: 400px; height: 140px;margin-left: 0;">
            <style>
                    .custom-header {{
                        font-weight: bold;
                        background-color: #FFFFFF;
                        padding: 5px;
                        display: flex;
                        justify-content: left;
                    }}
                    .custom-header table {{
                        border-collapse: collapse;
                        table-layout: fixed;
                        background-color: #FFFFFF;
                        # background-color: #e0ffff;
                        # background-color: #000000;
                        
                    }}
                    .custom-header th,.custom-header td {{
                        border: 1px solid #ccc;
                        padding: 8px;
                        text-align: left;
                        font-size: 16px;
                        width: 200px;
                    }}
            </style>
                                    
            <div class="custom-header">
                <table>
                    <colgroup>
                        <col style="width: 30%;">
                        <col style="width: 30%;">
                    </colgroup>                
                    <tr>
                        <th>Project Code</th>
                        <td>{project_code}</td>
                    </tr>
                </table>
                <table>
                    <tr>
                        <th>lot</th>
                        <td>{lot}</td>
                    </tr>
                    <tr>
                        <th>性能</th>
                        <td>{c_r_wp}</td>
                    </tr>
                    </tr>            
                </table>
            </div>
            """
            
            with st.container():
                cols = st.columns([4])
                with cols[0]:
                    st.markdown(header_html, unsafe_allow_html=True)
            st.write('rfl: ', df)
            st.session_state[f'org_rfl_pj_{i}'] = df
            
            st.session_state[f'rfl_pj_response_{i}'] = render_aggrid_rfl(go,df,str(i))

        # #車両階層のないものにも同様の処理
        # for i,(key, df) in enumerate(group_df_wo_veh):
        #     # st.write('df_org: ', df_org)
        #     # st.write('gp_df: ', df)
        #     if not key[1] in ['排気', 'OBD','高電圧']:  #山口　よくないのはわかっているけど個々の動作は音振OBDに限定したかった TODO 恒久版の対策を考えること
        #         continue
        #     # st.write(key)
        #     # st.write(df)
        #     # go を使いまわすとバインドされたDFが表示されるため毎回作成
        #     go = gop.create_gridop_rfl_list()
            
        #     header_html = f"""
        #     <div style="width: 400px; height: 140px;margin-left: 0;">
        #     <style>
        #             .custom-header {{
        #                 font-weight: bold;
        #                 background-color: #FFFFFF;
        #                 padding: 5px;
        #                 display: flex;
        #                 justify-content: left;
        #             }}
        #             .custom-header table {{
        #                 border-collapse: collapse;
        #                 table-layout: fixed;
        #                 background-color: #FFFFFF;
        #                 # background-color: #e0ffff;
        #                 # background-color: #000000;
                        
        #             }}
        #             .custom-header th,.custom-header td {{
        #                 border: 1px solid #ccc;
        #                 padding: 8px;
        #                 text-align: left;
        #                 font-size: 16px;
        #                 width: 200px;
        #             }}
        #     </style>
                                    
        #     <div class="custom-header">
        #         <table>
        #             <colgroup>
        #                 <col style="width: 30%;">
        #                 <col style="width: 30%;">
        #             </colgroup>                
        #             <tr>
        #                 <th>Project Code</th>
        #                 <td>{key[0]}</td>
        #             </tr>
        #         </table>
        #         <table>
        #             <tr>
        #                 <th>lot</th>
        #                 <td>{key[2]}</td>
        #             </tr>
        #             <tr>
        #                 <th>性能</th>
        #                 <td>{key[1]}</td>
        #             </tr>
        #             </tr>            
        #         </table>
        #     </div>
        #     """
            
        #     with st.container():
        #         cols = st.columns([4])
        #         with cols[0]:
        #             st.markdown(header_html, unsafe_allow_html=True)
        #     #st.write(df)
        #     st.session_state[f'org_rfl_pj_{i}'] = df
            
        #     st.session_state[f'rfl_pj_response_{count_key+i}'] = render_aggrid_rfl(go,df,str(i) + '_s')
        #     # st.write(f'session response {i}', st.session_state[f'rfl_pj_response_{i}'])

        

#チョー 02/26 
if st.session_state.rerun_rfl:
    # print("rerun rfl")
    st.session_state.rerun_rfl = False
    st.rerun()

# #RFLメニューが選択された場合
# if int(st.session_state['chosen_id'])  == 4:
#     url = "http://10.20.147.183:8502/"  # 挿入したい外部ページのURL 山口さんが作ったRFLページ
#     st.markdown(f"""
#         <style>
#         .responsive-iframe {{
#             position: relative;
#             overflow: hidden;
#             padding-top: 56.25%;
#         }}
#         .responsive-iframe iframe {{
#             position: absolute;
#             top: 0;
#             left: 0;
#             width: 100%;
#             height: 100%;
#             border: 0;
#         }}
#         </style>
#         <div class="responsive-iframe">
#             <iframe src="{url}" frameborder="0" allowfullscreen></iframe>
#         </div>
#     """, unsafe_allow_html=True)

# st.markdown(
#     """
#     <div style="text-align: right; margin-top: 50px;">
#         お問い合わせ先：UU3溝越 中野 武田
#     </div>
#     """,
#     unsafe_allow_html=True
# )

#山口　計算用のページ作成

if int(st.session_state['chosen_id'])  == 5 :
   Jcurb.Jcurb_ui()

#チョー　追加 03/10
if not st.session_state.login_begin:
    col1, col2, col3, col4 = st.columns([1, 1, 1, 10])
    with col1:
        if st.button('TOPへ'):
            st.session_state.login_begin = True
            st.rerun()
    with col2:
        st.button('About')
    with col3:
        st.button('Contact')
    with col4:
        st.markdown(
            """
            <div style="text-align: right; font-size: 16px;">
                <span style="font-weight: bold;font-size: 20px;">お問い合わせ先</span><br>
                <span><i class="fas fa-user"></i> UU3溝越 中野 武田</span><br>
                <span><i class="fas fa-envelope"></i> aaaa@mail.nissan.co.jp</span><br>
                <span><i class="fas fa-phone"></i> 090-XXXX-XXXX</span>
            </div>
            <style>
                /* Load Font Awesome icons */
                @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css');
            </style>
            """,
            unsafe_allow_html=True
        )
    # st.rerun()
else:
    st.image(co.inf_img, use_column_width=True)
    col1, col2, col3, col4, col5 = st.columns([3,3,3,3,7])
    with col1:
        st.markdown(
            """
            <div style="text-align: left; font-size: 16px;">
                <span style="font-weight: bold;font-size: 20px;">お問い合わせ先：</span><br>
            </div>
            <style>
                /* Load Font Awesome icons */
                @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css');
            </style>
            """,
            unsafe_allow_html=True
        )   
    with col2:
        st.markdown(
            """
            <div style="text-align: left; font-size: 16px;">
                <span><i class="fas fa-user"></i> ：UU3溝越 中野 武田</span><br>
            </div>
            """,
            unsafe_allow_html=True
        )    

    with col3:
        st.markdown(
            """
            <div style="text-align: left; font-size: 16px;">
                <span><i class="fas fa-envelope"></i> ：aaaa@mail.nissan.co.jp</span><br>
            </div>
            """,
            unsafe_allow_html=True
        )  

    with col4:
        st.markdown(
            """
            <div style="text-align: left; font-size: 16px;">
                <span><i class="fas fa-phone"></i> ：090-XXXX-XXXX</span>
            </div>
            """,
            unsafe_allow_html=True
        )  

del sql