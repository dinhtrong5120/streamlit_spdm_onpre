"""ARASのIOM Referenceを参考に作成された、IOMによく似たナニカ

似せて作られているが中身は別物のため、一部挙動が異なることに注意して使われたし。
"""
from copy import copy, deepcopy
import requests
import hashlib
from lxml import etree


class Innovator:
    """ARASとのセッション情報の保持及びAMLの適用を行う

    Attributes:
        baseURL (str): ARAS URL
        database (str): ARAS Database name
        header (dict[str]): requests header
    """
    def __init__(self, ArasUrl: str, ArasDB: str, header: dict[str]) -> None:
        self.baseURL = ArasUrl
        self.database = ArasDB
        self.header = header
        self.header['Content-Type'] = "text/xml;charset=utf-8"
        self.header["SOAPaction"] = "ApplyAML"

    @classmethod
    def connect(cls, ArasUrl: str, ArasDB: str, username: str, password:str) -> None:
        """
        Args:
            ArasUrl (str):
            [URL of ARAS Server] / [Alias of Innovator Server]
            ArasDB (str): Innovator server name
            username (str): Login user name
            password (str): Login user password
        """
        token = cls.getToken(ArasUrl, ArasDB, username, password)
        # headerにトークンをセット
        header = {"Authorization":"Bearer " + token}
        return cls(ArasUrl, ArasDB, header)


    @classmethod
    def getToken(cls, ArasUrl: str, ArasDB: str, username: str, password: str) -> str:
        #パスワードをMD5ハッシュ値へ変換
        oauth_password_hs = hashlib.md5(password.encode()).hexdigest()
        #OAuthServerURLの取得
        url = ArasUrl + "/Server/OAuthServerDiscovery.aspx"
        response1 = requests.get(url)
        oauth_Server_URL = response1.json()["locations"][0]["uri"]
        #Token EndPointの取得
        url2 = oauth_Server_URL + ".well-known/openid-configuration"
        response2 = requests.get(url2)
        oauth_ServerToken_URL = response2.json()["token_endpoint"]
        #Tokenの取得
        payload = {'grant_type': 'password', 'scope': 'Innovator', 'client_id': 'IOMApp',
                   'username': username, 'password': oauth_password_hs, 'database': ArasDB} #oauth_username
        response3 = requests.post(oauth_ServerToken_URL,  data=payload)
        return response3.json()["access_token"]


    def newIOMItem(self, tbl, act='get'):
        return IOMItem.newItem(tbl, act, self)


    def applyAML(self, aml: str):
        """AMLをARASサーバに読み込ませる
        POSTリクエストにAMLを付帯させ、SOAP APIによりARASサーバーメソッド"ApplyAML"を実行させます。

        Args:
            aml (str): AML文字列

        Raieses:
            Exception: 'HTTP Error' はPOSTリクエストのレスポンスコードが200以外の場合に生じます。
            'ApplyAMLError' はSOAP APIに基づくレスポンスコンテンツであるXMLにて、Faultタグが存在する場合に生じます。
        """
        send_xml = "<?xml version='1.0' encoding='utf-8' ?>"\
                   "<SOAP-ENV:Envelope xmlns:SOAP-ENV='http://schemas.xmlsoap.org/soap/envelope/'><SOAP-ENV:Body>"\
                       "<ApplyAML>" + aml + "</ApplyAML>"\
                   "</SOAP-ENV:Body></SOAP-ENV:Envelope>"
        
        response = requests.post(f'{self.baseURL}/Server/InnovatorServer.aspx', headers=self.header, data=send_xml.encode())
        if response.status_code != 200:
            raise Exception(f'HTTP Error {response.status_code}', response.text)
        result = IOMItem(response.content)
        namespace = result._aml.nsmap
        fault = result._aml.xpath('//SOAP-ENV:Fault', namespaces=namespace)
        if result.isError():
            # variable "detail" contains faultcode, faultactor and detail
            detail = (etree.tostring(child, encoding='utf-8').decode()
                      if child.tag == 'detail' else child.text
                      for child_lis in [f.getchildren() for f in fault] for child in child_lis)
            raise Exception('ApplyAMLError', *detail)
        return result


