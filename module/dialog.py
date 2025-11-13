import streamlit as st
import pandas as pd
import const.constpara as co
from Aras_connect.Middle import IFtoARAS
import module.grid_option as gop
from st_aggrid import AgGrid, JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder
import json
from module.PsqlModule import psql_class
import time #チョー #10/28
import datetime #山口 現在時刻が欲しかったため追加 11/14
import yaml #チョー #10/28
from psycopg2 import sql as psql#11/19
from streamlit_free_text_select import st_free_text_select
import yaml # 山口　なぜかYAMLインポートできていなかったため追加12/26
import plotly.graph_objects as graph #山口　時系列可視化にplotly使用 1/31
import module.mail_send as mail
from module.utils import init_session_state, get_matching_key
from module.data_processing import RFLDataProcesser


option_keys = ['selectoption1', 'selectoption2', 'selectoption3']
option_keys2 = ['selectoption1', 'selectoption2', 'selectoption3', 'selectoption4', 'selectoption5']
# option_keys3 = ['selectoption1', 'selectoption2', 'selectoption3', 'selectoption4', 'selectoption5', 'selectoption6']#ヤマグチ　sim用に使う 12/1
option_keys3 = ['selectoption1', 'selectoption2', 'selectoption3', 'selectoption4', 'selectoption5']#チョー　共通用に使う 03/10
# Telema RFL用オプション作成
option_keys4 = ['selectoption1', 'selectoption2', 'selectoption3','selectoption4']
noData = ["-","－","﹣","‐","⁃­","‑","−","˗","‒","–","—","﹘","―","⎯","⏤","─","ｰ","ー","一"] 

with open(co.css, encoding='utf-8') as f:
    css = f.read()

with open(co.css_ag, encoding='utf-8') as f:
    css_ag = json.load(f)

# CSSをStreamlitに適用
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

if 'username' not in st.session_state or 'password' not in st.session_state:
    st.switch_page("app.py")
else:
    username = st.session_state.username
    password = st.session_state.password

#aras = IFtoARAS(username, password, co.ARASURL, co.ARASDB)
sql = psql_class()

@st.dialog("Project")
def choice_se():
    if 'selectoption1' not in st.session_state:
        st.session_state['selectoption1'] = []
    z_model_code = sql.get_project("z_model_code")
    selectoption1 = st.multiselect(
        'プロジェクト:',
        z_model_code,
        key='unique_key_1',
        default=st.session_state['selectoption1'],
    )
    st.session_state['selectoption1'] = selectoption1
    # マルチセレクト２、、１と同じ流れ
    if 'selectoption2' not in st.session_state:
        st.session_state['selectoption2'] = []
    destination = sql.get_project("destination",selectoption1)
    if destination != st.session_state['selectoption2']:
        st.session_state['selectoption2'] = []
    
    selectoption2 = st.multiselect(
        '仕向け:',
        destination,
        key='unique_key_2',
        default=st.session_state['selectoption2'],
    )
    st.session_state['selectoption2'] = selectoption2
    if 'selectoption3' not in st.session_state:
        st.session_state['selectoption3'] = []
    drive_system = sql.get_project("drive_system",selectoption1,selectoption2)
    if drive_system != st.session_state['selectoption3']:
        st.session_state['selectoption3'] = []
        
    selectoption3 = st.multiselect(
        '駆動方式:',
        drive_system,
        key='unique_key_3',
        default=st.session_state['selectoption3'],
    
    )
    st.session_state['selectoption3'] = selectoption3

    if all(st.session_state[key] for key in option_keys):
        project_number = sql.get_project("project_number",
                                         st.session_state['selectoption1'],
                                         st.session_state['selectoption2'],
                                         st.session_state['selectoption3']) 
        st.session_state['project_number'] = project_number
        if 'selectoption4' not in st.session_state:
            st.session_state['selectoption4'] = []
        project_lot = sql.get_project("project_lot",project_number)
        if project_lot != st.session_state['selectoption4']:
            st.session_state['selectoption4'] = []
        selectoption4 = st.multiselect(
            'ロット:',
            project_lot,
            key='unique_key_4',
            default=st.session_state['selectoption4'],
        )
        st.session_state['selectoption4'] = selectoption4
        
        if 'selectoption5' not in st.session_state:
            st.session_state['selectoption5'] = []
        phase_list = sql.get_project("phase_list",project_number,selectoption4)
        if phase_list != st.session_state['selectoption5']:
            st.session_state['selectoption5'] = []
        selectoption5 = st.multiselect(
            'フェーズ:',
            phase_list,
            key='unique_key_5',
            default=st.session_state['selectoption5'],
        )
        st.session_state['selectoption5'] = selectoption5
        st.markdown('<span id="button-right"></span>', unsafe_allow_html=True)
        if st.button("完了"):
            if all(st.session_state[key] for key in option_keys2):
                df1,df2=sql.posgre_get_date(project_number,selectoption4,selectoption5)
                st.session_state.prj_info_list = df1
                st.session_state.se_data_stuck = df2
                #山口　デバック
                df1
                df2
                st.rerun()
            else:
                st.error('全て選択してくださぃ！！', icon="🚨")
    st.session_state.chosen_id = 1

@st.dialog("条件選択")     
def choice_r():
    st.write("Rリストはまだ設定されていない")
    st.session_state.chosen_id = 2
@st.dialog("条件選択")
def choice_sim():#山口　SIM用ダイアログ実装　12/1　新ダイアログに対応させる 12/10  
    if 'architecture_name' not in st.session_state:
        st.session_state['architecture_name'] = []
        st.session_state['selectoption1'] = []
    architecture_list = sql.get_project("architecture_name")
    selected_archi = st.multiselect(
        'PTシステムタイプ',
        architecture_list,
        key ='select_archi_unique_key',
        default = st.session_state['architecture_name']
    )
    st.session_state['architecture_name'] = selected_archi
    if 'selectoption1' not in st.session_state or len(selected_archi) <= 0:
        st.session_state['selectoption1'] = []
    # z_model_code = sql.get_project("z_model_code")
    z_model_code = sql.get_project("z_model_code",selected_archi)
    selectoption1 = st.multiselect(
        'プロジェクト:',
        z_model_code,
        key='unique_key_1',
        default=st.session_state['selectoption1'],
    )
    st.session_state['selectoption1'] = selectoption1
    # マルチセレクト２、、１と同じ流れ
    if 'selectoption2' not in st.session_state:
        st.session_state['selectoption2'] = []
    destination = sql.get_project("destination",selectoption1)

    if destination != st.session_state['selectoption2']:
        st.session_state['selectoption2'] = []
    
    selectoption2 = st.multiselect(
        '仕向け:',
        destination,
        key='unique_key_2',
        default=st.session_state['selectoption2'],
    )
    st.session_state['selectoption2'] = selectoption2
    if 'selectoption3' not in st.session_state:
        st.session_state['selectoption3'] = []
    drive_system = sql.get_project("drive_system",selectoption1,selectoption2)
    if drive_system != st.session_state['selectoption3']:
        st.session_state['selectoption3'] = []
        
    selectoption3 = st.multiselect(
        '駆動方式:',
        drive_system,
        key='unique_key_3',
        default=st.session_state['selectoption3'],
    
    )
    st.session_state['selectoption3'] = selectoption3

    if all(st.session_state[key] for key in option_keys):
        project_number = sql.get_project("project_number",
                                        st.session_state['selectoption1'],
                                        st.session_state['selectoption2'],
                                        st.session_state['selectoption3']) 
        st.session_state['project_number'] = project_number
        if 'selectoption4' not in st.session_state:
            st.session_state['selectoption4'] = []
        project_lot = sql.get_project("project_lot",st.session_state['selectoption1'],
                                        st.session_state['selectoption2'],st.session_state['selectoption3'])
        if project_lot != st.session_state['selectoption4']:
            st.session_state['selectoption4'] = []
        selectoption4 = st.multiselect(
            'ロット:',
            project_lot,
            key='unique_key_4',
            default=st.session_state['selectoption4'],
        )
        st.session_state['selectoption4'] = selectoption4
        
        if 'selectoption5' not in st.session_state:
            st.session_state['selectoption5'] = []
        phase_list = sql.get_project("phase_list",
                                        st.session_state['selectoption1'],
                                        st.session_state['selectoption2'],
                                        st.session_state['selectoption3'],
                                        st.session_state['selectoption4'])
        if phase_list != st.session_state['selectoption5']:
            st.session_state['selectoption5'] = []
        selectoption5 = st.multiselect(
            'フェーズ:',
            phase_list,
            key='unique_key_5',
            default=st.session_state['selectoption5'],
        )
        st.session_state['selectoption5'] = selectoption5
        
        #チョー バリエーション選択不要にする 03/10
        # #バリエーション選択用にselection6の追加
        # if 'selectoption6' not in st.session_state:
        #     st.session_state['selectoption6'] = []
        # variation_list = sql.get_project('variation_list', selectoption1,selectoption3, selectoption4, selectoption5)
        # if variation_list != st.session_state['selectoption6']:
        #     st.session_state['selectoption6'] = []
        # selectoption6 = st.multiselect(
        #     'バリエーション:',
        #     variation_list,
        #     key='unique_key_6',
        #     default=st.session_state['selectoption6']
        #     )
        # st.session_state['selectoption6'] = selectoption6
        #st.write(selectoption6)
        st.markdown('<span id="button-right"></span>', unsafe_allow_html=True)
        if st.button("完了"):
            if all(st.session_state[key] for key in option_keys3):
                # df1,df2=sql.posgre_get_data_sim(selectoption1, selectoption2, selectoption3, selectoption4,selectoption5, selectoption6)#山口　SEとは違い、プロジェクトコードだけではどのシナリオか完全に識別できない、仕向けと駆動方式も飛ばすように変更 2/13
                df1,df2=sql.posgre_get_data_sim(selectoption1, selectoption2, selectoption3, selectoption4,selectoption5) #チョー バリエーション選択不要にする 03/10

                st.session_state.sim_prj_info_list = df1
                st.session_state.sim_data_stuck = df2
                #山口　デバック
                df1
                df2
                st.rerun()
            else:
                st.error('全て選択してくださぃ！！', icon="🚨")
    #st.write("SIM管理表はまだ設定されていない")
    st.session_state.chosen_id = 3
    
        # if 'selectoption1' not in st.session_state:
        #     st.session_state['selectoption1'] = []
        # z_model_code = sql.get_project("z_model_code")
        # selectoption1 = st.multiselect(
        #     'プロジェクト:',
        #     z_model_code,
        #     key='unique_key_1',
        #     default=st.session_state['selectoption1'],
        # )
        # st.session_state['selectoption1'] = selectoption1
        # # マルチセレクト２、、１と同じ流れ
        # if 'selectoption2' not in st.session_state:
        #     st.session_state['selectoption2'] = []
        # destination = sql.get_project("destination",selectoption1)
        # if destination != st.session_state['selectoption2']:
        #     st.session_state['selectoption2'] = []
        
        # selectoption2 = st.multiselect(
        #     '仕向け:',
        #     destination,
        #     key='unique_key_2',
        #     default=st.session_state['selectoption2'],
        # )
        # st.session_state['selectoption2'] = selectoption2
        # if 'selectoption3' not in st.session_state:
        #     st.session_state['selectoption3'] = []
        # drive_system = sql.get_project("drive_system",selectoption1,selectoption2)
        # if drive_system != st.session_state['selectoption3']:
        #     st.session_state['selectoption3'] = []
            
        # selectoption3 = st.multiselect(
        #     '駆動方式:',
        #     drive_system,
        #     key='unique_key_3',
        #     default=st.session_state['selectoption3'],
        
        # )
        # st.session_state['selectoption3'] = selectoption3

        # if all(st.session_state[key] for key in option_keys):
        #     project_number = sql.get_project("project_number",
        #                                     st.session_state['selectoption1'],
        #                                     st.session_state['selectoption2'],
        #                                     st.session_state['selectoption3']) 
        #     st.session_state['project_number'] = project_number
        #     if 'selectoption4' not in st.session_state:
        #         st.session_state['selectoption4'] = []
        #     project_lot = sql.get_project("project_lot",project_number)
        #     if project_lot != st.session_state['selectoption4']:
        #         st.session_state['selectoption4'] = []
        #     selectoption4 = st.multiselect(
        #         'ロット:',
        #         project_lot,
        #         key='unique_key_4',
        #         default=st.session_state['selectoption4'],
        #     )
        #     st.session_state['selectoption4'] = selectoption4
            
        #     if 'selectoption5' not in st.session_state:
        #         st.session_state['selectoption5'] = []
        #     phase_list = sql.get_project("phase_list",project_number,selectoption4)
        #     if phase_list != st.session_state['selectoption5']:
        #         st.session_state['selectoption5'] = []
        #     selectoption5 = st.multiselect(
        #         'フェーズ:',
        #         phase_list,
        #         key='unique_key_5',
        #         default=st.session_state['selectoption5'],
        #     )
        #     st.session_state['selectoption5'] = selectoption5
            
        #     #バリエーション選択用にselection6の追加
        #     if 'selectoption6' not in st.session_state:
        #         st.session_state['selectoption6'] = []
        #     variation_list = sql.get_project('variation_list', project_number, selectoption4, selectoption5)
        #     if variation_list != st.session_state['selectoption6']:
        #         st.session_state['selectoption6'] = []
        #     selectoption6 = st.multiselect(
        #         'バリエーション:',
        #         variation_list,
        #         key='unique_key_6',
        #         default=st.session_state['selectoption6']
        #         )
        #     st.session_state['selectoption6'] = selectoption6
        #     st.write(selectoption6)
        #     st.markdown('<span id="button-right"></span>', unsafe_allow_html=True)
        #     if st.button("完了"):
        #         if all(st.session_state[key] for key in option_keys3):
        #             df1,df2=sql.posgre_get_data_sim(selectoption1,selectoption4,selectoption5, selectoption6)
        #             st.session_state.sim_prj_info_list = df1
        #             st.session_state.sim_data_stuck = df2
        #             #山口　デバック
        #             df1
        #             df2
        #             st.rerun()
        #         else:
        #             st.error('全て選択してくださぃ！！', icon="🚨")
        # #st.write("SIM管理表はまだ設定されていない")
        # st.session_state.chosen_id = 3
@st.dialog("条件選択",width="large")
def choice_rfl():
    st.write("RFL条件はまだ設定されていない")
    st.session_state.chosen_id = 3

@st.dialog("正常終了")
def success_dia():
    st.success("正常に変更が完了しました。")
    if st.button('OK'):
        st.rerun()

@st.dialog("異常終了")
def error_dia():
    st.error("変更に失敗しました。管理者に問い合わせてください。")
    st.write('管理者:○○')

@st.dialog("変更確認",width="large")
def updata_conf_dia():
    st.write("下記データを選択しました。最終確認を行ってください。")#山口　編集方法変更に伴い文言を変えた　10/25
    st.write("本当に変更する場合、「実行」ボタンを押下してください。")
    go = gop.update_conf_go()
    st.session_state.Prj_updata = AgGrid(
           st.session_state.updata_conf_dia_result,
           custom_css=css_ag,
           gridOptions=go,
           reload_data=False,
           height=220,
            )

    if st.button("実行"):
        # st.session_state.update_chk_conf = st.session_state.Prj_updata["selected_rows"] #チョー　#10/23　課題リスト#24番 
        
        # if st.session_state.update_chk_conf is None: #変更する行がチェックされない場合
        #     no_check()
        # elif 'update_chk_conf' in st.session_state and (
        #     'state_name' not in st.session_state.update_chk_conf.columns or #ステータスが選択されない場合
        #     'user_memo' not in st.session_state.update_chk_conf.columns #メモが記入されない場合
        # ) or st.session_state.update_chk_conf['state_name'].isnull().sum()>0 or st.session_state.update_chk_conf['user_memo'].isnull().sum()>0:
        #     st.session_state.update_chk_conf = None #チョー　#10/23　課題リスト#24番
        #     no_input()
        # else:
            
        #     mapping = {'机上設計値(フィジカルデータ無し)':0, '設計値①(一部フィジカルデータ含む机上検討値)': 1, '設計値②(フィジカルデータ)':2,' ':3}#山口　承認情報へそのまま文字が着てエラーになるのを避ける 書き換え
        #     st.session_state.update_chk_conf = st.session_state.Prj_updata["selected_rows"]
        #     st.session_state.update_chk_conf["state_name"] = st.session_state.update_chk_conf["state_name"].replace(mapping)
        #     st.rerun()

        #チョー　01/14 変更確認ダイアログでチェックボックス無しで変更する
        prj_data = st.session_state.Prj_updata['data']
        prj_df = pd.DataFrame(prj_data)
        mapping = {'0.机上設計値(フィジカルデータ無し)':0, '1.設計値(一部フィジカルデータ含む机上検討値)':1, '2.設計値(フィジカルデータ)':2, "3.スペック":3, '4.名称':4, '5.対象外':5, ' ':6}#山口　承認情報へそのまま文字が着てエラーになるのを避ける 書き換え　3/27書き換え書き換え
        prj_df['state_name'] = prj_df['state_name'].replace(mapping)
        st.session_state.update_chk_conf = prj_df
        st.rerun()

@st.dialog("更新確認",width="large")       
def updata_conf_dia_rlist():#山口　R用 1/29
    st.write("下記データを選択しました。最終確認を行ってください。")
    st.write("本当に更新する場合パラメータを選択しをし実行ボタンを押下してください。")
    go = gop.update_conf_go_rlist()
    st.session_state.Prj_updata = AgGrid(
           st.session_state.updata_conf_dia_result,
           custom_css=css_ag,
           gridOptions=go,
           reload_data=False,
           height=220,
            )
    if st.button("実行"):
        # st.session_state.update_chk_conf = st.session_state.Prj_updata["selected_rows"]
        
        # if st.session_state.update_chk_conf is None: #変更する行がチェックされない場合
        #     no_check()
        # #elif 'update_chk_conf' in st.session_state or st.session_state.update_chk_conf['state_name'].isnull().sum()>0 or st.session_state.update_chk_conf['user_memo'].isnull().sum()>0:
        # #    st.session_state.update_chk_conf = None #チョー　#10/23　課題リスト#24番
        # #    no_input()
        # else:

        #     st.session_state.update_chk_conf = st.session_state.Prj_updata["selected_rows"]

        #     st.rerun()

        #02/07 チョー　
        prj_data = st.session_state.Prj_updata['data']
        prj_df = pd.DataFrame(prj_data)
        st.session_state.update_chk_conf = prj_df
        st.rerun()

@st.dialog("更新確認",width="large")       
def updata_conf_dia_sim():#山口　sim用 12/2
    st.write("下記データを選択しました。最終確認を行ってください。")
    st.write("本当に更新する場合パラメータを選択しをし実行ボタンを押下してください。")
    go = gop.update_conf_go_sim()
    st.session_state.Prj_updata = AgGrid(
           st.session_state.updata_conf_dia_result,
           custom_css=css_ag,
           gridOptions=go,
           reload_data=False,
           height=220,
            )

    if st.button("実行"):
        st.session_state.update_chk_conf = st.session_state.Prj_updata["selected_rows"]
        
        if st.session_state.update_chk_conf is None: #変更する行がチェックされない場合
            no_check()
        #elif 'update_chk_conf' in st.session_state or st.session_state.update_chk_conf['state_name'].isnull().sum()>0 or st.session_state.update_chk_conf['user_memo'].isnull().sum()>0:
        #    st.session_state.update_chk_conf = None #チョー　#10/23　課題リスト#24番
        #    no_input()
        else:
            #山口　FIXEDとステータスの特例で、メモが入力されていないとアップデートさせない 1/31
            if (st.session_state.Prj_updata["selected_rows"]['senario_parameter_id'].values[0]==96 or st.session_state.Prj_updata["selected_rows"]['senario_parameter_id'].values[0]==98) :
                if (st.session_state.Prj_updata["selected_rows"]['user_memo'].values[0] is None or st.session_state.Prj_updata["selected_rows"]['user_memo'].values[0] ==''):
                    st.error('ステータス、FIXEDの編集はメモが必須入力です。')
                    st.session_state.update_chk_conf=None
                    return
                #山口　ここでFIXはステータスが入力されていないとできないとしたい 1/31
                elif st.session_state.Prj_updata["selected_rows"]['senario_parameter_id'].values[0]==98:
                    
                    project_id=st.session_state.Prj_updata["selected_rows"]['project_id'].values[0]
                    senario_parameter_id=96#ステータスを表すパラメータid
                    phase_id= st.session_state.Prj_updata["selected_rows"]['phase_id'].values[0]
                    phase= st.session_state.Prj_updata["selected_rows"]['phase'].values[0]
                    variation_id=st.session_state.Prj_updata["selected_rows"]['variation_id'].values[0]
                    variation=st.session_state.Prj_updata["selected_rows"]['variation'].values[0]
                    study_id=st.session_state.Prj_updata["selected_rows"]['study_id'].values[0]
                    df_ingrid=st.session_state.aggrid
                    b = str(project_id) + ';' #列名の最初についている文字列
                    a = ';' + phase[0]+phase[-1]+variation+study_id#列名の最後についている文字列
                    if df_ingrid[df_ingrid[b+'project_id'+a]==project_id][df_ingrid[b+'senario_parameter_id'+a]==senario_parameter_id][df_ingrid[b+'phase_id'+a]==phase_id][df_ingrid[b+'variation_id'+a]==variation_id][df_ingrid[b+'study_id'+a]==study_id][b+'value'+a].values[0] is None or df_ingrid[df_ingrid[b+'project_id'+a]==project_id][df_ingrid[b+'senario_parameter_id'+a]==senario_parameter_id][df_ingrid[b+'phase_id'+a]==phase_id][df_ingrid[b+'variation_id'+a]==variation_id][df_ingrid[b+'study_id'+a]==study_id][b+'value'+a].values[0] == '':
                        st.error('FIXEDを変更するにはステータスを先に変更しておく必要があります。')
                        st.session_state.update_chk_conf=None
                        return
                    
                       

                   


            
            st.session_state.update_chk_conf = st.session_state.Prj_updata["selected_rows"]

            st.rerun()

def no_check():
    st.error("変更する行をチェックしてください。")

def no_input():
    st.error("ステータスを選択してメモを記入してください。")

@st.dialog("選択エラー")
def data_none():
    st.error("データが選択されていません。")#山口　編集方法変更に伴い文言を変えた　10/25

#チョー　変更情報なしで「変更」ボタンを押すとき、エラーメッセージ表示ダイアログ　04/24
@st.dialog("情報変更エラー")
def data_no_change():
    st.error("変更された情報がありません。")

@st.dialog("条件を選択してください")
def AGdata_none():
    st.error("条件が選択されていない")
    
@st.dialog("更新キャンセル")
def update_cancel():
    st.error("更新ダイアログでチェックがされなかったので更新をキャンセルしました。")

def file_name(fileId):
    file_nm= aras.get_fileName_id(fileId)
    return file_nm

@st.dialog("MAP")
def file_download():
    st.error("プロジェクトが選択されていない。まず条件から選んでください") #チョー　＃10/29　Project→プロジェクトに変更する

#チョー #関数追加 #10/25 課題リスト17番    
@st.dialog("MAP確認")
def map_multiselected(selected_proj):
    confirmed_proj = st.multiselect("複数のプロジェクトが選択されています。どれをMAPするか確認してください。", selected_proj, default=selected_proj)
    if st.button("確認"):
    	#プロジェクトが選択されるかをチェックする
        if not confirmed_proj:   
            st.error("MAPするには、少なくとも1つのプロジェクトを選択してください。")
        else:
            import pages.SPDM_LIST as spdm_list
            for item in confirmed_proj:
                variable_name = spdm_list.get_map_link(item)
                open_link = getattr(co, variable_name, None)
                print('open link: ', open_link)
                if open_link:
                    st.components.v1.html(
                        f"""
                        <script>
                            window.open('{open_link}', '_blank');
                        </script>
                        """,
                        height=0,
                    )
                time.sleep(0.5)    
            spdm_list.st.session_state.map_click = True
            st.rerun()   # ダイアログを閉じる
 
@st.dialog("No URL")#山口　マップURLが設定されていないと起用ダイアログ 11/4
def URL_none(selected_row):
    st.error(selected_row['z_prj_number'] + ' ' + selected_row['z_parent_paraitem'] + ' ' + selected_row['z_child_paraitem'] + ' ' + selected_row['z_wp_name_get_str'] + "に紐づくMapURLがありません。")

# @st.dialog("プロジェクト選択", width='large') #山口　ブックマーク用ダイアログ10/28
# def choice_se_bookmark():
#     # st.session_state['compare_click'] = False
#     df_bookmarks = sql.get_bookmarks(st.session_state.username)#get bookmark info
#     print(df_bookmarks)
    
#     df_transformed = df_bookmarks.groupby('bookmark_number').apply(
#         lambda x: pd.Series({
#             'bookmark_number': x['bookmark_number'].iloc[0],
#             'value': '; '.join(x['value'].tolist())
#         })
#     ).reset_index(drop=True)

#     print(df_transformed)
#     keys = df_transformed['bookmark_number']#山口　ここはKEY取得方法カエタ！！！！！11/7
#     values = df_transformed['value']
#     selectables = dict(zip(keys,values))
#     print(selectables) 
#     next_bookmark=max(keys)+1
    
