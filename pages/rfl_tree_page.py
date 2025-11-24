"""
Summary:
    RFLツリーページ表示モジュール
Author:
    Telema Tanaka
Created:
    2025-03-25
"""
from sqlalchemy import false
import streamlit as st
import pandas as pd
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState
from module.utils import init_session_state
from module.tree.common.builder import TreeUtils as t_builder
import module.tree.l_tree.builder as l_builder

import module.tree.r_tree.primary as r_p
import module.tree.r_tree.secondary as r_s
import module.tree.r_tree.third as r_t

import module.tree.f_tree.primary as f_p
import module.tree.f_tree.secondary as f_s
import module.tree.f_tree.third as f_t

import module.tree.effect_first.r_tree.secondary as effect_r_s
import module.tree.effect_first.r_tree.third as effect_r_t

import module.tree.effect_first.f_tree.secondary as effect_f_s
import module.tree.effect_first.f_tree.third as effect_f_t

from db.rfl_repository import RFLRepository as rflq
from module.PsqlModule import psql_class
import pandas as pd
from collections import defaultdict

sql = psql_class()

# ---init_session---
init_session_state('r_tree')
init_session_state('f_tree')
init_session_state('l_tree')
init_session_state('detail_flag')
init_session_state('secondary_tree_flag')
init_session_state('third_tree_flag')
init_session_state('f_detail_flag')
init_session_state('l_change_flag')
init_session_state('primary_f_set')
init_session_state('tree_setting')
init_session_state('tree_direction_flag')
init_session_state('view_change_flag')
init_session_state('effect_first_flag')
init_session_state('r_update_flag')
init_session_state('all_r_flag')

# ---button---
col = st.columns([3,1,1,1,1,1])

with col[0]:
    if st.button('戻る'):

        st.session_state.tree_view = False
        st.session_state.detail_flag = False
        st.session_state.secondary_tree_flag = False
        st.session_state.third_tree_flag = False
        st.session_state.r_tree = False
        st.session_state.f_tree = False
        st.session_state.l_tree = False
        st.session_state.l_change_flag = False
        st.session_state.r_update_flag = True
        st.session_state.all_r_flag = False
        st.switch_page('pages/SPDM_LIST.py')

if not st.session_state.l_tree:

    with col[1]:
        if st.button('1次影響'):
            st.session_state.third_tree_flag = False
            st.session_state.secondary_tree_flag = False
            st.rerun()
    with col[2]:
        if st.button('2次影響'):
            st.session_state.third_tree_flag = False
            st.session_state.secondary_tree_flag = True
            st.rerun()
    with col[3]:
        if st.button('3次影響'):
            st.session_state.secondary_tree_flag = False
            st.session_state.third_tree_flag = True
            st.rerun()

rfl_cols = st.columns([10,3,3,3,8,2,3,2])

if 'tree_direction' not in st.session_state:
    # initial direction
    st.session_state.tree_direction = 'right'

# ---session切り替え---
# 初期ページはR-Lのツリーを表示

if st.session_state.r_tree == []:
    # st.session_state.r_tree = True
    st.session_state.r_update_flag = True

with rfl_cols[1]:
    if st.button('R_Update'):
        st.session_state.r_tree = False
        st.session_state.f_tree = False
        st.session_state.l_tree = False
        st.session_state.l_change_flag = False
        st.session_state.secondary_tree_flag = False
        st.session_state.third_tree_flag = False
        st.session_state.r_update_flag = True
        st.session_state.all_r_flag = False
        st.session_state.all_r_tree_list = None
        st.rerun()

with rfl_cols[2]:
    if st.button('R全体ツリー'):
        st.session_state.r_tree = False
        st.session_state.f_tree = False
        st.session_state.l_tree = False
        st.session_state.l_change_flag = False
        st.session_state.secondary_tree_flag = False
        st.session_state.third_tree_flag = False
        st.session_state.r_update_flag = False
        st.session_state.all_r_flag = True
        st.session_state.r_tree_list = None

with rfl_cols[3]:
    if st.button('R'):
        st.session_state.r_tree = True
        st.session_state.f_tree = False
        st.session_state.l_tree = False
        st.session_state.l_change_flag = False
        st.session_state.secondary_tree_flag = False
        st.session_state.third_tree_flag = False
        st.session_state.r_update_flag = False
        st.session_state.all_r_flag = False
        st.rerun()

with rfl_cols[4]:
    if st.button('F'):
        st.session_state.r_tree = False
        st.session_state.f_tree = True
        st.session_state.l_tree = False
        st.session_state.l_change_flag = False
        st.session_state.secondary_tree_flag = False
        st.session_state.third_tree_flag = False
        st.session_state.r_update_flag = False
        st.session_state.all_r_flag = False
        st.rerun()

with rfl_cols[5]:
    if st.button('ALLOCATION'):
        st.session_state.r_tree = False
        st.session_state.f_tree = False
        st.session_state.l_tree = True
        st.session_state.l_change_flag = False
        st.session_state.secondary_tree_flag = False
        st.session_state.third_tree_flag = False
        st.session_state.r_update_flag = False
        st.session_state.all_r_flag = False
        st.rerun()



