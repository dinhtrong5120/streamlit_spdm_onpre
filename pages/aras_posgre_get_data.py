import const.constpara as co
from Aras_connect.Middle import IFtoARAS
import pandas as pd
from module.PsqlModule import psql_class
import streamlit as st


    
username = "GWE00199"
password = "GWE00199"
aras = IFtoARAS(username, password, co.ARASURL, co.ARASDB)
sql = psql_class()
st.markdown("DONT CLICK PLZ")
if st.button("プロジェクト更新"):

    
    # username = "GWE00199"
    # password = "GWE00199"
    # aras = IFtoARAS(username, password, co.ARASURL, co.ARASDB)
    # sql = psql_class()
    # res, prj_all, _ = aras.SearchPrjWithLot('SElist', op='startswith')

    # df = pd.json_normalize(prj_all['value'])

    # z_number_list = df['z_number'].tolist()

    # filtered_data = [
    #     item for item in prj_all["value"]
    #     if item.get("z_number") in z_number_list
    # ]

    # prj_info = [
    #     prj | {'lot_id': lot['related_id']['id'], 'lot_name': lot['related_id']['z_name']}
    #     for prj in filtered_data
    #     for lot in prj['z_sm_r_Prj_Lot']
    # ]
    # prj_info_df = pd.DataFrame(prj_info)
    # prj_info_df2 = prj_info_df[['z_destination', 'z_drive_system', 'z_model_code', 'z_number', 'z_vehicle_type']]
    # "prj_info_df2"
    # prj_info_df2
    # sql.table_insert(prj_info_df2,'dialog_list')


    # data=[]
    # for i, prj in enumerate(prj_info):
    #     lotid = prj['lot_id']
    #     # ロット下の全体パラメータを取得
    #     res, res_json, _ = aras.getLotWithAllpara(lotid)
    #     data.append(res_json)

    # para_list = [
    #     {**rel['related_id'], 'z_name': item['z_name']}
    #     for item in data
    #     for rel in item['z_sm_r_Lot_Allpara']
    # ]
    # para_list_df = pd.DataFrame(para_list)

    # para_list_df['z_design_file_check'] = [aras.get_fileName_id(idx, value) for idx, value in enumerate(para_list_df['z_design_file_check'])]
    # para_list_df = para_list_df.loc[:, 'generation':]
    # "para_list_df"
    # para_list_df

    # #sql.table_insert(para_list_df,'se_project_record')
    # #sql.detail_data_update()

    st.write("I SAID DONT")

