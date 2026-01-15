from sqlalchemy import false
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
from db.rfl_repository import RFLRepository as rflq #telema-kyaw
import re


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
    # st.write('test sim upd: ', st.session_state.updata_conf_dia_result)
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
    #telema-kyaw feedback #11/05
    phase_list = sql.get_project("phase_list",
                st.session_state['selectoption1'],
                st.session_state['selectoption2'],
                st.session_state['selectoption3'],
                st.session_state['selectoption4'])
    st.session_state.other_phase = phase_list


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
        execute_sim_list(False)
    elif selected_tab == 'rfl_list':
        # execute_rfl_list()
        execute_rfl_list_tlm()  #11/05

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
def execute_sim_list(reload_r = False): #sim-fixedしたとき、R情報もリロードする必要なのでreload_r = Falseを追加しました。
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

    if reload_r is True:
        df1, df2 = sql.posgre_get_rlist(
            st.session_state['selectoption1'],
            st.session_state['selectoption2'],
            st.session_state['selectoption3'],
            st.session_state['selectoption4'],
            st.session_state['selectoption5']
        )
        st.session_state.r_prj_info_list = df1
        st.session_state.rlist_data_stuck = df2
    st.session_state.chosen_id = 3
    st.rerun()

# #チョー　03/10
# def execute_rfl_list():
#     df1 = sql.posgre_get_rfl(
#         st.session_state['selectoption1'],
#         st.session_state['selectoption2'],
#         st.session_state['selectoption3'],
#         st.session_state['selectoption4'],
#         st.session_state['selectoption5']
#     )
    
#     st.session_state.rfl_list = df1
#     st.session_state.chosen_id = 4
#     st.rerun()

#telema-kyaw  #11/05
def execute_rfl_list_tlm():
    # df1 = rflq.posgre_get_rfl_tlm(
    #     st.session_state['selectoption1'],
    #     st.session_state['selectoption2'],
    #     st.session_state['selectoption3'],
    #     st.session_state['selectoption4'],
    #     st.session_state['selectoption5'],
    #     # st.session_state['selectoption6'],
    #     # st.session_state['selectoption7'],
    #     # st.session_state['selected_hr'],
    #     # st.session_state['wp']
    # )
    # st.session_state.rfl_list = df1

    if 'wp' not in st.session_state:
        st.session_state.wp = []

    # rfl_list_info = rflq.get_rfl_all_hierarchy_levels(st.session_state.wp, True)
    rfl_list_info = rflq.get_rfl_all_hierarchy_levels(
                                        st.session_state['selectoption1'],
                                        st.session_state['selectoption2'],
                                        st.session_state['selectoption3'],
                                        st.session_state['selectoption4'],
                                        st.session_state['selectoption5'],
                                        st.session_state.wp, True)
    st.write('rfl list info: ', rfl_list_info)
    
    st.session_state.rfl_list = rfl_list_info

    #update_bk 11/19
    rfl_all_info = sql.posgre_get_rfl(
        st.session_state['selectoption1'],
        st.session_state['selectoption2'],
        st.session_state['selectoption3'],
        st.session_state['selectoption4'],
        st.session_state['selectoption5']
    )
    # rfl_all_info = rflq.get_rfl_all_hierarchy_levels(
    #                 st.session_state['selectoption1'],
    #                 st.session_state['selectoption2'],
    #                 st.session_state['selectoption3'],
    #                 st.session_state['selectoption4'],
    #                 st.session_state['selectoption5'],
    #                 [], True)
    st.session_state.rfl_matrix = rfl_all_info

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

        #telema-kyaw start  #11/05
        st.session_state.other_phase = phase_list

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
    yaml_file_path = rf'C:\Users\GWE00224\OneDrive - Nissan Motor Corporation\simrequest_variables\{yaml_file_name}'
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

@st.dialog("RFLへ転記",width='large') # 山口　RFL転記用ダイアログ　2/6 複数プロジェクト選択されていると起用に選択肢を追加する必要あり　2/11 whats a mess 
def send_to_RFL_YamaguciFunc():
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
    st.write('df selected study: ', df_selected_study)
    #選択されたスタディの必要情報を取得する
    senario_parameter_col = [col for col in df_selected_study.columns if 'senario_parameter_id' in col][0] #senario_parameter_idが含まれる列はこの時点で1列の想定
    st.write('senario_parameter cols: ', senario_parameter_col)
    selected_performance = df_selected_study[df_selected_study[senario_parameter_col]==15].loc[:,df_selected_study.columns.str.contains(';value;')].values.tolist()[0][0]#変な取り方の自覚あるけど直す時間ない
    st.write('selected perf:', selected_performance)
    if selected_performance is None:
        st.error(selected_study_id + "には性能領域の入力がありません。")
        return 
    selected_requirement = df_selected_study[df_selected_study[senario_parameter_col]==3].loc[:,df_selected_study.columns.str.contains(';value;')].values.tolist()[0][0]
    st.write('selected req: ', selected_requirement)
    if selected_requirement is None:
        st.error(selected_study_id + "には目標性能の入力がありません。")
        return
    selected_usecase = df_selected_study[df_selected_study[senario_parameter_col]==14].loc[:,df_selected_study.columns.str.contains(';value;')].values.tolist()[0][0]
    st.write('selected usecase: ', selected_usecase)
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
    st.write('selected perf: ',selected_performance)
    # st.write(project_id)
    # st.write(phase_id)
    # st.write(variation_id)
    st.write(df_send_info)
    if st.button('実行'):
        sql.update_RFL_by_senario(selected_performance, selected_requirement, selected_usecase, project_id, phase_id, variation_id, df_send_info, username, now)
        #st.write('pretend something happens')
        st.success("RFL更新しました")


@st.dialog("RFLへ転記",width='large') # 山口　RFL転記用ダイアログ　2/6 複数プロジェクト選択されていると起用に選択肢を追加する必要あり　2/11 whats a mess 
def send_to_RFL_kyaw_edit_yamaguchifunc():
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
    st.write('df selected study: ', df_selected_study)
    #選択されたスタディの必要情報を取得する
    senario_parameter_col = [col for col in df_selected_study.columns if 'senario_parameter_id' in col][0] #senario_parameter_idが含まれる列はこの時点で1列の想定
    st.write('senario_parameter cols: ', senario_parameter_col)
    selected_performance = df_selected_study[df_selected_study[senario_parameter_col]==15].loc[:,df_selected_study.columns.str.contains(';value;')].values.tolist()[0][0]#変な取り方の自覚あるけど直す時間ない
    st.write('selected perf:', selected_performance)
    if selected_performance is None:
        st.error(selected_study_id + "には性能領域の入力がありません。")
        return 
    selected_requirement = df_selected_study[df_selected_study[senario_parameter_col]==3].loc[:,df_selected_study.columns.str.contains(';value;')].values.tolist()[0][0]
    st.write('selected req: ', selected_requirement)
    if selected_requirement is None:
        st.error(selected_study_id + "には目標性能の入力がありません。")
        return
    selected_usecase = df_selected_study[df_selected_study[senario_parameter_col]==14].loc[:,df_selected_study.columns.str.contains(';value;')].values.tolist()[0][0]
    st.write('selected usecase: ', selected_usecase)
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
    st.write('selected perf: ',selected_performance)
    # st.write(project_id)
    # st.write(phase_id)
    # st.write(variation_id)
    st.write(df_send_info)
    if st.button('実行'):
        df_RFL_to_edit = sql.update_RFL_by_senario(selected_performance, selected_requirement, selected_usecase, project_id, phase_id, variation_id, df_send_info, username, now)
        #st.write('pretend something happens')
        st.write('result: ', df_RFL_to_edit)
        for i, row in df_send_info.iterrows():
            rflcategory = row[3]
            targetid = row[4]#山口　ここのIDはRFLテーブルのIDではなくｒ、ｆ、ｌいずれかのテーブルのＩＤ

            value = row[2]
            st.write('targetid: ', targetid)
            if rflcategory =='R':
                st.write('write first:',df_RFL_to_edit[df_RFL_to_edit['requirement_id']==targetid])
                st.write('write sec:',df_RFL_to_edit[df_RFL_to_edit['requirement_id']==targetid]['rfl_id'].values.tolist() )
                rflids = df_RFL_to_edit[df_RFL_to_edit['requirement_id']==targetid]['rfl_id'].values.tolist() 

                ids_str = ', '.join('%s' for _ in rflids)
                # st.write('r rfl id:',rflids)
                st.write('r rfl_ids_str: ',rflids)
                st.write('in R:',(value, *rflids))
                # query = f"update prj_rfl set requirement = %s where project_info_id = %s and phase_id = %s and rfl_id in ({ids_str});"
                    
                # print(query)
                # cur.execute(query,(value, project_id, phase_id,  *rflids))
                
            elif rflcategory=='F':
                rflids = df_RFL_to_edit[df_RFL_to_edit['function_id']==targetid]['rfl_id'].values.tolist() 
                ids_str = ', '.join('%s' for _ in rflids)
                st.write('f rfl_ids_str: ',rflids)
                st.write('in F:',(value, *rflids))
                # query = f"update prj_rfl set function = %s where project_info_id = %s and phase_id = %s and rfl_id in ({ids_str});"
                # print(query)
                # cur.execute(query,(value, project_id, phase_id, *rflids))
            elif rflcategory =='L':
                rflids = df_RFL_to_edit[df_RFL_to_edit['logic_id']==targetid]['rfl_id'].values.tolist() 
                ids_str = ', '.join('%s' for _ in rflids)
                st.write('l rfl_ids_str: ',rflids)
                st.write('in L:',(value, *rflids))
                # query = f"update prj_rfl set logic = %s where project_info_id = %s and phase_id = %s and rfl_id in ({ids_str});"
                # print(query)
                # cur.execute(query,(value, project_id, phase_id, *rflids))
            else:
                st.error('unexpected error:rflcategory not match')
                continue
        st.success("RFL更新しました")


# def get_values_for_selectbox(df, scenario_param_id):
#     values = []

#     for col in df.columns:
#         if ';value;' in col:
#             spi_col = col.replace(';value;', ';senario_parameter_id;')

#             if spi_col in df.columns:
#                 vals = df.loc[df[spi_col] == scenario_param_id, col]
#                 values.extend(vals.dropna().tolist())

#     return values


def get_values_by_suffix(df, scenario_param_id, suffix=None):
    """
    Get values for scenario_param_id.
    If suffix is given, only consider columns whose name ends with that suffix.
    """
    values = []

    for col in df.columns:
        if ';value;' in col:
            # corresponding senario_parameter_id column
            spi_col = col.replace(';value;', ';senario_parameter_id;')
            if spi_col in df.columns and (df[spi_col] == scenario_param_id).any():
                # if suffix is given, filter columns by suffix
                if suffix is None or col.endswith(suffix):
                    vals = df.loc[df[spi_col] == scenario_param_id, col]
                    values.extend(vals.dropna().tolist())

    # remove duplicates and sort
    return sorted(list(dict.fromkeys(values)))

def selectbox_and_filter(df, scenario_param_id, label, prev_suffixes=None):
    """
    Show a selectbox for a given scenario_param_id and filter df based on selected value's suffix(es).

    Args:
        df: pd.DataFrame to filter
        scenario_param_id: int, the scenario_param_id for get_values_by_suffix
        label: str, label for the Streamlit selectbox
        prev_suffixes: list of suffix strings to filter options before selection

    Returns:
        selected_value: str, the value chosen in selectbox
        filtered_df: pd.DataFrame filtered based on suffix(es)
        suffixes: list of str, suffix(es) of selected value
    """
    # Determine suffix argument for get_values_by_suffix safely
    if prev_suffixes:
        suffix_arg = prev_suffixes[0]
    else:
        suffix_arg = None

    # Get options for selectbox
    options = get_values_by_suffix(df, scenario_param_id, suffix=suffix_arg)
    options = ['選択してください。'] + options

    # Show selectbox
    selected_value = st.selectbox(label, options)

    if selected_value != '選択してください。':
        # Find all columns where selected value exists
        matching_cols = [col for col in df.columns if ';value;' in col and (df[col] == selected_value).any()]

        if matching_cols:
            # Extract unique suffixes from all matching columns
            suffixes = list({col.split(';')[-1] for col in matching_cols})

            # Filter df to keep columns containing any of these suffixes
            filtered_columns = [col for col in df.columns if any(suf in col for suf in suffixes)]
            filtered_df = df[filtered_columns].copy()
        else:
            # No matching columns found: fallback
            suffixes = prev_suffixes if prev_suffixes else []
            filtered_df = df.copy()
    else:
        # Nothing selected: fallback
        suffixes = prev_suffixes if prev_suffixes else []
        filtered_df = df.copy()
    st.write('selected value: ', selected_value)
    # st.write('filtered df: ', filtered_df)
    # st.write('suffixes: ', suffixes)
    return selected_value, filtered_df, suffixes


@st.dialog("RFLへ転記",width='large') # 山口　RFL転記用ダイアログ　2/6 複数プロジェクト選択されていると起用に選択肢を追加する必要あり　2/11 whats a mess 
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
    st.write('fixed cols: ', fixed_columns)

    # 3. split column names and take the last part
    split_parts = [col.split(';')[-1] for col in fixed_columns]
    st.write('split parts: ', split_parts)

    # 4. find columns in sim_data_stuck that CONTAIN those split parts
    matched_columns = [
        col for col in sim_data_stuck.columns
        if any(part in col for part in split_parts)
    ]
    # st.write('match cols: ', matched_columns)

    # 5. create new DataFrame
    new_df = sim_data_stuck[matched_columns].copy()
    st.write('new df: ', new_df)

    # # 1️⃣ First selectbox (no suffix filter)
    # options_15 = get_values_by_suffix(new_df, 15)
    # options_15 = ['選択してください。'] + options_15  # add placeholder at the top

    # selected_value_performance = st.selectbox(
    #     '領域',
    #     options_15
    # )

    # # Determine the suffix of the selected column dynamically
    # if selected_value_performance != '選択してください。':
    #     col_15 = [col for col in new_df.columns if ';value;' in col and (new_df[col] == selected_value_performance).any()][0]
    #     suffix_15 = col_15.split(';')[-1]  # e.g., 'P1提案仕様00_J32V'
    #     # 🔽 filter new_df by suffix
    #     filtered_columns = [
    #         col for col in new_df.columns
    #         if suffix_15 in col
    #     ]
    #     new_df = new_df[filtered_columns].copy()
    #     st.write('filtered new df: ', new_df)
    # else:
    #     suffix_15 = None  # nothing selected

    # st.write('suffix 15: ', suffix_15)
    # st.write('newdf after 15: ', new_df)

    # # 2️⃣ Second selectbox (filter by suffix of the first selection)
    # options_56 = get_values_by_suffix(new_df, 56, suffix=suffix_15)
    # options_56 = ['選択してください。'] + options_56

    # selected_value_design_item1 = st.selectbox(
    #     '設計項目（大）',
    #     options_56
    # )

    # # 3️⃣ Third selectbox (filter by same suffix)
    # options_57 = get_values_by_suffix(new_df, 57, suffix=suffix_15)
    # options_57 = ['選択してください。'] + options_57

    # selected_value_design_item2 = st.selectbox(
    #     '設計項目（小）',
    #     options_57
    # )

    # # 4️⃣ Fourth selectbox (filter by same suffix)
    # options_3 = get_values_by_suffix(new_df, 3, suffix=suffix_15)
    # options_3 = ['選択してください。'] + options_3

    # selected_value_requirement = st.selectbox(
    #     '目標性能',
    #     options_3
    # )

    # -------------------------
    # Usage for your 4 selectboxes

    # 1️⃣ First selectbox
    selected_value_performance, new_df, suffixes = selectbox_and_filter(new_df, 15, '領域')

    # 2️⃣ Second selectbox
    selected_value_design_item1, new_df, suffixes = selectbox_and_filter(new_df, 56, '設計項目（大）', prev_suffixes=suffixes)

    # 3️⃣ Third selectbox
    selected_value_design_item2, new_df, suffixes = selectbox_and_filter(new_df, 57, '設計項目（小）', prev_suffixes=suffixes)

    # 4️⃣ Fourth selectbox
    selected_value_requirement, new_df, suffixes = selectbox_and_filter(new_df, 3, '目標性能', prev_suffixes=suffixes)
    st.write('new df: ', new_df)
    st.write('suffixes: ', suffixes)
        

    # options_15 = get_values_for_selectbox(new_df, 15)
    # selected_value_performance = st.selectbox(
    #     'Select value (scenario_param_id = 15)',
    #     options_15
    # )

    # options_56 = get_values_for_selectbox(new_df, 56)
    # selected_value_design_item1 = st.selectbox(
    #     'Select value (scenario_param_id = 56)',
    #     options_56
    # )

    # options_57 = get_values_for_selectbox(new_df, 57)
    # selected_value_design_item2 = st.selectbox(
    #     'Select value (scenario_param_id = 57)',
    #     options_57
    # )

    # options_3 = get_values_for_selectbox(new_df, 3)
    # selected_value_requirement = st.selectbox(
    #     'Select value (scenario_param_id = 3)',
    #     options_3
    # )
    # project_id = int(
    #     (
    #         new_df.loc[:, new_df.columns.str.contains(';project_id;')]
    #         .stack()
    #         .dropna()
    #         .iloc[0]
    #     )
    # )
    selected_usecase_list = get_values_by_suffix(new_df, 14)
    st.write('selected usecase list:', selected_usecase_list)

    # project_id = int(new_df.loc[:,new_df.columns.str.contains(';project_id;')].values.tolist()[0][0])
    # phase_id = int(new_df.loc[:,new_df.columns.str.contains(';phase_id;')].values.tolist()[0][0])
    # variation_id = int(new_df.loc[:,new_df.columns.str.contains(';variation_id;')].values.tolist()[0][0])
    project_ids = new_df.filter(like=';project_id;').iloc[0].drop_duplicates().astype(int).tolist()
    phase_ids = new_df.filter(like=';phase_id;').iloc[0].drop_duplicates().astype(int).tolist()
    variation_ids = new_df.filter(like=';variation_id;').iloc[0].drop_duplicates().astype(int).tolist()

    st.write('pj id: ', project_ids)
    st.write('ph id: ', phase_ids)
    st.write('var id: ', variation_ids)

    keys = [
        'study_id',
        'parameter_name_1',
        'parameter_name_2',
        'value',
        'rflcategory',
        'rflid'
    ]

    cols_to_keep = [
        col for col in new_df.columns
        if any(f';{key};{suf}' in col for key in keys for suf in suffixes)
    ]

    filtered_new_df = new_df[cols_to_keep].copy()
    # st.write('filtered new df1: ', filtered_new_df)

    # find rflid columns for current suffixes
    rflid_cols = [
        col for col in filtered_new_df.columns
        if any(f';rflid;{suf}' in col for suf in suffixes)
    ]

    value_cols = [
        col for col in filtered_new_df.columns
        if any(f';value;{suf}' in col for suf in suffixes)
    ]

    def has_value(df, cols):
        return (
            df[cols]
            .notna()
            & (df[cols].astype(str).apply(lambda s: s.str.strip() != ''))
        ).any(axis=1)
    
    mask = has_value(filtered_new_df, rflid_cols) & has_value(filtered_new_df, value_cols)

    filtered_new_df = filtered_new_df[mask].copy()


    # # drop rows where rflid is null / empty
    # filtered_new_df = filtered_new_df[
    #     filtered_new_df[rflid_cols]
    #     .apply(
    #         lambda row: row.notna() & (row.astype(str).str.strip() != '')
    #     )
    #     .any(axis=1)
    # ].copy()

    st.write('filtered new df2: ', filtered_new_df)
    # st.write('filtered new df2 stack: ', filtered_new_df.stack())
    


    if st.button('次へ'):
        if selected_value_performance == '選択してください。':
            st.error('領域を選択してください。')
        elif selected_value_performance == 'PTシステムレビュー向け全R項目':
            st.error('指定されたプロジェクト、フェーズ、性能、ユースケースに該当するRFLが見つかりませんでした。')
        else:
            df_RFL_to_edit = sql.get_RFL_by_senario([selected_value_performance], selected_value_requirement, selected_usecase_list, project_ids, phase_ids, variation_ids, filtered_new_df, suffixes, username, now)
            st.write('df_RFL_to_edit: ', df_RFL_to_edit)
            # st.write('return res2: ', return_res2)
            # --- Process each suffix ---
            final_dfs = []

            for suf in suffixes:
                # Identify columns for this suffix
                studyid_col = [c for c in filtered_new_df.columns if f'study_id;{suf}' in c][0]
                param1_col = [c for c in filtered_new_df.columns if f'parameter_name_1;{suf}' in c][0]
                param2_col = [c for c in filtered_new_df.columns if f'parameter_name_2;{suf}' in c][0]
                rflcat_col = [c for c in filtered_new_df.columns if f'rflcategory;{suf}' in c][0]
                rflid_col = [c for c in filtered_new_df.columns if f'rflid;{suf}' in c][0]
                value_col = [c for c in filtered_new_df.columns if f'value;{suf}' in c][0]

                # Normalize column names
                base_cols = {
                    studyid_col: 'study_id',
                    param1_col: 'parameter_name_1',
                    param2_col: 'parameter_name_2',
                    rflcat_col: 'rflcategory',
                    rflid_col: 'rflid',
                    value_col: 'value'
                }
                send_df = filtered_new_df.rename(columns=base_cols)[list(base_cols.values())]

                # Split by R / F / L
                df_R = send_df[send_df['rflcategory'] == 'R'].copy()
                df_F = send_df[send_df['rflcategory'] == 'F'].copy()
                df_L = send_df[send_df['rflcategory'] == 'L'].copy()

                # Skip if no R rows
                if df_R.empty:
                    continue

                # Rename ID columns to match df_RFL_to_edit
                df_R = df_R.rename(columns={'rflid': 'requirement_id'})
                df_F = df_F.rename(columns={'rflid': 'function_id'})
                df_L = df_L.rename(columns={'rflid': 'logic_id'})

                # Prefix all columns
                df_R = df_R.add_prefix('r_')
                df_F = df_F.add_prefix('f_')
                df_L = df_L.add_prefix('l_')
                st.write('df r: ', df_R)
                st.write('df f: ', df_F)
                st.write('df l: ', df_L)

                mask = df_RFL_to_edit['requirement_id'].isin(df_R['r_requirement_id'])

                if not df_F.empty:
                    mask |= df_RFL_to_edit['function_id'].isin(df_F['f_function_id'])

                if not df_L.empty:
                    mask |= df_RFL_to_edit['logic_id'].isin(df_L['l_logic_id'])

                rfl_to_upd_df = df_RFL_to_edit[mask].copy()

                st.write('rfl to upd df: ', rfl_to_upd_df)


                # # Merge R -> df_RFL_to_edit
                # r_join = df_R.merge(
                #     df_RFL_to_edit,
                #     left_on='r_requirement_id',
                #     right_on='requirement_id',
                #     how='inner'
                # )

                # # Merge F linked by function_id
                # if not df_F.empty:
                #     rf_join = r_join.merge(
                #         df_F,
                #         left_on='function_id',
                #         right_on='f_function_id',
                #         how='left'
                #     )
                # else:
                #     rf_join = r_join.copy()

                # # Merge L linked by logic_id
                # if not df_L.empty:
                #     rfl_join = rf_join.merge(
                #         df_L,
                #         left_on='logic_id',
                #         right_on='l_logic_id',
                #         how='left'
                #     )
                # else:
                #     rfl_join = rf_join.copy()
                # st.write('rfl_join: ', rfl_join)

                # # Ensure all expected final columns exist
                # final_cols = [
                #     'r_study_id','r_parameter_name_1','r_parameter_name_2','r_rflcategory','r_requirement_id','r_value',
                #     'f_study_id','f_parameter_name_1','f_parameter_name_2','f_rflcategory','f_function_id','f_value',
                #     'l_study_id','l_parameter_name_1','l_parameter_name_2','l_rflcategory','l_logic_id','l_value'
                # ]
                # for col in final_cols:
                #     if col not in rfl_join.columns:
                #         rfl_join[col] = None

                # final_dfs.append(rfl_join[final_cols])

            # # Combine all suffixes
            # if final_dfs:
            #     final_df = pd.concat(final_dfs, axis=0, ignore_index=True)
            # else:
            #     final_df = pd.DataFrame(columns=final_cols)
            # st.write('final df: ', final_df)
            # st.success('true')



    
    # fixed_study_ids = [col.split(selectoption6)[-1]  for col in fixed_columns]
    # selected_study_id = st.selectbox(
    #     '転記するStudyID:',
    #     fixed_study_ids,
    #     key='selected_study_dashboard_id'
    #     )
    # df_selected_study = sim_data_stuck.loc[:, sim_data_stuck.columns.str.contains(selected_study_id)]
    # st.write('df selected study: ', df_selected_study)
    # #選択されたスタディの必要情報を取得する
    # senario_parameter_col = [col for col in df_selected_study.columns if 'senario_parameter_id' in col][0] #senario_parameter_idが含まれる列はこの時点で1列の想定
    # st.write('senario_parameter cols: ', senario_parameter_col)
    # selected_performance = df_selected_study[df_selected_study[senario_parameter_col]==15].loc[:,df_selected_study.columns.str.contains(';value;')].values.tolist()[0][0]#変な取り方の自覚あるけど直す時間ない
    # st.write('selected perf:', selected_performance)
    # if selected_performance is None:
    #     st.error(selected_study_id + "には性能領域の入力がありません。")
    #     return 
    # selected_requirement = df_selected_study[df_selected_study[senario_parameter_col]==3].loc[:,df_selected_study.columns.str.contains(';value;')].values.tolist()[0][0]
    # st.write('selected req: ', selected_requirement)
    # if selected_requirement is None:
    #     st.error(selected_study_id + "には目標性能の入力がありません。")
    #     return
    # selected_usecase = df_selected_study[df_selected_study[senario_parameter_col]==14].loc[:,df_selected_study.columns.str.contains(';value;')].values.tolist()[0][0]
    # st.write('selected usecase: ', selected_usecase)
    # if selected_usecase is None:
    #     st.error(selected_study_id + "には走行パターン名の入力がありません。")
    #     return

    # project_id = df_selected_study.loc[:,df_selected_study.columns.str.contains(';project_id;')].values.tolist()[0][0]
    # phase_id = df_selected_study.loc[:,df_selected_study.columns.str.contains(';phase_id;')].values.tolist()[0][0]
    # variation_id = df_selected_study.loc[:,df_selected_study.columns.str.contains(';variation_id;')].values.tolist()[0][0]
    
    # parameter_name_1_col = [col for col in df_selected_study.columns if 'parameter_name_1' in col][0]
    # #send_info_col = [col for col in df_selected_study.columns if 'rflcategory' in col or 'rflid' in col or 'parameter_name_1' in col or 'parameter_name_2' in col or ';value;' in col] #山口　この方法では列の順番は不定になる　固定するため書き直し 2/13
    # rflcategory_col = [col for col in df_selected_study.columns if 'rflcategory' in col][0]
    # rflid_col = [col for col in df_selected_study.columns if 'rflid' in col][0]
    # parameter_name_2_col = [col for col in df_selected_study.columns if 'parameter_name_2' in col][0]
    # value_col =[col for col in df_selected_study.columns if ';value;' in col][0]
    # send_info_col = [parameter_name_1_col, parameter_name_2_col,  value_col, rflcategory_col, rflid_col]
    # # st.write(df_selected_study[send_info_col])
    # #山口　下記df_send_info定義は、rflidが記入あるものとしたい 
    # # df_send_info = df_selected_study[df_selected_study[parameter_name_1_col]=='Output ' +selected_performance][send_info_col]
    # df_send_info = df_selected_study.dropna(subset=[value_col,  rflid_col])[send_info_col]
    # st.write('走行パターン' + selected_usecase)
    # st.write('selected perf: ',selected_performance)
    # # st.write(project_id)
    # # st.write(phase_id)
    # # st.write(variation_id)
    # st.write(df_send_info)
    # if st.button('実行'):
    #     sql.update_RFL_by_senario(selected_performance, selected_requirement, selected_usecase, project_id, phase_id, variation_id, df_send_info, username, now)
    #     #st.write('pretend something happens')
    #     st.success("RFL更新しました")




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



# @st.dialog("新規作成")
# def create_project1():
#     if 'phase_click' not in st.session_state:
#         st.session_state['phase_click'] = False
#     st.markdown("SEリストを新規作成します。<br>新規作成する項目を選択し、新しいロット/フェーズを設定してください。", unsafe_allow_html=True)
#     col1, col2, col3 = st.columns([1,1,2])
#     with col1:
#         lot_btn = st.button("ロット")
#     with col2:
#         phase_btn = st.button("フェーズ")

#     if lot_btn:
#         st.session_state['phase_click'] = False
#         st.write("ロットボタンを押した。")
#     if phase_btn:
#         st.session_state['phase_click'] = True
#     # if st.session_state['phase_click'] is True:
#     #     create_phase_dia1()