sub_cols = st.columns([15,15,15,1,1,1,1])

with rfl_cols[6]:

    if st.button('direction'):
        st.session_state.tree_direction_flag = not(st.session_state.tree_direction_flag)

    if st.session_state.tree_direction_flag:
        if st.button('↓'):
            st.session_state.tree_direction = 'down'
            st.rerun()
        if st.button('↑'):
            st.session_state.tree_direction = 'up'
            st.rerun()
        if st.button('→'):
            st.session_state.tree_direction = 'right'
            st.rerun()
        if st.button('←'):
            st.session_state.tree_direction = 'left'
            st.rerun()


with rfl_cols[7]:

    if st.button('viewモード切替'):
        st.session_state.view_change_flag = not(st.session_state.view_change_flag)

    if st.session_state.view_change_flag:

        if st.button('hierarchy_view'):
            st.session_state.effect_first_flag = False
            st.session_state.view_change_flag = False
            st.rerun()

        if st.button('effect_first'):
            st.session_state.effect_first_flag = True
            st.session_state.view_change_flag = False
            st.rerun()


        if st.session_state.effect_first_flag:
            st.info('NOW : effect_first_view')
        else:
            st.success('NOW : hierarchy_view_mode')


def show_df_from_r():
    """Rツリーにおいて、ノードをクリックした際RFLを表示する機能
    """

    hr =  st.session_state.curr_state.selected_id[:2]

    if hr == 'ed':
        pass
    else:
        if hr == 'v_':
            hr = '車両'
        if hr == 's_':
            hr = 'システム'
        if hr == 'u_':
            hr = 'ユニット'
        wp =  st.session_state.curr_state.selected_id[2:]
        df = rflq.posgre_get_rfl_tlm(
        st.session_state['selectoption1'],
        st.session_state['selectoption2'],
        st.session_state['selectoption3'],
        st.session_state['selectoption4'],
        st.session_state['selectoption5'],
        [hr],
        [wp],
        )

        st.session_state.rfl_list = df
        st.session_state.tree_view = False
        st.session_state.secondary_tree_flag = False
        st.switch_page('pages/SPDM_LIST.py')

def show_df_from_f():
    """Fツリーにおいて、ノードをクリックした際RFLを表示する機能
    """

    hr =  st.session_state.curr_state.selected_id[:2]

    if hr == 'ed':
        pass
    else:
        if hr == 'v_':
            hr = '車両'
        if hr == 's_':
            hr = 'システム'
        if hr == 'u_':
            hr = 'ユニット'

        no_prefix =  st.session_state.curr_state.selected_id[2:]
        wp = no_prefix[:no_prefix.find('_')]
        f_item = no_prefix[no_prefix.find('_')+1:]


        df = rflq.posgre_get_rfl_from_f(
        st.session_state['selectoption1'],
        st.session_state['selectoption2'],
        st.session_state['selectoption3'],
        st.session_state['selectoption4'],
        st.session_state['selectoption5'],
        [hr],
        [wp],
        f_item
        )

        st.session_state.rfl_list = df
        st.session_state.tree_view = False
        st.session_state.f_tree_view = False
        st.session_state.detail_flag = False
        st.switch_page('pages/SPDM_LIST.py')

def show_df_from_l():
    """Allocationツリーにおいて、ノードをクリックした際RFLを表示する機能
    """

    hr =  st.session_state.curr_state.selected_id[:2]
    no_prefix =  st.session_state.curr_state.selected_id[2:]
    wp = no_prefix[:no_prefix.rfind('_')]
    wp = no_prefix[no_prefix.rfind('_')+1:]
    if hr == 'ed':
        pass
    elif hr == 'c_':
        st.markdown(f"<p><span  style='color:#cc3300;'>{wp}</span> : 選択したノードはComponentです。RFLを表示できません。</p>", unsafe_allow_html=True)
    else:
        if hr == 'v_':
            hr = '車両'
        if hr == 's_':
            hr = 'システム'
        if hr == 'u_':
            hr = 'ユニット'

        df = rflq.posgre_get_rfl_tlm(
        st.session_state['selectoption1'],
        st.session_state['selectoption2'],
        st.session_state['selectoption3'],
        st.session_state['selectoption4'],
        st.session_state['selectoption5'],
        [hr],
        [wp],
        )

        st.session_state.rfl_list = df
        st.session_state.tree_view = False
        st.session_state.l_tree_view = False
        st.session_state.detail_flag = False
        st.session_state.l_change_flag = False

        if df.empty:
            st.markdown(f"<p><span  style='color:#cc3300;'>{wp}</span> : 選択したノードはPRJ_RFLが存在しないノードです。RFLを表示できません。</p>", unsafe_allow_html=True)
        else:
            st.switch_page('pages/SPDM_LIST.py')


#  --------------------------------------------- tree_data ------------------------------------------------------

