# standard library imports
import socket
import logging
import subprocess
import threading
import socketserver
import demjson
import os
import time
import re

# third party libraries

# package imports
from phantomcli.phantom import PhantomCamera
from phantomcli.image import PhantomImage
from phantomcli.command import parse_parameters


# Setting the server
FOLDER_PATH = os.path.dirname(os.path.abspath(__file__))
# Setting up the logger to be used by this module
logger = logging.getLogger(__name__)
# It is important to configure this, because if this isnt set it could be, that running a program, which uses this
# module twice in a row, it can happen, that the socket address is not properly released and it wont work.
socketserver.ThreadingTCPServer.allow_reuse_address = True


class PhantomSocket:
    """
    Objects of this class handle the control connection to a phantom camera.

    CHANGELOG

    Added 20.02.2019
    """

    DEFAULT_PORT = 7115

    DUMMY_COMMAND = b'get info.name'

    RESPONSE_TERMINATION = '\r\n'

    RESPONSE_SEPARATOR = r'\r\n'

    def __init__(self, ip, timeout=10, data_ip='127.0.0.1', data_port=7116, camera_class=PhantomCamera):
        """
        Constructor.

        CHANGELOG

        Added 20.02.2019

        Changed 21.02.2019
        THe timeout is now saved as an attribute.
        Moved the socket creation code to a separate method and not calling it inside the constructor anymore.
        Rather in the connect method.

        Changed 23.02.2019
        Added the parameter for the data port and the the attributes for the data port and the data server, which will
        contain a reference to the server object, which will be used to receive images from the phantom.

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

        # 23.02.2019
        # With the data server attribute will store a reference to the server object, which handles the data
        # transmission. When transferring images the phantom will attempt to connect TO US and then send the raw bytes
        # over this secondary stream.
        # The data ip will be the ip on which the data server is supposed to listen on. The phantom requires a rather
        # specific IP and netmask setting for its controlling unit.
        self.data_port = data_port
        self.data_ip = data_ip
        self.data_server = None

    # ######################################
    # IMAGE ACQUISITION OPERATION ON PHANTOM
    # ######################################

    def img(self):
        """
        This method will send a "img" command to the phantom, which will cause it to take a picture and then send it
        over a newly established data connection to the data server associated with this object.
        This method will then wait for the whole image to be transmitted and return a PhantomImage representation of
        the image.

        CHANGELOG

        Added 23.02.2019

        :return:
        """
        # We need to assume, that the data server has been started before calling this method, which is th case if the
        # attribute is not None
        assert self.data_server is not None

        # With the data server already open, we are telling the phantom to connect to it now using the "startdata"
        # command. After the connection has been established we will send the actual "img" command, which will trigger
        # the phantom to send image bytes over the just established data connection.
        self.startdata()
        self.send_img_request()

        # Over the control connection we have to receive the response to the "img" command, because it will contain the
        # the format and the resolution of the image. Based on the fact that every pixel uses up two bytes and the res.
        # gives us the total number of pixels, only this way the data server knows how many bytes to receive until it
        # is supposed to return the result.
        response = self.receive_image_response()
        self.logger.debug('The response dict: %s', response)
        resolution = response['res']
        self.data_server.size = self.image_byte_size(resolution, image_format='p16')

        # This call to "receive_image" will be blocking until the server has received every single byte of the image.
        # From the raw byte string we can reconstruct the image with the additional info about the resolution (when to
        # make a column break)
        image_bytes = self.data_server.receive_image()
        phantom_image = PhantomImage.from_p16(image_bytes, response['res'])

        return phantom_image

    def image_byte_size(self, resolution, image_format='p16'):
        """
        Calculates the byte size to be received over the socket given the resolution of the image and the used format

        CHANGELOG

        Added 23.02.2019

        :param resolution:
        :param image_format:
        :return:
        """
        pixel_count = resolution[0] * resolution[1]
        if image_format == 'p16':
            byte_count = pixel_count * 2
        else:
            raise NotImplementedError('Format %s is not supported' % image_format)
        return byte_count

    def send_img_request(self):
        """
        This method assembles the command needed to request a image from the camera and sends it off

        CHANGELOG

        Added 23.02.2019

        :return:
        """
        command_string = 'img {cine:-1, start:1, cnt:1, fmt:272}'
        self.send(command_string)
        self.logger.debug('Sent img request for grabbing a picture')

    def receive_image_response(self):
        """
        This method receives the response string of the phantom and parses the parameters into a dict

        CHANGELOG

        Added 23.02.2019

        :return:
        """
        response_string = self.receive_until(self.RESPONSE_TERMINATION)
        self.logger.debug('img request response %s', response_string)
        response_string = self.clean_response(response_string)
        response_parameters = parse_parameters(response_string)

        return response_parameters

    # ################################
    # DATA STREAM OPERATION ON PHANTOM
    # ################################

    def start_data_server(self):
        """
        Creates a new PhantomDataTransferServer on the given data_ip and data_port defined for this object and starts
        its thread.

        CHANGELOG

        Added 23.02.2019

        :return:
        """
        self.data_server = PhantomDataTransferServer(self.data_ip, self.data_port)
        self.data_server.start()

    def startdata(self):
        """
        Sends the port of the open data server to the phantom camera with the "startdata" command.
        Before image data can be transmitted, the phantom camera needs to be told, on which port it can establish a new
        data connection.

        CHANGELOG

        Added 23.02.2019

        :return:
        """
        assert self.data_server is not None

        # Sending the corresponding command with the set data port to the camera
        self.send_startdata_request(self.data_port)
        # Wait for the camera to say "OK!"
        self.receive_get_response()

    def send_startdata_request(self, port):
        """
        Given the port this method simply assembles the correct command syntax for the phantom and sends the command
        off

        CHANGELOG

        Added 23.02.2019

        :param port:
        :return:
        """
        command_string = 'startdata {port:%s}' % port
        self.send(command_string)
        self.logger.debug('Sent start data request on port %s to phantom', port)

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

        CHANGELOG

        Added 21.02.2019

        Changed 22.02.2019
        Moved the code, that actually assembles the command string into its own method "send_get_request".
        Calling that here

        :param structure_name:
        :return:
        """
        # 22.02.2019
        # Sending the get request based on the structure name given
        self.send_get_request(structure_name)

        # Receiving the response from the camera. The response will be given as a list of strings. some commands may
        # return multiple lines of data, but most just a single line -> list with one string element
        response_list = self.receive_get_response()
        return response_list

    def send_get_request(self, structure_name):
        """
        Given the name of a structure/attribute of the phantom camera, this method will construct the command string
        according to the protocols syntax and sends it to the phantom.

        CHANGELOG

        Added 22.02.2019

        :param structure_name:
        :return:
        """
        # Creating the command string according to the syntax and then sending it to the camera. The encoding is handled
        # by the "send" method
        command_string = 'get {}'.format(structure_name)
        self.send(command_string)
        self.logger.debug('Sent get request for "%s" to the phantom', structure_name)

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
        response_string = self.receive_until(self.RESPONSE_TERMINATION)
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
        if self.RESPONSE_SEPARATOR in response_string:
            return response_string.split(self.RESPONSE_SEPARATOR)
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
        except ConnectionRefusedError:
            self.logger.error('Connection to Phantom at %s failed!', self.ip)
            raise ModuleNotFoundError('Connection refused at {}'.format(self.ip))

    def disconnect(self):
        """
        Closes the socket connection and stops the data server, if one is running

        CHANGELOG

        Added 21.02.2019

        Changed 23.02.2019
        In case there is a running data server associated with this object, it is being closed as well now

        :return:
        """
        # 23.02.2019
        # In case we have started a data server to receive images, we obviously need to close it again as well
        if self.data_server is not None:
            self.data_server.stop()

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
        message += '\r\n'
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

    # ###############
    # UTILITY METHODS
    # ###############

    def clean_response(self, response):
        """
        Given a response string from the phantom, this method will remove the "OK!" string at the front.

        CHANGELOG

        Added 23.02.2019

        :param response:
        :return:
        """
        return response.replace('OK! ', '').replace('Ok!', '')


