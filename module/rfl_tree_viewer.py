"""
Summary:
    RFLツリー作成モジュール
Author:
    Telema Tanaka
Created:
    2025-03-25
"""

import streamlit as st
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState
from streamlit_flow.layouts import TreeLayout,LayeredLayout, RadialLayout,Layout
from uuid import uuid4
from module.utils import init_session_state
from db.rfl_repository import RFLRepository as rflq

class TreeUtils():
    """共通メソッドクラス

    Methods:
        create_node : ノードを作成
        create_edge : エッジを作成
        create_flow : フローを作成

    """
    @staticmethod
    def create_node(id,pos,data,hr,node_type='default',source_position='bottom',target_position='top'):
        """ノードを作成

        Args:
            id (str): ノードのID
            pos (int): ノードの位置
            data (str): ノードの表示名称
            hr (str, optional): 階層
            node_type (str, optional): default. Defaults to 'default'.
            source_position (str, optional): エッジの発生位置. Defaults to 'bottom'.
            target_position (str, optional): エッジの到達位置. Defaults to 'top'.

        Returns:
            _type_: node
        """
        # ディレクションによってエッジの方向を変更
        if st.session_state.tree_direction == 'down':
            source_position = 'bottom'
            target_position = 'top'

        if st.session_state.tree_direction == 'up':
            source_position = 'top'
            target_position = 'bottom'

        if st.session_state.tree_direction == 'right':
            source_position = 'right'
            target_position = 'left'

        if st.session_state.tree_direction == 'left':
            source_position = 'left'
            target_position = 'right'


        if hr == 'vehicle':
            bg_color = '#002060'
        if hr == 'system':
            bg_color = '#Ed7D31'
        if hr == 'unit':
            bg_color = '#00B0F0'
        if hr == 'comp':
            bg_color = '#d62728'
        color = 'white'
        node_wsize = '180px'
        node_hsize = '80px'

        style = {
            'background-color':bg_color,
            'color':color,
            'width':node_wsize,
            # 'height':node_hsize
        }

        return StreamlitFlowNode(
            id = id,
            pos = pos,
            data = {'content':data},
            node_type = node_type,
            source_position = source_position,
            target_position = target_position,
            style = style
        )

    @staticmethod
    def create_edge(id,source,target,animated=False,edge_type='step'):
        """エッジを作成

        Args:
            id (str): エッジのID
            source (str): エッジ発生元のノードID
            target (str): エッジ到達先のノードID
            animated (bool, optional): エッジアニメーション. Defaults to False.
            edge_type (str, optional): step=カギ線. Defaults to 'step'.

        Returns:
            _type_: _description_
        """
        return StreamlitFlowEdge(
            id = id,
            source = source,
            target = target,
            animated = animated,
            edge_type = edge_type,
            selected= False
        )

    @staticmethod
    def create_flow(flow,key):
        """フローを作成

        Args:
            flow (flow): フローオブジェクト
            key (str): ユニークなキー
        """

        # class CustomELKLayout(Layout):
        #     def __to_dict__(self) -> dict[str, any]:
        #         return {
        #         "elkOptions": {
        #             "org.eclipse.elk.algorithm": "layered",
                    # "elk.layering": "LONGEST_PATH",
                    # "elk.spacing": {"nodeNode": 150, "edgeEdge": 100}
                # }
            # }
        # layout = CustomELKLayout()

        if st.session_state.tree_direction == 'right':
            direction='right'
            layout = LayeredLayout(direction=direction)

        if st.session_state.tree_direction == 'left':
            direction='left'
            layout = LayeredLayout(direction=direction)

        if st.session_state.tree_direction == 'down':
            direction='down'
            layout = TreeLayout(direction=direction)

        if st.session_state.tree_direction == 'up':
            direction='up'
            layout = TreeLayout(direction=direction)

        st.session_state.curr_state = streamlit_flow(
            key,
            flow,
            layout = layout,
            fit_view=True,
            height=500,
            enable_node_menu=True,
            enable_edge_menu=True,
            enable_pane_menu=True,
            get_edge_on_click=True,
            get_node_on_click=True,
            show_minimap=False,
            hide_watermark=True,
            allow_new_edges=True,
            min_zoom=0.1
        )

