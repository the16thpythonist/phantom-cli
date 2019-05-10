# standard library
import socketserver
import logging
import threading
import time
import socket
import struct
import binascii

from uuid import getnode as get_mac

# third party

# from this package

# #######################################
# THE HANDLERS FOR THE ACTUAL CONNECTIONS
# #######################################


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

        Changed 26.02.2019
        Now the program is not expecting the complete amount of pixels to be received, but is also fine with the last
        100 bytes missing from the last TCP package. The missing bytes will just be padded with zeros. This was
        necessary as the camera seems to miss a few bytes from time to time.

        Changed 18.03.2019
        Fixed a bug, where the program would call strip on the data and randomly interpret some of the pixels as
        whitespace characters, which would cause some pixels to go missing.

        :return:
        """
        self.server.logger.debug(
            'New DATA STREAM connection from IP %s and PORT %s',
            self.client_address[0],
            self.client_address[1]
        )

        # To this buffer we will append all the incoming byte data and then, when all the data is received return the
        # contens of the buffer to the server, so that the PhantomSocket client can access it there
        buffer = []
        buffer_length = 0
        while self.server.running:
            data = self.request.recv(524288)
            if data and data[0] == '' or len(data) == 0:
                continue

            if len(buffer) != self.server.size:
                buffer.append(data)
                buffer_length += len(data)
                self.server.logger.debug('Received: %s/%s', buffer_length, self.server.size)

            if buffer_length == self.server.size:
                # Once the image has been received, the byte string is being passed to the server object by setting
                # its 'image_bytes' attribute. The the main loop is being ended, thus ending the whole handler thread
                append_bytes = ('\x00' * (self.server.size - len(buffer))).encode('utf-8')
                buffer_bytes = b''.join(buffer)
                self.server.image_bytes = buffer_bytes
                self.server.logger.debug('Received %s bytes; had to append %s', len(buffer), len(append_bytes))
                self.server.logger.debug('Finished receiving image with %s bytes', len(self.server.image_bytes))
                break

        self.request.close()
        self.server.logger.debug('Data Handler shutting down...')


class PhantomXDataTransferHandler(threading.Thread):
    """
    This thread will be started by the 10G Data transfer server, if an image has to be received
    """
    # CONSTANT DEFINITIONS
    # --------------------

    # The protocol identifier, which a phantom camera uses in the ethernet frame header to identify the data packages
    PHANTOM_ETHERNET_PROTOCOL = b'\x88\xb7'

    # The header size is required to compute the payload size, which in turn is required to extract the payload data
    # from the whole ethernet frame.
    # 10.05.2019
    # Turns out the header size is actually 32 and not 14
    HEADER_SIZE = 32

    def __init__(self, server):
        """
        The constructor

        CHANGELOG

        Added 19.03.2019

        :param server:
        """
        threading.Thread.__init__(self)
        self.server = server
        self.socket = None

    # MAIN THREAD METHOD
    # ------------------
    # This is the method, that is being executed as the thread

    def run(self):
        """
        A new socket will be created to listen for raw ethernet frames. All ethernet frames are then received and
        decoded to check for their protocol identifier, if it matches a phantom camera the payload is being appended to
        the buffer for the image data

        CHANGELOG

        Added 19.03.2019

        :return: void
        """
        self.server.logger.debug('New RAW frame handler for INTERFACE %s', self.server.ip)

        # Creating the socket to accept the raw ethernet frame
        # For the case of a RAW socket connection "server.ip" has to be the string identifier of a network interface.
        # "socket.htons(3)" specifies to listen for all protocols (The irrelevant packages are filtered after receiving)
        self.socket = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket.htons(3))
        self.socket.bind((self.server.ip, 0))

        # To this buffer we will append all the incoming byte data and then, when all the data is received return the
        # contents of the buffer to the server, so that the PhantomSocket client can access it there
        # The handler object really only interact with the server, so that the client has to only interact with the
        # server.
        buffer = []
        buffer_length = 0
        self.server.logger.debug("Running status: %s", self.server.running)
        while self.server.running:
            data = self.socket.recv(10000)

            # This will decode the raw bytes string, which has been received into the various parts of the header and
            # the payload and save those as values in a dictionary for easy access
            data_dict = self.unpack_data(data)

            # A package is only processed as part of the image, if the protocol identifier matches the one used by the
            # phantom camera.
            # If that is the case, the payload data is being appended to the buffer.
            if data_dict['protocol'] == self.PHANTOM_ETHERNET_PROTOCOL:
                payload = data_dict['payload']
                buffer.append(payload)
                buffer_length += len(payload)
                self.server.logger.debug('Received %s/%s bytes total', buffer_length, self.server.size)

            # when all data has been received, the buffer is being concatenated to one long bytes string and returned
            # to the server.
            if buffer_length >= self.server.size:
                self.server.image_bytes = b''.join(buffer)[0:self.server.size]
                self.server.logger.debug('Received image with %s/%s bytes', buffer_length, self.server.size)
                break

        self.socket.close()
        self.server.logger.debug('Data Handler shutting down...')

    # HELPER METHODS
    # --------------

    @classmethod
    def unpack_data(cls, data):
        """
        Given the data received as bytes string, this method will unpack the various informations within the header
        and the payload into a dictionary with the keys "source" for the src MAC address, "destination" for the dst
        MAC, "protocol" for the used protocol identifier and "payload" for the data sent within the ethernet frame

        CHANGELOG

        Added 19.03.2019

        Changed 10.05.2019
        Fixed the unpacking by changing the header size from 14 to 32 and modifying the struct unpack accordingly

        :param data:
        :return: data
        """
        payload_length = len(data) - 32
        format_string = '!6s6s2s18s{}s'.format(payload_length)
        source_address, destination_address, protocol, _, payload = struct.unpack(format_string, data)
        data_dict = {
            'source':       source_address,
            'destination':  destination_address,
            'protocol':     protocol,
            'payload':      payload
        }
        return data_dict


# ################################
# THE DATA TRANSFER SERVER OBJECTS
# ################################


class DataTransferServer:
    """
    This is the base class for all possible variations of data transfer servers. The most important ones being the
    one for the "normal" network data transmission and the one for the 10G network transmission.
    This class defines all the common functionality which all data transfer servers have to share (acting as sort of an
    interface as well.).

    IMPORTANT: A child class inheriting from this class has to initialize the according socketserver.Server class first,
    as this base class makes assumptions about that behaviour.

    CHANGELOG

    Added 19.03.2019
    """

    def __init__(self, ip, port, format, handler_class):
        """
        The constructor.

        CHANGELOG

        Added 19.03.2019

        :param ip:
        :param port:
        :param format:
        :param handler_class:
        """
        # Creating a new logger, whose name is a combination from the module name and the class name of this very class
        self.log_name = '{}.{}'.format(__name__, self.__class__.__name__)
        self.logger = logging.getLogger(self.log_name)

        # Saving the ip and the port. The tuple of both ip and port is needed for most of the networking functionality
        # of python.
        self.ip = ip
        self.port = port
        self.address = (self.ip, self.port)

        self.format = format
        self.handler_class = handler_class

        self.size = 0
        self.image_bytes = None
        self.running = None
        self.thread = None

    def set_data_size(self, size):
        self.size = size


class PhantomDataTransferServer(socketserver.ThreadingTCPServer, DataTransferServer):
    """
    This is a threaded server, that is being started, by the main phantom control instance, the PhantomSocket.
    It listens for incoming connections FROM the phantom camera, because over these secondary channels the camera
    transmits the raw byte data.

    The way it works:
    The main program execution maintains a reference to this object. This object will work as the main access point
    for receiving images using the "receive_image" method. But the actual process of receiving the image is not handled
    in this object.
    Although this object listens for incoming data connections, but as soon as a camera makes a request for a new
    connection for transferring an image, this object automatically creates a handler object and passes the data
    connection to that handler, which is then in charge of receiving the data in a separate thread.
    The "receive_image" method just waits until the handler is finished, gets the image from the handler and then passes
    it along to the main program

    CHANGELOG

    Added 23.02.2019

    Changed 19.03.2019
    Moved most of the actual functions into a base class. This class now only inherits from that base class.
    """
    def __init__(self, ip, port, fmt, handler_class=PhantomDataTransferHandler):
        DataTransferServer.__init__(self, ip, port, fmt, handler_class)
        socketserver.ThreadingTCPServer.__init__(self, self.address, self.handler_class)

        # This has to be called in the constructor as well
        self.create_thread()

    # DATA RECEPTION FUNCTIONS
    # ------------------------

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
        self.logger.debug('Reset internal buffer to %s after image with %s bytes', self.image_bytes,
                          len(image_bytes))
        return image_bytes

    # SOCKET SERVER SERVER RELATED FUNCTIONS
    # --------------------------------------

    def create_thread(self):
        self.thread = threading.Thread(target=self.serve_forever)

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


class PhantomXDataTransferServer(socketserver.ThreadingUnixStreamServer, DataTransferServer):
    """
    This is a threaded server, that is being started by the main phantom control instance.
    It listens for incoming RAW ETHERNET FRAME connections on the specified ethernet interface.

    The way it works:
    The main program execution maintains a reference to this object. This object will work as the main access point
    for receiving images using the "receive_image" method. But the actual process of receiving the image is not handled
    in this object.
    Although this object listens for incoming data connections, but as soon as a camera makes a request for a new
    connection for transferring an image, this object automatically creates a handler object and passes the data
    connection to that handler, which is then in charge of receiving the data in a separate thread.
    The "receive_image" method just waits until the handler is finished, gets the image from the handler and then passes
    it along to the main program

    CHANGELOG

    Added 19.03.2019
    """
    def __init__(self, interface, port, fmt, handler_class=PhantomXDataTransferHandler):
        DataTransferServer.__init__(self, interface, port, fmt, handler_class)

        self.handler = self.handler_class(self)

    # DATA RECEPTION FUNCTIONS
    # ------------------------
    # These functions will be used to interface with the transmission process from the outside

    def receive_image(self):
        """
        This method will block the execution of the program, until all the image data has been received. If the image
        data has been received, the internal buffer for the image, which is the "image_bytes" attribute will be cleared
        for the next image, and the current byte string will be returned

        Added 19.03.2019

        Changed 10.05.2019
        Since this server object does not automatically dispatch a handler (ethernet frames are stateless transmission)
        A new handler thread has to be started after an image has been received.

        :return:
        """
        while self.image_bytes is None:
            time.sleep(0.1)

        # Once the transmission is finished the data will be returned. At the same time the internal attribute which
        # holds the bytes string of the image will be reset to None, so it is ready for the next transmission.
        image_bytes = self.image_bytes
        self.image_bytes = None
        self.logger.debug('Reset internal buffer to %s after image with %s bytes', self.image_bytes,
                          len(image_bytes))

        # 10.05.2019
        # After the previous handler did its purpose, a new handler has to be started to handle the (possibly) next
        # transmission of an image
        self.renew_handler()

        return image_bytes

    # SOCKET SERVER RELATED FUNCTIONS
    # -------------------------------

    def renew_handler(self):
        """
        Creates a new handler object and starts it

        CHANGELOG

        Added 10.05.2019

        :return:
        """
        self.handler = self.handler_class(self)
        self.handler.start()

    def stop(self):
        """
        Closes the handler object, that is still running.

        CHANGELOG

        Added 19.03.2019
        :return:
        """
        self.running = False
        self.handler.join()

    def start(self):
        """
        Starts the first handler object.

        CHANGELOG

        Added 19.03.2019
        :return:
        """
        self.running = True
        self.handler.start()


# ##############
# HELPER CLASSES
# ##############


class RawByteSender:
    """
    This class has a single purpose: To send raw ethernet frames. The constructor expects the raw bytes string to send,
    the interface name to send the frames to, the destination MAC address, the protocol identifier and the package
    size.
    With these configurations the sender can be used to send out the data as raw ethernet frames, packed up in
    packages of the defined size.

    CHANGELOG

    Added 19.03.2019
    """

    # CONSTANT DEFINITIONS
    # --------------------

    SIZE = 1504

    HEADER_SIZE = 32

    def __init__(self, raw_bytes, interface, destination_address, protocol, package_size=1500):
        """
        The constructor.

        CHANGELOG

        Added 19.03.2019

        :param raw_bytes:
        :param interface:
        :param destination_address:
        :param protocol:
        :param package_size:
        """
        # Creating a new logger, whose name is a combination from the module name and the class name of this very class
        self.log_name = '{}.{}'.format(__name__, self.__class__.__name__)
        self.logger = logging.getLogger(self.log_name)

        self.bytes = raw_bytes
        self.size = len(self.bytes)
        self.destination = destination_address
        self.source = hex(get_mac())[2:]
        self.protocol = protocol

        # We need a socket of the type "SOCK_RAW" with "AF_PACKET" to be able to send raw ethernet frames.
        # In contrary to "normal" sockets, we also do not need to specify a IP address to bind them but rather the
        # interface identifier string for the interface used to send them (for example eth0 for the ethernet port)
        self.socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        self.socket.bind((interface, 0))

        self.sent_bytes = 0

        self.package_size = package_size

    def send(self):
        """
        Sends out all the data

        This method creates packages of the configured size from small parts of the raw bytes and sends them
        through the socket until no raw bytes are left to be sent.

        CHANGELOG

        Added 19.03.2019

        :return: void
        """
        while self.sent_bytes < self.size:
            # The "get_package" method assembles the byte string of one ethernet frame, which consists of a header and
            # the payload, which is a fraction of the raw bytes to be send.
            package = self.get_package()
            self.socket.sendall(package)

    def get_package(self):
        """
        Creates a new ethernet frame byte string from the raw data that is left and returns it.

        CHANGELOG

        Added 19.03.2019

        :return: bytes string
        """
        # creates the bytes string part, which is the header of the ethernet frame. This is essentially always the same
        # and contains information about
        header = self.get_header()
        payload = self.get_payload()
        return header + payload

    def get_header(self):
        """
        Creates a new bytes string, which will work as the header of the ethernet frame. The header contains
        information about the source and destination MAC address for the package and a protocol identifier, which is
        usually used to identify protocols, that are built on top of ethernet frames.

        CHANGELOG

        Added 19.03.2019

        :return: bytes string
        """
        header = struct.pack(
            '!6s6s2s18s',
            binascii.unhexlify(self.source),
            binascii.unhexlify(self.destination),
            binascii.unhexlify(self.protocol),
            binascii.unhexlify('00')
        )
        return header

    def get_payload(self):
        """
        Creates a new bytes string from the part of the given raw data, that is still left. The part of the raw data
        to be used is identified by the counter "sent_bytes" which keeps track of how many bytes have already been sent
        and the size of the payload.

        CHANGELOG

        Added 19.03.2019

        :return: bytes string
        """
        # Calculates the size (in bytes), which the payload is allowed to have, when working with the given package and
        # header size.
        size = self.get_payload_size()

        # Slice the calculated section of the raw data and use it as the payload
        payload = self.bytes[self.sent_bytes:self.sent_bytes + size]
        self.sent_bytes += size
        return payload

    def get_payload_size(self):
        """
        Calculates the size (in bytes), which the payload is allowed to have, when working with the given package and
        header size.

        CHANGELOG

        Added 19.03.2019

        :return: int
        """
        return self.package_size - self.HEADER_SIZE
