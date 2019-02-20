# standard library imports
import socket
import logging


# Setting up the logger to be used by this module
logger = logging.getLogger(__name__)


class PhantomSocket:

    PORT = 7115

    def __init__(self, ip):
        self.ip = ip
        logger.debug('Created a new PhantomSocket object to IP %s on PORT %s', self.ip, self.PORT)

        # Creating the socket object to be used to connect to the
