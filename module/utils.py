"""
Summary: 
        共通関数
Functions:
    init_session_state: セッション初期化
Author:
    Telema Tanaka
Created:
    2025-02-07
"""

import streamlit as st
import re

def init_session_state(key):
    """initialize session key
    Args:
        key (string): session_key
    """
    if key not in st.session_state:
        st.session_state[key] = []

def get_matching_key(pattern):
    result = []
    match_key = [key for key in st.session_state.keys() if re.match(pattern,key)]
    for key in match_key:
        result.append(key)
    return result
