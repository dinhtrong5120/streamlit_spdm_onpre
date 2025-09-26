import pandas as pd
import numpy as np
import streamlit as st

def is_num(s, na=False):
    """数値かどうか判定。デフォルトではnanはfalseとする。

    Args:
        s (string)
        na (bool)

    Returns:
        bool
    """
    try:
        if np.isnan(float(s)):
            return na
    except (ValueError, TypeError):
        return False
    else:
        return True

def del_session(keys):
    """Streamlitのセッション情報を一括で削除する

    Args:
        keys (list or str): deleteしたいkeyまたはそのリスト
    """
    if isinstance(keys, str):
        keys = [keys]
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]

def set_session(dic, delete=None):
    """Streamlit のセッション情報を一括で変更する

    Args:
        dic (dict): keyはsession_stateのkey。valueは設定したい値
        delete: deleteしたいkey
    """
    for k, v in dic.items():
        if k in st.session_state:
            st.session_state[k] = v
    if delete is not None:
        del_session(delete)

def write_df(sheet, df, start_row, start_col):
    """pandas DataframeをExcelに入力

    Args:
        sheet (openpyxl worksheet)
        df (Pandas DataFrame)
        start_row (int): 入力先左上の行番号
        start_col (int): 入力先左上の列番号
    """
    for y in range(len(df)):
        for x in range(len(df.columns)):
            sheet.cell(row=start_row + y,
                       column=start_col + x,
                       value=df.iloc[y, x])

def fill_index(df):
    for i, row in df.iterrows():
        if df.index.get_loc(i) == 0:
            continue
        for col in row.index:
            if pd.isnull(row[col]):
                df.at[i,col] = df.at[i-1,col]
            else:
                break
    return df

def comp_ePT(df):
    '''GT-SUITE ePT損失Mapの外挿補間関数

    Args:
        df (pandas DataFrame)
    '''
    if df[0].isna().all():
        df[0] = 0
    row_index = np.array(df.index).astype('int64')
    col_index = np.array(df.columns).astype('int64')
    arr = df.values.astype('float64')
    # 補間対象フィルタ
    filter = np.isnan(arr)
    filter[:,0] = False

    arr1 = col_index * np.abs(row_index.reshape([-1,1])) * 2 * np.pi / 60 / 1000
    arr1 = arr1.astype('float64')

    arr2 = (1 - arr / arr1) * 100
    df2 = pd.DataFrame(arr2,index=row_index, columns=col_index).ffill(axis='columns')

    df = df.mask(filter,(arr1 * (100 - df2.values) / 100))
    return df

def comp_GB(df):
    '''GT-SUITE GB損失Mapの外挿補間関数

    Args:
        df (pandas DataFrame)
    '''
    # 正トルクかつ高回転の外挿補間
    df[df.index>0] = df[df.index>0].ffill(axis='columns')
    # 負トルクかつ高回転の外挿補間
    for col in df.index:
        if col < 0:
            # 正トルク時の値で補間
            df.loc[col] = df.loc[col].fillna(df.loc[abs(col)])
    return df

def seino_normalize(l):
    '''RFLの性能の名称を正規化する

    Args:
        l (iterable[string])

    Returns:
        list[string]
    '''
    l = ['燃費' if str(x)=='電費' else str(x) for x in l]
    l = ['音振' if '音振' in x else x for x in l]
    l = ['音振' if '高周波' in x else x for x in l]
    l = ['音振' if '低周波' in x else x for x in l]
    return l

