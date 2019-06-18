# Standard library import

# Package import
from phantomcli.network import PhantomSocket
from phantomcli.network import PhantomMockServer

from phantomcli._util import MockTestCase


class TestPhantomSocket(MockTestCase):

    MOCK_SERVER_CLASS = PhantomMockServer
    PHANTOM_SOCKET_CLASS = PhantomSocket

    def test_mock_test_case_working(self):
        phantom_socket = self.get_phantom_socket()
        phantom_socket.connect()
        self.assertTrue(True)
        phantom_socket.disconnect()

    def test_ping_working_to_localhost(self):
        phantom_socket = self.get_phantom_socket()
        is_pingable = phantom_socket.ping()
        self.assertTrue(is_pingable)

    def test_change_acquisition_mode(self):
        phantom_socket = self.get_phantom_socket()
        phantom_socket.connect()

        phantom_socket.set_mode(PhantomSocket.MODE_STANDARD)
        self.wait_request()
        request = self.get_requests()[0]
        self.assertEqual(request[0], 'iload')

        phantom_socket.disconnect()

    def test_startdata_command_string(self):
        phantom_socket: PhantomSocket = self.get_phantom_socket()
        phantom_socket.connect()

        phantom_socket.start_data_server()
        phantom_socket.startdata()
        phantom_socket.img()
        self.wait_request()
        request = self.get_requests()[0]
        print(request)
        self.assertTrue(False)