class PhantomDataTransferHandler(socketserver.BaseRequestHandler):
    """
    A handler object will be instantiated to handle a new connection to the PhantomDataTransferServer, which is being
    used to transmit image data from the phantom camera to the control unit.
    This module will only handle a single connection, which means receiving all the bytes of the image and then
    returning the complete byte string back to the server, before the handler closes.

    CHANGELOG

    Added 23.02.2019
    """

    def handle(self):
        """
        Main method for handling the data transfer connection.
        Will handle a single data transmission and then end itself

        CHANGELOG

        Added 23.02.2019
        :return:
        """
        self.server.logger.debug(
            'New DATA STREAM connection from IP %s and PORT %s',
            self.client_address[0],
            self.client_address[1]
        )

        # To this buffer we will append all the incoming byte data and then, when all the data is received return the
        # contens of the buffer to the server, so that the PhantomSocket client can access it there
        buffer = b''
        while self.server.running:
            data = self.request.recv(8192).strip()
            if data and data[0] == '' or len(data) == 0:
                continue

            if len(buffer) != self.server.size:
                buffer += data
                self.server.logger.debug(len(buffer))
            if len(buffer) >= self.server.size - 100:
                # Once the image has been received, the byte string is being passed to the server object by setting
                # its 'image_bytes' attribute. The the main loop is being ended, thus ending the whole handler thread
                self.server.image_bytes = buffer + ('\x00' * (self.server.size - len(buffer))).encode('utf-8')
                self.server.logger.debug('Finished receiving image with %s bytes', len(self.server.image_bytes))
                break

        self.request.close()
        self.server.logger.debug('Data Handler shutting down...')


