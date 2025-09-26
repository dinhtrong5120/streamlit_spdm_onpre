"""
Summary:
    RFLツリーページ表示モジュール
Author:
    Telema Tanaka
Created:
    2025-03-25
"""

import streamlit as st
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState
from streamlit_flow.layouts import TreeLayout, RadialLayout
from uuid import uuid4
from module.utils import init_session_state
from module.rfl_tree_viewer import create_hierarchy_flow as create_hr_flow,TreeUtils as t_utils,create_function_flow as create_f_flow,create_allocation_flow as create_l_flow
from db.rfl_repository import RFLRepository as rflq

# ---button---
col = st.columns([3,1,1,1])

with col[0]:
    if st.button('戻る'):
        st.session_state.tree_view = False
        st.session_state.detail_flag = False
        st.session_state.r_tree = True
        st.session_state.f_tree = False
        st.session_state.l_tree = False
        st.session_state.l_change_flag = False
        st.switch_page('pages/SPDM_LIST.py')

rfl_cols = st.columns([10,1,1,1,1])

# ---init_session---
init_session_state('r_tree')
init_session_state('f_tree')
init_session_state('l_tree')
init_session_state('detail_flag')
init_session_state('f_detail_flag')
init_session_state('l_change_flag')

if 'tree_direction' not in st.session_state:
    st.session_state.tree_direction = 'down'

sub_cols = st.columns([4,1,1,1])
# ---session切り替え---
# 初期ページはR-Lのツリーを表示

if st.session_state.r_tree == []:
    st.session_state.r_tree = True

with rfl_cols[1]:
    if st.button('R'):
        st.session_state.r_tree = True
        st.session_state.f_tree = False
        st.session_state.l_tree = False
        st.session_state.l_change_flag = False

with rfl_cols[2]:
    if st.button('F'):
        st.session_state.r_tree = False
        st.session_state.f_tree = True
        st.session_state.l_tree = False
        st.session_state.l_change_flag = False

with rfl_cols[3]:
    if st.button('ALLOCATION'):
        st.session_state.r_tree = False
        st.session_state.f_tree = False
        st.session_state.l_tree = True
        st.session_state.l_change_flag = False

sub_cols = st.columns([15,15,15,1,1,1,1])

with rfl_cols[4]:
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
        st.session_state.detail_flag = False
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
        # wp = no_prefix[:no_prefix.rfind('_')]
        # f_item = no_prefix[no_prefix.rfind('_')+1:]
        wp = no_prefix[:no_prefix.find('_')]
        f_item = no_prefix[no_prefix.find('_')+1:]
        print(wp)


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

def tree_from_vehicle():
    """Rツリー表示
    基準階層:車両階層
    """

    wp = st.session_state.wp[0]
    key = 'from_vehicle'
    wps = rflq.get_wps(wp,'車両')
    print('wp in tree_from_vehicle:', wp)
    print('wps in tree_from_vehicle:', wps)

    create_hr_flow(wp,wps)
    t_utils.create_flow(st.session_state.curr_state,key)

    # Nodeを押下した際DFを表示
    if st.session_state.curr_state.selected_id:
        show_df_from_r()

def tree_from_below_vehicle():
    """Rツリー表示
    基準階層:システム階層以下
    """

    # tree構築
    hierarchy = st.session_state.selected_hr[0]
    if not st.session_state.detail_flag :

        if hierarchy == 'システム':
            key = 'from_system'

        if hierarchy == 'ユニット':
            key = 'from_unit'
        print('hierarchy: ', hierarchy)
        print('st session wp: ', st.session_state.wp)
        print('st session wp2: ', st.session_state.wp[0])
        wps = rflq.get_wps(st.session_state.wp[0],hierarchy)
        print('wps: ', wps)
        top_hierarchy = wps.iat[0,0]
        print('top_hierarchy: ', top_hierarchy)
        create_hr_flow(top_hierarchy,wps)
        t_utils.create_flow(st.session_state.curr_state,key)

        with col[1]:
            if st.button('全体表示'):
                st.session_state.detail_flag = True
                st.rerun()

    elif st.session_state.detail_flag:

        if hierarchy == 'システム':
            detail_key = 'from_system_detail'

        if hierarchy == 'ユニット':
            detail_key = 'from_unit_detail'

        wps = rflq.get_wps(st.session_state.tree_top_hierarchy,'車両')
        create_hr_flow(st.session_state.tree_top_hierarchy,wps)
        t_utils.create_flow(st.session_state.curr_state,detail_key)

        with col[1]:
            if st.button('単独表示'):
                st.session_state.detail_flag = False
                st.rerun()

    # Nodeを押下した際DFを表示
    if st.session_state.curr_state.selected_id:
        show_df_from_r()

