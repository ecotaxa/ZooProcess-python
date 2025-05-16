from src.DB import DB
import requests

class TaskStatus:
    def __init__(self, taskId:str, db:DB ):
        self.taskId = taskId
        self.db = db
        self.url = self.db.makeUrl(f"task/{self.taskId}")

    def sendRunning(self, message:str="running") -> requests.Response:
        # print("sendRunning Status")
        
        body = {
            "status": "RUNNING",
            "log": message
        }

        # print("url:", self.url)
        print("body:", body)
        # print("headers:", self.db.getHeader())

        response = requests.post(self.url, json=body, headers=self.db.getHeader())
        # print("response: ", response)
        # print("response: ", response.status_code)
        return response

    def sendError(self, message:str="error") -> requests.Response:
        # print("sendError Status")
        body = {
            "status": "FAILED",
            "log": message
        }

        response = requests.post(self.url, json=body, headers=self.db.getHeader())
        # print("response: ", response)
        # print("response: ", response.status_code)
        return response

    def sendDone(self, message:str="done") -> requests.Response:
        # print("sendDone Status")
        body = {
            "status": "FINISHED",
            "log": message
        }
        response = requests.post(self.url, json=body, headers=self.db.getHeader())
        # print("response: ", response)
        # print("response: ", response.status_code)
        return response

    def sendImage(self, path:str, type:str) -> requests.Response:        
        # print("sendImageProcessed")
        url = self.db.makeUrl(f"scan/{self.taskId}?nomove&taskid")
        print("url: ", url)
        body = {
            "type": type,
            "scan": path
        }
        response = requests.post(url, json=body, headers=self.db.getHeader())
        # print("response: ", response)
        # print("response: ", response.status_code)
        return response
    

