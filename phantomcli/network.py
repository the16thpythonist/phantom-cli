# standard library imports
import socket
import logging
import subprocess
import threading
import socketserver

# third party libraries

# package imports
from phantomcli.phantom import PhantomCamera

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

    GET_RESPONSE_TERMINATION = '\r\n'

    GET_RESPONSE_SEPARATOR = r'\r\n'

    def __init__(self, ip, timeout=10, camera_class=PhantomCamera):
        """
        Constructor.

        CHANGELOG

        Added 20.02.2019

        Changed 21.02.2019
        THe timeout is now saved as an attribute.
        Moved the socket creation code to a separate method and not calling it inside the constructor anymore.
        Rather in the connect method.

        :param ip:
        """
        # Creating the logger, whose name combines the module, in which this class is based as well as the name of the
        # class
        self.log_name = '{}.{}'.format(__name__, self.__class__.__name__)
        self.logger = logging.getLogger(self.log_name)

        # The actual camera class to be referred to with using this socket is being passed as a parameter
        self.camera_class = camera_class

        # At the moment there is no need for being able to pass a custom port, because the phantom always runs on the
        # same port (given by DEFAULT_PORT) anyways.
        self.port = self.DEFAULT_PORT
        self.ip = ip

        # 21.02.2019
        # Saving the timeout to it can be accessed when creating a new socket in the connect method
        self.timeout = timeout
        self.logger.debug('Created a new PhantomSocket object to IP %s on PORT %s', self.ip, self.port)

        self.socket = None

    # #########################
    # GET OPERATIONS ON PHANTOM
    # #########################

    def get_all(self):
        """
        Executes a get call for ALL possible properties of the phantom camera. The list of all the available properties
        to issue a get command for is taken from the class stored in "camera_class". Returns a list of response lists.
        These response lists contain the string lines of the response.

        CHANGELOG

        Added 21.02.2019

        :return:
        """
        phantom_structures = self.camera_class.all_properties()
        responses = []
        for structure_name in phantom_structures:
            response = self.get(structure_name)
            responses.append(response)
        return responses

    def get(self, structure_name):
        """
        Issues a "get" call for the given structure/variable name

        Return

        :param structure_name:
        :return:
        """
        # Creating the command string according to the syntax and then sending it to the camera. The encoding is handled
        # by the "send" method
        command_string = 'get {}'.format(structure_name)
        self.send(command_string)
        self.logger.debug('Sent command "%s" to the phantom', command_string)

        # Receiving the response from the camera. The response will be given as a list of strings. some commands may
        # return multiple lines of data, but most just a single line -> list with one string element
        response_list = self.receive_get_response()
        return response_list

    def receive_get_response(self):
        """
        Receives the response following a "get" request to the camera and returns a list with the string lines of the
        response

        So as far as I have understood the protocol, every response is terminated by an unescaped newline character
        (\r\n), which means an "actual" new line. But there are some responses, that send out multiple lines of data
        and each of these lines is terminated by an escaped character.
        This means to receive a proper response, we will just simply receive all data until there is an actual new line
        and sort out the individual lines in the end.

        But the possibilities of there being multiple lines means we will have to return a list anyways even if it is
        just a single line.

        CHANGELOG

        Added 21.02.2019

        :return:
        """
        response_string = self.receive_until(self.GET_RESPONSE_TERMINATION)
        response_list = self.get_response_list(response_string)
        return response_list

    def get_response_list(self, response_string):
        """
        Given the string of a "get" response from the camera, this will split the string according to the
        GET_RESPONSE_SEPARATOR and return the list of lines.

        CHANGELOG

        Added 21.02.2019

        :param response_string:
        :return:
        """
        if self.GET_RESPONSE_SEPARATOR in response_string:
            return response_string.split(self.GET_RESPONSE_SEPARATOR)
        else:
            return [response_string]

    # ####################################
    # BASIC NETWORK / SOCKET FUNCTIONALITY
    # ####################################

    def connect(self):
        """
        Actually calls the connect method on the socket.

        CHANGELOG

        Added 20.02.2019

        Changed 21.02.2019
        Calling the "create_socket" method to make a fresh socket for every new connection.

        :return:
        """
        try:
            # 21.02.2019
            # Creating a fresh socket for every new connection
            self.create_socket()

            destination = self.get_host_tuple()
            self.socket.connect(destination)
            self.logger.info('Connected to Phantom at %s on port %s', self.ip, self.port)
        except socket.timeout:
            self.logger.error('Connecting to Phantom at %s failed!', self.ip)
            raise ModuleNotFoundError('There is no socket at {}!'.format(self.ip))

    def disconnect(self):
        """
        Simply closes the socket connection

        CHANGELOG

        Added 21.02.2019

        :return:
        """
        self.close()
        self.logger.debug('Disconnected from phantom')

    def create_socket(self):
        """
        This method creates a new tcp socket and assigns it to the "socket" attribute of the object

        CHANGELOG

        Added 21.02.2019

        :return: void
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(self.timeout)

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
        Sends the given message to the camera over the socket.

        CHANGELOG

        Added 20.02.2019

        :param message:
        :return:
        """
        # TODO: MAYBE WE NEED TO ADD AN ESCAPE CHARACTER HERE AT THE END NEWLINE
        result = self.socket.sendall(message.encode('utf-8'))
        self.logger.debug('Sending "%s" to %s with result %s', message, self.ip, result)

    def receive_until(self, substring, buffer_size=1028):
        """
        Receives as many bytes from the socket until the given substring appeared in the byte stream
        Returns the decoded string, without the substring

        CHANGELOG

        Added 21.02.2019

        :param substring:
        :param buffer_size:
        :return:
        """
        receiving = True
        buffer = ''
        while receiving:
            data = self.socket.recv(buffer_size)
            data_decoded = data.decode('utf-8')
            buffer += data_decoded

            if substring in buffer:
                receiving = False

        return buffer.replace(substring, '')

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
        # I have actually tried using the "pythonping" package here, but it just didnt work. It would always hang itself
        # when the destination was unreachable, the function call remained blocking and never issued a timeout.
        command = 'ping -c 1 {}'.format(self.ip)
        response = subprocess.call(command, shell=True, stdout=subprocess.DEVNULL)
        self.logger.debug('Pinged %s and received response "%s"', self.ip, response)
        return response == 0