def create_hierarchy_flow(top_hierarchy,wps,x_offset=150,y_offset=150):
    """Logic-Requirementの連関ツリーを作成

    Args:
        top_hierarchy (str): 車両階層WP
        wps (dataframe): 連関wps
        x_offset (int, optional): Node間のx_offset. Defaults to 150.
        y_offset (int, optional): Node間のy_offset. Defaults to 150.
    """
    prefixes = ['v_','s_','u_','c_']
    array = []
    nodes = []
    edges = []

    org_top = st.session_state.wp[0]
    wps = wps.drop(wps.columns[0],axis=1)
    top_hierarchy_id = prefixes[0] + top_hierarchy

    st.session_state.tree_top_hierarchy = top_hierarchy

    # Vechile
    nodes.append(TreeUtils.create_node(
        id = top_hierarchy_id,
        pos = (0,0),
        data = top_hierarchy,
        hr = 'vehicle'
        )
    )

    for row in wps.values:
        array.append(row)

    for i,item in enumerate(array):
        system_hr = item[0]
        unit_hr = item[1]
        system_hr_id = prefixes[1] + item[0]
        unit_hr_id = prefixes[2] + item[1]

        sys_pos = (i*x_offset,y_offset)
        unit_pos = (i*x_offset,y_offset)

        # system node
        nodes.append(TreeUtils.create_node(
            id = system_hr_id,
            pos = sys_pos,
            data = system_hr,
            hr = 'system'
            )
        )

        # unit node
        nodes.append(TreeUtils.create_node(
            id = unit_hr_id,
            pos = unit_pos,
            data = unit_hr,
            hr = 'unit',
            )
        )

        animated = False
        if st.session_state.detail_flag:
            if system_hr == org_top or unit_hr == org_top:
                animated = False
            else:
                animated = True

        # system edge
        edges.append(TreeUtils.create_edge(
                id=f'edge_{top_hierarchy}-{system_hr}',
                source=top_hierarchy_id,
                target=system_hr_id,
                animated=animated
                )
            )

        # unit edge
        edges.append(TreeUtils.create_edge(
                id=f'edge_{system_hr}-{unit_hr}',
                source=system_hr_id,
                target=unit_hr_id,
                animated=animated
                )
            )

    st.session_state.curr_state = StreamlitFlowState(nodes, edges)


def create_function_flow(functions,x_offset=150,y_offset=150):
    """Function-Functionの連関ツリーを作成

    Args:selec
        functions (dataframe): 連関Functions
        x_offset (int, optional): Node間のx_offset. Defaults to 150.
        y_offset (int, optional): Node間のy_offset. Defaults to 150.
    """
    prefixes = ['v_','s_','u_','c_']
    array = []
    nodes = []
    edges = []
    org_top = st.session_state.wp[0]

    columns = functions.columns.tolist()
    for index, row in functions.iterrows():
        array.append(row[columns].tolist())

    for i,row in enumerate(array):
            v_id = prefixes[0] + row[0] + f'_{row[3]}'
            s_id = prefixes[1] + row[1] + f'_{row[4]}'
            u_id = prefixes[2] + row[2] + f'_{row[5]}'
            pos = (x_offset,i*y_offset)

            # vehicle node
            nodes.append(TreeUtils.create_node(
                id = v_id,
                pos = pos,
                data = row[3],
                hr = 'vehicle'
                )
            )

            # system node
            nodes.append(TreeUtils.create_node(
                id = s_id,
                pos = pos,
                data = row[4],
                hr = 'system'
                )
            )

            # unit node
            nodes.append(TreeUtils.create_node(
                id = u_id,
                pos = pos,
                data = row[5],
                hr = 'unit'
                )
            )

            # 点線の場合、edge_typeを変更(暫定)
            animated = False
            edge_type = 'step'
            if st.session_state.f_detail_flag:
                if row[1] == org_top or row[2] == org_top:
                    animated = False
                else:
                    animated = True
                    edge_type = 'default'

            # system edge
            edges.append(TreeUtils.create_edge(
                    id = f'edge_{row[3]}-{row[4]}',
                    source = v_id,
                    target = s_id,
                    animated = animated,
                    edge_type = edge_type
                    )
                )

            # unit edge
            edges.append(TreeUtils.create_edge(
                    id = f'edge_{row[4]}-{row[5]}',
                    source = s_id,
                    target = u_id,
                    animated = animated,
                    edge_type = edge_type
                    )
                )

    st.session_state.curr_state = StreamlitFlowState(nodes, edges)


