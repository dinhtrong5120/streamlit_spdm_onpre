"""
Summary:
    F-TREE
Author:
    Telema Tanaka
Created:
    2025-07-25
"""

from db.rfl_repository import RFLRepository as rflq
from module.tree.common.builder import TreeUtils as t_builder
import module.tree.effect_first.f_tree.secondary as f_s
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

    nodes,edges = f_s.create_secondary_v_u_flow(hr,primary_df,secondary_df)

    third_font_color = font_color_def['third_color']
    third_edge_color = edge_color_def['third_color']


    for row in (third_array):
            v_wp = row[0]
            s_from_v_wp = row[1]
            s_from_u_wp = row[2]
            u_wp = row[3]

            v_data = row[4]
            s_from_v_data = row[5]
            s_from_u_data = row[6]
            u_data = row[7]

            v_id = prefixes[0] + v_wp + f'_{v_data}'
            s_from_v_id =  prefixes[1] + s_from_v_wp + f'_{s_from_v_data}'
            s_from_u_id = prefixes[1] + s_from_u_wp + f'_{s_from_u_data}'
            u_id = prefixes[2] + u_wp + f'_{u_data}'

            # 基本設定
            v_s_edge = 'step'
            v_s_animated = False
            s_u_edge = 'step'
            s_u_animated = False

            # 重複箇所抽出
            edge_color = '#000000'

            # 3次接続の場合、破線にする
            # 1→2
            if s_from_v_data not in third_common_values:
                v_s_edge = 'default'
                v_s_animated = True
                edge_color = third_edge_color
                marker_end_type = 'arrowclosed'
                marker_end_color = third_edge_color
                s_from_v_color = third_font_color

                # system node
                nodes.append(t_builder.create_node(
                    id = s_from_v_id,
                    data = s_from_v_data,
                    hr = 'system',
                    color = s_from_v_color
                    )
                )

                # vechicle - system edge
                edges.append(t_builder.create_edge(
                        id = f'edge_{v_data}-{s_from_v_data}',
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
            if s_from_u_data not in third_common_values:
                s_u_edge = 'default'
                s_u_animated = True
                edge_color = third_edge_color
                marker_end_type = 'arrowclosed'
                marker_end_color = third_edge_color
                s_from_u_color = third_font_color

                # system node
                nodes.append(t_builder.create_node(
                    id = s_from_u_id,
                    data = s_from_u_data,
                    hr = 'system',
                    color = s_from_u_color
                    )
                )


                # system - unit edge
                edges.append(t_builder.create_edge(
                        id = f'edge_{u_data}-{s_from_u_data}',
                        source = u_id,
                        target = s_from_u_id,
                        animated = s_u_animated,
                        edge_type = s_u_edge,
                        edge_color = edge_color,
                        marker_end_type = marker_end_type,
                        marker_end_color = marker_end_color
                        )
                    )

    return (nodes,edges)


# ------------ 3次影響 ------------
# System
def create_third_s_flow(primary_df,secondary_df,project_code,primary_wps,secondary_wps,primary_set):
    """ALLOCATIONツリーを作成

    Args:
        df (dataframe): l_dataframe
    """

    prefixes = ['v_','s_','u_','c_']
    third_array = []
    nodes = []
    edges = []

    # Function 共通値抽出
    # primary_df_values_set = set(primary_df.values.ravel())
    secondary_df_values_set = set(secondary_df.values.ravel())

    # Third WPS 抽出
    primary_wps_set = set(primary_wps.values.ravel())
    secondary_wps_set = set(secondary_wps.values.ravel())
    secondary_wps_set = list(secondary_wps_set - primary_wps_set)
    # Third df 取得
    third_df = rflq.get_f_primary_wps('f_s',tuple(secondary_wps_set),project_code)
    third_array = third_df.values.tolist()
    third_df_values_set = set(third_df.values.ravel())

    third_common_values = list(third_df_values_set & secondary_df_values_set )
    nodes,edges = f_s.create_secondary_s_flow(primary_df,secondary_df,primary_set)

    third_font_color = font_color_def['third_color']
    third_edge_color = edge_color_def['third_color']

    for row in (third_array):

        v_wp = row[0]
        v_data = row[3]
        v_id = prefixes[0] + v_wp + f'_{v_data}'

        s_wp = row[1]
        s_data = row[4]
        s_id = prefixes[1] + s_wp + f'_{s_data}'


        u_wp = row[2]
        u_data = row[5]
        u_id = prefixes[2] + u_wp + f'_{u_data}'

        v_s_edge = 'step'
        v_s_animated = False
        s_u_edge = 'step'
        s_u_animated = False
        edge_color = "#000000"

        # 3次接続の場合、破線にする
        if v_data not in third_common_values:
            v_s_edge = 'default'
            v_s_animated = True
            edge_color = third_edge_color
            marker_end_type = 'arrowclosed'
            marker_end_color = third_edge_color
            v_color = third_font_color


            nodes.append(t_builder.create_node(
                id = v_id,
                data = v_data,
                hr = 'vehicle',
                color = v_color
            ))



            # system edge
            edges.append(t_builder.create_edge(
                    id = f'edge_{s_data}-{v_data}',
                    source = s_id,
                    target = v_id,
                    animated = v_s_animated,
                    edge_type = v_s_edge,
                    edge_color = edge_color,
                    marker_end_type = marker_end_type,
                    marker_end_color = marker_end_color
                    )
                )

        if u_data not in third_common_values:
            s_u_edge = 'default'
            s_u_animated = True
            edge_color = third_edge_color
            marker_end_type = 'arrowclosed'
            marker_end_color = third_edge_color
            u_color = third_font_color



            nodes.append(t_builder.create_node(
                id = u_id,
                data = u_data,
                hr = 'unit',
                color = u_color
            ))


            # unit edge
            edges.append(t_builder.create_edge(
                    id = f'edge_{s_data}-{u_data}',
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