def create_tree_element(tree,effect):
    hr = st.session_state.selected_hr[0]
    wp = st.session_state.wp[0]
    project_code = st.session_state.selectoption1[0]

    if effect == 'primary':
        if tree == 'r':
            element = rflq.get_r_primary_wps(hr,wp,project_code)
            st.session_state.primary_wps = element

            return (hr,element)

        if tree == 'f':
            element = rflq.get_f_primary_wps(hr,wp,project_code)
            st.session_state.primary_func = element
            return (hr,element)


    if effect == 'secondary':
        if tree == 'r':
            element = rflq.get_r_secondary_wps(hr,wp,project_code)
            return (hr,element)

        if tree == 'f':
            element = rflq.get_f_secondary_wps(hr,wp,project_code)
            return (hr,element)

    if effect == 'third':
        if tree == 'r':
            element = rflq.get_r_secondary_wps(hr,wp,project_code)
            return (hr,element,wp,project_code)

        if tree == 'f':
            element = rflq.get_f_secondary_wps(hr,wp,project_code)
            return (hr,element,wp,project_code)

        if tree == 'f_s':
            primary_wps = rflq.get_r_primary_wps('f_s',wp,project_code)
            secondary_wps = rflq.get_r_secondary_wps(hr,wp,project_code)
            return (hr,wp,project_code,primary_wps,secondary_wps)
#  --------------------------------------------- r_tree ------------------------------------------------------

# 1次影響
def create_r_primary_tree():
    hr,wps = create_tree_element('r','primary')

    if hr == '車両':
        nodes,edges = r_p.create_primary_v_u_flow(hr,wps)
        st.session_state.curr_state = StreamlitFlowState(nodes,edges)
        key = 'from_vehicle'

    if hr == 'システム':
        nodes,edges  = r_p.create_primary_s_flow(wps)
        key = 'from_system'
        st.session_state.curr_state = StreamlitFlowState(nodes, edges)

    if hr == 'ユニット':
        nodes,edges = r_p.create_primary_v_u_flow(hr,wps)
        st.session_state.curr_state = StreamlitFlowState(nodes,edges)
        key = 'from_unit'

    t_builder.create_flow(st.session_state.curr_state,key)


# 2次影響
def create_r_secondary_tree():
    hr,secondary_df = create_tree_element('r','secondary')
    primary_df = st.session_state.primary_wps

    if hr == '車両':
        if st.session_state.effect_first_flag:
            nodes,edges = effect_r_s.create_secondary_v_u_flow(hr,primary_df,secondary_df)
        else:
            nodes,edges = r_s.create_secondary_v_u_flow(hr,primary_df,secondary_df)
        st.session_state.curr_state = StreamlitFlowState(nodes, edges)
        key = 'secondary_v'

    if hr == 'システム':
        if st.session_state.effect_first_flag:
            nodes,edges = effect_r_s.create_secondary_s_flow(primary_df,secondary_df)
        else:
            nodes,edges = r_s.create_secondary_s_flow(primary_df,secondary_df)
        st.session_state.curr_state = StreamlitFlowState(nodes, edges)
        key = 'secondary_s'

    if hr == 'ユニット':
        if st.session_state.effect_first_flag:
            nodes,edges = effect_r_s.create_secondary_v_u_flow(hr,primary_df,secondary_df)
        else:
            nodes,edges = r_s.create_secondary_v_u_flow(hr,primary_df,secondary_df)
        st.session_state.curr_state = StreamlitFlowState(nodes, edges)
        key = 'secondary_u'
    t_builder.create_flow(st.session_state.curr_state,key)


# 3次影響
def create_r_third_tree():
    primary_df = st.session_state.primary_wps
    hr,secondary_df,wp,project_code = create_tree_element('r','third')

    if hr == '車両':
        third_df = rflq.get_r_third_wps(hr,wp,project_code)
        if st.session_state.effect_first_flag:
            nodes,edges = effect_r_t.create_third_v_u_flow(hr,primary_df,secondary_df,third_df)
        else:
            nodes,edges = r_t.create_third_v_u_flow(hr,primary_df,secondary_df,third_df)
        st.session_state.curr_state = StreamlitFlowState(nodes, edges)
        key = 'third_v'

    if hr == 'システム':
        if st.session_state.effect_first_flag:
            nodes,edges = effect_r_t.create_third_s_flow(primary_df,secondary_df,project_code)
        else:
            nodes,edges = r_t.create_third_s_flow(primary_df,secondary_df,project_code)
        st.session_state.curr_state = StreamlitFlowState(nodes, edges)
        key = 'third_s'

    if hr == 'ユニット':
        third_df = rflq.get_r_third_wps(hr,wp,project_code)
        if st.session_state.effect_first_flag:
            nodes,edges = effect_r_t.create_third_v_u_flow(hr,primary_df,secondary_df,third_df)
        else:
            nodes,edges = r_t.create_third_v_u_flow(hr,primary_df,secondary_df,third_df)
        st.session_state.curr_state = StreamlitFlowState(nodes, edges)
        key = 'third_u'

    t_builder.create_flow(st.session_state.curr_state,key)


#  --------------------------------------------- f_tree ------------------------------------------------------