#     col1, col2 = st.columns([5, 5])
#     with col2:
#         if 'bookmark_selection' not in st.session_state:
#             st.session_state['bookmark_selection'] = 0
#         bookmark_selection = st.selectbox(
#             'お気に入り条件:',
#             list(selectables.values()),
#             key='bookmark_key_1',
#             index=0
#         )
#         #st.write(bookmark_selection)
#         st.session_state['bookmark_selection'] = [k for k, v in selectables.items() if v==bookmark_selection][0]
#         selected_number = st.session_state['bookmark_selection']
#         print("selected id: " + str(selected_number))
#         col21,col22 = st.columns([2,2])
#         with col21:
#             if st.button("お気に入りで表示") :
#                 if selected_number >0:
#                     st.session_state['selectoption1'] = df_bookmarks[(df_bookmarks['bookmark_number']==selected_number) & (df_bookmarks['category']==1)]['value'].tolist()
#                     st.session_state['selectoption2'] = df_bookmarks[(df_bookmarks['bookmark_number']==selected_number) & (df_bookmarks['category']==2)]['value'].tolist()
#                     st.session_state['selectoption3'] = df_bookmarks[(df_bookmarks['bookmark_number']==selected_number) & (df_bookmarks['category']==3)]['value'].tolist()
#                     project_number = sql.get_project("project_number",
#                                                      st.session_state['selectoption1'],
#                                                      st.session_state['selectoption2'],
#                                                      st.session_state['selectoption3']) 
#                     st.session_state['project_number'] = project_number
#                     st.session_state['selectoption4'] = df_bookmarks[(df_bookmarks['bookmark_number']==selected_number) & (df_bookmarks['category']==4)]['value'].tolist()
#                     st.session_state['selectoption5'] = df_bookmarks[(df_bookmarks['bookmark_number']==selected_number) & (df_bookmarks['category']==5)]['value'].tolist()
#                     selectoption4 = st.session_state['selectoption4']
#                     selectoption5 = st.session_state['selectoption5']
#                     print(project_number)
#                     print(selectoption4)
#                     df1,df2=sql.posgre_get_date(st.session_state['selectoption1'],
#                                         st.session_state['selectoption2'],
#                                         st.session_state['selectoption3'],
#                                         st.session_state['selectoption4'],
#                                         st.session_state['selectoption5'])
#                     st.session_state.prj_info_list = df1
#                     st.session_state.se_data_stuck = df2
#                     #山口　デバック
#                     df1
#                     df2
#                     st.session_state['compare_click'] = False #チョー 11/25 
#                     st.rerun()
#                 else:
#                     st.error("お気に入り条件が選択されていません")
#         with col22:
#             if st.button("お気に入りを削除"):
#                 if selected_number>0:
#                     sql.delete_bookmark(selected_number, st.session_state.username)
#                     st.write("お気に入りを削除しました")
#                     time.sleep(1)
#                     st.rerun()
#                 else:
#                     st.error("お気に入り条件が選択されていません") 
#     with col1:
#         if 'architecture_name' not in st.session_state:
#             st.session_state['architecture_name'] = []
#             st.session_state['selectoption1'] = []
#         architecture_list = sql.get_project("architecture_name")
#         selected_archi = st.multiselect(
#             'PTシステムタイプ',
#             architecture_list,
#             key ='select_archi_unique_key',
#             default = st.session_state['architecture_name']
#         )
#         st.session_state['architecture_name'] = selected_archi
#         if 'selectoption1' not in st.session_state or len(selected_archi) <= 0:
#             st.session_state['selectoption1'] = []
#         # z_model_code = sql.get_project("z_model_code")
#         z_model_code = sql.get_project("z_model_code",selected_archi)
#         selectoption1 = st.multiselect(
#             'プロジェクト:',
#             z_model_code,
#             key='unique_key_1',
#             default=st.session_state['selectoption1'],
#         )
#         st.session_state['selectoption1'] = selectoption1
#         # マルチセレクト２、、１と同じ流れ
#         if 'selectoption2' not in st.session_state:
#             st.session_state['selectoption2'] = []
#         destination = sql.get_project("destination",selectoption1)

#         if destination != st.session_state['selectoption2']:
#             st.session_state['selectoption2'] = []
        
#         selectoption2 = st.multiselect(
#             '仕向け:',
#             destination,
#             key='unique_key_2',
#             default=st.session_state['selectoption2'],
#         )
#         st.session_state['selectoption2'] = selectoption2
#         if 'selectoption3' not in st.session_state:
#             st.session_state['selectoption3'] = []
#         drive_system = sql.get_project("drive_system",selectoption1,selectoption2)
#         if drive_system != st.session_state['selectoption3']:
#             st.session_state['selectoption3'] = []
            
#         selectoption3 = st.multiselect(
#             '駆動方式:',
#             drive_system,
#             key='unique_key_3',
#             default=st.session_state['selectoption3'],
        
#         )
#         st.session_state['selectoption3'] = selectoption3

#         if all(st.session_state[key] for key in option_keys):
#             if 'selectoption4' not in st.session_state:
#                 st.session_state['selectoption4'] = []
#             project_lot = sql.get_project("project_lot",st.session_state['selectoption1'],
#                                           st.session_state['selectoption2'],st.session_state['selectoption3'])
#             if project_lot != st.session_state['selectoption4']:
#                 st.session_state['selectoption4'] = []
#             selectoption4 = st.multiselect(
#                 'ロット:',
#                 project_lot,
#                 key='unique_key_4',
#                 default=st.session_state['selectoption4'],
#             )
#             st.session_state['selectoption4'] = selectoption4
            
#             if 'selectoption5' not in st.session_state:
#                 st.session_state['selectoption5'] = []
#             phase_list = sql.get_project("phase_list",
#                                          st.session_state['selectoption1'],
#                                          st.session_state['selectoption2'],
#                                          st.session_state['selectoption3'],
#                                          st.session_state['selectoption4'])
#             if phase_list != st.session_state['selectoption5']:
#                 st.session_state['selectoption5'] = []
#             selectoption5 = st.multiselect(
#                 'フェーズ:',
#                 phase_list,
#                 key='unique_key_5',
#                 default=st.session_state['selectoption5'],
#             )
#             st.session_state['selectoption5'] = selectoption5
#             st.markdown('<span id="button-right"></span>', unsafe_allow_html=True)
#             col11, col12 = st.columns(2)
            
#             with col12:
#                 if st.button("完了"):
#                     if all(st.session_state[key] for key in option_keys2):
#                         df1,df2=sql.posgre_get_date(st.session_state['selectoption1'],
#                                          st.session_state['selectoption2'],
#                                          st.session_state['selectoption3'],
#                                          st.session_state['selectoption4'],
#                                          st.session_state['selectoption5'])
#                         st.session_state.prj_info_list = df1
#                         st.session_state.se_data_stuck = df2
#                         #山口　デバック
#                         df1
#                         df2
#                         st.session_state['compare_click'] = False
#                         st.rerun()
#                     else:
#                         st.error('全て選択してくださぃ！！', icon="🚨")
#             with col11:
#                 bookmarked = st.button("条件をお気に入りに追加")
#                 if bookmarked:
#                     if all(st.session_state[key] for key in option_keys2):
#                         sql.insert_bookmark(selectoption1,selectoption2,selectoption3,selectoption4,selectoption5,st.session_state.username, next_bookmark)
#                         st.write("お気に入りに追加しました。")
#                         time.sleep(1)
#                         st.rerun()
#         st.session_state.chosen_id = 1

#チョー choice_se_bookmark関数を調整する　03/10
@st.dialog("プロジェクト選択", width='large')  # 山口　ブックマーク用ダイアログ10/28
def choice_se_bookmark(selected_tab):
    # Get bookmark info
    df_bookmarks = sql.get_bookmarks(st.session_state.username)
    st.session_state['se_df_bookmarks'] = df_bookmarks #比較ダイアログで使ってる　08/22 10/29
    df_transformed = transform_bookmarks(df_bookmarks)
    print('df trans: ', df_transformed)
    selectables = create_selectables(df_transformed)
    next_bookmark = max(df_transformed['bookmark_number']) + 1
    print('next bookmark: ', next_bookmark)
    col1, col2 = st.columns([5, 5])
    
    with col1:
        handle_project_selection(selected_tab, next_bookmark)
        print('login session dialogs: ', st.session_state.login_begin)
    with col2:
        handle_bookmark_selection(selectables, df_bookmarks, selected_tab, next_bookmark)

#チョー　03/10
def transform_bookmarks(df_bookmarks):
    return df_bookmarks.groupby('bookmark_number').apply(
        lambda x: pd.Series({
            'bookmark_number': x['bookmark_number'].iloc[0],
            'value': '; '.join(x.sort_values('category')['value'].tolist())
        })
    ).reset_index(drop=True)


#チョー　03/10
def create_selectables(df_transformed):
    keys = df_transformed['bookmark_number']
    values = df_transformed['value']
    return dict(zip(keys, values))

#チョー　03/10
def handle_bookmark_selection(selectables, df_bookmarks, selected_tab, next_bookmark):
    if 'bookmark_selection' not in st.session_state:
        st.session_state['bookmark_selection'] = 0

    bookmark_selection = st.selectbox(
        'お気に入り条件:',
        list(selectables.values()),
        key='bookmark_key_1',
        index=0
    )
    
    st.session_state['bookmark_selection'] = [k for k, v in selectables.items() if v == bookmark_selection][0]
    selected_number = st.session_state['bookmark_selection']
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("お気に入りで表示"):
            if selected_number > 0:
                update_session_options(df_bookmarks, selected_number)
                st.session_state.login_begin = False
                st.session_state.summary_rlist_flag = False
                execute_selected_tab(selected_tab)
            else:
                st.error("お気に入り条件が選択されていません")
    with col2:
        if st.button("お気に入りを削除"):
            if selected_number > 0:
                sql.delete_bookmark(selected_number, st.session_state.username)
                st.write("お気に入りを削除しました")
                st.session_state.summary_rlist_flag = False
                time.sleep(1)
                st.rerun()
            else:
                st.error("お気に入り条件が選択されていません")

#チョー　03/10
def update_session_options(df_bookmarks, selected_number):
    # print('update session fun:')
    for category in range(0, 6):
        if category == 0:
            st.session_state['architecture_name'] = df_bookmarks[
                (df_bookmarks['bookmark_number'] == selected_number) & 
                (df_bookmarks['category'] == category)
            ]['value'].tolist()
        else:
            st.session_state[f'selectoption{category}'] = df_bookmarks[
                (df_bookmarks['bookmark_number'] == selected_number) & 
                (df_bookmarks['category'] == category)
            ]['value'].tolist()
            # print('session:', st.session_state[f'selectoption{category}'])


#チョー　03/10
def execute_selected_tab(selected_tab):
    ##山口　Prj実行したら、全帳票の入ったsession_stateをリセットしないと、選択したプロジェクトを変えたのに古いプロジェクトが表示される事態になる。
    if 'prj_info_list' in st.session_state:
        del st.session_state.prj_info_list
    if 'se_data_stuck' in st.session_state:
        del st.session_state.se_data_stuck
    if 'sim_prj_info_list' in st.session_state:
        del st.session_state.sim_prj_info_list
    if 'sim_data_stuck' in st.session_state:
        del st.session_state.sim_data_stuck
    if 'r_prj_info_list' in st.session_state:
        del st.session_state.r_prj_info_list
    if 'rlist_data_stuck' in st.session_state:
        del st.session_state.rlist_data_stuck
    if 'rfl_list' in st.session_state:
        del st.session_state.rfl_list

    if selected_tab == 'se_list':
        execute_se_list()
    elif selected_tab == 'r_list':
        execute_r_list()
    elif selected_tab == 'sim_list':
        execute_sim_list()
    elif selected_tab == 'rfl_list':
        execute_rfl_list()

#チョー　03/10
def execute_se_list():
    df1, df2 = sql.posgre_get_date(
        st.session_state['selectoption1'],
        st.session_state['selectoption2'],
        st.session_state['selectoption3'],
        st.session_state['selectoption4'],
        st.session_state['selectoption5']
    )
    st.session_state.prj_info_list = df1
    st.session_state.se_data_stuck = df2
    st.session_state['compare_click'] = False
    st.session_state.login_begin = False
    st.session_state.chosen_id = 1
    st.rerun()

#チョー　03/10
def execute_r_list():
    df1, df2 = sql.posgre_get_rlist(
        st.session_state['selectoption1'],
        st.session_state['selectoption2'],
        st.session_state['selectoption3'],
        st.session_state['selectoption4'],
        st.session_state['selectoption5']
    )
    
    if len(df1) == 0:
        st.error('選択されたプロジェクトの要求リストは登録されていません。')
    else:
        st.session_state.r_prj_info_list = df1
        st.session_state.rlist_data_stuck = df2
        st.session_state['compare_click'] = False
        st.session_state['compare_back_click'] = False
        st.session_state.chosen_id = 2
        st.rerun()

#チョー　03/10
def execute_sim_list():
    df1, df2 = sql.posgre_get_data_sim(
        st.session_state['selectoption1'],
        st.session_state['selectoption2'],
        st.session_state['selectoption3'],
        st.session_state['selectoption4'],
        st.session_state['selectoption5']
    )
    #len(df1) == 0 チェックは不要に3/24


    st.session_state.sim_prj_info_list = df1
    st.session_state.sim_data_stuck = df2
    st.session_state.chosen_id = 3
    st.rerun()

#チョー　03/10
def execute_rfl_list():
    df1 = sql.posgre_get_rfl(
        st.session_state['selectoption1'],
        st.session_state['selectoption2'],
        st.session_state['selectoption3'],
        st.session_state['selectoption4'],
        st.session_state['selectoption5']
    )
    
    st.session_state.rfl_list = df1
    st.session_state.chosen_id = 4
    st.rerun()

