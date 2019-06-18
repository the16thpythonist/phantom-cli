#!/usr/bin/env python3

# standard library imports
import logging

# third party imports
import click
import texttable

# package imports
from phantomcli.network import PhantomSocket
from phantomcli.phantom import PhantomCamera
from phantomcli.scripts.util import logging_config, logging_format, formats
from phantomcli.scripts.util import log_help, format_help


# The list with all the attribute names to be read from the camera
attributes = [
    'info.model',
    'info.name',
    '',
    'info.features',
    'info.imgformats',
    'info.maxcines',
    'info.xmax',
    'info.ymax',
    '',
    'info.snstemp',
    'info.camtemp',
    'info.tepower',
    'info.fanpower',
    '',
    'eth.ip',
    'eth.netmask',
    'eth.broadcast',
    '',
    'defc.res',
    'defc.exp',
    'defc.rate',
    'defc.edrecp'
]


@click.command('connection')
@click.option('--format', '-f', default='P16', help=format_help)
@click.option('--log', '-l', default='ERROR', help=log_help)
@click.argument('ip')
def command(ip, log, format):
    """
    Given the IP ADDRESS of the camera, this will send a series of requests for the most important attributes of the
    camera and then display them in a table to the console. The table will contain the name of the attribute fetched,
    its actual value from the camera and a short description for that attribute.
    """
    # Setting up the logging
    logging.basicConfig(format=logging_format, level=logging_config[log])

    # Creating a new PhantomSocket object, which will be used to communicate with the camera
    phantom_socket = PhantomSocket(ip, img_format=formats[format])
    phantom_socket.connect()
    click.echo('CONNECTED TO THE PHANTOM!')

    # Requesting all the necessary data over the network from the phantom camera
    results = []
    for attribute in attributes:
        # This will insert an empty row in the table formatting, which will just make the table look cleaner
        if attribute == '':
            results.append(['', '', ''])
            continue

        # The get method returns a list with the lines of the response in case of single response values (as all are
        # in this list of attributes) it has the form "attribute name : value" and because we only want the value, we
        # we only use the second part of the split string
        value = phantom_socket.get(attribute)[0]
        value = value.split(':')[1]

        description = PhantomCamera.DESCRIPTIONS[attribute]

        results.append([attribute, value, description])
    click.echo('ALL ATTRIBUTES FETCHED!')

    # formatting the output nicely
    table = texttable.Texttable()
    table.set_deco(texttable.Texttable.HEADER)
    table.set_cols_dtype(['t', 't', 't'])
    table.set_cols_width([15, 20, 39])
    results.insert(0, ['Attribute', 'Value', 'Description'])
    table.add_rows(results)

    table_string = table.draw()
    click.echo('\n%s' % table_string)


if __name__ == '__main__':
    command()
