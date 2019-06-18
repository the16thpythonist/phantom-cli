# standard library imports
import os

# third party imports

# package imports
from phantomcli.image import PhantomImage


FOLDER_PATH = os.path.dirname(os.path.abspath(__file__))


# ##############
# THE BASE CLASS
# ##############


class PhantomCamera:
    """
    This is an abstract base class defining general functionality for a phantom camera

    CHANGELOG

    Added 21.02.2019
    """

    # SENSOR INFORMATION FIELDS
    # -------------------------

    SENSOR_INFO_DESCRIPTIONS = {
        'info.sensor':              'Integer Type of sensor used',
        'info.snsversion':          'Version number of the sensor',
        'info.cfa':                 'Integer type of color filter deposited within the sensor',
        'info.filter':              'Integer Type of additional filer used'
    }

    # The default values to be returned by the mock
    SENSOR_INFO_DEFAULT = {
        'info.sensor':              1,
        'info.snsversion':          13302,
        'info.cfa':                 1,
        'info.filter':              1
    }

    # ########################################
    # VERSION AND CAMERA IDENTIFICATION FIELDS
    # ########################################

    IDENTIFICATION_INFO_DESCRIPTIONS = {
        'info.hwver':               'Current hardware version integer',
        'info.kernel':              'Current kernel version integer',
        'info.swver':               'Current firmware version integer',
        'info.xver':                'Current FPGA version integer',
        'info.model':               'String name of the camera model',
        'info.pver':                'Protocol version. Has to be 16',
        'info.sver':                'System (which is kernel and filesystem) release number',
        'info.serial':              'Serial number of the camera',
        'info.name':                'string name, the camera is operating under'
    }

    IDENTIFICATION_INFO_DEFAULT = {
        'info.hwver':               1200,
        'info.kernel':              1200,
        'info.swver':               1200,
        'info.xver':                34,
        'info.model':               'Phantom v2632',
        'info.pver':                16,
        'info.sver':                78,
        'info.serial':              146299363572937,
        'info.name':                'MockPhantom'
    }

    # ########################
    # CAPABILITIES INFO FIELDS
    # ########################

    CAPABILITIES_INFO_DESCRIPTIONS = {
        'info.features':            'A string of space-separated tokens, each indicating a supported feature of the '
                                    'camera',
        'info.imgformats':          'A string with all the image formats supported by the "img" command',
        'info.videosystems':        'String list of formats supported by on the video output',
        'info.maxcines':            'Integer count for the maximum number of cines that can be allocated at the '
                                    'same time',
        'info.ymax':                'Maximum horizontal resolution in pixels',
        'info.xmax':                'Maximum vertical resolution in pixels',
        'info.xinc':                'Vertical increment number. All valid vertical resolution settings have to be a '
                                    'multiple of the increment',
        'info.yinc':                'Horizontal increment number. All valid horizontal resolution setting have to be '
                                    'a multiple of the increment',
        'info.kernsz':              'Size of the acquisition kernel in pixels',
        'info.memsz':               'Size of the installed internal memory of the camera in megabytes',
        'info.cinemem':             'Total amount of image memory available for storing cines in megabytes',
        'info.mdepths':             'Bit mask describing the available memory depths in the camera, if the n-th byte '
                                    'is set, then image data can ve acquired using an n bits pixel size',
        'info.minexp':              'The minimum exposure time the camera is capable if in nano seconds',
        'info.xblock':              'The number of x pixels the camera reads in one clock cycle',
        'info.yblock':              'The number of y pixels the camera reads in one clock cycle',
        'info.pixps':               'Time to read one pixel in pico seconds',
        'info.minfrate':            'Minimum framerate in frames per second',
        'info.maxrate':             'Maximum framerate in frames per second',
        'info.rtopacket':           'Size of one packet sent over the network in bytes',
        'info.rtobyteps':           'Duration of sending one byte in pico seconds',
        'info.rto_channels':        'Number of RTO channels'
    }

    CAPABILITIES_INFO_DEFAULT = {
        'info.features':            ' bref atrig lowexp ',
        'info.imgformats':          'P16 P16R P10 P8 P8R',
        'info.maxcines':            1600
    }

    # ###############################
    # CAMERA STATUS MONITORING FIELDS
    # ###############################

    STATUS_INFO_DESCRIPTIONS = {
        'info.snstemp':             'The temperature at which the sensor dies',
        'info.tepower':             'Amount of power used by the sensor thermoelectric cooler as a percentage of full '
                                    'cooling power. Negative power levels indicate a heating instead of a cooling',
        'info.camtemp':             'Camera temperature measured inside the body',
        'info.fanpower':            'Fan speed as percentage of maximum speed',
        'info.batti':               'Battery current in milli amps',
        'info.battv':               'Battery voltage in milli volts',
        'info.batttimer':           'Number if seconds until camera will turn off by itself',
        'info.genlockstat':         'State of genlock system'
    }

    STATUS_INFO_DEFAULT = {
        'info.snstemp':             60,
        'info.tepower':             12,
        'info.fanpower':            32,
        'info.camtemp':             45,
        'info.batti':               1200,
        'info.battv':               1370,
    }

    # ####################################
    # ETHERNET CONFIGURATION OF THE CAMERA
    # ####################################

    ETHERNET_DESCRIPTIONS = {
        'eth.ip':                   'The string IP address of the camera',
        'eth.netmask':              'The string network mask used',
        'eth.broadcast':            'The string broadcast mask',
        'eth.gateway':              'string IP address of default gateway',
        'eth.mtu':                  'MTU used by the camera',
        'eth.xip':                  'string IP address for 10G connection',
        'eth.xnetmask':             'String network mask for 10G connection',
        'eth.xbroadcast':           'String Broadcast mask for 10G connection'
    }

    ETHERNET_DEFAULT = {
        'eth.ip':                   '127.0.0.1',
        'eth.netmask':              '255.255.0.0',
        'eth.broadcast':            '127.0.0.1',
    }

    # ###############################
    # IMAGE CAPTURE PROCESS OF CAMERA
    # ###############################

    CAPTURE_PROCESS_DESCRIPTIONS = {
        'defc.res':                 'The resolution of the image as a string',
        'defc.rate':                'Frame rate in pictures per second',
        'defc.exp':                 'Exposure time in nano seconds',
        'defc.edrecp':              'EDR exposure time in nano seconds',
        'defc.ptframes':            'Number of post trigger frames',
        'defc.shoff':               'Shutter off',
        'defc.ramp':                'Frame rate ramping specification string',
        'defc.bcount':              'Number of frames per burst',
        'defc.ptframes':            'The amount of frames to record after a trigger command',
    }

    CAPTURE_PROCESS_DEFAULT = {
        'defc.res':                 '1500 x 1000',
        'defc.exp':                 10000000,
        'defc.rate':                1000000,
        'defc.edrecp':              100,
        'defc.ptframes':            100
    }

    # ########################
    # CINE STATE OF THE CAMERA
    # ########################

    CINE_DESCRIPTIONS = {
        'c1.sate':                  'The state of the cine',
    }

    CINE_DEFAULT = {
        'c1.state':                 'STR'
    }

    # ##############################
    # MERGING ALL THE DICTS INTO ONE
    # ##############################

    DESCRIPTIONS = {
        **SENSOR_INFO_DESCRIPTIONS,
        **CAPABILITIES_INFO_DESCRIPTIONS,
        **IDENTIFICATION_INFO_DESCRIPTIONS,
        **STATUS_INFO_DESCRIPTIONS,
        **ETHERNET_DESCRIPTIONS,
        **CAPTURE_PROCESS_DESCRIPTIONS,
        **CINE_DESCRIPTIONS
    }

    DEFAULTS = {
        **SENSOR_INFO_DEFAULT,
        **IDENTIFICATION_INFO_DEFAULT,
        **CAPABILITIES_INFO_DEFAULT,
        **CAPTURE_PROCESS_DEFAULT,
        **STATUS_INFO_DEFAULT,
        **ETHERNET_DEFAULT,
        **CINE_DEFAULT
    }

    # ##################
    # ACTUAL IMAGES DATA
    # ##################

    SAMPLE_IMAGE_PATH = os.path.join(FOLDER_PATH, 'sample.jpg')

    # NETWORK RELATED ADDITIONAL FIELD
    # --------------------------------

    DEFAULT_CONTROL_PORT = 7115

    # ###########
    # THE METHODS
    # ###########

    def __init__(
            self,
            control_port: int = DEFAULT_CONTROL_PORT
    ):
        """
        The constructor

        CHANGELOG

        Added 22.02.2019

        Changed 01.03.2019
        Added the attribute values, which will contain a copy of the DEFAULTS array, which contains the initial values
        to all the internal structures of the phantom. We need the actual values now because by using "set" commands it
        should be possible to modify the attributes of a Camera instance
        """
        # 01.03.2019
        # So the values can be modified by a set command
        self.values = self.DEFAULTS.copy()

        # 20.05.2019
        self.port = control_port

    # #################
    # CAMERA OPERATIONS
    # #################

    def get(self, structure_name):
        """
        Returns the default value for that particular structure

        CHANGELOG

        Added 22.02.2019

        Changed 01.03.2019
        Instead of grabbing the value directly from the static DEFAULTS dict, it is now being taken from the "values"
        attribute of the phantom instance. This way the values can reflect a change through a set command

        :param structure_name:
        :return:
        """
        return '%s : %s' % (structure_name, self.values[structure_name])

    def set(self, structure_name, value):
        """
        Set a new value to one of the cameras attributes

        CHANGELOG

        Added 01.03.2019

        :param structure_name:
        :param value:
        :return:
        """
        if structure_name in self.values.keys():
            self.values[structure_name] = value
        else:
            raise KeyError('Phantom does not have an attribute %s' % structure_name)

    def grab(self):
        # TODO: Make it return a randomly generated static image
        raise NotImplementedError()

    def grab_sample(self):
        """
        Returns a PhantomImage object for the sample image in the project folder

        CHANGELOG

        Added 23.02.2019

        :return: PhantomImage
        """
        # Loading a new PhantomImage from the given sample JPEG image
        phantom_image = PhantomImage.from_jpeg(self.SAMPLE_IMAGE_PATH)
        return phantom_image

    def grab_random(self):
        resolution = self.get_resolution()
        phantom_image = PhantomImage.random(resolution)
        return phantom_image

    def get_resolution(self):
        """
        Returns the resolution of the camera as a tuple (x, y) specifically

        CHANGELOG

        Added 18.03.2019

        :return:
        """
        # The resolution of the Phantom camera is stored in the "defc.res" field in the form of a string which looks
        # like this "x_res x y_res". The two values being separated by an "x" character
        resolution_string = self['defc.res']
        resolution_string = resolution_string.strip()
        resolution = resolution_string.split('x')
        return int(resolution[0]), int(resolution[1])

    # ##################
    # DICT MAGIC METHODS
    # ##################

    # These methods will implement behaviour which will make any instance of the PhantomCamera accessible like a
    # python dict object itself.

    def __getitem__(self, item):
        """
        Attempts to return the corresponding value of the internal "values" array for the given key "item".
        If the key does not exists in that dict, will raise a KeyError like usual

        CHANGELOG

        Added 18.03.2019

        :param item:
        :return:
        """
        return self.values[item]

    def __setitem__(self, key, value):
        """
        Attempts to set a new value to the given key
        Will raise a key error if the phantom camera is not defined with an attribute like that

        CHANGELOG

        Added 18.03.2019

        :param key:
        :param value:
        :return:
        """
        if key in self.values.keys():
            self.values[key] = value
        else:
            raise KeyError('A PhantomCamera has no attribute with name "%s"' % key)

    # ##############
    # STATIC METHODS
    # ##############

    @classmethod
    def all_properties(cls):
        """
        returns a list of strings, where each string is the name of a readable field/structure of the phantom camera

        CHANGELOG

        Added 21.02.2019

        :return:
        """
        # This list should contain all the static description dictionaries for the variables/structures of the phantom
        # camera. The final list is being assembled from the keys of each of these dicts
        description_dicts = [
            cls.SENSOR_INFO_DESCRIPTIONS,
            cls.STATUS_INFO_DESCRIPTIONS,
            cls.IDENTIFICATION_INFO_DESCRIPTIONS,
            cls.CAPABILITIES_INFO_DESCRIPTIONS,
            cls.ETHERNET_DESCRIPTIONS
        ]
        properties = []
        for description_dict in description_dicts:
            key_list = list(description_dict.keys())
            properties += key_list
        return properties