#チョー　03/10
def handle_project_selection(selected_tab, next_bookmark):
    if 'architecture_name' not in st.session_state:
        st.session_state['architecture_name'] = []
        st.session_state['selectoption1'] = []

    architecture_list = sql.get_project("architecture_name")
    selected_archi = st.multiselect(
        'PTシステムタイプ',
        architecture_list,
        key='select_archi_unique_key',
        default=st.session_state['architecture_name']
    )

    if 'selectoption1' not in st.session_state or len(selected_archi) <= 0:
        st.session_state['selectoption1'] = []

    z_model_code = sql.get_project("z_model_code", selected_archi)
    selectoption1 = st.multiselect(
        'プロジェクト:',
        z_model_code,
        key='unique_key_1',
        default=st.session_state['selectoption1'],
    )
    
    
    if 'selectoption2' not in st.session_state:
        st.session_state['selectoption2'] = []

    print('selection 2: ', st.session_state['selectoption2'])

    destination = sql.get_project("destination", selectoption1)
    selectoption2 = st.multiselect(
        '仕向け:',
        destination,
        key='unique_key_2',
        default=[st.session_state['selectoption2'] if st.session_state['selectoption2'] in destination else None][0], #山口　デフォルト値が選択肢にない場合のエラーを防ぐ7/3
    )


    if 'selectoption3' not in st.session_state:
        st.session_state['selectoption3'] = []

    drive_system = sql.get_project("drive_system", selectoption1, selectoption2)
    selectoption3 = st.multiselect(
        '駆動方式:',
        drive_system,
        key='unique_key_3',
        default=[st.session_state['selectoption3'] if st.session_state['selectoption3'] in drive_system else None][0],#山口　デフォルト値が選択肢にない場合のエラーを防ぐ7/3
    )
    

    #if all(st.session_state[key] for key in option_keys):
    if selectoption1 and selectoption2 and selectoption3:
        if 'selectoption4' not in st.session_state:
            st.session_state['selectoption4'] = []

        project_lot = sql.get_project("project_lot", selectoption1,
                                      selectoption2, selectoption3)
        selectoption4 = st.multiselect(
            'ロット:',
            project_lot,
            key='unique_key_4',
            default=[st.session_state['selectoption4'] if st.session_state['selectoption4'] in project_lot else None][0],#山口　デフォルト値が選択肢にない場合のエラーを防ぐ7/3
        )
        

        if 'selectoption5' not in st.session_state:
            st.session_state['selectoption5'] = []

        phase_list = sql.get_project("phase_list",
                                     selectoption1,
                                     selectoption2,
                                     selectoption3,
                                     selectoption4)
        selectoption5 = st.multiselect(
            'フェーズ:',
            phase_list,
            key='unique_key_5',
            default=[st.session_state['selectoption5'] if st.session_state['selectoption5'] in phase_list else None][0],#山口　デフォルト値が選択肢にない場合のエラーを防ぐ7/3
        )

        st.markdown('<span id="button-right"></span>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("条件をお気に入りに追加"):
                # if all(st.session_state[key] for key in option_keys2):
                if selectoption4 and selectoption5:
                    sql.insert_bookmark(selected_archi,selectoption1, selectoption2, selectoption3, selectoption4, selectoption5,
                                        st.session_state.username, next_bookmark)
                    st.write("お気に入りに追加しました。")
                    st.session_state['selectoption1'] = selectoption1
                    st.session_state['selectoption2'] = selectoption2
                    st.session_state['selectoption3'] = selectoption3
                    st.session_state['selectoption4'] = selectoption4
                    st.session_state['selectoption5'] = selectoption5
                    time.sleep(1)
                    st.session_state.login_begin = False
                    st.session_state.summary_rlist_flag = False
                    reload_info()
                    # st.rerun()
        with col2:
             if st.button("完了"):
                #if all(st.session_state[key] for key in option_keys2):
                if selectoption4 and selectoption5:
                    st.session_state['architecture_name'] = selected_archi
                    st.session_state['selectoption1'] = selectoption1
                    st.session_state['selectoption2'] = selectoption2
                    st.session_state['selectoption3'] = selectoption3
                    st.session_state['selectoption4'] = selectoption4
                    st.session_state['selectoption5'] = selectoption5
                    st.session_state.login_begin = False
                    st.session_state.summary_rlist_flag = False
                    execute_selected_tab(selected_tab)
                    # st.rerun()
                else:
                    st.error('全て選択してくださぃ！！', icon="🚨")


@st.dialog("MAP編集", width='large') #山口　マップ用ダイアログ11/13 sim用に対応 12/6 マップ名の追加 12/9
def mapgrid(result):
    
    for i, row in result.iterrows():
        project_id=row['project_id']
        if int(st.session_state.chosen_id)==1:
            map_name= row['z_request_median']
            parameter_id=row['se_parameter_id']
        elif int(st.session_state.chosen_id)==3:
            map_name= row['value']
            parameter_id=row['senario_parameter_id']
        df_map_variables = None
        phase_id=row['phase_id']
        URL = row['URL']#山口　マップ登録できてないとき用のURL取得 12/10
        print(st.session_state.chosen_id)
        variation_id=row['variation_id']
        
        if int(st.session_state.chosen_id)==1:
            print("get se map")
            df_map_variables = sql.get_map_variables(project_id, parameter_id, phase_id, variation_id)
        elif int(st.session_state.chosen_id)==3:
            print("get sim map")
            study_id=row['study_id']
            df_map_variables = sql.get_senario_map_variables(project_id,parameter_id, phase_id, variation_id, study_id)
        #df_map_variables
        mode = None
        df_display=None
        vallist=[]
        if len(df_map_variables)>1:
            #X軸、Y軸、マップがそろっているか確認する
            xcount= len(df_map_variables[df_map_variables['axis']=='X'])
            ycount=len(df_map_variables[df_map_variables['axis']=='Y'])
            mapcount=len(df_map_variables[df_map_variables['axis']=='MAP'])
            tablecount=len(df_map_variables[df_map_variables['axis']=='TABLE'])
            vallist=[]
     
           
            for i, valrow in df_map_variables.iterrows():
                vallist.append("{}:{} 単位:{}".format(valrow['axis'], valrow['variable_name'], valrow['unit']))
            
            if xcount==1 & ycount==1 & mapcount==1:
                mode='MAP'
                df_X=df_map_variables[df_map_variables['axis']=='X']
                df_Y=df_map_variables[df_map_variables['axis']=='Y']
                df_MAP=df_map_variables[df_map_variables['axis']=='MAP']
                X=df_X['value'].tolist()[0].split(', ')#ただvalueを文字列としてとってsplitしたかっただけ
                Y=df_Y['value'].tolist()[0].split(', ')
                MAP=df_MAP['value'].tolist()[0].split('; ')#;で行分割　,で列分割
                MAP = [x.replace(';','').split(', ') for x in MAP] 
                MAP = pd.DataFrame(MAP)
                # st.write(len(X)) #チョー　01/14
                # st.write(len(Y)) #チョー　01/14
                # st.write(MAP.shape) #チョー　01/14
                if len(X)==MAP.shape[1] and len(Y)==MAP.shape[0]:
                    #見せるように、元のマップの大きさ+10のDFを定義
                    df_display=pd.DataFrame(index=range(100), columns=['c_' + str(i) for i in range(100)])
                    #1行目はX、2行目はY、2,2からMap表示
                    df_display.iloc[0,0]='↓Y \ X→'
                    df_display.iloc[0,1:1+len(X)]=X
                    df_display.iloc[1:1+len(Y),0]=Y
                    df_display.iloc[1:1+len(Y),1:1+len(X)]=MAP.values
            
                 
                else:
                    st.error(row['z_prj_number'] + ' ' + row['z_parent_paraitem'] + ' ' + row['z_child_paraitem'] + ' ' + row['z_wp_name_get_str'] + "は軸の長さが一致しません。")
                    
            elif xcount==1 and tablecount>=1:
                
                mode='TABLE'
                df_X=df_map_variables[df_map_variables['axis']=='X']
                df_TABLE=df_map_variables[df_map_variables['axis']=='TABLE']
                X=df_X['value'].tolist()[0].split(', ')#ただvalueを文字列としてとってsplitしたかっただけ
                TABLE = [trow['value'].split(',') for i, trow in df_TABLE.iterrows() ]
                TABLE = pd.DataFrame(TABLE)
                
                if len(X) == TABLE.shape[1]:
                    df_display=pd.DataFrame(index=range(100), columns=['c_' + str(i) for i in range(100)])
                    df_display.iloc[0,0]='X→'
                    for index in range(tablecount):
                        df_display.iloc[index+1,0]='T→'
                    df_display.iloc[0,1:len(X)+1]=X
                    df_display.iloc[1:tablecount+1, 1:len(X)+1]=TABLE.values
                    
                else:
                    st.error(row['z_prj_number'] + ' ' + row['z_parent_paraitem'] + ' ' + row['z_child_paraitem'] + ' ' + row['z_wp_name_get_str'] + "は軸の長さが一致しません。")
                
             
            else:
                st.error(row['z_prj_number'] + ' ' + row['z_parent_paraitem'] + ' ' + row['z_child_paraitem'] + ' ' + row['z_wp_name_get_str'] + "は軸の数が未対応です。")
            
            #DFとモード定まったら表示
            if df_display is not None and mode is not None:
                
                for i, v in enumerate(vallist):
                    st.markdown(v)
                if URL:#山口　URL表示用ボタンの追加12/10
                    if st.button('元URL') :
                        st.components.v1.html(
                            f"""
                            <script>
                                window.open('{URL}','_blank')
                            </script>
                           """,
                            height=0
                        )
                if st.button('拡大表示'):  #山口　別ページ表示処理の追加
                    st.session_state.df_display=df_display
                    st.session_state.row = row
                    st.session_state.mode = mode
                    st.session_state.df_map_variables=df_map_variables
                    st.session_state.vallist = vallist
                    st.switch_page("pages/map_grid_page.py")
                
                builder = GridOptionsBuilder.from_dataframe(df_display)
                builder.configure_selection(selection_mode='multiple')
                builder.configure_default_column(editable=True, width=20)
                builder.configure_grid_options(enableRangeSelection=True)
                grid_option= builder.build()
                grid_edited = AgGrid(df_display, gridOptions = grid_option)
                df_edited = grid_edited['data']
            
            #更新ボタン押したとき処理
            
            
            if st.button('更新'):
                df_edited.columns = [str(i) for i in range(100)]
                df_edited = df_edited.fillna('')
                subqueries = ""
                XtoSql=None
                YtoSql=None
                MAPtoSql=None
                TABLEtoSqls=None
                map_variable_id_X=None
                map_variable_id_Y=None
                map_variable_id_MAP=None
                map_variable_id_TABLEs=None
                if int(st.session_state.chosen_id)==1:
                    z_paravalueid=row['z_paravalueid']#.tolist()[0]
                elif int(st.session_state.chosen_id)==3:
                    z_paravalueid=row['id']
                username=st.session_state.username
                now = datetime.datetime.now()
                #一度軸あっているかだけ確認する
                not_valid=False
                if mode=='MAP':
                    Xlen=int(df_edited.iloc[0,1:].last_valid_index())
                    Ylen=int(df_edited.iloc[1:,0].last_valid_index())
                    st.write(Xlen)
                    st.write(Ylen)
                    for i in range(Xlen):
                        mapylen = df_edited.iloc[1:,i+1].last_valid_index()
                        
                        if mapylen is None or Ylen!=int(mapylen):
                            st.error('Y軸とマップの高さが一致していません！！')
                            not_valid=True
                            break
                    if not not_valid:
                        for i in range(Ylen):
                            mapxlen = df_edited.iloc[i+1,1:].last_valid_index()
                           
                            if mapxlen is None or Xlen!=int(mapxlen):
                                st.error('X軸とマップの幅が一致していません！！')
                                not_valid=True
                                break
                    
                    if not not_valid:
                        Xedited=df_edited.iloc[0,1:Xlen+1].tolist()
                        Yedited=df_edited.iloc[1:Ylen+1,0].tolist()
                        MAPedited=df_edited.iloc[1:Ylen+1,1:Xlen+1].values.tolist()
                        XtoSql=', '.join(map(str,Xedited))
                        YtoSql=', '.join(map(str,Yedited))
                        MAPtoSql='; '.join([', '.join(map(str, row)) for row in MAPedited])
                        
                        map_variable_id_X=df_X['map_variable_id'].tolist()[0]
                        map_variable_id_Y=df_Y['map_variable_id'].tolist()[0]
                        map_variable_id_MAP=df_MAP['map_variable_id'].tolist()[0]
                    
                elif mode=='TABLE':
                    Xlen=int(df_edited.iloc[0,1:].last_valid_index())
                    Tablelens=[editedrow.last_valid_index() for editedi, editedrow in df_edited.iloc[1:tablecount+1].iterrows()]
                    
                    for ti in range(tablecount):
                        if Tablelens[ti] is None or int(Tablelens[ti])!=Xlen:
                            st.error('X軸とテーブルの長さが一致していません！！')
                            not_valid=True
                            break
                    
                    if not not_valid:
                        Xedited=df_edited.iloc[0,1:Xlen+1].tolist()
                        XtoSql=', '.join(map(str,Xedited))
                        map_variable_id_X=df_X['map_variable_id'].tolist()[0]
                       
                        TABLEtoSqls=[]
                        map_variable_id_TABLEs=[]
                        for ti in range(tablecount):
                            TABLEedited=df_edited.iloc[ti+1,1:Xlen+1].tolist()
                            TABLEtoSqls.append(', '.join(map(str,TABLEedited)))
                            map_variable_id_TABLEs.append(df_TABLE.iloc[ti]['map_variable_id'].tolist())
                        print(map_variable_id_TABLEs)
                
                if not not_valid:
                    if int(st.session_state.chosen_id)==1:
                        sql.update_map_variables(project_id, parameter_id, phase_id, variation_id, z_paravalueid, username, now, map_name, Xid=map_variable_id_X, Xval=XtoSql, Yid=map_variable_id_Y, Yval=YtoSql, MAPid=map_variable_id_MAP, MAPval=MAPtoSql, TABLEids=map_variable_id_TABLEs, TABLEvals=TABLEtoSqls)
                    elif int(st.session_state.chosen_id)==3:
                        sql.update_senario_map_variables(project_id, parameter_id, phase_id, variation_id, study_id, z_paravalueid, username, now, map_name, Xid=map_variable_id_X, Xval=XtoSql, Yid=map_variable_id_Y, Yval=YtoSql, MAPid=map_variable_id_MAP, MAPval=MAPtoSql, TABLEids=map_variable_id_TABLEs, TABLEvals=TABLEtoSqls)
                    st.write('Map情報を更新しました。')
                    time.sleep(1)
                    st.rerun()
        else:
            st.error(row['z_prj_number'] + ' ' + row['z_parent_paraitem'] + ' ' + row['z_child_paraitem'] + ' ' + row['z_wp_name_get_str'] + "にMapが紐づけられていません。")
            if row['URL'] is not None:#山口　DB上にMAPデータがないがURLがある場合、代わりにURL遷移する 12/10
                st.write('代わりにURL遷移します')
                URL = row['URL']
                
                if URL:
                    st.components.v1.html(
                        f"""
                        <script>
                            window.open('{URL}','_blank')
                        </script>
                       """,
                        height=0
                    )
            #dia.URL_none(row)
            
            
def judge_map_mode(df_map_variables):
    xcount= len(df_map_variables[df_map_variables['axis']=='X'])
    ycount=len(df_map_variables[df_map_variables['axis']=='Y'])
    zcount=len(df_map_variables[df_map_variables['axis']=='Z']) #Z軸の追加
    cubecount=len(df_map_variables[df_map_variables['axis']=='CUBE'])
    mapcount=len(df_map_variables[df_map_variables['axis']=='MAP'])
    tablecount=len(df_map_variables[df_map_variables['axis']=='TABLE'])
    if xcount==1 and ycount==1 and zcount==1 and cubecount==1: 
        return 'CUBE'
    elif xcount==1 and ycount==1 and mapcount==1:
        return 'MAP'
    elif xcount==1 and tablecount>=1:
        return 'TABLE'

def get_df_display(df_map_variables, mode):
    if mode=='CUBE': #CUBEモードの追加 12/13
        list_df_displays = []
        df_X=df_map_variables[df_map_variables['axis']=='X']
        df_Y=df_map_variables[df_map_variables['axis']=='Y']
        df_Z=df_map_variables[df_map_variables['axis']=='Z']
        df_CUBE=df_map_variables[df_map_variables['axis']=='CUBE']
        X=df_X['value'].tolist()[0].split(', ')#ただvalueを文字列としてとってsplitしたかっただけ
        Y=df_Y['value'].tolist()[0].split(', ')
        Z=df_Z['value'].tolist()[0].split(', ')
        CUBE=df_CUBE['value'].tolist()[0].split('| ')#|でMAP分割　;で行分割
        MAPs = [MAP.replace('|','').split('; ') for MAP in CUBE] 
        MAPs = [[x.replace(';','').split(', ') for x in MAP] for MAP in MAPs]
        MAPs = [pd.DataFrame(MAP) for MAP in MAPs]
        MAP = MAPs[0]
                    
        for i,MAP in enumerate(MAPs):
            if not (len(X)==MAP.shape[1] and len(Y)==MAP.shape[0]): 
                return None, None, None, 'XY軸とMAPの大きさが一致していません。'
            #見せるように、元のマップの大きさ+10のDFを定義
            df_display=pd.DataFrame(index=range(100), columns=range(100))
            #1行目はX、2行目はY、2,2からMap表示
            df_display.iloc[0,0]='↓Y \ X→'
            df_display.iloc[0,1:1+len(X)]=X
            df_display.iloc[1:1+len(Y),0]=Y
            df_display.iloc[1:1+len(Y),1:1+len(X)]=MAP.values
            list_df_displays.append(df_display)
        #Z軸も見せる
        df_display_z = pd.DataFrame(index=range(1), columns=range(len(Z)+5))#いったんZ軸はのばさない やっぱり伸ばす
        df_display_z.iloc[0,0]='Z→'
        df_display_z.iloc[0,1:1+len(Z)]=Z
        return None, df_display_z, list_df_displays, None
                
    elif mode=='MAP':
        df_X=df_map_variables[df_map_variables['axis']=='X']
        df_Y=df_map_variables[df_map_variables['axis']=='Y']
        df_MAP=df_map_variables[df_map_variables['axis']=='MAP']
        X=df_X['value'].tolist()[0].split(', ')#ただvalueを文字列としてとってsplitしたかっただけ
        Y=df_Y['value'].tolist()[0].split(', ')
        MAP=df_MAP['value'].tolist()[0].split('; ')#;で行分割　,で列分割
        MAP = [x.replace(';','').split(', ') for x in MAP] 
        MAP = pd.DataFrame(MAP)

        if not (len(X)==MAP.shape[1] and len(Y)==MAP.shape[0]):
            return None, None, None, 'XY軸とMAPの大きさが一致していません。'

        #見せるように、元のマップの大きさ+10のDFを定義
        df_display=pd.DataFrame(index=range(100), columns=range(100))
        #1行目はX、2行目はY、2,2からMap表示
        df_display.iloc[0,0]='↓Y \ X→'
        df_display.iloc[0,1:1+len(X)]=X
        df_display.iloc[1:1+len(Y),0]=Y
        df_display.iloc[1:1+len(Y),1:1+len(X)]=MAP.values
                
        return df_display, None, None, None

    elif mode=='TABLE': 
        tablecount=len(df_map_variables[df_map_variables['axis']=='TABLE'])
        df_X=df_map_variables[df_map_variables['axis']=='X']
        df_TABLE=df_map_variables[df_map_variables['axis']=='TABLE']
        X=df_X['value'].tolist()[0].split(', ')#ただvalueを文字列としてとってsplitしたかっただけ
        TABLE = [trow['value'].split(', ') for i, trow in df_TABLE.iterrows() ]
        TABLE = pd.DataFrame(TABLE)
        if not len(X) == TABLE.shape[1]:
            return None, None, None, 'X軸とTABLEの大きさが一致していません。'
        df_display=pd.DataFrame(index=range(100), columns=range(100))
        df_display.iloc[0,0]='X→'
        for index in range(tablecount):
            df_display.iloc[index+1,0]='T→'
        df_display.iloc[0,1:len(X)+1]=X
        df_display.iloc[1:tablecount+1, 1:len(TABLE[0])+1]=TABLE.values
                        
        return df_display, None, None, None
                
    else:
        return None, None, None, '想定外のmode'
    
def create_df_display_for_new_map():
    new_map_name = None
    xname=None
    yname=None
    zname=None
    cube_variable_name = None
    map_variable_name=None
    tablenames=[]

    mode = st.selectbox(
        'マップ種類:',
        ['MAP','TABLE', 'CUBE'],
        key='map_selector'
    )
            
    st.session_state.mapmode=mode
    df_display=pd.DataFrame(index=range(100), columns=range(100))
    new_map_name = st.text_input('MAP名')
    df_map_variables_all = sql.get_map_variables_all()
    df_optionX = df_map_variables_all[df_map_variables_all['axis']=='X']
    df_optionY = df_map_variables_all[df_map_variables_all['axis']=='Y']
    df_optionZ = df_map_variables_all[df_map_variables_all['axis']=='Z']
    df_optionMAP = df_map_variables_all[df_map_variables_all['axis']=='MAP']
    df_optionTABLE = df_map_variables_all[df_map_variables_all['axis']=='TABLE']
    df_optionCUBE = df_map_variables_all[df_map_variables_all['axis']=='CUBE']

    optionX = (df_optionX['id'].astype(str) + "_" + df_optionX['variable_name']+ "_" + df_optionX['unit']).values.tolist()
    optionY = (df_optionY['id'].astype(str) + "_" + df_optionY['variable_name']+ "_" + df_optionY['unit']).values.tolist()
    optionZ = (df_optionZ['id'].astype(str) + "_" + df_optionZ['variable_name']+ "_" + df_optionZ['unit']).values.tolist()
    optionMAP = (df_optionMAP['id'].astype(str) + "_" + df_optionMAP['variable_name']+ "_" + df_optionMAP['unit']).values.tolist()
    optionTABLE= (df_optionTABLE['id'].astype(str) + "_" + df_optionTABLE['variable_name']+ "_" + df_optionTABLE['unit']).values.tolist()
    optionCUBE = (df_optionCUBE['id'].astype(str) + "_" + df_optionCUBE['variable_name']+ "_" + df_optionCUBE['unit']).values.tolist()
    optionScope =['System_Control', 'Carbody', 'Driveline_EV_4WD', 'Electrical_auxiliaries_Low_Voltage', 'Electrical_auxiliaries_High_Voltage', 'Battery_Low_Voltage', 'Battery_High_Voltage', 'DCDC', 'Electrical_Motor_Fr', 'Electrical_Motor_Rr', 'Gearbox_Fr', 'Gearbox_Rr', 'HVAC', 'Cabin', 'gr_boundary_conditions', 'Scenarios', 'gr_thm_HV_eletm', 'specific_pre_post', 'Charger', 'Flywheel', 'Exhaust', 'Engine', 'Engine_thermal_mangement', 'Gearbox_Gen', 'Electrical_Motor_Gen']  #TODO 今はScopeを直書きしているが本来どこかのDBを参照させるべき
    
    optionX = sorted(optionX, key=lambda x: int(x.split('_')[0]))
    optionY = sorted(optionY, key=lambda x: int(x.split('_')[0]))
    optionZ = sorted(optionZ, key=lambda x: int(x.split('_')[0]))
    optionMAP = sorted(optionMAP, key=lambda x: int(x.split('_')[0]))
    optionTABLE = sorted(optionTABLE, key=lambda x: int(x.split('_')[0]))
    optionCUBE = sorted(optionCUBE, key=lambda x: int(x.split('_')[0]))

    if mode=='CUBE':#TODO
        xcount=1
        ycount=1
        zcount=1
        list_df_displays = []
        df_display.iloc[0,0]='↓Y \ X→'
        df_display.iloc[0,1] = 0
        df_display.iloc[1,0] = 0
        df_display.iloc[1,1] = 0
        df_display_z = pd.DataFrame(index=range(1),columns=range(10))
        df_display_z.iloc[0,0]='Z→'
        df_display_z.iloc[0,1]=0
        #thing is, making list_df_displays is impossibe since Zlen is not desided yet
        #or could i let users selected just like i did on table mode
        #forget about it just prepare 10 map
        for i in range(10):
            list_df_displays.append(df_display.copy())
        
        xname = st.selectbox('X軸名',optionX)
        yname= st.selectbox('Y軸名',optionY)
        zname = st.selectbox('Z軸名', optionZ)
        cube_variable_name = st.selectbox('MAP変数名',optionCUBE)
        

        df_display = None
        tablenames = None
        map_variable_name = None
    elif mode=='MAP':
        
        df_display.iloc[0,0]='↓Y \ X→'
        df_display.iloc[0,1] = 0
        df_display.iloc[1,0] = 0
        df_display.iloc[1,1] = 0
        xcount=1
        ycount=1
        mapcount=1
                
        tablecount=0
        xname = st.selectbox('X軸名',optionX)
        yname= st.selectbox('Y軸名',optionY)
        map_variable_name = st.selectbox('MAP変数名',optionMAP)
        
        df_display_z = None
        list_df_displays = None
        zname = None
        tablenames = None
        cube_variable_name = None
    else:
        table_dim=st.selectbox(
            'テーブル次元数:',
            [1,2,3,4,5,6,7,8,9,10],
            key='table_dim'
        )
        df_display.iloc[0,0]='X→'
        df_display.iloc[0,1]=0
        xname = st.selectbox('X軸名',optionX)
                
        for index in range(table_dim):
            tablenames.append(st.selectbox('TABLE変数名', optionTABLE,key='tablename' + str(index)))
            df_display.iloc[index+1,0]='T→'
            df_display.iloc[index+1,1]=1
        xcount=1
        tablecount=table_dim
                
        df_display_z = None
        list_df_displays = None
        zname = None
        cube_variable_name = None
    
    scope_name = st.selectbox('Scope:MAPが使用されるユニット', optionScope)
    
    return new_map_name, mode, df_display, df_display_z, list_df_displays,xname, yname, zname, tablenames, map_variable_name, cube_variable_name, scope_name

@st.dialog("MAP編集", width='large') #山口　マップ用ダイアログをmap_structureテーブルに対応させたもの 久しぶりに見に来たらもう意味わかんない...
def mapgrid_by_name(result):
    #マップ新規作成時、リストへの登録の行うため各IDを取得しておく
    st.write(result)
    project_id=result['project_id'].tolist()[0]
    phase_id=result['phase_id'].tolist()[0]
    if int(st.session_state['chosen_id']) == 1:
        parameter_id=result['se_parameter_id'].tolist()[0] 
        variation_id=result['variation_id'].tolist()[0]
        study_id=None
        map_name=result['z_request_median'].tolist()[0]
    elif int(st.session_state['chosen_id']) == 2:
        parameter_id=result['r_parameter_id'].tolist()[0]
        variation_id=None
        study_id=None
        map_name=result['value'].tolist()[0]
    elif int(st.session_state['chosen_id']) == 3:
        parameter_id=result['senario_parameter_id'].tolist()[0]
        variation_id=result['variation_id'].tolist()[0]
        study_id=result['study_id'].tolist()[0]
        map_name=result['value'].tolist()[0]
        
    df_map_variables = sql.get_map_variables_by_name(map_name)

    mode = None
    vallist=[]
    if not df_map_variables is None: 
        for i, valrow in df_map_variables.iterrows():
            vallist.append("{}:{} 単位:{}".format(valrow['axis'], valrow['variable_name'], valrow['unit']))

        mode = judge_map_mode(df_map_variables)    
        
        #X軸、Y軸、マップがそろっているか確認する
        
        df_display = None
        df_display_z = None
        list_df_displays = []
        
        df_display, df_display_z, list_df_displays, err = get_df_display(df_map_variables, mode)

        if err is not None:
            st.error(err)
            return
        
        st.session_state.df_display = df_display
        st.session_state.df_display_z = df_display_z
        st.session_state.df_displays = list_df_displays
        st.session_state.mapmode=mode
        st.session_state.create_new_map=False
    else:
        st.error( "このパラメータ名のマップは存在しません。")
        st.session_state.create_new_map=True
        
        st.session_state.mapmode='MAP'
        

    
        
    #新規作成であればモード選択させる ようやくCube取り組める 7/9
    if st.session_state.create_new_map==True:
        new_map_name, mode, df_display, df_display_z, list_df_displays,xname, yname, zname, tablenames, map_variable_name, cube_variable_name, scope_name = create_df_display_for_new_map()
    else:
        new_map_name = xname = yname = zname = tablenames = map_variable_name   = cube_variable_name = scope_name = None

    # if 'df_display' not in st.session_state:
    #     st.error(result['value'] + "に紐づくMapがありません。")
    #     return
        #dia.URL_none(row)
            #DFとモード定まったら表示
    df_edited = []
    df_edited_z = []
    df_editeds = []
    if mode is not None:
        for i, v in enumerate(vallist):
            st.markdown(v)
        #Z軸の表示,表示するマップの選択
        
        df_edited, df_edited_z, df_editeds =  show_map_grid(mode, df_display, df_display_z, list_df_displays)

        # if mode == 'CUBE' and df_display_z is not None:
                    
        #     df_edited_z = st.data_editor(df_display_z, width=1000, hide_index=True)
        #     zlen = int(df_edited_z.iloc[0,1:].last_valid_index())
        #     df_editeds = [pd.DataFrame([]) for tmp in range(zlen)]
        #     for dim_to_display in range(zlen):
        #         df_editeds[dim_to_display] = st.data_editor(list_df_displays[dim_to_display], width=1000, hide_index=True, key='cube_map_'+str(dim_to_display))
        # else:
        #     df_edited = st.data_editor(df_display, width=1000, hide_index=True)
        # if st.button('拡大表示'):  #山口　別ページ表示処理の追加
                #     st.session_state.df_display=df_display
        #     st.session_state.row = result
                #     st.session_state.mapmode = mode
                #     st.session_state.df_map_variables=df_map_variables
                #     st.session_state.vallist = vallist
                #     st.switch_page("pages/map_grid_page_by_name.py")
    else:
        st.error('unexpected mode')
    ############################################################新ボタン押したとき処理
    if st.button('更新'):

        update_mapgrid_by_name(mode, df_edited, df_editeds, df_edited_z,  map_name, new_map_name, xname, yname, zname, cube_variable_name, map_variable_name,tablenames, project_id, parameter_id,phase_id, variation_id, study_id ,scope_name)
    
def get_grid_option_for_mapgrid_by_name(df_display, df_display_z, list_df_displays):
    grid_option_z = None
    grid_option_first_map = None
    grid_option_other_map = None
    
    if df_display_z is not None:
        grid_option_z = {
            "defaultColDef": {
            "editable": True,
            "width": 80,
            "resizable": True,
            },
            'columnDefs': [
            ],
            "enableRangeSelection": True,
            "rowSelection": "multiple",
        }
        for i in range(len(df_display_z.columns)):
            grid_option_z['columnDefs'].append({'field':str(i)})
    
    if df_display is not None:

        grid_option_first_map = {
            "defaultColDef": {
            "editable": True,
            "width": 80,
            "resizable": True,
            },
            'columnDefs': [
            ],
            "enableRangeSelection": True,
            "rowSelection": "multiple",
        }
        for i in range(len(df_display.columns)):
            grid_option_first_map['columnDefs'].append({'field':str(i)})

    if list_df_displays is not None:
        grid_option_first_map = {
            "defaultColDef": {
            "editable": True,
            "width": 80,
            "resizable": True,
            },
            'columnDefs': [
            ],
            "enableRangeSelection": True,
            "rowSelection": "multiple",
        }
        for i in range(len(list_df_displays[0].columns)):
            grid_option_first_map['columnDefs'].append({'field':str(i)})
        grid_option_other_map = {
            "defaultColDef": {
            "editable": True,
            "width": 80,
            "resizable": True,
            },
            'columnDefs': [

            ],
            "enableRangeSelection": True,
            "rowSelection": "multiple",
            "getRowStyle": JsCode("""
            function(params) {
                console.log(params);
                if (params.rowIndex === 0) {
                    return { 'editable': false ,
                            'background-color':'#666666'};
                }
            }
            """),
            "columnDefs": [
            {
                "field": "0",
                "editable": False,
                'cellStyle':{
                    'background-color': '#666666'
                }
            },
            ],
        }
        for i in range(len(list_df_displays[0].columns)-1):
            grid_option_other_map['columnDefs'].append({'field':str(i+1)})
    
    return grid_option_z, grid_option_first_map, grid_option_other_map

def show_map_grid(mode, df_display, df_display_z, list_df_displays):
    '''
    マップDFを受け取りst.aggridで表示する
    '''
    
    grid_option_z, grid_option_first_map, grid_option_other_map = get_grid_option_for_mapgrid_by_name(df_display, df_display_z, list_df_displays)

    if mode == 'CUBE' and df_display_z is not None:
        df_display_z.columns = df_display_z.columns.map(str)


        grid_edited_z = AgGrid(df_display_z, gridOptions=grid_option_z,  allow_unsafe_jscode=True, height=100)
        df_edited_z = grid_edited_z['data']
        zlen = int(df_edited_z.iloc[0,1:].last_valid_index())
        df_editeds = [pd.DataFrame([]) for tmp in range(zlen)]
        grid_editeds = []
        for dim_to_display in range(zlen):
            st.write("表示Z軸:" + str(df_edited_z.iloc[0, dim_to_display+1]))
            list_df_displays[dim_to_display].columns = list_df_displays[dim_to_display].columns.map(str)
            if dim_to_display == 0:
                grid_editeds.append(AgGrid(list_df_displays[dim_to_display], gridOptions=grid_option_first_map, allow_unsafe_jscode=True, key='grid_' + str(dim_to_display)))                
            else:
                grid_editeds.append(AgGrid(list_df_displays[dim_to_display], gridOptions=grid_option_other_map, allow_unsafe_jscode=True, key='grid_' + str(dim_to_display)))                
            df_editeds[dim_to_display] = grid_editeds[dim_to_display]['data']

        df_edited = None
            
    else:
        grid_edited = AgGrid(df_display, gridOptions=grid_option_first_map, allow_unsafe_jscode=True, )
        df_edited = grid_edited['data']
        df_edited_z = None
        df_editeds = None
    
   
    return df_edited, df_edited_z, df_editeds
            
def validate_edited_map(mode, df_edited, df_edited_z, df_editeds):
    not_valid = False
    if mode == 'MAP':
        Xlen = int(df_edited.iloc[0, 1:].last_valid_index())
        Ylen = int(df_edited.iloc[1:, 0].last_valid_index())
        for i in range(Xlen):
            mapylen = df_edited.iloc[1:, i + 1].last_valid_index()
            if mapylen is None or Ylen != int(mapylen):
                st.error('Y軸とマップの高さが一致していません！！')
                not_valid = True
                return not_valid

        for i in range(Ylen):
            mapxlen = df_edited.iloc[i + 1, 1:].last_valid_index()
            if mapxlen is None or Xlen != int(mapxlen):
                st.error('X軸とマップの幅が一致していません！！')
                not_valid = True
                return not_valid
    elif mode == 'TABLE':
        Xlen = int(df_edited.iloc[0, 1:].last_valid_index())
        tablecount = int(df_edited.iloc[1:, 1].last_valid_index())
        Tablelens = [editedrow.last_valid_index() for editedi, editedrow in df_edited.iloc[1:tablecount + 1].iterrows()]
        for ti in range(tablecount):
            if Tablelens[ti] is None or int(Tablelens[ti]) != Xlen:
                st.error('X軸とテーブルの長さが一致していません！！')
                not_valid = True
                return not_valid

    elif mode == 'CUBE':
        Xlen0=int(df_editeds[0].iloc[0,1:].last_valid_index())
        Ylen0=int(df_editeds[0].iloc[1:,0].last_valid_index())
        Zlen=int(df_edited_z.iloc[0,1:].last_valid_index())
        
        #Z軸長さがあっているか確認
        if not Zlen==len(df_editeds):
            st.error('Z軸とマップの数が一致していません！！')
            not_valid=True
            return not_valid
    
        for df_edited in df_editeds:
            Xlen=int(df_edited.iloc[1:,1:].last_valid_index())
            Ylen=int(df_edited.iloc[1:,1:].transpose().last_valid_index())
            if Xlen!=Xlen0:
                st.error('各マップでX軸の幅が一致していません！！')
                not_valid=True
                return not_valid
            elif Ylen!=Ylen0:
                st.error('各マップでY軸の高さが一致していません！！')
                not_valid=True
                return not_valid
            
            for i in range(Xlen):
                mapylen = df_edited.iloc[1:,i+1].last_valid_index()
                
                if mapylen is None or Ylen!=int(mapylen):
                    st.error('Y軸とマップの高さが一致していません！！')
                    not_valid=True
            
                    return not_valid
            
            for i in range(Ylen):
                mapxlen = df_edited.iloc[i+1,1:].last_valid_index()
                
                if mapxlen is None or Xlen!=int(mapxlen):
                    st.error('X軸とマップの幅が一致していません！！')
                    not_valid=True
                    return not_valid
    return not_valid

def make_sql_text(mode, df_edited, df_edited_z, df_editeds):
    '''
    df_editedの値をSQLに変換する関数
    '''
    XtoSql = None
    YtoSql = None
    ZtoSql = None
    CUBEtoSql = None
    MAPtoSql = None
    TABLEtoSqls = None

    if mode=='MAP':
        Xlen=int(df_edited.iloc[0,1:].last_valid_index())
        Ylen=int(df_edited.iloc[1:,0].last_valid_index())
        
        Xedited=df_edited.iloc[0,1:Xlen+1].tolist()
        Yedited=df_edited.iloc[1:Ylen+1,0].tolist()
        MAPedited=df_edited.iloc[1:Ylen+1,1:Xlen+1].values.tolist()
        XtoSql=', '.join(map(str,Xedited))
        YtoSql=', '.join(map(str,Yedited))
        MAPtoSql='; '.join([', '.join(map(str, row)) for row in MAPedited])
                        
        ZtoSql = None
        CUBEtoSql = None
        TABLEtoSqls = None
        
    elif mode=='TABLE':
        Xlen=int(df_edited.iloc[0,1:].last_valid_index())
        tablecount = int(df_edited.iloc[1:,1].last_valid_index())
                    
                    
        Xedited=df_edited.iloc[0,1:Xlen+1].tolist()
        XtoSql=', '.join(map(str,Xedited))
        TABLEtoSqls=[]
        for ti in range(tablecount):
            TABLEedited=df_edited.iloc[ti+1,1:Xlen+1].tolist()
            TABLEtoSqls.append(', '.join(map(str, TABLEedited)))
            # map_variable_id_TABLEs.append(df_TABLE.iloc[ti]['map_variable_id'].tolist())
            
        YtoSql = None
        ZtoSql = None
        CUBEtoSql = None
        MAPtoSql = None
                
    elif mode=='CUBE':
        Xlen0=int(df_editeds[0].iloc[0,1:].last_valid_index())
        Ylen0=int(df_editeds[0].iloc[1:,0].last_valid_index())
        Zlen=int(df_edited_z.iloc[0,1:].last_valid_index())
        
        Zedited = df_edited_z.iloc[0,1:Zlen+1].tolist()
        Xedited=df_editeds[0].iloc[0,1:Xlen0+1].tolist()
        Yedited=df_editeds[0].iloc[1:Ylen0+1,0].tolist()
        ZtoSql=', '.join(map(str,Zedited))
        XtoSql=', '.join(map(str,Xedited))
        YtoSql=', '.join(map(str,Yedited))
        
        for df_edited in df_editeds:
            MAPedited=df_edited.iloc[1:Ylen0+1,1:Xlen0+1].values.tolist()
            MAPtoSql='; '.join([', '.join(map(str, row)) for row in MAPedited])
            if CUBEtoSql is None:
                CUBEtoSql = MAPtoSql
            else:
                CUBEtoSql = CUBEtoSql + '| ' + MAPtoSql
                            
        MAPtoSql = None
        TABLEtoSqls = None
    return XtoSql, YtoSql, ZtoSql, CUBEtoSql, MAPtoSql, TABLEtoSqls
    
def get_map_variable_id(mode, map_name):
    '''
    マップ名から、各軸のマップIDを返却する関数
    '''    
    map_variable_id_X = map_variable_id_Y = map_variable_id_Z = map_variable_id_CUBE = map_variable_id_MAP = map_variable_id_TABLEs = None

    df_map_variables = sql.get_map_variables_by_name(map_name)
    df_X=df_map_variables[df_map_variables['axis']=='X']
    df_Y=df_map_variables[df_map_variables['axis']=='Y']
    df_Z=df_map_variables[df_map_variables['axis']=='Z']
    df_CUBE=df_map_variables[df_map_variables['axis']=='CUBE']
    df_MAP=df_map_variables[df_map_variables['axis']=='MAP']
    df_TABLE=df_map_variables[df_map_variables['axis']=='TABLE']
    if mode=='MAP':
        map_variable_id_X=df_X['map_variable_id'].tolist()[0]
        map_variable_id_Y=df_Y['map_variable_id'].tolist()[0]
        map_variable_id_MAP=df_MAP['map_variable_id'].tolist()[0]
        map_variable_id_Z = None
        map_variable_id_CUBE = None
        map_variable_id_TABLEs = None

    elif mode=='TABLE':
        tablecount = len(df_TABLE)
        map_variable_id_X=df_X['map_variable_id'].tolist()[0]
        map_variable_id_TABLEs=[]
        for ti in range(tablecount):
            map_variable_id_TABLEs.append(df_TABLE.iloc[ti]['map_variable_id'].tolist())
        map_variable_id_Y = None
        map_variable_id_Z = None
        map_variable_id_CUBE = None
        map_variable_id_MAP = None
    elif mode=='CUBE':
        map_variable_id_X=df_X['map_variable_id'].tolist()[0]
        map_variable_id_Y=df_Y['map_variable_id'].tolist()[0]
        map_variable_id_Z=df_Z['map_variable_id'].tolist()[0]
        map_variable_id_CUBE = df_CUBE['map_variable_id'].tolist()[0]
        map_variable_id_MAP = None
        map_variable_id_TABLEs = None
    
    return map_variable_id_X, map_variable_id_Y, map_variable_id_Z, map_variable_id_CUBE, map_variable_id_MAP, map_variable_id_TABLEs

def update_mapgrid_by_name(mode, df_edited, df_editeds, df_edited_z,  map_name, new_map_name, xname, yname, zname, cube_variable_name,  map_variable_name, tablenames, project_id, parameter_id, phase_id, variation_id, study_id, scope_name):
    #TODO newmapが入力された場合はそのマップをvalueとしてtest_project_senario_parameterをアップデートする
    XtoSql=None
    YtoSql=None
    ZtoSql=None
    CUBEtoSql=None
    MAPtoSql=None
    TABLEtoSqls=None
    map_variable_id_X=None
    map_variable_id_Y=None
    map_variable_id_Z=None
    map_variable_id_CUBE=None
    map_variable_id_MAP=None
    map_variable_id_TABLEs=None
    
    username=st.session_state.username
    now = datetime.datetime.now()
    #一度軸あっているかだけ確認する 

    not_valid=False
    not_valid = validate_edited_map(mode, df_edited, df_edited_z, df_editeds)
    if not_valid:
       return 
    XtoSql, YtoSql, ZtoSql, CUBEtoSql, MAPtoSql, TABLEtoSqls = make_sql_text(mode, df_edited, df_edited_z, df_editeds)
    
    
    if st.session_state.create_new_map==False:
        map_variable_id_X, map_variable_id_Y, map_variable_id_Z, map_variable_id_CUBE, map_variable_id_MAP, map_variable_id_TABLEs =  get_map_variable_id(mode, map_name)
    else:
        if mode=='MAP':
            map_variable_id_X = xname.split("_")[0]
            map_variable_id_Y = yname.split("_")[0]
            map_variable_id_MAP =  map_variable_name.split("_")[0]
            if len(set([map_variable_id_X, map_variable_id_Y, map_variable_id_MAP]))!=len([map_variable_id_X, map_variable_id_Y, map_variable_id_MAP]):
                st.error('変数名に重複があります。変数名はかぶらないようにしてください。')
                return
        elif mode=='TABLE':
            tablecount = int(df_edited.iloc[1:,1].last_valid_index())
            map_variable_id_X = xname.split("_")[0]
            for ti in range(tablecount):
                map_variable_id_TABLEs.append(tablenames[ti].split("_")[0])
            if len(set(map_variable_id_TABLEs + [map_variable_id_X]))!=len(map_variable_id_TABLEs + [map_variable_id_X]):
                st.error('変数名に重複があります。変数名はかぶらないようにしてください。')
                return
        elif mode=='CUBE':
            map_variable_id_X = xname.split("_")[0]
            map_variable_id_Y = yname.split("_")[0]
            map_variable_id_Z = zname.split("_")[0]
            map_variable_id_CUBE = cube_variable_name.split("_")[0]

            if len(set([map_variable_id_X, map_variable_id_Y, map_variable_id_Z, map_variable_id_CUBE]))!=len([map_variable_id_X, map_variable_id_Y, map_variable_id_Z, map_variable_id_CUBE]):
                st.error('変数名に重複があります。変数名はかぶらないようにしてください。')
                return

    

    if not st.session_state.create_new_map:

    
        sql.update_map_variables_by_name(map_name, username, now, Xid=map_variable_id_X, Xval=XtoSql, Yid=map_variable_id_Y, Yval=YtoSql, MAPid=map_variable_id_MAP, MAPval=MAPtoSql, TABLEids=map_variable_id_TABLEs, TABLEvals=TABLEtoSqls, Zid=map_variable_id_Z, Zval=ZtoSql, CUBEid=map_variable_id_CUBE, CUBEval=CUBEtoSql)#山口　Cubeへの対応 
    else:
        sql.create_new_map(new_map_name, username, now, xname, XtoSql, map_variable_id_X, yname, YtoSql, map_variable_id_Y, zname, ZtoSql, map_variable_id_Z, cube_variable_name, CUBEtoSql, map_variable_id_CUBE, map_variable_name, MAPtoSql, map_variable_id_MAP,  tablenames, TABLEtoSqls, map_variable_id_TABLEs, project_id, parameter_id, phase_id, variation_id, study_id, scope_name)

    #sql.update_map_variables(subqueries)
    st.write('Map情報を更新しました。')
    del st.session_state.create_new_map

    del st.session_state.mapmode
    time.sleep(1)
    st.rerun()

@st.dialog("シナリオ時系列", width='large') #山口　時系列表示ダイアログ
def timeseriesgrid(result):        
    for index, row in result.iterrows():
        usecase_id = row['usecase_id']
        df_timeseries_variables = sql.get_usecase_timeseries(usecase_id)
        if len(df_timeseries_variables)>0:
            #ユースケースIDに一致する時系列があったときに、それぞれ縦に並べて表示用グリッドに表示
            df_time = df_timeseries_variables[df_timeseries_variables['usecase_parameter_id']==5]
            df_vsp = df_timeseries_variables[df_timeseries_variables['usecase_parameter_id']==6]
            df_grad = df_timeseries_variables[df_timeseries_variables['usecase_parameter_id']==7]
            df_alttitude = df_timeseries_variables[df_timeseries_variables['usecase_parameter_id']==8]
            #st.write(df_time)
            time = df_time['value'].tolist()[0].split(', ')
            vsp = df_vsp['value'].tolist()[0].split(', ')
            grad = df_grad['value'].tolist()[0].split(', ')
            alttitude = df_alttitude['value'].tolist()[0].split(', ')
            
            # if len(time)!=len(vsp) or len(grad)!=len(alttitude) or len(vsp)!=len(grad):
            #     st.error('時系列データの長さが各パラメータで一致していません！！')
            
            df_display=pd.DataFrame(index=range(100000), columns=['時間[s]', '車速[km/h]','勾配[degC]', '標高[m]'])#行数10万で仮置き
            
       
            df_display.iloc[0:len(time),0] = time
            df_display.iloc[0:len(time),1] = vsp
            df_display.iloc[0:len(time),2] = grad
            df_display.iloc[0:len(time),3] = alttitude

            st.session_state.time=time
            st.session_state.vsp=vsp
            st.session_state.grad=grad
            st.session_state.alttitude=alttitude
            st.session_state.df_display=df_display
        else:
            st.error('ユースケースが登録されていません。')

        if 'df_display' in st.session_state:
            df_editeds = []
            if df_display is not None :
                df_edited = st.data_editor(df_display, width=1000, hide_index=True)
                fig = graph.Figure()
                fig.add_trace(graph.Scatter(x=df_edited['時間[s]'], y=df_edited['車速[km/h]'], mode='lines', name='車速[km/h]'))
                fig.add_trace(graph.Scatter(x=df_edited['時間[s]'], y=df_edited['勾配[degC]'], mode='lines', name='勾配[degC]'))
                fig.add_trace(graph.Scatter(x=df_edited['時間[s]'], y=df_edited['標高[m]'], mode='lines', name='標高[m]'))

                fig.update_layout(yaxis_type='linear')#山口　公開サーバだとこの一文が必要になる
                st.plotly_chart(fig, theme='streamlit')

                

def create_yaml_file(td_variable_list, usecase_name):
    # 山口　mapにも対応さSせる 12/16 
    # #走行パターンに応じてシミュレーション結果からDBに返す必要のあるパラメータを決めるため ユースケース名を引数に追 7/1?
    #走行パターンのディているから時系列だったりのデータを入れる機 7/4
    # Initialize the nested dictionary structure
    df_usecase_td = sql.get_usecase_td(usecase_name) 
    if len(df_usecase_td)==0:
        
        return 
    df_usecase_td = df_usecase_td[['submodel', 'usecase_detail_id', 'variable_name', 'value']].dropna()
    td_variable_list_scenarios = td_variable_list[td_variable_list['scope']=='Scenarios']
    td_variable_list_others = td_variable_list[td_variable_list['scope']!='Scenarios']
    if len(td_variable_list_scenarios) == 0:
        st.warning('このスタディで、走行パターン系パラメータの変更はありません。')
    else:
        if td_variable_list_scenarios['submodel'].tolist()[0] == df_usecase_td['submodel'].tolist()[0]:
            df_usecase_td['td'] = td_variable_list_scenarios['td'].tolist()[0]
            df_usecase_td['scope'] = td_variable_list_scenarios['scope'].tolist()[0]
            df_usecase_td['overall_value'] = df_usecase_td['value']
            df_usecase_td['parameter_unit'] = ''
            df_usecase_td['project_id'] = td_variable_list_scenarios['project_id'].tolist()[0]
            df_usecase_td['phase_id'] = td_variable_list_scenarios['phase_id'].tolist()[0]
            df_usecase_td['variation_id'] = td_variable_list_scenarios['variation_id'].tolist()[0]
            df_usecase_td['study_id'] = td_variable_list_scenarios['study_id'].tolist()[0]
            td_variable_list_scenarios = pd.concat([df_usecase_td, td_variable_list_scenarios])
        else:
            st.info('Studyに入力されたユースケースサブモデルと、ユースケース' + usecase_name + 'に紐づくサブモデルが異なっています。Studyに入力されたサブモデルを使用します。')
    
    td_variable_list = pd.concat([td_variable_list_others, td_variable_list_scenarios])

     
    yaml_data = {}
    overall_value=None
        #df_usecase_tdをtd_variable_listに組み込む
  
    # Populate the dictionary based on the DataFrame
    for index, row in td_variable_list.iterrows():
        if row['overall_value'] is not None or row['overall_value']!='':
            td_value = row['td']
            scope_value = row['scope']
            submodel_value = row['submodel']
            variable_name_value = row['variable_name']
            unit = row['parameter_unit']
            try:
                temp_value = float(row['overall_value'])  # Convert to float first
            except:
                temp_value=row['overall_value'] 
            
            # Check if the value is an integer
            if isinstance(temp_value,int):
                overall_value = int(temp_value)  # Convert to int if it's an integer
            elif isinstance(temp_value, str) and unit=='Map': # 山口　added elif to see if value is a map name
                df_map_variables = sql.get_map_variables_by_name(temp_value)
                #st.write(df_map_variables)
                if df_map_variables is not None:
                    TABLE_value = df_map_variables[df_map_variables['axis']=='TABLE']
                    MAP_value = df_map_variables[df_map_variables['axis']=='MAP']
                    CUBE_value = df_map_variables[df_map_variables['axis']=='CUBE']
                    #st.write(TABLE_value)
                    #st.write(MAP_value)
                    #st.write(CUBE_value)

                    if len(TABLE_value)==1:
                        TABLE_value = TABLE_value['value'].tolist()[0]
                        X_value = df_map_variables[df_map_variables['axis']=='X']['value'].tolist()[0]
                        overall_value = [X_value, TABLE_value]
                    elif len(MAP_value)==1:
                        MAP_value = MAP_value['value'].tolist()[0].replace(';',',')
                        X_value = df_map_variables[df_map_variables['axis']=='X']['value'].tolist()[0]
                        Y_value = df_map_variables[df_map_variables['axis']=='Y']['value'].tolist()[0]
                        overall_value = [X_value, Y_value, MAP_value]
                    elif len(CUBE_value)==1:
                        CUBE_value = CUBE_value['value'].tolist()[0].replace('|',',').replace(';',',')
                        X_value = df_map_variables[df_map_variables['axis']=='X']['value'].tolist()[0]
                        Y_value = df_map_variables[df_map_variables['axis']=='Y']['value'].tolist()[0]
                        Z_value = df_map_variables[df_map_variables['axis']=='Z']['value'].tolist()[0]
                        overall_value = [X_value, Y_value, Z_value, CUBE_value]
                else:
                    st.warning(variable_name_value +'に紐づくMAPはありませんでした')
                    overall_value=None
                    continue
            elif isinstance(temp_value, str) and variable_name_value == 'Time_Series': #変数名がTime_Seriesの時の特例を設定する
            #TODO　　ここでTimeSeriesを並び替えないと絶対事故る
                usecase_parameter_sort_map = {5:1, 6:2, 7:3, 27:4, 8:5}
                timeseries_variable = td_variable_list[td_variable_list['variable_name']=='Time_Series']
                timeseries_variable['sort_key'] = timeseries_variable['usecase_detail_id'].map(usecase_parameter_sort_map)
                timeseries_variable = timeseries_variable.sort_values(by='sort_key')
                overall_value = timeseries_variable['overall_value'].values.tolist()
            
            else:
                overall_value = temp_value  # Keep it as float if it's not
            ##overall_valueが空白、もしくはリストの各要素に空白がある場合、データ不足としてYAML化を防ぐ
            ##Timeseries以外は。Timeseriesはカンマ区切りの文字列としてくるのでスキップ
            
            if variable_name_value != 'Time_Series':
                if not isinstance(overall_value,list):
                    try: 
                        tmp = float(overall_value)
                    except ValueError as e:
                        st.warning(variable_name_value + 'は数字以外が含まれています。Simへの入力をスキップします。')
                        continue
                else:
                    flag_not_floatable = False
                    for lst in overall_value:
                        for v in lst:
                            try:
                                tmp = float(v)
                            except ValueError as e:
                                st.warning(variable_name_value + 'のマップには数値以外が含まれています。Simへの入力をスキップします。')
                                flag_not_floatable = True
                                break
                        if flag_not_floatable:
                            break
                    if flag_not_floatable:
                        continue

            
            
            # Create the key for the outermost level
            project_id = row['project_id']
            phase_id = row['phase_id']
            variation_id = row['variation_id']
            study_id = row['study_id']

            outer_key = f"{project_id},{phase_id},{variation_id},{study_id},{usecase_name}" # 山口走行パターンに応じてシミュレーション結果からDBに返す必要のあるパラメータを決めるため　　ユースケース名にキーに追加
            if outer_key not in yaml_data:
                yaml_data[outer_key] = {}
            
            # Use td_value as the next level key
            if td_value not in yaml_data[outer_key]:
                yaml_data[outer_key][td_value] = {}
            
            if scope_value not in yaml_data[outer_key][td_value]:
                yaml_data[outer_key][td_value][scope_value] = {}
            
            if submodel_value not in yaml_data[outer_key][td_value][scope_value]:
                yaml_data[outer_key][td_value][scope_value][submodel_value] = {}
            
            yaml_data[outer_key][td_value][scope_value][submodel_value][variable_name_value] = overall_value
            #st.write(overall_value)
        
    st.write(yaml_data)
    # Get the current date and time for the filename
    # now = datetime.datetime.now()
    # current_datetime = now.strftime("%Y%m%d_%H%M%S")
    # output_filename = f'output_{current_datetime}.yaml'
    # Write the nested dictionary to a YAML file
    if yaml_data is None:
        st.error('nothing to write')
        return
    filename_suffix = outer_key.rsplit(',', 1)[0].replace(',','') #removing comma #山口　　ユースケース名はファイル名に含めたくない
    yaml_file_name = f'variable_{filename_suffix}.yaml'
    #update the path to OneDrive
    yaml_file_path = rf'C:\Users\BSN00147\OneDrive - Nissan Motor Corporation\simrequest_variables\{yaml_file_name}'
    with open(yaml_file_path, 'w') as yaml_file:
        yaml.dump(yaml_data, yaml_file, default_flow_style=False, allow_unicode=True)
    print(f"JSON file has been created and saved as '{yaml_file_path}'.")          
    st.info(study_id + "のSim実行をリクエストしました。結果が反映されるまでしばらくお待ちください。")






# #チョー 12/13
# def create_yaml_file(td_variable_list):# 山口　mapにも対応さSせる 12/16
#     # Initialize the nested dictionary structure
#     yaml_data = {}
#     overall_value=None
#     #st.write(td_variable_list)
#     # Populate the dictionary based on the DataFrame
#     for index, row in td_variable_list.iterrows():
#         if row['overall_value'] is not None or row['overall_value']!='':
            
#             td_value = row['td']
#             scope_value = row['scope']
#             submodel_value = row['submodel']
#             variable_name_value = row['variable_name']
#             unit = row['parameter_unit']
#             try:
#                 temp_value = float(row['overall_value'])  # Convert to float first
#             except:
#                 temp_value=row['overall_value']
#             # Check if the value is an integer
#             if isinstance(temp_value,int):
#                 overall_value = int(temp_value)  # Convert to int if it's an integer
#             elif isinstance(temp_value, str) and unit=='Map': # 山口　added elif to see if value is a map name
#                 df_map_variables = sql.get_map_variables_by_name(temp_value)
#                 #st.write(df_map_variables)
#                 if df_map_variables is not None:
#                     TABLE_value = df_map_variables[df_map_variables['axis']=='TABLE']
#                     MAP_value = df_map_variables[df_map_variables['axis']=='MAP']
#                     CUBE_value = df_map_variables[df_map_variables['axis']=='CUBE']
#                     #st.write(TABLE_value)
#                     #st.write(MAP_value)
#                     #st.write(CUBE_value)

#                     if len(TABLE_value)==1:
#                         TABLE_value = TABLE_value['value'].tolist()[0]
#                         X_value = df_map_variables[df_map_variables['axis']=='X']['value'].tolist()[0]
#                         overall_value = [X_value, TABLE_value]
#                     elif len(MAP_value)==1:
#                         MAP_value = MAP_value['value'].tolist()[0].replace(';',',')
#                         X_value = df_map_variables[df_map_variables['axis']=='X']['value'].tolist()[0]
#                         Y_value = df_map_variables[df_map_variables['axis']=='Y']['value'].tolist()[0]
#                         overall_value = [X_value, Y_value, MAP_value]
#                     elif len(CUBE_value)==1:
#                         CUBE_value = CUBE_value['value'].tolist()[0].replace('|',',').replace(';',',')
#                         X_value = df_map_variables[df_map_variables['axis']=='X']['value'].tolist()[0]
#                         Y_value = df_map_variables[df_map_variables['axis']=='Y']['value'].tolist()[0]
#                         Z_value = df_map_variables[df_map_variables['axis']=='Z']['value'].tolist()[0]
#                         overall_value = [X_value, Y_value, Z_value, CUBE_value]
#                     #st.write(overall_value)
#                 else:
#                     st.write(variable_name_value +'に紐づくMAPはありませんでした')
#                     overall_value=None
#                     continue

#             else:
#                 overall_value = temp_value  # Keep it as float if it's not
            
#             # Create the key for the outermost level
#             project_id = row['project_id']
#             phase_id = row['phase_id']
#             variation_id = row['variation_id']
#             study_id = row['study_id']

#             outer_key = f"{project_id},{phase_id},{variation_id},{study_id}"
            
#             if outer_key not in yaml_data:
#                 yaml_data[outer_key] = {}
            
#             # Use td_value as the next level key
#             if td_value not in yaml_data[outer_key]:
#                 yaml_data[outer_key][td_value] = {}
            
#             if scope_value not in yaml_data[outer_key][td_value]:
#                 yaml_data[outer_key][td_value][scope_value] = {}
            
#             if submodel_value not in yaml_data[outer_key][td_value][scope_value]:
#                 yaml_data[outer_key][td_value][scope_value][submodel_value] = {}
            
#             yaml_data[outer_key][td_value][scope_value][submodel_value][variable_name_value] = overall_value
#             #st.write(overall_value)
#             #st.write(yaml_data)
#     # Get the current date and time for the filename
#     # now = datetime.datetime.now()
#     # current_datetime = now.strftime("%Y%m%d_%H%M%S")
#     # output_filename = f'output_{current_datetime}.yaml'
#     # Write the nested dictionary to a YAML file
#     print(yaml_data)
#     filename_suffix = outer_key.replace(',','') #removing comma
#     yaml_file_name = f'variable_{filename_suffix}.yaml'
#     #update the path to OneDrive
#     yaml_file_path = rf'C:\Users\BSN00147\OneDrive - Nissan Motor Corporation\simrequest_variables\{yaml_file_name}'
#     with open(yaml_file_path, 'w') as yaml_file:
#         yaml.dump(yaml_data, yaml_file, default_flow_style=False, allow_unicode=True)
#     # print(f"JSON file has been created and saved as '{output_filename}'.")

@st.dialog("sim実行", width='large')#山口 sim実行用のダイアログ12/6 wip
def sim():

    """
    シナリオリストでSim実行を押したときに表示されるダイアログ
    Studyを選択させ、そのスタディの変数情報をYAMLに変換する
    """
    sim_prj_info_list = st.session_state.sim_prj_info_list
    sim_data_stuck = st.session_state.sim_data_stuck
    #Study_id選択一覧の表示
    study_ids = list(set(sim_prj_info_list['study_id'].tolist()))
    selected_study_id = st.selectbox(
        '実行するStudy_id:',
        study_ids,
        key='selected_study_id'
        )
    studylen = len(selected_study_id)
    selected_study=sim_data_stuck.loc[:, sim_data_stuck.columns.str[-studylen:].str.contains(str(selected_study_id))] # 山口　単にselected_study_idをcontainsで絞っても１つにならないことがあるため、列名の後ろ（study文字数）分を見る　12/26
    
    TDrow = selected_study[(selected_study.loc[:,selected_study.columns.str.contains('senario_parameter_id')]==13).values]
    TDname = TDrow.loc[:, TDrow.columns.str.contains(';value;')]
    if TDname.values[0] is None or TDname.values[0] == '':#StudyにTD名がない時の実行防止 2025/9/3
        st.error('選択されたStudyには実行するTD名の入力がありません')
        return
    usecase_name_row = selected_study[(selected_study.loc[:,selected_study.columns.str.contains('senario_parameter_id')]==14).values] # 山口　走行パターンに応じてシミュレーション結果からDBに返す必要のあるパラメータを決めるため　　取得を追加6/26
    usecase_name = usecase_name_row.loc[:, usecase_name_row.columns.str.contains(';value;')].values[0].tolist()[0]
    senario_submodelrow=selected_study[(selected_study.loc[:,selected_study.columns.str.contains('senario_parameter_id')]==70).values]# 山口　シナリオサブモデル名の取得 12/26
    senario_submodel = senario_submodelrow.loc[:, senario_submodelrow.columns.str.contains(';value;')].values[0].tolist()[0]
    if senario_submodel is None or senario_submodel == '':#Studyにシナリオサブモデル名がない時の実行防止 2025/9/3
        st.error('選択されたStudyには実行するシナリオサブモデル名の入力がありません')
        return
    project_id = selected_study.loc[0, selected_study.columns.str.contains('project_id')].values.tolist()[0]  # 山口　どのスタディか絞り込むために必要な情報の追加　12/16
    phase_id = selected_study.loc[0, selected_study.columns.str.contains('phase_id')].values.tolist()[0]  # 山口　どのスタディか絞り込むために必要な情報の追加　12/16
    variation_id = selected_study.loc[0,selected_study.columns.str.contains('variation_id')].values.tolist()[0]  # 山口　どのスタディか絞り込むために必要な情報の追加　12/16
    tdname_value = TDname.iloc[0,0]
    # print('tdname_value:: ',tdname_value)

    #チョー 12/13
    if st.button("実行") and senario_submodel is not None and TDname is not None:
        #実行するTDの変数となる項目の一覧を取得
        td_variable_list = sql.get_td_senario(project_id, phase_id, variation_id, selected_study_id, senario_submodel, [tdname_value])  #山口　どのスタディか絞り込むために必要な情報を引数に追加　12/16
        
        #st.write(td_variable_list)
        td_variable_list = td_variable_list.dropna(subset=['overall_value','variable_name']) # 山口　空白行は渡すパラメータに含まない
        if len(td_variable_list) >0:
            create_yaml_file(td_variable_list, usecase_name)

@st.dialog("Dashboard表示")  # 山口 Dashboard表示用ダイアログ　12/18
def to_dashboard():
    sim_prj_info_list = st.session_state.sim_prj_info_list
    sim_data_stuck = st.session_state.sim_data_stuck
    study_ids = list(set(sim_prj_info_list['study_id'].tolist()))
    selected_study_id = st.selectbox(
        '表示するStudy_id:',
        study_ids,
        key='selected_study_dashboard_id'
        )
    
    selected_study=sim_data_stuck.loc[:, sim_data_stuck.columns.str.contains(selected_study_id)]
    TDrow = selected_study[(selected_study.loc[:,selected_study.columns.str.contains('senario_parameter_id')]==13).values]
    TDname = TDrow.loc[:, TDrow.columns.str.contains(';value;')]
    project_id = selected_study.loc[0, selected_study.columns.str.contains('project_id')].tolist()[0]  # 山口　どのスタディか絞り込むために必要な情報の追加　12/16
    phase_id = selected_study.loc[0, selected_study.columns.str.contains('phase_id')].tolist()[0]  # 山口　どのスタディか絞り込むために必要な情報の追加　12/16
    variation_id = selected_study.loc[0,selected_study.columns.str.contains('variation_id')].tolist()[0]  # 山口　どのスタディか絞り込むために必要な情報の追加　12/16
    tdname_value = TDname.iloc[0,0]
    SysA_project_file_name = str(int(project_id)) + str(int(phase_id)) + str(int(variation_id)) + str(selected_study_id)
    if st.button("Dashboard表示 wip"):
        st.write("link will be here : http://10.20.147.231:8510")
        st.write("project file : " + SysA_project_file_name)
    
# @st.dialog("RFLへ転記") # 山口　RFL転記用ダイアログ　2/6
# def send_to_RFL():
#     sim_prj_info_list = st.session_state.sim_prj_info_list
#     sim_data_stuck = st.session_state.sim_data_stuck

#     fixed_study_ids =  sim_data_stuck[sim_data_stuck.loc[:, sim_data_stuck.columns.str.contains('value')]=='FIXED'].loc[:, sim_data_stuck.columns.str.contains('study_id')].tolist()#value列にFixedとかかれている行のstudy_id列
#     selected_study_id = st.selectbox(
#         '転記するStudyID:',
#         fixed_study_ids,
#         key='selected_study_dashboard_id'
#         )

@st.dialog("RFLへ転記") # 山口　RFL転記用ダイアログ　2/6 複数プロジェクト選択されていると起用に選択肢を追加する必要あり　2/11 whats a mess 
def send_to_RFL():
    now = datetime.datetime.now()

    sim_data_stuck = st.session_state.sim_data_stuck

    #各プロジェクト情報の表示、複数あれば選ばせる
    if len(st.session_state['selectoption1'])==1:
                st.write("プロジェクト：" + st.session_state['selectoption1'][0])
                selectoption1 = st.session_state['selectoption1'][0]
    else:
        selectoption1 = st.selectbox(
            'プロジェクト:',
            st.session_state['selectoption1'],
            key='unique_key_1'
    
        )
    if len(st.session_state['selectoption2'])==1:
                st.write("仕向け：" + st.session_state['selectoption2'][0])
                selectoption2 = st.session_state['selectoption2'][0]
    else:
        selectoption2 = st.selectbox(
            '仕向け:',
            st.session_state['selectoption2'],
            key='unique_key_2'
    
        )
    if len(st.session_state['selectoption3'])==1:
                st.write("駆動方式：" + st.session_state['selectoption3'][0])
                selectoption3 = st.session_state['selectoption3'][0]
    else:
        selectoption3 = st.selectbox(
            '駆動方式:',
            st.session_state['selectoption3'],
            key='unique_key_3'
    
        )
    if len(st.session_state['selectoption4'])==1:
                st.write("ロット：" + st.session_state['selectoption4'][0])
                selectoption4 = st.session_state['selectoption4'][0]
    else:
        selectoption4 = st.selectbox(
            'ロット：',
            st.session_state['selectoption4'],
            key='unique_key_4'
    
        )
    if len(st.session_state['selectoption5'])==1:
                st.write("フェーズ：" + st.session_state['selectoption5'][0])
                selectoption5 = st.session_state['selectoption5'][0]
    else:
        selectoption5 = st.selectbox(
            'フェーズ：',
            st.session_state['selectoption5'],
            key='unique_key_5'
    
        )
    if len(st.session_state['selectoption6'])==1:
                st.write("バリエーション：" + st.session_state['selectoption6'][0])
                selectoption6 = st.session_state['selectoption6'][0]
    else:
        selectoption6 = st.selectbox(
            'バリエーション：',
            st.session_state['selectoption6'],
            key='unique_key_6'
    
        )
    value_columns = [col for col in sim_data_stuck.columns if 'value' in col and 'original' not in col]
    fixed_columns = [col for col in value_columns if (sim_data_stuck[col] == 'FIXED').any()]
    
    fixed_study_ids = [col.split(selectoption6)[-1]  for col in fixed_columns]
    selected_study_id = st.selectbox(
        '転記するStudyID:',
        fixed_study_ids,
        key='selected_study_dashboard_id'
        )
    df_selected_study = sim_data_stuck.loc[:, sim_data_stuck.columns.str.contains(selected_study_id)]
    #選択されたスタディの必要情報を取得する
    senario_parameter_col = [col for col in df_selected_study.columns if 'senario_parameter_id' in col][0] #senario_parameter_idが含まれる列はこの時点で1列の想定
    selected_performance = df_selected_study[df_selected_study[senario_parameter_col]==15].loc[:,df_selected_study.columns.str.contains(';value;')].values.tolist()[0][0]#変な取り方の自覚あるけど直す時間ない
    if selected_performance is None:
        st.error(selected_study_id + "には性能領域の入力がありません。")
        return 
    selected_requirement = df_selected_study[df_selected_study[senario_parameter_col]==3].loc[:,df_selected_study.columns.str.contains(';value;')].values.tolist()[0][0]
    if selected_requirement is None:
        st.error(selected_study_id + "には目標性能の入力がありません。")
        return
    selected_usecase = df_selected_study[df_selected_study[senario_parameter_col]==14].loc[:,df_selected_study.columns.str.contains(';value;')].values.tolist()[0][0]
    if selected_usecase is None:
        st.error(selected_study_id + "には走行パターン名の入力がありません。")
        return

    project_id = df_selected_study.loc[:,df_selected_study.columns.str.contains(';project_id;')].values.tolist()[0][0]
    phase_id = df_selected_study.loc[:,df_selected_study.columns.str.contains(';phase_id;')].values.tolist()[0][0]
    variation_id = df_selected_study.loc[:,df_selected_study.columns.str.contains(';variation_id;')].values.tolist()[0][0]
    parameter_name_1_col = [col for col in df_selected_study.columns if 'parameter_name_1' in col][0]
    parameter_name_1_col = [col for col in df_selected_study.columns if 'parameter_name_1' in col][0]
    #send_info_col = [col for col in df_selected_study.columns if 'rflcategory' in col or 'rflid' in col or 'parameter_name_1' in col or 'parameter_name_2' in col or ';value;' in col] #山口　この方法では列の順番は不定になる　固定するため書き直し 2/13
    rflcategory_col = [col for col in df_selected_study.columns if 'rflcategory' in col][0]
    rflid_col = [col for col in df_selected_study.columns if 'rflid' in col][0]
    parameter_name_2_col = [col for col in df_selected_study.columns if 'parameter_name_2' in col][0]
    value_col =[col for col in df_selected_study.columns if ';value;' in col][0]
    send_info_col = [parameter_name_1_col, parameter_name_2_col,  value_col, rflcategory_col, rflid_col]
    # st.write(df_selected_study[send_info_col])
    #山口　下記df_send_info定義は、rflidが記入あるものとしたい 
    # df_send_info = df_selected_study[df_selected_study[parameter_name_1_col]=='Output ' +selected_performance][send_info_col]
    df_send_info = df_selected_study.dropna(subset=[value_col,  rflid_col])[send_info_col]
    st.write('走行パターン' + selected_usecase)
    # st.write(selected_performance)
    # st.write(project_id)
    # st.write(phase_id)
    # st.write(variation_id)
    st.write(df_send_info)
    if st.button('実行'):
        sql.update_RFL_by_senario(selected_performance, selected_requirement, selected_usecase, project_id, phase_id, variation_id, df_send_info, username, now)
        #st.write('pretend something happens')
        st.success("RFL更新しました")



@st.dialog("正常終了")
def create_success_dia():
    st.success("正常に作成が完了しました。")

def create_select_boxes(archi_list, col_count):

    if col_count == 1:
        compare_label = "ベース(比較基準)"
    elif col_count == 2:
        compare_label = "リファレンス(比較対象)"
    labels = ["PTシステムタイプ","プロジェクト", "仕向け", "駆動方式", "ロット", "フェーズ","バリエーション"]
    st.markdown(compare_label, unsafe_allow_html=True)

    selected_archi = st.selectbox(
        labels[0],
        archi_list,
        key = f'select_archi_unique_key_{col_count}',        
    )
    if len(st.session_state['architecture_ls']) < col_count:
        st.session_state['architecture_ls'].append(selected_archi)
    else:
        st.session_state['architecture_ls'][col_count - 1] = selected_archi

    z_model_code = sql.get_project("z_model_code",[selected_archi])
    
    compare_option1 = st.selectbox(labels[1], z_model_code, key=f"main_opt1_{col_count}", label_visibility="visible")
    if len(st.session_state['compare_option1']) < col_count:
        st.session_state['compare_option1'].append(compare_option1)
    else:
        st.session_state['compare_option1'][col_count - 1] = compare_option1

    destination = sql.get_project("destination",[compare_option1])
    compare_option2 = st.selectbox(labels[2], destination, key=f"main_opt2_{col_count}", label_visibility="visible")
    if len(st.session_state['compare_option2']) < col_count:
        st.session_state['compare_option2'].append(compare_option2)
    else:
        st.session_state['compare_option2'][col_count - 1] = compare_option2

    drive_system = sql.get_project("drive_system",[compare_option1],[compare_option2])
    compare_option3 = st.selectbox(labels[3], drive_system, key=f"main_opt3_{col_count}", label_visibility="visible")
    if len(st.session_state['compare_option3']) < col_count:
        st.session_state['compare_option3'].append(compare_option3)
    else:
        st.session_state['compare_option3'][col_count - 1] = compare_option3

    project_lot = sql.get_project("project_lot",[compare_option1],[compare_option2],[compare_option3])
    compare_option4 = st.selectbox(labels[4], project_lot, key=f"main_opt4_{col_count}", label_visibility="visible")
    if len(st.session_state['compare_option4']) < col_count:
        st.session_state['compare_option4'].append(compare_option4)
    else:
        st.session_state['compare_option4'][col_count - 1] = compare_option4

    if compare_option4 is not None:

        compare_phase_list = sql.get_project("phase_list",[compare_option1],[compare_option2],[compare_option3],[compare_option4])

        compare_option5 = st.selectbox(labels[5], compare_phase_list, key=f"main_opt5_{col_count}", label_visibility="visible")
        if len(st.session_state['compare_option5']) < col_count:
            st.session_state['compare_option5'].append(compare_option5)
        else:
            st.session_state['compare_option5'][col_count - 1] = compare_option5

        varation_list=sql.get_varation([compare_option1],[compare_option2],[compare_option3],[compare_option4],[compare_option5])
        varation_select_list = varation_list['modified_string'].tolist()
        selected_varation = st.selectbox(labels[6], varation_select_list, key=f"main_opt6_{col_count}", label_visibility="visible")

        mapping = dict(zip(varation_list['modified_string'], varation_list['z_wp_name_get_str']))

        selected_wp_name = mapping[selected_varation]

        if len(st.session_state['compare_option6']) < col_count:
            st.session_state['compare_option6'].append(selected_wp_name)
        else:
            st.session_state['compare_option6'][col_count - 1] = selected_wp_name


# # Dialog function
# @st.dialog("設計値比較", width="large")
# def compare_se():
#     if 'architecture_ls' not in st.session_state:
#         st.session_state['architecture_ls'] = []
#     # List of compare options
#     compare_options = ['compare_option1', 'compare_option2', 'compare_option3', 'compare_option4', 'compare_option5','compare_option6']

#     # Initialize session state for each compare option if not already set
#     for option in compare_options:
#         if option not in st.session_state:
#             st.session_state[option] = []
#     architecture_list = sql.get_project("architecture_name")
#     architecture_list = ['選択してください。'] + architecture_list
    
#     col1, col2 = st.columns(2)
    
#     with col1:
#         create_select_boxes(architecture_list, 1)
#     with col2:
#         create_select_boxes(architecture_list, 2)
#     if all(st.session_state[option] for option in compare_options):
#         if st.button("完了"):

#             compare_option1 = list(set(st.session_state['compare_option1']))
#             compare_option2 = list(set(st.session_state['compare_option2']))
#             compare_option3 = list(set(st.session_state['compare_option3']))
#             compare_option4 = list(set(st.session_state['compare_option4']))
#             compare_option5 = list(set(st.session_state['compare_option5']))
#             compare_option6 = list(set(st.session_state['compare_option6']))
            
#             if (
#                 None not in compare_option1 and
#                 None not in compare_option2 and
#                 None not in compare_option3 and
#                 None not in compare_option4 and
#                 None not in compare_option5 and
#                 None not in compare_option6
#             ):
#                 df1,df2=sql.posgre_get_compare_data(compare_option1,compare_option2,compare_option3,compare_option4,compare_option5,compare_option6)
#                 st.session_state.prj_info_list = df1
#                 st.session_state.se_data_stuck = df2
#                 st.session_state.compare_click = True
#                 st.rerun()
#             else:
#                 st.error("全ての項目を選択してください。")

# def create_phase_dia1():
#     # if 'create_option1' not in st.session_state:
#     #     st.session_state['create_option1'] = []
    
#     architecture_list = sql.get_project("architecture_name")
#     selected_archi = st.selectbox(
#         'PTシステムタイプ',
#         architecture_list,
#         key ='select_archi_unique_key1'
#     )

#     z_model_code = sql.get_project("z_model_code",[selected_archi])

#     # Use the previously selected value if it exists
#     create_option1 = st.selectbox("プロジェクト", z_model_code, key=f"create_opt1")

#     destination = sql.get_project("destination",[create_option1])

#     create_option2 = st.selectbox("仕向け", destination, key=f"create_opt2")

#     drive_system = sql.get_project("drive_system",[create_option1],[create_option2])
#     create_option3 = st.selectbox("駆動方式", drive_system, key=f"create_opt3")

#     if create_option3 is not None:
        
#         project_lot = sql.get_project("project_lot",[create_option1],[create_option2],[create_option3])
#         create_option4 = st.selectbox("ロット", project_lot, key=f"create_opt4")
    
#         create_phase_list = sql.get_project("phase_list",[create_option1],[create_option2],[create_option3],[create_option4])

#         all_phase_list = sql.get_all_phase(create_phase_list, "NOT")

#         create_option5_before = st_free_text_select(
#             label="フェーズ",
#             options=all_phase_list,
#             delay=300,
#             index=0
#         )
#         if st.button("次へ"):
#             st.session_state.phase_click = False
#             st.session_state.next_click = True
#             phase_id, is_new_phase = sql.get_phase_id(create_option5_before)

#             if 'new_phase_id' not in st.session_state:
#                 st.session_state['new_phase_id'] = 0
#             st.session_state.new_phase_id = phase_id[0]
#             if 'new_phase_value' not in st.session_state:
#                     st.session_state['new_phase_value'] = []
#             if 'is_new_phase' not in st.session_state:
#                 st.session_state['is_new_phase'] = False
#             st.session_state.new_phase_value = create_option5_before
#             if is_new_phase is True:
#                 st.session_state.is_new_phase = True
            
#             st.rerun()

# def create_phase_dia2():

#     architecture_list = sql.get_project("architecture_name")
#     selected_archi = st.selectbox(
#         'PTシステムタイプ',
#         architecture_list,
#         key ='select_archi_unique_key2'
#     )

#     z_model_code2 = sql.get_project("z_model_code",[selected_archi])

#     create_option21 = st.selectbox("プロジェクト", z_model_code2, key=f"create_opt21")

#     destination2 = sql.get_project("destination",[create_option21])
#     create_option22 = st.selectbox("仕向け", destination2, key=f"create_opt22")

#     drive_system2 = sql.get_project("drive_system",[create_option21],[create_option22])
#     create_option23 = st.selectbox("駆動方式", drive_system2, key=f"create_opt23")
    
#     if create_option23 is not None:

#         project_lot2 = sql.get_project("project_lot",[create_option21],[create_option22],[create_option23])
#         create_option24 = st.selectbox("ロット", project_lot2, key=f"create_opt24")   

#         create_phase_list2 = sql.get_project("phase_list",[create_option21],[create_option22],[create_option23],[create_option24])
#         all_phase_list2 = sql.get_all_phase(create_phase_list2, "ALL")
        
#         create_option5_after = st.selectbox("フェーズ", create_phase_list2, key=f"create_opt25")
#         if st.button("作成"):
#             st.session_state.next_click = False
#             st.session_state.create_click = True
#             stuck =sql.posgre_copy_data([create_option21],[create_option22],[create_option23],[create_option24],[create_option5_after])

#             stuck['phase_id'] = st.session_state.new_phase_id

#             if 'is_new_phase' not in st.session_state or st.session_state['is_new_phase'] is False:   
#                 sql.insert_project_parameters(stuck)

#             elif st.session_state['is_new_phase'] is True: 
#                 phase_inserted = sql.insert_phase(st.session_state.new_phase_id,st.session_state.new_phase_value) 
#                 if phase_inserted is True:
#                     sql.insert_project_parameters(stuck)
#             st.rerun()


#Kyaw #CompareSE Upd 08/22
@st.dialog("設計値比較", width="large")
def compare_se():
    # Always start with 2 columns (col1, col2)
    if 'num_cols' not in st.session_state:
        st.session_state['num_cols'] = 2
    # Only set num_cols from last_num_cols if this is the first open of the dialog
    if 'dialog_opened_once' not in st.session_state or not st.session_state['dialog_opened_once']:
        if 'last_num_cols' in st.session_state:
            st.session_state['num_cols'] = st.session_state['last_num_cols']
        st.session_state['dialog_opened_once'] = True
    df_bookmarks = st.session_state['se_df_bookmarks']

    df_filtered = df_bookmarks[df_bookmarks['value'] != '選択されていません']
    df_filtered = df_filtered.sort_values(['bookmark_number', 'category'])
    # Remove bookmarks that have more than 6 entries
    df_filtered = df_filtered[
        df_filtered.groupby('bookmark_number')['value'].transform('count') <= 6
    ]
    bookmark_list = (
        df_filtered
        .groupby('bookmark_number')['value']
        .apply(lambda x: ';'.join(x) + ';')
        .tolist()
    )
    # Baseline columns from current selection BEFORE rendering the widget
    current_selected = st.session_state.get('selected_bookmarks', [])

    st.session_state['num_cols'] = max(2, len(current_selected),st.session_state['num_cols'])

    # Layout for Add and Remove buttons BEFORE the widget so mutation is allowed
    extra_col, add_col, remove_col = st.columns([10,1,1])
    with add_col:
        if st.button('**➕**'):
            st.session_state['num_cols'] += 1
            
    with remove_col:
        # Disable remove if only 2 columns remain
        remove_disabled = st.session_state['num_cols'] <= 2
        if st.button('**➖**', disabled=remove_disabled): 
            if st.session_state['num_cols'] > 2:
                # Trim the last bookmark BEFORE widget instantiation
                if isinstance(current_selected, list) and len(current_selected) > 0 and len(current_selected) == st.session_state['num_cols']:
                    st.session_state['selected_bookmarks'] = current_selected[:-1]
                # Decrease the column count
                st.session_state['num_cols'] -= 1
                
                

    selected_bookmarks = st.multiselect(
        "お気に入りを選択してください。",
        options=bookmark_list,
        key='selected_bookmarks',
        # help="1列目がベース、以降はリファレンスとして表示されます。",
        placeholder="1つ目の選択がベース、2つ目以降はリファレンスとして表示されます。"
    )
    st.session_state['num_cols'] = max(2, len(selected_bookmarks), st.session_state['num_cols'])

    session_keys = [
        'select_archi_unique_key_{}',
        'select_project_unique_key_{}',
        'select_destination_unique_key_{}',
        'select_drivesystem_unique_key_{}',
        'select_lot_unique_key_{}',
        'select_phase_unique_key_{}',
        'select_variation_unique_key_{}'
    ]

    for col_idx, bookmark in enumerate(selected_bookmarks):
        # Split by ';' and remove empty strings
        values = [v for v in bookmark.split(';') if v]
        for i, value in enumerate(values):
            if i < len(session_keys):
                st.session_state[session_keys[i].format(col_idx)] = value

    # Small spacer between multiselect and header labels
    # st.markdown('<div style="height:0.75em"></div>', unsafe_allow_html=True)

    num_cols_for_header = st.session_state['num_cols']
    header_cols = st.columns([1, num_cols_for_header - 1])
    with header_cols[0]:
        st.write('**ベース(比較基準)**')
    with header_cols[1]:
        st.write('**リファレンス(比較対象)**')

    # Create columns for each pair
    cols = st.columns(st.session_state['num_cols'])
    for i, col in enumerate(cols):
        with col:
            architecture_list = sql.get_project("architecture_name")
            full_archi_list = ['選択してください。'] + architecture_list
            last_archi_key = f'last_select_archi_{i}'
            default_archi = st.session_state.get(last_archi_key, '選択してください。')

            if default_archi not in full_archi_list:
                default_archi = '選択してください。'
            selected_archi = st.selectbox(
                f'PTシステムタイプ',
                full_archi_list,
                key=f'select_archi_unique_key_{i}',
                index=full_archi_list.index(default_archi)
            )

            z_model_code = sql.get_project("z_model_code",[selected_archi])
            default_project = st.session_state.get(f'last_select_project_{i}', None)
            selected_project = st.selectbox(
                f'プロジェクト',
                # ['[J32V]', 'P33C', '[H61P]'],
                z_model_code,
                key=f'select_project_unique_key_{i}',
                index=z_model_code.index(default_project) if default_project in z_model_code else 0
            )

            destination = sql.get_project("destination",[selected_project])
            default_destination = st.session_state.get(f'last_select_destination_{i}', None)
            selected_destination = st.selectbox(
                f'仕向け',
                # ['JPN', 'US'],
                destination,
                key=f'select_destination_unique_key_{i}',
                index=destination.index(default_destination) if default_destination in destination else 0
            )

            drive_system = sql.get_project("drive_system",[selected_project],[selected_destination])
            default_drivesystem = st.session_state.get(f'last_select_drivesystem_{i}', None)
            selected_drivesystem = st.selectbox(
                f'駆動方式',
                # ['2WD','4WD'],
                drive_system,
                key=f'select_drivesystem_unique_key_{i}',
                index=drive_system.index(default_drivesystem) if default_drivesystem in drive_system else 0
            )

            lot = sql.get_project("project_lot",[selected_project],[selected_destination],[selected_drivesystem])
            default_lot = st.session_state.get(f'last_select_lot_{i}', None)
            selected_lot = st.selectbox(
                f'ロット',
                # ['Pre-Pro','[V]/[U]'],
                lot,
                key=f'select_lot_unique_key_{i}',
                index=lot.index(default_lot) if default_lot in lot else 0
            )

            phase = sql.get_project("phase_list",[selected_project],[selected_destination],[selected_drivesystem],[selected_lot])
            default_phase = st.session_state.get(f'last_select_phase_{i}', None)
            selected_phase = st.selectbox(
                f'フェーズ',
                # ['中間確認会#1', '中間確認会#2', 'PTシステムレビュー#1'],
                phase,
                key=f'select_phase_unique_key_{i}',
                index=phase.index(default_phase) if default_phase in phase else 0
            )

            varation_list=sql.get_varation([selected_project],[selected_destination],[selected_drivesystem],[selected_lot],[selected_phase])

            if isinstance(varation_list, pd.DataFrame):
                varation_list = varation_list.iloc[:, 0].tolist()

            default_variation = st.session_state.get(f'last_select_variation_{i}', None)
            if default_variation not in varation_list:
                default_variation = varation_list[0] if varation_list else None
                st.session_state[f'last_select_variation_{i}'] = default_variation

            selected_variation = st.selectbox(
                f'バリエーション',
                # ['BCS仕様', 'Kick off仕様❶', 'Kick off仕様2'],
                varation_list,
                key=f'select_variation_unique_key_{i}',
                index=varation_list.index(default_variation) if default_variation in varation_list else 0
            )
    num_cols = st.session_state['num_cols']

    selected_archi = []
    selected_project = []
    selected_destination = []
    selected_drivesystem = []
    selected_lot = []
    selected_phase = []
    selected_variation = []

    for i in range(num_cols):
        selected_archi.append(st.session_state.get(f'select_archi_unique_key_{i}', []))
        selected_project.append(st.session_state.get(f'select_project_unique_key_{i}', []))
        selected_destination.append(st.session_state.get(f'select_destination_unique_key_{i}', []))
        selected_drivesystem.append(st.session_state.get(f'select_drivesystem_unique_key_{i}', []))
        selected_lot.append(st.session_state.get(f'select_lot_unique_key_{i}', []))
        selected_phase.append(st.session_state.get(f'select_phase_unique_key_{i}', []))
        selected_variation.append(st.session_state.get(f'select_variation_unique_key_{i}', []))

    if st.button("比較"):
        # --- Validation before comparison ---
        error_found = False
        # 1. Check all selectboxes are selected (not default)
        for i in range(num_cols):
            if (
                selected_archi[i] in [None, '', '選択してください。'] or
                selected_project[i] in [None, '', '選択してください。'] or
                selected_destination[i] in [None, '', '選択してください。'] or
                selected_drivesystem[i] in [None, '', '選択してください。'] or
                selected_lot[i] in [None, '', '選択してください。'] or
                selected_phase[i] in [None, '', '選択してください。'] or
                selected_variation[i] in [None, '', '選択してください。']
            ):
                st.error(f"列{i+1} の全ての項目を選択してください。")
                error_found = True

        # 2. Check for duplicate selections
        selections = [
            (
                selected_archi[i],
                selected_project[i],
                selected_destination[i],
                selected_drivesystem[i],
                selected_lot[i],
                selected_phase[i],
                selected_variation[i]
            )
            for i in range(num_cols)
        ]
        if error_found is False and len(selections) != len(set(selections)):
            st.error("同じプロジェクトが複数あります。各列は異なるプロジェクトを選択してください。")
            error_found = True

        if not error_found:
            df1,df2=sql.posgre_get_compare_data(selected_archi,selected_project,selected_destination,selected_drivesystem,selected_lot,selected_phase,selected_variation)
            st.session_state.prj_info_list = df1
            st.session_state.se_data_stuck = df2
            st.session_state.compare_click = True
            
            # Save selections for each column
            for i in range(len(selected_archi)):
                st.session_state[f'last_select_archi_{i}'] = selected_archi[i]
                st.session_state[f'last_select_project_{i}'] = selected_project[i]
                st.session_state[f'last_select_destination_{i}'] = selected_destination[i]
                st.session_state[f'last_select_drivesystem_{i}'] = selected_drivesystem[i]
                st.session_state[f'last_select_lot_{i}'] = selected_lot[i]
                st.session_state[f'last_select_phase_{i}'] = selected_phase[i]
                st.session_state[f'last_select_variation_{i}'] = selected_variation[i]

            st.session_state['last_num_cols'] = len(selected_archi)
            st.session_state['dialog_opened_once'] = False    
            st.rerun()



@st.dialog("新規作成")
def create_project1():
    if 'phase_click' not in st.session_state:
        st.session_state['phase_click'] = False
    st.markdown("SEリストを新規作成します。<br>新規作成する項目を選択し、新しいロット/フェーズを設定してください。", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1,2])
    with col1:
        lot_btn = st.button("ロット")
    with col2:
        phase_btn = st.button("フェーズ")

    if lot_btn:
        st.session_state['phase_click'] = False
        st.write("ロットボタンを押した。")
    if phase_btn:
        st.session_state['phase_click'] = True
    if st.session_state['phase_click'] is True:
        create_phase_dia1()

