#!/usr/bin/env python3

# standard library imports
import logging

# third party imports
import click

# package imports
from phantomcli.network import PhantomSocket
from phantomcli.scripts.util import logging_config, formats
from phantomcli.scripts.util import format_help, log_help


@click.command('connection')
@click.option('--format', '-f', default='P16', help=format_help)
@click.option('--log', '-l', default='ERROR', help=log_help)
@click.argument('ip')
@click.argument('key')
def command(key, ip, log, format):
    """
    Given the IP ADDRESS of the camera, to which you are connected and the ATTRIBUTE NAME of the attribute you want
    to access a command will be sent to the camera, returning the value of the requested attribute and displaying it
    in the console.
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
