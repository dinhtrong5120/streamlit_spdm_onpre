"""
Summary:
    F-TREE second
Author:
    Telema Tanaka
Created:
    2025-07-23
"""

from module.tree.f_tree.primary import create_primary_s_flow as create_primary_s
from module.tree.common.builder import TreeUtils as t_builder
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
    secondary_df_values_set = set(secondary_df.values.ravel())
    secondary_common_values = list(primary_df & secondary_df_values_set)

    primary_color = font_color_def['primary_color']
    secondary_color = font_color_def['secondary_color']

    primary_edge_color = edge_color_def['primary_color']
    secondary_edge_color = edge_color_def['secondary_color']

    for row in (secondary_array):
            v_wp = row[0]
            s_wp = row[1]
            u_wp = row[2]

            v_data = row[4]
            s_data = row[5]
            u_data = row[6]


            v_id = prefixes[0] + v_wp + f'_{v_data}'
            s_id = prefixes[1] + s_wp + f'_{s_data}'
            u_id = prefixes[2] + u_wp + f'_{u_data}'

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
                v_data = row[7]
                v_wp = row[3]
                v_id = prefixes[0] + v_wp + f'_{v_data}'
                s_u_edge = 'default'
                s_u_animated = True
                s_u_animated = True
                s_u_marker_end_type = 'arrowclosed'
                u_color = secondary_color
                s_u_edge_color = secondary_edge_color

                if v_data not in secondary_common_values:
                    v_s_edge = 'default'
                    v_s_animated = True
                    v_s_marker_start_type = 'arrowclosed'
                    v_color = secondary_color
                    v_s_edge_color = secondary_edge_color

            if hierarchy == 'ユニット':
                u_data = row[7]
                u_wp = row[3]
                u_id = prefixes[2] + u_wp + f'_{u_data}'
                v_s_edge = 'default'
                v_s_animated = True
                v_s_marker_start_type = 'arrowclosed'
                v_color = secondary_color
                v_s_edge_color = secondary_edge_color

                if u_data not in secondary_common_values:
                    s_u_edge = 'default'
                    s_u_animated = True
                    s_u_marker_end_type = 'arrowclosed'
                    u_color = secondary_color
                    s_u_edge_color = secondary_edge_color

            # vehicle node
            nodes.append(t_builder.create_node(
                id = v_id,
                data = v_data,
                hr = 'vehicle',
                color = v_color
                )
            )

            # system node
            nodes.append(t_builder.create_node(
                id = s_id,
                data = s_data,
                hr = 'system'
                )
            )

            # secondary_node
            nodes.append(t_builder.create_node(
                id = u_id,
                data = u_data,
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

    return (nodes,edges)

# ------------ 2次影響 ------------
# System
def create_secondary_s_flow(primary_df,secondary_df,primary_set):
    """ALLOCATIONツリーを作成

    Args:
        df (dataframe): l_dataframe
    """

    prefixes = ['v_','s_','u_','c_']
    nodes = []
    edges = []

    secondary_array = secondary_df.values.tolist()

    # 共通値抽出
    secondary_df_values_set = set(secondary_df.values.ravel())
    common_values = list(primary_set & secondary_df_values_set)
    nodes,edges,_ = create_primary_s(primary_df)

    primary_color = font_color_def['primary_color']
    secondary_color = font_color_def['secondary_color']

    primary_edge_color = edge_color_def['primary_color']
    secondary_edge_color = edge_color_def['secondary_color']

    for row in (secondary_array):

            v_wp = row[0]
            s_wp = row[1]
            s2_wp = row[2]
            u_wp = row[3]

            v_data = row[4]
            s_data = row[5]
            s2_data = row[6]
            u_data = row[7]

            v_id = prefixes[0] + v_wp + f'_{v_data}'
            s_id = prefixes[1] + s_wp + f'_{s_data}'
            s2_id = prefixes[1] + s2_wp + f'_{s2_data}'
            u_id = prefixes[2] + u_wp + f'_{u_data}'

            s_color = primary_color
            s2_color = primary_color


            # 基本設定
            v_s_edge = 'step'
            v_s_animated = False
            s_u_edge = 'step'
            s_u_animated = False
            marker_start_type = None
            marker_end_type = None

            v_s_edge_color = primary_edge_color
            s_u_edge_color = primary_edge_color

            # 2次接続の場合、破線にする
            if s_data not in common_values:
                v_s_edge = 'default'
                v_s_animated = True
                marker_end_type = 'arrowclosed'
                s_color = secondary_color
                v_s_edge_color = secondary_edge_color

            if s2_data not in common_values:
                s_u_edge = 'default'
                s_u_animated = True
                marker_start_type = 'arrowclosed'
                s2_color = secondary_color
                s_u_edge_color = secondary_edge_color

            # vechicle - system edge
            edges.append(t_builder.create_edge(
                    id = f'edge_{v_data}-{s_data}',
                    source = v_id,
                    target = s_id,
                    animated = v_s_animated,
                    edge_type = v_s_edge,
                    marker_end_type = marker_end_type,
                    edge_color = v_s_edge_color
                    )
                )

            # system - unit edge
            edges.append(t_builder.create_edge(
                    id = f'edge_{s2_data}-{u_data}',
                    source = s2_id,
                    target = u_id,
                    animated = s_u_animated,
                    edge_type = s_u_edge,
                    marker_start_type = marker_start_type,
                    edge_color = s_u_edge_color
                    )
                )

            # vehicle node
            nodes.append(t_builder.create_node(
                id = v_id,
                data = v_data,
                hr = 'vehicle'
                )
            )

            # system node
            nodes.append(t_builder.create_node(
                id = s_id,
                data = s_data,
                hr = 'system',
                color = s_color
                )
            )


            # system node2
            nodes.append(t_builder.create_node(
                id = s2_id,
                data = s2_data,
                hr = 'system',
                color = s2_color
                )
            )

            # unit node
            nodes.append(t_builder.create_node(
                id = u_id,
                data = u_data,
                hr = 'unit'
                )
            )
    return (nodes,edges)