@st.dialog("新規作成")
def create_project2():
    st.markdown("コピーするプロジェクトを選択してください。", unsafe_allow_html=True)
    create_phase_dia2()



@st.dialog("新規study追加")
def create_new_study():#山口　新規study用ダイアログ　　selectboxは初期値にインデックス指定する必要ある12/5 各Selectoptionの選択された数によって表示を切り替える12/26
    sim_prj_info_list = st.session_state.sim_prj_info_list.copy()
    #ここで決める必要のあるもの定義
    project_id=None
    phase_id=None
    variation_id=None
    study_id=None
    base_study_id=None  #山口　参照元スタディの変数宣言 1/24
    TD=None
    R=None
    usecase=None
    Carbody_submodel = None
    Carbody_parameters = []
    EM_Fr_submodel = None
    EM_Fr_parameters = []
    EM_Fr_MAPs = []
    Gearbox_Fr_submodel = None
    Gearbox_Fr_parameters = []
    Gearbox_Fr_MAPs = []
    EM_Rr_submodel = None
    EM_Rr_parameters = []
    EM_Rr_MAPs = []
    Gearbox_Rr_submodel = None
    Gearbox_Rr_parameters = []
    Gearbox_Rr_MAPs = []
    Battery_submodel = None
    Battery_parameters = []
    Battery_MAPs = []
    tab1, tab2, tab3, tab4 = st.tabs(['Base SE','Parameters', 'Map','ユースケース追加リクエスト'])
    metas = sql.get_metas()
    #st.write(metas)
    with tab1:
        #　山口　SEリストベース、Studyリストベースを切り替えられるように 1/23

        baseselection = st.selectbox(
            'ベース選択',
            ['SEリストベース','Studyベース' ],
            key = 'base_selection'
        )
        if baseselection=='SEリストベース':
        #projectダイアログ
            if 'selectoption1' not in st.session_state:
                st.session_state['selectoption1'] = []
            
            if len(st.session_state['selectoption1'])==1:
                st.write("プロジェクト：" + st.session_state['selectoption1'][0])
                selectoption1 = st.session_state['selectoption1'][0]
            else:
                selectoption1 = st.selectbox(
                    'プロジェクト:',
                    st.session_state['selectoption1'],
                    key='unique_key_1'
            
                )
                st.session_state['selectoption1'] = [selectoption1]
            
            #destinationダイアログ

            metas_filtered1 = metas[metas['project_code']==selectoption1]
            #st.write(metas_filtered1)
            if 'selectoption2' not in st.session_state:
                st.session_state['selectoption2'] = []
            if len(st.session_state['selectoption2'])==1:
                st.write('仕向け：' + st.session_state['selectoption2'][0])
                selectoption2 = st.session_state['selectoption2'][0]
            else:
                selectoption2 = st.selectbox(
                    '仕向け:',
                    st.session_state['selectoption2'],
                    key='unique_key_2'
                    

                )
                st.session_state['selectoption2'] = [selectoption2]
            #drivetrainダイアログ
            
            metas_filtered2 = metas_filtered1[metas_filtered1['destination']==selectoption2]
            #st.write(metas_filtered2)
            if 'selectoption3' not in st.session_state:
                st.session_state['selectoption3'] = []
            if len(st.session_state['selectoption3'])==1:
                st.write('駆動方式：' + st.session_state['selectoption3'][0])
                selectoption3 = st.session_state['selectoption3'][0]
            else:
                selectoption3 = st.selectbox(
                    '駆動方式:',
                    st.session_state['selectoption3'],
                    key='unique_key_3'
                )
                st.session_state['selectoption3'] = [selectoption3]
            
            #lotダイアログ
            
            metas_filtered3 = metas_filtered2[metas_filtered2['drivetrain']==selectoption3]
            #st.write(metas_filtered3)
            if 'selectoption4' not in st.session_state:
                st.session_state['selectoption4'] = []
            if len(st.session_state['selectoption4'])==1:
                st.write('ロット：' + st.session_state['selectoption4'][0])
                selectoption4 = st.session_state['selectoption4'][0]
            else:

                selectoption4 = st.selectbox(
                    'ロット:',
                    st.session_state['selectoption4'],
                    key='unique_key_4'
                )
                st.session_state['selectoption4'] = [selectoption4]
            
            #phaseダイアログ

            metas_filtered4 = metas_filtered3[metas_filtered3['lot']==selectoption4]
            #st.write(metas_filtered4)
            if 'selectoption5' not in st.session_state:
                st.session_state['selectoption5'] = []
            if len(st.session_state['selectoption5'])==1:
                st.write('フェーズ：' + st.session_state['selectoption5'][0])
                selectoption5 = st.session_state['selectoption5'][0]
            else:

                selectoption5 = st.selectbox(
                    'フェーズ:',
                    st.session_state['selectoption5'],
                    key='unique_key_5'
                )
                st.session_state['selectoption5'] = [selectoption5]
            
            #variationダイアログ

            metas_filtered5 = metas_filtered4[metas_filtered4['phase']==selectoption5]
            #st.write(metas_filtered5)
            if 'selectoption6' not in st.session_state:
                st.session_state['selectoption6'] = []
            if len(st.session_state['selectoption6'])==1:
                st.write('バリエーション：' + st.session_state['selectoption6'][0])
                selectoption6 = st.session_state['selectoption6'][0]
            else:         

                selectoption6 = st.selectbox(
                    'バリエーション:',
                    st.session_state['selectoption6'],

                    key='unique_key_6'
                )
                st.session_state['selectoption6'] = [selectoption6]
            metas_filtered6 = metas_filtered5[metas_filtered5['variation']==selectoption6]
            #st.write(metas_filtered6)
            if len(metas_filtered6) == 0:
                st.error('選択されたメタ情報に対応する諸元リスト情報が見つかりませんでした。')
                return
            project_id=metas_filtered6['project_id'].tolist()[0]#何でここだけこんな書き方しないといけないのか...
            #st.write(metas_filtered6)
            phase_id = metas_filtered6['phase_id'].tolist()[0]
            variation_id=metas_filtered6['variation_id'].tolist()[0]
            phase = selectoption5
            variation = selectoption6
        else:#山口　スタディベースを選択したときの処理。
            
            #単にstudy_idのみを表示させると、複数バリエーション等で同じStudy_idが入っていた際にどちらを選べばよいかわからなくなるため、一いに定めらるようにprj名等もつける
            #ここで選択されたphase,variationはselectoption5,6として格納する 3/21
            sim_prj_info_list['selectable_studies'] = sim_prj_info_list['study_id'] + '_'+ sim_prj_info_list['project_code'] + '_' + sim_prj_info_list['phase'] + '_' + sim_prj_info_list['variation'] +'_'+ str(sim_prj_info_list['project_id'].tolist()[0]) + '_' + str(sim_prj_info_list['phase_id'].tolist()[0]) + '_' + str(sim_prj_info_list['variation_id'].tolist()[0])
            selectable_studies = sim_prj_info_list['selectable_studies'].tolist()
            base_study_id = st.selectbox(
                'ベーススタディID',
                selectable_studies,
                key = 'select_base_study'
            )
            base_ids = base_study_id.split('_')
            base_study_id = base_ids[0]
            
            phase = base_ids[2]
            variation = base_ids[3]
            project_id = int(base_ids[4])
            phase_id = int(base_ids[5])
            variation_id = int(base_ids[6])
            selectoption5 = phase
            selectoption6 = variation


            


        study_id = st.text_input('スタディID', placeholder='Study000', max_chars=16, help='')
        
        st.session_state['study_id'] = study_id

        #StudyIDに重複が発生していないか確認する必要あり 1/8
        sim_prj_info = st.session_state.sim_prj_info_list
        #StudyIDに重複が発生していないか確認する必要あり 1/8 スタディが一つもない場合を考慮していないのでする 3/24
        if len(sim_prj_info_list) >= 1:
            study_ids_existing = sim_prj_info_list[sim_prj_info_list['project_id']==project_id][sim_prj_info_list['phase']==phase][sim_prj_info_list['variation']==variation]['study_id'].tolist()
            if study_id in study_ids_existing:
                st.error("入力されたStudyIDはすでに存在しているため使用できません！！")

        df_R_parameter = sql.get_R_project_record(project_id, phase_id) # 山口　Rテーブルから要求一覧をとる やはりこっちを採用4/1
        # df_R_parameter = sql.get_R_parameter() # 山口　プロジェクトに紐づいているのではなくすべて表示
        R_list = df_R_parameter['performance'].drop_duplicates().tolist()
        R_list = ['PTシステムレビュー向け全R項目'] + R_list #山口　すべてのR項目をoutputとして登録できる選択肢を追加　7/30
        print(R_list)
        #Rリストダイアログ
        if 'selectoptionR' not in st.session_state:
            st.session_state['selectoptionR'] = []
        if R_list != st.session_state['selectoptionR']:
            st.session_state['selectoptionR'] = []
        selectoptionR = st.selectbox(
            '領域:',
            R_list,
            key='unique_key_R'        
        )
        st.session_state['selectoptionR'] = selectoptionR
        R = selectoptionR
        #ユースケースリストダイアログ,Project_idを定めるまで表示しない
        if project_id is not None:
            #usecase_list = ['WLTC','WOT', 'Eisenhower']#ユースケーステーブル作成後一覧を、RとProjの組み合わせでとれるようにする
            design_item_list = df_R_parameter[df_R_parameter['performance']==R]['design_item_3'].drop_duplicates().tolist() #山口　選んだ性能からユースケース選択 検討項目名に変更 1/30
            if 'selectoptionDesignItem' not in st.session_state:
                st.session_state['selectoptionDesignItem'] = []
            if design_item_list != st.session_state['selectoptionDesignItem']:
                st.session_state['selectoptionDesignItem'] = []
            selectoptionDesignItem = st.selectbox(
                '検討項目:',
                design_item_list,
                key='unique_key_d'        
            )
            st.session_state['selectoptionDesignItem'] = selectoptionDesignItem
            designItem = selectoptionDesignItem
            #山口　検討項目と別にユースケースを選択させる用に変更 やっぱり検討項目に紐づくものが欲しい 4/1
            df_usecase_list = sql.get_usecase_list()
            usecase_list = df_R_parameter[df_R_parameter['performance']==R][df_R_parameter['design_item_3']==designItem]['usecase'].drop_duplicates().tolist()
            if 'selectoptionUsecase' not in st.session_state:
                st.session_state['selectoptionUsecase'] = []
            if design_item_list != st.session_state['selectoptionUsecase']:
                st.session_state['selectoptionUsecase'] = []
            selectoptionUsecase = st.selectbox(
                'ユースケース',
                usecase_list,
                key='unique_key_u'
            )
            st.session_state['selectoptionUsecase'] = selectoptionUsecase
            usecase=selectoptionUsecase

            usecase_submodel_list = df_usecase_list[df_usecase_list['usecase']==usecase][df_usecase_list['parameter_name']=='submodel']['value'].tolist()
            #山口　条件処理順番入れ替えた 4/1
            if len(usecase_submodel_list)==0 or usecase_submodel_list[0] == "" or usecase_submodel_list[0] is None:
                st.warning('このユースケースのSysAサブモデルは登録されていません。')
            else:
                usecase_submodel = usecase_submodel_list[0]
                st.write(usecase_submodel)
            
        #TDファイル名を指定する、td_variablesであるTD名すべてから
        td_list = sql.get_td_list()
        if 'selectoptionTD' not in st.session_state:
            st.session_state['selectoptionTD'] = []
        if td_list != st.session_state['selectoptionTD']:
            st.session_state['selectoptionTD'] = []
        selectoptionTD = st.selectbox(
            'TD file:',
            td_list,
            key='unique_key_TD'        
        )
        st.session_state['selectoptionTD'] = selectoptionTD
        TD = selectoptionTD

    with tab2:
        #CarBodyサブモデルとパラメータを定めるダイアログ TDを定めるまで表示しない
        
        if TD is not None:
            
            Carbody_sub_list = sql.get_submodel_list(TD, 'Carbody')
            if 'selectoptionCarbody' not in st.session_state:
                st.session_state['selectoptionCarbody'] = []
            if Carbody_sub_list != st.session_state['selectoptionCarbody']:
                st.session_state['selectoptionCarbody'] = []
            selectoptionCarbody = st.selectbox(
                '車両サブモデル:',
                Carbody_sub_list,
                key='unique_key_Carbody'        
            )
            st.session_state['selectoptionCarbody'] = selectoptionCarbody
            Carbody_submodel=selectoptionCarbody
            if project_id is not None and phase_id is not None and variation_id is not None:
            
                
                df_carbody_parameter_list = sql.get_senario_parameter('Carbody', project_id, phase_id, variation_id, 'SCALAR', base_study_id)  #山口　参照元スタディをSQLで渡すため引数追加1/24
                with st.expander("Carbodyパラメータ"):
                    for i,row in df_carbody_parameter_list.iterrows():
                        senario_parameter_id = row['senario_parameter_id']
                        parameter_name = row['parameter_name_2']
                        original_value = row['original_value']
                        update_value = st.text_input(parameter_name, original_value,key='Carbody' + parameter_name)
                        
                        #変数名と更新後の値はとりあえず辞書としよう
                        valdic = {senario_parameter_id:update_value}
                        if len(Carbody_parameters)==i:
                            Carbody_parameters.append(valdic)
                        else:
                            Carbody_parameters[i]=valdic
            #EM_Fr
            EM_Fr_sub_list = sql.get_submodel_list(TD, 'Electrical_Motor_Fr')
            if 'selectoptionEM_Fr' not in st.session_state:
                st.session_state['selectoptionEM_Fr'] = []
            if EM_Fr_sub_list != st.session_state['selectoptionEM_Fr']:
                st.session_state['selectoptionEM_Fr'] = []
            selectoptionEM_Fr = st.selectbox(
                'FrMOTサブモデル:',
                EM_Fr_sub_list,
                key='unique_key_EM_Fr'        
            )
            st.session_state['selectoptionEM_Fr'] = selectoptionEM_Fr
            EM_Fr_submodel=selectoptionEM_Fr
            if project_id is not None and phase_id is not None and variation_id is not None:
            
                
                df_EM_Fr_parameter_list = sql.get_senario_parameter('Electrical_Motor_Fr', project_id, phase_id, variation_id, 'SCALAR', base_study_id)
                #st.write(df_EM_Fr_parameter_list)
                with st.expander("FrMotパラメータ"):
                    for i,row in df_EM_Fr_parameter_list.iterrows():
                        senario_parameter_id = row['senario_parameter_id']
                        parameter_name = row['parameter_name_2']
                        original_value = row['original_value']
                        update_value = st.text_input(parameter_name, original_value,key='EM_Fr' + parameter_name)
                        
                        #変数名と更新後の値はとりあえず辞書としよう
                        valdic = {senario_parameter_id:update_value}
                        if len(EM_Fr_parameters)==i:
                            EM_Fr_parameters.append(valdic)
                        else:
                            EM_Fr_parameters[i]=valdic
            #EM_Rr
            EM_Rr_sub_list = sql.get_submodel_list(TD, 'Electrical_Motor_Rr')
            if 'selectoptionEM_Rr' not in st.session_state:
                st.session_state['selectoptionEM_Rr'] = []
            if EM_Rr_sub_list != st.session_state['selectoptionEM_Rr']:
                st.session_state['selectoptionEM_Rr'] = []
            selectoptionEM_Rr = st.selectbox(
                'RrMOTサブモデル:',
                EM_Rr_sub_list,
                key='unique_key_EM_Rr'
            )
            st.session_state['selectoptionEM_Rr'] = selectoptionEM_Rr
            EM_Rr_submodel=selectoptionEM_Rr
            if project_id is not None and phase_id is not None and variation_id is not None:
            
                
                df_EM_Rr_parameter_list = sql.get_senario_parameter('Electrical_Motor_Rr', project_id, phase_id, variation_id, 'SCALAR', base_study_id)
                #st.write(df_EM_Rr_parameter_list)
                with st.expander("RrMotパラメータ"):
                    for i,row in df_EM_Rr_parameter_list.iterrows():
                        senario_parameter_id = row['senario_parameter_id']
                        parameter_name = row['parameter_name_2']
                        original_value = row['original_value']
                        update_value = st.text_input(parameter_name, original_value, key='EM_Rr' + parameter_name)
                        
                        #変数名と更新後の値はとりあえず辞書としよう
                        valdic = {senario_parameter_id:update_value}
                        if len(EM_Rr_parameters)==i:
                            EM_Rr_parameters.append(valdic)
                        else:
                            EM_Rr_parameters[i]=valdic
            
            #Gearbox_Fr
            Gearbox_Fr_sub_list = sql.get_submodel_list(TD, 'Gearbox_Fr')
            if 'selectoptionGearbox_Fr' not in st.session_state:
                st.session_state['selectoptionGearbox_Fr'] = []
            if Gearbox_Fr_sub_list != st.session_state['selectoptionGearbox_Fr']:
                st.session_state['selectoptionGearbox_Fr'] = []
            selectoptionGearbox_Fr = st.selectbox(
                'FrGearboxサブモデル:',
                Gearbox_Fr_sub_list,
                key='unique_key_Gearbox_Fr'        
            )
            st.session_state['selectoptionGearbox_Fr'] = selectoptionGearbox_Fr
            Gearbox_Fr_submodel=selectoptionGearbox_Fr
            if project_id is not None and phase_id is not None and variation_id is not None:
            
                
                df_Gearbox_Fr_parameter_list = sql.get_senario_parameter('Gearbox_Fr', project_id, phase_id, variation_id, 'SCALAR', base_study_id)
                #st.write(df_Gearbox_Fr_parameter_list)
                with st.expander("FrGearboxパラメータ"):
                    for i,row in df_Gearbox_Fr_parameter_list.iterrows():
                        senario_parameter_id = row['senario_parameter_id']
                        parameter_name = row['parameter_name_2']
                        original_value = row['original_value']
                        update_value = st.text_input(parameter_name, original_value,key='Gearbox_Fr' + parameter_name)
                        
                        #変数名と更新後の値はとりあえず辞書としよう
                        valdic = {senario_parameter_id:update_value}
                        if len(Gearbox_Fr_parameters)==i:
                            Gearbox_Fr_parameters.append(valdic)
                        else:
                            Gearbox_Fr_parameters[i]=valdic
            
            #Gearbox_Rr
            Gearbox_Rr_sub_list = sql.get_submodel_list(TD, 'Gearbox_Rr')
            if 'selectoptionGearbox_Rr' not in st.session_state:
                st.session_state['selectoptionGearbox_Rr'] = []
            if Gearbox_Rr_sub_list != st.session_state['selectoptionGearbox_Rr']:
                st.session_state['selectoptionGearbox_Rr'] = []
            selectoptionGearbox_Rr = st.selectbox(
                'RrGearboxサブモデル:',
                Gearbox_Rr_sub_list,
                key='unique_key_Gearbox_Rr'        
            )
            st.session_state['selectoptionGearbox_Rr'] = selectoptionGearbox_Rr
            Gearbox_Rr_submodel=selectoptionGearbox_Rr
            if project_id is not None and phase_id is not None and variation_id is not None:
            
                
                df_Gearbox_Rr_parameter_list = sql.get_senario_parameter('Gearbox_Rr', project_id, phase_id, variation_id, 'SCALAR', base_study_id)
                #st.write(df_Gearbox_Rr_parameter_list)
                with st.expander("RrGearboxパラメータ"):
                    for i,row in df_Gearbox_Rr_parameter_list.iterrows():
                        senario_parameter_id = row['senario_parameter_id']
                        parameter_name = row['parameter_name_2']
                        original_value = row['original_value']
                        update_value = st.text_input(parameter_name, original_value,key='Gearbox_Rr' + parameter_name)
                        
                        #変数名と更新後の値はとりあえず辞書としよう
                        valdic = {senario_parameter_id:update_value}
                        if len(Gearbox_Rr_parameters)==i:
                            Gearbox_Rr_parameters.append(valdic)
                        else:
                            Gearbox_Rr_parameters[i]=valdic
        
            #Battery
            Battery_sub_list = sql.get_submodel_list(TD, 'Battery_High_Voltage')
            if 'selectoptionBattery' not in st.session_state:
                st.session_state['selectoptionBattery'] = []
            if Battery_sub_list != st.session_state['selectoptionBattery']:
                st.session_state['selectoptionBattery'] = []
            selectoptionBattery = st.selectbox(
                'Batteryサブモデル:',
                Battery_sub_list,
                key='unique_key_Battery'        
            )
            st.session_state['selectoptionBattery'] = selectoptionBattery
            Battery_submodel=selectoptionBattery
            if project_id is not None and phase_id is not None and variation_id is not None:
            
                
                df_Battery_parameter_list = sql.get_senario_parameter('Battery_High_Voltage', project_id, phase_id, variation_id, 'SCALAR', base_study_id)
                #st.write(df_Battery_parameter_list)
                with st.expander("Batteryパラメータ"):
                    for i,row in df_Battery_parameter_list.iterrows():
                        senario_parameter_id = row['senario_parameter_id']
                        parameter_name = row['parameter_name_2']
                        original_value = row['original_value']
                        update_value = st.text_input(parameter_name, original_value,key='Battery' + parameter_name)
                        
                        #変数名と更新後の値はとりあえず辞書としよう
                        valdic = {senario_parameter_id:update_value}
                        if len(Battery_parameters)==i:
                            Battery_parameters.append(valdic)
                        else:
                            Battery_parameters[i]=valdic
            
    with tab3:#山口　表示するマップはパラメータのスコープに合わせる 12/26
        
        if project_id is not None and phase_id is not None and variation_id is not None:
            
            df_MAP_list = sql.get_map_list()
            #EM_Fr
            df_EM_Fr_MAP_list = sql.get_senario_parameter('Electrical_Motor_Fr', project_id, phase_id, variation_id,'MAP', base_study_id)
            #st.write(df_EM_Fr_parameter_list)
            for i,row in df_EM_Fr_MAP_list.iterrows():
                senario_parameter_id = row['senario_parameter_id']
                parameter_name = row['parameter_name_2']
                original_value = row['original_value']
                scope = row['scope']
                print(df_MAP_list)
                update_value = st.selectbox(
                                parameter_name,
                                df_MAP_list[df_MAP_list['scope']==scope]['map_name'].tolist(),
                                key='unique_key_' + parameter_name    + scope # 山口　同一のパラメータ名が来た時のエラーを起こさないため、scope名もキーに追加 3/19     
                            )
                
                #変数名と更新後の値はとりあえず辞書としよう
                valdic = {senario_parameter_id:update_value}
                if len(EM_Fr_MAPs)==i:
                    EM_Fr_MAPs.append(valdic)
                else:
                    EM_Fr_MAPs[i]=valdic
                    
            #EM_Rr
            df_EM_Rr_MAP_list = sql.get_senario_parameter('Electrical_Motor_Rr', project_id, phase_id, variation_id,'MAP', base_study_id)
            #st.write(df_EM_Rr_parameter_list)
            for i,row in df_EM_Rr_MAP_list.iterrows():
                senario_parameter_id = row['senario_parameter_id']
                parameter_name = row['parameter_name_2']
                original_value = row['original_value']
                scope = row['scope']
                update_value = st.selectbox(
                                parameter_name,
                                df_MAP_list[df_MAP_list['scope']==scope]['map_name'].tolist(),
                                key='unique_key_' + parameter_name       + scope # 山口　同一のパラメータ名が来た時のエラーを起こさないため、scope名もキーに追加 3/19  
                            )
                
                #変数名と更新後の値はとりあえず辞書としよう
                valdic = {senario_parameter_id:update_value}
                if len(EM_Rr_MAPs)==i:
                    EM_Rr_MAPs.append(valdic)
                else:
                    EM_Rr_MAPs[i]=valdic
            
            #Gearbox_Fr
            df_Gearbox_Fr_MAP_list = sql.get_senario_parameter('Gearbox_Fr', project_id, phase_id, variation_id,'MAP', base_study_id)
            #st.write(df_Gearbox_Fr_parameter_list)
            for i,row in df_Gearbox_Fr_MAP_list.iterrows():
                senario_parameter_id = row['senario_parameter_id']
                parameter_name = row['parameter_name_2']
                original_value = row['original_value']
                scope = row['scope']
                update_value = st.selectbox(
                                parameter_name,
                                df_MAP_list[df_MAP_list['scope']==scope]['map_name'].tolist(),
                                key='unique_key_' + parameter_name    + scope # 山口　同一のパラメータ名が来た時のエラーを起こさないため、scope名もキーに追加 3/19     
                            )
                
                #変数名と更新後の値はとりあえず辞書としよう
                valdic = {senario_parameter_id:update_value}
                if len(Gearbox_Fr_MAPs)==i:
                    Gearbox_Fr_MAPs.append(valdic)
                else:
                    Gearbox_Fr_MAPs[i]=valdic

            #Gearbox_Rr
            df_Gearbox_Rr_MAP_list = sql.get_senario_parameter('Gearbox_Rr', project_id, phase_id, variation_id,'MAP', base_study_id)
            #st.write(df_Gearbox_Rr_parameter_list)
            for i,row in df_Gearbox_Rr_MAP_list.iterrows():
                senario_parameter_id = row['senario_parameter_id']
                parameter_name = row['parameter_name_2']
                original_value = row['original_value']
                scope = row['scope']
                update_value = st.selectbox(
                                parameter_name,
                                df_MAP_list[df_MAP_list['scope']==scope]['map_name'].tolist(),
                                key='unique_key_' + parameter_name + scope # 山口　同一のパラメータ名が来た時のエラーを起こさないため、scope名もキーに追加 3/19 
                            )
                
                #変数名と更新後の値はとりあえず辞書としよう
                valdic = {senario_parameter_id:update_value}
                if len(Gearbox_Rr_MAPs)==i:
                    Gearbox_Rr_MAPs.append(valdic)
                else:
                    Gearbox_Rr_MAPs[i]=valdic
    
    with tab4:
       
        user = st.session_state.username

        user = st.text_input("社員番号",value=user)
        message = st.text_area("メッセージ", value="ユースケース追加依頼")

        

        if st.button("依頼送信"):
            if user == "":
                st.error("社員番号は必須です。")
            else:
                mail.request_usecase(user, message)
                st.success("メールを送信しました。")
        
    #この時点で必要情報集まったため更新
    
    if st.button('作成'):
        if study_id =='':
            st.error('study_idを入力してください！')
        elif len(st.session_state.sim_prj_info_list) >= 1 and study_id in study_ids_existing:#山口　エラー条件追加 1/8 新規スタディ用の条件追加3/24
            st.error("入力されたStudyIDはすでに存在しているため使用できません！！")
        else:
            if R == 'PTシステムレビュー向け全R項目': #PTシステムレビュー向け全R項目が選ばれていたら、ここまでにdesignItem, usecaseが宣言されていないため、ここでからであることを宣言する
                designItem = '-'
                usecase = '-'
                usecase_submodel = '-'
                
            submodels = [Carbody_submodel, EM_Fr_submodel,  EM_Rr_submodel, Gearbox_Fr_submodel, Gearbox_Rr_submodel, Battery_submodel]
            variables = [Carbody_parameters,  EM_Fr_parameters, EM_Fr_MAPs, EM_Rr_parameters, EM_Rr_MAPs, Gearbox_Fr_parameters, Gearbox_Fr_MAPs, Gearbox_Rr_parameters, Gearbox_Rr_MAPs, Battery_parameters, Battery_MAPs]
            #sql.add_new_study(project_id, phase_id, variation_id, study_id)
            sql.add_new_study(project_id, phase_id, variation_id, study_id, R, designItem, usecase, usecase_submodel, TD, submodels, variables)#山口　ユースケースサブモデる名を追加 R->designitemに変更 2/1 PTシステムレビュー向け全R項目に対応できるように変更する7/30
            st.write('新規Studyを追加しました。')
            time.sleep(1)
            #02/12 チョー　新規追加した後、リロードするため
            st.session_state.create_new_sim = True
            st.rerun()
            # reload_info()

