
import requests


class Server:

    def __init__(self, url, testurl="/ping"):
        self.url = url
        self.testurl = self.url.rstrip("/") +testurl

    def test_server(self) -> bool :
        result = requests.get(self.testurl, timeout=2.50)

        if result.status_code != 200:
            raise Exception(f"Server {self.url} not responding")
        
        return True

    def getUrl(self):
        return self.url




