class SeparateServer:
    def __init__(self, server, dbserver):

        # print(f"Separate({server}, {dbserver})")
        self.server = server
        self.dbserver = dbserver

        # line bellow to comment when offline
        # self.isServersRunning()

    def isServersRunning(self):
        self.server.test_server()
        self.dbserver.test_server()
