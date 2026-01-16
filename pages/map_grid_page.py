import pandas as pd
import streamlit as st
import const.constpara as co
import extra_streamlit_components as stx
from st_aggrid import AgGrid, JsCode
import datetime
import json
import module.dialog as dia
import module.grid_option as gop
from module.PsqlModule import psql_class
import time
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

cell_highlight = JsCode("""
function(params) {
	if(params.node.rowIndex() === 0){
		return{
			"backgroundColor":"#000000"
		}
	};
	return null;
}
""")



if 'df_display' not in st.session_state or 'row' not in st.session_state or 'mode' not in st.session_state or 'df_map_variables' not in st.session_state or 'vallist' not in st.session_state:
    print('not enough')
    st.switch_page("./pages/SPDM_LIST.py")
    
if 'df_edited' not in st.session_state: 
    st.session_state.df_edited=None
def back_to_SPDM_LIST():
    st.session_state.df_display=None
    st.session_state.row = None
    st.session_state.mode = None
    st.session_state.df_map_variables=None
    st.session_state.vallist = None
    st.switch_page("./pages/SPDM_LIST.py")
    
def update_map():
    #  セッションすてーとない必要変数の用意
    row = st.session_state.row
    mode = st.session_state.mode
    df_map_variables = st.session_state.df_map_variables
    vallist = st.session_state.vallist
    df_edited =st.session_state.df_edited
    
    #ここからdialog.py mapgridの処理と同じ
    project_id=row['project_id']
    parameter_id=None
    if int(st.session_state.chosen_id)==1:
        print("seid")
        map_name= row['z_request_median']
        parameter_id=row['se_parameter_id']
    elif int(st.session_state.chosen_id)==3:
        print("simid")
        map_name= row['value']
        parameter_id=row['senario_parameter_id']
    phase_id=row['phase_id']
    variation_id=row['variation_id']
    xcount= len(df_map_variables[df_map_variables['axis']=='X'])
    ycount=len(df_map_variables[df_map_variables['axis']=='Y'])
    mapcount=len(df_map_variables[df_map_variables['axis']=='MAP'])
    tablecount=len(df_map_variables[df_map_variables['axis']=='TABLE'])
    
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
        z_paravalueid=rpw['id']
    username=st.session_state.username
    now = datetime.datetime.now()
    #一度軸あっているかだけ確認する
    not_valid=False
    if mode=='MAP':
        df_X=df_map_variables[df_map_variables['axis']=='X']
        df_Y=df_map_variables[df_map_variables['axis']=='Y']
        df_MAP=df_map_variables[df_map_variables['axis']=='MAP']
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
        
    elif mode=='TABLE':#ここも後で実装
        df_X=df_map_variables[df_map_variables['axis']=='X']
        df_TABLE=df_map_variables[df_map_variables['axis']=='TABLE']
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
        dia.success_dia()
        time.sleep(1)
        st.rerun()
        st.switch_page("./pages/SPDM_LIST.py")
    
    
    
   
   
def main():
    flag_update=False
    col1, col2,col3 = st.columns([1,6,1])
    with col1:
        if st.button("戻る"):
            back_to_SPDM_LIST()
    with col3:
        if st.button("確定"):
            flag_update=True
    df_display = st.session_state.df_display
    vallist = st.session_state.vallist
    mode = st.session_state.mode
    
    #gb = GridOptionsBuilder.from_dataframe(df_display)
    #gb.configure_default_column(editable=True, cellStyle=cell_highlight)
    #gridOptions = gb.build()
    
    

    mapop = gop.make_mapop()
    mapop["cellStyle"] = cell_highlight
    if df_display is not None and mode is not None:
        
        for i, v in enumerate(vallist):
            st.markdown(v)
        st.session_state.df_edited = st.data_editor(df_display, height=3600, hide_index=True)
        #ag_response=AgGrid(
        #df_display,
        #gridOptions=mapop,
        #allow_unsafe_jscode=True
        
        #)
        #st.session_state.df_edited = ag_response['data']
    
    if flag_update:
        st.write("boom")
        update_map()

if __name__ == "__main__":
    main()


