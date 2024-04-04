

import unittest

from src.server import Server


class Test_server(unittest.TestCase):

    def test_Niko_server(self):

        server = Server("http://niko.obs-vlfr.fr:5000")
        online = server.test_server()

        self.assertTrue(online)


    def test_Seb_server(self):

        server = Server("http://seb:5000")
        online = server.test_server()

        self.assertTrue(online)



    def test_Localhost_server(self):
        server = Server("http://localhost:5001")
        self.assertRaises(Exception, server.test_server)

    def test_dbserver(self):

        server = Server("http://zooprocess.imev-mer.fr:8081/v1/ping")

        self.assertTrue(server.test_server())



