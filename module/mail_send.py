#
# import win32com.client
# import sys
# import pythoncom
#
# def mail_send_func(user, comment):
#
#     outlook = win32com.client.Dispatch("Outlook.Application")
#     mail = outlook.CreateItem(0)
#
#     mail.to = 'N202551'
#     mail.CC = 'BSN00147'
#     mail.subject = 'SpDM閲覧権限の依頼がありました。'
#     mail.bodyFormat = 2
#     mail.body = '''
# ユーザがUIの編集操作を要求しています。
#
# ユーザ：''' + user + ''' のアカウントを作成してください。
#
# <ユーザコメント>
#
# ''' + comment + '''
#
#
# おわり
#
# '''
#
#     mail.Send()
#
#
# def request_usecase(user, comment):
#     pythoncom.CoInitialize()
#     outlook = win32com.client.Dispatch("Outlook.Application")
#     mail = outlook.CreateItem(0)
#
#     mail.to = 'N202551'
#     mail.CC = 'BSN00147'
#     mail.subject = 'ユースケースの追加申請がありました。'
#     mail.bodyFormat = 2
#     mail.body = '''
# <ユーザ>'''+user+'''
# <ユーザコメント>
#
# ''' + comment + '''
#
#
# おわり
#
# '''
#
#     mail.Send()
#     outlook.quit()
#     pythoncom.CoUninitialize()
# if __name__ == "__main__":
#     mail_send_func(sys.argv[1],sys.argv[2])