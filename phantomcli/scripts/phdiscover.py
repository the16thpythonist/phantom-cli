#!/usr/bin/env python3

# standard library imports
import logging

# third party imports
import click

# package imports
from phantomcli.network import PhantomSocket
from phantomcli.scripts.util import logging_config, logging_format
from phantomcli.scripts.util import log_help


@click.command('phdiscover')
@click.option('--log', '-l', default='ERROR', help=log_help)
def command(log):
    """
    Given the IP ADDRESS of the camera, this will open a secondary channel to the camera to receive the raw data of
    the current frame. Once the data has been transmitted completely a new window will open, displaying the image from
    the camera.
    """
    logging.basicConfig(
        format=logging_format,
        level=logging_config[log]
    )

    click.echo("Sending a discovery broadcast into the network...")
    click.echo("Waiting {timeout} seconds for responses".format(timeout=PhantomSocket.DISCOVERY_TIMEOUT))

    discovery_results = PhantomSocket.discover()

    for camera in discovery_results:
        string_template = "\nPhantom Camera using {protocol}:\n" \
                          "     IP address:          {ip}\n" \
                          "     Listening on PORT:   {port}\n" \
                          "     Hardware version:    {hwver}\n" \
                          "     Serial number:       {serial}\n"
        string = string_template.format(**camera)
        click.echo(string)


if __name__ == '__main__':
    command()