def create_f_primary_tree():
    hr,wps = create_tree_element('f','primary')

    if hr == '車両':
        nodes,edges,primary_array = f_p.create_primary_v_u_flow(hr,wps)
        st.session_state.curr_state = StreamlitFlowState(nodes,edges)
        st.session_state.primary_f_set = primary_array
        key = 'from_vehicle'

    if hr == 'システム':
        nodes,edges,primary_array = f_p.create_primary_s_flow(wps)
        st.session_state.curr_state = StreamlitFlowState(nodes,edges)
        st.session_state.primary_f_set = primary_array
        key = 'from_system'

    if hr == 'ユニット':
        nodes,edges,primary_array = f_p.create_primary_v_u_flow(hr,wps)
        st.session_state.curr_state = StreamlitFlowState(nodes,edges)
        st.session_state.primary_f_set = primary_array
        key = 'from_unit'

    t_builder.create_flow(st.session_state.curr_state,key)

def create_f_secondary_tree():
    hr,secondary_df = create_tree_element('f','secondary')
    primary_df = st.session_state.primary_func
    primary_set = st.session_state.primary_f_set

    if hr == '車両':
        if st.session_state.effect_first_flag:
            nodes,edges = effect_f_s.create_secondary_v_u_flow(hr,primary_set,secondary_df)
        else:
            nodes,edges = f_s.create_secondary_v_u_flow(hr,primary_set,secondary_df)
        st.session_state.curr_state = StreamlitFlowState(nodes,edges)
        key = 'from_vehicle'

    if hr == 'システム':
        if st.session_state.effect_first_flag:
            nodes,edges = effect_f_s.create_secondary_s_flow(primary_df,secondary_df,primary_set)
        else:
            nodes,edges = f_s.create_secondary_s_flow(primary_df,secondary_df,primary_set)
        st.session_state.curr_state = StreamlitFlowState(nodes,edges)
        key = 'from_system'

    if hr == 'ユニット':
        if st.session_state.effect_first_flag:
            nodes,edges = effect_f_s.create_secondary_v_u_flow(hr,primary_set,secondary_df)
        else:
            nodes,edges = f_s.create_secondary_v_u_flow(hr,primary_set,secondary_df)
        st.session_state.curr_state = StreamlitFlowState(nodes,edges)
        key = 'from_unit'

    t_builder.create_flow(st.session_state.curr_state,key)



def create_f_third_tree():
    hr,secondary_df,wp,project_code = create_tree_element('f','third')
    primary_df = st.session_state.primary_func
    primary_set = st.session_state.primary_f_set

    if hr == '車両':
        third_df = rflq.get_f_third_wps(hr,wp,project_code)
        if st.session_state.effect_first_flag:
            nodes,edges = effect_f_t.create_third_v_u_flow(hr,primary_set,secondary_df,third_df)
        else:
            nodes,edges = f_t.create_third_v_u_flow(hr,primary_set,secondary_df,third_df)
        st.session_state.curr_state = StreamlitFlowState(nodes,edges)
        key = 'from_vehicle'

    if hr == 'システム':
        hr,wp,project_code,primary_wps,secondary_wps = create_tree_element('f_s','third')
        if st.session_state.effect_first_flag:
            nodes,edges = effect_f_t.create_third_s_flow(primary_df,secondary_df,project_code,primary_wps,secondary_wps,primary_set)
        else:
            nodes,edges = f_t.create_third_s_flow(primary_df,secondary_df,project_code,primary_wps,secondary_wps,primary_set)
        st.session_state.curr_state = StreamlitFlowState(nodes,edges)
        key = 'from_system'

    if hr == 'ユニット':
        third_df = rflq.get_f_third_wps(hr,wp,project_code)
        if st.session_state.effect_first_flag:
            nodes,edges = effect_f_t.create_third_v_u_flow(hr,primary_set,secondary_df,third_df)
        else:
            nodes,edges = f_t.create_third_v_u_flow(hr,primary_set,secondary_df,third_df)
        st.session_state.curr_state = StreamlitFlowState(nodes,edges)
        key = 'from_unit'

    t_builder.create_flow(st.session_state.curr_state,key)


def display_whole_wp():
    """全体表示切り替え関数
    """
    st.session_state.l_change_flag = False

def display_selected_wp():
    """選択表示切り替え関数
    """
    st.session_state.l_change_flag = True


def l_tree_in_pj():
    """Lツリー表示
    基準階層:車両階層
    スコープ:Project
    """

    l_tree_df = rflq.get_l_tree(st.session_state.selectoption1[0])
    key = 'l_tree_in_pj'
    l_builder.create_wp_flow(l_tree_df,False)
    t_builder.create_flow(st.session_state.curr_state,key)

    # Nodeを押下した際DFを表示
    if st.session_state.curr_state.selected_id:
        show_df_from_l()

