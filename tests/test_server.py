import unittest

from providers.server import Server
from config_rdr import config


class Test_server(unittest.TestCase):

    @unittest.skip("")
    def test_Niko_server(self):

        server = Server("http://niko.obs-vlfr.fr:5000")
        online = server.test_server()

        self.assertTrue(online)

    @unittest.skip("")
    def test_Seb_server(self):

        server = Server("http://seb:5000")
        online = server.test_server()

        self.assertTrue(online)

    @unittest.skip("")
    def test_Localhost_server(self):
        server = Server("http://localhost:5001")
        self.assertRaises(Exception, server.test_server)

    @unittest.skip("")
    def test_dbserver(self):

        server = Server("http://zooprocess.imev-mer.fr:8081/v1/ping")

        self.assertTrue(server.test_server())

    def test_dbserver_withconfig(self):
        # print(config.dbserver)
        server = Server(config.dbserver)
        self.assertTrue(server.test_server())