# #########################
# MOCK SERVER FUNCTIONALITY
# #########################


class PhantomMockControlInterface(socketserver.BaseRequestHandler):
    """
    The Handler for the MockServer.
    For every incoming connection to the mock server a handler object is instantiated. Since a phantom camera manages
    only one single ongoing socket connection, there will only be one object of this class managing THE connection.

    CHANGELOG

    Added 21.02.2019
    """

    def handle(self):
        """
        This method gets called by the socket server for each incoming connection.
        In here all the magic needs to happen. All the incoming commands to the phantom need to be handled here.

        CHANGELOG

        Added 21.02.2019

        :return: void
        """
        self.server.logger.info(
            'New connection IP %s PORT %s connected to phantom Mock!',
            self.client_address[0],
            self.client_address[1]
        )

        # The connection with the phantom camera is based on one ongoing socket connection. That is why we are using a
        # infinite while loop here
        while True:
            data = self.request.recv(1024).strip()
            request = data.decode('utf-8')
            if request and request[0] == '':
                continue
            if len(request) == 0:
                continue

            self.server.logger.debug('Incoming request "%s"', request)
            request_split = request.split(' ')
            command = request_split[0]
            data = request_split[1:]

            # Dynamically choosing the right sub handle method of this class based on the given command type and then
            # executing that method with the rest of the data passed to the function
            handle = getattr(self, 'handle_{}'.format(command))
            handle(data)

    # ###################################
    # THE COMMAND SPECIFIC HANDLE METHODS
    # ###################################

    def handle_get(self, data):
        """
        All get requests are diverted into this method with "data" being a list with a single string element, which is
        the name of the expected structure.
        The expected value is being fetched from the camera object and a response is sent.

        CHANGELOG

        Added 21.02.2019

        :param data:
        :return:
        """
        # Actually getting the value from the phantom object
        structure_name = data[0]
        self.server.logger.debug('GET %s', structure_name)
        structure_value = self.server.camera.get(structure_name)

        # Sending the response
        response_list = self.create_response_list(structure_value)
        self.send_get_response(response_list)

    # #############################
    # ADDITIONAL NETWORK OPERATIONS
    # #############################

    def send_get_response(self, response_list):
        """
        Given a list of strings for the response, it will be sent to the client

        CHANGELOG

        Added 21.02.2019

        :param response_list:
        :return:
        """
        response_string = r'\r\n'.join(response_list)
        self.send(response_string)

    def send(self, message):
        """
        The most low level send method. In the end all data that is being send back will end up here. This method
        handles the adding of the CRLF to the end of the string (the termination character of phantom) and the encoding
        before actually sending over the topic.

        CHANGELOG

        Added 21.02.2019

        :param message:
        :return:
        """
        # Every phantom massage is terminated by a carriage return/newline
        message_encoded = '{}\r\n'.format(message).encode('utf-8')
        self.request.sendall(message_encoded)

    # ###############
    # UTILITY METHODS
    # ###############

    def create_response_list(self, structure):
        """
        Given the value of a phantom attribute (Whatever the phantom object returns for the get method. Can be anything
        like int, string or even list already) this method converts it into a list of strings (the format needed to
        send a get response)

        CHANGELOG

        Added 21.02.2019

        :param structure:
        :return:
        """
        if isinstance(structure, list):
            string_list = list(map(str, structure))
        else:
            string_list = [str(structure)]
        return string_list


class PhantomMockServer(socketserver.ThreadingTCPServer):
    """
    This wraps the socket functionality for simulating a phantom operating on the IP "127.0.0.1" (localhost) and the
    port 7115 (default phantom control port)

    CHANGELOG

    Added 20.02.2019
    """

    # The mock server always has to operate on localhost
    IP = '127.0.0.1'
    # A phantom camera control interface is always connected to the
    PORT = 7115

    def __init__(self, camera_class=PhantomCamera, handler_class=PhantomMockControlInterface):
        """
        The constructor.

        CHANGELOG

        Added 21.02.2019

        :param class camera_class:
        """
        # Creating a new logger, whose name is a combination from the module name and the class name of this very class
        self.log_name = '{}.{}'.format(__name__, self.__class__.__name__)
        self.logger = logging.getLogger(self.log_name)

        # The ip and port of the mock server are not configurable
        self.ip = self.IP
        self.port = self.PORT

        # The handler and the camera class, on which the mock behaviour is based on can be passed as arguments to ensure
        # loose coupling
        self.handler_class = handler_class
        self.camera_class = camera_class
        self.camera = self.camera_class()

        super(PhantomMockServer, self).__init__((self.ip, self.port), self.handler_class)
        self.logger.debug('Created MockServer bound to IP %s and PORT %s', self.ip, self.port)

        self.thread = threading.Thread(target=self.serve_forever)

    def start(self):
        """
        Starts a server Thread and returns Thread object

        CHANGELOG

        Added 21.02.2019

        :return:
        """
        self.thread.daemon = True
        self.thread.start()
        self.logger.debug('main thread has started')






