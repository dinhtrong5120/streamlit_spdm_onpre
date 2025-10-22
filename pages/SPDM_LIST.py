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
from db.rfl_repository import RFLRepository as rflq #telema-kyaw
import os
from module.data_processing import create_rfl_grid_excel_data
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

# MAPボタンを押した後、リロード処理を行う    #チョー　10/31
if 'map_click' not in st.session_state:
    st.session_state.map_click = False

if 'chosen_id' not in st.session_state:
    st.session_state.chosen_id = 1  # ここどうしようか、、、山口 12/3
else:
    st.session_state.chosen_id = st.session_state.chosen_id

# チョー 02/26
if 'rerun_rfl' not in st.session_state:
    st.session_state['rerun_rfl'] = False
# チョー 04/03
if 'summary_rlist_flag' not in st.session_state:
    st.session_state.summary_rlist_flag = False


# チョー #関数追加 #10/2
# MAPリンクを取得するため、選択されたプロジェクトに応じてプロジェクトを変更する
def get_map_link(project_name):
    return project_name.replace(' ', '_').replace('[', '').replace(']', '').replace('-', '_') + '_MAP'


# タブメニュー表示・処理    #チョー　10/31
def title_tab_bar():
    _chosen_id = st.session_state.chosen_id
    chosen_id = stx.tab_bar(data=[
        stx.TabBarItemData(id=1, title="諸元リスト(SEリスト)", description=None),
        stx.TabBarItemData(id=2, title="要求リスト(Rリスト)", description=None),
        stx.TabBarItemData(id=3, title="SIM管理表", description=None),
        # Telema RFL用タブ作成 2025/01/28
        stx.TabBarItemData(id=4, title="RFL", description=None),
    ], default=st.session_state.chosen_id)
    st.session_state.chosen_id = chosen_id
    if _chosen_id != chosen_id:  # 山口 タブバー押してもすぐ画面更新されないため強制リロードをかける12/3
        st.rerun()


# 02/07 チョー　変更ダイアログでチェックボックス無しで表示するようの処理
def update_reload_fun(df_mold, chk_column_name):
    # Find the column name that contains 'selected' (this works even if it contains dynamic characters)
    selected_column = [col for col in df_mold.columns if chk_column_name in col.lower()]
    # print('selected_column: ', selected_column)
    if selected_column:
        # チョー 02/03編集
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


# r_summaryをUpdateする処理    チョー　04/24
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


# 変更変更ボタン処理    #チョー　01/16
def update_button():
    update_btn = st.button("変更")
    if update_btn and 'se_data_stuck' in st.session_state and int(st.session_state['chosen_id']) == 1:

        df_mold = pd.DataFrame(st.session_state.aggrid)

        # 02/07 チョー　関数分ける、呼び出す
        se_update_info = update_reload_fun(df_mold, 'select')
        if se_update_info is None or se_update_info.empty:
            dia.data_none()
        else:
            st.session_state.updata_conf_dia_result = se_update_info
            dia.updata_conf_dia()

    elif update_btn and 'rlist_data_stuck' in st.session_state and int(
            st.session_state['chosen_id']) == 2:  # 山口 Rリストに対しての機能追加 1/29
        # r_summaryのUpdateする処理を行う　チョー　04/24
        if st.session_state.summary_rlist_flag is True:
            r_summary_update()
        else:
            df_mold = pd.DataFrame(st.session_state.aggrid)

            # 02/07 チョー　ダイアログでチェックボックス無しで変更する
            r_update_info = update_reload_fun(df_mold, 'target_selected')
            if r_update_info is None or r_update_info.empty:
                dia.data_none()
            else:
                st.session_state.updata_conf_dia_result = r_update_info
                dia.updata_conf_dia_rlist()

    elif update_btn and 'sim_data_stuck' in st.session_state and int(st.session_state['chosen_id']) == 3:
        df_mold = pd.DataFrame(st.session_state.aggrid)
        # st.dataframe(df_mold)
        result = sql.db_update_selected(df_mold, now, username)
        # st.dataframe(result)
        if result is None or result.empty:
            # st.dataframe(result)
            dia.data_none()
        else:
            st.session_state.updata_conf_dia_result = result
            dia.updata_conf_dia_sim()
    elif update_btn and not 'se_data_stuck' in st.session_state:
        dia.AGdata_none()


# リロードボタン表示    #チョー　10/31
def reload_button():
    # 複数プロジェクトを選択してMAPボタンを押下後、ダイアログでの確認ボタンを押してリロード処理を行う
    if st.session_state.map_click is True:
        reload_info()
    # リロードボタンを押下後、リロード処理を行う
    elif st.button("リロード"):
        reload_info()
 
