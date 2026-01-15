"""
Summary:
    R_TREE
Author:
    Telema Tanaka
Created:
    2025-03-25
Updated:
    2025-07-15
    大幅修正
"""

from module.tree.r_tree.primary import create_primary_s_flow as create_primary_s
from module.tree.common.builder import TreeUtils as t_builder
import streamlit as st
from config.config import effect_font_color_defs as font_color_def,effect_edge_color_defs as edge_color_def

# ------------ 2次影響 ------------
# Vehicle,Unit
def create_secondary_v_u_flow(hierarchy,primary_df,secondary_df):
    """Vehicle,Unitの2次影響ツリー作成

    Args:
        hr (String): vehicle/unit
        primary_df (DataFrame): 1次影響data
        secondary_df (DataFrame): 2次影響data
    """

    prefixes = ['v_','s_','u_','c_']
    secondary_array = []
    nodes = []
    edges = []

    secondary_array = secondary_df.values.tolist()
    # st.write('primary_df: ', primary_df)
    # st.write('secondary_df: ', secondary_df)
    # st.write('secondary_array: ', secondary_array)

    primary_df_values_set = set(primary_df.values.ravel())
    secondary_df_values_set = set(secondary_df.values.ravel())
    secondary_common_values = list(primary_df_values_set & secondary_df_values_set)
    primary_color = font_color_def['primary_color']
    secondary_color = font_color_def['secondary_color']

    primary_edge_color = edge_color_def['primary_color']
    secondary_edge_color = edge_color_def['secondary_color']


    for row in (secondary_array):
            v_wp = row[0]
            s_wp = row[1]
            u_wp = row[2]

            v_id = prefixes[0] + v_wp
            s_id = prefixes[1] + s_wp
            u_id = prefixes[2] + u_wp

            v_s_edge = 'step'
            v_s_animated = False
            s_u_edge = 'step'
            s_u_animated = False
            v_s_marker_start_type = None
            s_u_marker_end_type = None
            v_color = primary_color
            u_color = primary_color

            v_s_edge_color = primary_edge_color
            s_u_edge_color = primary_edge_color


            if hierarchy == '車両':
                secondary_wp = row[3]
                v_wp = secondary_wp
                v_id = prefixes[0] + v_wp
                s_u_edge = 'default'
                s_u_animated = True
                s_u_marker_end_type = 'arrowclosed'
                u_color = secondary_color
                s_u_edge_color = secondary_edge_color

                if secondary_wp not in secondary_common_values:
                    v_s_edge = 'default'
                    v_s_animated = True
                    v_s_marker_start_type = 'arrowclosed'
                    v_color = secondary_color
                    v_s_edge_color = secondary_edge_color

            if hierarchy == 'ユニット':
                secondary_wp = row[3]
                u_wp = secondary_wp
                u_id = prefixes[2] + u_wp
                v_s_edge = 'default'
                v_s_animated = True
                v_s_marker_start_type = 'arrowclosed'
                v_color = secondary_color
                v_s_edge_color = secondary_edge_color

                if secondary_wp not in secondary_common_values:
                    s_u_edge = 'default'
                    s_u_animated = True
                    s_u_marker_end_type = 'arrowclosed',
                    u_color = secondary_color
                    s_u_edge_color = secondary_edge_color

            # vehicle node
            nodes.append(t_builder.create_node(
                id = v_id,
                data = v_wp,
                hr = 'vehicle',
                color = v_color
                )
            )

            # system node
            nodes.append(t_builder.create_node(
                id = s_id,
                data = s_wp,
                hr = 'system'
                )
            )

            # secondary_node
            nodes.append(t_builder.create_node(
                id = u_id,
                data = u_wp,
                hr = 'unit',
                color = u_color
                )
            )

            edges.append(t_builder.create_edge(
                    id = f'edge_{v_wp}-{s_wp}',
                    source = v_id,
                    target = s_id,
                    animated = v_s_animated,
                    edge_type = v_s_edge,
                    marker_start_type = v_s_marker_start_type,
                    edge_color = v_s_edge_color
                    )
                )

            # system - unit edge
            edges.append(t_builder.create_edge(
                    id = f'edge_{s_wp}-{u_wp}',
                    source = s_id,
                    target = u_id,
                    animated = s_u_animated,
                    edge_type = s_u_edge,
                    marker_end_type = s_u_marker_end_type,
                    edge_color = s_u_edge_color
                    )
                )

    st.write('nodes count: ', len(nodes))
    st.write('edges count: ', len(edges))
    return (nodes,edges)