# @st.dialog("新規作成")
# def create_project2():
#     st.markdown("コピーするプロジェクトを選択してください。", unsafe_allow_html=True)
#     create_phase_dia2()



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
            usecase_list = ['WLTC','WOT', 'Eisenhower']#ユースケーステーブル作成後一覧を、RとProjの組み合わせでとれるようにする
            # First dropdown: design_item_1
            design_item1_list = df_R_parameter[df_R_parameter['performance']==R]['design_item_1'].drop_duplicates().tolist()

            if 'selectoptionDesignItem1' not in st.session_state:
                st.session_state['selectoptionDesignItem1'] = []

            if design_item1_list != st.session_state['selectoptionDesignItem1']:
                st.session_state['selectoptionDesignItem1'] = []

            selectoptionDesignItem1 = st.selectbox(
                '設計項目（大）',
                design_item1_list,
                key='unique_key_d1'
            )
            st.session_state['selectoptionDesignItem1'] = selectoptionDesignItem1
            designItem1 = selectoptionDesignItem1

            # Second dropdown: design_item_2 (dependent on first dropdown)
            design_item2_list = df_R_parameter[
                (df_R_parameter['performance'] == R) & 
                (df_R_parameter['design_item_1'] == selectoptionDesignItem1)
            ]['design_item_2'].drop_duplicates().tolist()
            # st.write('design_item2_list: ', design_item2_list)
            if 'selectoptionDesignItem2' not in st.session_state:
                st.session_state['selectoptionDesignItem2'] = []

            if design_item2_list != st.session_state['selectoptionDesignItem2']:
                st.session_state['selectoptionDesignItem2'] = []

            selectoptionDesignItem2 = st.selectbox(
                '設計項目（小）',
                design_item2_list,
                key='unique_key_d2'
            )

            st.session_state['selectoptionDesignItem2'] = selectoptionDesignItem2
            designItem2 = selectoptionDesignItem2


            # Third dropdown: design_item_3 (dependent on first dropdown)
            design_item3_list = df_R_parameter[
                (df_R_parameter['performance'] == R) & 
                (df_R_parameter['design_item_1'] == selectoptionDesignItem1) &
                (df_R_parameter['design_item_2'] == selectoptionDesignItem2)
            ]['design_item_3'].drop_duplicates().tolist()

            if 'selectoptionDesignItem3' not in st.session_state:
                st.session_state['selectoptionDesignItem3'] = []

            if design_item3_list != st.session_state['selectoptionDesignItem3']:
                st.session_state['selectoptionDesignItem3'] = []

            selectoptionDesignItem3 = st.selectbox(
                '検討項目',
                design_item3_list,
                key='unique_key_d3'
            )

            st.session_state['selectoptionDesignItem3'] = selectoptionDesignItem3
            designItem3 = selectoptionDesignItem3

            # #usecase_list = ['WLTC','WOT', 'Eisenhower']#ユースケーステーブル作成後一覧を、RとProjの組み合わせでとれるようにする
            # design_item_list = df_R_parameter[df_R_parameter['performance']==R]['design_item_3'].drop_duplicates().tolist() #山口　選んだ性能からユースケース選択 検討項目名に変更 1/30
            # if 'selectoptionDesignItem' not in st.session_state:
            #     st.session_state['selectoptionDesignItem'] = []
            # if design_item_list != st.session_state['selectoptionDesignItem']:
            #     st.session_state['selectoptionDesignItem'] = []
            # selectoptionDesignItem = st.selectbox(
            #     '検討項目:',
            #     design_item_list,
            #     key='unique_key_d'        
            # )
            # st.session_state['selectoptionDesignItem'] = selectoptionDesignItem
            # designItem = selectoptionDesignItem
            # #山口　検討項目と別にユースケースを選択させる用に変更 やっぱり検討項目に紐づくものが欲しい 4/1
            # df_usecase_list = sql.get_usecase_list()
            # usecase_list = df_R_parameter[df_R_parameter['performance']==R][df_R_parameter['design_item_3']==designItem]['usecase'].drop_duplicates().tolist()
            # if 'selectoptionUsecase' not in st.session_state:
            #     st.session_state['selectoptionUsecase'] = []
            # if design_item_list != st.session_state['selectoptionUsecase']:
            #     st.session_state['selectoptionUsecase'] = []
            # selectoptionUsecase = st.selectbox(
            #     'ユースケース',
            #     usecase_list,
            #     key='unique_key_u'
            # )
            
            #山口　検討項目と別にユースケースを選択させる用に変更 やっぱり検討項目に紐づくものが欲しい 4/1
            df_usecase_list = sql.get_usecase_list()
            usecase_list = df_R_parameter[df_R_parameter['performance']==R][df_R_parameter['design_item_3']==designItem3]['usecase'].drop_duplicates().tolist()
            if 'selectoptionUsecase' not in st.session_state:
                st.session_state['selectoptionUsecase'] = []
            if design_item3_list != st.session_state['selectoptionUsecase']:
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
                #designItemをdesignItem1,2,3に変更した　#12/04 Kyaw
                designItem1 = '-' #設計項目（大）
                designItem2 = '-' #設計項目（小）
                designItem3 = '-' #検討項目
                usecase = '-'
                usecase_submodel = '-'
                
            submodels = [Carbody_submodel, EM_Fr_submodel,  EM_Rr_submodel, Gearbox_Fr_submodel, Gearbox_Rr_submodel, Battery_submodel]
            variables = [Carbody_parameters,  EM_Fr_parameters, EM_Fr_MAPs, EM_Rr_parameters, EM_Rr_MAPs, Gearbox_Fr_parameters, Gearbox_Fr_MAPs, Gearbox_Rr_parameters, Gearbox_Rr_MAPs, Battery_parameters, Battery_MAPs]
            #sql.add_new_study(project_id, phase_id, variation_id, study_id)
            sql.add_new_study(project_id, phase_id, variation_id, study_id, R, designItem1, designItem2, designItem3, usecase, usecase_submodel, TD, submodels, variables)#山口　ユースケースサブモデる名を追加 R->designitemに変更 2/1 PTシステムレビュー向け全R項目に対応できるように変更する7/30
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
def choice_sim_fixed_bk():
    # if 'sim_study_list' not in st.session_state:
    #     st.session_state['sim_study_list'] = []
    # study_ids = st.session_state.sim_prj_info_list['study_id'].tolist()

    # Assuming st.session_state.sim_data_stuck contains your DataFrame
    sim_data_stuck = st.session_state.sim_data_stuck
    st.write('sim_data_stuck: ', sim_data_stuck)

    # Find columns that have 'senario_parameter_id' in their name (regardless of %% and other words)
    senario_columns = [col for col in sim_data_stuck.columns if 'senario_parameter_id' in col]
    st.write('senario_columns: ', senario_columns)
    # Now filter the data where 'senario_parameter_id' column has the value 3
    filtered_data = sim_data_stuck[sim_data_stuck[senario_columns].apply(lambda row: 3 in row.values, axis=1)]
    st.write('filtered_data: ', filtered_data)
    # Now, select columns that contain 'value' in their name
    filtered_value_columns = [col for col in filtered_data.columns if ';value;' in col]
    st.write('filtered_value_columns: ', filtered_value_columns)
    # Filter the data to show only those columns
    filtered_data = filtered_data[filtered_value_columns]
    st.write('filtered_data: ', filtered_data)
    dropdown_values = filtered_data.values.flatten()
    st.write('dropdown_values: ', dropdown_values)
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
                

#12/01 チョー　確定ダイアログ
@st.dialog("Fixed")
def choice_sim_fixed_bk2():
    # if 'sim_study_list' not in st.session_state:
    #     st.session_state['sim_study_list'] = []
    # study_ids = st.session_state.sim_prj_info_list['study_id'].tolist()

    # Assuming st.session_state.sim_data_stuck contains your DataFrame
    sim_data_stuck = st.session_state.sim_data_stuck
    # st.write('sim_data_stuck: ', sim_data_stuck)

    # # Find columns that have 'senario_parameter_id' in their name (regardless of %% and other words)
    # senario_columns = [col for col in sim_data_stuck.columns if 'senario_parameter_id' in col]
    
    # # Find columns that have 'study_id' in their name (regardless of %% and other words)
    # study_id_columns = [col for col in sim_data_stuck.columns if 'study_id' in col]
    
    # Helper function to filter data by senario_parameter_id and matching values
    def filter_by_parameter_values(data, senario_id, match_values):
        """
        Filter data to only include columns where senario_parameter_id has matching values.
        Returns filtered dataframe with only columns from matching study IDs.
        """
        # Find rows where the senario_parameter_id exists
        senario_cols = [col for col in data.columns if 'senario_parameter_id' in col]
        study_cols = [col for col in data.columns if 'study_id' in col]
        filtered_rows = data[data[senario_cols].apply(lambda row: senario_id in row.values, axis=1)]
        
        # Find which value columns have matching values, then get study_id
        matching_study_ids = set()
        value_cols = [col for col in data.columns if ';value;' in col]
        
        for idx, row in filtered_rows.iterrows():
            for value_col in value_cols:
                if row[value_col] in match_values:
                    col_suffix = value_col.split(';')[-1]
                    study_id_col = [c for c in study_cols if c.endswith(col_suffix)]
                    if study_id_col:
                        matching_study_ids.add(row[study_id_col[0]])
        
        # Get column suffixes for the matching study IDs
        matching_suffixes = set()
        for idx, row in data.iterrows():
            for study_col in study_cols:
                if row[study_col] in matching_study_ids:
                    matching_suffixes.add(study_col.split(';')[-1])
        
        # Filter columns
        filtered_cols = [col for col in data.columns if col.split(';')[-1] in matching_suffixes]
        return data[filtered_cols]
    
    # Filter by senario_parameter_id = 96 with value '有効'
    filtered_data_by_study = filter_by_parameter_values(sim_data_stuck, 96, ['有効'])
    st.write('filtered_data_by_study: ', filtered_data_by_study)
    
    # Helper function to get dropdown values for a specific senario_parameter_id from filtered data
    def get_dropdown_values(data, senario_id):
        filtered = data[[col for col in data.columns if 'senario_parameter_id' in col]].apply(lambda row: senario_id in row.values, axis=1)
        filtered_data = data[filtered]
        value_columns = [col for col in filtered_data.columns if ';value;' in col]
        values = filtered_data[value_columns].values.flatten()
        return sorted(list(set(values)))
    
    # Get dropdown values for senario_parameter_id = 15 (領域) only from valid study_names
    dropdown_values_perf = get_dropdown_values(filtered_data_by_study, 15)
    st.write('dropdown_values_perf: ', dropdown_values_perf)

    # performance_list = sql.get_sim_performance(study_ids)

    selected_area = st.multiselect(
        '領域',
        dropdown_values_perf,
        key ='selected_area_unique_key',
        default=dropdown_values_perf[0] if len(dropdown_values_perf) > 0 else []
    )
    
    # Filter by selected area values for senario_parameter_id = 15
    if selected_area:
        filtered_data_by_area = filter_by_parameter_values(filtered_data_by_study, 15, selected_area)
        st.write('filtered_data_by_area: ', filtered_data_by_area)
        dropdown_values = get_dropdown_values(filtered_data_by_area, 3)
    else:
        dropdown_values = []
    
    st.write('dropdown_values: ', dropdown_values)

    target_performance = st.multiselect(
        '目標性能',
        dropdown_values,
        key ='target_performance_unique_key',
        default=dropdown_values[0] if len(dropdown_values) > 0 else []
    )

    # Get study_id list after filtering by 領域 and 目標性能
    selected_study_ids = []
    if selected_area and target_performance:
        # Further filter by target_performance (senario_parameter_id 3)
        filtered_data_by_performance = filter_by_parameter_values(filtered_data_by_area, 3, target_performance)
        st.write('filtered_data_by_performance: ', filtered_data_by_performance)
        
        # Extract study_id values from the filtered data (excluding NULL/NaN values)
        study_id_cols_final = [col for col in filtered_data_by_performance.columns if 'study_id' in col]
        if study_id_cols_final:
            for idx, row in filtered_data_by_performance.iterrows():
                for study_col in study_id_cols_final:
                    value = row[study_col]
                    # Only add non-null values
                    if value is not None and str(value) != 'nan' and str(value).strip() != '':
                        selected_study_ids.append(value)
            selected_study_ids = list(set(selected_study_ids))  # Remove duplicates
        
        st.write('selected_study_ids (filtered by 領域 and 目標性能): ', selected_study_ids)

    if selected_area and target_performance:
        sim_proj_info_list = st.session_state.sim_prj_info_list
        project_ids = sim_proj_info_list['project_id'].unique().tolist()
        phase_ids = sim_proj_info_list['phase_id'].unique().tolist()
        variation_ids = sim_proj_info_list['variation_id'].unique().tolist()
        destinations = sim_proj_info_list['destination'].unique().tolist()
        drivetrains = sim_proj_info_list['drivetrain'].unique().tolist()
        performance_lists= sql.getr_value_to_sim(project_ids,destinations,drivetrains,phase_ids,variation_ids,selected_area, target_performance)

        st.write('performance_lists: ', performance_lists)

        if performance_lists.empty:
            st.error('No Performance Lists.')
        else:
            selected_performance_1 = st.multiselect(
                '設計項目（大）',
                performance_lists['design_item_1'].unique(),
                key ='selected_perf1_unique_key',
                # default=dropdown_values[0] if len(dropdown_values) > 0 else []
            )

            # Filter design_item_2 based on selected_performance_1
            if selected_performance_1:
                filtered_performance_lists = performance_lists[performance_lists['design_item_1'].isin(selected_performance_1)]
                design_item_2_options = filtered_performance_lists['design_item_2'].unique()
            else:
                design_item_2_options = []

            selected_performance_2 = st.multiselect(
                '設計項目（小）',
                design_item_2_options,
                key ='selected_perf2_unique_key',
            )
                
            # st.rerun()
    # selected_performance_1 = st.multiselect(
    #     '設計項目（大）',
    #     dropdown_values,
    #     key ='selected_perf1_unique_key',
    #     default=dropdown_values[0] if len(dropdown_values) > 0 else []
    # )

    # if target_performance:
    #     sim_proj_info_list = st.session_state.sim_prj_info_list
    #     project_ids = sim_proj_info_list['project_id'].unique().tolist()
    #     phase_ids = sim_proj_info_list['phase_id'].unique().tolist()
    #     variation_ids = sim_proj_info_list['variation_id'].unique().tolist()
    #     destinations = sim_proj_info_list['destination'].unique().tolist()
    #     drivetrains = sim_proj_info_list['drivetrain'].unique().tolist()
    #     performance_list2 = sql.getr_value_to_sim(project_ids,destinations,drivetrains,phase_ids,variation_ids,selected_performance_1)

    #     # study_ids = st.session_state.sim_prj_info_list['study_id'].tolist()

    #     selected_performance_2 = st.multiselect(
    #         '設計項目（小）',
    #         # ["WLTC","WLTC2","WLTC3"],
    #         performance_list2,
    #         key ='selected_perf2_unique_key',
            
    #     )

    #     if st.button('実行',key='fixed_sim_button_key_1'):
    #         if selected_performance_1 and selected_performance_2:
    #             fixed_list = sql.get_sim_fix_list(project_ids,destinations,drivetrains,phase_ids,variation_ids,selected_performance_1,selected_performance_2)
    #             if fixed_list.empty:
    #                 st.error('No Fixed Data.')
    #             else:
    #                 st.session_state.fixed_sim_info = fixed_list
    #                 st.session_state['fix_sim_study_list'] = True
    #                 st.rerun()
    #         else:
    #             st.error('項目を選択してください。')
                

#12/01 チョー　確定ダイアログ
@st.dialog("Fixed")
def choice_sim_fixed_bk3():
    # if 'sim_study_list' not in st.session_state:
    #     st.session_state['sim_study_list'] = []
    # study_ids = st.session_state.sim_prj_info_list['study_id'].tolist()

    # Assuming st.session_state.sim_data_stuck contains your DataFrame
    sim_data_stuck = st.session_state.sim_data_stuck
    # st.write('sim_data_stuck: ', sim_data_stuck)

    # # Find columns that have 'senario_parameter_id' in their name (regardless of %% and other words)
    # senario_columns = [col for col in sim_data_stuck.columns if 'senario_parameter_id' in col]
    
    # # Find columns that have 'study_id' in their name (regardless of %% and other words)
    # study_id_columns = [col for col in sim_data_stuck.columns if 'study_id' in col]
    
    # Step 1: Get valid study_ids where parameter 96 = '有効' (do this ONCE)
    senario_cols = [col for col in sim_data_stuck.columns if 'senario_parameter_id' in col]
    study_cols = [col for col in sim_data_stuck.columns if 'study_id' in col]
    value_cols = [col for col in sim_data_stuck.columns if ';value;' in col]
    
    # Find rows where parameter 96 exists #有効/無効列
    filtered_96 = sim_data_stuck[sim_data_stuck[senario_cols].apply(lambda row: 96 in row.values, axis=1)]
    
    # Get study_ids where parameter 96 = '有効'
    valid_study_ids = set()
    for idx, row in filtered_96.iterrows():
        for value_col in value_cols:
            if row[value_col] == '有効':
                col_suffix = value_col.split(';')[-1]
                study_id_col = [c for c in study_cols if c.endswith(col_suffix)]
                if study_id_col:
                    study_id_value = row[study_id_col[0]]
                    if study_id_value is not None and str(study_id_value) != 'nan' and str(study_id_value).strip() != '':
                        valid_study_ids.add(study_id_value)
    
    st.write('valid_study_ids (有効): ', valid_study_ids)
    
    # Helper function to get dropdown values for a specific parameter from valid study_ids
    def get_dropdown_values_for_studies(data, study_ids, senario_id):
        """Get dropdown values for a parameter, only from specified study_ids"""
        if not study_ids:
            return []
        
        # Find rows where the parameter exists
        senario_cols = [col for col in data.columns if 'senario_parameter_id' in col]
        study_cols = [col for col in data.columns if 'study_id' in col]
        value_cols = [col for col in data.columns if ';value;' in col]
        
        filtered_rows = data[data[senario_cols].apply(lambda row: senario_id in row.values, axis=1)]
        
        # Get values only from columns belonging to valid study_ids
        values = set()
        for idx, row in filtered_rows.iterrows():
            for value_col in value_cols:
                col_suffix = value_col.split(';')[-1]
                study_id_col = [c for c in study_cols if c.endswith(col_suffix)]
                if study_id_col and row[study_id_col[0]] in study_ids:
                    values.add(row[value_col])
        
        return sorted(list(values))
    
    # Get dropdown values for parameter 15 (領域) from valid study_ids
    dropdown_values_perf = get_dropdown_values_for_studies(sim_data_stuck, valid_study_ids, 15)
    st.write('dropdown_values_perf: ', dropdown_values_perf)

    selected_area = st.multiselect(
        '領域',
        dropdown_values_perf,
        key ='selected_area_unique_key',
        default=dropdown_values_perf[0] if len(dropdown_values_perf) > 0 else []
    )
    
    # Filter study_ids by selected_area (parameter 15)
    area_filtered_study_ids = valid_study_ids.copy()
    if selected_area:
        # Find which study_ids have the selected area values
        area_filtered_study_ids = set()
        filtered_15 = sim_data_stuck[sim_data_stuck[senario_cols].apply(lambda row: 15 in row.values, axis=1)]
        
        for idx, row in filtered_15.iterrows():
            for value_col in value_cols:
                if row[value_col] in selected_area:
                    col_suffix = value_col.split(';')[-1]
                    study_id_col = [c for c in study_cols if c.endswith(col_suffix)]
                    if study_id_col:
                        study_id_value = row[study_id_col[0]]
                        if study_id_value in valid_study_ids:  # Only include if it was already valid
                            area_filtered_study_ids.add(study_id_value)
        
        st.write('area_filtered_study_ids: ', area_filtered_study_ids)
        dropdown_values = get_dropdown_values_for_studies(sim_data_stuck, area_filtered_study_ids, 3)
    else:
        dropdown_values = []
    
    st.write('dropdown_values: ', dropdown_values)

    target_performance = st.multiselect(
        '目標性能',
        dropdown_values,
        key ='target_performance_unique_key',
        default=dropdown_values[0] if len(dropdown_values) > 0 else []
    )

    # Filter study_ids by target_performance (parameter 3)
    selected_study_ids = []
    if selected_area and target_performance:
        performance_filtered_study_ids = set()
        filtered_3 = sim_data_stuck[sim_data_stuck[senario_cols].apply(lambda row: 3 in row.values, axis=1)]
        
        for idx, row in filtered_3.iterrows():
            for value_col in value_cols:
                if row[value_col] in target_performance:
                    col_suffix = value_col.split(';')[-1]
                    study_id_col = [c for c in study_cols if c.endswith(col_suffix)]
                    if study_id_col:
                        study_id_value = row[study_id_col[0]]
                        if study_id_value in area_filtered_study_ids:  # Only include if it was already in area filter
                            performance_filtered_study_ids.add(study_id_value)
        
        selected_study_ids = list(performance_filtered_study_ids)
        st.write('selected_study_ids (filtered by 領域 and 目標性能): ', selected_study_ids)

    if selected_area and target_performance:
        sim_proj_info_list = st.session_state.sim_prj_info_list
        project_ids = sim_proj_info_list['project_id'].unique().tolist()
        phase_ids = sim_proj_info_list['phase_id'].unique().tolist()
        variation_ids = sim_proj_info_list['variation_id'].unique().tolist()
        destinations = sim_proj_info_list['destination'].unique().tolist()
        drivetrains = sim_proj_info_list['drivetrain'].unique().tolist()
        performance_lists= sql.getr_value_to_sim(project_ids,destinations,drivetrains,phase_ids,variation_ids,selected_area, target_performance)

        st.write('performance_lists: ', performance_lists)

        if performance_lists.empty:
            st.error('No Performance Lists.')
        else:
            selected_performance_1 = st.multiselect(
                '設計項目（大）',
                performance_lists['design_item_1'].unique(),
                key ='selected_perf1_unique_key',
                # default=dropdown_values[0] if len(dropdown_values) > 0 else []
            )

            # Filter design_item_2 based on selected_performance_1
            if selected_performance_1:
                filtered_performance_lists = performance_lists[performance_lists['design_item_1'].isin(selected_performance_1)]
                design_item_2_options = filtered_performance_lists['design_item_2'].unique()
            else:
                design_item_2_options = []

            selected_performance_2 = st.multiselect(
                '設計項目（小）',
                design_item_2_options,
                key ='selected_perf2_unique_key',
            )
                
            # st.rerun()
    # selected_performance_1 = st.multiselect(
    #     '設計項目（大）',
    #     dropdown_values,
    #     key ='selected_perf1_unique_key',
    #     default=dropdown_values[0] if len(dropdown_values) > 0 else []
    # )

    # if target_performance:
    #     sim_proj_info_list = st.session_state.sim_prj_info_list
    #     project_ids = sim_proj_info_list['project_id'].unique().tolist()
    #     phase_ids = sim_proj_info_list['phase_id'].unique().tolist()
    #     variation_ids = sim_proj_info_list['variation_id'].unique().tolist()
    #     destinations = sim_proj_info_list['destination'].unique().tolist()
    #     drivetrains = sim_proj_info_list['drivetrain'].unique().tolist()
    #     performance_list2 = sql.getr_value_to_sim(project_ids,destinations,drivetrains,phase_ids,variation_ids,selected_performance_1)

    #     # study_ids = st.session_state.sim_prj_info_list['study_id'].tolist()

    #     selected_performance_2 = st.multiselect(
    #         '設計項目（小）',
    #         # ["WLTC","WLTC2","WLTC3"],
    #         performance_list2,
    #         key ='selected_perf2_unique_key',
            
    #     )

    #     if st.button('実行',key='fixed_sim_button_key_1'):
    #         if selected_performance_1 and selected_performance_2:
    #             fixed_list = sql.get_sim_fix_list(project_ids,destinations,drivetrains,phase_ids,variation_ids,selected_performance_1,selected_performance_2)
    #             if fixed_list.empty:
    #                 st.error('No Fixed Data.')
    #             else:
    #                 st.session_state.fixed_sim_info = fixed_list
    #                 st.session_state['fix_sim_study_list'] = True
    #                 st.rerun()
    #         else:
    #             st.error('項目を選択してください。')
                