#リロードボタン処理    #チョー　10/31山口　simページ追加により条件分岐追加 12/9
def reload_info():
    st.session_state.map_click = False
    # 条件を選択された前、リロードボタンを押した場合
    if 'se_data_stuck' not in st.session_state or st.session_state.dialog_state:
        st.switch_page("pages/SPDM_LIST.py")  # SEリストページへ移動する
    elif int(st.session_state.chosen_id) == 1 and 'se_data_stuck' in st.session_state:
        # 更新された情報を取得する
        df1, df2 = sql.posgre_get_date(st.session_state['selectoption1'],
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
        df1, df2 = sql.posgre_get_data_sim(st.session_state['selectoption1'], st.session_state['selectoption4'],
                                           st.session_state['selectoption5'])  # チョー 03/10
        st.session_state.sim_prj_info_list = df1
        st.session_state.sim_data_stuck = df2
    else:
        st.error('unexpected reload')


# 条件ボタン表示・処理    #チョー　10/31
def condition_button():
    if st.button("PRJ選択"):  # or st.session_state.dialog_state:

        #チョー　共通ダイアログを使う 03/10
        if int(st.session_state['chosen_id'])  == 1:
            dia.choice_se_bookmark('se_list')
        if int(st.session_state['chosen_id'])  == 2:
            dia.choice_se_bookmark('r_list')
        if int(st.session_state['chosen_id'])  == 3:
            dia.choice_se_bookmark('sim_list') 
        if int(st.session_state['chosen_id'])  == 4:
            dia.choice_se_bookmark('rfl_list')


# ログインボタン表示・処理    #チョー　10/31
def login_button():
    if st.button("Logout"):
        st.switch_page("app.py")

#MAPボタン表示・処理    #チョー　10/31
def map_button():
    # 山口　マップをグリッド表示するためのやつ `11/13
    if st.button("MAP"):

        if "se_data_stuck" in st.session_state and int(st.session_state.chosen_id) == 1:  # 山口　chosen_idを条件に追加12/5
            df_mold = pd.DataFrame(st.session_state.aggrid)
            result = sql.db_update_selected(df_mold, now, username)  # 選択した項目入手

            if len(result) == 1:  # この機能は複数選択で動かすわけにいかない
                dia.mapgrid(result)

            else:
                st.error("MAP表示は1項目選択時のみしか機能しません！！")
                st.write(result)
        elif "sim_data_stuck" in st.session_state and int(st.session_state.chosen_id) == 3:  # 山口　simMap用の追加 12/5
            df_mold = pd.DataFrame(st.session_state.aggrid)
            result = sql.db_update_selected(df_mold, now, username)  # 選択した項目入手

            if len(result) == 1:  # この機能は複数選択で動かすわけにいかない
                dia.mapgrid_by_name(result)  # 名前参照用に変更する
                # dia.mapgrid(result)
            else:
                st.write(result)
                st.error("MAP表示は1項目選択時のみしか機能しません！！")
                st.write(result)
        else:
            st.error("uhhhh..")


# 山口　時系列表示機能用ボタン 1/29
def timeseries_button():
    if st.button('時系列表示'):
        if 'rlist_data_stuck' in st.session_state and int(st.session_state.chosen_id) == 2:
            df_mold = pd.DataFrame(st.session_state.aggrid)
            result = df_mold[df_mold['timeseries_selected']]  # 選択した項目入手

            if len(result) == 1:  # この機能は複数選択で動かすわけにいかない
                dia.timeseriesgrid(result)
            else:
                st.write(result)
                st.error("MAP表示は1項目選択時のみしか機能しません！！")


# 比較ボタン表示・処理    #チョー　11/25
def compare_button():
    if st.session_state['compare_click'] is False:
        if st.button("設計値比較"):
            dia.compare_se()
    else:
        if st.button("戻る"):
            st.session_state['compare_click'] = False
            st.rerun()

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
    elif int(st.session_state.chosen_id) == 3:
        if st.button("新規"):
            dia.create_new_study()


def sim_button():  # 山口　simボタン 12/6
    if st.button('sim実行'):
        if 'sim_data_stuck' in st.session_state:
            dia.sim()


def dashboard_button():  # 山口　simボタン 12/6
    if st.button('結果'):
        if 'sim_data_stuck' in st.session_state:
            dia.to_dashboard()


def send_to_RFL_button():
    if st.button('RFL転記'):
        if 'sim_data_stuck' in st.session_state:
            dia.send_to_RFL()


# 02/10 チョー　確定ボタン処理
def fixed_button():
    if st.button('確定'):
        if 'sim_data_stuck' in st.session_state and 'sim_prj_info_list' in st.session_state:
            dia.choice_sim_fixed()


# 02/10 チョー　有効ステータスのリストがある場合
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


# チョー 03/25 #Rリスト以外のタブに移動されると、rlist_previous_selectedセッションを削除する　
if int(st.session_state['chosen_id']) != 2:
    # 05/07
    for key in ['rlist_previous_selected', 'dt_previous_selected', 'r_sum_reload_flag']:
        if key in st.session_state:
            del st.session_state[key]

# チョー　05/07
if int(st.session_state['chosen_id']) == 2:
    keys_to_delete = ['dt_previous_selected', 'r_sum_reload_flag', 'summary_rlist']
    for key in keys_to_delete:
        if key in st.session_state and not st.session_state.summary_rlist_flag:
            del st.session_state[key]

def r_list_selected():
    options = st.session_state.total_selected_rlist
    selected_option = st.selectbox('選択', options, label_visibility='collapsed')
    # チョー 03/25 # Rリストの初期表示にセッション情報に設定する
    if 'rlist_previous_selected' not in st.session_state:
        st.session_state.rlist_previous_selected = options[0]

    if selected_option != '選択してください。':
        # print('rlist_previous_selected:',st.session_state.rlist_previous_selected)
        # print('selected:',selected_option)
        # st.session_state.rlist_display_flag = True
        if 'selectoption6' not in st.session_state or st.session_state.rlist_previous_selected != selected_option:  # 以前選択する値と現在選択する値が違うとDB処理を行う　 #チョー 03/25
            st.session_state.rlist_previous_selected = selected_option  # チョー 03/25 #選択された情報をセッションに設定する

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


# 05/07　WD　Dropdown選択
def dt_list_selected():
    dt_list = st.session_state.total_drivetrain_selected
    dt_selected_option = st.selectbox('選択', dt_list, label_visibility='collapsed')
    if 'dt_previous_selected' not in st.session_state:  # 初期表示の場合
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


# 「ステートメント記入」ボタン表示　＃チョー　04/16
def r_statement_button():
    if st.button('ステートメント記入'):
        dia.insert_r_statement()


# Kyaw 07/22
def edit_column_width_button():
    if st.button('モード保存'):
        dia.confirm_resized_column_width()

    # チョー 03/10


if st.session_state.button_edit_state and not st.session_state.login_begin:
    if int(st.session_state[
               'chosen_id']) == 1 and "prj_info_list" in st.session_state:  # プロジェクトが選択された場合　＃チョー　10/31 山口　選ばれた帳票でボタンを変更するように条件追加 11/30

        if 'compare_click' not in st.session_state:
            st.session_state['compare_click'] = False

        col1, col2, col3, col4, col5 = st.columns([10, 1.5, 1, 1, 1.8])
        with col1:
            title_tab_bar()  # タブメニュー表示関数を呼び出す
        with col2:
            condition_button()  # 条件ボタン表示関数を呼び出す
        with col3:
            update_button()  # 編集ボタン表示関数を呼び出す
        with col4:
            map_button()  # MAP示関数を呼び出す
        with col5:
            compare_button()  # 比較ボタン表示関数を呼び出す #11/25

    elif int(st.session_state['chosen_id']) == 2 and "r_prj_info_list" in st.session_state:  # 山口 Rリスト用表示ボタン 1/29

        col_def = [9, 1.2, 5, 1, 1.3, 1.6]  # チョー 04/24
        if st.session_state.summary_rlist_flag is True:
            col_def = [9, 1, 2, 1, 0.001, 0.001]  # チョー 選択リストなしで表示する 04/24
        col1, col2, col3, col4, col5, col6 = st.columns(col_def)
        with col1:
            title_tab_bar()  # タブメニュー表示関数を呼び出す
        with col2:
            condition_button()  # 条件ボタン表示関数を呼び出す
        with col4:
            update_button()  # 編集ボタン表示関数を呼び出す
        if st.session_state.summary_rlist_flag is False:
            with col3:
                r_list_selected()  # チョー 追加　03/10
            with col5:
                timeseries_button()  # 時系列ボタン
            with col6:
                edit_column_width_button()  # Kyaw 07/23
        else:
            with col3:
                dt_list_selected()  # チョー 追加　05/07

        # one for the left space, one for the right-aligned widget　＃チョー 04/03 サマリーモードを追加する
        col1, col2, col3, col4 = st.columns([8, 1, 1.5, 1.5])
        with col4:
            on = st.toggle("サマリーモード", key="summary_rlist_flag")
        if st.session_state.summary_rlist_flag:  # チョー　04/16
            with col3:
                r_statement_button()

    elif int(st.session_state['chosen_id']) == 3 and "sim_prj_info_list" in st.session_state:  # 山口　sim実行用ボタン追加　12/6
        col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(
            [8, 1, 1, 1, 1, 1, 1, 1, 1])  # 山口　列増やした12/5 また列増やした1/29 またまた列増やした2/6
        with col1:
            title_tab_bar()  # タブメニュー表示関数を呼び出す
        with col2:
            condition_button()  # 条件ボタン表示関数を呼び出す
        with col3:
            update_button()  # 編集ボタン表示関数を呼び出す
        with col4:
            map_button()  # MAPボタン表示関数を呼び出す
        with col5:
            create_button()  # 山口　新規Sim作成ボタン 12/5
        with col6:
            sim_button()
        with col7:
            dashboard_button()  # 山口　ダッシュボード表示ボタン12/18
        with col8:
            send_to_RFL_button()  # 山口　RFL転記用ボタン2/6
        # with col9:
        #     pass #山口　シナリオのR比較するためreserve
        with col9:
            fixed_button()  # 02/10 チョー　確定ボタン処理を呼び出す
    else:
        col1, col2, col3 = st.columns([10, 1, 1.5])
        with col1:
            title_tab_bar()  # タブメニュー表示関数を呼び出す
        # with col:
        #     condition_button()  #条件ボタン表示関数を呼び出す
        with col3:
            condition_button()  # 条件ボタン表示関数を呼び出す
else:  # チョー 追加 03/10
    col1, col2, col3, col4, col5 = st.columns([10, 1, 1, 1, 1])
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


if 'create_new_sim' in st.session_state:
        if st.session_state.create_new_sim is True:
            # st.session_state.create_new_sim = False
            # reload_info_update()
            reload_updated()

# チョー　01/16
if 'updated_msg' in st.session_state and st.session_state.updated_msg is True:
    updated_success_msg()

# チョー　05/07
if 'r_sum_reload_flag' not in st.session_state:
    st.session_state.r_sum_reload_flag = True

# チョー　05/07
if 'summary_rlist' not in st.session_state:
    st.session_state.summary_rlist = None


# チョー 04/03 #rリストのサマリーGrid表示
def display_r_summary():
    # チョー　05/07
    if st.session_state.r_sum_reload_flag:
        r_df1, r_df2 = sql.get_r_summary()
        # st.write('db df1: ', r_df1)
        # st.write('db df2: ', r_df2)
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
            'summary_index'  # 山口　サマリーでの順番を指定するため 5/8
        ]

        df_selects = st.session_state.df_selects

        # Select the corresponding columns from r_df `山口　ドロップダウンで変更してもステートメントが変わらないため、先に＠ｄｆ１準備してget_r_statementもdf1から取得するように変更した5/8
        df1 = r_df2[get_column_from_rlist]

        # ｒステートメントを取得する　＃チョー　04/16
        r_statement_df = sql.get_r_statement(list(set(df1['project_id'])), list(set(df1['phase_id'])), 'R')
        st.session_state.r_statement_df = r_statement_df

        r_parameter_id_column = f'r_parameter_id'
        judge_column = f'judge'
        performance_column = f'performance'
        wp_id_column = f'wp_id'

        # Remove rows where the specific judge column is NaN or None or ''
        df1 = df1[df1[judge_column].notna() & (df1[judge_column] != '')]  # 04/08

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
            df1 = pd.concat(selected_rows).sort_values(by='summary_index').reset_index(
                drop=True)  # 山口 サマリーの並べ替えを実装する 5/8

            df1[f'judge_emoji'] = df1[f'{judge_column}'].apply(
                lambda x: '🟢' if x == 'OK' else '🟠' if x == 'NG' else '🟡'  # OK,NG以外は黄色にする #チョー　04/16
            )

            # st.write("df1 before result:", df1)

            df2 = sql.get_wp_statement(list(set(df1['project_id'])), list(set(df1['phase_id'])),
                                       df1[wp_id_column].dropna().astype(int), 'R')
            # st.write("result_df in wp statement:", df2)

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
            st.session_state.r_sum_reload_flag = False  # チョー　05/07
        else:
            st.session_state.summary_rlist = None  # チョー　05/07


