import streamlit as st
from io import BytesIO
import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl import Workbook
from openpyxl.styles import Border, Side, Font,PatternFill,Color,Alignment
import module.excel.excel_hierarchical_style as hr_styles


def create_hierarchical_excel_data(df,GridBlock:hr_styles.GridBlock,wb=None,meta_info=None,wp=None):
    """excelデータ作成

    Args:
        df (dataframe): rfl_dataframe
        BytesIO: excel_file
        meta_info(dict): meta_info

    Returns:
        BytesIO: stream(excel data)
    """

    prefix = df.columns[1][:1]

    # meta_infoはダイアログで入力した内容を車両性能の上に表示する

    if wb == None:
        wb = Workbook()
        meta_info = meta_info
        ws = wb.active
        ws.title = f'RFL_XXXX_{wp}'
    else:
        wb.seek(0)
        wb = load_workbook(wb)
        ws = wb.active

    ws.sheet_view.showGridLines=False


    # ------------------------------------- Helper -------------------------------------

    def paint_cell(min_row,max_row,min_col,max_col,fill):
        """Helper : セル色付け処理

        Args:
            min_row (int): min row for range
            max_row (int): max row for range
            min_col (int): min col for range
            max_col (int): max col for range
            fill (PatternFill): PatternFill
        """

        for row in range(min_row,max_row + 1):
            for col in range(min_col,max_col + 1):
                cell = ws.cell(row=row,column=col)
                cell.fill = fill

    def set_font(ws,font):
        """ Helper : font全適用

        Args:
            ws (Workbook): active worksheet
            font (string): Meiryo UI
        """

        # font全適用
        for row in ws:
            for cell in row:
                old_font = cell.font
                new_font = Font(
                    name=font,
                    color=old_font.color,
                    size=old_font.size
                )
                cell.font = new_font

    def format_df(df):
        """Helper : 不必要カラムドロップ

        Args:
            df (dataframe): rfl dataframe

        Returns:
            dataframe: front dataframe for excel
        """

        prefix = df.columns[0][:2]
        drop_column = [col.format(prefix) for col in hr_styles.DROP_COLUMN]
        df = df.drop(columns=drop_column, errors='ignore')
        return df

    def create_header_outer_border(min_row,max_row,min_col,max_col):
        """Helper : 外枠作成

        Args:
            min_row (int): min row for range
            max_row (int): max row for range
            min_col (int): min col for range
            max_col (int): max col for range
        """

        thin_side = Side(border_style="thin", color="000000")
        medium_side = Side(border_style="medium",color="000000")
        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                cell = ws.cell(row=row, column=col)

                # 外枠設定 最終行列の場合、medium
                top = medium_side if row == min_row else None
                bottom = thin_side if row == max_row else None
                left = medium_side if col == min_col else None
                right = medium_side if col == max_col else None

                cell.border = Border(top=top, bottom=bottom, left=left, right=right)

    def set_column_and_cell_format(ws):
        """Helper : setting column width height,Font Setting

        Args:
            ws (Workbook): active worksheet
        """

        # 幅限界設定
        limit = hr_styles.LIMIT_WIDTH

        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter

            for cell in col:
                # 折り返し設定
                cell.alignment = Alignment(wrapText=True)

                # font設定
                old_font = cell.font
                new_font = Font(name='Meiryo UI',color=old_font.color,size=old_font.size)
                cell.font = new_font

                # 幅調整用max_length格納
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))

            # 各列幅自動調整
            adjusted_width = (max_length + 2) * 1.5
            if adjusted_width > limit:
                adjusted_width = limit
            ws.column_dimensions[column].width = adjusted_width

    # ----------------------------------- Meta -----------------------------------

    def create_meta_info(meta_info,ws):
        """メタ情報グリッド作成

        Args:
            df (dataframe): rfl dataframe
            ws (Workbook): active worksheet
        """

        for column,data in zip(hr_styles.META_DEF.values(),meta_info.values()):

            # 項目
            cell = ws.cell(row=column.row,column=column.col,value=column.value)
            cell.border = column.side
            cell.fill = column.fill

            # Value
            cell = ws.cell(row=column.row,column=column.col + 1,value=data)
            cell.border = hr_styles.META_BORDER


    # ------------------------------------- Header -------------------------------------

    def create_header(ws,hr):
        """Hierarchy,各Header作成

        Args:
            ws (Workbook): active worksheet
            hr (string): hierarchy prefix
        """

        # Hierarchy 判定
        if hr == 'c':
            value = '車両性能'
            hr_header_fill = hr_styles.VEHICLE_FILL
        if hr == 's':
            value = 'System'
            hr_header_fill = hr_styles.SYSTEM_FILL
        if hr == 'u':
            value = 'Unit'
            hr_header_fill = hr_styles.UNIT_FILL

        # ------------------------------------- Hierarchy Header -------------------------------------

        # Hierarchy Header
        hr_header = ws.cell(row=hr_styles.HIERARCHY_ROW,column=GridBlock.init_col,value=value)

        # Hierarchy Header Font
        hr_header.font = hr_styles.HR_FONT

        # Hierarchy Header Color
        for row in ws.iter_rows(**GridBlock.hr_header_range):
            for cell in row:
                cell.fill = hr_header_fill


        # ------------------------------------- RFL Header -------------------------------------

        for header in GridBlock.header_defs.values():
            ws.cell(row=header.row,column=header.col,value=header.value)
            create_header_outer_border(header.row,header.row,header.col,header.max_col)
            paint_cell(header.row,header.row,header.col,header.max_col,header.fill)


    # ------------------------------------- Column -------------------------------------

    def create_columns(ws):
        """各カラム作成

        Args:
            ws (Workbook): active worksheet
        """

        # Columns
        for column in GridBlock.column_defs.values():
            cell = ws.cell(row=column.row,column=column.col,value=column.value)
            cell.border = column.side
            paint_cell(column.row,column.row,column.col,column.col,column.fill)


    # ------------------------------------- Value -------------------------------------
    # value input , draw grid line

    def input_value(df,ws):
        """input value of dataframe

        Args:
            df (dataframe): dataframe
            ws (Workbook): active worksheet
        """

        medium = Side(style='medium')
        thin = Side(style='thin')
        bottom = thin

        target_cols = hr_styles.BORDER_DELETE_TARGET_COL
        for r_idx,row in enumerate(dataframe_to_rows(df , index=False,header=False)):
            row_number = df.shape[0]
            col_number = df.shape[1]

            for c_idx,value in enumerate(row):
                
                # target = df.columns[r_idx][2:]
                target = df.columns[c_idx][2:]
                # ヘッダーの区切りをmediumに設定
                if c_idx in (GridBlock.medium_border_cols):
                    left = medium
                else:
                    left = thin

                # 最終列の線をmediumに設定
                if c_idx == col_number - 1:
                    right = medium

                else:
                    right = thin


                # # 最終行の線をmediumに設定
                # if r_idx == row_number - 1:
                #     bottom = medium

                # else:
                #     bottom = thin


                # 指定列の罫線削除処理
                if target in target_cols:
                    if r_idx == row_number-1:
                        next_value = 'max_row'
                    else:
                        next_value = df.iat[r_idx+1,c_idx]

                    if next_value == '' or next_value == None:
                        bottom = None

                    if value == '' or value == None:
                        top = None
                    else:
                        top = thin
                else:
                    top = thin

                # 承認、ノート列の調整
                del_target = ['sender_judge','sender_name','sender_date','sender_comment','receiver_judge','receiver_name','receiver_date','receiver_comment','note']
                if df.columns[c_idx][2:] in del_target:
                    target_suffix = ['r_item','f_item','l_item']

                    # rflがすべて重複しているケースを抽出
                    matched_cols = [col for col in df.columns if col[2:] in target_suffix]
                    row_for_varidation = df.loc[df.index[r_idx],matched_cols]
                    is_all_empty = ((pd.isna(row_for_varidation)) | (row_for_varidation == '')).all()
                    if is_all_empty:
                        if r_idx == row_number - 1:
                            next_value = 'max_row'
                        else:
                            next_value = df.iat[r_idx+1,c_idx]

                        prev_value = df.iat[r_idx-1,c_idx]

                        # bottom
                        if next_value:
                            bottom = thin

                        if next_value == '' or next_value is None:
                            bottom = None

                        if (value == '' or value is None):
                            top = None
                        else:
                            top = thin

                # 最終行の線をmediumに設定
                if r_idx == row_number - 1:
                    bottom = medium


                # 処理とエクセル列の開始地点のずれを修正
                cell = ws.cell(row=hr_styles.VALUE_ROW + r_idx,column=GridBlock.init_col + c_idx,value=value)
                cell.border = Border(
                    left = left,
                    right=right,
                    top=top,
                    bottom=bottom
                )



    # メタ情報作成
    if meta_info is not None:
        create_meta_info(meta_info,ws)

    create_header(ws,prefix)
    create_columns(ws)
    input_value(df,ws)

    # set column width and set cell font
    set_column_and_cell_format(ws)

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)

    return stream.getvalue()