#kayw-rfl
def r_tree_node_clicked(curr_state):

    hr =  curr_state.selected_id.split('_')[0]    
    wp =  curr_state.selected_id.split('_')[2]
    
    if hr and wp:
        if hr == 'vehicle':
            hr = '車両'
        if hr == 'system':
            hr = 'システム'
        if hr == 'unit':
            hr = 'ユニット'
        df = rflq.posgre_get_rfl_tlm(
            st.session_state['selectoption1'],
            st.session_state['selectoption2'],
            st.session_state['selectoption3'],
            st.session_state['selectoption4'],
            st.session_state['selectoption5'],
            [hr],
            [wp],
        )
        # print('hr in node clicked: ', hr)
        # print('wp in node clicked: ', wp)
        st.session_state.rfl_list = df
        st.session_state['hierarchy'] = [hr]
        st.session_state['wp'] = [wp]
        st.session_state.tree_view = False
        st.session_state.detail_flag = False
        st.session_state.secondary_tree_flag = False
        st.session_state.third_tree_flag = False
        st.session_state.r_tree = False
        st.session_state.f_tree = False
        st.session_state.l_tree = False
        st.session_state.l_change_flag = False
        st.session_state.r_update_flag = True
        st.session_state.all_r_flag = False
        st.session_state.all_r_tree_list = None
        st.session_state.r_tree_list = None
        st.session_state.secondary_tree_flag = False
        st.switch_page('pages/SPDM_LIST.py')
  
# session分岐
if st.session_state.r_tree:
    if st.session_state.secondary_tree_flag:
        create_r_secondary_tree()
    elif st.session_state.third_tree_flag:
        create_r_third_tree()
    else:
        create_r_primary_tree()

    # Nodeを押下した際DFを表示
    if st.session_state.curr_state.selected_id:
        show_df_from_r()

if st.session_state.f_tree:
    if st.session_state.secondary_tree_flag:
        create_f_secondary_tree()
    elif st.session_state.third_tree_flag:
        create_f_third_tree()
    else:
        create_f_primary_tree()

    # Nodeを押下した際DFを表示
    if st.session_state.curr_state.selected_id:
        show_df_from_f()

if st.session_state.l_tree:
        l_tree_in_pj()

def combine_item_columns(df, col1='r_item', col2='r_uc', new_col='r_item_combined'):
    """
    Combines two columns with a newline separator into a single display column.
    Used for visual node content.
    """
    if col1 in df.columns and col2 in df.columns:
        df[new_col] = df[col1].astype(str) + '\n' + df[col2].astype(str)
    return df


def filter_by_hierarchy(df, level):
    """
    Filters the dataframe by a specific hierarchy level (1=vehicle, 2=system, 3=unit).
    """
    return df[df['hierarchy_id'] == level].reset_index(drop=True)


def get_allocation_edges(source_df, target_df, source_key, target_key, source_prefix, target_prefix):
    """
    Generates edges between source and target DataFrames by matching allocation values.
    Handles type conversion and checks for validity.
    """
    edges = []
    for s_idx, s_row in source_df.iterrows():
        source_val = s_row[source_key]
        if pd.notna(source_val):
            try:
                source_int = int(float(source_val))  # Convert safely
            except (ValueError, TypeError):
                continue
            for t_idx, t_row in target_df.iterrows():
                target_val = t_row[target_key]
                if pd.notna(target_val):
                    try:
                        target_int = int(float(target_val))
                    except (ValueError, TypeError):
                        continue
                    if source_int == target_int:
                        edges.append({
                            f"{source_prefix}_idx": s_idx,
                            f"{target_prefix}_idx": t_idx,
                            f"{source_prefix}_allocation": source_val,
                            f"{target_prefix}_r_s_id": target_val
                        })
    return edges


def build_nodes(df, prefix, x_pos, wp_suffix=""):
    nodes = []
    for idx, row in df.iterrows():
        combined_data = row.get('r_item_combined', '')
        html_data = combined_data.replace('\n', '<br>').replace('~', '\\~')
        node = t_builder.create_node(
            id=f"{prefix}_{idx}{wp_suffix}",
            data=html_data,
            hr=prefix,
            pos=(x_pos, idx * 250),
            node_type='default',
            width='300px',
        )
        nodes.append(node)
    return nodes


def create_edges(connections, source_prefix, target_prefix, nodes, wp_suffix=""):
    edges = []
    for conn in connections:
        source_idx = conn[f'{source_prefix}_idx']
        target_idx = conn[f'{target_prefix}_idx']
        source_id = f"{source_prefix}_{source_idx}{wp_suffix}"
        target_id = f"{target_prefix}_{target_idx}{wp_suffix}"
        if any(n.id == source_id for n in nodes) and any(n.id == target_id for n in nodes):
            edge = t_builder.create_edge(
                id=f"edge_{source_id}_to_{target_id}",
                source=source_id,
                target=target_id,
                animated=True,
                edge_type='default',
                selected=True,
                marker_end_type='arrow'
            )
            edges.append(edge)
    return edges


