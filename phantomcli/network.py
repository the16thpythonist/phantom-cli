# standard library imports
import socket
import logging
import subprocess
import threading

# third party libraries


# Setting up the logger to be used by this module
logger = logging.getLogger(__name__)


class PhantomSocket:
    """
    Objects of this class handle the control connection to a phantom camera.

    CHANGELOG

    Added 20.02.2019
    """

    DEFAULT_PORT = 7115

    DUMMY_COMMAND = b'get info.name'

    def __init__(self, ip, timeout=10):
        """
        Constructor.

        CHANGELOG

        Added 20.02.2019

        :param ip:
        """
        # Creating the logger, whose name combines the module, in which this class is based as well as the name of the
        # class
        self.log_name = '{}.{}'.format(__name__, self.__class__.__name__)
        self.logger = logging.getLogger(self.log_name)

        # At the moment there is no need for being able to pass a custom port, because the phantom always runs on the
        # same port (given by DEFAULT_PORT) anyways.
        self.port = self.DEFAULT_PORT
        self.ip = ip
        self.logger.debug('Created a new PhantomSocket object to IP %s on PORT %s', self.ip, self.port)

        # Creating the socket object to be used to connect to the phantom
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(timeout)

    def connect(self):
        """
        Actually calls the connect method on the socket.

        CHANGELOG

        Added 20.02.2019

        :return:
        """
        try:
            destination = self.get_host_tuple()
            self.socket.connect(destination)
            self.logger.info('Connected to Phantom at %s on port %s', self.ip, self.port)
        except socket.timeout:
            self.logger.error('Connecting to Phantom at %s failed!', self.ip)
            raise ModuleNotFoundError('There is no socket at {}!'.format(self.ip))

    def get_host_tuple(self):
        """
        Returns a tuple, whose first element is the string IP address to connect to and the second being the int PORT.
        This is exactly the kind of tuple, that has to be passed to the socket constructor.

        CHANGELOG

        Added 20.02.2019

        :return: Tuple(str, int)
        """
        return self.ip, self.port

    def send(self, message):
        """

        :param message:
        :return:
        """
        result = self.socket.sendall(message)
        self.logger.debug('Sending "%s" to %s with result %s', message, self.ip, result)

    def close(self):
        """
        Safely closes the socket, which is connected to the phantom

        CHANGELOG

        Added 20.02.2019

        :return:
        """
        self.socket.close()

    def ping(self):
        """
        This method will ping the phantom camera with a single package and return true, if there was a response and
        false if there was a timeout

        CHANGELOG

        Added 20.02.2019

        :return: bool
        """
        # TODO: Maybe make it support windows as well
        # I have actually tried using the pythonping package here, but it just didnt work. It would always hang itself
        # when the destination was unreachable, the function call remained blocking and never issued a timeout.
        command = 'ping -c 1 {}'.format(self.ip)
        response = subprocess.call(command, shell=True, stdout=subprocess.DEVNULL)
        self.logger.debug('Pinged %s and received response "%s"', self.ip, response)
        return response == 0


# TODO: Use socket server here.
class PhantomMockServer(threading.Thread):
    """
    This wraps the socket functionality for simulating a phantom operating on the IP "127.0.0.1" (localhost) and the
    port 7115 (default phantom control port)

    CHANGELOG

    Added 20.02.2019
    """

    IP = '127.0.0.1'
    PORT = 7115

    def __init__(self):
        threading.Thread.__init__(self)

        self.log_name = '{}.{}'.format(__name__, self.__class__.__name__)
        self.logger = logging.getLogger(self.log_name)

        self.port = self.PORT
        self.ip = self.IP

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.ip, self.port))
        logger.debug('Created a new PhantomMockServer object bound to IP %s and PORT %s', self.ip, self.port)

    def run(self):
        """
        Starts the mock server

        CHANGELOG

        Added 20.02.2019
        :return:
        """
        # Creating a new socket that accepts incoming connections
        self.socket.listen(10)
        connection, address = self.socket.accept()
        with connection:
            logger.debug('MockServer connected to %s', address)
            while True:
                data = connection.recv(1024)
                # logger.debug('MockServer received data %s', data)
                if data:
                    logger.debug('Received data "%s"', data)
        self.socket.close()