def create_allocation_flow(vwp,x_offset=150,y_offset=150):
    """ALLOCATIONツリーを作成

    Args:
        vwp (dataframe): 車両階層領域一覧 / 選択した車両階層領域
        x_offset (int, optional): Node間のxoffset Defaults to 150.
        y_offset (int, optional): Node間のyoffset. Defaults to 150.
    """

    def _get_wp_paths(parent_id=None, current_path=None):
        """ツリー経路を配列に格納
        Args:
            parent_id (_type_, optional): _description_. Defaults to None.
            current_path (_type_, optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        """
        df = rflq.get_wp_tree(parent_id)
        if df.empty:
            return [current_path]
        paths = []
        for _, row in df.iterrows():
            # wpを結合
            new_path = current_path + [row['wp']]
            child_paths = _get_wp_paths(row['id'], new_path)
            paths.extend(child_paths)
        return paths


    def get_wp_paths(top_node=None):
        """ツリー経路を配列に格納

        Args:
            parent_id (int): parent_id
            current_path (str): 再帰内にて重ねるパス

        Returns:
            _type_: _description_
        """

        array = []
        if top_node is not None:
            for _,top_row in top_node.iterrows():
                if top_node.empty:
                    return []

                current_path = [top_row['wp']]
                id = int(top_row['id'])
                result = (_get_wp_paths(id,current_path))
                array.append([result])
            return array
        else:
            df = rflq.get_all_vwp()
            paths = []

            for _, row in df.iterrows():
                current_path = [row['wp']]
                child_paths = _get_wp_paths(row['id'],current_path)
                paths.extend(child_paths)
            return paths

    def flatten(nested_list):
        """多次元を2次元に調整

        Args:
            nested_list (list): 多次元配列

        Returns:
            _type_: list
        """
        result = []
        for element in nested_list:
            if isinstance(element, list):
                if any(isinstance(sub_element, list) for sub_element in element):
                    result.extend(flatten(element))
                else:
                    result.append(element)
            else:
                result.append([element])
        return result


    def create_flow_data(tree_list):
        """Allocationのツリーを作成

        Args:
            tree_list (list): Treeデータを格納した2次元配列
        """
        prefixes = ['v_','s_','u_','c_']
        nodes = []
        edges = []
        for i,row in enumerate(tree_list):

            # DBのdataが揃っていないときの対策
            until_v_flag = False
            until_s_flag = False
            until_c_flag = False

            if len(row) < 2:
                until_v_flag = True
            if len(row) < 3:
                until_s_flag = True
            if len(row) > 3:
                until_c_flag = True

            if until_v_flag is False:
                s_id = prefixes[1] +  f'_{row[1]}'
            if until_s_flag is False:
                u_id = prefixes[2] +  f'_{row[2]}'
            if until_c_flag:
                c_id = prefixes[3] +  f'_{row[3]}'

            v_id = prefixes[0] + row[0]
            pos = x_offset,y_offset*i
            # vehicle node
            nodes.append(TreeUtils.create_node(
                id = v_id,
                pos = pos,
                data = row[0],
                hr = 'vehicle'
                )
            )

            if until_v_flag is False:
                # system node
                nodes.append(TreeUtils.create_node(
                    id = s_id,
                    pos = pos,
                    data = row[1],
                    hr = 'system'
                    )
                )

                # system edge
                edges.append(TreeUtils.create_edge(
                    id = f'edge_{v_id}-{s_id}',
                    source = v_id,
                    target = s_id,

                    )
                )

            if until_s_flag is False:
                # unit node
                nodes.append(TreeUtils.create_node(
                    id = u_id,
                    pos = pos,
                    data = row[2],
                    hr = 'unit'
                    )
                )

                # unit edge
                edges.append(TreeUtils.create_edge(
                    id = f'edge_{s_id}-{u_id}',
                    source = s_id,
                    target = u_id,

                    )
                )

            if until_c_flag:
            # comp node
                nodes.append(TreeUtils.create_node(
                    id = c_id,
                    pos = pos,
                    data = row[3],
                    hr = 'comp'
                    )
                )
                edges.append(TreeUtils.create_edge(
                    id = f'edge_{u_id}-{c_id}',
                    source = u_id,
                    target = c_id,
                    )
                )
        st.session_state.curr_state = StreamlitFlowState(nodes, edges)

    if st.session_state.l_change_flag and st.session_state.selected_wp != []:
        selected_vwp = tuple(vwp)
        df = rflq.get_selected_allocation(selected_vwp)
        tree_list =[]
        tree_list = get_wp_paths(df)

        # selectorで複数選んだ時の分岐
        multi_flag = True if len(tree_list)>1 else False
        if multi_flag:
            # 3重のリストになっている為調整
            create_flow_data(flatten(tree_list))
        else:
            # 3重のリストになっている為調整
            create_flow_data(tree_list[0][0])
    else:
        tree_list = get_wp_paths()
        create_flow_data(tree_list)
