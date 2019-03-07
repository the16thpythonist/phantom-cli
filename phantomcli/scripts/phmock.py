#!/usr/bin/env python3

# standard library imports
import logging
import time

from collections import defaultdict

# third party imports
import click

# package imports
from phantomcli.network import PhantomMockServer
from phantomcli.scripts.util import logging_format, logging_config


@click.command('connection')
@click.option('--log', '-l', default='DEBUG')
def command(log):
    logging.basicConfig(format=logging_format, level=logging_config[log])

    # Simply starting a mock server here and waiting for any requests to come in
    mock_server = PhantomMockServer()
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
