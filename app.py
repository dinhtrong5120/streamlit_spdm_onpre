import streamlit as st
from Aras_connect.Middle import IFtoARAS
import const.constpara as co
from module.PsqlModule import psql_class#山口　SQL扱うためクラス追加　11/30
sql = psql_class()#山口　SQL使うためインスタンス生成 11/30
# import streamlit_authenticator as stauth

st.set_page_config(
     page_title=co.pg_title,
     page_icon=co.n_icon,
     layout="wide",
     initial_sidebar_state = "collapsed"
     )

# カスタムCSSを追加してテキストを中央に配置

# CSSファイルの内容を読み込む
with open(co.css, encoding='utf-8') as f:
    css = f.read()

# CSSをStreamlitに適用
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

def main():
    col1, col2, col3 = st.columns([3, 3, 3])
    if 'error' not in st.session_state:
        st.session_state.error = False
        
    with col2:
        with st.container(border=True):
            st.markdown(f'<h1 class="center-text">{co.pg_title}</h1>', unsafe_allow_html=True)

            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            btn1, btn2 = st.columns([3, 5])
            with btn1:
                st.markdown('<span id="button-left"></span>', unsafe_allow_html=True)
                login_button = btn1.button("ログイン")
            # with btn2:
            #     st.markdown('<span id="button-right"></span>', unsafe_allow_html=True)
                # no_login_button = btn2.button("ログインせずに閲覧")

            if login_button:
                # if no_login_button:
                #     username = co.user
                #     password = co.user
                if username == "":
                    st.error("ユーザ名が未入力です。")
                elif password == "":
                    st.error("パスワードが未入力です。")
                elif len(username) < 7:
                    st.error("ユーザ名が間違えている可能性があります。")
                else:#山口　Arasを経由→DBに名前があれば通れるように変更 11/30
                    #aras = IFtoARAS(username, password, co.ARASURL, co.ARASDB)
                    user = sql.get_user(username)
                    st.session_state.username = username
                    st.session_state.password = password
                    if user == username and username == password: #山口　パスワード＝社員番号とした条件追加　12/16
                        st.session_state.error = False
                        if username == co.user:
                            st.session_state.button_edit_state = False
                        else:    
                            st.session_state.button_edit_state = True
                        sql.set_login_log(username)#山口　ログイン日時を記録
                        st.session_state.login_begin = True #チョー　ログインした後の初期表示
                        st.switch_page("pages/SPDM_LIST.py")
                        
                        
                    else:
                        st.session_state.error = True

            if st.session_state.error:
                st.markdown("""
                            <div style="color: red; background-color: #f8d7da; padding: 10px; border-radius: 5px;">
                                <strong>ログイン情報が間違えているかアクセス権がありません。</strong><br>
                                下記よりアクセス権限付与依頼ができます。
                            </div><br>
                            """, unsafe_allow_html=True)
                if st.button("アクセス権付与依頼"):
                    st.session_state.error = False
                    st.switch_page("pages/アクセス権付与依頼.py")       

def main1():
    username = "KNT21617"
    password = "KNT21617"
    user = sql.get_user(username)
    st.session_state.username = username
    st.session_state.password = password
    if user == username and username == password:  # 山口　パスワード＝社員番号とした条件追加　12/16
        st.session_state.error = False
        if username == co.user:
            st.session_state.button_edit_state = False
        else:
            st.session_state.button_edit_state = True
        sql.set_login_log(username)  # 山口　ログイン日時を記録
        st.session_state.login_begin = True  # チョー　ログインした後の初期表示
        st.switch_page("pages/SPDM_LIST.py")
if __name__ == "__main__":
    main1()