# Kyaw 07/23 #Check the columns that have resized or not!
def resized_column_width(edit):
    # Get current column state
    column_state = edit.grid_response.get("columnsState")
    # st.write('column state: ',column_state)
    if column_state:
        # Extract current resized info
        current_widths = [
            {"colId": col["colId"], "width": round(col["width"], 2), "hide": col["hide"]}
            for col in column_state if "colId" in col and "width" in col and "hide" in col
        ]
        # st.write("Current column widths:", current_widths)

        # Initialize initial state only once
        if "initial_column_widths" not in st.session_state:
            st.session_state.initial_column_widths = current_widths
        # st.write("Initial widths stored.",st.session_state.initial_column_widths)

        # Compare current with initial
        changed_columns = []
        for current_col in current_widths:
            for initial_col in st.session_state.initial_column_widths:
                if current_col["colId"] == initial_col["colId"]:
                    if abs(current_col["width"] - initial_col["width"]) > 0.1 or current_col["hide"] != initial_col[
                        "hide"]:  # ignore tiny diffs
                        changed_columns.append(current_col)
                    break

        # Store changed info and show
        if changed_columns:
            # st.warning("🛠 Changed column widths:")
            # st.json(changed_columns)
            st.session_state.changed_column_widths = changed_columns
        else:
            # st.success("No changes in column widths.")
            st.session_state.changed_column_widths = []
    else:
        # st.info("Resize some columns to track changes.")
        print('Resize some columns to track changes.')


