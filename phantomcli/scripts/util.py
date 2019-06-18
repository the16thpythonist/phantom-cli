# standard library imports
import logging
from collections import defaultdict

# local imports

from phantomcli.network import PhantomSocket


# ##############
# LOGGING CONFIG
# ##############

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


###########################
# HANDLING TRANSFER FORMATS
###########################

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

##############################
# HANDLING ACQUISITION MODES #
##############################

# This is a mapping from the strings, the user can pass as identifiers for acquisition modes to the actual constants
# needed to be passed to the according method of the phantom socket object.
_modes = {
    'S':                    PhantomSocket.MODE_STANDARD,
    'standard':             PhantomSocket.MODE_STANDARD,
    'SB':                   PhantomSocket.MODE_STANDARD_BINNED,
    'standard-binned':      PhantomSocket.MODE_STANDARD_BINNED,
    'HS':                   PhantomSocket.MODE_HIGH_SPEED,
    'high-speed':           PhantomSocket.MODE_HIGH_SPEED,
    'HSB':                  PhantomSocket.MODE_HIGH_SPEED_BINNED,
    'high-speed-binned':    PhantomSocket.MODE_HIGH_SPEED_BINNED
}

# ##################
# COMMAND HELP TEXTS
# ##################

# Many of the commands use the same options, to is makes sense to define the help texts here for them all instead of
# copy pasting them for each of them...

format_help = "The transfer format to be used, when transmitting image data. " \
              "The possible options are 'P10', 'P16' and 'P8'. Default is 'P16' with 16 bit per pixel"

log_help = "The level of logging to be displayed in the console output. The options are 'ERROR' for only displaying " \
           "error messages, 'INFO' for log messages marking important steps in the program execution or 'DEBUG' " \
           "for displaying all log messages. Default is 'ERROR'"

xnetwork_help = "Setting this flag will enable the transmission using the 10G interface. Make sure, that you are " \
                "indeed connected using the 10G ethernet interface before setting this flag."