class IOMItem:
    """ARASのIOMリファレンスに似せて作られたオブジェクト。

    - ARASのIOMの名前空間を模して作られている。
    しかし、同名のメソッドの挙動が必ずしも一致するとは限らないので注意されたい。
        - 特にapply()は根本的に挙動が異なるので要注意。
    - ARASへのログイン情報はクラス変数innovatorに持たせている。
    複数アカウントを切り替えながら使いたいときには要注意
    - lxmlでのシリアライズ時の文字コードはUTF-8とする。
    - 例外処理は実装中。エラーで止まるだろうから大丈夫、ではなく怪しい処理はソースを確認してほしい。
    - 誰か詳しい人がIOM.dllを利用するなどして書き直してくれると嬉しい

    Attributes:
        innovator (:obj:`Innovator`): Innovatorアイテム。セッション情報の保持用
        nsmap (:obj:`dict`): namespace map of the XML
        tree (:obj:`lxml.etree._ElementTree`): AML tree
        node (:obj:`lxml.etree._Element`): AML node with 'Item' tag.
        When nodeList is not None, this attribute should be None.
        nodeList (:obj:`list[node]`): list of AML nodes with 'Item' tag.
        When node is not None, this attribute should be None.
    """

    innovator = None

    def __init__(self, AML: str | bytes, innovator: 'Innovator'=None) -> None:
        if innovator is not None:
            IOMItem.innovator = innovator
        if type(AML) == str:
            AML = AML.encode()
        root = etree.fromstring(AML)
        self.nsmap = root.nsmap
        self.node = None
        self.nodeList = None
        if root.tag == 'AML':
            self._aml = root
            self.tree = root.getroottree()
            children = self._aml.getchildren()
            if len(children) == 1:
                self.node = children[0]
            elif len(children) > 1:
                self.nodeList = children
        elif root.tag == 'Item':
            self._aml = etree.Element('AML')
            self._aml.append(root)
            self.tree = self._aml.getroottree()
            self.node = root
        else:
            self._aml = root
            self.tree = root.getroottree()
            item_list = root.xpath('//Item', namespaces=self.nsmap)

            # 最上位のItemタグを検索
            count = None
            top_items = []
            for item in item_list:
                temp = item.getparent()
                _count = 0
                while(temp is not None):
                    _count += 1
                    temp = temp.getparent()
                if count is None:
                    count = _count
                    top_items = [item]
                elif _count == count:
                    count = _count
                    top_items.append(item)
                elif _count < count:
                    count = _count
                    top_items = [item]
            if len(top_items) == 1:
                self.node = top_items[0]
            elif len(top_items) > 1:
                self.nodeList = top_items

    @classmethod
    def newItem(cls, tbl: str, act: str='get', innovator=None) -> 'IOMItem':
        """指定したアイテムタイプのAMLを作成する。
        引数の情報を元にAMLを作成し、IOMItemを初期化する。
        ARASサーバーアクションのデフォルトはgetとする。
        誤って指定した場合もサーバーへの破壊的影響がないため。

        Args:
            tbl (str): ARAS ItemType
            act (str): ARAS Sever action
            innovator (:obj:`Innovator`): Innovatorアイテム。
            セッション情報確保用。
        """
        item = etree.Element('Item', type=tbl, action=act)
        return cls(etree.tostring(item, encoding='utf-8'), innovator)


    def __deepcopy__(self, memo=None):
        copied = copy(self)
        copied.tree = deepcopy(self.tree)
        xp = self.getXPath()
        if self.isCollection():
            copied.node = None
            copied.nodeList = [copied.tree.xpath(x, namespaces=self.nsmap)[0] for x in xp]
            copied._aml = copied.tree.getroot()
        elif self.node is not None:
            copied.node = copied.tree.xpath(xp, namespaces=self.nsmap)[0]
            copied.nodeList = None
            copied._aml = copied.tree.getroot()
        else:
            copied.node = None
            copied.nodeList = None
            copied._aml = copied.tree.getroot()
        return copied


    def apply(self) -> 'IOMItem':
        """AMLをサーバに渡して実行する。
        オリジナルのIOMItem.apply()と仕様が異なるので注意!!

        - 最上位タグがAMLの場合はそのままデコードして実行する。
        - 最上位タグがItemの場合はAMLタグでラッピングして実行する。
        - XML内部にAMLタグが存在する場合は、そのノードを一つにまとめて実行する。
        - それ以外の場合はnode属性をAMLタグでラッピングして実行する。
        """
        return IOMItem.innovator.applyAML(self.toAML())


    def setAttribute(self, attrib: str, value):
        if self.isCollection():
            raise Exception("The instance doesn't represent a single item.")
        self.node.set(attrib, value)


    def setID(self, value: str):
        if self.isCollection():
            raise Exception("The instance doesn't represent a single item.")
        self.node.set('id', value)


    def setAction(self, act: str):
        if self.isCollection():
            raise Exception("The instance doesn't represent a single item.")
        self.node.set('action', act)


    def setProperty(self, propertyName: str, value):
        if self.isCollection():
            raise Exception("The instance doesn't represent a single item.")
        props = self.node.xpath(propertyName)
        if len(props) == 0:
            prop = etree.SubElement(self.node, propertyName)
        elif len(props) == 1:
            prop = props[0]
        else:
            raise Exception('More than one property found')
        if type(value) in [int, float]:
            value = str(value)
        prop.text = value


    def setPropertyAttribute(self, propertyName: str, attributeName: str, value):
        if self.isCollection():
            raise Exception("The instance doesn't represent a single item.")
        props = self.node.xpath(propertyName)
        if len(props) == 0:
            prop = etree.SubElement(self.node, propertyName)
        elif len(props) == 1:
            prop = props[0]
        else:
            raise Exception('More than one property found')
        prop.set(attributeName, value)


    def setPropertyCondition(self, propertyName, condition):
        self.setPropertyAttribute(propertyName, 'condition', condition)


    def createRelationship(self, relationshipTypeName: str, action):
        if self.isCollection():
            raise Exception("The instance doesn't represent a single item.")
        relationship = etree.SubElement(self.node, 'Relationships')
        etree.SubElement(relationship, 'Item', type=relationshipTypeName, action=action)

    def setRelationships(self, relationshipTypeName):
        self.createRelationship(relationshipTypeName, action=self.getAction())


    def appendItem(self, item: 'IOMItem') -> 'IOMItem':
        if item.isCollection():
            raise ValueError("The argumet instance doesn't represent a single item.")
        if self.isCollection():
            nd = self.nodeList[-1]
        elif self.node is not None:
            nd = self.node
        else:
            raise Exception("The instance doesn't have any node.")
        nd.addnext(item.node)
        add_node = nd.getnext()
        if self.isCollection():
            self.nodeList.append(add_node)
        elif self.node is not None:
            self.nodeList = [self.node, add_node]
        self.node = None
        return self


    def appendNewItem(self, tbl: str, act=None) -> 'IOMItem':
        if act is None:
            act = self.action
        if self.isCollection():
            parent = self.nodeList[0].getparent()
        else:
            parent = self.node.getparent()
        etree.SubElement(parent, 'Item', type=tbl, action=act)
        self.nodeList = parent.findall('Item')
        self.node = None
        return self


    def isCollection(self):
        if self.node is None and self.nodeList is not None:
            return True
        else:
            return False


    def isError(self):
        fault = self._aml.xpath('//SOAP-ENV:Fault', namespaces=self.nsmap)
        return len(fault) > 0


    def getAttribute(self, attrib: str) -> str:
        if self.isCollection():
            raise Exception("The instance doesn't represent a single item.")
        return self.node.get(attrib)


    def getItemType(self) -> str:
        if self.isCollection():
            raise Exception("The instance doesn't represent a single item.")
        return self.node.get('type')


    def getAction(self) -> str:
        if self.isCollection():
            raise Exception("The instance doesn't represent a single item.")
        return self.node.get('action')


    def getID(self) -> str:
        if self.isCollection():
            raise Exception("The instance doesn't represent a single item.")
        return self.node.get('id')


    def getId(self) -> str:
        return self.getID(self)


    def getProperty(self, propertyName: str) -> (str|None):
        if self.isCollection():
            raise Exception("The instance doesn't represent a single item.")
        prop = self.node.find(propertyName)
        return None if prop is None else prop.text


    def getPropertyAttribute(self, propertyName: str, attributeName: str) -> (str|None):
        if self.isCollection():
            raise Exception("The instance doesn't represent a single item.")
        prop = self.node.find(propertyName)
        return None if prop is None else prop.get(attributeName)


    def getRelationships(self, relationshipTypeName: str=None):
        if self.isCollection():
            raise Exception("The instance doesn't represent a single item.")
        ret = copy(self)
        # ret.tree = deepcopy(self.tree)
        relations = ret.node.xpath('./Relationships/Item', namespaces=self.nsmap)
        node_list = []
        for rel in relations:
            if relationshipTypeName is None:
                node_list.append(rel)
            elif rel.get("type") == relationshipTypeName:
                node_list.append(rel)
        ret.nodeList = node_list
        ret.node = None
        return ret


    def getRelatedItem(self):
        if self.isCollection():
            raise Exception("The instance doesn't represent a single item.")
        ret = copy(self)
        # ret.tree = deepcopy(self.tree)
        # related = ret.tree.xpath(self.getXPath()+'/related_id/Item', namespaces=self.nsmap)
        related = ret.node.xpath('./related_id/Item', namespaces=self.nsmap)
        if bool(related):
            ret.node = related[0]
            ret.nodeList = None
            return ret
        else: return None


    def getParentItem(self):
        if self.isCollection():
            raise Exception("The instanse doesn't represent a single item.")
        # 親がItemタグかrootノードになるまで再帰的に親をチェック
        def _getparentitem(node):
            parent = node.getparent()
            if parent is None:
                return None
            elif parent.tag == 'Item':
                return parent
            else:
                return _getparentitem(parent)
        parent_item = _getparentitem(self.node)
        if parent_item is None:
            return None
        else:
            ret = copy(self)
            ret.node = parent_item
            return ret


    def getItemsByXPath(self, xpath: str) -> 'IOMItem':
        ret = copy(self)
        if xpath.startswith('/'):
            node_list = [
                nd for nd
                in self.tree.xpath(xpath, namespaces=self.nsmap)
                if nd.tag=='Item'
            ]
        else:
            if self.isCollection():
                node_list = []
                for nd in self.nodeList:
                    node_list += [
                        n for n
                        in nd.xpath(xpath, namespaces=self.nsmap)
                        if n.tag == 'Item'
                    ]
            else:
                node_list = [
                    nd for nd
                    in ret.node.xpath(xpath, namespaces=self.nsmap)
                    if nd.tag == 'Item'
                ]

        if len(node_list) == 0:
            ret.node = None
            ret.nodeList = None
        elif len(node_list) == 1:
            ret.node = node_list[0]
            ret.nodeList = None
        else:
            ret.node = None
            ret.nodeList = node_list
        return ret


    def getItemByIndex(self, index: int):
        """nodeList内のnodeで、Indexで指定されたアイテムをnodeに持つIOMItemを返す。

        元のオブジェクトのtreeをdeepcopyし、nodeとnodeListを再定義するという挙動をするため、
        重めの処理となっていた……が浅いコピーに変更した。
        nodeList内の要素を順に取り出したいときは getItemIter()を使うこと。
        """
        if not self.isCollection():
            raise Exception("The instance does not represent a collection of items.")
        ret = copy(self)
        # ret.tree = deepcopy(self.tree)
        # xp = self.tree.getpath(self.nodeList[index])
        # elems = ret.tree.xpath(xp, namespaces=self.nsmap)
        # if len(elems) == 0:
        #     raise Exception("The node of the index was not found")
        # ret.node = elems[0]
        ret.node = ret.nodeList[index]
        ret.nodeList = None
        return ret


    def getXPath(self):
        """treeのルートからnodeまたはnodeList内各nodeまでのXPathを取得

        変更:
            元は愚直に親ノードのタグを再帰的に取得していたが、
            ElementTreeのgetpathメソッドを用いるように変更。
            treeとnodeの関連が途切れると使用不能になるので注意
        """
        def get_xpath(node):
            if node.getparent() is not None:
                parent_path = get_xpath(node.getparent())
                return f"{parent_path}/{node.tag}"
            return f"/{node.tag}"

        # if self.isCollection():
        #     return [get_xpath(node) for node in self.nodeList]
        # elif self.node is not None:
        #     return get_xpath(self.node)
        # else:
        #     return None

        if self.isCollection():
            return [self.tree.getpath(nd) for nd in self.nodeList]
        elif self.node is not None:
            return self.tree.getpath(self.node)
        else:
            return None


    def getItemCount(self):
        if self.isCollection():
            return len(self.nodeList)
        else:
            return 0 if self.node is None else 1


    def getItemIter(self):
        """nodeList内の各ノードをnodeに持つIOMItemのジェネレータを作成する。

        treeもnodeも浅いコピーとなっているのに注意
        """
        if not self.isCollection():
            raise Exception("The instance does not represent a collection of items.")
        for nd in self.nodeList:
            temp = copy(self)
            temp.nodeList = None
            temp.node = nd
            yield temp


    def removeAttribute(self, attributeName: str):
        if self.isCollection():
            raise Exception("The instance doesn't represent a single item.")
        self.node.attrib.pop(attributeName, None)


    def removeProperty(self, propertyName: str):
        if self.isCollection():
            raise Exception("The instance doesn't represent a single item.")
        props = self.node.findall(propertyName)
        if len(props) == 0:
            return
        else:
            for prop in props:
                self.node.remove(prop)


    def removePropertyAttribute(self, propertyName: str, attributeName: str):
        if self.isCollection():
            raise Exception("The instance doesn't represent a single item.")
        props = self.node.findall(propertyName)
        if len(props) == 0:
            return
        else:
            for prop in props:
                prop.attrib.pop(attributeName, None)


    def _removeRelationships(self, relationshipTypeName: str=None):
        """!!! 動作未確認 !!!"""
        if self.isCollection():
            raise Exception("The instance doesn't represent a single item.")
        relationships = self.node.xpath('Relationships')
        if relationshipTypeName is None:
            for rel in relationships:
                self.node.remove(rel)
        else:
            for rel in relationships:
                _items = rel.xpath(relationshipTypeName)
                for _i in _items:
                    rel.remove(_i)


    def toString(self, pretty_print=False) -> str:
        """xml treeを文字列に変換する。
        フォーカス中のノードではなく、ツリー全体の文字列表現が返る。

        Args:
            pretty_print (bool): タグごとに改行・インデントを付ける。
            デバッグ・ファイル出力時におススメ。defaultはFalse.
        """
        return etree.tostring(self.tree, encoding='utf-8', pretty_print=pretty_print).decode()


    def toAML(self) -> str:
        """apply() にて Innovator.applyAML() に渡されるAMLを返す。"""
        root = self.tree.getroot()
        _amls = root.xpath('//AML')
        if root.tag == 'AML':
            aml_text = self.toString()
        elif root.tag == 'Item':
            aml_text = '<AML>' + self.toString() + '</AML>'
        elif len(_amls) == 1:
            aml_text = etree.tostring(_amls[0], encoding='utf-8').decode()
        elif len(_amls) > 1:
            # _aml = deepcopy(_amls[0])
            _aml = _amls[:1]
            for _a in _amls[1:]:
                for _c in _a.getchildren():
                    _aml.append(_c)
            aml_text = etree.tostring(_aml, encoding='utf-8').decode()
        elif self.isCollection():
            aml = etree.Element('AML')
            for node in self.nodeList:
                aml.append(copy(node))
            aml_text = etree.tostring(aml, encoding='utf-8').decode()
        else:
            aml = etree.Element('AML')
            aml.append(copy(self.node))
            aml_text = etree.tostring(aml, encoding='utf-8').decode()
        return aml_text


    def toDict(self) -> list[dict]:
        """nodeまたはnodeListをdictのlistに変換する。

        各attributeと子ノードのテキストを辞書に格納している。
        子ノードにさらに子ノード（＝孫ノード）が存在する場合は、子ノードのテキストの代わりに、
        孫ノードを辞書のリスト化したものを格納している。
        ただし、<Relationships>タグを除き、要素数が1になる場合は辞書をリスト化せず辞書のまま格納する。
        """
        if self.isCollection():
            item_list = self.nodeList
        else:
            item_list = [self.node]

        def _nodelist2dict(nodelist):
            ret = []
            for node in nodelist:
                _dict = copy(node.attrib)
                for c in node.getchildren():
                    gchildren = c.getchildren()
                    if len(gchildren) == 0:
                        _dict[c.tag] = c.text
                    elif c.tag == 'Relationships':
                        item_types = dict()
                        for gchild in gchildren:
                            relationship_type = gchild.get("type")
                            if relationship_type not in item_types.keys():
                                item_types[relationship_type] = [gchild]
                            else:
                                item_types[relationship_type].append(gchild)
                        for k, l in item_types.items():
                            _dict[k] = _nodelist2dict(l)
                    elif len(gchildren) > 1:
                        _dict[c.tag] = _nodelist2dict(gchildren)
                    else:
                        _dict[c.tag] = _nodelist2dict(gchildren)[0]
                ret.append(_dict)
            return ret

        return _nodelist2dict(item_list)


