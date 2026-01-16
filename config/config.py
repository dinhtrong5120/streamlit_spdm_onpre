"""
Summary: 
        設定情報
Functions:
    init_session_state: セッション初期化
Author:
    Telema Tanaka
Created:
    2025-02-12
"""

import streamlit as st

class RFLGridConfig:
    # RFL_requirement_view_cols
    cols = {
        'r_cols' : {
            'wp': {
                'title': 'WP',
                'col': 'r_wp'
            },            
            # 'wp_id': {
            #     'title': 'WP_ID',
            #     'col': 'r_wp_id'
            # }, 
            'pj': {
                'title': 'PJ_ID',
                'col': 'r_pj_id'
            },
            'item': {
                'title': '要求項目',
                'col': 'r_item'
            },
            'value': {
                'title': '要求値',
                'col': 'req'
            },
            'unit': {
                'title': '単位',
                'col': 'r_unit'
            },
            'scene': {
                'title': '環境・運転条件',
                'col': 'r_scene'
            },
            'req_condition' :{
                'title' : '等号・不等号',
                'col' : 'req_condition'
            },  
        },
        # RFL_function_view_cols    
        'f_cols' : {
            'item': {
                'title': '機能',
                'col': 'f_item'
            },
            'value': {
                'title': '機能目標',
                'col': 'func'
            },
            'unit': {
                'title': '単位',
                'col': 'f_unit'
            },            
        },
        # RFL_function_view_cols    
        'l_cols' : {
            'item' :{
                'title' : '要求',
                'col' : 'l_item'
            },
            'value' :{
                'title' : '要求値',
                'col' : 'logic'
            },
            'unit' :{
                'title' : '単位',
                'col' : 'l_unit'
            },
            'scene' :{
                'title' : '環境・運転条件',
                'col' : 'l_scene'
            },
            'note' :{
                'title' : 'Note',
                'col' : 'note'
            },
            'allocation' :{
                'title' : 'Allocation',
                'col' : 'l_wp'
            }, 
            'log_condition' :{
                'title' : '等号・不等号',
                'col' : 'log_condition'
            },             
        },
        #RFL承認のため　＃チョー　04/14
        'approve_cols' : {
            'sender_selected':{
                'title':'',
                'col':'sender_selected',
            },
            'sender_judge':{
                'title':'承認',
                'col':'sender_judge',
            },
            'sender_name':{
                'title':'承認者',
                'col':'sender_name',
            },
            'sender_date':{
                'title':'日付',
                'col':'sender_date',
            },
            'sender_comment':{
                'title':'コメント',
                'col':'sender_comment',
            },
            'receiver_selected':{
                'title':'',
                'col':'receiver_selected',
            },
            'receiver_judge':{
                'title':'承認',
                'col':'receiver_judge',
            },
            'receiver_name':{
                'title':'承認者',
                'col':'receiver_name',
            },
            'receiver_date':{
                'title':'日付',
                'col':'receiver_date',
            },
            'receiver_comment':{
                'title':'コメント',
                'col':'receiver_comment',
            },
        },
        # RFL_container_title_view_cols
        'containers' : {
            'pj': {
                'title': 'PJ',
                'col': 'project_code'
            },
            'wp' : {
                'title': '性能',
                'col':  'r_wp'
            },
            'lot' : {
                'title': 'lot',
                'col':  'lot'
            },
            # 'check' :{
            #     'title' : '',
            #     'col' : 'checkBox'
            # } 
        }
    }
    
    prefixes = ['c_','s_','u_']
    
    
    
    @classmethod
    def get_value(cls):
        results = []
        for i in range(len(cls.prefixes)):
        
            target_key = 'col'
            
            # 関数内関数
            def get_nest_value(values,result=None):
                if result is None:
                    result = []
                    
                for key,value in values.items():
                    
                    if key == target_key:
                        
                        if value in ('project_code','r_wp','lot','checkBox'):
                            result.append(value)    
                        else:
                            result.append(cls.prefixes[i] + value)
                            
                    elif isinstance(value,dict):
                        get_nest_value(value,result)
                        
                return result
            
            
            result = get_nest_value(cls.cols)
            results.append(result)
        return results
    
#telema-kyaw rfl tree update 922
effect_font_color_defs = {
    'primary_color': '#FFFFFF',
    'secondary_color': '#12FF03',
    'third_color': "#d30808"
}

effect_edge_color_defs = {
    'primary_color': '#000000',
    'secondary_color': "#000000",
    'third_color': "#d30808"
}