def reload_info():#山口　SPDM_LISTから持ってきた1/8
    print('reload info:')
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
        # df1,df2=sql.posgre_get_data_sim(st.session_state['selectoption1'],st.session_state['selectoption2'],st.session_state['selectoption3'],st.session_state['selectoption4'],st.session_state['selectoption5'], st.session_state['selectoption6'])
        #チョー 03/10
        df1,df2=sql.posgre_get_data_sim(st.session_state['selectoption1'],st.session_state['selectoption2'],st.session_state['selectoption3'],st.session_state['selectoption4'],st.session_state['selectoption5'])
        st.session_state.sim_prj_info_list = df1
        st.session_state.sim_data_stuck = df2
    else:
        st.error('unexpected reload')

#チョー　01/08　Rリスト処理追加
@st.dialog("PRJ選択")
def choice_r_list():
    if 'architecture_name' not in st.session_state:
        st.session_state['architecture_name'] = []
        st.session_state['selectoption1'] = []
    architecture_list = sql.get_project("architecture_name")
    selected_archi = st.multiselect(
        'PTシステムタイプ',
        architecture_list,
        key ='select_archi_unique_key',
        default = st.session_state['architecture_name']
    )
    st.session_state['architecture_name'] = selected_archi
    if 'selectoption1' not in st.session_state or len(selected_archi) <= 0:
        st.session_state['selectoption1'] = []
    # z_model_code = sql.get_project("z_model_code")
    z_model_code = sql.get_project("z_model_code",selected_archi)
    selectoption1 = st.multiselect(
        'プロジェクト:',
        z_model_code,
        key='unique_key_1',
        default=st.session_state['selectoption1'],
    )
    st.session_state['selectoption1'] = selectoption1

    if 'selectoption2' not in st.session_state:
        st.session_state['selectoption2'] = []
    destination = sql.get_project("destination",selectoption1)

    if destination != st.session_state['selectoption2']:
        st.session_state['selectoption2'] = []
    
    selectoption2 = st.multiselect(
        '仕向け:',
        destination,
        key='unique_key_2',
        default=st.session_state['selectoption2'],
    )
    st.session_state['selectoption2'] = selectoption2
    if 'selectoption3' not in st.session_state:
        st.session_state['selectoption3'] = []
    drive_system = sql.get_project("drive_system",selectoption1,selectoption2)
    if drive_system != st.session_state['selectoption3']:
        st.session_state['selectoption3'] = []
        
    selectoption3 = st.multiselect(
        '駆動方式:',
        drive_system,
        key='unique_key_3',
        default=st.session_state['selectoption3'],
        max_selections=2
    )
    st.session_state['selectoption3'] = selectoption3

    if all(st.session_state[key] for key in option_keys):
        if 'selectoption4' not in st.session_state:
            st.session_state['selectoption4'] = []
        project_lot = sql.get_project("project_lot",st.session_state['selectoption1'],
                                        st.session_state['selectoption2'],st.session_state['selectoption3'])
        if project_lot != st.session_state['selectoption4']:
            st.session_state['selectoption4'] = []
        selectoption4 = st.multiselect(
            'ロット:',
            project_lot,
            key='unique_key_4',
            default=st.session_state['selectoption4'],
        )
        st.session_state['selectoption4'] = selectoption4
        
        if 'selectoption5' not in st.session_state:
            st.session_state['selectoption5'] = []
        phase_list = sql.get_project("phase_list",
                                        st.session_state['selectoption1'],
                                        st.session_state['selectoption2'],
                                        st.session_state['selectoption3'],
                                        st.session_state['selectoption4'])
        if phase_list != st.session_state['selectoption5']:
            st.session_state['selectoption5'] = []
        selectoption5 = st.multiselect(
            'フェーズ:',
            phase_list,
            key='unique_key_5',
            default=st.session_state['selectoption5'],
        )
        st.session_state['selectoption5'] = selectoption5

        #チョー　バリエーション選択不要 03/10
        # #バリエーション選択用にselection6の追加
        # if 'selectoption6' not in st.session_state:
        #     st.session_state['selectoption6'] = []
        # variation_list = sql.get_project('variation_list', selectoption1,selectoption3, selectoption4, selectoption5)
        # if variation_list != st.session_state['selectoption6']:
        #     st.session_state['selectoption6'] = []
        # selectoption6 = st.multiselect(
        #     'バリエーション:',
        #     variation_list,
        #     key='unique_key_6',
        #     default=st.session_state['selectoption6'],
        #     max_selections= 2 if len(selectoption3) == 1 else 1 if len(selectoption3) == 2 else 0
        #     )
        # st.session_state['selectoption6'] = selectoption6

        st.markdown('<span id="button-right"></span>', unsafe_allow_html=True)
        # print('R list select:')
        if st.button("完了"):
            if all(st.session_state[key] for key in option_keys2):
                # df1,df2=sql.posgre_get_rlist(st.session_state['selectoption1'],
                #                     st.session_state['selectoption2'],
                #                     st.session_state['selectoption3'],
                #                     st.session_state['selectoption4'],
                #                     st.session_state['selectoption5'],
                #                     st.session_state['selectoption6'])
                #チョー 03/10
                df1,df2=sql.posgre_get_rlist(st.session_state['selectoption1'],
                                    st.session_state['selectoption2'],
                                    st.session_state['selectoption3'],
                                    st.session_state['selectoption4'],
                                    st.session_state['selectoption5'])
                
                if(len(df1)==0):  #山口　まだRリストを登録できていないプロジェクトが選択されたとき、警告を出すように　1/16
                    st.error('選択されたプロジェクトの要求リストは登録されていません。')
                else:
                    st.session_state.r_prj_info_list = df1
                    st.session_state.rlist_data_stuck = df2
                    # # st.session_state.r_prj_filter = df3

                    # df1
                    # # df2
                    st.session_state['compare_click'] = False
                    st.session_state['compare_back_click'] = False
                    st.rerun()
            else:
                st.error('全て選択してくださぃ！！', icon="🚨")
    st.session_state.chosen_id = 2

