#!/usr/bin/env python3

# standard library imports
import logging
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
def command(ip, log):
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging_config[log])

    mock_server = PhantomMockServer()
    mock_server.start()

    phantom_socket = PhantomSocket(ip)
    phantom_socket.ping()

    phantom_socket.connect()


if __name__ == '__main__':
    command()
