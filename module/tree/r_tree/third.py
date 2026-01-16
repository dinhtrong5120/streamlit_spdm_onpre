"""
Summary:
    R-TREE third
Author:
    Telema Tanaka
Created:
    2025-07-18
"""

from _plotly_utils.exceptions import PlotlyDictValueError
from db.rfl_repository import RFLRepository as rflq
from module.tree.common.builder import TreeUtils as t_builder
from module.tree.r_tree.secondary import create_secondary_v_u_flow as create_secondary_v_u,create_secondary_s_flow as create_secondary_s
import streamlit as st
from config.config import effect_font_color_defs as font_color_def
from config.config import effect_edge_color_defs as edge_color_def

# ------------ 3次影響 ------------
# Vehicle,Unit
def create_third_v_u_flow(hr,primary_df,secondary_df,third_df):
    """ALLOCATIONツリーを作成

    Args:
        df (dataframe): l_dataframe
    """

    prefixes = ['v_','s_','u_','c_']
    third_array = []
    nodes = []
    edges = []

    third_array = third_df.values.tolist()

    # 共通値抽出
    secondary_df_values_set = set(secondary_df.values.ravel())
    df_values_set = set(third_df.values.ravel())
    third_common_values = list(df_values_set & secondary_df_values_set)
    nodes,edges = create_secondary_v_u(hr,primary_df,secondary_df)

    third_font_color = font_color_def['third_color']
    third_edge_color = edge_color_def['third_color']

    for row in (third_array):
            v_wp = row[0]
            v_id = prefixes[0] + v_wp

            s_wp_from_v = row[1]
            s_from_v_id = prefixes[1] + s_wp_from_v

            s_wp_from_u = row[2]
            s_from_u_id = prefixes[1] + s_wp_from_u

            u_wp = row[3]
            u_id = prefixes[2] + u_wp


            # 基本設定
            v_s_edge = 'step'
            v_s_animated = False
            s_u_edge = 'step'
            s_u_animated = False


            if s_wp_from_v not in third_common_values:
                v_s_edge = 'default'
                v_s_animated = True
                edge_color = third_edge_color
                marker_end_type = 'arrowclosed'
                marker_end_color =  third_edge_color


                # system node
                nodes.append(t_builder.create_node(
                    id = s_from_v_id,
                    data = s_wp_from_v,
                    hr = 'system',
                    color = third_font_color
                    )
                )

                # vechicle - system edge
                edges.append(t_builder.create_edge(
                        id = f'edge_{v_wp}-{s_wp_from_v}',
                        source = v_id,
                        target = s_from_v_id,
                        animated = v_s_animated,
                        edge_type = v_s_edge,
                        edge_color = edge_color,
                        marker_end_type = marker_end_type,
                        marker_end_color = marker_end_color,
                        )
                    )
            # system - unit
            if s_wp_from_u not in third_common_values:
                s_u_edge = 'default'
                s_u_animated = True
                edge_color = third_edge_color
                marker_start_type = 'arrowclosed'
                marker_start_color = third_edge_color


                # system node
                nodes.append(t_builder.create_node(
                    id = s_from_u_id,
                    data = s_wp_from_u,
                    hr = 'system',
                    color = third_font_color
                    )
                )


                # system - unit edge
                edges.append(t_builder.create_edge(
                        id = f'edge_{s_wp_from_u}-{u_wp}',
                        source = s_from_u_id,
                        target = u_id,
                        animated = s_u_animated,
                        edge_type = s_u_edge,
                        edge_color = edge_color,
                        marker_start_type = marker_start_type,
                        marker_start_color = marker_start_color
                        )
                    )
    return (nodes,edges)


# ------------ 3次影響 ------------
# System
def create_third_s_flow(primary_df,secondary_df,project_code):
    """ALLOCATIONツリーを作成

    Args:
        df (dataframe): l_dataframe
    """

    prefixes = ['v_','s_','u_','c_']
    third_array = []
    nodes = []
    edges = []

    # 共通値抽出
    primary_df_values_set = set(primary_df.values.ravel())
    secondary_df_values_set = set(secondary_df.values.ravel())
    print('primary_df_values_set in create_third_s_flow: ',primary_df_values_set)
    print('secondary_df_values_set in create_third_s_flow: ',secondary_df_values_set)
    
    # system_node 抽出
    secondary_wps = list(secondary_df_values_set - primary_df_values_set)
    print('secondary_wps in create_third_s_flow: ',secondary_wps)
    third_df = rflq.get_r_primary_wps('システム',tuple(secondary_wps),project_code)
    third_array = third_df.values.tolist()
    third_df_values_set = set(third_df.values.ravel())
    third_common_values = list(third_df_values_set & secondary_df_values_set )
    nodes,edges = create_secondary_s(primary_df,secondary_df)

    primary_color = font_color_def['primary_color']
    third_color = font_color_def['third_color']

    normal_edge_color = edge_color_def['primary_color']
    third_edge_color = edge_color_def['third_color']

    for row in (third_array):

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
            edge_color = normal_edge_color
            v_color = primary_color
            u_color = primary_color


            # 3次接続の場合、破線にする
            if v_wp not in third_common_values:
                v_s_edge = 'default'
                v_s_animated = True
                edge_color = third_edge_color
                marker_start_type = 'arrowclosed'
                marker_start_color = third_edge_color
                v_color = third_color


                # vehicle node
                nodes.append(t_builder.create_node(
                    id = v_id,
                    data = v_wp,
                    hr = 'vehicle',
                    color = v_color
                    )
                )

                # system edge
                edges.append(t_builder.create_edge(
                        id = f'edge_{v_wp}-{s_wp}',
                        source = v_id,
                        target = s_id,
                        animated = v_s_animated,
                        edge_type = v_s_edge,
                        edge_color = edge_color,
                        marker_start_type = marker_start_type,
                        marker_start_color = marker_start_color
                        )
                    )

            if u_wp not in third_common_values:
                s_u_edge = 'default'
                s_u_animated = True
                edge_color = third_edge_color
                marker_end_type = 'arrowclosed'
                marker_end_color =  third_edge_color
                u_color = third_color


                # unit node
                nodes.append(t_builder.create_node(
                    id = u_id,
                    data = u_wp,
                    hr = 'unit',
                    color = u_color
                    )
                )


               # unit edge
                edges.append(t_builder.create_edge(
                        id = f'edge_{s_wp}-{u_wp}',
                        source = s_id,
                        target = u_id,
                        animated = s_u_animated,
                        edge_type = s_u_edge,
                        edge_color = edge_color,
                        marker_end_type = marker_end_type,
                        marker_end_color = marker_end_color
                        )
                    )

    return (nodes,edges)