#02/10 チョー　確定ダイアログ
@st.dialog("Fixed")
def choice_sim_fixed():
    # if 'sim_study_list' not in st.session_state:
    #     st.session_state['sim_study_list'] = []
    # study_ids = st.session_state.sim_prj_info_list['study_id'].tolist()

    # Assuming st.session_state.sim_data_stuck contains your DataFrame
    sim_data_stuck = st.session_state.sim_data_stuck

    # Find columns that have 'senario_parameter_id' in their name (regardless of %% and other words)
    senario_columns = [col for col in sim_data_stuck.columns if 'senario_parameter_id' in col]

    # Now filter the data where 'senario_parameter_id' column has the value 3
    filtered_data = sim_data_stuck[sim_data_stuck[senario_columns].apply(lambda row: 3 in row.values, axis=1)]
    # Now, select columns that contain 'value' in their name
    filtered_value_columns = [col for col in filtered_data.columns if ';value;' in col]
    # Filter the data to show only those columns
    filtered_data = filtered_data[filtered_value_columns]

    dropdown_values = filtered_data.values.flatten()

    # Remove duplicates to avoid repeating options in the dropdown
    dropdown_values = sorted(list(set(dropdown_values)))

    # performance_list = sql.get_sim_performance(study_ids)

    selected_performance_1 = st.multiselect(
        '設計項目（大）',
        dropdown_values,
        key ='selected_perf1_unique_key',
        default=dropdown_values[0]
    )

    if selected_performance_1:
        sim_proj_info_list = st.session_state.sim_prj_info_list
        project_ids = sim_proj_info_list['project_id'].unique().tolist()
        phase_ids = sim_proj_info_list['phase_id'].unique().tolist()
        variation_ids = sim_proj_info_list['variation_id'].unique().tolist()
        destinations = sim_proj_info_list['destination'].unique().tolist()
        drivetrains = sim_proj_info_list['drivetrain'].unique().tolist()
        performance_list2 = sql.getr_value_to_sim(project_ids,destinations,drivetrains,phase_ids,variation_ids,selected_performance_1)

        # study_ids = st.session_state.sim_prj_info_list['study_id'].tolist()

        selected_performance_2 = st.multiselect(
            '設計項目（小）',
            # ["WLTC","WLTC2","WLTC3"],
            performance_list2,
            key ='selected_perf2_unique_key',
            
        )

        if st.button('実行',key='fixed_sim_button_key_1'):
            if selected_performance_1 and selected_performance_2:
                fixed_list = sql.get_sim_fix_list(project_ids,destinations,drivetrains,phase_ids,variation_ids,selected_performance_1,selected_performance_2)
                if fixed_list.empty:
                    st.error('No Fixed Data.')
                else:
                    st.session_state.fixed_sim_info = fixed_list
                    st.session_state['fix_sim_study_list'] = True
                    st.rerun()
            else:
                st.error('項目を選択してください。')
                

