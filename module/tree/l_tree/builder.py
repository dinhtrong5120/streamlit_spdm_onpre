"""
Summary:
    RFLツリー作成モジュール
Author:
    Telema Tanaka
Created:
    2025-03-25
Updated:
    2025-07-15
    大幅修正
"""

import streamlit as st
from streamlit_flow.state import StreamlitFlowState
from module.utils import init_session_state
from module.tree.common.builder import TreeUtils as t_builder


# treeのdiff作成
def create_diff_list(array,base):
    """treeのdiffリストを作成

    Args:
        array (list): 全体表示対象のノード群
        base (list): 通常表示のノード群

    Returns:
        list: diff list
    """
    diff = [row for row in array if row not in base]

    base_values = set()
    diff_values = set()
    for row in diff:
        diff_values.update(row)
    for row in base:
        base_values.update(row)
    diff_list = (list(diff_values - base_values))

    return diff_list


# L Tree
def create_wp_flow(df,flag,x_offset=150,y_offset=150):
    """ALLOCATIONツリーを作成

    Args:
        df (dataframe): l_dataframe
    """

    prefixes = ['v_','s_','u_','c_']
    array = []
    nodes = []
    edges = []
    columns = df.columns.tolist()
    for index, row in df.iterrows():
        array.append(row[columns].tolist())

    org_top = st.session_state.wp[0]

    init_session_state('session_state.base_tree_array')
    init_session_state('session_state.detail_tree_array')
    if not flag :
        st.session_state.base_tree_array = array

        for i,row in enumerate(array):
            v_id = prefixes[0] + row[0]
            s_id = prefixes[1] + row[1]
            u_id = prefixes[2] + row[2]
            pos = (x_offset,i*y_offset)

            # vehicle node
            nodes.append(t_builder.create_node(
                id = v_id,
                pos = pos,
                data = row[0],
                hr = 'vehicle'
                )
            )

            # system node
            nodes.append(t_builder.create_node(
                id = s_id,
                pos = pos,
                data = row[1],
                hr = 'system'
                )
            )

            # unit node
            nodes.append(t_builder.create_node(
                id = u_id,
                pos = pos,
                data = row[2],
                hr = 'unit'
                )
            )

            v_s_edge = 'step'
            s_u_edge = 'step'
            animated = False

            # system edge
            edges.append(t_builder.create_edge(
                    id = f'edge_{row[0]}-{row[1]}',
                    source = v_id,
                    target = s_id,
                    animated = animated,
                    edge_type = v_s_edge
                    )
                )

            # unit edge
            edges.append(t_builder.create_edge(
                    id = f'edge_{row[1]}-{row[2]}',
                    source = s_id,
                    target = u_id,
                    animated = animated,
                    edge_type = s_u_edge
                    )
                )
    if flag :
        diff_list = create_diff_list(array,st.session_state.base_tree_array)

        for i,row in enumerate(array):
                v_id = prefixes[0] + row[0]
                s_id = prefixes[1] + row[1]
                u_id = prefixes[2] + row[2]
                pos = (x_offset,i*y_offset)

                # vehicle node
                nodes.append(t_builder.create_node(
                    id = v_id,
                    pos = pos,
                    data = row[0],
                    hr = 'vehicle'
                    )
                )

                # system node
                nodes.append(t_builder.create_node(
                    id = s_id,
                    pos = pos,
                    data = row[1],
                    hr = 'system'
                    )
                )

                # unit node
                nodes.append(t_builder.create_node(
                    id = u_id,
                    pos = pos,
                    data = row[2],
                    hr = 'unit'
                    )
                )


                v_s_edge = 'step'
                v_s_animated = False
                s_u_edge = 'step'
                s_u_animated = False

                if row[0] in diff_list:
                    v_s_edge = 'default'
                    v_s_animated = True

                if row[1] in diff_list or row[2] in diff_list:
                    s_u_edge = 'default'
                    s_u_animated = True

                # system edge
                edges.append(t_builder.create_edge(
                        id = f'edge_{row[0]}-{row[1]}',
                        source = v_id,
                        target = s_id,
                        animated = v_s_animated,
                        edge_type = v_s_edge
                        )
                    )

                # unit edge
                edges.append(t_builder.create_edge(
                        id = f'edge_{row[1]}-{row[2]}',
                        source = s_id,
                        target = u_id,
                        animated = s_u_animated,
                        edge_type = s_u_edge
                        )
                    )

    st.session_state.curr_state = StreamlitFlowState(nodes, edges)