def deduplicate_nodes_and_edges(nodes, edges):
    """
    Deduplicates nodes by category and content. Rewrites edge references to canonical node IDs.
    Ensures only one node per unique (prefix, content) pair.
    """
    id_canonical_map = {}
    canonical_ids = set()
    for node in nodes:
        if node.id.startswith("wp_header_"):
            continue  # skip dedup for header
        category = node.id.split('_', 1)[0]
        content = node.data.get('content') if hasattr(node, 'data') else None
        key = (category, content)
        if key not in id_canonical_map:
            id_canonical_map[key] = node.id
            canonical_ids.add(node.id)

    # Map every node.id to its canonical ID
    node_id_remap = {n.id: id_canonical_map.get((n.id.split('_', 1)[0], n.data.get('content')), n.id) for n in nodes}

    # Keep only one copy of each canonical node
    deduped_nodes = []
    seen_node_ids = set()
    for node in nodes:
        canonical_id = node_id_remap[node.id]
        if canonical_id not in seen_node_ids:
            seen_node_ids.add(canonical_id)
            deduped_nodes.append(node)

    # Deduplicate edges by (source, target) after remapping
    deduped_edges = []
    seen_pairs = set()
    for edge in edges:
        src = node_id_remap.get(edge.source, edge.source)
        tgt = node_id_remap.get(edge.target, edge.target)
        if (src, tgt) not in seen_pairs:
            seen_pairs.add((src, tgt))
            edge.id = f"edge_{src}_to_{tgt}"
            edge.source = src
            edge.target = tgt
            deduped_edges.append(edge)

    return deduped_nodes, deduped_edges


def reassign_node_positions(nodes, x_offset=0):
    pos_x = {'vehicle': 0, 'system': 450, 'unit': 900, 'wp': 450}
    y_step = 250
    categorized_nodes = defaultdict(list)

    for node in nodes:
        if isinstance(node.id, str):
            prefix = node.id.split('_')[0]
            categorized_nodes[prefix].append(node)

    rebuilt = []
    for prefix, node_list in categorized_nodes.items():
        for idx, n in enumerate(node_list):
            content = n.data.get('content') if hasattr(n, 'data') else n.data
            y_pos = idx * y_step if prefix != 'wp' else -100  # WP header stays on top
            rebuilt.append(t_builder.create_node(
                id=n.id,
                data=content,
                hr=prefix,
                pos=(pos_x.get(prefix, 0) + x_offset, y_pos),
                node_type='default',
                width='300px',
                color='white' if prefix != 'wp' else '#DDEEFF',
            ))
    return rebuilt


# Drop duplicates from rfl_list based on hierarchy type
hierarchy = st.session_state['hierarchy']
prefix = 'c'
# print('hierarchy in rfl_tree_page: ', hierarchy)
# Handle hierarchy as a list - check if any of the hierarchy values match
if isinstance(hierarchy, list):
    if '車両' in hierarchy:
        prefix = 'c'
    elif 'システム' in hierarchy:
        prefix = 's'
    elif 'ユニット' in hierarchy:
        prefix = 'u'
else:
    # Handle hierarchy as a single string (fallback)
    if hierarchy == '車両':
        prefix = 'c'
    elif hierarchy == 'システム':
        prefix = 's'
    elif hierarchy == 'ユニット':
        prefix = 'u'

# Get the column name for the project ID based on hierarchy
pj_id_column = f'{prefix}_r_pj_id'

# Check if the required project ID column exists
if pj_id_column in st.session_state.rfl_list.columns:
    # Extract unique project IDs
    unique_pj_ids = st.session_state.rfl_list[pj_id_column].drop_duplicates().tolist()
    if st.session_state.r_update_flag is True:
        # print('in r_update_flag')
        st.session_state.all_r_tree_list = None
        st.session_state.r_tree_list = None
        # Fetch tree structure data from SQL
        result_df = sql.get_r_tree(
            unique_pj_ids,
            st.session_state['selectoption5'],
            st.session_state['hierarchy'],
            st.session_state['wp'],
            'R'
        )
        st.session_state.r_tree_list = result_df
    elif st.session_state.all_r_flag is True:
        st.session_state.r_tree_list = None
        st.session_state.all_r_tree_list = None
        # Fetch tree structure data from SQL
        result_df = sql.get_r_tree(
            unique_pj_ids,
            st.session_state['selectoption5'],
            st.session_state['hierarchy'],
            [],
            'ALL_R'
        )
        st.session_state.all_r_tree_list = result_df