# SEリストメニューが選択された場合
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
        elif not st.session_state.login_begin:  # チョー　追加 03/10
            # st.error(f'SEリスト条件から選んでください。')
            st.image(co.inf_img, use_column_width=True)
    else:
        is_re_render_selist = True
        # ==========    
    if is_re_render_selist and not st.session_state.login_begin:  # チョー　追加 03/10

        st.session_state.create_click = False
        go = gop.create_gridop()

        if st.session_state['compare_click'] is True:
            st.info("値を変更する場合は「戻る」ボタンを押してください。")


        def render_aggrid(go):
            edit = AgGrid(
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

        # go#山口デバック用
        # st.session_state.prj_info_list
        if "update_chk_conf" in st.session_state:
            if st.session_state.update_chk_conf is not None:
                # st.session_state.update_chk_conf #デバック用　山口
                print("gonna update")
                sql.update_record(st.session_state.update_chk_conf)
                st.session_state.update_flg = True
                st.session_state.se_data_stuck = st.session_state.aggrid
                del st.session_state['update_chk_conf']
                # dia.success_dia()   
                reload_updated()  # チョー　01/16

# Rリストメニューが選択された場合 #チョー　01/08
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
                    st.rerun()  # チョー 03/10

            except Exception as e:
                raise e  # Rリストのロードが最初の一回目でできない件、Try内でエラーが起きているという仮説もと、raiseさせてみると、特にException表示もなくロードされた、正直意味わからない 5/10 山口
                is_re_render_rlist = False
        elif not st.session_state.login_begin:  # チョー 03/10
            st.error(f'PRJを選択してください。')
            st.image(co.inf_img, use_column_width=True)
    else:
        is_re_render_rlist = True
        # ==========
    if is_re_render_rlist and not st.session_state.login_begin and not st.session_state.summary_rlist_flag:  # チョー 03/10
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
                update_mode="GRID_CHANGED"  # Kyaw 07/23 To get the resized columns' value when its changed
            )
            resized_column_width(edit)  # Kyaw 07/23 Call the function
            return edit['data']
        st.session_state.aggrid = render_aggrid(go)

        # st.session_state.prj_info_list
        if "update_chk_conf" in st.session_state:
            # st.write('update_chk_conf session: ', st.session_state.update_chk_conf)
            if st.session_state.update_chk_conf is not None:
                # st.session_state.update_chk_conf #デバック用　
                print("gonna update")
                sql.update_record_rlist(st.session_state.update_chk_conf)
                st.session_state.update_flg = True
                st.session_state.rlist_data_stuck = st.session_state.aggrid
                del st.session_state['update_chk_conf']
                # dia.success_dia()    
                reload_updated()  # 02/07 チョー　リロード関数を呼び出す
    elif st.session_state.summary_rlist_flag:
        display_r_summary()
        # ステートメント表示　＃チョー　04/16
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


# sim管理表のページによって表示行を変える関数
def hide_rows_based_on_pages(df_sim, pages):
    id_col = df_sim.loc[:, df_sim.columns.str.contains(';senario_parameter_id;')].columns.tolist()[0]
    if pages == '初期仕様':
        senario_id_not_to_show = [
            0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 29, 30, 34, 36, 37,
            38, 39, 42, 43, 45, 55, 70, 96, 97, 98, 99
        ]
        return df_sim[~df_sim[id_col].isin(senario_id_not_to_show)]

    if pages == 'バリエーション表':
        senario_id_to_show = [
            410,
            600, 602,
            10001,
            20046, 20048,
            20021, 20022, 20025,
            20070, 20026,
            25000,
            110008, 110004, 110005,
            300000, 300001, 300002,
            400000, 400001,
            401000, 401001

        ]
        return df_sim[df_sim[id_col].isin(senario_id_to_show)]
    return df_sim


