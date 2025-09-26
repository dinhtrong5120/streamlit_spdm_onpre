import streamlit as st
from email.mime.text import MIMEText
# import mail_send
import subprocess
import const.constpara as co

#チョー　01/14
st.set_page_config(
     page_title=co.pg_title,
     page_icon=co.n_icon,
     layout="wide",
     initial_sidebar_state = "collapsed"
     )

# CSSファイルの内容を読み込む
with open(co.css, encoding='utf-8') as f:
    css = f.read()

# CSSをStreamlitに適用
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# 実行するPythonファイルのパス
file_path = co.mail_path

def main():
    if 'username' not in st.session_state or st.session_state.username == co.user:
        user = ''
    else:
        user = st.session_state.username

    user = st.text_input("社員番号",value=user)
    message = st.text_area("メッセージ", value="アクセス権付与依頼")

    col1, col2,col3 = st.columns([1,1,3])

    if col1.button("編集できるように要求"):
        if user == "":
            st.error("社員番号は必須です。")
        else:
            subprocess.call(['python', file_path, user, message])
            st.success("メールを送信しました。")

    if col2.button("ログイン画面に戻る"):
        st.session_state.error = False
        st.switch_page("app.py")
        
if __name__ == "__main__":
    main()