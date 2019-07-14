#!/usr/bin/env python3

# standard library imports
import logging
import time

# third party imports
import click

# package imports
from phantomcli.network import PhantomMockServer
from phantomcli.scripts.util import logging_format, logging_config
from phantomcli.scripts.util import log_help


@click.command('connection')
@click.option('--log', '-l', default='ERROR', help=log_help)
def command(log):
    """
    Starts a socket server listening at the local IP "127.0.0.1" and on port "7115". The socket server emulate a
    phantom camera and will respond to most commands like a camera would.
    At the moment the "get" "set" and "img" operations are supported.

    Can be terminated by issuing a keyboard interrupt by pressing "CTRL + C"
    """
    logging.basicConfig(format=logging_format, level=logging_config[log])

    # Simply starting a mock server here and waiting for any requests to come in
    mock_server = PhantomMockServer(image_policy='sample')
    mock_server.start()
    click.echo('MOCK SERVER STARTED!')

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        mock_server.stop()
        click.echo('\nMOCK SERVER STOPPED!')


if __name__ == '__main__':
    command()
