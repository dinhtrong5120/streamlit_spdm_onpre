"""
Summary:
    RFLツリー作成モジュール
Author:
    Telema Tanaka
Created:
    2025-03-25
Updated:
    2025-07-15
"""

import streamlit as st
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.layouts import TreeLayout,LayeredLayout

class TreeUtils():
    """共通メソッドクラス

    Methods:
        create_node : ノードを作成
        create_edge : エッジを作成
        create_flow : フローを作成

    """
    @staticmethod
    def create_node(id,data,hr,pos=(0,0),node_type='default',source_position='bottom',target_position='top',color='white',width=None,height=None):
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
        if hr is None:
            bg_color = ''
        font_size = '15px'
        node_wsize = width if width is not None else width  # Use custom width or default
        node_hsize = height if height is not None else height  # Use custom height or default

        style = {
            'background-color':bg_color,
            'color':color,
            'width':node_wsize,
            'font-size':font_size,
            'height':node_hsize
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
    def create_edge(id,source,target,animated=False,edge_type='step',marker_end_type='None',selected=False,edge_color='#000000',marker_end_color='#000000',marker_start_type=None,marker_start_color='#000000'):
        """エッジを作成

        Args:
            id (str): エッジのID
            source (str): エッジ発生元のノードID
            target (str): エッジ到達先のノードID
            animated (bool, optional): エッジアニメーション. Defaults to False.
            edge_type (str, optional): step=カギ線. Defaults to 'step'.
            marker_end_type (str,optional): arrow,arrowcolsed,None. Defaults to None.
            edge_color (str,optional): edge_color. Defaults to #000000.
            end_color (str,optional): エッジ終端のカラー. Defaults to #000000.
            marker_start_type (str,optional): arrow,arrowclosed,None Defaults to None

        Returns:
            _type_: _description_
        """


        return StreamlitFlowEdge(
            id = id,
            source = source,
            target = target,
            animated = animated,
            edge_type = edge_type,
            selected= selected,
            marker_start={
                'type': marker_start_type,
                'color': marker_start_color
            },
            marker_end={
                'type': marker_end_type,
                'color':marker_end_color
            },
            style= {
                'strokeWidth': 1,
                'stroke': edge_color,
                },
        )

    @staticmethod
    def create_flow(flow,key):
        """フローを作成

        Args:
            flow (flow): フローオブジェクト
            key (str): ユニークなキー
        """

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