# SEリスト以外のタブを選択すると何も表示されない。　＃チョー　11/01
# #Rリストメニューが選択された場合
# #SIM管理表メニューが選択された場合
# SIM管理表メニューが選択された場合 山口　機能実装のため有効化
if int(st.session_state['chosen_id']) == 3:
    # Ha-san added 0214
    searching_input_sim_values, is_enough_sim_input = get_session_choices(5)  # チョー 03/10
    is_re_render_sim = False
    # ==========
    if 'sim_data_stuck' not in st.session_state or st.session_state.dialog_state:
        # Ha-san added 0214
        if is_enough_sim_input:
            try:
                df1, df2 = sql.posgre_get_data_sim(*searching_input_sim_values[1:])
                st.session_state.sim_prj_info_list = df1
                st.session_state.sim_data_stuck = df2
                is_re_render_sim = True
                st.rerun()  # チョー 03/10
            except Exception as e:
                raise e  # Rリストと同様に、raiseさせると最初の一回でロードできるようになる　???? 山口 6/7
                is_re_render_sim = False
        elif not st.session_state.login_begin:  # チョー 03/10
            st.error(f'PRJを選択してください。')
            st.image(co.inf_img, use_column_width=True)
    else:
        is_re_render_sim = True
        # ==========
    if is_re_render_sim and not st.session_state.login_begin:  # チョー 03/10
        # st.session_state.sim_data_stuck
        # 山口　simリストのページ分け

        pages = st.radio('', ['sim', '初期仕様', 'バリエーション表', '最終仕様'])  # st.session_state.sim_prj_info_list

        if len(st.session_state.sim_prj_info_list) == 0:
            st.error('選択されたプロジェクトのスタディは一つもありません。上記「新規」ボタンから作成できます。')
        else:
            go = gop.create_gridopsim()


            def render_aggrid(go):
                edit = AgGrid(
                    hide_rows_based_on_pages(st.session_state.sim_data_stuck, pages),
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


            # go
            st.session_state.aggrid = render_aggrid(go)
            if "update_chk_conf" in st.session_state:
                if st.session_state.update_chk_conf is not None:
                    st.session_state.update_chk_conf  # デバック用　山口
                    print("gonna update")
                    sql.update_record_sim(st.session_state.update_chk_conf)
                    st.session_state.update_flg = True
                    st.session_state.sim_data_stuck = st.session_state.aggrid
                    del st.session_state['update_chk_conf']
                    dia.success_dia()


def render_aggrid_rfl(go, df, key):
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
    if st.button("反映", type='secondary'):
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
    }}0
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


ChangeButtonColour('second button', 'red', 'blue')  # button txt to find, colour to assign


def rfl_edit_button_on():
    if st.button('編集', type='secondary'):
        dia.on_rfl_edit()


def rfl_edit_button_off():
    if st.button('編集中', type='primary'):
        dia.off_rfl_edit()


def rfl_compare_button():
    if st.button("比較"):
        dia.compare_rfl()


def rfl_tree_button():
    if st.button("ツリー"):
        dia.choice_rfl()


# -----Telema-----

# telema-kyaw start
def make_update_button(i):
    if st.button("反映", type='secondary', key=f'update_btn{i}'):
        dia.choice_rfl()


def make_rfl_edit_on_button(i):
    if st.button('編集', type='secondary', key=f'edit_btn{i}'):
        dia.on_rfl_edit()


def make_rfl_edit_off_button(i):
    if st.button('編集中', type='primary', key=f'editing_btn{i}'):
        dia.off_rfl_edit()


def make_rfl_compare_button(i):
    if st.button("比較", key=f'compare_btn{i}'):
        dia.compare_rfl()


def make_rfl_tree_button(i):
    if st.button("ツリー", key=f'tree_btn{i}'):
        st.session_state.tree_view = True
        st.rerun()
