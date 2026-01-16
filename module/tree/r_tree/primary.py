"""
Summary:
    R-Tree
Author:
    Telema Tanaka
Created:
    2025-07-18
"""
from module.tree.common.builder import TreeUtils as t_builder

# ------------ 1次影響 ------------
# Vehicle,Unit
def create_primary_v_u_flow(hierarchy,df):
    prefixes = ['v_','s_','u_','c_']
    array = []
    nodes = []
    edges = []
    animated = False

    array = df.values.tolist()

    if hierarchy == '車両':

        wp = array[0][0]
        id = prefixes[0] + wp
        hr = 'vehicle'

    if hierarchy == 'ユニット':

        wp = array[0][2]
        id = prefixes[2] + wp
        hr = 'unit'

    # criterion node
    nodes.append(t_builder.create_node(
        id = id,
        data = wp,
        hr = hr
    ))

    for row in (array):
        s_wp = row[1]
        s_id = prefixes[1] + s_wp

        nodes.append(t_builder.create_node(
            id = s_id,
            data = s_wp,
            hr = 'system'
        ))

        if hierarchy == '車両':
            source_id = id
            target_id  = s_id

        if hierarchy == 'ユニット':
            source_id = s_id
            target_id  = id


        edges.append(t_builder.create_edge(
                id=f'edge_{wp}-{s_wp}',
                source=source_id,
                target=target_id,
                animated=animated
        )

        )

    return (nodes,edges)

# ------------ 1次影響 ------------
#  System
def create_primary_s_flow(wps):

    prefixes = ['v_','s_','u_','c_']
    array = []
    nodes = []
    edges = []
    animated = False

    array = wps.values.tolist()

    for row in (array):
        v_wp = row[0]
        v_id = prefixes[0] + v_wp
        s_wp = row[1]
        s_id = prefixes[1] + s_wp
        u_wp = row[2]
        u_id = prefixes[2] + u_wp

        nodes.append(t_builder.create_node(
            id = v_id,
            data = v_wp,
            hr = 'vehicle'
        ))

        # system node
        nodes.append(t_builder.create_node(
            id = s_id,
            data = s_wp,
            hr = 'system'
        ))


        nodes.append(t_builder.create_node(
            id = u_id,
            data = u_wp,
            hr = 'unit'
        ))

        # system edge
        edges.append(t_builder.create_edge(
                id=f'edge_{v_wp}-{s_wp}',
                source=v_id,
                target=s_id,
                animated=animated
                )
        )

        # unit edge
        edges.append(t_builder.create_edge(
                id=f'edge_{s_wp}-{u_wp}',
                source=s_id,
                target=u_id,
                animated=animated
                )
        )

    return (nodes,edges)