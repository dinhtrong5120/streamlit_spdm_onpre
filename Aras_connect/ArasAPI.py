"""ARAS RESTful API for Python

Get an access token with MD5 and make three requests:
GET, POST, and PATCH.
The DELETE request is commented out
because it seems to be disabled in Nissan's environment.
"""
import requests
import hashlib
from typing import Union
import json
import pandas as pd
###APIクラス ～パーシスタンス～###
class Arasapi:
    def __init__(self, baseURL:str, database:str):
        self.baseURL = baseURL #
        self.database = database #

    ### アクセストークン ###
    def _access_token(self, username:str, password:str):
        #パスワードをMD5ハッシュ値へ変換
        oauth_password_hs = hashlib.md5(password.encode()).hexdigest()
        #OAuthServerURLの取得
        url = self.baseURL + "/Server/OAuthServerDiscovery.aspx"
        response1 = requests.get(url)
        oauth_Server_URL = response1.json()["locations"][0]["uri"]
        #Token EndPointの取得
        url2 = oauth_Server_URL + ".well-known/openid-configuration"
        response2 = requests.get(url2)
        oauth_ServerToken_URL = response2.json()["token_endpoint"]
        #Tokenの取得
        payload = {'grant_type': 'password', 'scope': 'Innovator', 'client_id': 'IOMApp',
                   'username': username, 'password': oauth_password_hs, 'database': self.database} #oauth_username
        response3 = requests.post(oauth_ServerToken_URL,  data=payload)

        if not response3.status_code == 200:
            return None
        
        token = response3.json()["access_token"]
        ##トークンはヘッダーで扱う##
        self.header = {"Authorization":"Bearer " + token}

        return response3.status_code

    ### get ###        
    def getArasData(self, query:str):
        return requests.get(f'{self.baseURL}/server/odata/{query}',
                             headers=self.header)
    
    def get_fileWithId(self,fileID):
        # file_id=pd.json_normalize(data[\"value"])["z_design_file_check"].values.tolist()[0]
        
        if fileID is not None:
            file_link="File('"+fileID+"')/$value"
            file_result=requests.get(self.baseURL + "/server/odata/{0}".format(file_link),headers=self.header)
            file_result=file_result.content
            file_link="File('"+fileID+"')/"
            file_nm_result=requests.get(self.baseURL + "/server/odata/{0}".format(file_link),headers=self.header)
            file_nm_result=file_nm_result.content
            json_str = file_nm_result.decode('utf-8')
            # JSON文字列を辞書に変換
            data = json.loads(json_str)
            # filenameフィールドの値を取得
            filename = data['filename']
        
            # file_result = self.baseURL + "/s/odata/{0}".format(file_link)+self.header
        return file_result,filename

    def get_fileNameWithId(self,fileID):
        # file_id=pd.json_normalize(data[\"value"])["z_design_file_check"].values.tolist()[0]
        # fileID = str(fileID)
        # print(fileID)
        filename = ""
        if not pd.isna(fileID):

            file_link="File('"+fileID+"')/"
            file_nm_result=requests.get(self.baseURL + "/server/odata/{0}".format(file_link),headers=self.header)
            file_nm_result=file_nm_result.content
            json_str = file_nm_result.decode('utf-8')
            # JSON文字列を辞書に変換
            data = json.loads(json_str)
            # filenameフィールドの値を取得
            filename = data['filename']
        return filename

    ### post ###
    def postArasData(self, query:str, JsonData:dict[str, Union[str, int, dict]]):
        return requests.post(f'{self.baseURL}/server/odata/{query}',
                             headers=self.header, json=JsonData)

    ### patch ###
    def patchArasData(self, query:str, JsonData:dict[str, Union[str, int, dict]]):
        return requests.patch(f'{self.baseURL}/server/odata/{query}',
                             headers=self.header, json=JsonData)

    # ### delete ###
    # def deleteArasData(self, query, JsonData=None):
    #     if JsonData:
    #         return requests.delete(f'{self.baseURL}/server/odata/{query}',
    #                                headers=self.header, json=JsonData)
    #     else:
    #         return requests.delete(f'{self.baseURL}/server/odata/{query}',
    #                                headers=self.header)