def make_rfl_download_button(key_no):
    """階層繋がりグリッドダウンロードボタン

    Args:
        key_no (string): ユニークキー
    """
    init_session_state('rfl_excel_data')
    # if not st.session_state.rfl_grid_download_ready:
    if "rfl_grid_download_ready" not in st.session_state:
        if st.button('ダウンロードデータ作成'):
            with st.spinner("データを準備中です"):
                excel_data = create_rfl_grid_excel_data()
                st.session_state.rfl_excel_data = excel_data
                st.session_state.rfl_grid_download_ready = True
                st.rerun()
    else:
        with st.container():
            clicked = st.download_button(
                label="ダウンロード",
                data=st.session_state.rfl_excel_data,
                file_name=f"RFL_XXXX_{st.session_state.wp[0]}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f'download_btn{key_no+1}')
            msg = st.empty()
            msg.success('ダウンロードが可能になりました。')
            if clicked:
                st.session_state.rfl_grid_download_ready = False
                st.rerun()

# -----Telema-----
# RFLプルダウン更新
# Created: 2025/02/18
# 一旦単独選択の実装とする
def make_rfl_refresh_button(disable):
    """メタ情報変更更新ボタン

    Args:
        key_no (_type_): for 文で生成するナンバー
    """
    if st.button("更新", key=f'refresh_btn', disabled=disable):
        pj_code = st.session_state.selectoption1
        phase = st.session_state.selected_meta['phase']
        hierarchy_list = st.session_state.selected_meta['hierarchy']
        wp_list = st.session_state.selected_meta['wp']
        print(hierarchy_list)
        st.session_state['selectoption5'] = phase
        st.session_state['hierarchy'] = hierarchy_list
        st.session_state['selected_hr'] = hierarchy_list  # telema-kyaw feedback
        st.session_state['wp'] = wp_list

        df = rflq.posgre_get_rfl_tlm(
            st.session_state['selectoption1'],
            st.session_state['selectoption2'],
            st.session_state['selectoption3'],
            st.session_state['selectoption4'],
            st.session_state['selectoption5'],
            st.session_state['hierarchy'],
            st.session_state['wp'],
        )
        st.session_state.rfl_list = df

        rfl_all_info = rflq.posgre_get_rfl(
            st.session_state['selectoption1'],
            st.session_state['selectoption2'],
            st.session_state['selectoption3'],
            st.session_state['selectoption4'],
            st.session_state['selectoption5']
        )
        st.session_state.rfl_matrix = rfl_all_info

        st.rerun()


# -----Telema-----
# telema-kyaw end

# kyaw-tree
init_session_state('tree_view')
if int(st.session_state['chosen_id']) == 4:
    if st.session_state.tree_view == True:
        init_session_state('detail_flag')
        st.switch_page('pages/rfl_tree_page.py')


def rfl_matrix_button():  # 山口　マトリックス表示機能　必要な変数をsession_stateに格納しページ遷移 2/13
    if st.button("T/O"):
        st.switch_page("pages/RFL_matrix.py")


def rfl_update_approval():
    if st.button('承認/取り消し'):
        # columns_to_check = [
        #     'c_sender_selected', 's_sender_selected', 'u_sender_selected',
        #     'c_receiver_selected', 's_receiver_selected', 'u_receiver_selected'
        # ]
        # hierarchy = st.session_state.selected_hr
        hierarchy = st.session_state.tmp_hr

        if hierarchy == '車両': prefix = 'c_'
        if hierarchy == 'システム': prefix = 's_'
        if hierarchy == 'ユニット': prefix = 'u_'
        columns_to_check = [
            f'{prefix}sender_selected', f'{prefix}receiver_selected'
        ]
        # Filter items from session_state that are DataFrames and match the prefix
        filtered_items = {
            key: value for key, value in st.session_state.items()
            if key.startswith('rfl_pj_response_') and isinstance(value, pd.DataFrame)
        }
        # Keep only rows with at least one True in the columns_to_check
        print(filtered_items.items())
        valid_items = {}
        for key, df in filtered_items.items():
            if all(col in df.columns for col in columns_to_check):
                mask = df[columns_to_check].any(axis=1)
                print("mask")
                print(mask)
                filtered_df = df[mask]
                if not filtered_df.empty:
                    valid_items[key] = filtered_df

        # Define the selection columns with just the 'c', 's', 'u' `prefixes`
        selection_columns = [prefix]
        # Now sort the valid items by their key
        sorted_items = sorted(valid_items.items(), key=lambda x: x[0])
        output_rows = []
        sender_or_receiver = ''

        print("vaild_items")
        print(valid_items)

        print("sorted_items")
        print(sorted_items)

        if sorted_items:
            for key, df in sorted_items:
                for _, row in df.iterrows():
                    for prefix in selection_columns:
                        if row[f'{prefix}sender_selected'] and row[f'{prefix}receiver_selected']:
                            print('first:')
                            return dia.approve_sender_receiver_error('selected_both')
                        # Dynamically check if any of the selected flags are True
                        if row[f'{prefix}sender_selected'] or row[f'{prefix}receiver_selected']:

                            if row[f'{prefix}sender_selected']:
                                sender_or_receiver = 'sender'
                            elif row[f'{prefix}receiver_selected']:
                                sender_or_receiver = 'receiver'

                            # Check if prj_id, rfl_id, and phase_id are not None
                            prj_id = row[f'{prefix}r_pj_id']
                            rfl_id = row[f'{prefix}rfl_id']
                            phase_id = row[f'{prefix}phase_id']

                            if prj_id is not None and rfl_id is not None and phase_id is not None:
                                judge_value = row[f'{prefix}{sender_or_receiver}_judge']
                                if judge_value is None:
                                    judge_value = '承認済み'
                                    name_value = row[f'{prefix}{sender_or_receiver}_name']
                                    date_value = row[f'{prefix}{sender_or_receiver}_date']
                                    comment_value = row[f'{prefix}{sender_or_receiver}_comment']
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
                                    'r_wp': row[f'{prefix}r_wp'],
                                    f'{sender_or_receiver}_r_item': row[f'{prefix}r_item'],
                                    f'{sender_or_receiver}_req': row[f'{prefix}req'],
                                    f'{sender_or_receiver}_l_item': row[f'{prefix}l_item'],
                                    f'{sender_or_receiver}_logic': row[f'{prefix}logic'],
                                    f'{sender_or_receiver}_judge': judge_value,
                                    f'{sender_or_receiver}_name': name_value,
                                    f'{sender_or_receiver}_date': date_value,
                                    f'{sender_or_receiver}_comment': comment_value,
                                    f'{sender_or_receiver}_selected': row[f'{prefix}{sender_or_receiver}_selected'],
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
                if len(all_values) > 1:
                    return dia.approve_sender_receiver_error('diff_approve_selected')

                dia.rfl_approval_update_confirm(final_df, sender_or_receiver)
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
    total = len(gp_df)  # 山口　このトータルハCSUごとに定めないとだめ 階層によって行数が変わるから

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

    for field in fields:
        header = field.split('_')[0]
        rfl_id_col = header + '_rfl_id'
        total = len(gp_df[rfl_id_col].dropna())

        count = count_non_empty(gp_df[field])
        summary[f"{field}_count"] = f"{count}/{total}"
        prefix = field.rsplit('_judge', 1)[0]
        summary[f"{prefix}_percentage"] = f"{calculate_percent(count, total)}%"
    return summary


# telema-kyaw
def rfl_approval_summary(base_df_summary):
    # base_df_summary =base_df_summary.sort_values(by=['c_index','s_index','u_index'])
    base_df_summary = base_df_summary.sort_values(by=["project_code", "c_r_wp_summary_index"])
    # 山口　グルーピング前に、全RFLを新規追加したIndex列で並び変える 4/18
    base_df_summary = base_df_summary.sort_values(by=['c_index', 's_index', 'u_index'])

    # 05/12
    # Separate rows
    base_df_summary_c = base_df_summary[base_df_summary["c_r_wp_summary_index"].notna()].copy()
    base_df_summary_s = base_df_summary[base_df_summary["c_r_wp_summary_index"].isna()].copy()

    # Create a unified sort key column using available index
    base_df_summary_c["sort_index"] = base_df_summary_c["c_r_wp_summary_index"]
    base_df_summary_s["sort_index"] = base_df_summary_s["s_r_wp_summary_index"]

    # Combine both
    combined_df = pd.concat([base_df_summary_c, base_df_summary_s], ignore_index=True)

    # Sort by project_code first, then unified index
    # combined_df = combined_df.sort_values(by=["sort_index"]).drop(columns=["sort_index"])
    combined_df = combined_df.sort_values(by=["sort_index", 'c_index', 's_index', 'u_index'])
    base_df_summary = combined_df
    # Optional: display result
    # st.write("Final sorted DataFrame:", base_df_summary)

    for col in base_df_summary.columns:  # ここなんでループしているのかわからない
        group_df_summary = base_df_summary.groupby(['sort_index'])

    # チョー　05/09
    summary_data = []
    for key, gp_df in group_df_summary:
        row = gp_df.iloc[0]
        group_identifier = extract_group_identifier(row)
        summary_data.append(summarize_group(gp_df, group_identifier))

    # Convert to DataFrame
    summary_df = pd.DataFrame(summary_data)
    return summary_df


# telema-kyaw feedback
def selected_hr_wp():
    cols2 = st.columns([1, 1, 1, 1])
    with st.container():

        selected_meta = {
            'hierarchy': '',
            'phase': '',
            'wp': ''
        }

        # 選択肢は一つまで対応

        with cols2[0]:
            selected_phase = st.multiselect(
                'Phase',
                st.session_state.other_phase,
                placeholder='Phaseを指定',
                key=f'phase_select'
            )
            selected_meta['phase'] = selected_phase

        with cols2[1]:
            hierarchy_list = ['']
            if selected_meta['phase']:
                hierarchy_list = rflq.get_hierarchy(st.session_state.selectoption1, selected_meta['phase'])
            selected_hierarchy = st.multiselect(
                '階層',
                hierarchy_list,
                disabled=not selected_meta['phase'],
                placeholder='階層を指定' if selected_meta['phase'] else 'Phaseを先に指定してください',
                key=f'hierarchy_select'

            )
            selected_meta['hierarchy'] = selected_hierarchy

        with cols2[2]:
            wp_list = ['']
            if selected_meta['phase'] and selected_meta['hierarchy']:
                wp_list = rflq.get_wp(st.session_state.selectoption1, selected_meta['phase'],
                                      selected_meta['hierarchy'])

            selected_wp = st.multiselect(
                '領域',
                wp_list,
                disabled=not selected_meta['hierarchy'],
                placeholder='領域を指定' if selected_meta['hierarchy'] else '階層を先に指定してください',
                key=f'wp_select'
            )
            selected_meta['wp'] = selected_wp

        st.session_state.selected_meta = selected_meta

        with cols2[3]:
            disable = True
            if selected_wp:
                disable = False
            st.markdown("<div style='height: 1.7em;'></div>", unsafe_allow_html=True)
            make_rfl_refresh_button(disable)


# -----Telema-----
# RFLグリッド表示
# Created: 2025/02/04
if int(st.session_state['chosen_id']) == 4:
    # Ha-san added 0214
    searching_input_rfl_values, is_enough_rfl_input = get_session_choices(5)  # 山口　フェーズ情報を持ってくるように
    is_re_render_rfl = False
    st.session_state.rerun_rfl = False
    # ==========

    cols_btn = st.columns([5, 1, 1, 1, 2, 1, 1])

    if 'rfl_matrix' not in st.session_state or len(st.session_state.rfl_matrix) < 1 or st.session_state.dialog_state:
        rfl_all_info = sql.posgre_get_rfl(*searching_input_rfl_values[1:])
        st.session_state.rfl_matrix = rfl_all_info

    if 'rfl_matrix' in st.session_state and not st.session_state.rfl_matrix.empty:
        base_df_summary = st.session_state.rfl_matrix
        summary_df = rfl_approval_summary(base_df_summary)
        # Display in Streamlit
        # st.write('summary_df: ',summary_df)
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
        selected_hr_wp()

    if 'rfl_list' not in st.session_state or len(st.session_state.rfl_list) < 1 or st.session_state.dialog_state:
        # Ha-san added 0214
        if is_enough_rfl_input:
            # telema-kyaw
            required_keys = ['selected_hr', 'wp']
            if all(k in st.session_state and st.session_state[k] is not None for k in required_keys):
                try:
                    # telema-kyaw
                    # rfl_all_info = sql.posgre_get_rfl(*searching_input_rfl_values[1:])
                    # st.session_state.rfl_matrix = rfl_all_info

                    df1_rfl = rflq.posgre_get_rfl_tlm(
                        st.session_state['selectoption1'],
                        st.session_state['selectoption2'],
                        st.session_state['selectoption3'],
                        st.session_state['selectoption4'],
                        st.session_state['selectoption5'],
                        st.session_state['selected_hr'],
                        st.session_state['wp'],
                    )
                    if df1_rfl is not None and not df1_rfl.empty:  # チョー 03/10
                        st.session_state.rfl_list = df1_rfl
                        is_re_render_sim = True
                        st.session_state.rerun_rfl = True
                    else:
                        st.error(f'PRJを選択してください。')
                        st.image(co.inf_img, use_column_width=True)
                    # st.rerun()
                except Exception as e:
                    raise e
                    print('print exception', e)
                    st.error(f'PRJを選択してください。')
                    st.image(co.inf_img, use_column_width=True)
                    is_re_render_rfl = False
            else:
                st.error(f'フェーズ、階層、性能を選択してください。')
                st.image(co.inf_img, use_column_width=True)
        elif not st.session_state.login_begin:  # チョー 03/10
            st.error(f'PRJを選択してください。')
            st.image(co.inf_img, use_column_width=True)

    else:
        is_re_render_rfl = True
        # ==========
    if is_re_render_rfl and not st.session_state.login_begin:  # チョー 03/10
        init_session_state('rfl_edit_state')
        # Pattern 1~2
        base_df = st.session_state.rfl_list
        # go = gop.create_gridop_rfl_list()
        base_df_summary = st.session_state.rfl_matrix  # telema-kyaw


        # pattern 1~2

        def render_aggrid(go, df):
            edit = AgGrid(
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
            group_df = df.groupby(['project_code', 'c_r_wp', 'lot'])
            data = []
            cols = st.columns([4, 1, 1, 1, 1, 1])  # 山口　マトリックス表示用のボタン追加 2/13

            with cols[1]:
                rfl_update_button()
            # with cols[2]:
            # rfl_edit_button()
            with cols[3]:
                rfl_compare_button()
            with cols[4]:
                rfl_tree_button()
            with cols[5]:
                rfl_matrix_button()  # 山口　マトリックス表示ファンクション 2/13
            # st.write('gp_df T: ', group_df)
            for i, (key, df) in enumerate(group_df):
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
                f'DF_{key1}_{key2}_{key3}': df for (key1, key2, key3), df in group_df
            }

            pd.set_option("display.max_rows", None)  # すべての行を表示
            pd.set_option("display.max_columns", None)  # すべての列を表示            
            # print(grouped_dfs)

            render_aggrid(go, df)


        elif st.session_state['compare_click'] is not True:
            # telema-kyaw
            hierarchy = st.session_state.tmp_hr
            print(hierarchy)
            if hierarchy == '車両': prefix = 'c_'
            if hierarchy == 'システム': prefix = 's_'
            if hierarchy == 'ユニット': prefix = 'u_'

            # pattern 3
            base_df = base_df.sort_values(by=["project_code", f"{prefix}r_wp_id"])

            df_org = base_df.copy()
            prefixes = ['c_', 's_', 'u_']
            # 関数化失敗
            cols = RFLGridConfig.get_value()
            # base_df
            # 後ほど関数化

            # to avoid same Ritems to appear in separated rows, sort them
            # just applied to car RFL only for now, further modifing could be needed idk
            #
            requirement_unique = base_df[f'{prefix}r_item'].drop_duplicates().tolist()
            requirement_map = {}
            for i, req in enumerate(requirement_unique):
                requirement_map[req] = i
            base_df[f'{prefix}r_item_index'] = base_df[f'{prefix}r_item'].map(requirement_map)

            # 山口　グルーピング前に、全RFLを新規追加したIndex列で並び変える 4/18　この並び替え列は、重複消し処理の前にやらなければならないため位置移動 6/18
            base_df = base_df.sort_values(by=[f'{prefix}index'])
            st.write(base_df)
            base_df.loc[base_df[f'{prefix}r_item'] == base_df[f'{prefix}r_item'].shift(), f'{prefix}r_item'] = ''
            base_df.loc[base_df[f'{prefix}r_unit'] == base_df[f'{prefix}r_unit'].shift(), f'{prefix}r_unit'] = ''
            mask_r_scene = base_df[f'{prefix}r_scene'] == base_df[f'{prefix}r_scene'].shift()

            base_df.loc[
                (base_df[f'{prefix}r_item'].isna() | (base_df[f'{prefix}r_item'] == '')) & mask_r_scene,
                f'{prefix}r_scene'
            ] = ''

            base_df.loc[base_df[f'{prefix}f_item'] == base_df[f'{prefix}f_item'].shift(), f'{prefix}f_item'] = ''
            base_df.loc[base_df[f'{prefix}f_unit'] == base_df[f'{prefix}f_unit'].shift(), f'{prefix}f_unit'] = ''

            base_df.loc[base_df[f'{prefix}l_item'] == base_df[f'{prefix}l_item'].shift(), f'{prefix}l_item'] = ''
            # base_df.loc[base_df[f'{prefix}l_unit'] == base_df[f'{prefix}l_unit'].shift(),f'{prefix}l_unit'] = ''

            mask_l_scene = base_df[f'{prefix}l_scene'] == base_df[f'{prefix}l_scene'].shift()

            # Check if l_item is not None (or NaN) and both masks are True
            base_df.loc[
                (base_df[f'{prefix}l_item'].isna() | (base_df[f'{prefix}l_item'] == '')) & mask_l_scene,
                f'{prefix}l_scene'
            ] = ''

            if 'meta_info_disp' not in st.session_state:
                st.session_state.meta_info_disp = False

            with cols_btn[1]:
                make_update_button(i)
            with cols_btn[2]:
                if st.session_state.rfl_edit_state is False or st.session_state.rfl_edit_state == []:
                    make_rfl_edit_on_button(i)
                elif st.session_state.rfl_edit_state:
                    make_rfl_edit_off_button(i)
            with cols_btn[3]:
                make_rfl_compare_button(i)
            with cols_btn[4]:
                # make_rfl_tree_button(i)
                make_rfl_download_button(i)
            with cols_btn[5]:
                rfl_matrix_button()
            with cols_btn[6]:
                rfl_update_approval()

            for col in base_df.columns:
                group_df = base_df.groupby(['project_code', 'archi', 'lot', 'phase', 'hierarchy', 'wp'])
            data = []
            for i, (key, df) in enumerate(group_df):
                go = gop.create_gridop_rfl_list()
                header_html = f"""
                <div style="width: 400px; height: 140px;margin-left: 0;">
                <style>
                    .custom-header {{
                        font-weight: bold;
                        # background-color: #FFFFFF;
                        background-color: #FFFFFF;
                        display: flex;
                        justify-content: left;
                        width: 100px;
                    }}
                    .custom-header table {{
                        border-collapse: collapse;
                        table-layout: fixed;
                        # background-color: #FFFFFF;
                        # background-color: #e0ffff;
                        background-color: #000000;
                        padding-top: 10px;
                        width: 100px;
                    }}
                    .custom-header th,.custom-header td {{
                        border: 1px solid #ccc;
                        padding: 1px;
                        text-align: center;
                        font-size: 10px;
                        width: 80px;
                        height: 40px;
                        background-color: #FFFFFF;
                    }}
                    .custom-header th{{
                        background-color: #4682B4;
                    }}
                </style>

                <div class="custom-header">
                    <table>
                        <table>
                            <tr>
                                <th>Project</th>
                                <td>{key[0]}</td>
                            </tr>
                            <tr>
                                <th>PTタイプ</th>
                                <td>{key[1]}</td>
                            </tr>
                        </table>
                        <table>
                            <tr>
                                <th>lot</th>
                                <td>{key[2]}</td>
                            </tr>
                            <tr>
                                <th>階層</th>
                                <td>{key[4]}</td>
                            </tr>
                        </table>
                        <table>
                            <tr>
                                <th>性能</th>
                                <td>{key[5]}</td>
                            </tr>
                            <tr>
                                <th>フェーズ</th>
                                <td>{key[3]}</td>
                            </tr>
                        </table>
                    </table>
                </div>
                """
                st.markdown(header_html, unsafe_allow_html=True)

                st.session_state[f'org_rfl_pj_{i}'] = df
                st.session_state[f'rfl_pj_response_{i}'] = render_aggrid_rfl(go, df, i)

# telema-kyaw
# -----Telema-----
# RFLセル変更状況リフレッシュ
# Created: 2025/02/19
init_session_state('edit_refresh')
if st.session_state.edit_refresh:
    st.session_state.edit_refresh = False
    st.rerun()
# -----Telema-----        

# チョー 02/26
if st.session_state.rerun_rfl:
    # print("rerun rfl")
    st.session_state.rerun_rfl = False
    st.rerun()

# チョー　追加 03/10
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
    col1, col2, col3, col4, col5 = st.columns([3, 3, 3, 3, 7])
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