def f_tree_from_vehicle():
    """Fツリー表示
    基準階層:車両
    """

    key = 'function_tree'
    hr = st.session_state.selected_hr[0]
    wp = st.session_state.wp[0]
    print('---------------result-----------------------')
    print(wp)
    print(hr)
    print('--------------------------------------')
    result = rflq.get_functions_on_related_wps(wp,hr)
    create_f_flow(result)

    t_utils.create_flow(st.session_state.curr_state,key)
    # Nodeを押下した際DFを表示
    if st.session_state.curr_state.selected_id:
        show_df_from_f()

def f_tree_from_below_vehicle():
    """Fツリー表示
    基準階層:システム以下
    """

    hierarchy = st.session_state.selected_hr[0]
    if not st.session_state.f_detail_flag :

        if hierarchy == 'システム':
            key = 'f_from_system'

        if hierarchy == 'ユニット':
            key = 'f_from_unit'

        wps = rflq.get_functions_on_related_wps(st.session_state.wp[0],hierarchy)
        create_f_flow(wps)

        st.session_state.f_top_hierarchy = wps.iat[0,0]
        t_utils.create_flow(st.session_state.curr_state,key)

        with col[1]:
            if st.button('全体表示'):
                st.session_state.f_detail_flag = True
                st.rerun()

    elif st.session_state.f_detail_flag:

        if hierarchy == 'システム':
            detail_key = 'f_from_system_detail'

        if hierarchy == 'ユニット':
            detail_key = 'f_from_unit_detail'
        print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
        print(st.session_state.f_top_hierarchy)
        print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
        wps = rflq.get_functions_on_related_wps(st.session_state.f_top_hierarchy,'車両')
        create_f_flow(wps)

        t_utils.create_flow(st.session_state.curr_state,detail_key)

        with col[1]:
            if st.button('単独表示'):
                st.session_state.f_detail_flag = False
                st.rerun()

    # Nodeを押下した際DFを表示
    if st.session_state.curr_state.selected_id:
        show_df_from_f()

def display_whole_wp():
    """全体表示切り替え関数
    """
    st.session_state.l_change_flag = False

def display_selected_wp():
    """選択表示切り替え関数
    """
    st.session_state.l_change_flag = True

def l_tree_from_vehicle():
    """Lツリー表示
    基準階層:車両階層
    """

    all_vwp = rflq.get_all_vwp()
    st.session_state.vwp_map = dict(zip(all_vwp['wp'],all_vwp['id']))
    option_vwp = all_vwp['wp'].tolist()

    # 全体表示
    if not st.session_state.l_change_flag:
        key = 'wp_tree'
        create_l_flow(all_vwp)
        t_utils.create_flow(st.session_state.curr_state,key)
        st.session_state.selected_wp = []

        with col[1]:
            st.button('領域選択表示',on_click=display_selected_wp)

    # 選択表示
    else:
        key = 'selected_wp_tree'
        if st.session_state.selected_wp:
            create_l_flow(st.session_state.selected_wp)
            t_utils.create_flow(st.session_state.curr_state,key)

        with col[1]:
            st.button('全体表示',on_click=display_whole_wp)

        with col[2]:
            selected_wp = st.multiselect(
                '領域',
                option_vwp,
                key = 'wp_select_key',
            )

        with col[3]:
            if st.button('選択表示'):
                st.session_state.selected_wp = selected_wp
                st.rerun()

    # Nodeを押下した際DFを表示
    if st.session_state.curr_state.selected_id:
        show_df_from_l()

# session分岐
if st.session_state.r_tree:
    if st.session_state.selected_hr[0] == '車両':
        tree_from_vehicle()
    else:
        tree_from_below_vehicle()

if st.session_state.f_tree:
    if st.session_state.selected_hr[0] == '車両':
        f_tree_from_vehicle()
    else:
        f_tree_from_below_vehicle()

if st.session_state.l_tree:
        l_tree_from_vehicle()