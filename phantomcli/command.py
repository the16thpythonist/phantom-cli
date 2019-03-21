# Standard library imports
import logging
from collections import defaultdict

# Third party imports
import parsimonious


logger = logging.getLogger(__name__)

# ############################################
# DEFINING THE GRAMMAR OF THE PHANTOM PROTOCOL
# ############################################

grammar = parsimonious.grammar.Grammar(r"""
    value       = space (tagged_list / resolution / unsigned / signed / string / hex_number / var_name) space
    unsigned    = ~"[0-9][0-9]*"
    signed      = "-" unsigned
    hex_number  = ~"0x[A-Fa-f0-9]+"
    string      = "\"" text "\""
    resolution  = unsigned space "x" space unsigned
    var_name    = identifier ("." identifier)*
    identifier  = ~"[A-Za-z][A-Za-z0-9]*"
    tagged_list = list_open space key_value ("," space key_value)* space list_close
    list_open   = "{"
    list_close  = "}"
    key_value   = var_name space ":" space value
    text        = ~"[^\"]*"
    space       = ~"\s*"
""")


class Visitor(parsimonious.nodes.NodeVisitor):
    def generic_visit(self, node, children):
        return children if children else None

    def visit_identifier(self, node, children):
        return node.text

    def visit_unsigned(self, node, children):
        return int(node.text)

    def visit_signed(self, node, children):
        return int(node.text)

    def visit_hex_number(self, node, children):
        return int(node.text, 0)

    def visit_string(self, node, children):
        _, text, _ = children
        return text

    def visit_resolution(self, node, children):
        width, _, _, _, height = children
        return (width, height)

    def visit_tagged_list(self, node, children):
        _, _, (key, value), nodes, _, _ = children
        result = {key: value}

        if isinstance(nodes, list):
            for sub_node in nodes:
                _, _, (key, value) = sub_node
                result[key] = value

        return result

    def visit_key_value(self, node, children):
        key, _, _, _, value = children
        return (key, value)

    def visit_var_name(self, node, children):
        return node.text

    def visit_value(self, node, children):
        _, value, _ = children
        return value[0]


def parse_parameters(string):
    logger.debug(string)
    return Visitor().visit(grammar.parse(string))


# ###########################
# DETAILS OF THE V16 PROTOCOL
# ###########################

class ImgFormatsMap:
    """
    This is a static class, that works as a wrapper for the image transfer format functionality. When specifying the
    image transfer format in an actual command call to the camera, their integer representations have to be used, but
    they also have a string name/token these are used when specifying the format as a function/constructor argument in
    the code for example, to make the code more readable and also not have the users have to memorize the uninformative
    integer numbers for each format.

    CHANGELOG

    Added 28.02.2019
    """

    _TOKENS = {
        '272':           'P16',
        '-272':          'P16R',
        '8':             'P8',
        '-8':            'P8R',
        '266':           'P10'
    }
    TOKENS = defaultdict(lambda: 'P16', **_TOKENS)

    _NUMBERS = {
        'P16':          272,
        'P16R':         (-272),
        'P8':           8,
        'P8R':          (-8),
        'P10':          266
    }
    NUMBERS = defaultdict(lambda: 272, **_NUMBERS)

    @classmethod
    def get_token(cls, number):
        """
        Given the number of the format, returns the corresponding string token.

        CHANGELOG

        Added 28.02.2019

        :param number:
        :return:
        """
        return cls.TOKENS[str(number)]

    @classmethod
    def get_number(cls, token):
        """
        Given the string token of a format, returns the corresponding number

        CHANGELOG

        Added 28.02.2019

        :param token:
        :return:
        """
        # The token string is supposed to be case insensitive, so that even if a human types in the letters in lower
        # case the program still knows "what was meant"
        token_upper = token.upper()
        return cls.NUMBERS[token_upper]
