"""
Summary:
    Fツリー作成モジュール
Author:
    Telema Tanaka
Created:
    2025-07-22

"""
from module.tree.common.builder import TreeUtils as t_builder

# ------------ 1次影響 ------------
# Vehicle,Unit
def create_primary_v_u_flow(hierarchy,df):
    prefixes = ['v_','s_','u_','c_']
    array = []
    nodes = []
    edges = []
    primary_array = set()
    animated = False
    array = df.values.tolist()

    for row in array:

        s_data = row[4]
        s_wp = row[1]
        s_id = prefixes[1] + s_wp + f'_{s_data}'

        if hierarchy == '車両':
            wp = row[0]
            data = row[3]
            id = prefixes[0] + wp + f'_{data}'
            hr = 'vehicle'
            source_id = id
            target_id = s_id

        if hierarchy == 'ユニット':
            wp = row[2]
            data = row[5]
            id = prefixes[2] + wp + f'_{data}'
            hr = 'unit'
            source_id = s_id
            target_id = id

        # vehicle node
        nodes.append(t_builder.create_node(
            id = id,
            data = data,
            hr = hr
            )
        )

        # system node
        nodes.append(t_builder.create_node(
            id = s_id,
            data = s_data,
            hr = 'system'
            )
        )


        # system edge
        edges.append(t_builder.create_edge(
                id = f'edge_{data}-{s_data}',
                source = source_id,
                target = target_id
                )
            )

        primary_array.update([data,s_data])
    return (nodes,edges,primary_array)

# ------------ 1次影響 ------------
#  System
def create_primary_s_flow(wps):

    prefixes = ['v_','s_','u_','c_']
    array = []
    nodes = []
    edges = []

    array = wps.values.tolist()
    primary_array = set()

    for row in (array):
        v_wp = row[0]
        v_data = row[3]
        v_id = prefixes[0] + v_wp + f'_{v_data}'

        s_wp = row[1]
        s_data = row[4]
        s_id = prefixes[1] + s_wp + f'_{s_data}'


        u_wp = row[2]
        u_data = row[5]
        u_id = prefixes[2] + u_wp + f'_{u_data}'


        nodes.append(t_builder.create_node(
            id = v_id,
            data = v_data,
            hr = 'vehicle'
        ))


        # system node
        nodes.append(t_builder.create_node(
            id = s_id,
            data = s_data,
            hr = 'system'
        ))


        nodes.append(t_builder.create_node(
            id = u_id,
            data = u_data,
            hr = 'unit'
        ))


        # system edge
        edges.append(t_builder.create_edge(
                id=f'edge_{v_data}-{s_data}',
                source=v_id,
                target=s_id,
                )
        )

        # unit edge
        edges.append(t_builder.create_edge(
                id=f'edge_{s_data}-{u_data}',
                source=s_id,
                target=u_id,
                )
        )
        primary_array.update([v_data,s_data,u_data])
    return (nodes,edges,primary_array)