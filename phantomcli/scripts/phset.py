#!/usr/bin/env python3

# standard library imports
import logging
import time

from collections import defaultdict

# third party imports
import click
import texttable

# package imports
from phantomcli.network import PhantomSocket
from phantomcli.scripts.util import logging_config, logging_format, formats
from phantomcli.phantom import PhantomCamera


@click.command('connection')
@click.option('--format', '-f', default='P16')
@click.option('--log', '-l', default='DEBUG')
@click.argument('ip')
@click.argument('key')
@click.argument('value')
def command(value, key, ip, log, format):
    # Setting up the logging to the console
    logging.basicConfig(format=logging_format, level=logging_config[log])

    # Creating the PhantomSocket object to communicate with the camera
    phantom_socket = PhantomSocket(ip, img_format=formats[format])
    phantom_socket.connect()
    click.echo('CONNECTED TO THE PHANTOM')

    # Actually calling the set command
    phantom_socket.set(key, value)
    response_list = phantom_socket.get(key)
    click.echo('SET THE NEW VALUE, RESPONSE TO "GET %s":\n%s' % (key, response_list))


if __name__ == '__main__':
    command()
