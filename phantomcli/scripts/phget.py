#!/usr/bin/env python3

# standard library imports
import logging
import time

from collections import defaultdict

# third party imports
import click

# package imports
from phantomcli.network import PhantomSocket
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
@click.option('--log', '-l', default='DEBUG')
@click.argument('ip')
@click.argument('key')
def command(key, ip, log):
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging_config[log])

    phantom_socket = PhantomSocket(ip)
    phantom_socket.connect()
    click.echo('CONNECTED TO THE PHANTOM CAMERA')

    result = phantom_socket.get(key)
    click.echo('PHANTOM RETURNED:\n\n{}'.format('\n'.join(result)))
    phantom_socket.disconnect()

if __name__ == '__main__':
    command()