#02/10 チョー　確定処理の確認ダイアログ
@st.dialog("確認",width="large")       
def fixed_dia_sim():
    st.write("下記データを選択しました。最終確認を行ってください。")
    st.write("本当に更新する場合パラメータを選択しを実行ボタンを押下してください。")
    go = gop.fixed_sim()
    st.session_state.Prj_updata = AgGrid(
        st.session_state.fixed_sim_info,
        custom_css=css_ag,
        gridOptions=go,
        reload_data=False,
        height=220,
            )

    if st.button("実行",key='fixed_sim_button_key_2'):
        selected_rows = st.session_state.Prj_updata['selected_rows']
        if selected_rows is None:
            st.error('FIXEDする項目を選択してください。')
        elif len(selected_rows) > 1:
            st.error('1行しかFIXEDできません。')
        elif selected_rows is not None:
            update_sim_r_flag = sql.update_fixed_r_record(selected_rows)
            if update_sim_r_flag is True:
                st.session_state.seupdate_sim_r_info = selected_rows
            st.rerun()


# -----Telema-----
# RFLダイアログ
# Created: 2025/02/04
@st.dialog("条件選択",width="large")
def choice_rfl():
    
    st.session_state.chosen_id = 4
    init_session_state('architecture_name')

    architecture_list = sql.get_project("architecture_name")
    selected_archi = st.multiselect(
        'PTシステムタイプ',
        architecture_list,
        key ='select_archi_unique_key',
        # default = st.session_state['architecture_name']
    )
    st.session_state['architecture_name'] = selected_archi

    init_session_state('selectoption1')    
    # if 'selectoption1' not in st.session_state or len(selected_archi) <= 0:
    #     st.session_state['selectoption1'] = []

    # 必要？
    # if len(selected_archi) <= 0:
    #     st.session_state['selectoption1'] = []
    
    # ⓪車両コード
    z_model_code = sql.get_project("z_model_code",selected_archi)
    selectoption1 = st.multiselect(
        'プロジェクト:',
        z_model_code,
        key='unique_key_1',
        # default=st.session_state['selectoption1'],
    )
    st.session_state['selectoption1'] = selectoption1

    # ③仕向地マスタ
    init_session_state('selectoption2')
    destination = sql.get_project("destination",selectoption1)

    # 必要?
    # if destination != st.session_state['selectoption2']:
    #     st.session_state['selectoption2'] = []
    
    selectoption2 = st.multiselect(
        '仕向け:',
        destination,
        key='unique_key_2',
        # default=st.session_state['selectoption2'],
    )
    st.session_state['selectoption2'] = selectoption2
    
    
    init_session_state('selectoption3')
    drive_system = sql.get_project("drive_system",selectoption1,selectoption2)
    
    # 必要?
    # if drive_system != st.session_state['selectoption3']:
    #     st.session_state['selectoption3'] = []
        
    selectoption3 = st.multiselect(
        '駆動方式:',
        drive_system,
        key='unique_key_3',
        # default=st.session_state['selectoption3'],
    
    )
    st.session_state['selectoption3'] = selectoption3

    if all(st.session_state[key] for key in option_keys):
        init_session_state('selectoption4')
        
        project_lot = sql.get_project(
            "project_lot",
            st.session_state['selectoption1'],
            st.session_state['selectoption2'],
            st.session_state['selectoption3']
        )
        
        # 必要?
        # if project_lot != st.session_state['selectoption4']:
        #     st.session_state['selectoption4'] = []
        
        selectoption4 = st.multiselect(
            'ロット:',
            project_lot,
            key='unique_key_4',
            # default=st.session_state['selectoption4'],
        )
        st.session_state['selectoption4'] = selectoption4

        #チョー　フェーズ選択する必要 #03/10
        phase_list = sql.get_project("phase_list",st.session_state['selectoption1'],st.session_state['selectoption2'],st.session_state['selectoption3'],st.session_state['selectoption4'])
        selectoption5 = st.multiselect('フェーズ:',phase_list,key='unique_key_5')
        st.session_state['selectoption5'] = selectoption5
        
        st.markdown('<span id="button-right"></span>', unsafe_allow_html=True)
        if st.button("完了"):
            if all(st.session_state[key] for key in option_keys4):
                #山口　WP表記統一の効果を見るため差し替え、検証終わり次第戻す
                # df1=sql.alt_posgre_get_rfl(
                #     st.session_state['selectoption1'],
                #     st.session_state['selectoption2'],
                #     st.session_state['selectoption3'],
                #     st.session_state['selectoption4']
                # )
                df1=sql.posgre_get_rfl(
                    st.session_state['selectoption1'],
                    st.session_state['selectoption2'],
                    st.session_state['selectoption3'],
                    st.session_state['selectoption4'],
                    st.session_state['selectoption5'])

                st.session_state.rfl_list = df1
                st.rerun()
            else:
                st.error('全て選択してくださぃ！！', icon="🚨")
    st.session_state.chosen_id = 4
# -----Telema-----

# -----Telema-----
# RFL比較ダイアログ作成
# Created: 2025/02/07
def create_select_boxes_for_rfl(archi_list, col_count):
    """RFL比較対象選択ダイアログ作成

    Args:
        archi_list (string): architecture_list
        col_count (int): 対象col
    """

    if col_count == 1:
        compare_label = "ベース(比較基準)"
    elif col_count == 2:
        compare_label = "リファレンス(比較対象)"
    # labels = ["PTシステムタイプ","プロジェクト", "仕向け", "駆動方式", "ロット", "フェーズ","バリエーション"]
    labels = ["PTシステムタイプ","プロジェクト", "仕向け", "駆動方式", "ロット"]
    st.markdown(compare_label, unsafe_allow_html=True)

    selected_archi = st.selectbox(
        labels[0],
        archi_list,
        key = f'select_archi_unique_key_{col_count}',        
    )
    
    if len(st.session_state['rfl_architecture']) < col_count:
        st.session_state['rfl_architecture'].append(selected_archi)
    else:
        st.session_state['rfl_architecture'][col_count - 1] = selected_archi

    z_model_code = sql.get_project("z_model_code",[selected_archi])
    
    compare_option1 = st.selectbox(labels[1], z_model_code, key=f"main_opt1_{col_count}", label_visibility="visible")

    if len(st.session_state['compare_option1']) < col_count:
        st.session_state['compare_option1'].append(compare_option1)
    else:
        st.session_state['compare_option1'][col_count - 1] = compare_option1

    destination = sql.get_project("destination",[compare_option1])
    compare_option2 = st.selectbox(labels[2], destination, key=f"main_opt2_{col_count}", label_visibility="visible")

    if len(st.session_state['compare_option2']) < col_count:
        st.session_state['compare_option2'].append(compare_option2)
    else:
        st.session_state['compare_option2'][col_count - 1] = compare_option2

    drive_system = sql.get_project("drive_system",[compare_option1],[compare_option2])
    compare_option3 = st.selectbox(labels[3], drive_system, key=f"main_opt3_{col_count}", label_visibility="visible")

    if len(st.session_state['compare_option3']) < col_count:
        st.session_state['compare_option3'].append(compare_option3)
    else:
        st.session_state['compare_option3'][col_count - 1] = compare_option3

    project_lot = sql.get_project("project_lot",[compare_option1],[compare_option2],[compare_option3])
    compare_option4 = st.selectbox(labels[4], project_lot, key=f"main_opt4_{col_count}", label_visibility="visible")

    if len(st.session_state['compare_option4']) < col_count:
        st.session_state['compare_option4'].append(compare_option4)
    else:
        st.session_state['compare_option4'][col_count - 1] = compare_option4

