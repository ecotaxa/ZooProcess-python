
import requests
from tests import BaseTest

# from src import config
# import src.config
from src.config import config


class DB(BaseTest):
    """
    A class to interact with a database using HTTP requests.

    Attributes:
        bearer (str): The bearer token for authorization.
        db (str): The base URL of the database.

    Methods:
        getHeader(type: str): Constructs the HTTP headers for requests.
        makeUrl(path: str): Constructs the full URL for a given path.
        get(url: str): Sends a GET request to the specified URL.
        post(url: str, body: dict): Sends a POST request with a JSON body.
        put(url: str, body: dict): Sends a PUT request with a JSON body.
        patch(url: str, body: dict): Sends a PATCH request with a JSON body.
    """    
    def __init__(self,bearer:str, db:str = config.db):
        if not bearer:
            raise ValueError("Bearer token is required")
        self.bearer = bearer
        self.db = db.rstrip('/')


    def getHeader(self, type:str = "application/json"):
        """Constructs the HTTP headers for requests."""
        return {
            "Authorization": f"Bearer {self.bearer}",
            "Content-Type": type
        }
    
    def makeUrl(self, path:str = "/"):
        """Constructs the full URL for a given path."""
        return f"{self.db}{path}"
    def get(self, url:str):
        """Sends a GET request to the specified URL."""
        response = requests.get(self.makeUrl(url), headers=self.getHeader())
        return response.json()
    
    def post(self, url:str, body:dict):
        """Sends a POST request with a JSON body."""
        response = requests.post(self.makeUrl(url), json=body, headers=self.getHeader())
        return response.json()
    
    def put(self, url:str, body:dict):
        """Sends a PUT request with a JSON body."""
        response = requests.put(self.makeUrl(url), json=body, headers=self.getHeader())
        return response.json()
    
    def patch(self, url:str, body:dict):
        """"Sends a PATCH request with a JSON body."""
        response = requests.patch(self.makeUrl(url), json=body, headers=self.getHeader())
        return response.json()