class PhantomDataTransferServer(socketserver.ThreadingTCPServer):
    """
    This is a threaded server, that is being started, by the main phantom control instance, the PhantomSocket.
    It listens for incoming connections FROM the phantom camera, because over these secondary channels the camera
    transmits the raw byte data.

    CHANGELOG

    Added 23.02.2019
    """

    def __init__(self, ip, port, handler_class=PhantomDataTransferHandler):
        """
        The constructor

        CHANGELOG

        Added 23.02.2019

        :param ip:
        :param port:
        :param handler_class:
        """
        # Creating a new logger, whose name is a combination from the module name and the class name of this very class
        self.log_name = '{}.{}'.format(__name__, self.__class__.__name__)
        self.logger = logging.getLogger(self.log_name)

        self.ip = ip
        self.port = port

        self.size = 0
        self.image_bytes = None

        self.handler_class = handler_class

        super(PhantomDataTransferServer, self).__init__((self.ip, self.port), self.handler_class)
        self.logger.debug('Created Phantom data stream server at IP %s on PORT %s', self.ip, self.port)
        self.thread = threading.Thread(target=self.serve_forever)
        self.running = None

    # ########################
    # DATA RECEPTION FUNCTIONS
    # ########################

    def receive_image(self):
        """
        This method will block the execution of the program, until all the image data has been received. If the image
        data has been received, the internal buffer for the image, which is the "image_bytes" attribute will be cleared
        for the next image, and the current byte string will be returned

        CHANGELOG

        Added 23.02.2019

        :return:
        """
        # Blocking as long as the transmission of the image data hasn't finished
        while self.image_bytes is None:
            time.sleep(0.1)

        # Once the transmission is finished the data will be returned. At the same time the internal attribute which
        # holds the bytes string of the image will be reset to None, so it is ready for the next transmission.
        image_bytes = self.image_bytes
        self.image_bytes = None
        self.logger.debug('Reset internal buffer to %s after image with %s bytes', self.image_bytes, len(image_bytes))
        return image_bytes

    def set_data_size(self, size):
        self.size = size

    # ######################################
    # SOCKET SERVER SERVER RELATED FUNCTIONS
    # ######################################

    def start(self):
        """
        Starts a server Thread and returns Thread object

        CHANGELOG

        Added 21.02.2019

        :return:
        """
        # Setting this boolean attribute will make the handlers run
        self.running = True

        # Actually starting the Thread, which runs the "serve_forever" method of the TCPServer
        self.thread.daemon = True
        self.thread.start()
        self.logger.debug('main thread has started')

    def stop(self):
        """
        Stops the server

        CHANGELOG

        Added 21.02.2019

        :return:
        """
        # Setting the running boolean value to False. This will stop the handler server
        self.running = False

        # Shutting down the actual sockets in the server
        self.server_close()
        self.shutdown()

        # Ensuring, that the Thread terminates
        self.thread.join()
        self.logger.debug('Server shutting down...')


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

    DATA_TIMEOUT = 10

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

        # 22.02.2019
        # Setting up a new data client socket
        self.data_client = None
        self.data_timeout = self.DATA_TIMEOUT

        # The connection with the phantom camera is based on one ongoing socket connection. That is why we are using a
        # infinite while loop here
        while self.server.running:
            data = self.request.recv(1024).strip()
            request = data.decode('utf-8')
            if request and request[0] == '' or len(request) == 0:
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

    def handle_img(self, data):
        """
        Handler for the "img" command on the phantom.
        This will read ot the actual image from the camera, send the response with the image meta data over the control
        interface and then actually send the image data as raw bytes over the secondary data connection.

        CHANGELOG

        Added 23.02.2019

        :param data:
        :return:
        """
        data_string = ''.join(data)
        self.server.logger.debug('IMG %s', data_string)
        parameters = parse_parameters(data_string)

        # "Grabbing" the image from the actual camera object (It is just a static jpeg in the project folder)
        phantom_image = self.server.camera.grab_sample()

        # The phantom protocol dictates, that following to a img command, the camera responds with data structure
        # giving little meta info about the picture to be send including the index of the cine, the picture is from.
        # The resolution and the used format
        self.send_img_response(phantom_image)

        # Here we send the actual image as bytes over the data socket connection
        self.server.logger.debug('Sending image now')
        self.send_image(phantom_image)
        self.server.logger.debug('finished sending image')

    def send_image(self, phantom_image):
        """
        Sends the actual image as byte string over the data client socket

        CHANGELOG

        Added 23.02.2019

        :param phantom_image:
        :return:
        """
        image_bytes = phantom_image.p16()
        self.server.logger.debug('Sending image with size %s bytes', len(image_bytes))
        self.data_client.sendall(image_bytes)

    def send_img_response(self, phantom_image, image_format=272):
        """
        Sends the response to the "img" command over the main control connection.
        This response contains the index of the cine, the image is from, the resolution of the image and the transfer
        format used.

        CHANGELOG

        Added 23.02.2019

        :param phantom_image:
        :param image_format:
        :return:
        """
        # The phantom protocol dictates, that following to a img command, the camera responds with data structure
        # giving little meta info about the picture to be send including the index of the cine, the picture is from.
        # The resolution and the used format
        x_res = phantom_image.resolution[0]
        y_res = phantom_image.resolution[1]
        response_string = 'OK! { cine:-1, res:%sx%s, fmt:%s}' % (x_res, y_res, image_format)
        # Sending over the socket
        self.send(response_string)

    def handle_startdata(self, data):
        """
        The handler for the "startdata" command.
        Creates a new client socket and connects it to the control units IP and on the port, that has been passed as
        the parameter to the command.

        CHANGELOG

        Added 23.02.2019

        :param data:
        :return:
        """
        data_string = ''.join(data)
        self.server.logger.debug('STARTDATA %s', data_string)
        parameters = parse_parameters(data_string)
        port = parameters['port']

        self.send_ok()

        # Starting a new socket client on and connecting to the control unit on the given port, that has been passed as
        # a parameter to the command.
        self.create_data_client()
        data_address = (self.client_address[0], port)
        self.data_client.connect(data_address)

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

    def handle_trig(self, data):
        self.send_ok()

    def handle_rec(self, data):
        self.send_ok()

    def handle_bye(self, data):
        self.send_ok()

    # #############################
    # ADDITIONAL NETWORK OPERATIONS
    # #############################

    def send_ok(self):
        """
        Sends the generic OK! message

        CHANGELOG

        Added 23.02.2019

        :return:
        """
        self.send('OK!')

    def create_data_client(self):
        """
        Creates a fresh socket and puts it into the "data_client" attribute. Also sets the according timeout

        CHANGELOG

        Added 23.02.2019

        :return:
        """
        self.data_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data_client.settimeout(self.data_timeout)

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


# ##################
# MOCK FUNCTIONALITY
# ##################


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
    # Image path
    IMAGE_PATH = os.path.join(FOLDER_PATH, 'sample.jpg')

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
        self.running = None

    def start(self):
        """
        Starts a server Thread and returns Thread object

        CHANGELOG

        Added 21.02.2019

        :return:
        """
        # Setting this boolean attribute will make the handlers run
        self.running = True

        # Actually starting the Thread, which runs the "serve_forever" method of the TCPServer
        self.thread.daemon = True
        self.thread.start()
        self.logger.debug('main thread has started')

    def stop(self):
        """
        Stops the server

        CHANGELOG

        Added 21.02.2019

        :return:
        """
        # Setting the running boolean value to False. This will stop the handler server
        self.running = False

        # Shutting down the actual sockets in the server
        self.shutdown()
        self.server_close()

        # Ensuring, that the Thread terminates
        self.thread.join()