#12/01 チョー　確定ダイアログ
@st.dialog("設計値確定",width="large")
def choice_sim_fixed_bk4():
    # if 'sim_study_list' not in st.session_state:
    #     st.session_state['sim_study_list'] = []
    # study_ids = st.session_state.sim_prj_info_list['study_id'].tolist()

    # Assuming st.session_state.sim_data_stuck contains your DataFrame
    sim_data_stuck = st.session_state.sim_data_stuck
    # st.write('sim_data_stuck: ', sim_data_stuck)

    # Step 1: Get column lists
    senario_cols = [col for col in sim_data_stuck.columns if 'senario_parameter_id' in col]
    study_cols = [col for col in sim_data_stuck.columns if 'study_id' in col]
    value_cols = [col for col in sim_data_stuck.columns if ';value;' in col]
    
    # # Step 2: Find rows where parameter 96 exists (有効/無効列)
    # filtered_96 = sim_data_stuck[sim_data_stuck[senario_cols].apply(lambda row: 96 in row.values, axis=1)]
    
    # # Step 3: Get col_suffixes of columns that have '有効' for parameter 96
    # valid_col_suffixes = set()
    # valid_study_ids = set()
    # for idx, row in filtered_96.iterrows():
    #     for value_col in value_cols:
    #         if row[value_col] == '有効':
    #             col_suffix = value_col.split(';')[-1]
    #             valid_col_suffixes.add(col_suffix)
    #             # Also get study_id for this suffix
    #             study_id_col = [c for c in study_cols if c.endswith(col_suffix)]
    #             if study_id_col:
    #                 study_id_value = row[study_id_col[0]]
    #                 if study_id_value is not None and str(study_id_value) != 'nan' and str(study_id_value).strip() != '':
    #                     valid_study_ids.add(study_id_value)

    # Step 2: Find rows where parameter 96 exists (有効/無効列)
    filtered_96 = sim_data_stuck[sim_data_stuck[senario_cols].apply(lambda row: 96 in row.values, axis=1)]
    # Find rows where parameter 98 exists (FIXED check)
    filtered_98 = sim_data_stuck[sim_data_stuck[senario_cols].apply(lambda row: 98 in row.values, axis=1)]

    # Step 3: Get col_suffixes of columns that have '有効' for parameter 96 AND not 'FIXED' for parameter 98
    valid_col_suffixes = set()
    valid_study_ids = set()
    
    # First pass: collect col_suffixes where parameter 96 = '有効'
    col_suffixes_with_yukou = {}  # {col_suffix: study_id}
    for idx, row in filtered_96.iterrows():
        for value_col in value_cols:
            if row[value_col] == '有効':
                col_suffix = value_col.split(';')[-1]
                study_id_col = [c for c in study_cols if c.endswith(col_suffix)]
                if study_id_col:
                    study_id_value = row[study_id_col[0]]
                    if study_id_value is not None and str(study_id_value) != 'nan' and str(study_id_value).strip() != '':
                        col_suffixes_with_yukou[col_suffix] = study_id_value
    
    # Second pass: exclude col_suffixes where parameter 98 = 'FIXED'
    col_suffixes_with_fixed = set()
    for idx, row in filtered_98.iterrows():
        for value_col in value_cols:
            if row[value_col] == 'FIXED':
                col_suffix = value_col.split(';')[-1]
                col_suffixes_with_fixed.add(col_suffix)
    
    # Keep only col_suffixes that have '有効' but NOT 'FIXED'
    for col_suffix, study_id in col_suffixes_with_yukou.items():
        if col_suffix not in col_suffixes_with_fixed:
            valid_col_suffixes.add(col_suffix)
            valid_study_ids.add(study_id)
    
    # st.write('valid_study_ids (有効 and not FIXED): ', valid_study_ids)
    # st.write('valid_col_suffixes (有効 and not FIXED): ', valid_col_suffixes)
    
    # Step 4: Filter dataframe to only include columns with valid suffixes
    valid_columns = [col for col in sim_data_stuck.columns if col.split(';')[-1] in valid_col_suffixes]
    filtered_df = sim_data_stuck[valid_columns]
    # st.write('filtered_df (有効 only): ', filtered_df)
    
    # Get column lists from filtered dataframe
    filtered_senario_cols = [col for col in filtered_df.columns if 'senario_parameter_id' in col]
    filtered_study_cols = [col for col in filtered_df.columns if 'study_id' in col]
    filtered_value_cols = [col for col in filtered_df.columns if ';value;' in col]
    
    # # Helper function to get dropdown values from filtered dataframe
    # def get_dropdown_values(data, senario_id, senario_cols, value_cols):
    #     """Get dropdown values for a parameter from filtered dataframe"""
    #     filtered_rows = data[data[senario_cols].apply(lambda row: senario_id in row.values, axis=1)]
    #     values = set()
    #     for idx, row in filtered_rows.iterrows():
    #         for value_col in value_cols:
    #             values.add(row[value_col])
    #     return sorted(list(values))

    # Helper function to get dropdown values for a specific parameter from valid study_ids
    def get_dropdown_values(data, study_ids, senario_id):
        """Get dropdown values for a parameter, only from specified study_ids"""
        if not study_ids:
            return []
        
        # Find rows where the parameter exists
        senario_cols = [col for col in data.columns if 'senario_parameter_id' in col]
        study_cols = [col for col in data.columns if 'study_id' in col]
        value_cols = [col for col in data.columns if ';value;' in col]
        
        filtered_rows = data[data[senario_cols].apply(lambda row: senario_id in row.values, axis=1)]
        
        # Get values only from columns belonging to valid study_ids
        values = set()
        for idx, row in filtered_rows.iterrows():
            for value_col in value_cols:
                col_suffix = value_col.split(';')[-1]
                study_id_col = [c for c in study_cols if c.endswith(col_suffix)]
                if study_id_col and row[study_id_col[0]] in study_ids:
                    values.add(row[value_col])
        
        return sorted(list(values))
    
    # Get dropdown values for parameter 15 (性能領域) from filtered dataframe
    # dropdown_values_perf = get_dropdown_values(filtered_df, 15, filtered_senario_cols, filtered_value_cols)
    dropdown_values_perf = get_dropdown_values(filtered_df, valid_study_ids, 15)
    # st.write('dropdown_values_perf: ', dropdown_values_perf)

    selected_area = st.multiselect(
        '領域',
        dropdown_values_perf,
        key ='selected_area_unique_key',
        default=dropdown_values_perf[0] if len(dropdown_values_perf) > 0 else []
    )
    
    # Filter study_ids by selected_area (parameter 15)
    area_filtered_study_ids = valid_study_ids.copy()
    if selected_area:
        # Find which study_ids have the selected area values
        area_filtered_study_ids = set()
        filtered_15 = filtered_df[filtered_df[filtered_senario_cols].apply(lambda row: 15 in row.values, axis=1)]
        
        for idx, row in filtered_15.iterrows():
            for value_col in filtered_value_cols:
                if row[value_col] in selected_area:
                    col_suffix = value_col.split(';')[-1]
                    study_id_col = [c for c in filtered_study_cols if c.endswith(col_suffix)]
                    if study_id_col:
                        study_id_value = row[study_id_col[0]]
                        if study_id_value in valid_study_ids:
                            area_filtered_study_ids.add(study_id_value)
        
        # st.write('area_filtered_study_ids: ', area_filtered_study_ids)
        # dropdown_values = get_dropdown_values(filtered_df, 3, filtered_senario_cols, filtered_value_cols)
        dropdown_values = get_dropdown_values(filtered_df,area_filtered_study_ids, 3)
    else:
        dropdown_values = []
    
    # st.write('dropdown_values: ', dropdown_values)

    target_performance = st.multiselect(
        '目標性能',
        dropdown_values,
        key ='target_performance_unique_key',
        default=dropdown_values[0] if len(dropdown_values) > 0 else []
    )

    # Filter study_ids by target_performance (parameter 3)
    selected_study_ids = []
    if selected_area and target_performance:
        performance_filtered_study_ids = set()
        filtered_3 = filtered_df[filtered_df[filtered_senario_cols].apply(lambda row: 3 in row.values, axis=1)]
        
        for idx, row in filtered_3.iterrows():
            for value_col in filtered_value_cols:
                if row[value_col] in target_performance:
                    col_suffix = value_col.split(';')[-1]
                    study_id_col = [c for c in filtered_study_cols if c.endswith(col_suffix)]
                    if study_id_col:
                        study_id_value = row[study_id_col[0]]
                        if study_id_value in area_filtered_study_ids:  # Only include if it was already in area filter
                            performance_filtered_study_ids.add(study_id_value)
        
        selected_study_ids = list(performance_filtered_study_ids)
        # st.write('selected_study_ids (filtered by 領域 and 目標性能): ', selected_study_ids)

    if selected_area and target_performance:
        sim_proj_info_list = st.session_state.sim_prj_info_list
        # st.write('sim_proj_info_list: ', sim_proj_info_list)
        project_ids = sim_proj_info_list['project_id'].unique().tolist()
        phase_ids = sim_proj_info_list['phase_id'].unique().tolist()
        variation_ids = sim_proj_info_list['variation_id'].unique().tolist()
        destinations = sim_proj_info_list['destination'].unique().tolist()
        drivetrains = sim_proj_info_list['drivetrain'].unique().tolist()
        performance_lists= sql.getr_value_to_sim(project_ids,destinations,drivetrains,phase_ids,variation_ids,selected_area, target_performance)

        # st.write('performance_lists: ', performance_lists)

        if performance_lists.empty:
            st.error('No Performance Lists.')
        else:
            selected_performance_1 = st.multiselect(
                '設計項目（大）',
                performance_lists['design_item_1'].unique(),
                key ='selected_perf1_unique_key',
                # default=dropdown_values[0] if len(dropdown_values) > 0 else []
            )

            # Filter design_item_2 based on selected_performance_1
            if selected_performance_1:
                filtered_performance_lists = performance_lists[performance_lists['design_item_1'].isin(selected_performance_1)]
                design_item_2_options = filtered_performance_lists['design_item_2'].unique()
            else:
                design_item_2_options = []

            selected_performance_2 = st.multiselect(
                '設計項目（小）',
                design_item_2_options,
                key ='selected_perf2_unique_key',
            )

            if selected_performance_1 and selected_performance_2:
                # Filter performance_lists to get IDs where design_item_1 and design_item_2 match selections
                filtered_performance = performance_lists[
                    (performance_lists['design_item_1'].isin(selected_performance_1)) &
                    (performance_lists['design_item_2'].isin(selected_performance_2))
                ]
                selected_performance_ids = filtered_performance['id'].tolist()
                # st.write('selected_performance_ids: ', selected_performance_ids)
                # st.write('filtered_performance: ', filtered_performance)
                # find rflcategory column (not constant name)
                rfl_cols = [col for col in filtered_df.columns if 'rflcategory' in col.lower()]
                # st.write('rfl_cols: ', rfl_cols)
                if len(rfl_cols) > 1:
                    filtered_r_df = filtered_df[
                                        (filtered_df[rfl_cols] == 'R').any(axis=1)
                                    ]
                    # st.write('filtered_r_df: ', filtered_r_df)
                    all_dfs = []
                    for suffix in valid_col_suffixes:
                        # 1. get columns belonging to this suffix
                        cols = [
                            col for col in filtered_r_df.columns
                            if col.split(';')[-1] == suffix
                        ]
                        # 2. rename to middle part
                        rename_map = {col: col.split(';')[1] for col in cols}
                        # 3. build DF
                        df_suffix = filtered_r_df[cols].rename(columns=rename_map)
                        all_dfs.append(df_suffix)

                    # Combine vertically
                    combined_df = pd.concat(all_dfs, ignore_index=True)
                    cols_to_check = ['id', 'project_id', 'senario_parameter_id', 'phase_id', 'variation_id', 'study_id']
                    # Drop rows where all these columns are None/NaN
                    combined_df = combined_df.dropna(subset=cols_to_check, how='all').reset_index(drop=True)
                    # st.write('combined_df: ', combined_df)
                    
                    # Filter combined_df to only include rows where rfl_id is in selected_performance_ids
                    fixed_df = combined_df[combined_df['rflid'].isin(selected_performance_ids)].reset_index(drop=True)
                    
                    # Merge filtered_performance columns into fixed_df
                    performance_info = filtered_performance[['id', 'performance', 'design_item_1', 'design_item_2']].rename(columns={'id': 'rflid'})
                    fixed_df = fixed_df.merge(
                        performance_info, 
                        on='rflid', 
                        how='left',
                        suffixes=('', '_perf')
                    )
                    
                    # st.write('fixed_df (with performance details): ', fixed_df)

                    if not fixed_df.empty:
                        st.write('確認内容')
                        go = gop.fixed_sim()
                        st.session_state.Prj_updata = AgGrid(
                            fixed_df,
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
                                # update_sim_r_flag = sql.update_fixed_r_record(selected_rows)
                                # if update_sim_r_flag is True:
                                #     st.session_state.seupdate_sim_r_info = selected_rows
                                st.rerun()
                
            # st.rerun()
    # selected_performance_1 = st.multiselect(
    #     '設計項目（大）',
    #     dropdown_values,
    #     key ='selected_perf1_unique_key',
    #     default=dropdown_values[0] if len(dropdown_values) > 0 else []
    # )

    # if target_performance:
    #     sim_proj_info_list = st.session_state.sim_prj_info_list
    #     project_ids = sim_proj_info_list['project_id'].unique().tolist()
    #     phase_ids = sim_proj_info_list['phase_id'].unique().tolist()
    #     variation_ids = sim_proj_info_list['variation_id'].unique().tolist()
    #     destinations = sim_proj_info_list['destination'].unique().tolist()
    #     drivetrains = sim_proj_info_list['drivetrain'].unique().tolist()
    #     performance_list2 = sql.getr_value_to_sim(project_ids,destinations,drivetrains,phase_ids,variation_ids,selected_performance_1)

    #     # study_ids = st.session_state.sim_prj_info_list['study_id'].tolist()

    #     selected_performance_2 = st.multiselect(
    #         '設計項目（小）',
    #         # ["WLTC","WLTC2","WLTC3"],
    #         performance_list2,
    #         key ='selected_perf2_unique_key',
            
    #     )

    #     if st.button('実行',key='fixed_sim_button_key_1'):
    #         if selected_performance_1 and selected_performance_2:
    #             fixed_list = sql.get_sim_fix_list(project_ids,destinations,drivetrains,phase_ids,variation_ids,selected_performance_1,selected_performance_2)
    #             if fixed_list.empty:
    #                 st.error('No Fixed Data.')
    #             else:
    #                 st.session_state.fixed_sim_info = fixed_list
    #                 st.session_state['fix_sim_study_list'] = True
    #                 st.rerun()
    #         else:
    #             st.error('項目を選択してください。')
                

# #12/01 チョー　確定ダイアログ #correct version
# @st.dialog("設計値確定")
# def choice_sim_fixed():

#     # Assuming st.session_state.sim_data_stuck contains your DataFrame
#     sim_data_stuck = st.session_state.sim_data_stuck
#     # st.write('sim_data_stuck: ', sim_data_stuck)

#     # Step 1: Get column lists
#     senario_cols = [col for col in sim_data_stuck.columns if 'senario_parameter_id' in col]
#     study_cols = [col for col in sim_data_stuck.columns if 'study_id' in col]
#     value_cols = [col for col in sim_data_stuck.columns if ';value;' in col]

#     # Step 2: Find rows where parameter 96 exists (有効/無効列)
#     filtered_96 = sim_data_stuck[sim_data_stuck[senario_cols].apply(lambda row: 96 in row.values, axis=1)]
#     # Find rows where parameter 98 exists (FIXED check)
#     filtered_98 = sim_data_stuck[sim_data_stuck[senario_cols].apply(lambda row: 98 in row.values, axis=1)]

#     # Step 3: Get col_suffixes of columns that have '有効' for parameter 96 AND not 'FIXED' for parameter 98
#     valid_col_suffixes = set()
#     valid_study_ids = set()
    
#     # First pass: collect col_suffixes where parameter 96 = '有効'
#     col_suffixes_with_yukou = {}  # {col_suffix: study_id}
#     for idx, row in filtered_96.iterrows():
#         for value_col in value_cols:
#             if row[value_col] == '有効':
#                 col_suffix = value_col.split(';')[-1]
#                 study_id_col = [c for c in study_cols if c.endswith(col_suffix)]
#                 if study_id_col:
#                     study_id_value = row[study_id_col[0]]
#                     if study_id_value is not None and str(study_id_value) != 'nan' and str(study_id_value).strip() != '':
#                         col_suffixes_with_yukou[col_suffix] = study_id_value
    
#     # Second pass: exclude col_suffixes where parameter 98 = 'FIXED'
#     col_suffixes_with_fixed = set()
#     for idx, row in filtered_98.iterrows():
#         for value_col in value_cols:
#             if row[value_col] == 'FIXED':
#                 col_suffix = value_col.split(';')[-1]
#                 col_suffixes_with_fixed.add(col_suffix)
    
#     # Keep only col_suffixes that have '有効' but NOT 'FIXED'
#     for col_suffix, study_id in col_suffixes_with_yukou.items():
#         if col_suffix not in col_suffixes_with_fixed:
#             valid_col_suffixes.add(col_suffix)
#             valid_study_ids.add(study_id)
    
#     # Step 4: Filter dataframe to only include columns with valid suffixes
#     valid_columns = [col for col in sim_data_stuck.columns if col.split(';')[-1] in valid_col_suffixes]
#     filtered_df = sim_data_stuck[valid_columns]
#     # st.write('filtered_df (有効 only): ', filtered_df)
    
#     # Get column lists from filtered dataframe
#     filtered_senario_cols = [col for col in filtered_df.columns if 'senario_parameter_id' in col]
#     filtered_study_cols = [col for col in filtered_df.columns if 'study_id' in col]
#     filtered_value_cols = [col for col in filtered_df.columns if ';value;' in col]

#     # Helper function to get dropdown values for a specific parameter from valid study_ids
#     def get_dropdown_values(data, study_ids, senario_id):
#         """Get dropdown values for a parameter, only from specified study_ids"""
#         if not study_ids:
#             return []
        
#         # Find rows where the parameter exists
#         senario_cols = [col for col in data.columns if 'senario_parameter_id' in col]
#         study_cols = [col for col in data.columns if 'study_id' in col]
#         value_cols = [col for col in data.columns if ';value;' in col]
        
#         filtered_rows = data[data[senario_cols].apply(lambda row: senario_id in row.values, axis=1)]
        
#         # Get values only from columns belonging to valid study_ids
#         values = set()
#         for idx, row in filtered_rows.iterrows():
#             for value_col in value_cols:
#                 col_suffix = value_col.split(';')[-1]
#                 study_id_col = [c for c in study_cols if c.endswith(col_suffix)]
#                 if study_id_col and row[study_id_col[0]] in study_ids:
#                     values.add(row[value_col])
        
#         return sorted(list(values))
    
#     # Get dropdown values for parameter 15 (性能領域) from filtered dataframe
#     # dropdown_values_perf = get_dropdown_values(filtered_df, 15, filtered_senario_cols, filtered_value_cols)
#     dropdown_values_perf = get_dropdown_values(filtered_df, valid_study_ids, 15)
#     # st.write('dropdown_values_perf: ', dropdown_values_perf)

#     selected_area_single = st.selectbox(
#         '領域',
#         dropdown_values_perf,
#         key ='selected_area_unique_key',
#         index=0 if len(dropdown_values_perf) > 0 else None
#     )
#     # Convert to list to maintain same format as multiselect
#     selected_area = [selected_area_single] if selected_area_single else []
    
#     # Filter study_ids by selected_area (parameter 15)
#     area_filtered_study_ids = valid_study_ids.copy()
#     if selected_area:
#         # Find which study_ids have the selected area values
#         area_filtered_study_ids = set()
#         filtered_15 = filtered_df[filtered_df[filtered_senario_cols].apply(lambda row: 15 in row.values, axis=1)]
        
#         for idx, row in filtered_15.iterrows():
#             for value_col in filtered_value_cols:
#                 if row[value_col] in selected_area:
#                     col_suffix = value_col.split(';')[-1]
#                     study_id_col = [c for c in filtered_study_cols if c.endswith(col_suffix)]
#                     if study_id_col:
#                         study_id_value = row[study_id_col[0]]
#                         if study_id_value in valid_study_ids:
#                             area_filtered_study_ids.add(study_id_value)
        
#         # st.write('area_filtered_study_ids: ', area_filtered_study_ids)
#         # dropdown_values = get_dropdown_values(filtered_df, 3, filtered_senario_cols, filtered_value_cols)
#         dropdown_values = get_dropdown_values(filtered_df,area_filtered_study_ids, 3)
#     else:
#         dropdown_values = []
    
#     # st.write('dropdown_values: ', dropdown_values)

#     target_performance_single = st.selectbox(
#         '目標性能',
#         dropdown_values,
#         key ='target_performance_unique_key',
#         index=0 if len(dropdown_values) > 0 else None
#     )
#     # Convert to list to maintain same format as multiselect
#     target_performance = [target_performance_single] if target_performance_single else []

#     # # Filter study_ids by target_performance (parameter 3)
#     # selected_study_ids = []
#     # if selected_area and target_performance:
#     #     performance_filtered_study_ids = set()
#     #     filtered_3 = filtered_df[filtered_df[filtered_senario_cols].apply(lambda row: 3 in row.values, axis=1)]
        
#     #     for idx, row in filtered_3.iterrows():
#     #         for value_col in filtered_value_cols:
#     #             if row[value_col] in target_performance:
#     #                 col_suffix = value_col.split(';')[-1]
#     #                 study_id_col = [c for c in filtered_study_cols if c.endswith(col_suffix)]
#     #                 if study_id_col:
#     #                     study_id_value = row[study_id_col[0]]
#     #                     if study_id_value in area_filtered_study_ids:  # Only include if it was already in area filter
#     #                         performance_filtered_study_ids.add(study_id_value)
        
#     #     selected_study_ids = list(performance_filtered_study_ids)
#         # st.write('selected_study_ids (filtered by 領域 and 目標性能): ', selected_study_ids)

#     if selected_area and target_performance:
#         sim_proj_info_list = st.session_state.sim_prj_info_list
#         # st.write('sim_proj_info_list: ', sim_proj_info_list)
#         project_ids = sim_proj_info_list['project_id'].unique().tolist()
#         phase_ids = sim_proj_info_list['phase_id'].unique().tolist()
#         variation_ids = sim_proj_info_list['variation_id'].unique().tolist()
#         destinations = sim_proj_info_list['destination'].unique().tolist()
#         drivetrains = sim_proj_info_list['drivetrain'].unique().tolist()
#         performance_lists= sql.getr_value_to_sim(project_ids,destinations,drivetrains,phase_ids,variation_ids,selected_area, target_performance)

#         # st.write('performance_lists: ', performance_lists)

#         if performance_lists.empty:
#             st.error('No Performance Lists.')
#         else:
#             design_item_1_options = performance_lists['design_item_1'].unique().tolist()
#             selected_performance_1_single = st.selectbox(
#                 '設計項目（大）',
#                 design_item_1_options,
#                 key ='selected_perf1_unique_key',
#                 index=0 if len(design_item_1_options) > 0 else None
#             )
#             # Convert to list to maintain same format as multiselect
#             selected_performance_1 = [selected_performance_1_single] if selected_performance_1_single else []

#             # Filter design_item_2 based on selected_performance_1
#             if selected_performance_1:
#                 filtered_performance_lists = performance_lists[performance_lists['design_item_1'].isin(selected_performance_1)]
#                 design_item_2_options = filtered_performance_lists['design_item_2'].unique().tolist()
#             else:
#                 design_item_2_options = []

#             selected_performance_2_single = st.selectbox(
#                 '設計項目（小）',
#                 design_item_2_options,
#                 key ='selected_perf2_unique_key',
#                 index=0 if len(design_item_2_options) > 0 else None
#             )
#             # Convert to list to maintain same format as multiselect
#             selected_performance_2 = [selected_performance_2_single] if selected_performance_2_single else []

#             if selected_performance_1 and selected_performance_2:
#                 # Filter performance_lists to get IDs where design_item_1 and design_item_2 match selections
#                 filtered_performance = performance_lists[
#                     (performance_lists['design_item_1'].isin(selected_performance_1)) &
#                     (performance_lists['design_item_2'].isin(selected_performance_2))
#                 ]
#                 selected_performance_ids = filtered_performance['id'].tolist()
#                 # st.write('selected_performance_ids: ', selected_performance_ids)
#                 # st.write('filtered_performance: ', filtered_performance)
#                 # find rflcategory column (not constant name)
#                 rfl_cols = [col for col in filtered_df.columns if 'rflcategory' in col.lower()]
#                 # st.write('rfl_cols: ', rfl_cols)
#                 if len(rfl_cols) > 1:
#                     filtered_r_df = filtered_df[
#                                         (filtered_df[rfl_cols] == 'R').any(axis=1)
#                                     ]
#                     # st.write('filtered_r_df: ', filtered_r_df)
#                     all_dfs = []
#                     for suffix in valid_col_suffixes:
#                         # 1. get columns belonging to this suffix
#                         cols = [
#                             col for col in filtered_r_df.columns
#                             if col.split(';')[-1] == suffix
#                         ]
#                         # 2. rename to middle part
#                         rename_map = {col: col.split(';')[1] for col in cols}
#                         # 3. build DF
#                         df_suffix = filtered_r_df[cols].rename(columns=rename_map)
#                         all_dfs.append(df_suffix)

#                     # Combine vertically
#                     combined_df = pd.concat(all_dfs, ignore_index=True)
#                     cols_to_check = ['id', 'project_id', 'senario_parameter_id', 'phase_id', 'variation_id', 'study_id']
#                     # Drop rows where all these columns are None/NaN
#                     combined_df = combined_df.dropna(subset=cols_to_check, how='all').reset_index(drop=True)
#                     # st.write('combined_df: ', combined_df)
                    
#                     # Filter combined_df to only include rows where rfl_id is in selected_performance_ids
#                     fixed_df = combined_df[combined_df['rflid'].isin(selected_performance_ids)].reset_index(drop=True)
                    
#                     # Merge filtered_performance columns into fixed_df
#                     performance_info = filtered_performance[['id', 'performance', 'design_item_1', 'design_item_2']].rename(columns={'id': 'rflid'})
#                     fixed_df = fixed_df.merge(
#                         performance_info, 
#                         on='rflid', 
#                         how='left',
#                         suffixes=('', '_perf')
#                     )
                    
#                     if not fixed_df.empty:
#                         # st.write('確認内容')
#                         # st.markdown(f'領域：{selected_area[0]}  設計項目（大）：{selected_performance_1[0]}  設計項目（小）：{selected_performance_2[0]}')
#                         # st.markdown(
#                         #     "### **確認内容**  \n"
#                         #     f"領域：{selected_area[0]}  \n"
#                         #     f"設計項目（大）：{selected_performance_1[0]}  \n"
#                         #     f"設計項目（小）：{selected_performance_2[0]}"
#                         # )
#                         st.markdown(
#                             "<h3>確認内容</h3>"
#                             f"&emsp;領域：{selected_area[0]}<br>"
#                             f"&emsp;設計項目（大）：{selected_performance_1[0]}<br>"
#                             f"&emsp;設計項目（小）：{selected_performance_2[0]}<br>",
#                             unsafe_allow_html=True
#                         )

#                         go = gop.fixed_sim()
#                         st.session_state.Prj_updata = AgGrid(
#                             fixed_df,
#                             custom_css=css_ag,
#                             gridOptions=go,
#                             reload_data=False,
#                             height=220,
#                         )

#                         if st.button("実行",key='fixed_sim_button_key_2'):
#                             selected_rows = st.session_state.Prj_updata['selected_rows']
#                             # st.write('selected_rows: ', selected_rows)
#                             if selected_rows is None:
#                                 st.error('FIXEDする項目を選択してください。')
#                             elif len(selected_rows) > 1:
#                                 st.error('1行しかFIXEDできません。')
#                             elif selected_rows is not None:
#                                 update_sim_r_flag = sql.update_fixed_r_record(selected_rows)
#                                 if update_sim_r_flag is True:
#                                     st.session_state.sim_fixed_update = True
#                                     # st.session_state.edit_refresh = True
#                                     execute_sim_list(True)
#                                     # st.rerun()
#                                 # st.write('you click button.')


# @st.dialog("設計値確定")
# def choice_sim_fixed():

#     # ============================================================
#     #  Helper Functions
#     # ============================================================

#     def extract_suffix(col_name: str) -> str:
#         """Return the last ';'-separated suffix."""
#         return col_name.split(';')[-1] #eg:14;column name is: senario_parameter_id;P1提案仕様251117test → P1提案仕様251117test


#     def get_matching_columns(columns, suffix):
#         """Return all columns whose suffix matches the given suffix."""
#         return [c for c in columns if c.endswith(suffix)]

#     def collect_valid_suffixes(df, senario_cols, study_cols, value_cols):
#         """
#         Determine valid study suffixes:
#           - parameter 96 must be '有効'
#           - parameter 98 must NOT be 'FIXED'
#         Returns:
#             valid_suffixes (set)
#             valid_study_ids (set)
#         """
#         # Rows containing parameter 96 & 98
#         rows_param96 = df[df[senario_cols].apply(lambda r: 96 in r.values, axis=1)]
#         rows_param98 = df[df[senario_cols].apply(lambda r: 98 in r.values, axis=1)]

#         suffix_yukou = {}   # suffix -> study_id
#         suffix_fixed = set()

#         # Collect "有効"
#         for _, row in rows_param96.iterrows():
#             for vcol in value_cols:
#                 if row[vcol] == "有効":
#                     suffix = extract_suffix(vcol)
#                     study_col = [c for c in study_cols if c.endswith(suffix)]
#                     if study_col:
#                         sid = row[study_col[0]]
#                         if sid and str(sid).strip() not in ("", "nan"):
#                             suffix_yukou[suffix] = sid

#         # Collect "FIXED"
#         for _, row in rows_param98.iterrows():
#             for vcol in value_cols:
#                 if row[vcol] == "FIXED":
#                     suffix_fixed.add(extract_suffix(vcol))

#         # Valid suffixes = 有効 but not FIXED
#         valid_suffixes = {s for s in suffix_yukou if s not in suffix_fixed}
#         valid_study_ids = {suffix_yukou[s] for s in valid_suffixes}

#         return valid_suffixes, valid_study_ids

#     def filter_df_by_suffixes(df, suffixes):
#         """Keep only columns whose suffix is in the given suffix set."""
#         valid_cols = [c for c in df.columns if extract_suffix(c) in suffixes]
#         return df[valid_cols]

#     def get_dropdown_values(df, study_ids, senario_id):
#         """
#         Returns sorted dropdown values for the given senario_id,
#         using only rows belonging to the given study_ids.
#         """
#         if not study_ids:
#             return []

#         senario_cols = [c for c in df.columns if "senario_parameter_id" in c]
#         study_cols = [c for c in df.columns if "study_id" in c]
#         value_cols = [c for c in df.columns if ";value;" in c]

#         # Filter rows having the target senario_id
#         rows = df[df[senario_cols].apply(lambda r: senario_id in r.values, axis=1)]

#         values = set()
#         for _, row in rows.iterrows():
#             for vcol in value_cols:
#                 suffix = extract_suffix(vcol)
#                 study_col = get_matching_columns(study_cols, suffix)
#                 if study_col and row[study_col[0]] in study_ids:
#                     values.add(row[vcol])

#         return sorted(values)

#     def filter_study_ids_by_value(df, study_ids, senario_id, selected_value):
#         """Return study_ids that have the selected_value under given senario_id."""
#         if not selected_value:
#             return set()

#         senario_cols = [c for c in df.columns if "senario_parameter_id" in c]
#         study_cols = [c for c in df.columns if "study_id" in c]
#         value_cols = [c for c in df.columns if ";value;" in c]

#         rows = df[df[senario_cols].apply(lambda r: senario_id in r.values, axis=1)]

#         result_ids = set()
#         for _, row in rows.iterrows():
#             for vcol in value_cols:
#                 if row[vcol] == selected_value:
#                     suffix = extract_suffix(vcol)
#                     study_col = get_matching_columns(study_cols, suffix)
#                     if study_col:
#                         sid = row[study_col[0]]
#                         if sid in study_ids:
#                             result_ids.add(sid)

#         return result_ids

#     # ============================================================
#     #  1) Load Data
#     # ============================================================

#     df = st.session_state.sim_data_stuck

#     senario_cols = [c for c in df.columns if "senario_parameter_id" in c]
#     study_cols   = [c for c in df.columns if "study_id" in c]
#     value_cols   = [c for c in df.columns if ";value;" in c]

#     # Determine valid suffixes / study_ids
#     valid_suffixes, valid_study_ids = collect_valid_suffixes(df, senario_cols, study_cols, value_cols)
#     st.write('valid_suffixes: ', valid_suffixes)
#     st.write('valid_study_ids: ', valid_study_ids)
#     # Restrict DF to only valid suffixes
#     filtered_df = filter_df_by_suffixes(df, valid_suffixes)

#     # # Recompute column lists for filtered DF
#     # f_senario_cols = [c for c in filtered_df.columns if "senario_parameter_id" in c]
#     # f_study_cols   = [c for c in filtered_df.columns if "study_id" in c]
#     # f_value_cols   = [c for c in filtered_df.columns if ";value;" in c]

#     # ============================================================
#     #  2) Dropdown: Performance Area (senario_id = 15)
#     # ============================================================

#     area_values = get_dropdown_values(filtered_df, valid_study_ids, senario_id=15)

#     selected_area = st.selectbox(
#         "領域",
#         area_values,
#         key="selected_area_unique_key",
#         index=0 if area_values else None
#     )

#     selected_area = [selected_area] if selected_area else []

#     # ============================================================
#     #  3) Dropdown: Target Performance (senario_id = 3)
#     # ============================================================

#     if selected_area:
#         area_filtered_ids = filter_study_ids_by_value(
#             filtered_df,
#             valid_study_ids,
#             senario_id=15,
#             selected_value=selected_area[0]
#         )

#         target_perf_values = get_dropdown_values(
#             filtered_df, area_filtered_ids, senario_id=3
#         )
#     else:
#         area_filtered_ids = set()
#         target_perf_values = []

#     selected_target_perf = st.selectbox(
#         "目標性能",
#         target_perf_values,
#         key="target_performance_unique_key",
#         index=0 if target_perf_values else None
#     )

#     selected_target_perf = [selected_target_perf] if selected_target_perf else []

#     # ============================================================
#     #  4) Performance List → Design Item Selection
#     # ============================================================

#     if selected_area and selected_target_perf:

#         info_list = st.session_state.sim_prj_info_list

#         project_ids = info_list["project_id"].unique().tolist()
#         phase_ids   = info_list["phase_id"].unique().tolist()
#         variation_ids = info_list["variation_id"].unique().tolist()
#         destinations = info_list["destination"].unique().tolist()
#         drivetrains  = info_list["drivetrain"].unique().tolist()

#         performance_lists = sql.getr_value_to_sim(
#             project_ids,
#             destinations,
#             drivetrains,
#             phase_ids,
#             variation_ids,
#             selected_area,
#             selected_target_perf
#         )

#         if performance_lists.empty:
#             st.error("対象するRリスト情報はありません.")
#             return

#         # Select Design Item 1
#         item1_opts = performance_lists["design_item_1"].unique().tolist()
#         selected_item1 = st.selectbox(
#             "設計項目（大）",
#             item1_opts,
#             key="selected_perf1_unique_key",
#             index=0 if item1_opts else None
#         )
#         selected_item1 = [selected_item1] if selected_item1 else []

#         # Select Design Item 2
#         if selected_item1:
#             pl_filtered = performance_lists[
#                 performance_lists["design_item_1"].isin(selected_item1)
#             ]
#             item2_opts = pl_filtered["design_item_2"].unique().tolist()
#         else:
#             pl_filtered = performance_lists
#             item2_opts = []

#         selected_item2 = st.selectbox(
#             "設計項目（小）",
#             item2_opts,
#             key="selected_perf2_unique_key",
#             index=0 if item2_opts else None
#         )
#         selected_item2 = [selected_item2] if selected_item2 else []

#         # ============================================================
#         #  5) Create FIXED Candidate Table
#         # ============================================================

#         if selected_item1 and selected_item2:

#             selected_ids = pl_filtered[
#                 pl_filtered["design_item_2"].isin(selected_item2)
#             ]["id"].tolist()

#             # Identify rflcategory columns
#             rfl_cols = [c for c in filtered_df.columns if "rflcategory" in c.lower()]

#             if len(rfl_cols) > 1:
#                 # Keep only rows where any rflcategory == 'R'
#                 df_R = filtered_df[(filtered_df[rfl_cols] == "R").any(axis=1)]

#                 # Build combined dataframe
#                 combined_list = []
#                 for suffix in valid_suffixes:
#                     cols = [c for c in df_R.columns if extract_suffix(c) == suffix]
#                     rename_map = {c: c.split(";")[1] for c in cols}
#                     combined_list.append(df_R[cols].rename(columns=rename_map))

#                 combined_df = pd.concat(combined_list, ignore_index=True)

#                 # Remove rows where key identifiers are all null
#                 key_cols = [
#                     "id", "project_id", "senario_parameter_id",
#                     "phase_id", "variation_id", "study_id"
#                 ]
#                 combined_df = combined_df.dropna(
#                     subset=key_cols, how="all"
#                 ).reset_index(drop=True)

#                 # Keep rows where rflid matches selected performance ids
#                 fixed_df = combined_df[combined_df["rflid"].isin(selected_ids)]

#                 # Merge in performance metadata
#                 perf_info = pl_filtered[
#                     ["id", "performance", "design_item_1", "design_item_2"]
#                 ].rename(columns={"id": "rflid"})

#                 fixed_df = fixed_df.merge(perf_info, on="rflid", how="left")

#                 if not fixed_df.empty:

#                     # Display confirmation section
#                     st.markdown(
#                         "<h3>確認内容</h3>"
#                         f"&emsp;領域：{selected_area[0]}<br>"
#                         f"&emsp;設計項目（大）：{selected_item1[0]}<br>"
#                         f"&emsp;設計項目（小）：{selected_item2[0]}<br>",
#                         unsafe_allow_html=True
#                     )

#                     go = gop.fixed_sim()
#                     st.session_state.Prj_updata = AgGrid(
#                         fixed_df,
#                         custom_css=css_ag,
#                         gridOptions=go,
#                         reload_data=False,
#                         height=220,
#                     )

#                     # Execute FIXED
#                     if st.button("実行", key="fixed_sim_button_key_2"):
#                         selected_rows = st.session_state.Prj_updata["selected_rows"]

#                         if not selected_rows:
#                             st.error("FIXEDする項目を選択してください。")
#                         elif len(selected_rows) > 1:
#                             st.error("1行しかFIXEDできません。")
#                         else:
#                             ok = sql.update_fixed_r_record(selected_rows)
#                             if ok:
#                                 # st.session_state.sim_fixed_update = True
#                                 execute_sim_list(True)


@st.dialog("設計値確定") #correct ver clean
def choice_sim_fixed_bk6():
    # ============================================================
    #  Helper Functions
    # ============================================================

    def extract_suffix(col_name: str) -> str:
        """Return the last ';'-separated suffix.
        Example: '14;senario_parameter_id;P1提案仕様251117test' -> 'P1提案仕様251117test'
        """
        return col_name.split(";")[-1]

    def get_matching_columns(columns, suffix):
        """Return all columns whose suffix matches the given suffix."""
        return [c for c in columns if c.endswith(suffix)]

    def collect_valid_suffixes(df, senario_cols, study_cols, value_cols):
        """
        Determine valid study suffixes:
          - parameter 96 must be '有効'
          - parameter 98 must NOT be 'FIXED'
        Returns:
            valid_suffixes (set)
            valid_study_ids (set)
        """
        # Filter rows containing parameter 96 & 98
        rows_param96 = df[df[senario_cols].apply(lambda r: 96 in r.values, axis=1)]
        rows_param98 = df[df[senario_cols].apply(lambda r: 98 in r.values, axis=1)]

        suffix_yukou = {}   # suffix -> study_id
        suffix_fixed = set() # suffixes marked FIXED

        # Collect "有効" study_ids for parameter 96
        for _, row in rows_param96.iterrows():
            for vcol in value_cols:
                if row[vcol] == "有効":
                    suffix = extract_suffix(vcol)
                    study_col = get_matching_columns(study_cols, suffix)
                    if study_col:
                        sid = row[study_col[0]]
                        if sid and str(sid).strip() not in ("", "nan"):
                            suffix_yukou[suffix] = sid

        # Collect "FIXED" suffixes for parameter 98
        for _, row in rows_param98.iterrows():
            for vcol in value_cols:
                if row[vcol] == "FIXED":
                    suffix_fixed.add(extract_suffix(vcol))

        # Only keep suffixes that are 有効 but NOT FIXED
        valid_suffixes = {s for s in suffix_yukou if s not in suffix_fixed}
        valid_study_ids = {suffix_yukou[s] for s in valid_suffixes}

        return valid_suffixes, valid_study_ids

    def filter_df_by_suffixes(df, suffixes):
        """Keep only columns whose suffix is in the given suffix set."""
        valid_cols = [c for c in df.columns if extract_suffix(c) in suffixes]
        return df[valid_cols]

    def get_dropdown_values(df, study_ids, senario_id):
        """Return sorted dropdown values for a parameter from valid study_ids."""
        if not study_ids:
            return []

        senario_cols = [c for c in df.columns if "senario_parameter_id" in c]
        study_cols = [c for c in df.columns if "study_id" in c]
        value_cols = [c for c in df.columns if ";value;" in c]

        # Filter rows having the target senario_id
        rows = df[df[senario_cols].apply(lambda r: senario_id in r.values, axis=1)]

        values = set()
        for _, row in rows.iterrows():
            for vcol in value_cols:
                suffix = extract_suffix(vcol)
                study_col = get_matching_columns(study_cols, suffix)
                if study_col and row[study_col[0]] in study_ids:
                    values.add(row[vcol])

        return sorted(values)

    def filter_study_ids_by_value(df, study_ids, senario_id, selected_value):
        """Return study_ids that have the selected_value under given senario_id."""
        if not selected_value:
            return set()

        senario_cols = [c for c in df.columns if "senario_parameter_id" in c]
        study_cols = [c for c in df.columns if "study_id" in c]
        value_cols = [c for c in df.columns if ";value;" in c]

        rows = df[df[senario_cols].apply(lambda r: senario_id in r.values, axis=1)]

        result_ids = set()
        for _, row in rows.iterrows():
            for vcol in value_cols:
                if row[vcol] == selected_value:
                    suffix = extract_suffix(vcol)
                    study_col = get_matching_columns(study_cols, suffix)
                    if study_col:
                        sid = row[study_col[0]]
                        if sid in study_ids:
                            result_ids.add(sid)

        return result_ids

    # ============================================================
    #  1) Load Data
    # ============================================================

    df = st.session_state.sim_data_stuck
    if df.empty:
        st.error("選択されたSIMリスト情報はありません。")
        return

    senario_cols = [c for c in df.columns if "senario_parameter_id" in c]
    study_cols   = [c for c in df.columns if "study_id" in c]
    value_cols   = [c for c in df.columns if ";value;" in c]

    # Determine valid suffixes / study_ids
    valid_suffixes, valid_study_ids = collect_valid_suffixes(df, senario_cols, study_cols, value_cols)
    if not valid_suffixes:
        st.error("有効かつ未FIXEDの項目が見つかりません。")
        return

    # Restrict DF to only valid suffixes
    filtered_df = filter_df_by_suffixes(df, valid_suffixes)
    if filtered_df.empty:
        # st.error("Filtered dataframe is empty after applying valid suffixes.")
        st.error("有効かつ未FIXEDの項目が見つかりません。")
        return

    # ============================================================
    #  2) Dropdown: Performance Area (senario_id = 15)
    # ============================================================

    area_values = get_dropdown_values(filtered_df, valid_study_ids, senario_id=15)
    if not area_values:
        # st.error("No Performance Area (領域) options available.")
        st.error("有効かつ未FIXEDの領域の項目が見つかりません。")
        return

    selected_area = st.selectbox(
        "領域",
        area_values,
        key="selected_area_unique_key",
        index=0 if area_values else None
    )
    selected_area = [selected_area] if selected_area else []

    # ============================================================
    #  3) Dropdown: Target Performance (senario_id = 3)
    # ============================================================

    if selected_area:
        area_filtered_ids = filter_study_ids_by_value(
            filtered_df,
            valid_study_ids,
            senario_id=15,
            selected_value=selected_area[0]
        )
        st.write('area_filtered_ids: ', area_filtered_ids)

        target_perf_values = get_dropdown_values(
            filtered_df, area_filtered_ids, senario_id=3
        )
        if not target_perf_values:
            st.error("選択された領域に対して有効かつ未FIXEDの目標性能の項目が見つかりません。")
            return
    else:
        st.error("No area selected. Cannot determine target performance.")
        return

    selected_target_perf = st.selectbox(
        "目標性能",
        target_perf_values,
        key="target_performance_unique_key",
        index=0 if target_perf_values else None
    )
    selected_target_perf = [selected_target_perf] if selected_target_perf else []

    # ============================================================
    #  4) Performance List → Design Item Selection
    # ============================================================

    if not selected_area or not selected_target_perf:
        st.error("領域と目標性能を選択してください。")
        return

    info_list = st.session_state.sim_prj_info_list
    if info_list.empty:
        st.error("SIMリストの対象Meta情報はありません。")
        return

    project_ids = info_list["project_id"].unique().tolist()
    phase_ids   = info_list["phase_id"].unique().tolist()
    variation_ids = info_list["variation_id"].unique().tolist()
    destinations = info_list["destination"].unique().tolist()
    drivetrains  = info_list["drivetrain"].unique().tolist()

    performance_lists = sql.getr_value_to_sim(
        project_ids,
        destinations,
        drivetrains,
        phase_ids,
        variation_ids,
        selected_area,
        selected_target_perf
    )
    if performance_lists.empty:
        st.error("対象するRリスト情報はありません.")
        return

    # Design Item 1
    item1_opts = performance_lists["design_item_1"].unique().tolist()
    if not item1_opts:
        st.error("設計項目（大）の項目が見つかりません。")
        return
    selected_item1 = st.selectbox(
        "設計項目（大）",
        item1_opts,
        key="selected_perf1_unique_key",
        index=0
    )
    selected_item1 = [selected_item1] if selected_item1 else []

    # Design Item 2
    pl_filtered = performance_lists[performance_lists["design_item_1"].isin(selected_item1)]
    item2_opts = pl_filtered["design_item_2"].unique().tolist()
    if not item2_opts:
        st.error("設計項目（小）の項目が見つかりません。")
        return
    selected_item2 = st.selectbox(
        "設計項目（小）",
        item2_opts,
        key="selected_perf2_unique_key",
        index=0
    )
    selected_item2 = [selected_item2] if selected_item2 else []

    # ============================================================
    #  5) Create FIXED Candidate Table
    # ============================================================

    selected_ids = pl_filtered[pl_filtered["design_item_2"].isin(selected_item2)]["id"].tolist()
    st.write('selected_ids: ', selected_ids)
    if not selected_ids:
        st.error("No matching performance IDs found for selected design items.")
        return

    rfl_cols = [c for c in filtered_df.columns if "rflcategory" in c.lower()]
    st.write('rfl_cols: ', rfl_cols)
    if len(rfl_cols) < 1:
        st.error("RFL Category columns are missing or insufficient.")
        return

    # Keep only rows where any rflcategory == 'R'
    df_R = filtered_df[(filtered_df[rfl_cols] == "R").any(axis=1)]
    st.write('df_R: ', df_R)
    if df_R.empty:
        st.error("No rows with rflcategory == 'R'.")
        return

    # Build combined dataframe
    combined_list = []
    for suffix in valid_suffixes:
        cols = [c for c in df_R.columns if extract_suffix(c) == suffix]
        rename_map = {c: c.split(";")[1] for c in cols}
        combined_list.append(df_R[cols].rename(columns=rename_map))
    combined_df = pd.concat(combined_list, ignore_index=True)

    key_cols = ["id", "project_id", "senario_parameter_id", "phase_id", "variation_id", "study_id"]
    combined_df = combined_df.dropna(subset=key_cols, how="all").reset_index(drop=True)
    if combined_df.empty:
        st.error("Combined dataframe is empty after dropping rows without key identifiers.")
        return

    # Filter by selected performance IDs
    fixed_df = combined_df[combined_df["rflid"].isin(selected_ids)]
    if fixed_df.empty:
        st.error("No FIXED candidates found for the selected performance IDs.")
        return

    # Merge performance metadata
    perf_info = pl_filtered[["id", "performance", "design_item_1", "design_item_2"]].rename(columns={"id": "rflid"})
    fixed_df = fixed_df.merge(perf_info, on="rflid", how="left")

    # Display confirmation
    st.markdown(
        "<h3>確認内容</h3>"
        f"&emsp;領域：{selected_area[0]}<br>"
        f"&emsp;設計項目（大）：{selected_item1[0]}<br>"
        f"&emsp;設計項目（小）：{selected_item2[0]}<br>",
        unsafe_allow_html=True
    )

    # Display FIXED table
    go = gop.fixed_sim()
    st.session_state.Prj_updata = AgGrid(
        fixed_df,
        custom_css=css_ag,
        gridOptions=go,
        reload_data=False,
        height=220,
    )

    # Execute FIXED
    if st.button("実行", key="fixed_sim_button_key_2"):
        selected_rows = st.session_state.Prj_updata["selected_rows"]
        # if not selected_rows:
        if selected_rows is None or selected_rows.empty:
            st.error("FIXEDする項目を選択してください。")
        elif len(selected_rows) > 1:
            st.error("1行しかFIXEDできません。")
        else:
            ok = sql.update_fixed_r_record(selected_rows)
            if ok:
                execute_sim_list(True)
            else:
                st.error("Failed to update FIXED record.")


@st.dialog("設計値確定") #correct ver 12/05
def choice_sim_fixed_bk7():
    # ============================================================
    #  Helper Functions
    # ============================================================

    def extract_suffix(col_name: str) -> str:
        """Return the last ';'-separated suffix.
        Example: '14;senario_parameter_id;P1提案仕様251117test' -> 'P1提案仕様251117test'
        """
        return col_name.split(";")[-1]

    def get_matching_columns(columns, suffix):
        """Return all columns whose suffix matches the given suffix."""
        return [c for c in columns if c.endswith(suffix)]

    def collect_valid_suffixes(df, senario_cols, study_cols, value_cols):
        """
        Determine valid study suffixes:
          - parameter 96 must be '有効'
          - parameter 98 must NOT be 'FIXED'
        Returns:
            valid_suffixes (set)
            valid_study_ids (set)
        """
        # Filter rows containing parameter 96 & 98
        rows_param96 = df[df[senario_cols].apply(lambda r: 96 in r.values, axis=1)]
        rows_param98 = df[df[senario_cols].apply(lambda r: 98 in r.values, axis=1)]

        suffix_yukou = {}   # suffix -> study_id
        suffix_fixed = set() # suffixes marked FIXED

        # Collect "有効" study_ids for parameter 96
        for _, row in rows_param96.iterrows():
            for vcol in value_cols:
                if row[vcol] == "有効":
                    suffix = extract_suffix(vcol)
                    study_col = get_matching_columns(study_cols, suffix)
                    if study_col:
                        sid = row[study_col[0]]
                        if sid and str(sid).strip() not in ("", "nan"):
                            suffix_yukou[suffix] = sid

        # Collect "FIXED" suffixes for parameter 98
        for _, row in rows_param98.iterrows():
            for vcol in value_cols:
                if row[vcol] == "FIXED":
                    suffix_fixed.add(extract_suffix(vcol))

        # Only keep suffixes that are 有効 but NOT FIXED
        valid_suffixes = {s for s in suffix_yukou if s not in suffix_fixed}
        valid_study_ids = {suffix_yukou[s] for s in valid_suffixes}

        return valid_suffixes, valid_study_ids

    def filter_df_by_suffixes(df, suffixes):
        """Keep only columns whose suffix is in the given suffix set."""
        valid_cols = [c for c in df.columns if extract_suffix(c) in suffixes]
        return df[valid_cols]

    def get_dropdown_values(df, study_ids, senario_id):
        """Return sorted dropdown values for a parameter from valid study_ids."""
        if not study_ids:
            return []

        senario_cols = [c for c in df.columns if "senario_parameter_id" in c]
        study_cols = [c for c in df.columns if "study_id" in c]
        value_cols = [c for c in df.columns if ";value;" in c]

        # Filter rows having the target senario_id
        rows = df[df[senario_cols].apply(lambda r: senario_id in r.values, axis=1)]

        values = set()
        for _, row in rows.iterrows():
            for vcol in value_cols:
                suffix = extract_suffix(vcol)
                study_col = get_matching_columns(study_cols, suffix)
                if study_col and row[study_col[0]] in study_ids:
                    values.add(row[vcol])

        return sorted(values)

    def filter_study_ids_by_value(df, study_ids, senario_id, selected_value):
        """Return study_ids that have the selected_value under given senario_id."""
        if not selected_value:
            return set()

        senario_cols = [c for c in df.columns if "senario_parameter_id" in c]
        study_cols = [c for c in df.columns if "study_id" in c]
        value_cols = [c for c in df.columns if ";value;" in c]

        rows = df[df[senario_cols].apply(lambda r: senario_id in r.values, axis=1)]

        result_ids = set()
        for _, row in rows.iterrows():
            for vcol in value_cols:
                if row[vcol] == selected_value:
                    suffix = extract_suffix(vcol)
                    study_col = get_matching_columns(study_cols, suffix)
                    if study_col:
                        sid = row[study_col[0]]
                        if sid in study_ids:
                            result_ids.add(sid)

        return result_ids

    # ============================================================
    #  1) Load Data
    # ============================================================

    df = st.session_state.sim_data_stuck
    if df.empty:
        st.error("選択されたSIMリスト情報はありません。")
        return

    senario_cols = [c for c in df.columns if "senario_parameter_id" in c]
    study_cols   = [c for c in df.columns if "study_id" in c]
    value_cols   = [c for c in df.columns if ";value;" in c]

    # Determine valid suffixes / study_ids
    valid_suffixes, valid_study_ids = collect_valid_suffixes(df, senario_cols, study_cols, value_cols)
    if not valid_suffixes:
        st.error("有効かつ未FIXEDの項目が見つかりません。")
        return

    # Restrict DF to only valid suffixes
    filtered_df = filter_df_by_suffixes(df, valid_suffixes)
    if filtered_df.empty:
        # st.error("Filtered dataframe is empty after applying valid suffixes.")
        st.error("有効かつ未FIXEDの項目が見つかりません。")
        return

    # ============================================================
    #  2) Dropdown: Performance Area (senario_id = 15)
    # ============================================================

    area_values = get_dropdown_values(filtered_df, valid_study_ids, senario_id=15)
    if not area_values:
        # st.error("No Performance Area (領域) options available.")
        st.error("有効かつ未FIXEDの領域の項目が見つかりません。")
        return

    selected_area = st.selectbox(
        "領域",
        area_values,
        key="selected_area_unique_key",
        index=0 if area_values else None
    )
    selected_area = [selected_area] if selected_area else []

    # ============================================================
    #  2.5) Update valid_suffixes and valid_study_ids after 領域 selection
    # ============================================================
    
    if not selected_area:
        st.error("領域を選択してください。")
        return
    
    # Filter study_ids by selected area (senario_id=15)
    area_filtered_ids = filter_study_ids_by_value(
        filtered_df,
        valid_study_ids,
        senario_id=15,
        selected_value=selected_area[0]
    )
    # st.write('area_filtered_ids: ', area_filtered_ids)
    
    # Update valid_study_ids
    valid_study_ids = area_filtered_ids
    
    # Update valid_suffixes to only include suffixes with these study_ids
    updated_suffixes = set()
    for suffix in valid_suffixes:
        study_col = get_matching_columns(study_cols, suffix)
        if study_col:
            # Check if this suffix has any of the valid_study_ids
            suffix_study_ids = df[study_col[0]].unique()
            if any(sid in valid_study_ids for sid in suffix_study_ids if sid and str(sid).strip() not in ("", "nan")):
                updated_suffixes.add(suffix)
    
    valid_suffixes = updated_suffixes
    # st.write('After 領域 - Updated valid_suffixes: ', valid_suffixes)
    # st.write('After 領域 - Updated valid_study_ids: ', valid_study_ids)
    
    # Re-filter the dataframe with updated suffixes
    filtered_df = filter_df_by_suffixes(df, valid_suffixes)
    if filtered_df.empty:
        st.error("選択された領域に一致する項目が見つかりません。")
        return

    # ============================================================
    #  3) Dropdown: Target Performance (senario_id = 3)
    # ============================================================

    target_perf_values = get_dropdown_values(
        filtered_df, valid_study_ids, senario_id=3
    )
    if not target_perf_values:
        st.error("選択された領域に対して有効かつ未FIXEDの目標性能の項目が見つかりません。")
        return

    selected_target_perf = st.selectbox(
        "目標性能",
        target_perf_values,
        key="target_performance_unique_key",
        index=0 if target_perf_values else None
    )
    selected_target_perf = [selected_target_perf] if selected_target_perf else []

    # ============================================================
    #  3.5) Update valid_suffixes and valid_study_ids after 目標性能 selection
    # ============================================================
    
    if not selected_target_perf:
        st.error("目標性能を選択してください。")
        return
    
    # Filter study_ids by selected target performance (senario_id=3)
    target_perf_filtered_ids = filter_study_ids_by_value(
        filtered_df,
        valid_study_ids,
        senario_id=3,
        selected_value=selected_target_perf[0]
    )
    # st.write('target_perf_filtered_ids: ', target_perf_filtered_ids)
    
    # Update valid_study_ids
    valid_study_ids = target_perf_filtered_ids
    
    # Update valid_suffixes to only include suffixes with these study_ids
    updated_suffixes = set()
    for suffix in valid_suffixes:
        study_col = get_matching_columns(study_cols, suffix)
        if study_col:
            # Check if this suffix has any of the valid_study_ids
            suffix_study_ids = df[study_col[0]].unique()
            if any(sid in valid_study_ids for sid in suffix_study_ids if sid and str(sid).strip() not in ("", "nan")):
                updated_suffixes.add(suffix)
    
    valid_suffixes = updated_suffixes
    # st.write('After 目標性能 - Updated valid_suffixes: ', valid_suffixes)
    # st.write('After 目標性能 - Updated valid_study_ids: ', valid_study_ids)
    
    # Re-filter the dataframe with updated suffixes
    filtered_df = filter_df_by_suffixes(df, valid_suffixes)
    if filtered_df.empty:
        st.error("選択された領域と目標性能に一致する項目が見つかりません。")
        return

    # ============================================================
    #  4) Performance List → Design Item Selection
    # ============================================================

    if not selected_area or not selected_target_perf:
        st.error("領域と目標性能を選択してください。")
        return

    info_list = st.session_state.sim_prj_info_list
    if info_list.empty:
        st.error("SIMリストの対象Meta情報はありません。")
        return

    project_ids = info_list["project_id"].unique().tolist()
    phase_ids   = info_list["phase_id"].unique().tolist()
    variation_ids = info_list["variation_id"].unique().tolist()
    destinations = info_list["destination"].unique().tolist()
    drivetrains  = info_list["drivetrain"].unique().tolist()

    performance_lists = sql.getr_value_to_sim(
        project_ids,
        phase_ids,
        variation_ids,
        selected_area,
        selected_target_perf
    )
    if performance_lists.empty:
        st.error("対象するRリスト情報はありません.")
        return

    # Design Item 1
    item1_opts = performance_lists["design_item_1"].unique().tolist()
    if not item1_opts:
        st.error("設計項目（大）の項目が見つかりません。")
        return
    selected_item1 = st.selectbox(
        "設計項目（大）",
        item1_opts,
        key="selected_perf1_unique_key",
        index=0
    )
    selected_item1 = [selected_item1] if selected_item1 else []

    # Design Item 2
    pl_filtered = performance_lists[performance_lists["design_item_1"].isin(selected_item1)]
    item2_opts = pl_filtered["design_item_2"].unique().tolist()
    if not item2_opts:
        st.error("設計項目（小）の項目が見つかりません。")
        return
    selected_item2 = st.selectbox(
        "設計項目（小）",
        item2_opts,
        key="selected_perf2_unique_key",
        index=0
    )
    selected_item2 = [selected_item2] if selected_item2 else []

    # ============================================================
    #  5) Create FIXED Candidate Table
    # ============================================================

    selected_ids = pl_filtered[pl_filtered["design_item_2"].isin(selected_item2)]["id"].tolist()
    # st.write('selected_ids: ', selected_ids)
    if not selected_ids:
        st.error("No matching performance IDs found for selected design items.")
        return

    rfl_cols = [c for c in filtered_df.columns if "rflcategory" in c.lower()]
    # st.write('rfl_cols: ', rfl_cols)
    if len(rfl_cols) < 1:
        st.error("RFL Category columns are missing or insufficient.")
        return

    # Keep only rows where any rflcategory == 'R'
    df_R = filtered_df[(filtered_df[rfl_cols] == "R").any(axis=1)]
    # st.write('df_R: ', df_R)
    if df_R.empty:
        st.error("No rows with rflcategory == 'R'.")
        return

    # Build combined dataframe
    combined_list = []
    for suffix in valid_suffixes:
        cols = [c for c in df_R.columns if extract_suffix(c) == suffix]
        rename_map = {c: c.split(";")[1] for c in cols}
        combined_list.append(df_R[cols].rename(columns=rename_map))
    combined_df = pd.concat(combined_list, ignore_index=True)

    key_cols = ["id", "project_id", "senario_parameter_id", "phase_id", "variation_id", "study_id"]
    combined_df = combined_df.dropna(subset=key_cols, how="all").reset_index(drop=True)
    if combined_df.empty:
        st.error("Combined dataframe is empty after dropping rows without key identifiers.")
        return

    # Filter by selected performance IDs
    fixed_df = combined_df[combined_df["rflid"].isin(selected_ids)]
    if fixed_df.empty:
        st.error("No FIXED candidates found for the selected performance IDs.")
        return

    # Merge performance metadata
    perf_info = pl_filtered[["id", "performance", "design_item_1", "design_item_2"]].rename(columns={"id": "rflid"})
    fixed_df = fixed_df.merge(perf_info, on="rflid", how="left")

    # Display confirmation
    st.markdown(
        "<h3>確認内容</h3>"
        f"&emsp;領域：{selected_area[0]}<br>"
        f"&emsp;設計項目（大）：{selected_item1[0]}<br>"
        f"&emsp;設計項目（小）：{selected_item2[0]}<br>",
        unsafe_allow_html=True
    )

    # Display FIXED table
    go = gop.fixed_sim()
    st.session_state.Prj_updata = AgGrid(
        fixed_df,
        custom_css=css_ag,
        gridOptions=go,
        reload_data=False,
        height=220,
    )

    # Execute FIXED
    if st.button("実行", key="fixed_sim_button_key_2"):
        selected_rows = st.session_state.Prj_updata["selected_rows"]
        # if not selected_rows:
        if selected_rows is None or selected_rows.empty:
            st.error("FIXEDする項目を選択してください。")
        elif len(selected_rows) > 1:
            st.error("1行しかFIXEDできません。")
        else:
            ok = sql.update_fixed_r_record(selected_rows)
            if ok:
                execute_sim_list(True)
            else:
                st.error("Failed to update FIXED record.")


# @st.dialog("設計値確定")
# def choice_sim_fixed():
#     # ============================================================
#     #  Helper Functions
#     # ============================================================

#     def extract_suffix(col_name: str) -> str:
#         """Return the last ';'-separated suffix.
#         Example: '14;senario_parameter_id;P1提案仕様251117test' -> 'P1提案仕様251117test'
#         """
#         return col_name.split(";")[-1]

#     def get_matching_columns(columns, suffix):
#         """Return all columns whose suffix matches the given suffix."""
#         return [c for c in columns if c.endswith(suffix)]

#     def collect_valid_suffixes(df, senario_cols, study_cols, value_cols):
#         """
#         Determine valid study suffixes:
#           - parameter 96 must be '有効'
#           - parameter 98 must NOT be 'FIXED'
#         Returns:
#             valid_suffixes (set)
#             valid_study_ids (set)
#         """
#         # Filter rows containing parameter 96 & 98
#         rows_param96 = df[df[senario_cols].apply(lambda r: 96 in r.values, axis=1)]
#         rows_param98 = df[df[senario_cols].apply(lambda r: 98 in r.values, axis=1)]

#         suffix_yukou = {}   # suffix -> study_id
#         suffix_fixed = set() # suffixes marked FIXED

#         # Collect "有効" study_ids for parameter 96
#         for _, row in rows_param96.iterrows():
#             for vcol in value_cols:
#                 if row[vcol] == "有効":
#                     suffix = extract_suffix(vcol)
#                     study_col = get_matching_columns(study_cols, suffix)
#                     if study_col:
#                         sid = row[study_col[0]]
#                         if sid and str(sid).strip() not in ("", "nan"):
#                             suffix_yukou[suffix] = sid

#         # Collect "FIXED" suffixes for parameter 98
#         for _, row in rows_param98.iterrows():
#             for vcol in value_cols:
#                 if row[vcol] == "FIXED":
#                     suffix_fixed.add(extract_suffix(vcol))

#         # Only keep suffixes that are 有効 but NOT FIXED
#         valid_suffixes = {s for s in suffix_yukou if s not in suffix_fixed}
#         valid_study_ids = {suffix_yukou[s] for s in valid_suffixes}

#         return valid_suffixes, valid_study_ids

#     def filter_df_by_suffixes(df, suffixes):
#         """Keep only columns whose suffix is in the given suffix set."""
#         valid_cols = [c for c in df.columns if extract_suffix(c) in suffixes]
#         return df[valid_cols]

#     def get_dropdown_values(df, study_ids, senario_id):
#         """Return sorted dropdown values for a parameter from valid study_ids."""
#         if not study_ids:
#             return []

#         senario_cols = [c for c in df.columns if "senario_parameter_id" in c]
#         study_cols = [c for c in df.columns if "study_id" in c]
#         value_cols = [c for c in df.columns if ";value;" in c]

#         # Filter rows having the target senario_id
#         rows = df[df[senario_cols].apply(lambda r: senario_id in r.values, axis=1)]

#         values = set()
#         for _, row in rows.iterrows():
#             for vcol in value_cols:
#                 suffix = extract_suffix(vcol)
#                 study_col = get_matching_columns(study_cols, suffix)
#                 if study_col and row[study_col[0]] in study_ids:
#                     values.add(row[vcol])

#         return sorted(values)

#     def filter_study_ids_by_value(df, study_ids, senario_id, selected_value):
#         """Return study_ids that have the selected_value under given senario_id."""
#         if not selected_value:
#             return set()

#         senario_cols = [c for c in df.columns if "senario_parameter_id" in c]
#         study_cols = [c for c in df.columns if "study_id" in c]
#         value_cols = [c for c in df.columns if ";value;" in c]

#         rows = df[df[senario_cols].apply(lambda r: senario_id in r.values, axis=1)]

#         result_ids = set()
#         for _, row in rows.iterrows():
#             for vcol in value_cols:
#                 if row[vcol] == selected_value:
#                     suffix = extract_suffix(vcol)
#                     study_col = get_matching_columns(study_cols, suffix)
#                     if study_col:
#                         sid = row[study_col[0]]
#                         if sid in study_ids:
#                             result_ids.add(sid)

#         return result_ids

#     # ============================================================
#     #  1) Load Data
#     # ============================================================

#     df = st.session_state.sim_data_stuck
#     if df.empty:
#         st.error("選択されたSIMリスト情報はありません。")
#         return

#     senario_cols = [c for c in df.columns if "senario_parameter_id" in c]
#     study_cols   = [c for c in df.columns if "study_id" in c]
#     value_cols   = [c for c in df.columns if ";value;" in c]

#     # Determine valid suffixes / study_ids
#     valid_suffixes, valid_study_ids = collect_valid_suffixes(df, senario_cols, study_cols, value_cols)
#     if not valid_suffixes:
#         st.error("有効かつ未FIXEDの項目が見つかりません。")
#         return

#     # Restrict DF to only valid suffixes
#     filtered_df = filter_df_by_suffixes(df, valid_suffixes)
#     if filtered_df.empty:
#         # st.error("Filtered dataframe is empty after applying valid suffixes.")
#         st.error("有効かつ未FIXEDの項目が見つかりません。")
#         return

#     # ============================================================
#     #  2) Dropdown: Performance Area (senario_id = 15)
#     # ============================================================

#     area_values = get_dropdown_values(filtered_df, valid_study_ids, senario_id=15)
#     if not area_values:
#         # st.error("No Performance Area (領域) options available.")
#         st.error("有効かつ未FIXEDの領域の項目が見つかりません。")
#         return

#     selected_area = st.selectbox(
#         "領域",
#         area_values,
#         key="selected_area_unique_key",
#         index=0 if area_values else None
#     )
#     selected_area = [selected_area] if selected_area else []

#     # ============================================================
#     #  2.5) Update valid_suffixes and valid_study_ids after 領域 selection
#     # ============================================================
    
#     if not selected_area:
#         st.error("領域を選択してください。")
#         return
    
#     # Filter study_ids by selected area (senario_id=15)
#     area_filtered_ids = filter_study_ids_by_value(
#         filtered_df,
#         valid_study_ids,
#         senario_id=15,
#         selected_value=selected_area[0]
#     )
#     # st.write('area_filtered_ids: ', area_filtered_ids)
    
#     # Update valid_study_ids
#     valid_study_ids = area_filtered_ids
    
#     # Update valid_suffixes to only include suffixes with these study_ids
#     updated_suffixes = set()
#     for suffix in valid_suffixes:
#         study_col = get_matching_columns(study_cols, suffix)
#         if study_col:
#             # Check if this suffix has any of the valid_study_ids
#             suffix_study_ids = df[study_col[0]].unique()
#             if any(sid in valid_study_ids for sid in suffix_study_ids if sid and str(sid).strip() not in ("", "nan")):
#                 updated_suffixes.add(suffix)
    
#     valid_suffixes = updated_suffixes
#     # st.write('After 領域 - Updated valid_suffixes: ', valid_suffixes)
#     # st.write('After 領域 - Updated valid_study_ids: ', valid_study_ids)
    
#     # Re-filter the dataframe with updated suffixes
#     filtered_df = filter_df_by_suffixes(df, valid_suffixes)
#     if filtered_df.empty:
#         st.error("選択された領域に一致する項目が見つかりません。")
#         return

#     # ============================================================
#     #  3) Dropdown: 設計項目（大）(senario_parameter_id = 56)
#     # ============================================================

#     item1_values = get_dropdown_values(
#         filtered_df, valid_study_ids, senario_id=56
#     )
#     if not item1_values:
#         st.error("選択された領域に対して有効かつ未FIXEDの設計項目（大）の項目が見つかりません。")
#         return

#     selected_item1 = st.selectbox(
#         "設計項目（大）",
#         item1_values,
#         key="selected_perf1_unique_key",
#         index=0 if item1_values else None
#     )
#     selected_item1 = [selected_item1] if selected_item1 else []

#     # ============================================================
#     #  3.5) Update valid_suffixes and valid_study_ids after 設計項目（大）selection
#     # ============================================================
    
#     if not selected_item1:
#         st.error("設計項目（大）を選択してください。")
#         return
    
#     # Filter study_ids by selected design item 1 (senario_parameter_id=56)
#     item1_filtered_ids = filter_study_ids_by_value(
#         filtered_df,
#         valid_study_ids,
#         senario_id=56,
#         selected_value=selected_item1[0]
#     )
#     # st.write('item1_filtered_ids: ', item1_filtered_ids)
    
#     # Update valid_study_ids
#     valid_study_ids = item1_filtered_ids
    
#     # Update valid_suffixes to only include suffixes with these study_ids
#     updated_suffixes = set()
#     for suffix in valid_suffixes:
#         study_col = get_matching_columns(study_cols, suffix)
#         if study_col:
#             # Check if this suffix has any of the valid_study_ids
#             suffix_study_ids = df[study_col[0]].unique()
#             if any(sid in valid_study_ids for sid in suffix_study_ids if sid and str(sid).strip() not in ("", "nan")):
#                 updated_suffixes.add(suffix)
    
#     valid_suffixes = updated_suffixes
#     # st.write('After 設計項目（大） - Updated valid_suffixes: ', valid_suffixes)
#     # st.write('After 設計項目（大） - Updated valid_study_ids: ', valid_study_ids)
    
#     # Re-filter the dataframe with updated suffixes
#     filtered_df = filter_df_by_suffixes(df, valid_suffixes)
#     if filtered_df.empty:
#         st.error("選択された領域と設計項目（大）に一致する項目が見つかりません。")
#         return

#     # ============================================================
#     #  4) Dropdown: 設計項目（小）(senario_parameter_id = 57)
#     # ============================================================

#     item2_values = get_dropdown_values(
#         filtered_df, valid_study_ids, senario_id=57
#     )
#     if not item2_values:
#         st.error("選択された領域と設計項目（大）に対して有効かつ未FIXEDの設計項目（小）の項目が見つかりません。")
#         return

#     selected_item2 = st.selectbox(
#         "設計項目（小）",
#         item2_values,
#         key="selected_perf2_unique_key",
#         index=0 if item2_values else None
#     )
#     selected_item2 = [selected_item2] if selected_item2 else []

#     # ============================================================
#     #  4.5) Update valid_suffixes and valid_study_ids after 設計項目（小）selection
#     # ============================================================
    
#     if not selected_item2:
#         st.error("設計項目（小）を選択してください。")
#         return
    
#     # Filter study_ids by selected design item 2 (senario_parameter_id=57)
#     item2_filtered_ids = filter_study_ids_by_value(
#         filtered_df,
#         valid_study_ids,
#         senario_id=57,
#         selected_value=selected_item2[0]
#     )
#     # st.write('item2_filtered_ids: ', item2_filtered_ids)
    
#     # Update valid_study_ids
#     valid_study_ids = item2_filtered_ids
    
#     # Update valid_suffixes to only include suffixes with these study_ids
#     updated_suffixes = set()
#     for suffix in valid_suffixes:
#         study_col = get_matching_columns(study_cols, suffix)
#         if study_col:
#             # Check if this suffix has any of the valid_study_ids
#             suffix_study_ids = df[study_col[0]].unique()
#             if any(sid in valid_study_ids for sid in suffix_study_ids if sid and str(sid).strip() not in ("", "nan")):
#                 updated_suffixes.add(suffix)
    
#     valid_suffixes = updated_suffixes
#     # st.write('After 設計項目（小） - Updated valid_suffixes: ', valid_suffixes)
#     # st.write('After 設計項目（小） - Updated valid_study_ids: ', valid_study_ids)
    
#     # Re-filter the dataframe with updated suffixes
#     filtered_df = filter_df_by_suffixes(df, valid_suffixes)
#     if filtered_df.empty:
#         st.error("選択された領域、設計項目（大）、設計項目（小）に一致する項目が見つかりません。")
#         return

#     # ============================================================
#     #  5) Dropdown: Target Performance (senario_id = 3)
#     # ============================================================

#     target_perf_values = get_dropdown_values(
#         filtered_df, valid_study_ids, senario_id=3
#     )
#     if not target_perf_values:
#         st.error("選択された領域、設計項目（大）、設計項目（小）に対して有効かつ未FIXEDの目標性能の項目が見つかりません。")
#         return

#     selected_target_perf = st.selectbox(
#         "目標性能",
#         target_perf_values,
#         key="target_performance_unique_key",
#         index=0 if target_perf_values else None
#     )
#     selected_target_perf = [selected_target_perf] if selected_target_perf else []

#     # ============================================================
#     #  5.5) Update valid_suffixes and valid_study_ids after 目標性能 selection
#     # ============================================================
    
#     if not selected_target_perf:
#         st.error("目標性能を選択してください。")
#         return
    
#     # Filter study_ids by selected target performance (senario_id=3)
#     target_perf_filtered_ids = filter_study_ids_by_value(
#         filtered_df,
#         valid_study_ids,
#         senario_id=3,
#         selected_value=selected_target_perf[0]
#     )
#     # st.write('target_perf_filtered_ids: ', target_perf_filtered_ids)
    
#     # Update valid_study_ids
#     valid_study_ids = target_perf_filtered_ids
    
#     # Update valid_suffixes to only include suffixes with these study_ids
#     updated_suffixes = set()
#     for suffix in valid_suffixes:
#         study_col = get_matching_columns(study_cols, suffix)
#         if study_col:
#             # Check if this suffix has any of the valid_study_ids
#             suffix_study_ids = df[study_col[0]].unique()
#             if any(sid in valid_study_ids for sid in suffix_study_ids if sid and str(sid).strip() not in ("", "nan")):
#                 updated_suffixes.add(suffix)
    
#     valid_suffixes = updated_suffixes
#     # st.write('After 目標性能 - Updated valid_suffixes: ', valid_suffixes)
#     # st.write('After 目標性能 - Updated valid_study_ids: ', valid_study_ids)
    
#     # Re-filter the dataframe with updated suffixes
#     filtered_df = filter_df_by_suffixes(df, valid_suffixes)
#     if filtered_df.empty:
#         st.error("選択された領域、設計項目（大）、設計項目（小）、目標性能に一致する項目が見つかりません。")
#         return

#     # ============================================================
#     #  6) Performance List → Get R List IDs
#     # ============================================================

#     if not selected_area or not selected_item1 or not selected_item2 or not selected_target_perf:
#         st.error("領域、設計項目（大）、設計項目（小）、目標性能を選択してください。")
#         return

#     info_list = st.session_state.sim_prj_info_list
#     if info_list.empty:
#         st.error("SIMリストの対象Meta情報はありません。")
#         return

#     project_ids = info_list["project_id"].unique().tolist()
#     phase_ids   = info_list["phase_id"].unique().tolist()
#     variation_ids = info_list["variation_id"].unique().tolist()
#     destinations = info_list["destination"].unique().tolist()
#     drivetrains  = info_list["drivetrain"].unique().tolist()

#     performance_lists = sql.getr_value_to_sim(
#         project_ids,
#         phase_ids,
#         variation_ids,
#         selected_area,
#         selected_target_perf
#     )
#     if performance_lists.empty:
#         st.error("対象するRリスト情報はありません.")
#         return

#     # Filter performance_lists by selected design items
#     pl_filtered = performance_lists[
#         (performance_lists["design_item_1"].isin(selected_item1)) &
#         (performance_lists["design_item_2"].isin(selected_item2))
#     ]
#     if pl_filtered.empty:
#         st.error("選択された設計項目（大）と設計項目（小）に一致するRリスト情報はありません。")
#         return

#     # ============================================================
#     #  7) Create FIXED Candidate Table
#     # ============================================================

#     selected_ids = pl_filtered["id"].tolist()
#     # st.write('selected_ids: ', selected_ids)
#     if not selected_ids:
#         st.error("No matching performance IDs found for selected design items.")
#         return

#     rfl_cols = [c for c in filtered_df.columns if "rflcategory" in c.lower()]
#     # st.write('rfl_cols: ', rfl_cols)
#     if len(rfl_cols) < 1:
#         st.error("RFL Category columns are missing or insufficient.")
#         return

#     # Keep only rows where any rflcategory == 'R'
#     df_R = filtered_df[(filtered_df[rfl_cols] == "R").any(axis=1)]
#     # st.write('df_R: ', df_R)
#     if df_R.empty:
#         st.error("No rows with rflcategory == 'R'.")
#         return

#     # Build combined dataframe
#     combined_list = []
#     for suffix in valid_suffixes:
#         cols = [c for c in df_R.columns if extract_suffix(c) == suffix]
#         rename_map = {c: c.split(";")[1] for c in cols}
#         combined_list.append(df_R[cols].rename(columns=rename_map))
#     combined_df = pd.concat(combined_list, ignore_index=True)

#     key_cols = ["id", "project_id", "senario_parameter_id", "phase_id", "variation_id", "study_id"]
#     combined_df = combined_df.dropna(subset=key_cols, how="all").reset_index(drop=True)
#     if combined_df.empty:
#         st.error("Combined dataframe is empty after dropping rows without key identifiers.")
#         return

#     # Filter by selected performance IDs
#     fixed_df = combined_df[combined_df["rflid"].isin(selected_ids)]
#     if fixed_df.empty:
#         st.error("No FIXED candidates found for the selected performance IDs.")
#         return

#     # Merge performance metadata
#     perf_info = pl_filtered[["id", "performance", "design_item_1", "design_item_2"]].rename(columns={"id": "rflid"})
#     fixed_df = fixed_df.merge(perf_info, on="rflid", how="left")

#     # Display confirmation
#     st.markdown(
#         "<h3>確認内容</h3>"
#         f"&emsp;領域：{selected_area[0]}<br>"
#         f"&emsp;設計項目（大）：{selected_item1[0]}<br>"
#         f"&emsp;設計項目（小）：{selected_item2[0]}<br>"
#         f"&emsp;目標性能：{selected_target_perf[0]}<br>",
#         unsafe_allow_html=True
#     )

#     # Display FIXED table
#     go = gop.fixed_sim()
#     st.session_state.Prj_updata = AgGrid(
#         fixed_df,
#         custom_css=css_ag,
#         gridOptions=go,
#         reload_data=False,
#         height=220,
#     )

#     # Execute FIXED
#     if st.button("実行", key="fixed_sim_button_key_2"):
#         selected_rows = st.session_state.Prj_updata["selected_rows"]
#         # if not selected_rows:
#         if selected_rows is None or selected_rows.empty:
#             st.error("FIXEDする項目を選択してください。")
#         elif len(selected_rows) > 1:
#             st.error("1行しかFIXEDできません。")
#         else:
#             ok = sql.update_fixed_r_record(selected_rows)
#             if ok:
#                 execute_sim_list(True)
#             else:
#                 st.error("Failed to update FIXED record.")


# @st.dialog("設計値確定") #updated ver 17:01 Both FIXED and 有効
# def choice_sim_fixed():
#     # ============================================================
#     #  Helper Functions
#     # ============================================================

#     def extract_suffix(col_name: str) -> str:
#         """Return the last ';'-separated suffix.
#         Example: '14;senario_parameter_id;P1提案仕様251117test' -> 'P1提案仕様251117test'
#         """
#         return col_name.split(";")[-1]

#     def get_matching_columns(columns, suffix):
#         """Return all columns whose suffix matches the given suffix."""
#         return [c for c in columns if c.endswith(suffix)]

#     def collect_valid_suffixes(df, senario_cols, study_cols, value_cols):
#         """
#         Determine valid study suffixes:
#           - parameter 96 must be '有効'
#           - parameter 98 must NOT be 'FIXED'
#         Returns:
#             valid_suffixes (set)
#             valid_study_ids (set)
#         """
#         # Filter rows containing parameter 96 & 98
#         rows_param96 = df[df[senario_cols].apply(lambda r: 96 in r.values, axis=1)]
#         rows_param98 = df[df[senario_cols].apply(lambda r: 98 in r.values, axis=1)]

#         suffix_yukou = {}   # suffix -> study_id
#         suffix_fixed = set() # suffixes marked FIXED

#         # Collect "有効" study_ids for parameter 96
#         for _, row in rows_param96.iterrows():
#             for vcol in value_cols:
#                 if row[vcol] == "有効":
#                     suffix = extract_suffix(vcol)
#                     study_col = get_matching_columns(study_cols, suffix)
#                     if study_col:
#                         sid = row[study_col[0]]
#                         if sid and str(sid).strip() not in ("", "nan"):
#                             suffix_yukou[suffix] = sid

#         # Collect "FIXED" suffixes for parameter 98
#         for _, row in rows_param98.iterrows():
#             for vcol in value_cols:
#                 if row[vcol] == "FIXED":
#                     suffix_fixed.add(extract_suffix(vcol))

#         # Only keep suffixes that are 有効 but NOT FIXED
#         valid_suffixes = {s for s in suffix_yukou if s not in suffix_fixed}
#         valid_study_ids = {suffix_yukou[s] for s in valid_suffixes}

#         return valid_suffixes, valid_study_ids

#     def filter_df_by_suffixes(df, suffixes):
#         """Keep only columns whose suffix is in the given suffix set."""
#         valid_cols = [c for c in df.columns if extract_suffix(c) in suffixes]
#         return df[valid_cols]

#     def get_dropdown_values(df, study_ids, senario_id):
#         """Return sorted dropdown values for a parameter from valid study_ids."""
#         if not study_ids:
#             return []

#         senario_cols = [c for c in df.columns if "senario_parameter_id" in c]
#         study_cols = [c for c in df.columns if "study_id" in c]
#         value_cols = [c for c in df.columns if ";value;" in c]

#         # Filter rows having the target senario_id
#         rows = df[df[senario_cols].apply(lambda r: senario_id in r.values, axis=1)]

#         values = set()
#         for _, row in rows.iterrows():
#             for vcol in value_cols:
#                 suffix = extract_suffix(vcol)
#                 study_col = get_matching_columns(study_cols, suffix)
#                 if study_col and row[study_col[0]] in study_ids:
#                     values.add(row[vcol])

#         return sorted(values)

#     def filter_study_ids_by_value(df, study_ids, senario_id, selected_value):
#         """Return study_ids that have the selected_value under given senario_id."""
#         if not selected_value:
#             return set()

#         senario_cols = [c for c in df.columns if "senario_parameter_id" in c]
#         study_cols = [c for c in df.columns if "study_id" in c]
#         value_cols = [c for c in df.columns if ";value;" in c]

#         rows = df[df[senario_cols].apply(lambda r: senario_id in r.values, axis=1)]

#         result_ids = set()
#         for _, row in rows.iterrows():
#             for vcol in value_cols:
#                 if row[vcol] == selected_value:
#                     suffix = extract_suffix(vcol)
#                     study_col = get_matching_columns(study_cols, suffix)
#                     if study_col:
#                         sid = row[study_col[0]]
#                         if sid in study_ids:
#                             result_ids.add(sid)

#         return result_ids

#     # ============================================================
#     #  1) Load Data
#     # ============================================================

#     df = st.session_state.sim_data_stuck
#     if df.empty:
#         st.error("選択されたSIMリスト情報はありません。")
#         return

#     senario_cols = [c for c in df.columns if "senario_parameter_id" in c]
#     study_cols   = [c for c in df.columns if "study_id" in c]
#     value_cols   = [c for c in df.columns if ";value;" in c]

#     # Determine valid suffixes / study_ids
#     valid_suffixes, valid_study_ids = collect_valid_suffixes(df, senario_cols, study_cols, value_cols)
#     if not valid_suffixes:
#         st.error("有効かつ未FIXEDの項目が見つかりません。")
#         return

#     # Restrict DF to only valid suffixes
#     filtered_df = filter_df_by_suffixes(df, valid_suffixes)
#     if filtered_df.empty:
#         # st.error("Filtered dataframe is empty after applying valid suffixes.")
#         st.error("有効かつ未FIXEDの項目が見つかりません。")
#         return

#     # ============================================================
#     #  2) Dropdown: Performance Area (senario_id = 15)
#     # ============================================================

#     area_values = get_dropdown_values(filtered_df, valid_study_ids, senario_id=15)
#     # Remove 'PTシステムレビュー向け全R項目' if it exists
#     area_values = [v for v in area_values if v != 'PTシステムレビュー向け全R項目']
#     if not area_values:
#         # st.error("No Performance Area (領域) options available.")
#         st.error("有効かつ未FIXEDの領域の項目が見つかりません。")
#         return

#     selected_area = st.selectbox(
#         "領域",
#         area_values,
#         key="selected_area_unique_key",
#         index=0 if area_values else None
#     )
#     selected_area = [selected_area] if selected_area else []

#     # ============================================================
#     #  2.5) Update valid_suffixes and valid_study_ids after 領域 selection
#     # ============================================================
    
#     if not selected_area:
#         st.error("領域を選択してください。")
#         return
    
#     # Filter study_ids by selected area (senario_id=15)
#     area_filtered_ids = filter_study_ids_by_value(
#         filtered_df,
#         valid_study_ids,
#         senario_id=15,
#         selected_value=selected_area[0]
#     )
#     # st.write('area_filtered_ids: ', area_filtered_ids)
    
#     # Update valid_study_ids
#     valid_study_ids = area_filtered_ids
    
#     # Update valid_suffixes to only include suffixes with these study_ids
#     updated_suffixes = set()
#     for suffix in valid_suffixes:
#         study_col = get_matching_columns(study_cols, suffix)
#         if study_col:
#             # Check if this suffix has any of the valid_study_ids
#             suffix_study_ids = df[study_col[0]].unique()
#             if any(sid in valid_study_ids for sid in suffix_study_ids if sid and str(sid).strip() not in ("", "nan")):
#                 updated_suffixes.add(suffix)
    
#     valid_suffixes = updated_suffixes
#     # st.write('After 領域 - Updated valid_suffixes: ', valid_suffixes)
#     # st.write('After 領域 - Updated valid_study_ids: ', valid_study_ids)
    
#     # Re-filter the dataframe with updated suffixes
#     filtered_df = filter_df_by_suffixes(df, valid_suffixes)
#     if filtered_df.empty:
#         st.error("選択された領域に一致する項目が見つかりません。")
#         return

#     # ============================================================
#     #  3) Dropdown: 設計項目（大）(senario_parameter_id = 56)
#     # ============================================================

#     item1_values = get_dropdown_values(
#         filtered_df, valid_study_ids, senario_id=56
#     )
#     if not item1_values:
#         st.error("選択された領域に対して有効かつ未FIXEDの設計項目（大）の項目が見つかりません。")
#         return

#     selected_item1 = st.selectbox(
#         "設計項目（大）",
#         item1_values,
#         key="selected_perf1_unique_key",
#         index=0 if item1_values else None
#     )
#     selected_item1 = [selected_item1] if selected_item1 else []

#     # ============================================================
#     #  3.5) Update valid_suffixes and valid_study_ids after 設計項目（大）selection
#     # ============================================================
    
#     if not selected_item1:
#         st.error("設計項目（大）を選択してください。")
#         return
    
#     # Filter study_ids by selected design item 1 (senario_parameter_id=56)
#     item1_filtered_ids = filter_study_ids_by_value(
#         filtered_df,
#         valid_study_ids,
#         senario_id=56,
#         selected_value=selected_item1[0]
#     )
#     # st.write('item1_filtered_ids: ', item1_filtered_ids)
    
#     # Update valid_study_ids
#     valid_study_ids = item1_filtered_ids
    
#     # Update valid_suffixes to only include suffixes with these study_ids
#     updated_suffixes = set()
#     for suffix in valid_suffixes:
#         study_col = get_matching_columns(study_cols, suffix)
#         if study_col:
#             # Check if this suffix has any of the valid_study_ids
#             suffix_study_ids = df[study_col[0]].unique()
#             if any(sid in valid_study_ids for sid in suffix_study_ids if sid and str(sid).strip() not in ("", "nan")):
#                 updated_suffixes.add(suffix)
    
#     valid_suffixes = updated_suffixes
#     # st.write('After 設計項目（大） - Updated valid_suffixes: ', valid_suffixes)
#     # st.write('After 設計項目（大） - Updated valid_study_ids: ', valid_study_ids)
    
#     # Re-filter the dataframe with updated suffixes
#     filtered_df = filter_df_by_suffixes(df, valid_suffixes)
#     if filtered_df.empty:
#         st.error("選択された領域と設計項目（大）に一致する項目が見つかりません。")
#         return

#     # ============================================================
#     #  4) Dropdown: 設計項目（小）(senario_parameter_id = 57)
#     # ============================================================

#     item2_values = get_dropdown_values(
#         filtered_df, valid_study_ids, senario_id=57
#     )
#     if not item2_values:
#         st.error("選択された領域と設計項目（大）に対して有効かつ未FIXEDの設計項目（小）の項目が見つかりません。")
#         return

#     selected_item2 = st.selectbox(
#         "設計項目（小）",
#         item2_values,
#         key="selected_perf2_unique_key",
#         index=0 if item2_values else None
#     )
#     selected_item2 = [selected_item2] if selected_item2 else []

#     # ============================================================
#     #  4.5) Update valid_suffixes and valid_study_ids after 設計項目（小）selection
#     # ============================================================
    
#     if not selected_item2:
#         st.error("設計項目（小）を選択してください。")
#         return
    
#     # Filter study_ids by selected design item 2 (senario_parameter_id=57)
#     item2_filtered_ids = filter_study_ids_by_value(
#         filtered_df,
#         valid_study_ids,
#         senario_id=57,
#         selected_value=selected_item2[0]
#     )
#     # st.write('item2_filtered_ids: ', item2_filtered_ids)
    
#     # Update valid_study_ids
#     valid_study_ids = item2_filtered_ids
    
#     # Update valid_suffixes to only include suffixes with these study_ids
#     updated_suffixes = set()
#     for suffix in valid_suffixes:
#         study_col = get_matching_columns(study_cols, suffix)
#         if study_col:
#             # Check if this suffix has any of the valid_study_ids
#             suffix_study_ids = df[study_col[0]].unique()
#             if any(sid in valid_study_ids for sid in suffix_study_ids if sid and str(sid).strip() not in ("", "nan")):
#                 updated_suffixes.add(suffix)
    
#     valid_suffixes = updated_suffixes
#     # st.write('After 設計項目（小） - Updated valid_suffixes: ', valid_suffixes)
#     # st.write('After 設計項目（小） - Updated valid_study_ids: ', valid_study_ids)
    
#     # Re-filter the dataframe with updated suffixes
#     filtered_df = filter_df_by_suffixes(df, valid_suffixes)
#     if filtered_df.empty:
#         st.error("選択された領域、設計項目（大）、設計項目（小）に一致する項目が見つかりません。")
#         return

#     # ============================================================
#     #  5) Dropdown: Target Performance (senario_id = 3)
#     # ============================================================

#     design_item3_values = get_dropdown_values(
#         filtered_df, valid_study_ids, senario_id=3
#     )
#     if not design_item3_values:
#         st.error("選択された領域、設計項目（大）、設計項目（小）に対して有効かつ未FIXEDの目標性能の項目が見つかりません。")
#         return

#     selected_item3 = st.selectbox(
#         "目標性能",
#         design_item3_values,
#         key="design_item3_unique_key",
#         index=0 if design_item3_values else None
#     )
#     selected_item3 = [selected_item3] if selected_item3 else []

#     # ============================================================
#     #  5.5) Update valid_suffixes and valid_study_ids after 目標性能 selection
#     # ============================================================
    
#     if not selected_item3:
#         st.error("目標性能を選択してください。")
#         return
    
#     # Filter study_ids by selected target performance (senario_id=3)
#     design_item3_filtered_ids = filter_study_ids_by_value(
#         filtered_df,
#         valid_study_ids,
#         senario_id=3,
#         selected_value=selected_item3[0]
#     )
#     # st.write('design_item3_filtered_ids: ', design_item3_filtered_ids)
    
#     # Update valid_study_ids
#     valid_study_ids = design_item3_filtered_ids
    
#     # Update valid_suffixes to only include suffixes with these study_ids
#     updated_suffixes = set()
#     for suffix in valid_suffixes:
#         study_col = get_matching_columns(study_cols, suffix)
#         if study_col:
#             # Check if this suffix has any of the valid_study_ids
#             suffix_study_ids = df[study_col[0]].unique()
#             if any(sid in valid_study_ids for sid in suffix_study_ids if sid and str(sid).strip() not in ("", "nan")):
#                 updated_suffixes.add(suffix)
    
#     valid_suffixes = updated_suffixes
#     # st.write('After 目標性能 - Updated valid_suffixes: ', valid_suffixes)
#     # st.write('After 目標性能 - Updated valid_study_ids: ', valid_study_ids)
    
#     # Re-filter the dataframe with updated suffixes
#     filtered_df = filter_df_by_suffixes(df, valid_suffixes)
#     if filtered_df.empty:
#         st.error("選択された領域、設計項目（大）、設計項目（小）、目標性能に一致する項目が見つかりません。")
#         return

#     # ============================================================
#     #  6) Performance List → Get R List IDs
#     # ============================================================

#     if not selected_area or not selected_item1 or not selected_item2 or not selected_item3:
#         st.error("領域、設計項目（大）、設計項目（小）、目標性能を選択してください。")
#         return

#     info_list = st.session_state.sim_prj_info_list
#     if info_list.empty:
#         st.error("SIMリストの対象Meta情報はありません。")
#         return

#     project_ids = info_list["project_id"].unique().tolist()
#     phase_ids   = info_list["phase_id"].unique().tolist()
#     variation_ids = info_list["variation_id"].unique().tolist()

#     performance_lists = sql.getr_value_to_sim(
#         project_ids,
#         phase_ids,
#         variation_ids,
#         selected_area,
#         selected_item1,
#         selected_item2,
#         selected_item3
#     )
#     if performance_lists.empty:
#         st.error("対象するRリスト情報はありません.")
#         return

#     # Filter performance_lists by selected design items
#     pl_filtered = performance_lists[
#         (performance_lists["design_item_1"].isin(selected_item1)) &
#         (performance_lists["design_item_2"].isin(selected_item2))
#     ]
#     if pl_filtered.empty:
#         st.error("選択された設計項目（大）と設計項目（小）に一致するRリスト情報はありません。")
#         return

#     # ============================================================
#     #  7) Create FIXED Candidate Table
#     # ============================================================

#     selected_ids = pl_filtered["id"].tolist()
#     # st.write('selected_ids: ', selected_ids)
#     if not selected_ids:
#         st.error("No matching performance IDs found for selected design items.")
#         return

#     rfl_cols = [c for c in filtered_df.columns if "rflcategory" in c.lower()]
#     # st.write('rfl_cols: ', rfl_cols)
#     if len(rfl_cols) < 1:
#         st.error("RFL Category columns are missing or insufficient.")
#         return

#     # Keep only rows where any rflcategory == 'R'
#     df_R = filtered_df[(filtered_df[rfl_cols] == "R").any(axis=1)]
#     # st.write('df_R: ', df_R)
#     if df_R.empty:
#         st.error("No rows with rflcategory == 'R'.")
#         return

#     # Build combined dataframe
#     combined_list = []
#     for suffix in valid_suffixes:
#         cols = [c for c in df_R.columns if extract_suffix(c) == suffix]
#         rename_map = {c: c.split(";")[1] for c in cols}
#         combined_list.append(df_R[cols].rename(columns=rename_map))
#     combined_df = pd.concat(combined_list, ignore_index=True)

#     key_cols = ["id", "project_id", "senario_parameter_id", "phase_id", "variation_id", "study_id"]
#     combined_df = combined_df.dropna(subset=key_cols, how="all").reset_index(drop=True)
#     if combined_df.empty:
#         st.error("Combined dataframe is empty after dropping rows without key identifiers.")
#         return

#     # Filter by selected performance IDs
#     fixed_df = combined_df[combined_df["rflid"].isin(selected_ids)]
#     if fixed_df.empty:
#         st.error("No FIXED candidates found for the selected performance IDs.")
#         return

#     # Merge performance metadata
#     perf_info = pl_filtered[["id", "performance", "design_item_1", "design_item_2"]].rename(columns={"id": "rflid"})
#     fixed_df = fixed_df.merge(perf_info, on="rflid", how="left")

#     # Display confirmation
#     st.markdown(
#         "<h3>確認内容</h3>"
#         f"&emsp;領域：{selected_area[0]}<br>"
#         f"&emsp;設計項目（大）：{selected_item1[0]}<br>"
#         f"&emsp;設計項目（小）：{selected_item2[0]}<br>"
#         f"&emsp;目標性能：{selected_item3[0]}<br>",
#         unsafe_allow_html=True
#     )

#     # Display FIXED table
#     go = gop.fixed_sim()
#     st.session_state.Prj_updata = AgGrid(
#         fixed_df,
#         custom_css=css_ag,
#         gridOptions=go,
#         reload_data=False,
#         height=220,
#     )

#     # Execute FIXED
#     if st.button("実行", key="fixed_sim_button_key_2"):
#         selected_rows = st.session_state.Prj_updata["selected_rows"]
#         # if not selected_rows:
#         if selected_rows is None or selected_rows.empty:
#             st.error("FIXEDする項目を選択してください。")
#         elif len(selected_rows) > 1:
#             st.error("1行しかFIXEDできません。")
#         else:
#             ok = sql.update_fixed_r_record(selected_rows)
#             if ok:
#                 execute_sim_list(True)
#             else:
#                 st.error("Failed to update FIXED record.")


# ============================================================
#  Helper Functions for 確定 function start
# ============================================================
def extract_suffix(col_name: str) -> str:
    """Return the last ';'-separated suffix.
    Example: '14;senario_parameter_id;P1提案仕様251117test' -> 'P1提案仕様251117test'
    """
    return col_name.split(";")[-1]

def get_matching_columns(columns, suffix):
    """Return all columns whose suffix matches the given suffix."""
    return [c for c in columns if c.endswith(suffix)]

def collect_valid_suffixes(df, senario_cols, study_cols, value_cols):
    """
    Determine valid study suffixes:
        - parameter 96 must be '有効'
    Returns:
        valid_suffixes (set)
        valid_study_ids (set)
    """
    # Filter rows containing parameter 96
    rows_param96 = df[df[senario_cols].apply(lambda r: 96 in r.values, axis=1)]

    suffix_yukou = {}   # suffix -> study_id

    # Collect "有効" study_ids for parameter 96
    for _, row in rows_param96.iterrows():
        for vcol in value_cols:
            if row[vcol] == "有効":
                suffix = extract_suffix(vcol)
                study_col = get_matching_columns(study_cols, suffix)
                if study_col:
                    sid = row[study_col[0]]
                    if sid and str(sid).strip() not in ("", "nan"):
                        suffix_yukou[suffix] = sid

    # Return all suffixes that are 有効
    valid_suffixes = set(suffix_yukou.keys())
    valid_study_ids = set(suffix_yukou.values())

    return valid_suffixes, valid_study_ids

def filter_suffixes_by_param98(df, suffixes, senario_cols, study_cols, value_cols):
    """
    Filter suffixes by parameter 98:
    - Keep suffixes where parameter 98 value is NOT 'FIXED'
    - Remove suffixes where parameter 98 value IS 'FIXED'
    Returns:
        filtered_suffixes (set)
    """
    if not suffixes:
        return set()
    
    suffixes_to_remove = set()
    
    # Check each suffix for parameter 98 value
    for suffix in suffixes:
        # Find columns with this suffix
        suffix_senario_cols = [scol for scol in senario_cols if extract_suffix(scol) == suffix]
        suffix_value_cols = [vcol for vcol in value_cols if extract_suffix(vcol) == suffix]
        
        if not suffix_senario_cols or not suffix_value_cols:
            # If no matching columns, keep the suffix (no parameter 98 data)
            continue
        
        # Check rows where this suffix has parameter 98
        found_fixed = False
        for _, row in df.iterrows():
            # Check if this row has parameter 98 for this suffix
            for s_col in suffix_senario_cols:
                if pd.notna(row[s_col]) and row[s_col] == 98:
                    # Found parameter 98, check corresponding value column
                    # The value column should have the same prefix (before the suffix)
                    # Extract prefix from senario column: e.g., "14;senario_parameter_id;P1..." -> "14"
                    s_prefix = s_col.split(";")[0] if ";" in s_col else None
                    if s_prefix:
                        # Find value column with same prefix and suffix
                        for v_col in suffix_value_cols:
                            v_prefix = v_col.split(";")[0] if ";" in v_col else None
                            if v_prefix == s_prefix:
                                # Check if value is 'FIXED'
                                if pd.notna(row[v_col]) and row[v_col] == 'FIXED':
                                    suffixes_to_remove.add(suffix)
                                    found_fixed = True
                                    break
                    if found_fixed:
                        break
            if found_fixed:
                break
    
    # Return suffixes that are NOT in the removal set
    return suffixes - suffixes_to_remove

def filter_df_by_suffixes(df, suffixes):
    """Keep only columns whose suffix is in the given suffix set."""
    valid_cols = [c for c in df.columns if extract_suffix(c) in suffixes]
    return df[valid_cols]

def get_dropdown_values(df, study_ids, senario_id):
    """Return sorted dropdown values for a parameter from valid study_ids."""
    if not study_ids:
        return []

    senario_cols = [c for c in df.columns if "senario_parameter_id" in c]
    study_cols = [c for c in df.columns if "study_id" in c]
    value_cols = [c for c in df.columns if ";value;" in c]

    # Filter rows having the target senario_id
    rows = df[df[senario_cols].apply(lambda r: senario_id in r.values, axis=1)]

    values = set()
    for _, row in rows.iterrows():
        for vcol in value_cols:
            suffix = extract_suffix(vcol)
            study_col = get_matching_columns(study_cols, suffix)
            if study_col and row[study_col[0]] in study_ids:
                values.add(row[vcol])

    return sorted(values)

def filter_study_ids_by_value(df, study_ids, senario_id, selected_value):
    """Return study_ids that have the selected_value under given senario_id."""
    if not selected_value:
        return set()

    senario_cols = [c for c in df.columns if "senario_parameter_id" in c]
    study_cols = [c for c in df.columns if "study_id" in c]
    value_cols = [c for c in df.columns if ";value;" in c]

    rows = df[df[senario_cols].apply(lambda r: senario_id in r.values, axis=1)]

    result_ids = set()
    for _, row in rows.iterrows():
        for vcol in value_cols:
            if row[vcol] == selected_value:
                suffix = extract_suffix(vcol)
                study_col = get_matching_columns(study_cols, suffix)
                if study_col:
                    sid = row[study_col[0]]
                    if sid in study_ids:
                        result_ids.add(sid)

    return result_ids
# ============================================================
#  Helper Functions for 確定 function end
# ============================================================


@st.dialog("設計値確定") #updated ver 17:15 Only 有効
def choice_sim_fixed():
    
    # ============================================================
    #  1) Load Data
    # ============================================================

    df = st.session_state.sim_data_stuck
    if df.empty:
        st.error("選択されたSIMリスト情報はありません。")
        return

    senario_cols = [c for c in df.columns if "senario_parameter_id" in c]
    study_cols   = [c for c in df.columns if "study_id" in c]
    value_cols   = [c for c in df.columns if ";value;" in c]

    # Determine valid suffixes / study_ids
    valid_suffixes, valid_study_ids = collect_valid_suffixes(df, senario_cols, study_cols, value_cols)
    if not valid_suffixes:
        st.error("有効データがありません。確定したいスタディデータを有効にしてください。")
        return

    # Restrict DF to only valid suffixes
    filtered_df = filter_df_by_suffixes(df, valid_suffixes)
    if filtered_df.empty:
        # st.error("Filtered dataframe is empty after applying valid suffixes.")
        st.error("有効データがありません。確定したいスタディデータを有効にしてください。")
        return

    # ============================================================
    #  2) Dropdown: Performance Area (senario_id = 15)
    # ============================================================

    area_values = get_dropdown_values(filtered_df, valid_study_ids, senario_id=15)
    # Remove 'PTシステムレビュー向け全R項目' if it exists
    area_values = [v for v in area_values if v != 'PTシステムレビュー向け全R項目']
    if not area_values:
        # st.error("No Performance Area (領域) options available.")
        st.error("有効データがありません。確定したいスタディデータを有効にしてください。")
        return

    selected_area = st.selectbox(
        "領域",
        area_values,
        key="selected_area_unique_key",
        index=0 if area_values else None
    )
    selected_area = [selected_area] if selected_area else []

    # ============================================================
    #  2.5) Update valid_suffixes and valid_study_ids after 領域 selection
    # ============================================================
    
    if not selected_area:
        st.error("領域を選択してください。")
        return
    
    # Filter study_ids by selected area (senario_id=15)
    area_filtered_ids = filter_study_ids_by_value(
        filtered_df,
        valid_study_ids,
        senario_id=15,
        selected_value=selected_area[0]
    )
    # st.write('area_filtered_ids: ', area_filtered_ids)
    
    # Update valid_study_ids
    valid_study_ids = area_filtered_ids
    
    # Update valid_suffixes to only include suffixes with these study_ids
    updated_suffixes = set()
    for suffix in valid_suffixes:
        study_col = get_matching_columns(study_cols, suffix)
        if study_col:
            # Check if this suffix has any of the valid_study_ids
            suffix_study_ids = df[study_col[0]].unique()
            if any(sid in valid_study_ids for sid in suffix_study_ids if sid and str(sid).strip() not in ("", "nan")):
                updated_suffixes.add(suffix)
    
    valid_suffixes = updated_suffixes
    # st.write('After 領域 - Updated valid_suffixes: ', valid_suffixes)
    # st.write('After 領域 - Updated valid_study_ids: ', valid_study_ids)
    
    # Re-filter the dataframe with updated suffixes
    filtered_df = filter_df_by_suffixes(df, valid_suffixes)
    if filtered_df.empty:
        st.error("選択された領域に一致する項目が見つかりません。")
        return

    # ============================================================
    #  3) Dropdown: 設計項目（大）(senario_parameter_id = 56)
    # ============================================================

    item1_values = get_dropdown_values(
        filtered_df, valid_study_ids, senario_id=56
    )
    if not item1_values:
        st.error("選択された領域に対して有効の設計項目（大）の項目が見つかりません。")
        return

    selected_item1 = st.selectbox(
        "設計項目（大）",
        item1_values,
        key="selected_perf1_unique_key",
        index=0 if item1_values else None
    )
    selected_item1 = [selected_item1] if selected_item1 else []

    # ============================================================
    #  3.5) Update valid_suffixes and valid_study_ids after 設計項目（大）selection
    # ============================================================
    
    if not selected_item1:
        st.error("設計項目（大）を選択してください。")
        return
    
    # Filter study_ids by selected design item 1 (senario_parameter_id=56)
    item1_filtered_ids = filter_study_ids_by_value(
        filtered_df,
        valid_study_ids,
        senario_id=56,
        selected_value=selected_item1[0]
    )
    # st.write('item1_filtered_ids: ', item1_filtered_ids)
    
    # Update valid_study_ids
    valid_study_ids = item1_filtered_ids
    
    # Update valid_suffixes to only include suffixes with these study_ids
    updated_suffixes = set()
    for suffix in valid_suffixes:
        study_col = get_matching_columns(study_cols, suffix)
        if study_col:
            # Check if this suffix has any of the valid_study_ids
            suffix_study_ids = df[study_col[0]].unique()
            if any(sid in valid_study_ids for sid in suffix_study_ids if sid and str(sid).strip() not in ("", "nan")):
                updated_suffixes.add(suffix)
    
    valid_suffixes = updated_suffixes
    # st.write('After 設計項目（大） - Updated valid_suffixes: ', valid_suffixes)
    # st.write('After 設計項目（大） - Updated valid_study_ids: ', valid_study_ids)
    
    # Re-filter the dataframe with updated suffixes
    filtered_df = filter_df_by_suffixes(df, valid_suffixes)
    if filtered_df.empty:
        st.error("選択された領域と設計項目（大）に一致する項目が見つかりません。")
        return

    # ============================================================
    #  4) Dropdown: 設計項目（小）(senario_parameter_id = 57)
    # ============================================================

    item2_values = get_dropdown_values(
        filtered_df, valid_study_ids, senario_id=57
    )
    if not item2_values:
        st.error("選択された領域と設計項目（大）に対して有効の設計項目（小）の項目が見つかりません。")
        return

    selected_item2 = st.selectbox(
        "設計項目（小）",
        item2_values,
        key="selected_perf2_unique_key",
        index=0 if item2_values else None
    )
    selected_item2 = [selected_item2] if selected_item2 else []

    # ============================================================
    #  4.5) Update valid_suffixes and valid_study_ids after 設計項目（小）selection
    # ============================================================
    
    if not selected_item2:
        st.error("設計項目（小）を選択してください。")
        return
    
    # Filter study_ids by selected design item 2 (senario_parameter_id=57)
    item2_filtered_ids = filter_study_ids_by_value(
        filtered_df,
        valid_study_ids,
        senario_id=57,
        selected_value=selected_item2[0]
    )
    # st.write('item2_filtered_ids: ', item2_filtered_ids)
    
    # Update valid_study_ids
    valid_study_ids = item2_filtered_ids
    
    # Update valid_suffixes to only include suffixes with these study_ids
    updated_suffixes = set()
    for suffix in valid_suffixes:
        study_col = get_matching_columns(study_cols, suffix)
        if study_col:
            # Check if this suffix has any of the valid_study_ids
            suffix_study_ids = df[study_col[0]].unique()
            if any(sid in valid_study_ids for sid in suffix_study_ids if sid and str(sid).strip() not in ("", "nan")):
                updated_suffixes.add(suffix)
    
    valid_suffixes = updated_suffixes
    # st.write('After 設計項目（小） - Updated valid_suffixes: ', valid_suffixes)
    # st.write('After 設計項目（小） - Updated valid_study_ids: ', valid_study_ids)
    
    # Re-filter the dataframe with updated suffixes
    filtered_df = filter_df_by_suffixes(df, valid_suffixes)
    if filtered_df.empty:
        st.error("選択された領域、設計項目（大）、設計項目（小）に一致する項目が見つかりません。")
        return

    # ============================================================
    #  5) Dropdown: Target Performance (senario_id = 3)
    # ============================================================

    design_item3_values = get_dropdown_values(
        filtered_df, valid_study_ids, senario_id=3
    )
    if not design_item3_values:
        st.error("選択された領域、設計項目（大）、設計項目（小）に対して有効の目標性能の項目が見つかりません。")
        return

    selected_item3 = st.selectbox(
        "目標性能",
        design_item3_values,
        key="design_item3_unique_key",
        index=0 if design_item3_values else None
    )
    selected_item3 = [selected_item3] if selected_item3 else []

    # ============================================================
    #  5.5) Update valid_suffixes and valid_study_ids after 目標性能 selection
    # ============================================================
    
    if not selected_item3:
        st.error("目標性能を選択してください。")
        return
    
    # Filter study_ids by selected target performance (senario_id=3)
    design_item3_filtered_ids = filter_study_ids_by_value(
        filtered_df,
        valid_study_ids,
        senario_id=3,
        selected_value=selected_item3[0]
    )
    # st.write('design_item3_filtered_ids: ', design_item3_filtered_ids)
    
    # Update valid_study_ids
    valid_study_ids = design_item3_filtered_ids
    
    # Update valid_suffixes to only include suffixes with these study_ids
    updated_suffixes = set()
    for suffix in valid_suffixes:
        study_col = get_matching_columns(study_cols, suffix)
        if study_col:
            # Check if this suffix has any of the valid_study_ids
            suffix_study_ids = df[study_col[0]].unique()
            if any(sid in valid_study_ids for sid in suffix_study_ids if sid and str(sid).strip() not in ("", "nan")):
                updated_suffixes.add(suffix)
    
    valid_suffixes = updated_suffixes
    # st.write('After 目標性能 - Updated valid_suffixes: ', valid_suffixes)
    # st.write('After 目標性能 - Updated valid_study_ids: ', valid_study_ids)
    
    # Re-filter the dataframe with updated suffixes
    filtered_df = filter_df_by_suffixes(df, valid_suffixes)
    if filtered_df.empty:
        print('error 1')
        st.error("選択された領域、設計項目（大）、設計項目（小）、目標性能に一致する項目が見つかりません。")
        return
    
    # Filter suffixes by parameter 98: remove suffixes where parameter 98 value is 'FIXED'
    # Use filtered_df and get columns from filtered_df
    filtered_senario_cols = [c for c in filtered_df.columns if "senario_parameter_id" in c]
    filtered_study_cols = [c for c in filtered_df.columns if "study_id" in c]
    filtered_value_cols = [c for c in filtered_df.columns if ";value;" in c]
    valid_suffixes = filter_suffixes_by_param98(filtered_df, valid_suffixes, filtered_senario_cols, filtered_study_cols, filtered_value_cols)
    # st.write('After parameter 98 filter - Updated valid_suffixes: ', valid_suffixes)
    
    # Re-filter the dataframe with updated suffixes after parameter 98 filter
    filtered_df = filter_df_by_suffixes(df, valid_suffixes)
    if filtered_df.empty:
        print('error 2')
        # st.error("選択された領域、設計項目（大）、設計項目（小）、目標性能に一致する項目が見つかりません。")
        st.error('選択した条件（目標性能）は現在『確定』状態です。')
        return

    # ============================================================
    #  6) Performance List → Get R List IDs
    # ============================================================

    if not selected_area or not selected_item1 or not selected_item2 or not selected_item3:
        st.error("領域、設計項目（大）、設計項目（小）、目標性能を選択してください。")
        return

    info_list = st.session_state.sim_prj_info_list
    if info_list.empty:
        st.error("SIMリストの対象Meta情報はありません。")
        return

    project_ids = info_list["project_id"].unique().tolist()
    phase_ids   = info_list["phase_id"].unique().tolist()
    variation_ids = info_list["variation_id"].unique().tolist()

    performance_lists = sql.getr_value_to_sim(
        project_ids,
        phase_ids,
        variation_ids,
        selected_area,
        selected_item1,
        selected_item2,
        selected_item3
    )
    if performance_lists.empty:
        st.error("対象するRリスト情報はありません.")
        return

    # # Filter performance_lists by selected design items
    # pl_filtered = performance_lists[
    #     (performance_lists["area"].isin(selected_area)) &
    #     (performance_lists["design_item_1"].isin(selected_item1)) &
    #     (performance_lists["design_item_2"].isin(selected_item2)) &
    #     (performance_lists["performance"].isin(selected_item3))
    # ]
    # if pl_filtered.empty:
    #     st.error("選択された領域、設計項目（大）、設計項目（小）、目標性能に一致するRリスト情報はありません。")
    #     return

    # ============================================================
    #  7) Create FIXED Candidate Table
    # ============================================================

    selected_ids = performance_lists["id"].tolist()
    # st.write('selected_ids: ', selected_ids)
    if not selected_ids:
        print('error 3')
        # st.error("No matching performance IDs found for selected design items.")
        st.error('選択された領域、設計項目（大）、設計項目（小）、目標性能に一致するR項目が見つかりません。')
        return

    rfl_cols = [c for c in filtered_df.columns if "rflcategory" in c.lower()]
    # st.write('rfl_cols: ', rfl_cols)
    if len(rfl_cols) < 1:
        print('error 4')
        # st.error("RFL Category columns are missing or insufficient.")
        st.error('選択された領域、設計項目（大）、設計項目（小）、目標性能に一致するR項目が見つかりません。')
        return

    # Keep only rows where any rflcategory == 'R'
    df_R = filtered_df[(filtered_df[rfl_cols] == "R").any(axis=1)]
    # st.write('df_R: ', df_R)
    if df_R.empty:
        # st.error("No rows with rflcategory == 'R'.")
        st.error('選択された領域、設計項目（大）、設計項目（小）、目標性能に一致するR項目が見つかりません。')
        return

    # Build combined dataframe
    combined_list = []
    for suffix in valid_suffixes:
        cols = [c for c in df_R.columns if extract_suffix(c) == suffix]
        rename_map = {c: c.split(";")[1] for c in cols}
        combined_list.append(df_R[cols].rename(columns=rename_map))
    combined_df = pd.concat(combined_list, ignore_index=True)

    key_cols = ["id", "project_id", "senario_parameter_id", "phase_id", "variation_id", "study_id"]
    combined_df = combined_df.dropna(subset=key_cols, how="all").reset_index(drop=True)
    if combined_df.empty:
        # st.error("Combined dataframe is empty after dropping rows without key identifiers.")
        st.error('選択された領域、設計項目（大）、設計項目（小）、目標性能に一致するR項目が見つかりません。')
        return

    # Filter by selected performance IDs
    fixed_df = combined_df[combined_df["rflid"].isin(selected_ids)]
    if fixed_df.empty:
        # st.error("No FIXED candidates found for the selected performance IDs.")
        st.error("選択された領域、設計項目（大）、設計項目（小）、目標性能に一致するR項目が見つかりません。")
        return

    # Merge performance metadata
    perf_info = performance_lists[["id", "performance", "design_item_1", "design_item_2"]].rename(columns={"id": "rflid"})
    fixed_df = fixed_df.merge(perf_info, on="rflid", how="left")

    # Display confirmation
    st.markdown(
        "<h3>確認内容</h3>"
        f"&emsp;領域：{selected_area[0]}<br>"
        f"&emsp;設計項目（大）：{selected_item1[0]}<br>"
        f"&emsp;設計項目（小）：{selected_item2[0]}<br>"
        f"&emsp;目標性能：{selected_item3[0]}<br>",
        unsafe_allow_html=True
    )

    # Display FIXED table
    go = gop.fixed_sim()
    st.session_state.Prj_updata = AgGrid(
        fixed_df,
        custom_css=css_ag,
        gridOptions=go,
        reload_data=False,
        height=220,
    )

    # Execute FIXED
    if st.button("実行", key="fixed_sim_button_key_2"):
        selected_rows = st.session_state.Prj_updata["selected_rows"]
        # if not selected_rows:
        if selected_rows is None or selected_rows.empty:
            st.error("FIXEDする項目を選択してください。")
        elif len(selected_rows) > 1:
            st.error("1行しかFIXEDできません。")
        else:
            ok = sql.update_fixed_r_record(selected_rows)
            if ok:
                execute_sim_list(True)
            else:
                st.error("Failed to update FIXED record.")





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

# #telema-kyaw  #11/05
# @st.dialog("RFL編集終了確認", width="large")
# def off_rfl_edit():
#     """RFL編集モード
#     """
#     st.write('編集モードを終了します　')
#     st.write('編集内容を確定しますか？')

#     # Reset index for alignment
#     original_df = st.session_state[f'org_rfl_pj_0'].reset_index(drop=True)
#     response_df = st.session_state[f'rfl_pj_response_0'].reset_index(drop=True)

#     original_df = original_df.drop(columns=['rfl_id','phase'], errors='ignore')
#     response_df = response_df.drop(columns=['rfl_id','phase'], errors='ignore')

#     # List of prefixes to remove
#     prefixes = ('c_', 's_', 'u_')

#     # Rename columns by removing these prefixes
#     original_df.rename(columns=lambda x: re.sub(r'^(c_|s_|u_)', '', x), inplace=True)
#     response_df.rename(columns=lambda x: re.sub(r'^(c_|s_|u_)', '', x), inplace=True)

#     # # Pattern to match columns containing 'sender_date' or 'receiver_date'
#     # date_pattern = re.compile(r'(sender_date|receiver_date)', re.IGNORECASE)

#     # # Select columns matching the pattern
#     # date_columns = [col for col in original_df.columns if date_pattern.search(col)]
    
#     # st.write("date_columns:", date_columns)
#     # Convert date columns to datetime for both DataFrames
#     date_columns = ['sender_date', 'receiver_date']
#     for col in date_columns:
#         original_df[col] = pd.to_datetime(original_df[col], errors='coerce')
#         response_df[col] = pd.to_datetime(response_df[col], errors='coerce')

#         original_df[col] = original_df[col].fillna(pd.Timestamp('1900-01-01'))
#         response_df[col] = response_df[col].fillna(pd.Timestamp('1900-01-01'))

#     # Optional: convert all other columns to string to avoid mismatches due to data types
#     for col in original_df.columns:
#         if col not in date_columns:
#             original_df[col] = original_df[col].astype(str)
#             response_df[col] = response_df[col].astype(str)

#     # st.write("original_df:", original_df)
#     # st.write("response_df:", response_df)

#     # st.write("Original last row:", original_df.iloc[-1])
#     # st.write("Response last row:", response_df.iloc[-1])

#     # st.write("Original last row dtypes:", original_df.iloc[-1].dtype)
#     # st.write("Response last row dtypes:", response_df.iloc[-1].dtype)

#     # diff = original_df.iloc[-1] != response_df.iloc[-1]
#     # st.write("Differences in last row:", diff)

#     # Now compare row-wise
#     # Create a boolean Series indicating if any column differs in each row
#     # diff_mask = (original_df != response_df).any(axis=1)

#     # # Select only the rows that are different
#     # rfl_changed_rows_df = response_df[diff_mask]

#     # st.write("Differences:", rfl_changed_rows_df)
#     # -------------------------------------------------------
#     # # Boolean DataFrame: True where values differ
#     # diff_cells = original_df != response_df

#     # # Boolean Series: True for rows where any column differs
#     # diff_rows = diff_cells.any(axis=1)

#     # # DataFrame with only the changed rows
#     # rfl_changed_rows_df = response_df[diff_rows].copy()
#     # st.write("Changed rows:", rfl_changed_rows_df)

#     # # DataFrame with only the columns that changed
#     # changed_columns_df = response_df[diff_rows].loc[:, diff_cells.any(axis=0)]
#     # st.write("Changed columns only:", changed_columns_df)

#     # # Optional: create a side-by-side diff view (Original vs New) for changed cells
#     # diff_side_by_side = pd.DataFrame()
#     # for col in changed_columns_df.columns:
#     #     diff_side_by_side[col + "_original"] = original_df.loc[diff_rows, col]
#     #     diff_side_by_side[col + "_new"] = response_df.loc[diff_rows, col]

#     # st.write("Changes side-by-side (original vs new):", diff_side_by_side)
#     # ----------------------------------------------------

#     # ------------------------------
#     # Compare row-wise and column-wise
#     # ------------------------------

#     # Boolean DataFrame: True where values differ
#     diff_cells = original_df != response_df

#     # Boolean Series: True for rows where any column differs
#     diff_rows = diff_cells.any(axis=1)

#     # Columns that changed
#     changed_cols_only = diff_cells.any(axis=0)
#     changed_cols_list = list(changed_cols_only[changed_cols_only].index)

#     # Include key identifier columns
#     key_columns = ['r_pj_id', 'phase_id', 'rfl_id', 'r_s_id','l_s_id','f_id']
#     for key in key_columns:
#         if key in original_df.columns and key not in changed_cols_list:
#             changed_cols_list.insert(0, key)  # insert keys at the beginning

#     # DataFrame with only changed columns + key identifiers
#     changed_columns_df = response_df.loc[diff_rows, changed_cols_list].copy()

#     # st.write("Changed columns before:", changed_columns_df)

#     # Mask unchanged values with None
#     for col in changed_columns_df.columns:
#         if col not in key_columns:
#             # Replace unchanged values with None
#             mask = diff_cells.loc[changed_columns_df.index, col]
#             changed_columns_df.loc[~mask, col] = None

#     # st.write("Changed columns after:", changed_columns_df)

#     # Convert unit values to unit IDs (only for f_unit and l_unit, not r_unit)
#     # r_unit comes from r_parameter table and doesn't need ID conversion
#     unit_columns = ['f_unit', 'l_unit']
#     units_dict = rflq.get_units_dict()
    
#     for unit_col in unit_columns:
#         if unit_col in changed_columns_df.columns:
#             unit_id_col = unit_col + '_id'
#             # Convert unit values to IDs, only for non-None values
#             changed_columns_df[unit_id_col] = changed_columns_df[unit_col].apply(
#                 lambda x: units_dict.get(x) if x is not None and pd.notna(x) and str(x) != 'nan' else None
#             )
#             # Only keep unit_id where unit value was actually changed
#             mask = diff_cells.loc[changed_columns_df.index, unit_col]
#             changed_columns_df.loc[~mask, unit_id_col] = None

#     # Convert allocation (WP) values to WP IDs
#     allocation_column = 'l_wp'
#     if allocation_column in changed_columns_df.columns:
#         wp_dict = rflq.get_wp_dict()
#         wp_id_col = 'l_wp_id'
#         # Convert WP values to IDs, only for non-None values
#         changed_columns_df[wp_id_col] = changed_columns_df[allocation_column].apply(
#             lambda x: wp_dict.get(x) if x is not None and pd.notna(x) and str(x) != 'nan' else None
#         )
#         # Only keep wp_id where allocation value was actually changed
#         mask = diff_cells.loc[changed_columns_df.index, allocation_column]
#         changed_columns_df.loc[~mask, wp_id_col] = None

#     # st.write("Changed columns with unit IDs and WP IDs:", changed_columns_df)

#     # # --- Drop completely empty rows (in case there are any)
#     # rfl_changed_rows_df = changed_columns_df.dropna(how="all", subset=['note', 'log_condition'])

#     # st.write("rfl_changed_rows_df:", rfl_changed_rows_df)

#     # # --- Separate DataFrames for each column update ---
#     # note_df = rfl_changed_rows_df[['r_pj_id', 'phase_id', 'rfl_id', 'note']].dropna(subset=['note'])
#     # log_condition_df = rfl_changed_rows_df[['rfl_id', 'log_condition']].dropna(subset=['log_condition'])
#     # st.write("note_df:", note_df)
#     # st.write("log_condition_df:", log_condition_df)


#     if st.button("確定する"):
#         if changed_columns_df.empty:
#             st.error("編集内容がありません。")
#         else:
#             st.session_state.rfl_edit_state = False
#             # rfl_org_pattern = r'^org_rfl_pj_\d+'
#             # rfl_res_pattern = r'^rfl_pj_response_\d+'

            
#             rfl_upd_res = sql.update_rfl_infos(changed_columns_df,original_df)

#             print('rfl_upd_res:', rfl_upd_res)

#             if not rfl_upd_res:
#                 st.error("RFL情報の更新に失敗しました。")
#             else:
#                 # DB更新後の表を表示 
#                 df=rflq.posgre_get_rfl_tlm(
#                     st.session_state['selectoption1'],
#                     st.session_state['selectoption2'],
#                     st.session_state['selectoption3'],
#                     st.session_state['selectoption4'],
#                     st.session_state['selectoption5'],
#                     st.session_state['selected_hr'],
#                     st.session_state['wp'],
#                 )
#                 st.session_state.rfl_list = df

#                 rfl_all_info = sql.posgre_get_rfl(
#                     st.session_state['selectoption1'],
#                     st.session_state['selectoption2'],
#                     st.session_state['selectoption3'],
#                     st.session_state['selectoption4'],
#                     st.session_state['selectoption5']
#                 )
#                 st.session_state.rfl_matrix = rfl_all_info

#                 st.session_state.edit_refresh = True
#                 time.sleep(0.5)
#                 st.rerun()
#             # # Loop over all keys
#             # for key in st.session_state:
#             #     if key.startswith("org_rfl_pj_"):
#             #         i = key.split("_")[-1]  # get the index
#             #         org_df = st.session_state[key]
#             #         response_key = f"rfl_pj_response_{i}"
#             #         response_df = st.session_state.get(response_key, None)

#             #         st.write(f"Index i = {i}")
#             #         st.write(f"{key}:")
#             #         st.dataframe(org_df)  # display DataFrame

#             #         if response_df is not None:
#             #             st.write(f"{response_key}:")
#             #             st.dataframe(response_df)  # display DataFrame
#             #         else:
#             #             st.write(f"{response_key}: No response found")
#             #         st.write("---")  # separator

#             # # 元のDFとresponseのDFのKeyを取得
#             # rfl_keys_org = get_matching_key(rfl_org_pattern)
#             # rfl_keys_res = get_matching_key(rfl_res_pattern)

#             # # originalとeditDFから差分を取得
#             # diff_cells = RFLDataProcesser.compare_dataframes(rfl_keys_org[0],rfl_keys_res[0])
#             # print(diff_cells)
#             # # 差分をUPDATE
#             # [rflq.update_rfl (cell['project_id'],cell['rfl_id'],cell['phase_id'],cell['diff_col'],cell['diff_value']) for cell in diff_cells]

#             # # DB更新後の表を表示 
#             # df=rflq.posgre_get_rfl_tlm(
#             #     st.session_state['selectoption1'],
#             #     st.session_state['selectoption2'],
#             #     st.session_state['selectoption3'],
#             #     st.session_state['selectoption4'],
#             #     st.session_state['selectoption5'],
#             #     st.session_state['selected_hr'],
#             #     st.session_state['wp'],
#             # )
#             # st.session_state.rfl_list = df

#             # rfl_all_info = sql.posgre_get_rfl(
#             #     st.session_state['selectoption1'],
#             #     st.session_state['selectoption2'],
#             #     st.session_state['selectoption3'],
#             #     st.session_state['selectoption4'],
#             #     st.session_state['selectoption5']
#             # )
#             # st.session_state.rfl_matrix = rfl_all_info

#             # st.session_state.edit_refresh = True
#             # st.rerun()

#     if st.button("破棄する"):
#         st.session_state.rfl_edit_state = False

#         # db更新無し 表示を元に戻す
#         df=rflq.posgre_get_rfl_tlm(
#             st.session_state['selectoption1'],
#             st.session_state['selectoption2'],
#             st.session_state['selectoption3'],
#             st.session_state['selectoption4'],
#             st.session_state['selectoption5'],
#             st.session_state['selected_hr'],
#             st.session_state['wp'],
#         )
#         st.session_state.rfl_list = df
#         st.session_state.edit_refresh = True
#         st.rerun()

#     if st.button("キャンセル"):
#         st.session_state.rfl_edit_state = True
#         st.rerun()


# #telema-kyaw  #11/05 updated 11/19
# @st.dialog("RFL編集終了確認", width="large")
# def off_rfl_edit():
#     """
#     RFL Edit Mode Confirmation Dialog
    
#     This function detects changes made by the user in the RFL grid and
#     creates a DataFrame for database updates.
    
#     Processing flow:
#     1. Compare original data (original_df) with edited data (response_df)
#     2. Detect changes for each hierarchy (c_, s_, u_)
#     3. Consolidate changed rows into a single DataFrame (remove prefixes)
#     4. Convert unit and WP values to IDs
#     5. Execute database update
#     """
#     st.write('編集モードを終了します　')
#     st.write('編集内容を確定しますか？')

#     # ============================================================
#     # Step 1: Data Preparation
#     # ============================================================
#     # Get original and edited data from session state
#     # reset_index(drop=True) resets the index to align row positions
#     original_df = st.session_state[f'org_rfl_pj_0'].reset_index(drop=True)
#     response_df = st.session_state[f'rfl_pj_response_0'].reset_index(drop=True)

#     # Drop unnecessary columns (rfl_id and phase are not needed for comparison), not to duplicate cols
#     original_df = original_df.drop(columns=['rfl_id','phase'], errors='ignore')
#     response_df = response_df.drop(columns=['rfl_id','phase'], errors='ignore')

#     # st.write('original_df: ', original_df)
#     # st.write('response_df: ', response_df)

#     # ============================================================
#     # Step 2: Configuration Definition
#     # ============================================================
#     # Hierarchy prefixes to process: c_=Vehicle, s_=System, u_=Unit
#     prefixes = ['c_', 's_', 'u_']
    
#     # Base column names (after prefix removal) to consolidate
#     # These columns will be consolidated into a single DataFrame by removing prefixes
#     base_columns = {
#         'req', 'func', 'logic', 'note', 'r_item', 'f_item', 'l_item', 
#         'r_unit', 'f_unit', 'l_unit', 'r_scene', 'l_scene',
#         'req_condition', 'log_condition',
#         'sender_judge', 'sender_name', 'sender_date', 'sender_comment',
#         'receiver_judge', 'receiver_name', 'receiver_date', 'receiver_comment',
#         'l_wp'
#     }
    
#     # Key columns (identifiers required for database updates)
#     # These columns are required for each hierarchy and are preserved after consolidation
#     key_base_names = ['r_pj_id', 'phase_id', 'rfl_id', 'r_s_id', 'l_s_id', 'f_id']
    
#     # Date columns (require special handling)
#     # Dates must be compared as datetime type, not as strings
#     date_base_names = ['sender_date', 'receiver_date']
    
#     # List to store consolidated rows
#     # A single DataFrame will be created from this list at the end
#     consolidated_rows = []
    
#     # ============================================================
#     # Step 3: Detect Changes for Each Hierarchy
#     # ============================================================
#     for prefix in prefixes:
#         # Get only columns that are in base_columns (with prefix) and their _id columns
#         # Also include key columns for identification
#         prefix_cols = []
        
#         # Add base columns with prefix (e.g., 'c_req', 'c_func', etc.)
#         for base_col in base_columns:
#             prefixed_col = f'{prefix}{base_col}'
#             if prefixed_col in original_df.columns:
#                 prefix_cols.append(prefixed_col)
#             # Also add _id version if it exists (e.g., 'c_f_unit_id', 'c_l_unit_id')
#             prefixed_id_col = f'{prefix}{base_col}_id'
#             if prefixed_id_col in original_df.columns:
#                 prefix_cols.append(prefixed_id_col)
        
#         # Add key columns (required for identification)
#         for key_base in key_base_names:
#             prefixed_key = f'{prefix}{key_base}'
#             if prefixed_key in original_df.columns:
#                 prefix_cols.append(prefixed_key)
        
#         # Skip if no columns exist for this hierarchy
#         if not prefix_cols:
#             continue
#         # st.write('response df: ', response_df)
#         # st.write('prefix_cols: ', prefix_cols)
#         # ============================================================
#         # Step 3.1: Extract Data for This Hierarchy Only
#         # ============================================================
#         # Extract only columns for this hierarchy from original and edited data
#         prefix_original = original_df[prefix_cols].copy()
#         prefix_response = response_df[prefix_cols].copy()
        
#         # ============================================================
#         # Step 3.2: Process Date Columns
#         # ============================================================
#         # Date columns must be compared as datetime type, not as strings
#         # Example: convert 'c_sender_date', 'c_receiver_date' to datetime type
#         for date_base in date_base_names:
#             date_col = f'{prefix}{date_base}'
#             if date_col in prefix_original.columns:
#                 # # Replace None values explicitly before conversion
#                 # prefix_original[date_col] = prefix_original[date_col].replace([None], pd.NaT)
#                 # prefix_response[date_col] = prefix_response[date_col].replace([None], pd.NaT)
#                 # Convert date strings to datetime type (becomes NaT on error or None)
#                 prefix_original[date_col] = pd.to_datetime(prefix_original[date_col], errors='coerce')
#                 prefix_response[date_col] = pd.to_datetime(prefix_response[date_col], errors='coerce')
#                 # Replace NaT (Not a Time) and None with 1700-01-01 to make comparison possible
#                 prefix_original[date_col] = prefix_original[date_col].fillna(pd.Timestamp('1700-01-01'))
#                 prefix_response[date_col] = prefix_response[date_col].fillna(pd.Timestamp('1700-01-01'))
        
        
#         # ============================================================
#         # Step 3.3: Convert Other Columns to String
#         # ============================================================
#         # Convert non-date columns to string for comparison
#         # This prevents comparison errors due to differences in numeric or other types
#         for col in prefix_original.columns:
#             if col not in [f'{prefix}{d}' for d in date_base_names]:
#                 prefix_original[col] = prefix_original[col].astype(str)
#                 prefix_response[col] = prefix_response[col].astype(str)
        
#         # ============================================================
#         # Step 3.4: Detect Changes
#         # ============================================================
#         # Compare cell by cell: True = values differ, False = values are same
#         prefix_diff_cells = prefix_original != prefix_response
        
#         # Check for changes row by row: True if any column in the row differs
#         prefix_diff_rows = prefix_diff_cells.any(axis=1)
        
#         # Skip to next hierarchy if no changes in this hierarchy
#         if not prefix_diff_rows.any():
#             continue
        
#         # ============================================================
#         # Step 3.5: Identify Changed Columns
#         # ============================================================
#         # Check for changes column by column: True if any row in the column differs
#         prefix_changed_cols = prefix_diff_cells.any(axis=0)
#         # Get list of column names that have changes
#         prefix_changed_cols_list = list(prefix_changed_cols[prefix_changed_cols].index)
        
#         # Add key columns (required even if not changed)
#         # Ensure identifiers needed for database updates are included
#         for key_base in key_base_names:
#             prefixed_key = f'{prefix}{key_base}'
#             # Add only if key column exists and is not already in the list
#             if prefixed_key in prefix_response.columns and prefixed_key not in prefix_changed_cols_list:
#                 prefix_changed_cols_list.insert(0, prefixed_key)  # Insert at beginning
        
#         # Filter out columns that don't actually exist
#         # Example: exclude columns like 's_r_item_index' that may have been added later
#         prefix_changed_cols_list = [col for col in prefix_changed_cols_list if col in prefix_response.columns]
        
#         # ============================================================
#         # Step 3.6: Extract Only Changed Rows and Columns
#         # ============================================================
#         # Extract only rows that have changes, containing only changed columns
#         prefix_changed_df = prefix_response.loc[prefix_diff_rows, prefix_changed_cols_list].copy()
        
#         # ============================================================
#         # Step 3.7: Mask Unchanged Cells as None
#         # ============================================================
#         # For rows with changes, set unchanged column values to None
#         # This ensures only actually changed values remain
#         for col in prefix_changed_df.columns:
#             # Key columns are always kept (not set to None)
#             if col not in [f'{prefix}{k}' for k in key_base_names]:
#                 # Create mask where True indicates changed cells for this column
#                 mask = prefix_diff_cells.loc[prefix_changed_df.index, col]
#                 # Replace unchanged cells with None
#                 prefix_changed_df.loc[~mask, col] = None
        
#         # ============================================================
#         # Step 3.8: Process Each Row and Add to Consolidated List
#         # ============================================================
#         for idx, row in prefix_changed_df.iterrows():
#             # ============================================================
#             # Step 3.8.1: Check Required Key Identifiers
#             # ============================================================
#             # r_pj_id, phase_id, and rfl_id are required (needed for database updates)
#             # Check using prefixed column names
#             prefixed_r_pj_id = f'{prefix}r_pj_id'
#             prefixed_phase_id = f'{prefix}phase_id'
#             prefixed_rfl_id = f'{prefix}rfl_id'
            
#             # Helper function to check if value is None, NaN, empty string, or string 'None'
#             def is_empty(value):
#                 return (value is None or 
#                        pd.isna(value) or 
#                        (isinstance(value, str) and (value.strip() == '' or value.strip().lower() == 'none' or value.strip().lower() == 'null' or value.strip().lower() == 'nan')))
            
#             # Skip if r_pj_id doesn't exist, is NaN, None, or empty string
#             if (prefixed_r_pj_id not in row.index or 
#                 is_empty(row[prefixed_r_pj_id])):
#                 continue
#             # Skip if phase_id doesn't exist, is NaN, None, or empty string
#             if (prefixed_phase_id not in row.index or 
#                 is_empty(row[prefixed_phase_id])):
#                 continue
#             # Skip if rfl_id doesn't exist or is NaN
#             if prefixed_rfl_id not in row.index or pd.isna(row[prefixed_rfl_id]):
#                 continue
            
#             # ============================================================
#             # Step 3.8.2: Create Row Dictionary for Consolidation
#             # ============================================================
#             consolidated_row = {}
            
#             # Add key columns (remove prefix)
#             # Example: 'c_r_pj_id' → 'r_pj_id'
#             for key_base in key_base_names:
#                 prefixed_key = f'{prefix}{key_base}'
#                 if prefixed_key in row.index and pd.notna(row[prefixed_key]):
#                     consolidated_row[key_base] = row[prefixed_key]
            
#             # ============================================================
#             # Step 3.8.3: Add Data Columns (Remove Prefix)
#             # ============================================================
#             # Add only data columns that have changes
#             has_data = False  # Flag indicating if at least one data column was added
#             for col in prefix_changed_cols_list:
#                 if col.startswith(prefix):
#                     # Remove prefix to get base column name
#                     # Example: 'c_req' → 'req'
#                     base_col = col[len(prefix):]
                    
#                     # Process only columns in base_columns or ending with _id
#                     if base_col in base_columns or base_col.endswith('_id'):
#                         value = row[col]
#                         # For _id columns: only add non-None/NaN/non-empty values
#                         # For non-_id columns: allow None/empty values to be added
#                         if base_col.endswith('_id'):
#                             # Strict check for ID columns
#                             if pd.notna(value) and str(value) != 'nan' and str(value) != 'None':
#                                 consolidated_row[base_col] = value
#                                 has_data = True
#                         else:
#                             # Allow None/empty values for non-ID columns
#                             consolidated_row[base_col] = value
#                             has_data = True
            
#             # ============================================================
#             # Step 3.8.4: Add to Consolidated List
#             # ============================================================
#             # Add only if at least one data column exists
#             # Don't add rows with only key columns
#             if has_data:
#                 consolidated_rows.append(consolidated_row)
    
#     # ============================================================
#     # Step 4: Create Consolidated DataFrame
#     # ============================================================
#     # Create DataFrame from consolidated rows list
#     # Example: if c_req and s_req were changed, create a 2-row DataFrame
#     #          Each row has a req column with respective r_pj_id and rfl_id
#     if consolidated_rows:
#         changed_columns_df = pd.DataFrame(consolidated_rows)
#     else:
#         changed_columns_df = pd.DataFrame()

#     st.write("changed_columns_df:", changed_columns_df)

#     # ============================================================
#     # Step 5: Convert Unit Values to IDs
#     # ============================================================
#     # Convert f_unit and l_unit values (strings) to corresponding IDs
#     # Note: r_unit comes from r_parameter table, so ID conversion is not needed
#     unit_columns = ['f_unit', 'l_unit']
#     units_dict = rflq.get_units_dict()  # Mapping dictionary: unit name → unit ID
    
#     for unit_col in unit_columns:
#         if unit_col in changed_columns_df.columns:
#             unit_id_col = unit_col + '_id'  # Example: 'f_unit' → 'f_unit_id'
#             # Convert unit name to unit ID
#             # Returns None if not found in dictionary
#             changed_columns_df[unit_id_col] = changed_columns_df[unit_col].apply(
#                 lambda x: units_dict.get(x) if x is not None and pd.notna(x) and str(x) != 'nan' else None
#             )
#             # Set unit_id to None for rows where unit value is NaN
#             changed_columns_df.loc[changed_columns_df[unit_col].isna(), unit_id_col] = None

#     # ============================================================
#     # Step 6: Convert Allocation (WP) Values to IDs
#     # ============================================================
#     # Convert l_wp values (strings) to corresponding WP IDs
#     allocation_column = 'l_wp'
#     if allocation_column in changed_columns_df.columns:
#         wp_dict = rflq.get_wp_dict()  # Mapping dictionary: WP name → WP ID
#         wp_id_col = 'l_wp_id'
#         # Convert WP name to WP ID
#         # Returns None if not found in dictionary
#         changed_columns_df[wp_id_col] = changed_columns_df[allocation_column].apply(
#             lambda x: wp_dict.get(x) if x is not None and pd.notna(x) and str(x) != 'nan' else None
#         )


#     if st.button("確定する"):
#         if changed_columns_df.empty:
#             st.error("編集内容がありません。")
#         else:
#             # Convert all ID columns to integers before database update
#             # This prevents SQL errors like "integer"型の入力構文が不正です: "1157.0"
#             id_columns = [col for col in changed_columns_df.columns if col.endswith('_id')]
#             for id_col in id_columns:
#                 if id_col in changed_columns_df.columns:
#                     # Convert to int, handling float values and NaN
#                     changed_columns_df[id_col] = changed_columns_df[id_col].apply(
#                         lambda x: int(float(x)) if pd.notna(x) and str(x) != 'nan' and str(x) != '' else None
#                     )
            
#             st.session_state.rfl_edit_state = False
#             # rfl_org_pattern = r'^org_rfl_pj_\d+'
#             # rfl_res_pattern = r'^rfl_pj_response_\d+'

            
#             rfl_upd_res = sql.update_rfl_infos(changed_columns_df,original_df)

#             print('rfl_upd_res:', rfl_upd_res)

#             if not rfl_upd_res:
#                 st.error("RFL情報の更新に失敗しました。")
#             else:
#                 # DB更新後の表を表示 
#                 # df=rflq.posgre_get_rfl_tlm(
#                 #     st.session_state['selectoption1'],
#                 #     st.session_state['selectoption2'],
#                 #     st.session_state['selectoption3'],
#                 #     st.session_state['selectoption4'],
#                 #     st.session_state['selectoption5'],
#                 #     st.session_state['selected_hr'],
#                 #     st.session_state['wp'],
#                 # )
#                 # st.session_state.rfl_list = df

#                 df = rflq.get_rfl_all_hierarchy_levels(
#                                         st.session_state['selectoption1'],
#                                         st.session_state['selectoption2'],
#                                         st.session_state['selectoption3'],
#                                         st.session_state['selectoption4'],
#                                         st.session_state['selectoption5'],
#                                         st.session_state.wp, True)
#                 st.session_state.rfl_list = df

#                 rfl_all_info = sql.posgre_get_rfl(
#                     st.session_state['selectoption1'],
#                     st.session_state['selectoption2'],
#                     st.session_state['selectoption3'],
#                     st.session_state['selectoption4'],
#                     st.session_state['selectoption5']
#                 )
#                 st.session_state.rfl_matrix = rfl_all_info

#                 st.session_state.edit_refresh = True
#                 time.sleep(0.5)
#                 st.rerun()
            

#     if st.button("破棄する"):
#         st.session_state.rfl_edit_state = False

#         # db更新無し 表示を元に戻す
#         # df=rflq.posgre_get_rfl_tlm(
#         #     st.session_state['selectoption1'],
#         #     st.session_state['selectoption2'],
#         #     st.session_state['selectoption3'],
#         #     st.session_state['selectoption4'],
#         #     st.session_state['selectoption5'],
#         #     st.session_state['selected_hr'],
#         #     st.session_state['wp'],
#         # )
#         # df = rflq.get_rfl_all_hierarchy_levels(
#         #                                 st.session_state['selectoption1'],
#         #                                 st.session_state['selectoption2'],
#         #                                 st.session_state['selectoption3'],
#         #                                 st.session_state['selectoption4'],
#         #                                 st.session_state['selectoption5'],
#         #                                 st.session_state.wp, True)
#         # st.session_state.rfl_list = df
#         st.session_state.edit_refresh = True
#         st.rerun()

#     if st.button("キャンセル"):
#         st.session_state.rfl_edit_state = True
#         st.rerun()
    

#telema-kyaw  #11/05
@st.dialog("RFL編集終了確認", width="large")
def off_rfl_edit():
    """
    RFL Edit Mode Confirmation Dialog
    
    This function detects changes made by the user in the RFL grid and
    creates a DataFrame for database updates.
    
    Processing flow:
    1. Compare original data (original_df) with edited data (response_df)
    2. Detect changes for each hierarchy (c_, s_, u_)
    3. Consolidate changed rows into a single DataFrame (remove prefixes)
    4. Convert unit and WP values to IDs
    5. Execute database update
    """
    st.write('編集モードを終了します　')
    st.write('編集内容を確定しますか？')

    # ============================================================
    # Step 0: Find all response DataFrames to process
    # ============================================================
    # Find all session state keys that start with 'rfl_pj_response_'
    response_keys = [key for key in st.session_state.keys() 
                     if isinstance(key, str) and key.startswith('rfl_pj_response_')]
    
    # Sort keys to process in order (e.g., rfl_pj_response_0, rfl_pj_response_1, ...)
    response_keys = sorted(response_keys, key=lambda x: int(x.split('_')[-1]) if x.split('_')[-1].isdigit() else 0)
    
    # ============================================================
    # Step 1: Configuration Definition
    # ============================================================
    # Hierarchy prefixes to process: c_=Vehicle, s_=System, u_=Unit
    prefixes = ['c_', 's_', 'u_']
    
    # Base column names (after prefix removal) to consolidate
    # These columns will be consolidated into a single DataFrame by removing prefixes
    base_columns = {
        'req', 'func', 'logic', 'note', 'r_item', 'f_item', 'l_item', 
        'r_unit', 'f_unit', 'l_unit', 'r_scene', 'l_scene',
        'req_condition', 'log_condition',
        'sender_judge', 'sender_name', 'sender_date', 'sender_comment',
        'receiver_judge', 'receiver_name', 'receiver_date', 'receiver_comment',
        'l_wp'
    }
    
    # Key columns (identifiers required for database updates)
    # These columns are required for each hierarchy and are preserved after consolidation
    key_base_names = ['r_pj_id', 'phase_id', 'rfl_id', 'r_s_id', 'l_s_id', 'f_id']
    
    # Date columns (require special handling)
    # Dates must be compared as datetime type, not as strings
    date_base_names = ['sender_date', 'receiver_date']
    
    # List to store consolidated rows from all DataFrames
    # A single DataFrame will be created from this list at the end
    consolidated_rows = []
    
    # List to store all original DataFrames for later use in update_rfl_infos
    all_original_dfs = []
    
    # ============================================================
    # Step 2: Loop through each response DataFrame
    # ============================================================
    for response_key in response_keys:
        # Extract index from key (e.g., 'rfl_pj_response_0' -> '0')
        index = response_key.split('_')[-1]
        org_key = f'org_rfl_pj_{index}'
        
        # Skip if corresponding original DataFrame doesn't exist
        if org_key not in st.session_state:
            continue
        
        # ============================================================
        # Step 2.1: Data Preparation for this DataFrame pair
        # ============================================================
        # Get original and edited data from session state
        # reset_index(drop=True) resets the index to align row positions
        original_df = st.session_state[org_key].reset_index(drop=True)
        response_df = st.session_state[response_key].reset_index(drop=True)

        # Drop unnecessary columns (rfl_id and phase are not needed for comparison), not to duplicate cols
        original_df = original_df.drop(columns=['rfl_id','phase'], errors='ignore')
        response_df = response_df.drop(columns=['rfl_id','phase'], errors='ignore')
        
        # Store original_df for later use in update_rfl_infos
        all_original_dfs.append(original_df.copy())

        # st.write('original_df: ', original_df)
        # st.write('response_df: ', response_df)
        
        # ============================================================
        # Step 2.2: Detect Changes for Each Hierarchy
        # ============================================================
        for prefix in prefixes:
            # Get only columns that are in base_columns (with prefix) and their _id columns
            # Also include key columns for identification
            prefix_cols = []
            
            # Add base columns with prefix (e.g., 'c_req', 'c_func', etc.)
            for base_col in base_columns:
                prefixed_col = f'{prefix}{base_col}'
                if prefixed_col in original_df.columns:
                    prefix_cols.append(prefixed_col)
                # Also add _id version if it exists (e.g., 'c_f_unit_id', 'c_l_unit_id')
                prefixed_id_col = f'{prefix}{base_col}_id'
                if prefixed_id_col in original_df.columns:
                    prefix_cols.append(prefixed_id_col)
            
            # Add key columns (required for identification)
            for key_base in key_base_names:
                prefixed_key = f'{prefix}{key_base}'
                if prefixed_key in original_df.columns:
                    prefix_cols.append(prefixed_key)
            
            # Skip if no columns exist for this hierarchy
            if not prefix_cols:
                continue
            # st.write('response df: ', response_df)
            # st.write('prefix_cols: ', prefix_cols)
            # ============================================================
            # Step 2.2.1: Extract Data for This Hierarchy Only
            # ============================================================
            # Extract only columns for this hierarchy from original and edited data
            prefix_original = original_df[prefix_cols].copy()
            prefix_response = response_df[prefix_cols].copy()
            
            # ============================================================
            # Step 2.2.2: Process Date Columns
            # ============================================================
            # Date columns must be compared as datetime type, not as strings
            # Example: convert 'c_sender_date', 'c_receiver_date' to datetime type
            for date_base in date_base_names:
                date_col = f'{prefix}{date_base}'
                if date_col in prefix_original.columns:
                    # # Replace None values explicitly before conversion
                    # prefix_original[date_col] = prefix_original[date_col].replace([None], pd.NaT)
                    # prefix_response[date_col] = prefix_response[date_col].replace([None], pd.NaT)
                    # Convert date strings to datetime type (becomes NaT on error or None)
                    prefix_original[date_col] = pd.to_datetime(prefix_original[date_col], errors='coerce')
                    prefix_response[date_col] = pd.to_datetime(prefix_response[date_col], errors='coerce')
                    # Replace NaT (Not a Time) and None with 1700-01-01 to make comparison possible
                    prefix_original[date_col] = prefix_original[date_col].fillna(pd.Timestamp('1700-01-01'))
                    prefix_response[date_col] = prefix_response[date_col].fillna(pd.Timestamp('1700-01-01'))
            
            
            # ============================================================
            # Step 2.2.3: Convert Other Columns to String
            # ============================================================
            # Convert non-date columns to string for comparison
            # This prevents comparison errors due to differences in numeric or other types
            for col in prefix_original.columns:
                if col not in [f'{prefix}{d}' for d in date_base_names]:
                    prefix_original[col] = prefix_original[col].astype(str)
                    prefix_response[col] = prefix_response[col].astype(str)
            
            # ============================================================
            # Step 2.2.4: Detect Changes
            # ============================================================
            # Compare cell by cell: True = values differ, False = values are same
            prefix_diff_cells = prefix_original != prefix_response
            
            # Check for changes row by row: True if any column in the row differs
            prefix_diff_rows = prefix_diff_cells.any(axis=1)
            
            # Skip to next hierarchy if no changes in this hierarchy
            if not prefix_diff_rows.any():
                continue
            
            # ============================================================
            # Step 2.2.5: Identify Changed Columns
            # ============================================================
            # Check for changes column by column: True if any row in the column differs
            prefix_changed_cols = prefix_diff_cells.any(axis=0)
            # Get list of column names that have changes
            prefix_changed_cols_list = list(prefix_changed_cols[prefix_changed_cols].index)
            
            # Add key columns (required even if not changed)
            # Ensure identifiers needed for database updates are included
            for key_base in key_base_names:
                prefixed_key = f'{prefix}{key_base}'
                # Add only if key column exists and is not already in the list
                if prefixed_key in prefix_response.columns and prefixed_key not in prefix_changed_cols_list:
                    prefix_changed_cols_list.insert(0, prefixed_key)  # Insert at beginning
            
            # Filter out columns that don't actually exist
            # Example: exclude columns like 's_r_item_index' that may have been added later
            prefix_changed_cols_list = [col for col in prefix_changed_cols_list if col in prefix_response.columns]
            
            # ============================================================
            # Step 2.2.6: Extract Only Changed Rows and Columns
            # ============================================================
            # Extract only rows that have changes, containing only changed columns
            prefix_changed_df = prefix_response.loc[prefix_diff_rows, prefix_changed_cols_list].copy()
            
            # ============================================================
            # Step 2.2.7: Mask Unchanged Cells as None
            # ============================================================
            # For rows with changes, set unchanged column values to None
            # This ensures only actually changed values remain
            for col in prefix_changed_df.columns:
                # Key columns are always kept (not set to None)
                if col not in [f'{prefix}{k}' for k in key_base_names]:
                    # Create mask where True indicates changed cells for this column
                    mask = prefix_diff_cells.loc[prefix_changed_df.index, col]
                    # Replace unchanged cells with None
                    prefix_changed_df.loc[~mask, col] = None
            
            # ============================================================
            # Step 2.2.8: Process Each Row and Add to Consolidated List
            # ============================================================
            for idx, row in prefix_changed_df.iterrows():
                # ============================================================
                # Step 2.2.8.1: Check Required Key Identifiers
                # ============================================================
                # r_pj_id, phase_id, and rfl_id are required (needed for database updates)
                # Check using prefixed column names
                prefixed_r_pj_id = f'{prefix}r_pj_id'
                prefixed_phase_id = f'{prefix}phase_id'
                prefixed_rfl_id = f'{prefix}rfl_id'
                
                # Helper function to check if value is None, NaN, empty string, or string 'None'
                def is_empty(value):
                    return (value is None or 
                           pd.isna(value) or 
                           (isinstance(value, str) and (value.strip() == '' or value.strip().lower() == 'none' or value.strip().lower() == 'null' or value.strip().lower() == 'nan')))
                
                # Skip if r_pj_id doesn't exist, is NaN, None, or empty string
                if (prefixed_r_pj_id not in row.index or 
                    is_empty(row[prefixed_r_pj_id])):
                    continue
                # Skip if phase_id doesn't exist, is NaN, None, or empty string
                if (prefixed_phase_id not in row.index or 
                    is_empty(row[prefixed_phase_id])):
                    continue
                # Skip if rfl_id doesn't exist or is NaN
                if prefixed_rfl_id not in row.index or pd.isna(row[prefixed_rfl_id]):
                    continue
                
                # ============================================================
                # Step 2.2.8.2: Create Row Dictionary for Consolidation
                # ============================================================
                consolidated_row = {}
                
                # Add key columns (remove prefix)
                # Example: 'c_r_pj_id' → 'r_pj_id'
                for key_base in key_base_names:
                    prefixed_key = f'{prefix}{key_base}'
                    if prefixed_key in row.index and pd.notna(row[prefixed_key]):
                        consolidated_row[key_base] = row[prefixed_key]
                
                # ============================================================
                # Step 2.2.8.3: Add Data Columns (Remove Prefix)
                # ============================================================
                # Add only data columns that have changes
                has_data = False  # Flag indicating if at least one data column was added
                for col in prefix_changed_cols_list:
                    if col.startswith(prefix):
                        # Remove prefix to get base column name
                        # Example: 'c_req' → 'req'
                        base_col = col[len(prefix):]
                        
                        # Process only columns in base_columns or ending with _id
                        if base_col in base_columns or base_col.endswith('_id'):
                            value = row[col]
                            # For _id columns: only add non-None/NaN/non-empty values
                            # For non-_id columns: allow None/empty values to be added
                            if base_col.endswith('_id'):
                                # Strict check for ID columns
                                if pd.notna(value) and str(value) != 'nan' and str(value) != 'None':
                                    consolidated_row[base_col] = value
                                    has_data = True
                            else:
                                # Allow None/empty values for non-ID columns
                                consolidated_row[base_col] = value
                                has_data = True
                
                # ============================================================
                # Step 2.2.8.4: Add to Consolidated List
                # ============================================================
                # Add only if at least one data column exists
                # Don't add rows with only key columns
                if has_data:
                    consolidated_rows.append(consolidated_row)
    
    # ============================================================
    # Step 4: Create Consolidated DataFrame
    # ============================================================
    # Create DataFrame from consolidated rows list
    # Example: if c_req and s_req were changed, create a 2-row DataFrame
    #          Each row has a req column with respective r_pj_id and rfl_id
    if consolidated_rows:
        changed_columns_df = pd.DataFrame(consolidated_rows)
    else:
        changed_columns_df = pd.DataFrame()

    st.write("changed_columns_df:", changed_columns_df)

    # ============================================================
    # Step 5: Convert Unit Values to IDs
    # ============================================================
    # Convert f_unit and l_unit values (strings) to corresponding IDs
    # Note: r_unit comes from r_parameter table, so ID conversion is not needed
    unit_columns = ['f_unit', 'l_unit']
    units_dict = rflq.get_units_dict()  # Mapping dictionary: unit name → unit ID
    
    for unit_col in unit_columns:
        if unit_col in changed_columns_df.columns:
            unit_id_col = unit_col + '_id'  # Example: 'f_unit' → 'f_unit_id'
            # Convert unit name to unit ID
            # Returns None if not found in dictionary
            changed_columns_df[unit_id_col] = changed_columns_df[unit_col].apply(
                lambda x: units_dict.get(x) if x is not None and pd.notna(x) and str(x) != 'nan' else None
            )
            # Set unit_id to None for rows where unit value is NaN
            changed_columns_df.loc[changed_columns_df[unit_col].isna(), unit_id_col] = None

    # ============================================================
    # Step 6: Convert Allocation (WP) Values to IDs
    # ============================================================
    # Convert l_wp values (strings) to corresponding WP IDs
    allocation_column = 'l_wp'
    if allocation_column in changed_columns_df.columns:
        wp_dict = rflq.get_wp_dict()  # Mapping dictionary: WP name → WP ID
        wp_id_col = 'l_wp_id'
        # Convert WP name to WP ID
        # Returns None if not found in dictionary
        changed_columns_df[wp_id_col] = changed_columns_df[allocation_column].apply(
            lambda x: wp_dict.get(x) if x is not None and pd.notna(x) and str(x) != 'nan' else None
        )


    if st.button("確定する"):
        if changed_columns_df.empty:
            st.error("編集内容がありません。")
        else:
            # Convert all ID columns to integers before database update
            # This prevents SQL errors like "integer"型の入力構文が不正です: "1157.0"
            id_columns = [col for col in changed_columns_df.columns if col.endswith('_id')]
            for id_col in id_columns:
                if id_col in changed_columns_df.columns:
                    # Convert to int, handling float values and NaN
                    changed_columns_df[id_col] = changed_columns_df[id_col].apply(
                        lambda x: int(float(x)) if pd.notna(x) and str(x) != 'nan' and str(x) != '' else None
                    )
            
            st.session_state.rfl_edit_state = False
            # rfl_org_pattern = r'^org_rfl_pj_\d+'
            # rfl_res_pattern = r'^rfl_pj_response_\d+'

            # Combine all original DataFrames into a single DataFrame for update_rfl_infos
            # Remove duplicate columns if any
            if all_original_dfs:
                combined_original_df = pd.concat(all_original_dfs, ignore_index=True)
                combined_original_df = combined_original_df.loc[:, ~combined_original_df.columns.duplicated()]
            else:
                combined_original_df = pd.DataFrame()
            
            rfl_upd_res = sql.update_rfl_infos(changed_columns_df, combined_original_df)

            print('rfl_upd_res:', rfl_upd_res)

            if not rfl_upd_res:
                st.error("RFL情報の更新に失敗しました。")
            else:
                # DB更新後の表を表示 
                # df=rflq.posgre_get_rfl_tlm(
                #     st.session_state['selectoption1'],
                #     st.session_state['selectoption2'],
                #     st.session_state['selectoption3'],
                #     st.session_state['selectoption4'],
                #     st.session_state['selectoption5'],
                #     st.session_state['selected_hr'],
                #     st.session_state['wp'],
                # )
                # st.session_state.rfl_list = df

                df = rflq.get_rfl_all_hierarchy_levels(
                                        st.session_state['selectoption1'],
                                        st.session_state['selectoption2'],
                                        st.session_state['selectoption3'],
                                        st.session_state['selectoption4'],
                                        st.session_state['selectoption5'],
                                        st.session_state.wp, True)
                st.session_state.rfl_list = df
                #update_bk 11/19
                rfl_all_info = sql.posgre_get_rfl(
                    st.session_state['selectoption1'],
                    st.session_state['selectoption2'],
                    st.session_state['selectoption3'],
                    st.session_state['selectoption4'],
                    st.session_state['selectoption5']
                )
                # rfl_all_info = rflq.get_rfl_all_hierarchy_levels(
                #     st.session_state['selectoption1'],
                #     st.session_state['selectoption2'],
                #     st.session_state['selectoption3'],
                #     st.session_state['selectoption4'],
                #     st.session_state['selectoption5'],
                #     [], True)
                st.session_state.rfl_matrix = rfl_all_info

                st.session_state.edit_refresh = True
                time.sleep(0.5)
                st.rerun()
            

    if st.button("破棄する"):
        st.session_state.rfl_edit_state = False

        # db更新無し 表示を元に戻す
        # df=rflq.posgre_get_rfl_tlm(
        #     st.session_state['selectoption1'],
        #     st.session_state['selectoption2'],
        #     st.session_state['selectoption3'],
        #     st.session_state['selectoption4'],
        #     st.session_state['selectoption5'],
        #     st.session_state['selected_hr'],
        #     st.session_state['wp'],
        # )
        # df = rflq.get_rfl_all_hierarchy_levels(
        #                                 st.session_state['selectoption1'],
        #                                 st.session_state['selectoption2'],
        #                                 st.session_state['selectoption3'],
        #                                 st.session_state['selectoption4'],
        #                                 st.session_state['selectoption5'],
        #                                 st.session_state.wp, True)
        # st.session_state.rfl_list = df
        st.session_state.edit_refresh = True
        st.rerun()

    if st.button("キャンセル"):
        st.session_state.rfl_edit_state = True
        st.rerun()
 
    
# #telema-kyaw  #11/05
# @st.dialog("RFL編集終了確認", width="large")
# def off_rfl_edit():
#     """
#     RFL Edit Mode Confirmation Dialog
    
#     This function detects changes made by the user in the RFL grid and
#     creates a DataFrame for database updates.
    
#     Processing flow:
#     1. Compare original data (original_df) with edited data (response_df)
#     2. Detect changes for each hierarchy (c_, s_, u_)
#     3. Consolidate changed rows into a single DataFrame (remove prefixes)
#     4. Convert unit and WP values to IDs
#     5. Execute database update
#     """
#     st.write('編集モードを終了します　')
#     st.write('編集内容を確定しますか？')

#     # ============================================================
#     # Step 1: Data Preparation
#     # ============================================================
#     # Get original and edited data from session state
#     # reset_index(drop=True) resets the index to align row positions
#     original_df = st.session_state[f'org_rfl_pj_0'].reset_index(drop=True)
#     response_df = st.session_state[f'rfl_pj_response_0'].reset_index(drop=True)

#     # Drop unnecessary columns (rfl_id and phase are not needed for comparison), not to duplicate cols
#     original_df = original_df.drop(columns=['rfl_id','phase'], errors='ignore')
#     response_df = response_df.drop(columns=['rfl_id','phase'], errors='ignore')

#     # ============================================================
#     # Step 2: Configuration Definition
#     # ============================================================
#     # Hierarchy prefixes to process: c_=Vehicle, s_=System, u_=Unit
#     prefixes = ['c_', 's_', 'u_']
    
#     # Base column names (after prefix removal) to consolidate
#     # These columns will be consolidated into a single DataFrame by removing prefixes
#     base_columns = {
#         'req', 'func', 'logic', 'note', 'r_item', 'f_item', 'l_item', 
#         'r_unit', 'f_unit', 'l_unit', 'r_scene', 'l_scene',
#         'req_condition', 'log_condition',
#         'sender_judge', 'sender_name', 'sender_date', 'sender_comment',
#         'receiver_judge', 'receiver_name', 'receiver_date', 'receiver_comment',
#         'l_wp'
#     }
    
#     # Key columns (identifiers required for database updates)
#     # These columns are required for each hierarchy and are preserved after consolidation
#     key_base_names = ['r_pj_id', 'phase_id', 'rfl_id', 'r_s_id', 'l_s_id', 'f_id']
    
#     # Date columns (require special handling)
#     # Dates must be compared as datetime type, not as strings
#     date_base_names = ['sender_date', 'receiver_date']
    
#     # List to store consolidated rows
#     # A single DataFrame will be created from this list at the end
#     consolidated_rows = []
    
#     # ============================================================
#     # Step 3: Detect Changes for Each Hierarchy
#     # ============================================================
#     for prefix in prefixes:
#         # Get all columns that start with this hierarchy's prefix
#         # Example: if prefix='c_', get 'c_req', 'c_r_pj_id', 'c_rfl_id', etc.
#         prefix_cols = [col for col in original_df.columns if col.startswith(prefix)]
        
#         # Skip if no columns exist for this hierarchy
#         if not prefix_cols:
#             continue
#         st.write('response df: ', response_df)
#         print('prefix_cols: ', prefix_cols)
#         # ============================================================
#         # Step 3.1: Extract Data for This Hierarchy Only
#         # ============================================================
#         # Extract only columns for this hierarchy from original and edited data
#         prefix_original = original_df[prefix_cols].copy()
#         prefix_response = response_df[prefix_cols].copy()
        
#         # ============================================================
#         # Step 3.2: Process Date Columns
#         # ============================================================
#         # Date columns must be compared as datetime type, not as strings
#         # Example: convert 'c_sender_date', 'c_receiver_date' to datetime type
#         for date_base in date_base_names:
#             date_col = f'{prefix}{date_base}'
#             if date_col in prefix_original.columns:
#                 # Convert date strings to datetime type (becomes NaT on error)
#                 prefix_original[date_col] = pd.to_datetime(prefix_original[date_col], errors='coerce')
#                 prefix_response[date_col] = pd.to_datetime(prefix_response[date_col], errors='coerce')
#                 # Replace NaT (Not a Time) with 1900-01-01 to make comparison possible
#                 prefix_original[date_col] = prefix_original[date_col].fillna(pd.Timestamp('1900-01-01'))
#                 prefix_response[date_col] = prefix_response[date_col].fillna(pd.Timestamp('1900-01-01'))
        
#         # ============================================================
#         # Step 3.3: Convert Other Columns to String
#         # ============================================================
#         # Convert non-date columns to string for comparison
#         # This prevents comparison errors due to differences in numeric or other types
#         for col in prefix_original.columns:
#             if col not in [f'{prefix}{d}' for d in date_base_names]:
#                 prefix_original[col] = prefix_original[col].astype(str)
#                 prefix_response[col] = prefix_response[col].astype(str)
        
#         # ============================================================
#         # Step 3.4: Detect Changes
#         # ============================================================
#         # Compare cell by cell: True = values differ, False = values are same
#         prefix_diff_cells = prefix_original != prefix_response
        
#         # Check for changes row by row: True if any column in the row differs
#         prefix_diff_rows = prefix_diff_cells.any(axis=1)
        
#         # Skip to next hierarchy if no changes in this hierarchy
#         if not prefix_diff_rows.any():
#             continue
        
#         # ============================================================
#         # Step 3.5: Identify Changed Columns
#         # ============================================================
#         # Check for changes column by column: True if any row in the column differs
#         prefix_changed_cols = prefix_diff_cells.any(axis=0)
#         # Get list of column names that have changes
#         prefix_changed_cols_list = list(prefix_changed_cols[prefix_changed_cols].index)
        
#         # Add key columns (required even if not changed)
#         # Ensure identifiers needed for database updates are included
#         for key_base in key_base_names:
#             prefixed_key = f'{prefix}{key_base}'
#             # Add only if key column exists and is not already in the list
#             if prefixed_key in prefix_response.columns and prefixed_key not in prefix_changed_cols_list:
#                 prefix_changed_cols_list.insert(0, prefixed_key)  # Insert at beginning
        
#         # Filter out columns that don't actually exist
#         # Example: exclude columns like 's_r_item_index' that may have been added later
#         prefix_changed_cols_list = [col for col in prefix_changed_cols_list if col in prefix_response.columns]
        
#         # ============================================================
#         # Step 3.6: Extract Only Changed Rows and Columns
#         # ============================================================
#         # Extract only rows that have changes, containing only changed columns
#         prefix_changed_df = prefix_response.loc[prefix_diff_rows, prefix_changed_cols_list].copy()
        
#         # ============================================================
#         # Step 3.7: Mask Unchanged Cells as None
#         # ============================================================
#         # For rows with changes, set unchanged column values to None
#         # This ensures only actually changed values remain
#         for col in prefix_changed_df.columns:
#             # Key columns are always kept (not set to None)
#             if col not in [f'{prefix}{k}' for k in key_base_names]:
#                 # Create mask where True indicates changed cells for this column
#                 mask = prefix_diff_cells.loc[prefix_changed_df.index, col]
#                 # Replace unchanged cells with None
#                 prefix_changed_df.loc[~mask, col] = None
        
#         # ============================================================
#         # Step 3.8: Process Each Row and Add to Consolidated List
#         # ============================================================
#         for idx, row in prefix_changed_df.iterrows():
#             # ============================================================
#             # Step 3.8.1: Check Required Key Identifiers
#             # ============================================================
#             # r_pj_id and rfl_id are required (needed for database updates)
#             # Check using prefixed column names
#             prefixed_r_pj_id = f'{prefix}r_pj_id'
#             prefixed_rfl_id = f'{prefix}rfl_id'
            
#             # Skip if r_pj_id doesn't exist or is NaN
#             if prefixed_r_pj_id not in row.index or pd.isna(row[prefixed_r_pj_id]):
#                 continue
#             # Skip if rfl_id doesn't exist or is NaN
#             if prefixed_rfl_id not in row.index or pd.isna(row[prefixed_rfl_id]):
#                 continue
            
#             # ============================================================
#             # Step 3.8.2: Create Row Dictionary for Consolidation
#             # ============================================================
#             consolidated_row = {}
            
#             # Add key columns (remove prefix)
#             # Example: 'c_r_pj_id' → 'r_pj_id'
#             for key_base in key_base_names:
#                 prefixed_key = f'{prefix}{key_base}'
#                 if prefixed_key in row.index and pd.notna(row[prefixed_key]):
#                     consolidated_row[key_base] = row[prefixed_key]
            
#             # ============================================================
#             # Step 3.8.3: Add Data Columns (Remove Prefix)
#             # ============================================================
#             # Add only data columns that have changes
#             has_data = False  # Flag indicating if at least one data column was added
#             for col in prefix_changed_cols_list:
#                 if col.startswith(prefix):
#                     # Remove prefix to get base column name
#                     # Example: 'c_req' → 'req'
#                     base_col = col[len(prefix):]
                    
#                     # Process only columns in base_columns or ending with _id
#                     if base_col in base_columns or base_col.endswith('_id'):
#                         value = row[col]
#                         # Add only non-None/NaN/non-empty values
#                         if pd.notna(value) and str(value) != 'nan' and str(value) != 'None':
#                             consolidated_row[base_col] = value
#                             has_data = True
            
#             # ============================================================
#             # Step 3.8.4: Add to Consolidated List
#             # ============================================================
#             # Add only if at least one data column exists
#             # Don't add rows with only key columns
#             if has_data:
#                 consolidated_rows.append(consolidated_row)
    
#     # ============================================================
#     # Step 4: Create Consolidated DataFrame
#     # ============================================================
#     # Create DataFrame from consolidated rows list
#     # Example: if c_req and s_req were changed, create a 2-row DataFrame
#     #          Each row has a req column with respective r_pj_id and rfl_id
#     if consolidated_rows:
#         changed_columns_df = pd.DataFrame(consolidated_rows)
#     else:
#         changed_columns_df = pd.DataFrame()

#     st.write("changed_columns_df:", changed_columns_df)

#     # ============================================================
#     # Step 5: Convert Unit Values to IDs
#     # ============================================================
#     # Convert f_unit and l_unit values (strings) to corresponding IDs
#     # Note: r_unit comes from r_parameter table, so ID conversion is not needed
#     unit_columns = ['f_unit', 'l_unit']
#     units_dict = rflq.get_units_dict()  # Mapping dictionary: unit name → unit ID
    
#     for unit_col in unit_columns:
#         if unit_col in changed_columns_df.columns:
#             unit_id_col = unit_col + '_id'  # Example: 'f_unit' → 'f_unit_id'
#             # Convert unit name to unit ID
#             # Returns None if not found in dictionary
#             changed_columns_df[unit_id_col] = changed_columns_df[unit_col].apply(
#                 lambda x: units_dict.get(x) if x is not None and pd.notna(x) and str(x) != 'nan' else None
#             )
#             # Set unit_id to None for rows where unit value is NaN
#             changed_columns_df.loc[changed_columns_df[unit_col].isna(), unit_id_col] = None

#     # ============================================================
#     # Step 6: Convert Allocation (WP) Values to IDs
#     # ============================================================
#     # Convert l_wp values (strings) to corresponding WP IDs
#     allocation_column = 'l_wp'
#     if allocation_column in changed_columns_df.columns:
#         wp_dict = rflq.get_wp_dict()  # Mapping dictionary: WP name → WP ID
#         wp_id_col = 'l_wp_id'
#         # Convert WP name to WP ID
#         # Returns None if not found in dictionary
#         changed_columns_df[wp_id_col] = changed_columns_df[allocation_column].apply(
#             lambda x: wp_dict.get(x) if x is not None and pd.notna(x) and str(x) != 'nan' else None
#         )


#     if st.button("確定する"):
#         if changed_columns_df.empty:
#             st.error("編集内容がありません。")
#         else:
#             st.session_state.rfl_edit_state = False
#             # rfl_org_pattern = r'^org_rfl_pj_\d+'
#             # rfl_res_pattern = r'^rfl_pj_response_\d+'

            
#             rfl_upd_res = sql.update_rfl_infos(changed_columns_df,original_df)

#             print('rfl_upd_res:', rfl_upd_res)

#             if not rfl_upd_res:
#                 st.error("RFL情報の更新に失敗しました。")
#             else:
#                 # DB更新後の表を表示 
#                 df=rflq.posgre_get_rfl_tlm(
#                     st.session_state['selectoption1'],
#                     st.session_state['selectoption2'],
#                     st.session_state['selectoption3'],
#                     st.session_state['selectoption4'],
#                     st.session_state['selectoption5'],
#                     st.session_state['selected_hr'],
#                     st.session_state['wp'],
#                 )
#                 st.session_state.rfl_list = df

#                 rfl_all_info = sql.posgre_get_rfl(
#                     st.session_state['selectoption1'],
#                     st.session_state['selectoption2'],
#                     st.session_state['selectoption3'],
#                     st.session_state['selectoption4'],
#                     st.session_state['selectoption5']
#                 )
#                 st.session_state.rfl_matrix = rfl_all_info

#                 st.session_state.edit_refresh = True
#                 time.sleep(0.5)
#                 st.rerun()
            

#     if st.button("破棄する"):
#         st.session_state.rfl_edit_state = False

#         # db更新無し 表示を元に戻す
#         df=rflq.posgre_get_rfl_tlm(
#             st.session_state['selectoption1'],
#             st.session_state['selectoption2'],
#             st.session_state['selectoption3'],
#             st.session_state['selectoption4'],
#             st.session_state['selectoption5'],
#             st.session_state['selected_hr'],
#             st.session_state['wp'],
#         )
#         st.session_state.rfl_list = df
#         st.session_state.edit_refresh = True
#         st.rerun()

#     if st.button("キャンセル"):
#         st.session_state.rfl_edit_state = True
#         st.rerun()
    


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
    st.write('final df:', final_df)
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
                    execute_rfl_list_tlm()
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

#kayw-rfl
@st.dialog('エラー', width='small')
def not_select_error():
    st.error("選択してください。")

#kayw-rfl #11/05
@st.dialog('TO自動判定結果保存', width='large')
def update_summary_to_result(df_selecteds):
    st.write("最終確認を行ってください。")
    st.write("本当に更新する場合、「実行」ボタンを押下してください。") 
    # st.write(df_selecteds)
    go = gop.update_rfl_summary_to_grid()
    rfl_summary_to_update = AgGrid(
           df_selecteds,
           custom_css=css_ag,
           gridOptions=go,
           reload_data=False,
           height=220,
        )

    if st.button('実行'):
        upd_to_result = sql.upd_rfl_summary_to_result(pd.DataFrame(rfl_summary_to_update['data']))
        if upd_to_result:        
            
            st.session_state.flag_summary_before = st.session_state.flag_summary
            del st.session_state.df_display_on_summary #if not delete, the page reload is not working
            st.session_state.rerun_rfl_to = True
            # rfl_all_info = sql.posgre_get_rfl(
            #     st.session_state['selectoption1'],
            #     st.session_state['selectoption2'],
            #     st.session_state['selectoption3'],
            #     st.session_state['selectoption4'],
            #     st.session_state['selectoption5']
            # )
            # st.session_state.rfl_matrix = rfl_all_info
            
            # time.sleep(1)  # Show success message briefly
            # del st.session_state.df_display_on_summary #if not delete, the page reload is not working
            # st.session_state.rerun_rfl_to = True
            # st.rerun()
            execute_rfl_list_tlm()
            # st.rerun()
        else:
            st.error('エラーが発生しました。')

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

            # toggle_on = True if edit_mode is '***Personalモード***' else False
            toggle_on = (edit_mode == '***Personalモード***')
 
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



def selected_data_for_new_create():
    if 'new_selected_archi' not in st.session_state:
        st.session_state['new_selected_archi'] = []
        st.session_state['new_selected_prj'] = []

    architecture_list = sql.get_project("architecture_name")
    selected_archi = st.multiselect(
        'PTシステムタイプ',
        architecture_list,
        key='new_archi_unique_key',
        max_selections = 1,
        default=st.session_state.get('new_selected_archi') or None
    )

    if 'new_selected_prj' not in st.session_state or len(selected_archi) <= 0:
        st.session_state['new_selected_prj'] = []

    project_code_list = sql.get_project("z_model_code", selected_archi)
    selected_project = st.multiselect(
        'プロジェクト:',
        project_code_list,
        key='new_prjunique_key',
        max_selections = 1,
        default=st.session_state.get('new_selected_prj') or None
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
        default=st.session_state.get('new_selected_destination') or None,
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
        default=st.session_state.get('new_selected_drive_system') or None,
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
        default=st.session_state.get('new_selected_lot') or None,
    )
    selected_phase_ids = []
    selected_variation_ids = []
    variation_rdo = ""
    new_variation_text = ""
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
            default=st.session_state.get('new_selected_phase') or None,
        )
        selected_phase_ids = phase_list[phase_list['phase'].isin(selected_phase)]['id'].tolist()
        # st.write('selected phase ids:', selected_phase_ids)

        # Initialize variation selection variables
        selected_variation_ids = []
        new_variation_text = ''
        variation_rdo = None
        
        # Helper function to get selected variation IDs from existing variations
        def get_existing_variation_ids():
            if 'new_selected_variation' not in st.session_state:
                st.session_state['new_selected_variation'] = []
            variation_list = sql.all_variation_to_create_new_project()
            selected_variation = st.multiselect(
                'バリエーション:',
                variation_list['variation'],
                key='new_variation_unique_key',
                max_selections=1,
                default=st.session_state.get('new_selected_variation') or None,
            )
            return variation_list[variation_list['variation'].isin(selected_variation)]['id'].tolist()
        
        if int(st.session_state['chosen_id']) == 1:
            variation_rdo = st.radio(
                "バリエーション",
                ["既にあるバリエーション", "新しいバリエーション"],
                index=0,
                label_visibility='collapsed',
                horizontal=True
            )
            if variation_rdo == '既にあるバリエーション':
                selected_variation_ids = get_existing_variation_ids()
            else:
                new_variation_text = st.text_input("バリエーション:")
                # st.write('variation text:', new_variation_text)
        elif int(st.session_state['chosen_id']) == 2:
            # Always use existing variation selection for chosen_id == 2
            selected_variation_ids = get_existing_variation_ids()

        # st.write('selected variation ids:', selected_variation_ids)

    return selected_archi, selected_project, selected_destination, selected_drive_system, selected_lot, selected_phase_ids, variation_rdo, selected_variation_ids, new_variation_text