if __name__ == '__main__':
    import lxml
    ArasUrl = "http://internal-awcp0018-alb00105-616219119.ap-northeast-1.elb.amazonaws.com/NPM_innovator"
    ArasDB = "NPM_Innovator"
    username = 'N911267'
    aras = Innovator(ArasUrl, ArasDB, username, username)
    item = aras.newIOMItem('z_sm_Simulation', 'get')
    item.setProperty('z_name','test20240328')
    # item.setPropertyAttribute('z_name', 'condition', 'like')
    item.setRelationships('z_sm_r_Simu_Model')
    sim_list = item.apply()
    # if sim_list.isCollection():
    #     for i, node in enumerate(sim_list.nodeList):
    #         name_ = node.find('z_name')
    #         if name_ is not None:
    #             print(i, name_.text)
    #     index = input('input :')
    #     sim_list = sim_list[int(index)]

    # print(sim_list.toString(pretty_print=True))
    sim_name = sim_list.node.find('z_name')
    print(sim_list.getID(),sim_name.text)
    sim_Model = sim_list.getRelationships('z_sm_r_Simu_Model')
    model1 = sim_Model.getItemByIndex(0)
    model1_name = model1.node.xpath('related_id/Item/z_model_name')[0].text
    model1.removeProperty("related_id")
    print()
    print('relationships id: ' + model1.getID())
    print(etree.tostring(model1.node, encoding='utf-8', pretty_print=True).decode())
    model1.setAttribute('action', 'delete')
    response = model1.apply()
    print(response.toString(pretty_print=True))

