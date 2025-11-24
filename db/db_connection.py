import pandas as pd
import psycopg2
from psycopg2 import OperationalError, InterfaceError, sql
import const.constpara as co
from sqlalchemy import create_engine, text
import traceback
import streamlit as st
st.session_state.username = 'ELR00028'

class DBConnection:

    def __init__(self,autocommit=True) -> None:
        self.conn_info = co.psql
        self.autocommit = autocommit

    def __enter__(self):
        self.conn = self.create_connection()
        self.conn.autocommit = self.autocommit
        return self.conn

    def __exit__(self,exc_type,exc_val,exc_tb):
        if not self.conn:
            return
        if exc_type:
            self.conn.rollback()
            traceback.print_tb(exc_tb)
        if not self.autocommit:
            self.conn.commit()
        self.conn.close()

    def create_connection(self):
        try:
            # connection = psycopg2.connect(
            #     dbname="postgres",
            #     user="postgres",
            #     password="postgres",
            #     host="localhost",
            #     port="5432"
            # )            
            # return connection
            connection = psycopg2.connect(
                dbname="SPDM_5",
                user="postgres",
                password="SQL123456",
                host="localhost",
                port="5433"
            )
            return connection
        except OperationalError as e:
            raise RuntimeError("DB接続に失敗しました") from e