# utils/url_params.py
import streamlit as st

def get_qp():
    # Streamlit mới có st.query_params; cũ dùng experimental_*
    try:
        return st.query_params  # dict-like
    except Exception:
        return st.experimental_get_query_params()

def set_qp(**kwargs):
    try:
        st.query_params.clear()
        for k, v in kwargs.items():
            st.query_params[k] = v
    except Exception:
        st.experimental_set_query_params(**kwargs)