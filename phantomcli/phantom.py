
# ##############
# THE BASE CLASS
# ##############


class PhantomCamera:
    """
    This is an abstract base class defining general functionality for a phantom camera

    CHANGELOG

    Added 21.02.2019
    """

    # #########################
    # SENSOR INFORMATION FIELDS
    # #########################

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

    # ##############################
    # MERGING ALL THE DICTS INTO ONE
    # ##############################

    DESCRIPTIONS = {
        **SENSOR_INFO_DESCRIPTIONS,
        **CAPABILITIES_INFO_DESCRIPTIONS,
        **IDENTIFICATION_INFO_DESCRIPTIONS,
        **STATUS_INFO_DESCRIPTIONS,
        **ETHERNET_DESCRIPTIONS,
    }

    DEFAULTS = {
        **SENSOR_INFO_DEFAULT,
        **IDENTIFICATION_INFO_DEFAULT
    }

    # ###########
    # THE METHODS
    # ###########

    def __init__(self):
        pass

    def get(self, structure_name):
        """
        Returns the default value for that particular structure

        :param structure_name:
        :return:
        """
        return self.DEFAULTS[structure_name]

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
