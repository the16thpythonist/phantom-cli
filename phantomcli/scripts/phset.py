#!/usr/bin/env python3

# standard library imports
import logging

# third party imports
import click

# package imports
from phantomcli.network import PhantomSocket
from phantomcli.scripts.util import logging_config, logging_format, formats
from phantomcli.scripts.util import log_help, format_help


@click.command('connection')
@click.option('--format', '-f', default='P16', help=format_help)
@click.option('--log', '-l', default='ERROR', help=log_help)
@click.argument('ip')
@click.argument('key')
@click.argument('value')
def command(value, key, ip, log, format):
    """
    Given the IP ADDRESS of the camera, the ATTRIBUTE NAME of the attribute to be changed and the new VALUE to be set
    this will send a command to the phantom, changing the value of the requests attribute to the new given value.
    """
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
