# Standard library import
from unittest import TestCase

# Package import
from phantomcli.network import PhantomSocket
from phantomcli.network import PhantomMockServer


class PhantomSocketTestCase(TestCase):

    GOOGLE_IP = '8.8.8.8'
    LOCALHOST_IP = '127.0.0.1'


class TestPhantomSocketBasic(TestCase):

    GOOGLE_IP = '8.8.8.8'
    LOCALHOST_IP = '127.0.0.1'

    @classmethod
    def setUpClass(cls):
        # Starting a mock server
        cls.mock_server = PhantomMockServer()
        cls.mock_server.start()

    @classmethod
    def tearDownClass(cls):
        cls.mock_server.stop()

    def test_true_is_true(self):
        self.assertTrue(True)

    def test_ping_working_to_localhost(self):
        # Setting up a phantom socket, that points to the localhost and executing a ping. This ensures that the ping
        # command is generally working, because localhost should be addressable no matter what the network config
        phantom_socket = PhantomSocket(self.LOCALHOST_IP)
        is_pingable = phantom_socket.ping()
        self.assertTrue(is_pingable)

    def test_ping_working_to_google_network_connection(self):
        # Setting to google server (because we can assume, that it is always up) This will test the connection to the
        # internet
        phantom_socket = PhantomSocket(self.GOOGLE_IP)
        is_pingable = phantom_socket.ping()
        self.assertTrue(is_pingable)

    def test_connect_to_mock_server(self):
        phantom_socket = PhantomSocket(self.LOCALHOST_IP)
        try:
            phantom_socket.connect()
            self.assertTrue(True)
            phantom_socket.disconnect()
        except ModuleNotFoundError:
            self.assertEqual('', 'PhantomSocket could not connect to the mock server!')

    def test_exception_when_attempting_to_connect_without_socket(self):
        # Attempting to connect to google, because google most likely doesnt have a listening socket on port 7115,
        # which should cause the exception
        phantom_socket = PhantomSocket(self.GOOGLE_IP)
        self.assertRaises(ModuleNotFoundError, phantom_socket.connect)
        phantom_socket.disconnect()
