# standard library
import time

from typing import Iterable, List, Dict, Tuple, Any

from unittest import TestCase


def dummy_callback(name: str, parameters: Iterable):
    """
    This is a dummy callback, which will be used as the default value for the MockServer callback parameter.
    Its is possible to specify a callback to be called whenever the mock server receives a new request.

    CHANGELOG

    Added 10.06.201

    :param name:
    :param parameters:
    :return:
    """
    pass


def value_or_default(dictionary: dict, key: str, default: Any):
    """
    Either returns the item of the "dictionary" corresponding to the given "key" or the given default value, if no
    such key exists within the dict.

    CHANGELOG

    Added 14.07.2019

    :param dictionary:
    :param key:
    :param default:
    :return:
    """
    if key in dictionary.keys():
        return dictionary[key]
    else:
        return default

# ###########
# FOR TESTING
# ###########

class MockTestCase(TestCase):
    """
    This is the abstract base class for all TestCases, which in some way have to test the network behaviour of the
    phantom socket object. The class will set up and start a MockServer thread and will relay all requests, that have
    been received by the mock server into the REQUESTS list.

    CHANGELOG

    Added 10.06.2019
    """
    # This is the IP on which the mock server operates on and is needed to connect the phantom socket object
    LOCALHOST_IP = '127.0.0.1'

    # These class variables store the classes of the mock server object and the phantom socket object. Although they
    # dont do that now. When a new TestCase class is being created from this abstract base class, these class variables
    # have to be overwritten with the correct classes.
    # This is necessary to avoid circular import dependencies, the concrete classes cannot be imported into this module
    MOCK_SERVER_CLASS = None
    PHANTOM_SOCKET_CLASS = None

    # This class variable will later contain the mock server object for the TestCase
    MOCK_SERVER = None

    # These lists will contain the requests that have been received by the mock server
    REQUESTS = []
    _REQUESTS = []

    # This is the timeout, after which a call to the "wait_request" method will raise an exception
    REQUEST_TIMEOUT = 5

    @classmethod
    def setUpClass(cls):
        """
        This method will be called before any tests of this class will be executed. It creates and starts a mock
        server thread using the callback which will save all the request received by the mock into a list of this
        class

        CHANGELOG

        Added 10.06.2019

        :return:
        """
        # Starting a mock server
        cls.MOCK_SERVER = cls.MOCK_SERVER_CLASS(
            callback=cls.request_callback
        )
        cls.MOCK_SERVER.start()

    @classmethod
    def tearDownClass(cls):
        """
        This method will be called after all tests of this class have been executed. It terminates the mock server
        thread

        CHANGELOG

        Added 10.06.2019

        :return:
        """
        cls.MOCK_SERVER.stop()

    @classmethod
    def request_callback(cls, command: str, data: List):
        """
        This is the callback, that is being passed to the mock server. The mock server will call that callback every
        time a new request is received using the command of that request as the first parameter and the parameters as
        the second.

        CHANGELOG

        Added 10.06.2019

        :param command:
        :param data:
        :return:
        """
        # When the callback is used within the mock server we are simply going to save the
        data_dict = cls.process_data(data)
        request_tuple = (command, data_dict)
        cls._REQUESTS.append(request_tuple)

    @classmethod
    def process_data(cls, data: List[str]) -> Dict[str, str]:
        """
        Given the list of strings, which represents the parameters to a request's command, this method will turn
        this list into a dict whose values are the parameter names and the values the parameter values.

        CHANGELOG

        Added 10.06.2019

        :param data:
        :return:
        """
        parameter_dict = {}
        for item in data:
            clean_string = item.strip('{').strip('}').strip(',')
            clean_string_split = clean_string.split(':')

            key = clean_string_split[0]
            value = clean_string_split[1]

            parameter_dict[key] = value

        return parameter_dict

    @classmethod
    def wait_request(cls):
        """
        This method blocks the test execution, until a request has been received by the mock server.
        It will raise an Exception, if no request is received after REQUEST_TIMEOUT seconds.

        CHANGELOG

        Added 10.06.2019

        :return:
        """
        start_time = time.time()
        while len(cls.REQUESTS) == len(cls._REQUESTS):
            print(cls._REQUESTS)
            if time.time() - start_time > cls.REQUEST_TIMEOUT:
                raise TimeoutError("The request did not arrive in time")
            time.sleep(0.1)
        cls.REQUESTS = cls._REQUESTS

    @classmethod
    def get_requests(cls) -> List[Tuple[str, Dict[str, str]]]:
        """
        Returns the list of all the requests, which the mock server has received.
        This will be a list of tuples, where each tuple represents one request. The first item of the tuple being the
        name of the command from the request and the second item being a dict with all the parameters to the command

        CHANGELOG

        Added 10.06.2019

        :return:
        """
        return cls.REQUESTS

    @classmethod
    def reset_requests(cls):
        """
        This method resets the list of request to be empty

        CHANGELOG

        Added 10.06.2019

        :return:
        """
        cls._REQUESTS = []
        cls.REQUESTS = []

    def setUp(self):
        """
        This method will be called before every test of this class, that is being executed. It will simply empty the
        requests lists.

        CHANGELOG

        Added 10.06.2019

        :return:
        """
        # At the beginning of each test case, we are going to empty the requests list, so that requests, that have
        # been acquired from other tests will not affect the current one.
        self.reset_requests()

    def get_phantom_socket(self):
        """
        This is a helper method, which will return a properly configured (to connect to the local mock server) phantom
        socket instance (connect not called).

        CHANGELOG

        Added 10.06.2019

        :return:
        """
        return self.PHANTOM_SOCKET_CLASS(self.LOCALHOST_IP)
