#!/usr/bin/env python3

# standard library imports
import logging
import time

from collections import defaultdict

# third party imports
import click

# package imports
from phantomcli.network import PhantomSocket
from phantomcli.scripts.util import logging_format, logging_config


@click.command('connection')
@click.option('--log', '-l', default='DEBUG')
@click.argument('ip')
def command(ip, log):
    logging.basicConfig(format=logging_format, level=logging_config[log])

    phantom_socket = PhantomSocket(ip)
    click.echo('CREATED A NEW PHANTOM SOCKET')
    result = phantom_socket.ping()
    if result:
        click.echo('TARGET IP IS PINGABLE!')
    else:
        click.echo('TARGET IP IS UNREACHABLE...')
        return 0

    try:
        phantom_socket.connect()
        click.echo('CONNECTED TO PHANTOM')
    except ModuleNotFoundError as e:
        click.echo('CONNECTION TO PHANTOM FAILES WITH ERROR:\n"{}"'.format(str(e)))

    name = phantom_socket.get('info.name')
    click.echo('PHANTOM IDENTIFIED WITH NAME "{}"'.format(name[0]))


if __name__ == '__main__':
    command()
