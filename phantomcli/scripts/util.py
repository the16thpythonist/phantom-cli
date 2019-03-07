# standard library imports
import logging
from collections import defaultdict


# This will be the translation table, which will be used to return the appropriate constant for defining the logging
# level based on the string passed through the command line option. We are using a default dict, so we do not have to
# deal with a if statement. In case an invalid string is given, the default dict will just return the constant for
# the debug mode, even though the given string isnt even one of its keys.
kwargs = {
    'DEBUG':    logging.DEBUG,
    'INFO':     logging.INFO,
    'WARNING':  logging.WARNING,
    'ERROR':    logging.ERROR
}
logging_config = defaultdict(lambda: logging.DEBUG, **kwargs)

logging_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# We are defining a default dict here to prevent the long if structure to sort out whether a passed format string is
# valid or not. This way, either a valid string is passed and it works or the default option is used anyways.
_formats = {
    'P16':      'P16',
    'P16R':     'P16R',
    'P10':      'P10',
    'P8':       'P8',
    '8':        'P8',
    'P8R':      'P8R',
    '8R':       'P8R',
}
formats = defaultdict(lambda: 'P16', **_formats)