# -----Telema-----


# -----Telema-----
# RFL比較
# Created: 2025/02/07
@st.dialog("RFL比較", width="large")
def compare_rfl():
    """RFL比較対象選択ダイアログ
    """
    
    init_session_state('rfl_architecture')
    # List of compare options
    
    # PJ,駆動,仕向け,ロット
    compare_options = ['compare_option1', 'compare_option2', 'compare_option3', 'compare_option4']

    # Initialize session state for each compare option if not already set
    for option in compare_options:
        init_session_state(option)
    architecture_list = sql.get_project("architecture_name")
    architecture_list = ['選択してください。'] + architecture_list
    
    col1, col2 = st.columns(2)
    
    with col1:
        create_select_boxes_for_rfl(architecture_list, 1)
    with col2:
        create_select_boxes_for_rfl(architecture_list, 2)
        
    if all(st.session_state[option] for option in compare_options):
        if st.button("完了"):

            compare_option1 = list(set(st.session_state['compare_option1']))
            compare_option2 = list(set(st.session_state['compare_option2']))
            compare_option3 = list(set(st.session_state['compare_option3']))
            compare_option4 = list(set(st.session_state['compare_option4']))
            compare_option5 = list(set(st.session_state['compare_option5']))
            
            if (
                None not in compare_option1 and
                None not in compare_option2 and
                None not in compare_option3 and
                None not in compare_option4 and
                None not in compare_option5
            ):
                df=sql.posgre_get_rfl(compare_option1,compare_option2,compare_option3,compare_option4,compare_option5)
                st.session_state.rfl_list_comp = df
                st.session_state.compare_click = True
                st.rerun()
            else:
                st.error("全ての項目を選択してください。")

# -----Telema-----
# RFL編集
# Created: 2025/02/12
@st.dialog("RFL編集", width="large")
def on_rfl_edit():
    """RFL編集モード
    """
    st.write('編集モードを開始します')
    if st.button("OK"):
        st.session_state.rfl_edit_state = True
        st.rerun()
    if st.button("戻る"):
        st.session_state.rfl_edit_state = False
        st.rerun()

@st.dialog("RFL編集終了確認", width="large")
def off_rfl_edit():
    """RFL編集モード
    """
    st.write('編集モードを終了します　')
    st.write('編集内容を確定しますか？')
    
    if st.button("確定する"):
        st.session_state.rfl_edit_state = False
        st.rerun()
        
    if st.button("破棄する"):
        st.session_state.rfl_edit_state = False
        rfl_org_pattern = r'^org_rfl_pj_\d+'
        rfl_res_pattern = r'^rfl_pj_response_\d+'
        
        rfl_keys_org = get_matching_key(rfl_org_pattern)
        rfl_keys_res = get_matching_key(rfl_res_pattern)
        
        diff_cells = RFLDataProcesser.compare_dataframes(rfl_keys_org,rfl_keys_res)
        print(diff_cells)

        st.rerun()
        
    if st.button("キャンセル"):
        st.session_state.rfl_edit_state = True
        st.rerun()
    
# -----Telema-----

#山口　　TOサマリ表示切り替え大ログt
@st.dialog('サマリー表示列選択', width="large")
def select_display_on_summary():
    st.info('一つの大項目_小項目につき、一行は必ず表示します')
    df_display_on_summary = st.session_state.df_display_on_summary.reset_index() #compare関数使用するときにindexがばらけていると使えないためリセットかける

    go_to_summary = {
        'columnDefs': [
            # {'field': 'se_parameter_id' },
            {'headerName':'サマリー表示する', 'field': 'summary_selected', 'cellRenderer': 'agCheckboxCellRenderer', 'cellEditor': 'agCheckboxCellEditor',}, #spanRows:大項目を'セルを結合'するイメージ
            {'headerName':'大項目', 'field': 'parameter_name_1'}, #spanRows:大項目を'セルを結合'するイメージ
            {'headerName':'小項目', 'field': 'parameter_name_2'},
        ],
        'defaultColDef': {
            'resizable': True,
            "enableValue": True,
            'value': True,
            'editable': True,
            
            
        },
        "cellSelection": True,
    }
    #R性能ごとにcolumnDefs追加
    df_rfl_performance = st.session_state.rfl_list.loc[:, 'c_r_wp'] #このやり方では車両しか取れない
    performance_list = [x.replace('logic_url_','') for x in df_display_on_summary.columns[df_display_on_summary.columns.str.contains('logic_url')].tolist()]

    print(performance_list)
    for performance in performance_list:
        rfl_logic_column_def ={
                'headerName':'logic_' + performance,
                'field':'logic_'+performance, 
            }
        rfl_scene_column_def ={
                'headerName':'scene_' + performance,
                'field':'scene_'+performance, 
            }
        go_to_summary['columnDefs'].append(rfl_logic_column_def)
        go_to_summary['columnDefs'].append(rfl_scene_column_def)
        
    select_summary_grid = AgGrid(df_display_on_summary,gridOptions=go_to_summary)
    df_edited_on_summary = select_summary_grid['data']
    #prj_rflをアップデートするために必要な列(project_id, phase_id, rfl_id, summary_select)のみに絞る
    df_display_on_summary = df_display_on_summary.iloc[:, df_display_on_summary.columns.str.contains('project_id|phase_id|rfl_id|summary_selected')]
    display_on_summary_select = df_display_on_summary['summary_selected'].values.tolist()
    df_edited_on_summary = df_edited_on_summary.iloc[:, df_edited_on_summary.columns.str.contains('project_id|phase_id|rfl_id|summary_selected')]
    edited_on_summary_select = df_edited_on_summary['summary_selected'].values.tolist()
    summary_select_change = [a != b for a, b in zip(display_on_summary_select, edited_on_summary_select)]
    df_update_target = df_edited_on_summary.iloc[summary_select_change]
    st.write(df_update_target)
    if st.button('サマリー表示更新'):
        #変更がないときはそれを伝える
        if df_update_target is None:
            st.error('表示非表示の変更が一つもありません。')
            return
        #更新情報の入ったDFを加工
        df = None
        for performance in performance_list:
            df_summary_selected = df_update_target['summary_selected']
            df_ids = df_update_target.loc[:, ['project_id_'+performance, 'phase_id_'+performance, 'rfl_id_'+performance]]
            if df is None:
                df  = pd.concat([df_ids, df_summary_selected], axis=1)
                df.columns = ['project_id', 'phase_id', 'rfl_id', 'summary_selected']
            else:
                df_per = pd.concat([df_ids, df_summary_selected], axis=1)
                df_per.columns = ['project_id', 'phase_id', 'rfl_id', 'summary_selected']
                df = pd.concat([df, df_per], axis=0)
                st.write(df)
        df.drop_duplicates(subset=['rfl_id'], inplace=True)#WDYM drop duplicate by project_id no
        sql.update_flag_display_on_summary(df)
        st.session_state.df_display_on_summary_before = st.session_state.df_display_on_summary.copy() 
        st.session_state.df_display_on_summary['summary_selected'].iloc[summary_select_change]=~st.session_state.df_display_on_summary['summary_selected'].iloc[summary_select_change]
        st.success("サマリー表示を更新しました")
        time.sleep(1)
        st.session_state.flag_summary_before = st.session_state.flag_summary
        del st.session_state.rfl_list # delete old rfl infomation after update 4/16
        del st.session_state.df_display_on_summary
        st.rerun()

#RFL承認の変更するエラー表示ダイアログ #チョー　04/14
@st.dialog("選択エラー")
def approve_sender_receiver_error(str):
    if str == 'selected_both':
        st.error('出し手と受け手、両方を選択されています。')
    if str == 'diff_approve_selected':
        st.error(''' 
            承認と承認取り消しが選択されています。  
            どちらか一方を選択してください。     
        ''')

    
#RFL承認の変更ダイアログ #チョー　04/14
@st.dialog('承認 / 承認取り消し確認', width="large")
def rfl_approval_update_confirm(final_df,sender_or_receiver):
    
    if not final_df.empty:
        btn_txt = '承認'
        approver = None
        if final_df[f'{sender_or_receiver}_judge'][0] == None:
            btn_txt = '承認取り消し'

        st.write("下記データを選択しました。最終確認を行ってください。")
        st.write(f'本当に変更する場合、「{btn_txt}」ボタンを押下してください。')
        if btn_txt != '承認取り消し':
            # Add a line break for spacing
            st.markdown("<br>", unsafe_allow_html=True)  # Adds a line break
            approver = st.text_input("承認サインを入力してください。")
        go = gop.update_rfl_sender_receiver_info(sender_or_receiver)
        st.session_state.rfl_approve_updata = AgGrid(
            final_df,
            custom_css=css_ag,
            gridOptions=go,
            reload_data=False,
            height=220,
        )

        if st.button(btn_txt):
            if btn_txt == '承認' and (approver is None or approver == ''):
                st.error('承認サインを入力してください。')
            else:
                approve_data = st.session_state.rfl_approve_updata['data']
                appr_df = pd.DataFrame(approve_data)
                rfl_upd_result = sql.update_rfl_approved_record(appr_df,approver,sender_or_receiver)
                if rfl_upd_result:
                    execute_rfl_list()
                st.rerun()
    
#山口 TOサマリからRFL更新用ダイアログ
@st.dialog("更新確認",width="large")       
def update_rfl_by_to_summary(df_selecteds):
    st.write("下記データを選択しました。最終確認を行ってください。")
    st.write("本当に更新する場合パラメータを選択をし実行ボタンを押下してください。")
    go = gop.update_conf_go_rfl_by_to_summary()
    rfl_by_to_summary_grid = AgGrid(
           df_selecteds,
           custom_css=css_ag,
           gridOptions=go,
           reload_data=False,
           height=220,
            )
    if st.button("実行"):
        sql.update_RFL_by_to_summary(df_selecteds)
        st.success("RFLを更新しました")
        time.sleep(1)
        st.session_state.flag_summary_before = st.session_state.flag_summary
        del st.session_state.rfl_list # delete old rfl infomation after update 4/16
        del st.session_state.df_display_on_summary
        st.rerun()

#ステートメント記入ダイアログ　＃チョー　04/16
@st.dialog('ステートメント記入', width='large')
def insert_r_statement():
    # Get the existing statement if available
    r_statement_def = ''
    if 'r_statement_df' in st.session_state and not st.session_state.r_statement_df.empty:
        r_statement_def = st.session_state.r_statement_df.iloc[0]['statement']

    # Display text area
    r_statement = st.text_area('ステートメントを入力してください。', height=170, value=r_statement_def)

    # Handle save button click
    if not st.button('保存'):
        return

    # Save new statement for each selected phase
    df_selects = st.session_state.df_selects
    for _, row in df_selects.iterrows():
        project_id = row['project_id']
        phase_id = row['phase_id']
        if sql.insert_upd_r_statement(project_id, phase_id, 'R', r_statement):
            st.session_state.summary_rlist_flag = True
            st.session_state.r_sum_reload_flag = True #チョー 05/07　記入後、リロードするため
            st.rerun()        

#TOのステートメント更新用作る。　ほんとにいつかまとめたい。。。
@st.dialog('ステートメント記入', width='large')
def insert_to_statement():
    # Get the existing statement if available
    to_statement_def = ''
    if 'df_to_statement' in st.session_state and not st.session_state.df_to_statement.empty:
        to_statement_def = st.session_state.df_to_statement.iloc[0]['statement']

    # Display text area
    to_statement = st.text_area('ステートメントを入力してください。', height=170, value=to_statement_def)

    # Handle save button click
    if not st.button('保存'):
        return

    # Save new statement for each selected phase
    df_selects = st.session_state.df_selects
    for _, row in df_selects.iterrows():
        project_id = row['project_id']
        phase_id = row['phase_id']
        if sql.insert_upd_r_statement(project_id, phase_id, 'TO', to_statement):
            st.success("ステートメントを更新しました")
            time.sleep(1)
            st.session_state.flag_summary_before = st.session_state.flag_summary
            st.rerun()        
        
        

#Rサマリー変更ダイアログ　＃チョー　04/24
@st.dialog('サマリー内容変更確認', width='large')
def update_r_summary(changed_rows):
    st.write("下記データを選択しました。最終確認を行ってください。")
    st.write("本当に更新する場合、「実行」ボタンを押下してください。") #04/24
    go = gop.update_rlist_summary_grid()
    r_summary_update = AgGrid(
           changed_rows,
           custom_css=css_ag,
           gridOptions=go,
           reload_data=False,
           height=220,
        )
    
    if st.button("実行"):
        upd_r_summary_result = sql.insert_upd_r_summary(pd.DataFrame(r_summary_update['data']))
        if upd_r_summary_result:
            st.session_state.summary_rlist_flag = True
            st.session_state.r_sum_reload_flag = True #チョー 05/07　内容変更後、リロードするため
            st.rerun()

@st.dialog('コスト情報更新', width='large')
def update_cost_info(df_cost_updated ):
    df_cost_to_update = df_cost_updated[df_cost_updated['selected']==True]
    st.write(df_cost_to_update)
    st.write("下記データを選択しました。最終確認を行ってください。")#山口　編集方法変更に伴い文言を変えた　10/25
    # go = gop.go_update_cost_info(df_cost_rate, df_surrogate_model_parameter, df_cost_item)
    go = gop.go_dialog_cost_info()
    ag_cost_to_update = AgGrid(df_cost_to_update, 
                     go,
                     allow_unsafe_jscode=True,
                     custom_css=css_ag,
                     fit_columns_on_grid_load=True,
                     )
    df_cost_to_update_confirmed = ag_cost_to_update['data'] 
    if st.button('更新'):
        st.write(df_cost_to_update_confirmed)
        sql.update_project_cost_item(df_cost_to_update_confirmed)
        del st.session_state.jcurb_project_ids_before # Jcurbのinitializationを再度行い再読み込みするため、変数削除
        st.success('更新が完了しました。')
        st.session_state.cost_updated=True
        st.rerun()

@st.dialog('コスト情報削除', width='large')
def delete_cost_info(df_cost_updated):
    df_cost_to_delete = df_cost_updated[df_cost_updated['selected']==True]
    st.write("下記データを選択しました。最終確認を行ってください。")
    # go = gop.go_update_cost_info(df_cost_rate, df_surrogate_model_parameter, df_cost_item)
    go = gop.go_dialog_cost_info()
    ag_cost_to_delete = AgGrid(df_cost_to_delete, 
                     go,
                     allow_unsafe_jscode=True,
                     custom_css=css_ag,
                     fit_columns_on_grid_load=True,
                     )
    df_cost_to_delete_confirmed = ag_cost_to_delete['data'] 
    if st.button('更新'):
        st.write(df_cost_to_delete_confirmed)
        sql.delete_project_cost_item(df_cost_to_delete_confirmed)
        del st.session_state.jcurb_project_ids_before # Jcurbのinitializationを再度行い再読み込みするため、変数削除
        st.success('更新が完了しました。')
        st.session_state.cost_updated=True
        st.rerun()

#Kyaw 10/29 モード保存機能のダイアログ #10/29 merge#5
@st.dialog('確認', width='small')
def confirm_resized_column_width():
    if 'changed_column_widths' in st.session_state or 'resize_column_result' in st.session_state:
        df = st.session_state.rlist_data_stuck
        #Drop duplicates using any column that contains *_id
        id_keywords = ["project_id", "phase_id", "variation_id"]
        id_columns = [col for col in df.columns if any(k in col for k in id_keywords)]

        df_deduped = df.drop_duplicates(subset=id_columns)

        #Create a mapping from original columns to cleaned keywords
        col_mapping = {}
        for col in id_columns:
            for keyword in id_keywords:
                if keyword in col:
                    col_mapping[col] = keyword
                    break

        #Select those columns from df_deduped and rename them
        df_selected = df_deduped[id_columns].rename(columns=col_mapping)  
        
        #Find the actual column names for each specific ID type
        project_col = next((col for col in df_deduped.columns if "project_id" in col), None)
        phase_col = next((col for col in df_deduped.columns if "phase_id" in col), None)
        variation_col = next((col for col in df_deduped.columns if "variation_id" in col), None)

        #Extract values (first row of deduplicated dataframe)
        project_id = df_deduped[project_col].iloc[0] if project_col else None
        phase_id = df_deduped[phase_col].iloc[0] if phase_col else None
        variation_id = df_deduped[variation_col].iloc[0] if variation_col else None

        changed_column_widths = st.session_state.changed_column_widths
        col_ids = [col["colId"] for col in changed_column_widths]
        widths = [col["width"] for col in changed_column_widths]
        hides = [col["hide"] for col in changed_column_widths]
        widths = [int(w) for w in widths]


        if st.session_state.changed_column_widths or not st.session_state.resize_column_result.empty:
            st.markdown('Personalモードを有効にすると、再ログイン後も列幅の変更内容が保持されます。Defaultモードに切り替えると、元の列幅が表示されますが、よろしいですか？')
            edit_mode = st.radio(
                label='モード選択',
                options=["***Personalモード***", "***Defaultモード***"],
                index=0,
                horizontal = True,
                label_visibility = 'collapsed'
            )

            toggle_on = True if edit_mode is '***Personalモード***' else False
 
            if st.button('確定'):
                result = sql.insert_edit_column(
                    project_id, phase_id, variation_id, st.session_state.username, col_ids, widths,hides,toggle_on
                )
                if result:
                    sql.get_resized_column(df_selected)
                    if not toggle_on:
                        del st.session_state.initial_column_widths
                    st.rerun()
        else:
            st.error('調整された列幅はありません。')



def selected_data_for_new_create(selected_data,selected_tab):
    if 'new_selected_archi' not in st.session_state:
        st.session_state['new_selected_archi'] = []
        st.session_state['new_selected_prj'] = []

    architecture_list = sql.get_project("architecture_name")
    selected_archi = st.multiselect(
        'PTシステムタイプ',
        architecture_list,
        key='new_archi_unique_key',
        max_selections = 1,
        default=st.session_state['new_selected_archi']
    )

    if 'new_selected_prj' not in st.session_state or len(selected_archi) <= 0:
        st.session_state['new_selected_prj'] = []

    project_code_list = sql.get_project("z_model_code", selected_archi)
    selected_project = st.multiselect(
        'プロジェクト:',
        project_code_list,
        key='new_prjunique_key',
        max_selections = 1,
        default=st.session_state['new_selected_prj'],
    )
    # st.session_state['selectoption1'] = selectoption1
    
    if 'new_selected_destination' not in st.session_state:
        st.session_state['new_selected_destination'] = []

    # print('selection 2: ', st.session_state['selectoption2'])

    destination_list = sql.get_project("destination", selected_project)
    selected_destination = st.multiselect(
        '仕向け:',
        destination_list,
        key='new_dest_unique_key',
        max_selections = 1,
        default=st.session_state['new_selected_destination'],
    )
    # st.session_state['selectoption2'] = selected_destination

    if 'new_selected_drive_system' not in st.session_state:
        st.session_state['new_selected_drive_system'] = []

    drive_system_list = sql.get_project("drive_system", selected_project, selected_destination)
    selected_drive_system = st.multiselect(
        '駆動方式:',
        drive_system_list,
        key='new_drive_unique_key',
        max_selections = 1,
        default=st.session_state['new_selected_drive_system'],
    )
    # st.session_state['selectoption3'] = selectoption3

    if 'new_selected_lot' not in st.session_state:
        st.session_state['new_selected_lot'] = []

    project_lot = sql.get_project("project_lot", selected_project, selected_destination, selected_drive_system)
    selected_lot = st.multiselect(
        'ロット:',
        project_lot,
        key='new_lot_unique_key',
        max_selections = 1,
        default=st.session_state['new_selected_lot'],
    )
    selected_phase_ids = []
    if selected_archi and selected_project and selected_destination and selected_drive_system and selected_lot:
        if 'new_selected_phase' not in st.session_state:
            st.session_state['new_selected_phase'] = []
        phase_list = sql.all_phase_to_create_new_project()
        # st.write('phase list: ', phase_list)
        selected_phase = st.multiselect(
            'フェーズ:',
            phase_list['phase'],
            key='new_phase_unique_key',
            max_selections = 1,
            default=st.session_state['new_selected_phase'],
        )
        selected_phase_ids = phase_list[phase_list['phase'].isin(selected_phase)]['id'].tolist()
        # st.write('selected phase ids:', selected_phase_ids)

    return selected_archi, selected_project, selected_destination, selected_drive_system, selected_lot, selected_phase_ids



def handle_project_for_new_create(selected_data, selected_tab):

    selected_archi, selected_project, selected_destination, selected_drive_system, selected_lot, selected_phase_ids = selected_data_for_new_create(selected_data, selected_tab)

    if st.button("作成"):
        # if not selected_archi and not selected_project and not selected_destination and not selected_drive_system and not selected_lot and len(selected_phase_ids) == 0:
        if (
            not selected_archi
            or not selected_project
            or not selected_destination
            or not selected_drive_system
            or not selected_lot
            or len(selected_phase_ids) == 0
        ):
            st.error('全て選択してくださぃ！！', icon="🚨")
        else:      
            if selected_data is None:
                st.error('ベースプロジェクトを選択してください。')
            elif len(selected_data) > 1:
                st.error('複数のベースプロジェクトを選択することはできません。')
            else:
                if int(st.session_state['chosen_id']) == 1:
                    inserted_res, res_msg = sql.insert_new_se_project(selected_data, selected_project, selected_destination, selected_drive_system, selected_lot, selected_phase_ids)
                if int(st.session_state['chosen_id']) == 2:
                    inserted_res, res_msg = sql.insert_new_rlist_and_rfl_list(selected_data, selected_project, selected_destination, selected_drive_system, selected_lot, selected_phase_ids)
                if res_msg != 'Success':
                    st.error('新規作成に失敗しました。')
                    st.error(res_msg)
                    
                if inserted_res and res_msg == 'Success':
                    st.session_state['new_selected_archi'] = selected_archi
                    st.session_state['new_selected_prj'] = selected_project
                    st.session_state['new_selected_destination'] = selected_destination
                    st.session_state['new_selected_drive_system'] = selected_drive_system
                    st.session_state['new_selected_lot'] = selected_lot
                    # st.session_state['architecture_name'] = selected_archi
                    st.session_state.login_begin = False
                    st.session_state.summary_rlist_flag = False
                    st.session_state.create_new_prj_success = True
                    st.rerun()
           

def is_empty(data):
    if isinstance(data, pd.DataFrame):
        return data.empty
    elif isinstance(data, list):
        return len(data) == 0
    return True  # Treat unknown types as e


@st.dialog("SE-LISTプロジェクト新規作成", width='medium')  
def create_new_se_prj():
    if 'prj_info_list' not in st.session_state or is_empty(st.session_state.prj_info_list):
        st.error('ベースプロジェクトの情報がありません。')
        st.session_state.login_begin = False
        st.session_state.summary_rlist_flag = False
    # if st.session_state.prj_info_list is not None:
    else:
        st.write("ベースプロジェクト一覧：")
        row_count = len(st.session_state.prj_info_list)
        
        row_height = 32  # Approximate row height
        header_height = 32
        scroll_padding = 24  # Extra space for horizontal scrollbar

        max_height = 300
        grid_height = min(row_count * row_height + header_height + scroll_padding + 10, max_height)

        #10/20 rename the columns name to use the same grid functions 
        st.session_state.prj_info_list_new = st.session_state.prj_info_list.rename(columns={
            'z_destination': 'destination',
            'z_drive_system': 'drivetrain',
            'z_name': 'lot',
            'z_class_name_get_str': 'phase'
        })



        go = gop.base_project_grid()
        st.session_state.selected_new_insert_data = AgGrid(
            st.session_state.prj_info_list_new,
            custom_css=css_ag,
            gridOptions=go,
            reload_data=False,
            height=grid_height
        )
        
        selected_data = st.session_state.selected_new_insert_data['selected_rows']

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("ベースプロジェクト一覧でチェックされたプロジェクトの項目を、下記のプロジェクトに反映します。よろしいでしょうか？")
        handle_project_for_new_create(selected_data,'SE')



@st.dialog("R-LISTプロジェクト新規作成", width='medium')  
def create_new_r_and_rfl_prj():

    if 'total_rlist_prj' not in st.session_state or is_empty(st.session_state.total_rlist_prj):
        st.error('ベースプロジェクトの情報がありません。')
        st.session_state.login_begin = False
        st.session_state.summary_rlist_flag = False
        # st.rerun()
    else:   
        st.write("ベースプロジェクト一覧：")
        row_count = len(st.session_state.total_rlist_prj)
        
        row_height = 32  # Approximate row height
        header_height = 32
        scroll_padding = 24  # Extra space for horizontal scrollbar

        max_height = 300
        grid_height = min(row_count * row_height + header_height + scroll_padding + 10, max_height)


        go = gop.base_project_grid()
        st.session_state.selected_new_insert_data = AgGrid(
            st.session_state.total_rlist_prj,
            custom_css=css_ag,
            gridOptions=go,
            reload_data=False,
            height=grid_height
        )
        
        selected_data = st.session_state.selected_new_insert_data['selected_rows']

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("ベースプロジェクト一覧でチェックされたプロジェクトの項目を、下記のプロジェクトに反映します。よろしいでしょうか？")
        handle_project_for_new_create(selected_data,'R')
        







    

        
        


