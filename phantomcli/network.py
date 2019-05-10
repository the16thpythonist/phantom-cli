
# standard library imports
import socket
import logging
import subprocess
import threading
import socketserver
import demjson
import os
import struct
import binascii

from collections import defaultdict
from uuid import getnode as get_mac

# third party libraries

# package imports
from phantomcli.phantom import PhantomCamera
from phantomcli.image import PhantomImage
from phantomcli.command import parse_parameters
from phantomcli.command import ImgFormatsMap
from phantomcli.data import PhantomDataTransferServer, PhantomXDataTransferServer, RawByteSender


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

    # CONSTANT DEFINITIONS
    # --------------------

    DEFAULT_PORT = 7115

    DUMMY_COMMAND = b'get info.name'

    RESPONSE_TERMINATION = '\r\n'

    RESPONSE_SEPARATOR = r'\r\n'

    # 19.03.2019
    # This is a mapping, for which the value of the network_type is used as the input and according to the boolean
    # value it will return the corresponding class for the data server, that either handles normal network connection
    # or the 10G network connection.
    # In general we are using default dicts here to avoid using if conditions to check for value validity. If a value
    # is invalid, the default option will be chosen.
    DATA_TRANSFER_SERVERS_MAPPING = defaultdict(lambda: PhantomDataTransferServer, **{
        'e':        PhantomDataTransferServer,
        'x':        PhantomXDataTransferServer
    })

    # IMAGE TRANSFER FORMATS
    # This dict assigns the byte size to each possible image transfer format. The byte size is an integer of how many
    # bytes each pixel is made up of in the corresponding raw data stream.
    IMG_FORMAT_BYTES = {
        'P8':               1,
        'P8R':              1,
        'P16':              2,
        'P16R':             2,
        'P10':              1.25
    }

    def __init__(
            self,
            ip,
            timeout=10,
            data_ip='127.0.0.1',
            data_port=7116,
            data_interface='enp1s0',
            img_format='P16',
            camera_class=PhantomCamera,
            network_type='e'
    ):
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

        Changed 28.02.2019
        Added the parameter and attribute "img_format" for saving the string token name of the transfer format to be
        used.

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
        self.data_interface = data_interface
        self.data_server = None

        # 19.03.2019
        # If the value is "e", than it means a normal network is being used, if it is "x" it means a 10G ethernet
        # connection is used, for which special rules apply and thus a special data transfer server is needed.
        self.network_type = network_type
        self.data_server_class = self.DATA_TRANSFER_SERVERS_MAPPING[self.network_type]

        # 28.02.2019
        # Will save the image format to be used for the
        self.img_format = img_format
        if self.network_type == 'x':
            self.img_format = 'P10'

    # ####################################
    # INITIALIZATION/CONFIGURATION METHODS
    # ####################################

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

        Changed 28.02.2019
        Actually using the value for the img format specified in "img_format" now.

        Changed 19.03.2019
        Moved the whole process of interacting with the data server object to actually receive the image into another
        method.
        Removed the call to startdata from this method, as this has to be done on a user level, because it should not
        be used when handling a x-network connection.

        :return:
        """
        # We need to assume, that the data server has been started before calling this method, which is th case if the
        # attribute is not None
        assert self.data_server is not None

        # With the data server already open, we are telling the phantom to connect to it now using the "startdata"
        # command. After the connection has been established we will send the actual "img" command, which will trigger
        # the phantom to send image bytes over the just established data connection.
        self.send_img_request()

        # Over the control connection we have to receive the response to the "img" command, because it will contain the
        # the format and the resolution of the image. Based on the fact that every pixel uses up two bytes and the res.
        # gives us the total number of pixels, only this way the data server knows how many bytes to receive until it
        # is supposed to return the result.
        response = self.receive_image_response()
        self.logger.debug('The response dict: %s', response)
        resolution = response['res']

        # 19.03.2019
        # Moved the whole process of communicating and creating the image wrapper object to a separate method
        phantom_image = self.receive_image(resolution)

        return phantom_image

    def receive_image(self, resolution):
        """
        Given the resolution of the image to be received, this method will handle the actual interaction with the data
        server object needed and the creation of the PhantomImage wrapper object from the raw byte string.

        CHANGELOG

        Added 19.03.2019

        :param resolution:
        :return:
        """
        resolution = (resolution[1], resolution[0])
        # This method will handle the necessary interactions with the data server to actually receive the raw byte
        # string representing the image from the data server's connection to the camera
        image_bytes = self.receive_image_bytes(resolution)

        # This creates a PhantomImage wrapper object from the raw bytes string. Obviously it also needs the resolution
        # for that to be able to know, where to make the "line breaks"
        phantom_image = self.create_image(image_bytes, resolution)

        return phantom_image

    def receive_image_bytes(self, resolution):
        """
        Given the resolution of the image, that is being sent, this method will calculate the according amount of bytes
        to be received, pass them to the data server and then receive the raw bytes string, representing the image
        from the data server. This byte string will then be returned.

        CHANGELOG

        Added 19.03.2019

        :param resolution:
        :return:
        """
        # 28.02.2019
        # The actual value of the "img_format" property is being used now, that all the formats are implemented
        self.data_server.size = self.image_byte_size(resolution, image_format=self.img_format)

        # This call to "receive_image" will be blocking until the server has received every single byte of the image.
        # From the raw byte string we can reconstruct the image with the additional info about the resolution (when to
        # make a column break)
        image_bytes = self.data_server.receive_image()

        return image_bytes

    def create_image(self, image_bytes, resolution):
        """
        Given the raw image data byte string and the resolution, together with the knowledge about the used transfer
        format in the attribute "img_format", this method will create a PhantomImage wrapper object for the image
        (Representation as numpy array)

        CHANGELOG

        Added 19.03.2019

        :param image_bytes:
        :param resolution:
        :return:
        """
        # 28.02.2019
        # The image is now also being created from the used transfer format based on the dynamic value saved in the
        # "img_format" attribute.
        self.logger.debug(
            'Converting %s byte string to PhantomImage with format %s and res %s',
            len(image_bytes),
            self.img_format,
            resolution
        )
        phantom_image = PhantomImage.from_transfer_format(self.img_format, image_bytes, resolution)

        return phantom_image

    def image_byte_size(self, resolution, image_format='P16'):
        """
        Calculates the byte size to be received over the socket given the resolution of the image and the used format

        CHANGELOG

        Added 23.02.2019

        Changed 28.02.2019
        All image transfer formats with their different byte sizes are implemented now and thus the size of the stream
        is calculated in here accordingly.

        Changed 20.03.2019
        Added additional explicit conversion of the result into an integer

        :param resolution:
        :param image_format:
        :return:
        """
        # 28.02.2019
        # To make the given string case insensitive
        image_format_upper = image_format.upper()

        pixel_count = resolution[0] * resolution[1]

        # 28.02.2019
        # All the formats are implemented now, and the amount of bytes each pixel is made up of is saved in the static
        # dict. The format still has to be a valid key to that dict though.
        if image_format_upper in self.IMG_FORMAT_BYTES.keys():
            byte_count = pixel_count * self.IMG_FORMAT_BYTES[image_format_upper]

            # 20.03.2019
            # As the value of bytes per pixel for the P10 format is not a whole number, we need the possibly float
            # into an int
            byte_count = int(byte_count)
        else:
            raise NotImplementedError('Format %s is not supported' % image_format)

        return byte_count

    def send_img_request(self):
        """
        This method assembles the command needed to request a image from the camera and sends it off

        CHANGELOG

        Added 23.02.2019

        Changed 28.02.2019
        Using the actual image format specified in the "img_format" attribute

        :return:
        """
        # 19.03.2019
        # Moved the creation of the command string to a separate method, because the command string is different,
        # based on the value of the "network_type" attribute of this object. And that difference is none of this methods
        # concern, this method only has to send the command, whatever that may be.
        command_string = self.img_command()
        self.send(command_string)
        self.logger.debug('Sent img request for grabbing a picture')

    def img_command(self):
        method_name = "%s_img_command" % self.network_type
        method = getattr(self, method_name)
        return method()

    def e_img_command(self):
        # 28.02.2019
        # The "img_format" attribute saves the string token name of the format, for the request to the camera the
        # number representation is needed though.
        img_format_number = ImgFormatsMap.get_number(self.img_format)
        command_string = 'img {cine: -1, start:0, cnt:1, fmt:%s}' % img_format_number
        return command_string

    def x_img_command(self):
        mac_address = self.get_hex_mac_address()
        command_string = 'ximg {cine: -1, start:0, cnt:1, dest:%s}' % mac_address
        return command_string

    def get_hex_mac_address(self):
        mac_address = get_mac()
        mac_string = '%012x' % mac_address
        return mac_string

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

        Changed 19.03.2019
        Moved the creation of the new data server object to a separate method.

        :return:
        """
        # 19.03.2019
        # Previously the creation of a new data transfer server was done by explicitly using the one class for the
        # normal network connection. Now this functionality has been outsourced to this new method, which creates
        # a new object from a class, which is based on the value of the "x_network_flag". But that doesnt influence
        # the rest of the handling of the data server, as both classes expose the same interface.
        self.assign_data_transfer_server()

        # Here we can just assume, that a new data server object has been instantiated in the "data_server" variable
        self.data_server.start()

    def assign_data_transfer_server(self):
        """
        This method creates a new instance of a data server class, based on whether the client object is using the
        normal or the 10G network connection (also called x-network).
        This new instance will then be saved in the "data_server" attribute of this client object.

        CHANGELOG

        Added 19.03.2019

        :return:
        """
        # Depending of whether this object operates on a 10G or normal network connection, this will either be the
        # name of the ethernet interface or the IP address of this machine.
        entry_point = self.data_entry_point()
        self.data_server = self.data_server_class(entry_point, self.data_port, self.img_format)

    def data_entry_point(self):
        """
        Returns the property of this system, which identifies where the phantom is supposed to send its image data to.
        For a normal network connection, this simply is the IP address, under which this machine is connected to the
        phantom, but for a x-network connection, it is the name of the ethernet interface on this machine

        CHANGELOG

        Added 19.03.2019

        :return:
        """
        if self.network_type == 'x':
            return self.data_interface
        else:
            return self.data_ip

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
    # SET OPERATIONS ON PHANTOM
    # #########################

    def set(self, structure_name, value):
        """
        Sets the given value to the given attribute of the phantom

        CHANGELOG

        Added 01.03.2019

        :param structure_name:
        :param value:
        :return:
        """
        self.send_set_request(structure_name, value)
        response_list = self.receive_set_response()
        return response_list

    def send_set_request(self, structure_name, value):
        """
        Send a SET request for the given value and attribute of the phantom over the network socket

        CHANGELOG

        Added 01.03.2019

        :param structure_name:
        :param value:
        :return:
        """
        command_string = 'set %s %s' % (structure_name, value)
        self.send(command_string)
        self.logger.debug('Send SET to phantom')

    def receive_set_response(self):
        """
        Receive the response to a SET request

        CHANGELOG

        Added 01.03.2019

        :return:
        """
        response_string = self.receive_until(self.RESPONSE_TERMINATION)
        response_list = self.get_response_list(response_string)
        return response_list

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

        Changed 10.05.2019
        Changed the exception, that is being raised from "ModuleNotFoundError" to Connection error

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
            raise ConnectionError('There is no socket at {}!'.format(self.ip))
        except ConnectionRefusedError:
            self.logger.error('Connection to Phantom at %s failed!', self.ip)
            raise ConnectionError('Connection refused at {}'.format(self.ip))

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

    # ###############################
    # OBJECT PROPERTIES GETTER/SETTER
    # ###############################

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

    def handle_ximg(self, data):
        """
        Handler for the "ximg" command on the pahntom
        This will read an image from the camera object, send a response and then send the image data over the
        ethernet interface configured for the mock server.

        CHANGELOG

        Added 19.03.2019

        Changed 10.05.2019
        Using the function "send_images_x" instead of doing all the network operations in this method.
        Also added support for actually sending as many images as specified in the image request

        :param data:
        :return:
        """
        data_string = ''.join(data)
        self.server.logger.debug('XIMG %s', data_string)

        # 10.05.2019
        # Parsing the commands for the call
        parameters = parse_parameters(data_string)
        destination = parameters['dest']
        count = parameters['cnt']

        phantom_image = self.server.grab_image(self.server.camera)
        self.server.logger.debug('created phantom image with resolution %s', phantom_image.resolution)

        # The phantom protocol dictates, that following to a img command, the camera responds with data structure
        # giving little meta info about the picture to be send including the index of the cine, the picture is from.
        # The resolution and the used format
        self.send_img_response(phantom_image)

        # 10.05.2019
        # Sending as many images as specified by the command request
        self.send_images_x(phantom_image, destination, count)

        self.server.logger.debug('sent raw data')

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

        # 18.03.2019
        # "Grabbing" an image based on the dynamic function object in "server.grab_image". Based on the config of the
        # mock, this may return different types of images.
        phantom_image = self.server.grab_image(self.server.camera)
        self.server.logger.debug('created phantom image with resolution %s', phantom_image.resolution)

        # The phantom protocol dictates, that following to a img command, the camera responds with data structure
        # giving little meta info about the picture to be send including the index of the cine, the picture is from.
        # The resolution and the used format
        self.send_img_response(phantom_image)

        # Here we send the actual image as bytes over the data socket connection
        self.server.logger.debug('Sending image now')
        self.send_image(phantom_image, parameters['fmt'])
        self.server.logger.debug('finished sending image')

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

        Changed 01.03.2019
        Actually sending an error message back now, when an unknown attribute is requested.

        :param data:
        :return:
        """
        # Actually getting the value from the phantom object
        structure_name = data[0]
        self.server.logger.debug('GET %s', structure_name)
        try:
            structure_value = self.server.camera.get(structure_name)

            # Sending the response
            response_list = self.create_response_list(structure_value)
            self.send_get_response(response_list)
        except KeyError:
            self.send_key_error(structure_name)

    def handle_set(self, data):
        """
        Setting the new value to the camera object maintained by the server

        CHANGELOG

        Added 01.03.2019

        :param data:
        :return:
        """
        structure_name = data[0]
        value = ''.join(data[1:])
        self.server.logger.debug('SET %s %s' % (structure_name, value))
        try:
            self.server.camera.set(structure_name, value)

            # Maybe actually check the data here at some point
            self.send_ok()
        except KeyError:
            self.send_key_error(structure_name)

    def handle_trig(self, data):
        self.server.logger.info("TRIG")
        self.send_ok()

    def handle_rec(self, data):
        self.send_ok()

    def handle_bye(self, data):
        self.send_ok()

    # BUSINESS LOGIC METHODS
    # ----------------------

    def send_images_x(self, phantom_image, destination_mac, count):
        """
        Sends as many images as specified by "count" over the ethernet interface to the destination MAC address

        CHANGELOG

        Added 10.05.2019

        :param phantom_image:
        :param destination_mac:
        :param count:
        :return:
        """
        for i in range(count):
            self.send_image_x(phantom_image, destination_mac)

    def send_image_x(self, phantom_image, destination_mac):
        """
        Sends the given phantom image over the 10G connection using raw ethernet frames to the machine specified by
        "destination_mac"

        CHANGELOG

        Added 10.05.2019

        :param phantom_image:
        :param destination_mac:
        :return:
        """
        # The interface identifier was set as a configuration of the MockServer object and can be obtained from it
        interface = self.server.interface

        # The protocol identifier for ethernet frames sent by a phantom camera can also be acquired from the mock
        # server object. It is defined as a constant, because it is not configurable. All phantom cameras use the same
        protocol = self.server.ETHERNET_PROTOCOL

        sender = RawByteSender(phantom_image.p10(), interface, destination_mac, protocol)
        sender.send()
        self.server.logger.debug("Sending image as raw ethernet frames")

    def send_image(self, phantom_image, image_format):
        """
        Sends the actual image as byte string over the data client socket

        CHANGELOG

        Added 23.02.2019

        :param phantom_image:
        :return:
        """
        image_bytes = phantom_image.to_transfer_format(image_format)
        self.server.logger.debug('Sending image with size %s bytes', len(image_bytes))
        self.data_client.sendall(image_bytes)

    # ADDITIONAL NETWORK OPERATIONS
    # -----------------------------

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
        response_string = 'OK! { cine: -1, res:%sx%s, fmt:%s}' % (x_res, y_res, image_format)
        # Sending over the socket
        self.send(response_string)

    def send_key_error(self, key):
        """
        Send a ERR response, which tells that the given structure name is not a valid attribute of the camera

        CHANGELOG

        Added 01.03.2019

        :param key:
        :return:
        """
        self.send('ERR: name %s is unknown' % key)

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

    # HELPER METHODS
    # --------------

    @classmethod
    def create_response_list(cls, structure):
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

    Changed 18.03.2019
    Replaced the "127.0.0.1" as ip with "0.0.0.0", which means to let the socket listen on all ip's, including but not
    being limited to 127.0.0.1. This could come in handy when for example trying to access the mock server from another
    machine within the same network, if the socket just listened to localhost, that wouldnt work.
    """
    # CONSTANT DEFINITIONS
    # --------------------

    # 18.03.2019
    # The mock server will operate on a fix port, but can be talked to through all IP addresses.
    DEFAULT_IP = '0.0.0.0'

    # A phantom camera control interface is always connected to the
    DEFAULT_PORT = 7115

    # 10.05.2019
    # This string defines the name of a network interface. This interface will be used to send the raw ethernet frames
    DEFAULT_INTERFACE = "enp1s0"

    # 10.05.2019
    # This string defines the protocol identifier sent with every ethernet frame. This value in particular is the
    # protocol ID a phantom camera uses, when transmitting data over a 10G connection.
    ETHERNET_PROTOCOL = '88b7'

    # Image path
    IMAGE_PATH = os.path.join(FOLDER_PATH, 'sample.jpg')

    # 20.3.2019
    # Based on the string keyword given as a parameter a different function will be used to grab the image from
    # the camera object.
    # One grab function loads a jpeg sample image and returns that.
    # The other grab function generates a random noise image and returns that.
    IMAGE_POLICIES = defaultdict(lambda: getattr(PhantomCamera, 'grab_sample'), **{
        'sample':   getattr(PhantomCamera, 'grab_sample'),
        'random':   getattr(PhantomCamera, 'grab_random')
    })

    # THE CONSTRUCTOR
    # ---------------

    def __init__(
            self,
            camera_class=PhantomCamera,
            handler_class=PhantomMockControlInterface,
            image_policy='sample',
            ip=DEFAULT_IP,
            port=DEFAULT_PORT,
            interface=DEFAULT_INTERFACE
    ):
        """
        The constructor.

        CHANGELOG

        Added 21.02.2019

        Changed 18.03.2019
        Added the parameter image policy, which can either be "sample", which will the mock cause to return a sample
        image from a JPEG over and over again, or "random" which will make it generate random images for each image
        request.

        Changed 10.05.2019
        Added the ip, port and interface parameters to make the network behaviour of the mock configurable

        :param class camera_class:
        """
        # Creating a new logger, whose name is a combination from the module name and the class name of this very class
        self.log_name = '{}.{}'.format(__name__, self.__class__.__name__)
        self.logger = logging.getLogger(self.log_name)

        # 10.05.2019
        # The network behaviour of the mock is defined by the ip address on which it operates, the port on which it
        # listens and for the 10G connectivity the interface identifier to which the raw ethernet frames will be sent
        self.ip = ip
        self.port = port
        self.interface = interface

        # 18.03.2019
        # Saving the image policy to be used.
        # The "grab_image" field will actually contain a function object. According to the string about the image policy
        # given it will either contain the "PhantomCamera.grab_sample" or the the "PhantomCamera.grab_random" function.
        # To actually acquire an image you have to call "self.grab_image(actual_phantom_camera_instance)"
        self.image_policy = image_policy
        self.grab_image = self.IMAGE_POLICIES[image_policy]
        self.logger.debug('Mock server image policy: %s (%s)', image_policy, self.grab_image.__name__)

        # The handler and the camera class, on which the mock behaviour is based on can be passed as arguments to ensure
        # loose coupling
        self.handler_class = handler_class
        self.camera_class = camera_class
        self.camera = self.camera_class()

        super(PhantomMockServer, self).__init__((self.ip, self.port), self.handler_class)
        self.logger.debug('Created MockServer bound to IP %s and PORT %s', self.ip, self.port)

        self.thread = threading.Thread(target=self.serve_forever)
        self.running = None

    # MANAGEMENT FUNCTIONS
    # --------------------

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
        self.logger.debug('Thread has been stopped')