if st.session_state.r_tree_list is not None:
    result_df = st.session_state.r_tree_list

    wp_spacing = 1500  # spacing between each r_wp tree
    x_offset = 0

    unique_r_wp = result_df['r_wp'].dropna().unique().tolist()

    all_nodes = []
    all_edges = []


    for idx, wp in enumerate(unique_r_wp):

        wp_suffix = f"_{wp}"
        wp_df = result_df[result_df['r_wp'] == wp].copy()
        wp_df = wp_df.sort_values(by=['hierarchy_id', 'r_wp_ld', 'index'])
        wp_df = combine_item_columns(wp_df)
        st.write('wp_df: ', wp_df)
        # Split data by hierarchy level
        vehicle_df = filter_by_hierarchy(wp_df, 1)[['rfl_id','r_item_combined', 'l_s_id', 'r_s_id','allocation']]
        st.write('vehicle_df: ', vehicle_df)
        st.write('drop v:', vehicle_df.dropna(subset=['allocation'], inplace=False).sort_values(by='allocation').reset_index(drop=True))
        system_df  = filter_by_hierarchy(wp_df, 2)[['rfl_id','r_item_combined', 'l_s_id', 'r_s_id','allocation']]
        st.write('system_df: ', system_df.sort_values(by='r_s_id').reset_index(drop=True))
        unit_df    = filter_by_hierarchy(wp_df, 3)[['rfl_id','r_item_combined', 'l_s_id', 'r_s_id','allocation']]
        st.write('unit_df: ', unit_df.sort_values(by='r_s_id').reset_index(drop=True))
        # Build edges based on allocation matches
        vehicle_system_edges = get_allocation_edges(vehicle_df, system_df, 'allocation', 'r_s_id', 'vehicle', 'system')
        system_unit_edges = get_allocation_edges(system_df, unit_df, 'allocation', 'r_s_id', 'system', 'unit')
        vehicle_unit_edges = []

        # Fallback edge logic if system level is missing
        if system_df.empty:
            vehicle_unit_edges = get_allocation_edges(vehicle_df, unit_df, 'allocation', 'r_s_id', 'vehicle', 'unit')

        # Generate nodes per hierarchy group
        nodes = build_nodes(vehicle_df, 'vehicle', x_offset + 0, wp_suffix) + \
                build_nodes(system_df, 'system', x_offset + 450, wp_suffix) + \
                build_nodes(unit_df, 'unit', x_offset + 900, wp_suffix)

        # Generate visual edges
        edges = create_edges(vehicle_system_edges, 'vehicle', 'system', nodes, wp_suffix) + \
                create_edges(system_unit_edges, 'system', 'unit', nodes, wp_suffix) + \
                create_edges(vehicle_unit_edges, 'vehicle', 'unit', nodes, wp_suffix)

        # Deduplicate nodes and edges
        nodes, edges = deduplicate_nodes_and_edges(nodes, edges)

        

        # Recalculate node positions to avoid overlap
        nodes = reassign_node_positions(nodes, x_offset=x_offset)
        all_nodes.extend(nodes)
        all_edges.extend(edges)
        x_offset += wp_spacing

    # If nodes exist, render flow diagram
    if all_nodes:
        # st.write('all node',all_nodes)
        # st.write('all edge',all_edges)
        st.session_state.r_curr_state = StreamlitFlowState(all_nodes, all_edges)
        updated_state = streamlit_flow(
            "rfl_r_tree_flow",
            state=st.session_state.r_curr_state,
            height=1000,
            fit_view=True,
            hide_watermark=True,
            allow_new_edges=False,
            enable_node_menu=True,
            enable_edge_menu=True,
            enable_pane_menu=True,
            get_edge_on_click=True,
            get_node_on_click=True,
            min_zoom=0.1
        )

        # Update state if diagram was modified
        if updated_state:
            st.session_state.r_curr_state = updated_state

        # Check if any node was clicked
        selected_id = st.session_state.r_curr_state.selected_id
        if selected_id:
            if any(n.id == selected_id for n in nodes):
                # st.write('Node clicked! Selected ID:', selected_id)
                r_tree_node_clicked(st.session_state.r_curr_state)  # Your custom handler


def get_allocation_edges_grouped(source_df, target_df, group_key, allocation_key, target_key, source_prefix, target_prefix):
    """
    Creates edges from each source node to all target nodes sharing the same group_key (e.g., 'r_s_id').
    Includes debug prints to trace data.
    """


    grouped_source_df = source_df.groupby(['r_s_id'],sort=False)

    grouped_target_df = target_df.drop_duplicates(subset=['r_item_combined']).reset_index(drop=True)
    edges = []

    for s_idx, (s_key, s_df) in enumerate(grouped_source_df):

        # s_df may contain multiple rows — loop through each if needed
        for _, s_row in s_df.iterrows():
            allocation_val = s_row['allocation']

            for t_idx, t_row in grouped_target_df.iterrows():
                r_s_id_val = t_row['r_s_id']

                if r_s_id_val == allocation_val:
                    edges.append({
                        f"{source_prefix}_idx": s_idx,
                        f"{target_prefix}_idx": t_idx,
                        f"{source_prefix}_allocation": allocation_val,
                        f"{target_prefix}_r_s_id": r_s_id_val
                    })

    return edges

