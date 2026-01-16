from copy import copy
from enum import Enum, auto
from typing import Union, Optional
from Aras_connect.ArasAPI import Arasapi
import requests
import uuid

class IFtoARAS:

    def __init__(self, username:str, passward:str, baseURL:str, database:str):
        self.toARAS = Arasapi(baseURL, database)
        self.aras_status = self.toARAS._access_token(username, passward)
        self.username=username
        self.baseURL = baseURL
        self.database = database

    def gettoAPI(self,tbl,expLis=[],ArasFil=[],arasID="") ->tuple[requests.Response, dict, str]:
        # ユーザー入力をそのまま渡すとインジェクション攻撃ができるので注意
        query=_makeQuery(tbl,expLis,ArasFil,arasID)
        tmp=self.toARAS.getArasData(query)
        return tmp, tmp.json(),query
    
    def gettoAPIFile(self,query):
        # ユーザー入力をそのまま渡すとインジェクション攻撃ができるので注意
        tmp=self.toARAS.getArasData(query)
        return tmp

    def SearchPrjWithLot(self, prj_number: str, op='contains') -> Union[tuple[requests.Response, dict, str], bool]:
        if op == 'eq':
            query = f"z_sm_Project?$filter=z_number eq '{prj_number}'"
        elif op == 'contains':
            query = f"z_sm_Project?$filter=contains(z_number,'{prj_number}')"
        elif op == 'startswith':
            query = f"z_sm_Project?$filter=startswith(z_number,'{prj_number}')"
        elif op == 'endswith':
            query = f"z_sm_Project?$filter=endswith(z_number,'{prj_number}')"
        elif op == 'ne':
            query = f"z_sm_Project?$filter=z_number ne '{prj_number}'"
        else:
            return False
        if len(prj_number) > 1:
            # query += "&$expand=z_sm_r_Simu_Para($expand=related_id)パラメータセット管理用"
            query += "&$expand=z_sm_r_Prj_Lot($expand=related_id)"
        res = self.toARAS.getArasData(query)

        return res, res.json(), query
    
    def testtest(self):
        query = "sm_Task?$expand=z_sm_r_Task_condition"#&$expand=z_sm_r_Task_Afile"#?$filter=itemtype contains 'B1E7EC0D76B844F29EAFBF4451144C03'"
        # query = "z_sm_Project?$filter=z_number eq 'SElist_[Kei]_JPN_2WD'" + "&$expand=z_sm_r_Prj_Lot($expand=related_id)"
        # res = self.toARAS.getArasData(query)
        # return res, res.json(), query 
        # query = _makeQuery('z_sm_Lot',['z_sm_r_Lot_Allpara($expand=related_id($expand=created_by_id))'] , ArasID=itemId)
        # query = _makeQuery('sm_Task',['z_sm_r_Task_Afile'])
        # query = _makeQuery('z_sm_Lot',['z_sm_r_Lot_Allpara($expand=related_id)'] , ArasID=itemId)
        res = self.toARAS.getArasData(query)
        return res, res.json(), query 
    
    # def testtest(self, parav):
    #     # query = f"z_sm_ParaValue?$filter=z_paravalueid eq '{parav}"
    #     query = f"z_sm_ParaValue?$filter=z_paravalueid eq '{parav}'"
    #     query += "&$expand=created_by_id"
    #     res = self.toARAS.getArasData(query)
    #     return res, res.json(), query
    
    # def SearchPrjWithsim(self, para_name: str) -> Union[tuple[requests.Response, dict, str], bool]:
    #     query = f"z_sm_Simulation?$filter=z_name eq 'パラメータセット管理用'"
    #     # if len(para_name) > 1:
    #     #     # query += "&$expand=z_sm_r_Simu_Para($expand=related_id)パラメータセット管理用"
    #     query += "&$expand=z_sm_r_Simu_Para($expand=related_id)"
    #     res = self.toARAS.getArasData(query)

    #     return res, res.json(), query
    
    def GetAllProjects(self) -> Union[tuple[requests.Response, dict, str], bool]:
        query = "z_sm_Project"
        res = self.toARAS.getArasData(query)
        return res, res.json(), query

    def SearchPrjWithLot2(
            self, prj_number: str, op: tuple['filter_op'], *args
        ):
        """
        Args:
            prj_number (str): search word.
            op (tuple[filter_op]): tuple of filter_op.
            The op must have one of the filter_op.eq to filter_op.endswith
            *args (tuple[prj_number, op]): tuple of prj_number and filter options
        """
        query = "z_sm_Project?"
        query += _make_fil_query('z_number', prj_number, True, op)

        for v in args:
            query += _make_fil_query('z_number', v[0], False, v[1])
        if len(prj_number) > 1:
            query += "&$expand=z_sm_r_Prj_Lot($expand=related_id)"
        res = self.toARAS.getArasData(query)
        return res, res.json(), query

    def _getClassWithWP(self, classId: str):
        """ID指定された階層 - 階層 - WP - タスクの一覧を取得
        """
        query = f"z_sm_Class('{classId}')?$expand=z_sm_r_C_C($expand=related_id($expand=z_sm_r_Class_WP($expand=related_id($expand=z_sm_r_WP_Task($expand=related_id)))))"
        res = self.toARAS.getArasData(query)
        return res
    
    def getVehicleTasks(self, classId: str):
        """車両階層内で、車両階層 - 何らかの階層 - WP - Task を満たす階層配置のタスクidとタスク名を取得

        車両階層直下のWPまたは車両階層下に複数の階層を挟む WP - Task は対象外

        Args:
            classId (str): 車両階層のアイテムid
        Returns:
            list[list]: (id, keyed_name)というタプルが車両階層、二次階層、WP、タスクの順に格納された配列、の配列
        """
        tree = []
        res = self._getClassWithWP(classId)
        if res.status_code == 200:
            veh_wp = res.json()
            for rel_class in veh_wp['z_sm_r_C_C']:
                c2 = rel_class['related_id']
                r_c_wp = c2.get('z_sm_r_Class_WP')
                if r_c_wp:
                    # 下位にWPが存在する場合
                    for rel_wp in r_c_wp:
                        wp = rel_wp['related_id']
                        r_wp_t = wp.get('z_sm_r_WP_Task')
                        if r_wp_t:
                            # 下位にタスクが存在する場合
                            for rel_task in r_wp_t:
                                t = rel_task['related_id']
                                temp = [
                                    (classId, veh_wp['keyed_name']),
                                    (c2['id'], c2['keyed_name']),
                                    (wp['id'], wp['keyed_name']),
                                    (t['id'], t['keyed_name'])
                                ]
                                tree.append(temp)
        return res, tree

    def getRelatedItems(self, itemType: str, itemID: str, relationshipTypeName: str):
        # クエリにselect文を追加したい
        query = _makeQuery(itemType, f"{relationshipTypeName}($expand=related_id)", ArasID=itemID)
        res = self.toARAS.getArasData(query)
        res.raise_for_status()
        related_items = [rel['related_id'] for rel in res[relationshipTypeName]]
        return related_items, res

    def getLotWithAllpara(self, itemId:str):
        # query = _makeQuery('z_sm_Lot',['z_sm_r_Lot_Allpara($expand=related_id($expand=created_by_id))'] , ArasID=itemId)
        query = _makeQuery('z_sm_Lot',['z_sm_r_Lot_Allpara($expand=related_id)'] , ArasID=itemId)
        res = self.toARAS.getArasData(query)
        return res, res.json(), query
    
    def get_file_id(self,fileID):
        tmp,file_nm =self.toARAS.get_fileWithId(fileID)
        return tmp,file_nm
    
    def get_fileName_id(self, idx, fileID):
        file_nm =self.toARAS.get_fileNameWithId(fileID)
        return file_nm

    # def getsimWithAllpara(self):#, itemId:str):
    #     # query = _makeQuery('z_sm_Simulation',['z_sm_ParaValue($expand=related_id)'] , ArasID=itemId)
    #     query = "z_sm_Simulation&$filter=z_number eq '{prj_number}'"#&$expand=z_sm_r_Simu_Para($expand=related_id)"
    #     res = self.toARAS.getArasData(query)
    #     return res, res.json(), query
    
    def getTaskWithCondition(self, itemId:str):
        query = _makeQuery('sm_Task', ['z_sm_r_Task_condition($expand=related_id)'], ArasID=itemId)
        res = self.toARAS.getArasData(query)
        return res, res.json(), query

    def posttoAPI(self, tbl:str, Data: dict):
        query=_makeQuery(tbl)
        tmp=self.toARAS.postArasData(query, Data)
        return tmp,query

    def createParameter(self, Data: dict):
        return self.posttoAPI('z_sm_ParaValue', Data)

    def createRSLotAndAllPara(self, LotId:str, ParaId:str):
        Data = {
            "source_id@odata.bind": f"z_sm_Lot('{LotId}')",
            "related_id@odata.bind": f"z_sm_ParaValue('{ParaId}')"
        }
        return self.posttoAPI("z_sm_r_Task_condition",Data)

    def createRSTaskAndCondition(self, TaskId:str, ParaId:str):
        Data = {
            "source_id@odata.bind": f"sm_Task('{TaskId}')",
            "related_id@odata.bind": f"z_sm_ParaValue('{ParaId}')"
        }
        return self.posttoAPI("z_sm_r_Lot_Allpara",Data)

    def patchtoAPI(self, tbl, Data, ID):
        query=_makeQuery(tbl,ArasID=ID)
        tmp=self.toARAS.patchArasData(query,Data)
        return tmp,query
    def UploadPost(self, UploadFile, tbl, z_file_type=""):
        ## vault URL調べる
        #ログインユーザのdefault_vaultの取得
        query=_makeQuery("User",[f'default_vault'],[f'login_name eq {self.username}'])
        vault_id_result=self.toARAS.getArasData(query)
        vault_id=vault_id_result.json()["value"][0]["default_vault"]["id"]
        query=_makeQuery("Vault",ArasFil=[f"id eq '{vault_id}'"])
        vault_URL_result = self.toARAS.getArasData(query)
        vault_URL=vault_URL_result.json()["value"][0]["vault_url"]
        vault_URL1=vault_URL.replace("/Vault/vaultserver.aspx","")
        ##get a transaction id for uploading a file to the vault server
        transaction_url = vault_URL1 + "/vault/odata/vault.BeginTransaction"
        Header01={}
        Header01["Content-Type"]="application/json"
        Header01.update(self.toARAS.header)
        transaction_res = requests.post(transaction_url, headers=Header01)
        transaction_id=transaction_res.json()["transactionId"]
        ##upload the selected file using the transaction id
        myUUID = uuid.uuid4()
        myUUIDString = str(myUUID).replace("-","")
        file_id = myUUIDString.upper()
        size=UploadFile.size
        file_name=UploadFile.name
        start = 0
        end = size-1
        chunk_size=10000
        upload_url = vault_URL1 + "/vault/odata/vault.UploadFile?fileId=" + file_id
        while end < size - 1:
            end = start + chunk_size-1
            if size - end < 0:
                end = size-1
        # get an array of headers for this upload request
        header01 = {
                        "Content-Disposition":"attachment; filename*=utf-8''" + file_name,
                        "Content-Range":"bytes " + str(start) + "-" + str(end) + "/" + str(size),
                        "Content-Type":"application/octet-stream",
                        "transactionid":transaction_id,
                        "Authorization":self.toARAS.header["Authorization"]
                    }
        tmp=UploadFile.read(end-start+1)
        response=requests.post(upload_url, headers=header01, data=tmp)
        response
        # make the request to upload this file content
        start += chunk_size
        # commit the vault transaction to finish the file upload
        boundary = "batch_" + file_id
        commit_headers = {
            "Content-Type":"multipart/mixed; boundary="+boundary,
            "transactionid":transaction_id,
            "Authorization":self.toARAS.header["Authorization"]
            }
        commit_url = vault_URL1 + "/vault/odata/vault.CommitTransaction"
        # it's important to use the \r\n end of line character, otherwise commit will fail
        EOL = "\r\n"
        # build the commit body string
        commit_body = "--"
        commit_body += boundary
        commit_body += EOL
        commit_body += "Content-Type: application/http"
        commit_body += EOL
        commit_body += EOL
        commit_body += "POST " + self.baseURL + "/server/odata/File HTTP/1.1"
        commit_body += EOL
        commit_body += "Content-Type: application/json"
        commit_body += EOL
        commit_body += EOL
        commit_body += '{"id":"' + file_id + '",'
        commit_body += '"filename":"' + file_name + '",'
        commit_body += '"file_size":' + str(size) + ','
        commit_body += '"Located":[{"file_version":1,"related_id":"67BBB9204FE84A8981ED8313049BA06C"}]}'
        commit_body += EOL
        commit_body += "--" + boundary + "--"
        # send the commit request to the vault server
        result = requests.post(commit_url, headers=commit_headers, data=commit_body)
        data={
            "z_file@odata.bind":f"File('{file_id}')",
            "z_file_type":z_file_type
        }
        FilePost=requests.post(self.baseURL + "/Server/odata/{0}".format(tbl),
                          headers=self.toARAS.header, json=data)
        return FilePost.json()["id"], result

    def deletetoAPI(self, tbl:str, arasID:str):
        send_xml = "<?xml version='1.0' encoding='utf-8' ?>"\
                   "<SOAP-ENV:Envelope xmlns:SOAP-ENV='http://schemas.xmlsoap.org/soap/envelope/'><SOAP-ENV:Body>"\
                       "<ApplyAML><AML>"\
                           f"<Item type='{tbl}' id='{arasID}' action='delete'></Item>"\
                       "</AML></ApplyAML>"\
                   "</SOAP-ENV:Body></SOAP-ENV:Envelope>"
        header = copy(self.toARAS.header)
        header['Content-Type'] = "text/xml;charset=utf-8"
        header['SOAPaction'] = "ApplyAML"
        return requests.post(f'{self.baseURL}/Server/InnovatorServer.aspx', headers=header, data=send_xml.encode())


