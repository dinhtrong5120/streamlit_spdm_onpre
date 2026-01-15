import pandas
import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import os
import re
import subprocess

# 本日日付を取得
now = datetime.datetime.now().date() #- relativedelta(days=1)
# ファイルパスを指定 FileName:UIから出力されたCSV tempName:CSVを行列きれいにしてエクセルに転記したもの vbsName:IDAJマクロを動かすためのスクリプトを指定
FileName = r'C:\Python Project\Streamlit\SE List\FY24_kei\output\kei_update_' + now.strftime('%Y%m%d') + '.csv'
tempName = r'C:\Python Project\Streamlit\SE List\FY24_kei\temp\temp_file.xlsx'
vbsName = r'C:\Python Project\Streamlit\SE List\FY24_kei\arasUpdata.vbs'
# FileName = r'C:\Python Project\Streamlit\SE List\FY24_kei\output\kei_update_' + now - relativedelta(days=1) + '.csv'

if os.path.isfile(FileName): #すでにファイルが作成されている場合
    # UIから出力されたCSVを読み込む
    df_out = pd.read_csv(FileName)
    #arasパラメータIDの列を取得
    id_key = [col for col in df_out.columns if 'z_paravalueid' in col]
    # 古いパラメータ情報はdatatimeの列とパラメータ列で重複削除
    df_out = df_out.sort_values('now_time', ascending=False).drop_duplicates(subset=id_key[0])
    prev_cols = None
    pre_df = pd.DataFrame()
    new_df = pd.DataFrame()
    # CSVから取得したものは＃１～４まで一つの行になっているが、更新するとき都合が悪いので＃ごとに縦に結合（concat）
    # 列名から数字を取得(findallプロパティ)から列が変わるまで横に結合し数字が変わったタイミングで縦結合している列名も区切り文字で分割してリネームしている
    for col_name, data in df_out.iteritems():
        match = re.findall(r'\d+', col_name)
        if match and prev_cols is not None and match != prev_cols or col_name == 'INDEX':
            pre_df['username'] = df_out['username']
            pre_df['password'] = df_out['password']
            new_df = pd.concat([new_df, pd.DataFrame(pre_df)])
            pre_df = {}
        col_nm_str = col_name.split(";")
        if len(col_nm_str) > 1:
            col_nm = col_nm_str[1]
        else:
            col_nm = col_nm_str[0]
        pre_df[col_nm] = data.tolist()
        if match:
            prev_cols = match
else:
    print('ファイルが生成されていません終了します')
    exit()

new_df.to_excel(tempName, index=False)

# windowsコマンドで実行　vbsファイルを指定
# command = ['cscript', vbsName]
# subprocess.call(command)