if st.session_state.all_r_tree_list is not None:
    df = st.session_state.all_r_tree_list

    if isinstance(df, pd.DataFrame):

        grouped = df.groupby('r_wp')
        all_nodes = []
        all_edges = []

        # Define fixed Y positions and node prefix for each hierarchy
        hierarchy_positions = {
            '車両': {'y': 0, 'prefix': 'vehicle'},
            'システム': {'y': 450, 'prefix': 'system'},
            'ユニット': {'y': 900, 'prefix': 'unit'}
        }

        # Track X offset for each hierarchy across all WPs
        hierarchy_max_x = {key: 0 for key in hierarchy_positions}

        for wp_value, group_df in grouped:
            # st.subheader(f"WP: {wp_value}")
            wp_df = group_df.copy()
            wp_df['r_item_combined'] = wp_df['r_item'].astype(str) + '\n' + wp_df['r_uc'].astype(str)
            wp_suffix = f"_{wp_value}"

            hierarchy_dfs = {}

            vehicle_df = filter_by_hierarchy(wp_df, 1)[['r_item_combined', 'l_s_id', 'r_s_id','allocation']]
            # st.write(f'vehicle df: ', vehicle_df)
            # vehicle_gp_df = vehicle_df.drop_duplicates(subset=['r_s_id']).reset_index(drop=True)
            # st.write(f'vehicle_gp_df: ', vehicle_gp_df)

            system_df  = filter_by_hierarchy(wp_df, 2)[['r_item_combined', 'l_s_id', 'r_s_id','allocation']]
            # st.write('system df: ', system_df)
            # system_gp_df = system_df.drop_duplicates(subset=['r_s_id']).reset_index(drop=True)
            # st.write(f'system_gp_df: ', system_gp_df)

            unit_df    = filter_by_hierarchy(wp_df, 3)[['r_item_combined', 'l_s_id', 'r_s_id','allocation']]
            # st.write('unit df: ', unit_df)
            # unit_gp_df = unit_df.drop_duplicates(subset=['r_s_id']).reset_index(drop=True)
            # st.write(f'unit_gp_df: ', unit_gp_df)

            vehicle_system_edges = []
            system_unit_edges = []
            vehicle_unit_edges = []


            for h_key, pos_conf in hierarchy_positions.items():
                prefix = pos_conf['prefix']
                y = pos_conf['y']
                x_offset = hierarchy_max_x[h_key]

                h_df = wp_df[wp_df['hierarchy'] == h_key].copy()
                if h_df.empty:
                    continue

                h_df = h_df.drop_duplicates(subset=['r_item_combined']).reset_index(drop=True)
                h_df['node_idx'] = h_df.index  # Local index within WP and hierarchy

                # Save hierarchy-specific df for edge construction later
                hierarchy_dfs[h_key] = h_df

                # Create nodes
                for idx, row in h_df.iterrows():
                    x_pos = x_offset + idx * 350
                    label_html = row['r_item_combined'].replace('\n', '<br>').replace('~', '\\~')
                    node_id = f"{prefix}_{idx}{wp_suffix}"

                    node = t_builder.create_node(
                        id=node_id,
                        data=label_html,
                        hr=prefix,
                        pos=(x_pos, y),
                        node_type='default',
                        width='300px'
                    )
                    all_nodes.append(node)

                # Update max X position for this hierarchy
                hierarchy_max_x[h_key] += len(h_df) * 350 #+ 350  # Add spacing after last node

            # vehicle_system_edges = get_allocation_edges(vehicle_df, system_df, 'allocation', 'r_s_id', 'vehicle', 'system')
            vehicle_system_edges = get_allocation_edges_grouped(
                vehicle_df, system_df, 
                group_key='r_s_id', allocation_key='allocation', target_key='r_s_id',
                source_prefix='vehicle', target_prefix='system'
            )


            # system_unit_edges = get_allocation_edges(system_df, unit_df, 'allocation', 'r_s_id', 'system', 'unit')
            system_unit_edges = get_allocation_edges_grouped(
                system_df, unit_df,
                group_key='r_s_id', allocation_key='allocation', target_key='r_s_id',
                source_prefix='system', target_prefix='unit'
            )

            vehicle_unit_edges = []
            if system_df.empty:
                vehicle_unit_edges = get_allocation_edges_grouped(
                    vehicle_df, unit_df,
                    group_key='r_s_id', allocation_key='allocation', target_key='r_s_id',
                    source_prefix='vehicle', target_prefix='unit'
                )

            # Create visual edges
            edges = create_edges(vehicle_system_edges, 'vehicle', 'system', all_nodes, wp_suffix) + \
                    create_edges(system_unit_edges, 'system', 'unit', all_nodes, wp_suffix) + \
                    create_edges(vehicle_unit_edges, 'vehicle', 'unit', all_nodes, wp_suffix)

            all_edges.extend(edges)

        # ---- Render Flow ----
        if all_nodes:
            # st.write('all node:', all_nodes)
            # st.write('all edge: ', all_edges)
            # print("Combined R Tree Flow")
            st.session_state.all_r_curr_state = StreamlitFlowState(all_nodes, all_edges)
            update_state = streamlit_flow(
                "combined_r_tree_flow",
                state=st.session_state.all_r_curr_state,
                height=1200,
                fit_view=True,
                hide_watermark=True,
                show_minimap=False,
                allow_new_edges=False,
                enable_node_menu=True,
                enable_edge_menu=True,
                enable_pane_menu=True,
                get_edge_on_click=True,
                get_node_on_click=True,
                min_zoom=0.1
            )

            if update_state:
                st.session_state.all_r_curr_state = update_state

            # Check if any node was clicked
            selected_id = st.session_state.all_r_curr_state.selected_id
            if selected_id:
                if any(n.id == selected_id for n in all_nodes):
                    r_tree_node_clicked(st.session_state.all_r_curr_state)  # Your custom handler
    else:
        st.error("`all_r_tree_list` is not a pandas DataFrame.")