class filter_op(Enum):
    # logical operators
    AND = auto()
    OR = auto()
    NOT = auto()
    # comparison operators for number
    lt = auto()
    le = auto()
    gt = auto()
    ge = auto()
    # comparison operators
    eq = auto()
    ne = auto()
    # string functions
    contains = auto()
    startswith = auto()
    endswith = auto()

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented
    

def _make_fil_query(
        property: str,
        search: Union[str, int, float],
        head=False,
        filter_options: tuple[filter_op]=(filter_op.eq)
    ):
    # クエリの先頭
    if head:
        query = '$filter='
    elif filter_op.OR in filter_options:
        query = ' or '
    else:
        query = ' and '

    # comparison operatorsまたはstring functionsを含んでいるかチェック
    compare_options = [x for x in filter_options if x >= filter_op.lt]
    if len(compare_options) != 1:
        raise ValueError('filter_op must have one of comparison options')

    # NOTの有無チェック
    if filter_op.NOT in filter_options:
        query += "not "

    compare_op = compare_options[0]
    if filter_op.lt <= compare_op <= filter_op.ne:
        if type(search) == str:
            query += f"{property} {compare_op.name} '{search}'"
        else:
            query += f"{property} {compare_op.name} {search}"
    elif compare_op >= filter_op.contains:
        query += f"{compare_op.name}({property}, '{search}')"

    return query


def _makeQuery(ArasTBL, ArasExp=[], ArasFil=[], ArasID="", ArasRTBL=""):
    query=ArasTBL
    if ArasFil!=[]:
        query+=f'?$filter={" and ".join(ArasFil)}'
    if ArasID!="":
        if not isHex(ArasID):
            raise TypeError('ArasID must be hex.')
        query+=f"('{ArasID}')"
    if ArasRTBL!="":
        query+=f'/{ArasRTBL}'
    if ArasExp!=[]:
        if ArasFil!=[]:
            query+=f'&$'
        else:
            query+=f'?$'
        query+=f'expand={(", ".join(ArasExp))}'
    return query


def isHex(num_str:str):
    """渡された引数が16進数であるか否かを判断する。

    16進数でないときはFalseを返し、0以外の整数であるときはその値を返す。
    0の時のみTrueを返す。
    """
    try:
        num_hex = int(num_str, 16)
        return num_hex if num_hex != 0 else True
    except ValueError:
        return False


