
from fastapi import FastAPI, HTTPException

def testBearer(db,bearer):
    if (bearer == None or db == None): 
        print("markTaskWithRunningStatus: bearer or db is None")
        print("bearer: ", bearer)
        print("db: ", db)
        raise HTTPException(status_code=404, detail="Bearer or db is None")

