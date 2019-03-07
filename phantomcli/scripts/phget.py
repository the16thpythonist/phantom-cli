#!/usr/bin/env python3

# standard library imports
import logging
import time

from collections import defaultdict

# third party imports
import click

# package imports
from phantomcli.network import PhantomSocket
from phantomcli.scripts.util import logging_format, logging_config, formats


@click.command('connection')
@click.option('--format', '-f', default='P16')
@click.option('--log', '-l', default='DEBUG')
@click.argument('ip')
@click.argument('key')
def command(key, ip, log, format):
    """

    CHANGELOG

    Added 23.02.2019

    Changed 28.20.2019
    Added the parameter "format" to specify the image transfer format to be used

    :param key:
    :param ip:
    :param log:
    :param format:
    :return:
    """
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging_config[log])

    # Using the default dict to get a valid format string no matter what
    format = formats[format]
    phantom_socket = PhantomSocket(ip, img_format=format)
    phantom_socket.connect()
    click.echo('CONNECTED TO THE PHANTOM CAMERA')

    result = phantom_socket.get(key)
    click.echo('PHANTOM RETURNED:\n\n{}'.format('\n'.join(result)))
    phantom_socket.disconnect()


if __name__ == '__main__':
    command()
