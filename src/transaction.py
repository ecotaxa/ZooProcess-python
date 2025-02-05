# try to import with transaction
# but didn't work, i cannot keep the transaction id between the requests
# even if i kept it it the db
# i don't know if Prisma, MongoDB or me that is the problem

# def BeginTransaction(db,bearer):
#     url = f"{db}transaction/begin"
#     print("url: ", url)

#     headers = {
#         "Authorization": f"Bearer {bearer}",
#         "Content-Type": "application/json"
#     }

#     response = requests.post(url, json={},headers=headers)

#     if response.status_code == 200:
#         print("response: ", response)
#         print("response text: ", response.text)
#         # transactionId = response.text
#         transactionId = json.loads(response.text)  # This removes the extra quotes
#         return transactionId
#     else:
#         raise HTTPException(status_code=response.status_code, detail="Error Cannot create a transaction")
# def RollBackTransaction(db,bearer,transactionId):
#     url = f"{db}transaction/rollback"
#     print("url: ", url)

#     headers = {
#         "Authorization": f"Bearer {bearer}",
#         "Content-Type": "application/json",
#         "X-Transaction-Id": transactionId
#     }

#     response = requests.post(url, json={},headers=headers)

#     if response.status_code in [200,204]:
#         print("response: ", response)
#         # print("response text: ", response.text)
#         print("Transaction cancelled")
#     else:
#         raise HTTPException(status_code=response.status_code, detail="Error Cannot RollBack the transaction: " + transactionId)
# def CommitTransaction(db,bearer,transactionId):
#     url = f"{db}transaction/commit"
#     print("url: ", url)

#     headers = {
#         "Authorization": f"Bearer {bearer}",
#         "Content-Type": "application/json",
#         "X-Transaction-Id": transactionId
#     }

#     response = requests.post(url, json={},headers=headers)

#     if response.status_code in [200,204]:
#         print("response: ", response)
#         print("response text: ", response.text)
#         print("Transaction commited")
#     else:
#         raise HTTPException(status_code=response.status_code, detail="Error Cannot commit the transaction: " + transactionId)

# with transaction
# @app.post("/import")
# def import_project(project:Project):

#     print("import project", project.path )
#     print("import project", project.bearer )
#     print("import project", project.db )
#     testBearer(project.db,project.bearer)
#     # if (project.bearer == None or project.db == None): 
#     #     print("markTaskWithRunningStatus: bearer or db is None")
#     #     # print("bearer: ", bearer)
#     #     # print("db: ", db)
#     #     return HTTPException(status_code=404, detail="Bearer or db is None")
#     #     return envoie un json avec plus d'infos mais pas le status code dans le header

#     transactionId  = BeginTransaction(project.db,project.bearer)
#     print("transactionId: ", transactionId)

#     # url = f"{dbserver.getUrl()}/projects"
#     url = f"{project.db}projects"
#     print("url: ", url)

#     body = {  
#         # "project_id": "null",
#         "name": 'SebProjectFromHappy',
#         # "thematic": "null",
#         "driveId": '65bd147e3ee6f56bc8737879',
#         "instrumentId": '65c4e0e44653afb2f69b11d1',
#         "acronym": 'acronym',
#         "description": 'dyfamed',
#         "ecotaxa_project_name": 'ecotaxa project name',
#         "ecotaxa_project_title": 'ecotaxa_project_title',
#         "ecotaxa_project": 1234,
#         "scanningOptions": 'LARGE',
#         "density": '2400'
#     }
    
#     headers = {
#         "Authorization": f"Bearer {project.bearer}",
#         "Content-Type": "application/json",
#         "X-Transaction-Id": transactionId
#     }

#     print("headers: ", headers)

#     response = requests.post(url, json=body, headers=headers)


#     if response.status_code != 204:
#         print("import project response: ", response)
#         print("response text: ", response.text)
#         try :
#             # RollBackTransaction(project.db, project.bearer, transactionId)
#             raise HTTPException(status_code=response.status_code, detail="Error importing project: " + response.text)
#         except:
#             print("Error RollBackTransaction")
#             raise HTTPException(status_code=response.status_code, detail="Error importing project: " + response.text)

#     print("response: ", response)
#     print("response: ", response.status_code)
          
#     projectid = response.json().get("id")


#     addSamples(project.path, project.bearer, project.db, projectid)


#     # CommitTransaction(project.db, project.bearer, transactionId)
    
#     return response.json()




# def post_project(db,bearer,transactionId):
        
#     url = f"{db}projects"
#     print("url: ", url)
    
#     body = {  
#     # "project_id": "null",
#     "name": 'SebProjectFromHappy',
#     # "thematic": "null",
#     "driveId": '65bd147e3ee6f56bc8737879',
#     "instrumentId": '65c4e0e44653afb2f69b11d1',
#     "acronym": 'acronym',
#     "description": 'dyfamed',
#     "ecotaxa_project_name": 'ecotaxa project name',
#     "ecotaxa_project_title": 'ecotaxa_project_title',
#     "ecotaxa_project": 1234,
#     "scanningOptions": 'LARGE',
#     "density": '2400'
#     }
    
#     headers = {
#         "Authorization": f"Bearer {bearer}",
#         "Content-Type": "application/json",
#         "X-Transaction-Id": transactionId
#     }

#     print("headers: ", headers)

#     response = requests.post(url, json=body, headers=headers)
#     print("import project response: ", response)
#     print("response text: ", response.text)


# @app.post("/test_transaction")
# def test_transaction(project:Project):
#     transactionId = BeginTransaction(project.db,project.bearer)
#     print("transactionId: ", transactionId)
#     # post_project(project.db,project.bearer,transactionId)
#     CommitTransaction(project.db,project.bearer,transactionId)
#     return {"message": "Transaction committed"}
