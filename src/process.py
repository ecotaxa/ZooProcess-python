

#from .SeparateServer import SeparateServer
import requests




class Separate:

    def __init__(self,scanId, bearer, server) -> None:
        self.scanId = scanId
        self.bearer = bearer
        self.dbserver = server.dbserver.getUrl()





    def getFolder(self):

        data = {
            "scanId": self.scanId
        }

        headers = {
            'Authorization': self.bearer,
        }

        response = requests.post(
            url=self.dbserver + "",
            data=data,
            headers=headers,
            timeout=30
        )


    def separate(self):
        pass
        




