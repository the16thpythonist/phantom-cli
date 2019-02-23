#!/usr/bin/env python3

# standard library imports
import logging
import time

from collections import defaultdict

# third party imports
import click
import matplotlib.pyplot as plt

# package imports
from phantomcli.network import PhantomSocket
from phantomcli.image import PhantomImage
from phantomcli.network import logger
from phantomcli.network import PhantomMockServer


# This will be the translation table, which will be used to return the appropriate constant for defining the logging
# level based on the string passed through the command line option. We are using a default dict, so we do not have to
# deal with a if statement. In case an invalid string is given, the default dict will just return the constant for
# the debug mode, even though the given string isnt even one of its keys.
kwargs = {
    'DEBUG':    logging.DEBUG,
    'INFO':     logging.INFO,
    'WARNING':  logging.WARNING,
    'ERROR':    logging.ERROR
}
logging_config = defaultdict(int, **kwargs)
logging_config.default_factory = lambda: logging.DEBUG


@click.command('connection')
@click.option('--dataport', '-p', default=60000)
@click.option('--dataip', '-i', default='127.0.0.1')
@click.option('--log', '-l', default='DEBUG')
@click.argument('ip')
def command(ip, log, dataip, dataport):
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging_config[log])

    phantom_socket = PhantomSocket(ip, data_ip=dataip, data_port=dataport)
    phantom_socket.connect()
    click.echo('CONNECTED TO THE PHANTOM CAMERA')

    phantom_socket.start_data_server()
    click.echo('STARTED THE DATA SERVER')

    phantom_image = phantom_socket.img()
    click.echo('RECEIVED IMAGE FROM PHANTOM')

    plt.imshow(phantom_image.array, cmap='gray')
    plt.show()

    phantom_socket.disconnect()


if __name__ == '__main__':
    command()
