#!/usr/bin/env python3

# standard library imports
import logging

# third party imports
import click

# package imports
from phantomcli.network import PhantomSocket

from phantomcli.scripts.util import logging_config
from phantomcli.scripts.util import _modes
from phantomcli.scripts.util import log_help


@click.command('connection')
@click.option('--log', '-l', default='ERROR', help=log_help)
@click.argument('ip')
@click.argument('mode')
def command(mode, ip, log):
    """
    Given the IP ADDRESS of the camera, to which you are connected and ACQUISITION MODE into which you want to put the
    camera, this command will send the according request to the camera.

    These are the possible strings to identify a mode:
    - standard / S
    - standard-binned / SB
    - high-speed / HS
    - high-speed-binned / HSB
    """
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging_config[log])

    # Using the default dict to get a valid format string no matter what
    phantom_socket = PhantomSocket(ip)
    phantom_socket.connect()
    click.echo('CONNECTED TO THE PHANTOM CAMERA')

    mode_identifier = _modes[mode]
    phantom_socket.set_mode(mode_identifier)
    click.echo('PHANTOM WILL TRANSIT INTO THE MODE "%s" NOW!' % mode_identifier)
    click.echo('THIS WILL CAUSE A REBOOT OF THE CAMERA, SO PLEASE HAVE PATIENCE')
    click.echo('IN CASE A CONNECTION CANNOT BE ESTABLISHED EVEN AFTER SOME TIME, HARD RESET THE CAMERA')
    click.echo('AFTER THE HARD RESET, THE MODE SHOULD BE CHANGED')
    phantom_socket.disconnect()


if __name__ == '__main__':
    command()