def handle_project_for_new_create(selected_data):

    selected_archi, selected_project, selected_destination, selected_drive_system, selected_lot, selected_phase_ids, variation_rdo, selected_variation_ids, new_variation_text = selected_data_for_new_create()

    if st.button("作成"):
        # if not selected_archi and not selected_project and not selected_destination and not selected_drive_system and not selected_lot and len(selected_phase_ids) == 0:
        if (
            not selected_archi
            or not selected_project
            or not selected_destination
            or not selected_drive_system
            or not selected_lot
            or len(selected_phase_ids) == 0
            or (variation_rdo == '既にあるバリエーション' and len(selected_variation_ids) == 0)
            or (variation_rdo == '' and len(selected_variation_ids) == 0)
        ):
            st.error('全て選択してくださぃ！！', icon="🚨")
        else:      
            if selected_data is None:
                st.error('ベースプロジェクトを選択してください。')
            elif len(selected_data) > 1:
                st.error('複数のベースプロジェクトを選択することはできません。')
            else:
                if int(st.session_state['chosen_id']) == 1:
                    inserted_res, res_msg = sql.insert_new_se_project(selected_data, selected_archi, selected_project, selected_destination, selected_drive_system, selected_lot, selected_phase_ids, selected_variation_ids, new_variation_text)
                if int(st.session_state['chosen_id']) == 2:
                    inserted_res, res_msg = sql.insert_new_rlist_and_rfl_list(selected_data, selected_archi, selected_project, selected_destination, selected_drive_system, selected_lot, selected_phase_ids, selected_variation_ids)
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
        handle_project_for_new_create(selected_data)



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
        handle_project_for_new_create(selected_data)
        







    

        
        