# ------------ 2次影響 ------------
# System
def create_secondary_s_flow(primary_df,secondary_df):
    """ALLOCATIONツリーを作成

    Args:
        df (dataframe): l_dataframe
    """

    prefixes = ['v_','s_','u_','c_']
    nodes = []
    edges = []

    secondary_array = secondary_df.values.tolist()
    # st.write('secondary_array: ', secondary_array)
    # 共通値抽出
    primary_df_values_set = set(primary_df.values.ravel())
    secondary_df_values_set = set(secondary_df.values.ravel())
    common_values = list(primary_df_values_set & secondary_df_values_set)
    # st.write('primary_df_values_set: ', primary_df_values_set)
    # st.write('secondary_df_values_set: ', secondary_df_values_set)
    # st.write('common_values: ', common_values)

    # nodes,edges = create_primary_s(primary_df)

    primary_color = font_color_def['primary_color']
    secondary_color = font_color_def['secondary_color']

    primary_edge_color = edge_color_def['primary_color']
    secondary_edge_color = edge_color_def['secondary_color']
    # st.write('primary_color: ', primary_color)
    # st.write('secondary_color: ', secondary_color)
    # st.write('primary_edge_color: ', primary_edge_color)
    # st.write('secondary_edge_color: ', secondary_edge_color)

    for row in (secondary_array):

            v_wp = row[0]
            s_wp = row[1]
            s2_wp = row[2]
            u_wp = row[3]
            # st.write('row: ', row)
            # st.write('v_wp: ', v_wp)
            # st.write('s_wp: ', s_wp)
            # st.write('s2_wp: ', s2_wp)
            # st.write('u_wp: ', u_wp)

            v_id = prefixes[0] + v_wp
            s_id = prefixes[1] + s_wp
            s2_id = prefixes[1] + s2_wp
            u_id = prefixes[2] + u_wp
            # st.write('v_id: ', v_id)
            # st.write('s_id: ', s_id)
            # st.write('s2_id: ', s2_id)
            # st.write('u_id: ', u_id)


            # 基本設定
            v_s_edge = 'step'
            v_s_animated = False
            s_u_edge = 'step'
            s_u_animated = False
            s_color = primary_color
            s2_color = primary_color

            v_s_edge_color = primary_edge_color
            s_u_edge_color = primary_edge_color

            marker_start_type = None
            marker_end_type = None
            # st.write('init v_s_edge: ', v_s_edge)
            # st.write('init v_s_animated: ', v_s_animated)
            # st.write('init s_u_edge: ', s_u_edge)
            # st.write('init s_u_animated: ', s_u_animated)
            # st.write('init s_color: ', s_color)
            # st.write('init s2_color: ', s2_color)
            # st.write('init v_s_edge_color: ', v_s_edge_color)
            # st.write('init s_u_edge_color: ', s_u_edge_color)
            # st.write('init marker_start_type: ', marker_start_type)
            # st.write('init marker_end_type: ', marker_end_type)



            # 2次接続の場合、破線にする
            if s_wp not in common_values:
                v_s_edge = 'default'
                v_s_animated = True
                marker_end_type = 'arrowclosed'
                s_color = secondary_color
                v_s_edge_color = secondary_edge_color
                # st.write('s_wp not in common_values -> update:')
                # st.write('v_s_edge: ', v_s_edge)
                # st.write('v_s_animated: ', v_s_animated)
                # st.write('marker_end_type: ', marker_end_type)
                # st.write('s_color: ', s_color)
                # st.write('v_s_edge_color: ', v_s_edge_color)

            if s2_wp not in common_values:
                s_u_edge = 'default'
                s_u_animated = True
                marker_start_type = 'arrowclosed'
                s2_color = secondary_color
                s_u_edge_color = secondary_edge_color
                # st.write('s2_wp not in common_values -> update:')
                # st.write('s_u_edge: ', s_u_edge)
                # st.write('s_u_animated: ', s_u_animated)
                # st.write('marker_start_type: ', marker_start_type)
                # st.write('s2_color: ', s2_color)
                # st.write('s_u_edge_color: ', s_u_edge_color)


            # vechicle - system edge
            # v -> s
            edges.append(t_builder.create_edge(
                    id = f'edge_{v_wp}-{s_wp}',
                    source = v_id,
                    target = s_id,
                    animated = v_s_animated,
                    edge_type = v_s_edge,
                    marker_end_type = marker_end_type,
                    edge_color = v_s_edge_color
                    )
                )
            # st.write('edge appended: ', {
            #     'id': f'edge_{v_wp}-{s_wp}',
            #     'source': v_id,
            #     'target': s_id,
            #     'animated': v_s_animated,
            #     'edge_type': v_s_edge,
            #     'marker_end_type': marker_end_type,
            #     'edge_color': v_s_edge_color
            # })

            # system - unit edge
            # s2 -> u
            edges.append(t_builder.create_edge(
                    id = f'edge_{s2_wp}-{u_wp}',
                    source = s2_id,
                    target = u_id,
                    animated = s_u_animated,
                    edge_type = s_u_edge,
                    marker_start_type = marker_start_type,
                    edge_color = s_u_edge_color
                    )
                )
            # st.write('edge appended: ', {
            #     'id': f'edge_{s2_wp}-{u_wp}',
            #     'source': s2_id,
            #     'target': u_id,
            #     'animated': s_u_animated,
            #     'edge_type': s_u_edge,
            #     'marker_start_type': marker_start_type,
            #     'edge_color': s_u_edge_color
            # })


            # vehicle node
            nodes.append(t_builder.create_node(
                id = v_id,
                data = v_wp,
                hr = 'vehicle',
                )
            )
            # st.write('node appended: ', {'id': v_id, 'data': v_wp, 'hr': 'vehicle'})

            # system node
            nodes.append(t_builder.create_node(
                id = s_id,
                data = s_wp,
                hr = 'system',
                color = s_color
                )
            )
            # st.write('node appended: ', {'id': s_id, 'data': s_wp, 'hr': 'system', 'color': s_color})


            # system node2
            nodes.append(t_builder.create_node(
                id = s2_id,
                data = s2_wp,
                hr = 'system',
                color = s2_color
                )
            )
            # st.write('node appended: ', {'id': s2_id, 'data': s2_wp, 'hr': 'system', 'color': s2_color})

            # unit node
            nodes.append(t_builder.create_node(
                id = u_id,
                data = u_wp,
                hr = 'unit'
                )
            )
            # st.write('node appended: ', {'id': u_id, 'data': u_wp, 'hr': 'unit'})


    return (nodes,edges)
