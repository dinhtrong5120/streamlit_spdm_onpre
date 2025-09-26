Dim objExcel
Dim objWorkbook
Dim objWorksheet
dim i
Dim args
dim VBA_file

' 引数を変数に代入
Set args = WScript.Arguments

' Excelアプリケーションオブジェクトを作成
Set objExcel = CreateObject("Excel.Application")

' ポップアップなどが出ないようにする
objExcel.DisplayAlerts = False

' ファイルパスを指定　VBA_file：IDAJツールのパス　change_file2wd:変換表2wd　change_file4wd：変換表4wd updata_file:csvをエクセルに変換されたファイル
VBA_file = "C:\Python Project\Streamlit\SE List\FY24_kei\Aras Updata VBA\パラメータ情報編集エクセル_ver18.08_数値更新用.xlsm"
change_file2wd = "https://nissangroup-my.sharepoint.com/personal/satoshi-ando_mail_nissan_co_jp/Documents/_%E2%96%A1kei_Sim_%E6%96%B0%E9%9A%8E%E5%B1%A4/%E5%A4%89%E6%8F%9B%E8%A1%A8/%E5%A4%89%E6%8F%9B%E8%A1%A8%EF%BC%88%E2%96%A1kei%EF%BC%89_2WD_20240515_%E2%96%A12.xlsx?web=1"
change_file4wd = "https://nissangroup-my.sharepoint.com/personal/satoshi-ando_mail_nissan_co_jp/Documents/_%E2%96%A1kei_Sim_%E6%96%B0%E9%9A%8E%E5%B1%A4/%E5%A4%89%E6%8F%9B%E8%A1%A8/%E5%A4%89%E6%8F%9B%E8%A1%A8%EF%BC%88%E2%96%A1kei%EF%BC%89_4WD_20240515_%E2%96%A11.xlsx?web=1"
Updata_faile = "C:\Python Project\Streamlit\SE List\FY24_kei\temp\temp_file.xlsx"
' ブックを開く　ブックのオブジェクトからシートを指定している
Set objWorkbook = objExcel.Workbooks.Open(VBA_file)
Set objWorksheet = objWorkbook.Worksheets("①他部門からの前提の新規作成・更新")
' 対象プロジェクトをリストに入力している
arr = Array("[kei]_Sim_test_2WD", "[kei]_Sim_test_4WD")

For Each prj In arr

    ' プロジェクト番号
    objWorksheet.Range("E3") = prj
    ' (エクセル利用者の)階層
    objWorksheet.Range("E4") = ""
    ' (エクセル利用者の)WP
    objWorksheet.Range("E5") = ""
    ' ロット
    objWorksheet.Range("E6") = "PT構想審査"
    ' 担当のタスク番号
    objWorksheet.Range("E7") = ""
    ' ArasURL
    objWorksheet.Range("G3") = "http://internal-awcp0018-alb00105-616219119.ap-northeast-1.elb.amazonaws.com/NPM_Innovator"
    ' データベース名
    objWorksheet.Range("G4") = "NPM_Innovator"
    ' ログインID
    objWorksheet.Range("G5") = "N911267"
    ' ログインパスワード
    objWorksheet.Range("G6") = "N911267"

    ' レンジで必要情報を入力したらマクロ実行　パラメータ取得マクロ
    objExcel.run "パラメータ値取得_Click" , "シート①_1"

    ' 実行が終了するまで待機する
    Do Until objExcel.Ready
        WScript.Sleep 1000 ' 1秒待機
    Loop

    ' エクセルファイルを指定
    Set updWorkbook = objExcel.Workbooks.Open(Updata_faile)
    Set updWorksheet = updWorkbook.Worksheets(1)
    ' 現在のループが2wdか4wdかで分岐を分ける（変換表はプロジェクトごとなので２つファイルがあります。
    if prj = "[kei]_Sim_test_2WD" then
        Set cngWorkbook = objExcel.Workbooks.Open(change_file2wd)
    else
        Set cngWorkbook = objExcel.Workbooks.Open(change_file4wd)
    end if        
    Set cngWorksheet = cngWorkbook.Worksheets("変換表")

    ' 最終行を取得する
    lastRow = updWorksheet.Cells(updWorksheet.Rows.Count, 1).End(-4162).Row

    ' 更新エクセルの最終行まで繰り返し処理を行う　更新エクセルのパラメータをマクロで出力されたパラメータにあるか確認する。あれば手作業の手順と同じように”更新”文字の入力と数値の入力をする
    For i = 2 To lastRow
        findValue = updWorksheet.Range("AE" & i)
        up_data = updWorksheet.Range("Z" & i)

        Set objRange = objWorksheet.Range("D:D")
        Set cobRange = cngWorksheet.Range("Z:Z")

        ' 指定したプロパティの値が一致するセルを検索する
        Set foundCell = objRange.Find(findValue)
        set cobfindcl = cobRange.Find(findValue)

        If Not foundCell Is Nothing Then
            search_row = foundCell.row
            objvalue = objWorksheet.Range("O" & search_row)
            ' 数値が違う場合更新手続きをするように自動で入力します
            if up_data <> objvalue Then
                objWorksheet.Range("B" & search_row) = "更新"
                objWorksheet.Range("O" & search_row) = up_data
                ' 更新したときは変換表も更新したことが分かるように更新した内容をシートに残す
                If Not cobfindcl Is Nothing Then
                    search_row = cobfindcl.row
                    cngWorksheet.Range("AR" & search_row) = up_data
                end if 
            end if
        End If
    Next
    
    updWorkbook.Close false
    cngWorkbook.Save
    cngWorkbook.Close
    ' Excelファイルを保存

    ' 更新すべきパラメータのすべてに入力が完了したら更新マクロを実行する
    objExcel.run "パラメータ値更新_Click" , "シート①_2"

    ' 実行が終了するまで待機する
    Do Until objExcel.Ready
        WScript.Sleep 1000 ' 1秒待機
    Loop

Next
' Excelファイルを閉じる
objWorkbook.Close false

' Excelアプリケーションを終了
objExcel.Quit

' オブジェクトを解放
set args = Nothing
Set cngWorksheet = Nothing
Set cngWorkbook = Nothing
Set objWorksheet = Nothing
Set objWorkbook = Nothing
Set objExcel = Nothing