def get_SEList(df_SE_full, kento="No002"):
    '''SEリストを取得する

    Args:
        df (pandas DataFrame): "07_性能計画情報リスト(データ入力用)"シート。pd.read_excelまま
        kento (string): "No001", "No002", "No003"のいずれか。いずれでもない場合はとりあえずNo001で作成。

    Returns:
        DataFrame: 先頭列に対象性能の表を結合した机上検討用リスト
    '''
    paraname_col = (5,12)
    seino_col = (1,4)
    df_SE_full = df_SE_full.iloc[5:].replace([' ','　'],pd.NA).dropna(how='all').reset_index(drop=True)

    # データ部分だけ取り出し（パラメータ名なし）
    kento_col_list = df_SE_full.loc[:,df_SE_full.loc[0,:].str.contains('D-SUV.+回目', na=False)].columns
    # print('cols',kento_col_list)  # debug add
    if kento == "No001":
        start_col = df_SE_full.columns.get_loc(kento_col_list[0])
        end_col = df_SE_full.columns.get_loc(kento_col_list[1])
    elif kento == "No002":
        start_col = df_SE_full.columns.get_loc(kento_col_list[1])
        end_col = df_SE_full.columns.get_loc(kento_col_list[2])
    elif kento == "No003":
        start_col = df_SE_full.columns.get_loc(kento_col_list[2])
        end_col = df_SE_full.columns.get_loc(kento_col_list[2]) * 2\
                - df_SE_full.columns.get_loc(kento_col_list[1])
    else: # とりあえずNo001を選択しておく
        start_col = df_SE_full.columns.get_loc(kento_col_list[0])
        end_col = df_SE_full.columns.get_loc(kento_col_list[1])

    _df = df_SE_full.iloc[2:,start_col:end_col]
    _df = _df.set_axis(labels=_df.loc[2,:],axis='columns')
    df_data = _df.iloc[2:].reset_index(drop=True)

    # パラメータ名を整える
    df_paraname = df_SE_full.iloc[4:,paraname_col[0]:paraname_col[1]+1].reset_index(drop=True)
    df_paraname = fill_index(df_paraname)

    seino_filter = df_SE_full.iloc[4:,seino_col[0]:seino_col[1]+1].reset_index(drop=True)
    seino_filter.columns = df_SE_full.columns[seino_col[0]:seino_col[1]+1]
    ID = df_SE_full.loc[:,df_SE_full.iloc[3]=='識別ID']
    ID = ID.iloc[4:,:].reset_index(drop=True)
    ID.columns = ['識別ID']

    df_paraname = df_paraname.reset_index(drop=True)
    df_paraname.columns = ['システム名', '管理区分','管理項目名','補足1','補足2','補足3','補足4','単位']

    df_paraname = pd.merge(seino_filter, df_paraname, left_index=True, right_index=True)

    # パラメータ名とデータを連結
    df_para = pd.merge(df_paraname, df_data, left_index=True, right_index=True)
    return pd.merge(df_para,ID, left_index=True, right_index=True)

def get_KijoKentoList(df_kijo_full, kento="No002"):
    '''SEリストから机上検討用リストを取得する

    Args:
        df_kijo_full (pandas DataFrame): "06_机上検討用データリスト(閲覧のみ)"シート。pd.read_excelまま
        kento (string): "No001", "No002", "No003"のいずれか。いずれでもない場合はとりあえずNo001で作成。

    Returns:
        DataFrame: 先頭列に対象性能の表を結合した机上検討用リスト
    '''
    paraname_col = (3,10)
    seino_col = (11,18)
    df_kijo_full = df_kijo_full.iloc[5:].replace([' ','　'],pd.NA).dropna(how='all').reset_index(drop=True)

    # データ部分だけ取り出し（パラメータ名なし）
    kento_col_list = df_kijo_full.loc[:,df_kijo_full.loc[0,:].str.contains('D-SUV.+回目', na=False)].columns
    # print('cols',kento_col_list)  # debug add
    if kento == "No001":
        start_col = df_kijo_full.columns.get_loc(kento_col_list[0])
        end_col = df_kijo_full.columns.get_loc(kento_col_list[1])
    elif kento == "No002":
        start_col = df_kijo_full.columns.get_loc(kento_col_list[1])
        end_col = df_kijo_full.columns.get_loc(kento_col_list[2])
    elif kento == "No003":
        start_col = df_kijo_full.columns.get_loc(kento_col_list[2])
        end_col = df_kijo_full.columns.get_loc(kento_col_list[2]) * 2\
                - df_kijo_full.columns.get_loc(kento_col_list[1])
    else: # とりあえずNo001を選択しておく
        start_col = df_kijo_full.columns.get_loc(kento_col_list[0])
        end_col = df_kijo_full.columns.get_loc(kento_col_list[1])

    _df = df_kijo_full.iloc[2:,start_col:end_col]
    _df = _df.set_axis(labels=_df.loc[2,:],axis='columns')
    df_data = _df.iloc[14:,:].reset_index(drop=True)
    df_car_info = _df.iloc[:14,:].reset_index(drop=True)

    # パラメータ名を整える
    df_paraname = df_kijo_full.iloc[16:,paraname_col[0]:paraname_col[1]+1].reset_index(drop=True)
    for i, row in df_paraname.iterrows():
        if i==0:continue
        for col in row.index:
            if pd.isnull(row[col]):
                df_paraname.at[i,col] = df_paraname.at[i-1,col]
            else:
                break
    seino_filter = df_kijo_full.iloc[16:,seino_col[0]:seino_col[1]+1].reset_index(drop=True)
    seino_filter.columns = df_kijo_full.iloc[3,seino_col[0]:seino_col[1]+1]

    df_paraname = df_paraname.reset_index(drop=True)
    df_paraname.columns = ['システム名', '管理区分','管理項目名','補足1','補足2','補足3','補足4','単位']

    df_paraname = pd.merge(seino_filter, df_paraname, left_index=True, right_index=True)

    # パラメータ名とデータを連結
    df_para = pd.merge(df_paraname, df_data, left_index=True, right_index=True)
    return df_para