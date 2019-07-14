# Standard library imports
import struct

from typing import ByteString, Tuple

# third party imports
import numpy as np
import imageio


class PhantomImage:
    """
    This class wraps functionality for dealing with phantom images. Most importantly the function to convert images
    to and from different file formats, including the protocol specific transmission formats

    CHANGELOG

    Added 23.02.2019

    Changed 20.03.2019
    Checking the edge case of what happens when the passed array is one dimensional.

    Changed 12.07.2019
    Added the class variable SUPPORTED_FORMATS, which contains a list of strings, where each string is an identfier
    for one of the transfer formats, which are supported.
    """

    # 12.07.2019
    SUPPORTED_FORMATS = [
        'P16',
        'P16R',
        'P8',
        'P8R',
        'P10',
        'P12L'
    ]

    def __init__(self, array):
        """
        The constructor

        Added 23.02.2019

        :param array:
        """
        self.array = array

        # 20.03.2019
        # In case a one dimensional array is being passed it is being interpreted that the y axis is just 1 pixel wide
        if len(array.shape) == 1:
            self.resolution = (array.shape[0], 1)
        else:
            self.resolution = (array.shape[0], array.shape[1])

    # ###############################
    # CONVERSION TO DIFFERENT FORMATS
    # ###############################

    def to_transfer_format(self, fmt):
        """
        Given either the string or the integer identifier for a transfer format, this method will return the according
        byte string for that format from the image.

        CHANGELOG

        Added 23.02.2019

        Changed 12.07.2019
        Added the P12L format.

        :param fmt:
        :return:
        """
        _methods = {
            272:    self.p16,
            -272:   self.p16,
            8:      self.p8,
            -8:     self.p8,
            266:    self.p10,
            'P16':  self.p16,
            'P16R': self.p16,
            'P8':   self.p8,
            'P8R':  self.p8,
            'P10':  self.p10,
            'P12L': self.p12l
        }
        return _methods[fmt]()

    def p16(self):
        """
        Converts the image to the P16 transfer format, which is essentially just a long byte string, with two bytes for
        each pixel in the image.

        CHANGELOG

        Added 23.02.2019

        Changed 18.03.2019
        Switched to using the struct packing to handle the byte strings.

        :return:
        """
        byte_buffer = []
        with np.nditer(self.array, op_flags=['readwrite'], order='C') as it:
            for x in it:

                # 18.03.2019
                # The format "<" tells that it is little endian byte order and "H" is for short, the datatype with
                # 2 bytes aka 16 bit.
                pixel_bytes = struct.pack('<H', x)
                byte_buffer.append(pixel_bytes)
        return b''.join(byte_buffer)

    def p8(self):
        """
        Converts the image to the P8 transfer format, which is essentially just a long byte string, with ONE byte
        (8 Bit) for each pixel in the image.

        CHANGELOG

        Added 26.02.2019

        Changed 18.03.2019
        Switched to using the struct packing to handle the byte strings.

        :return:
        """
        byte_buffer = []
        with np.nditer(self.array, op_flags=['readwrite'], order='C') as it:
            for x in it:

                # 18.03.2019
                # The format ">" stands for big endian byte order and "B" is for "unsigned char" data type, which has
                # 1 byte aka 8 bit.
                pixel_bytes = struct.pack('>B', x)
                byte_buffer.append(pixel_bytes)
        return b''.join(byte_buffer)

    def p10(self):
        """
        Converts the image to the P10 transfer format.

        CHANGELOG

        Added 26.02.2019

        :return:
        """

        byte_buffer = []
        with np.nditer(self.array, op_flags=['readwrite'], order='C') as it:

            # Make two bytes out of it and then just delete the first 6
            index = 0
            temp = 0
            for x in it:

                temp += int(x)
                temp <<= 10
                index += 1

                if index == 4:
                    temp >>= 10
                    bytes_string = temp.to_bytes(5, 'big')
                    byte_buffer.append(bytes_string)
                    temp = 0
                    index = 0

        return b''.join(byte_buffer)

    def p12l(self):
        """
        Returns the byte string, which is the image converted into P12L transfer format

        CHANGELOG

        Added 12.07.2019

        :return:
        """
        # The P12L format is a 12 Bit transfer format. It is the most practical one, since the bit depth of most of the
        # phantom cameras is 12 Bit. So the transferred data neither looses accuracy (such as with the 10 Bit format)
        # Nor is redundant bits being transmitted (Such as with the 16 Bit format).
        # Since two pixels have 24 Bit, they can be converted into 3 bytes (8x3=24) directly

        byte_buffer = []
        with np.nditer(self.array, op_flags=['readwrite'], order='C') as it:
            while not it.finished:
                temp = int(it[0])
                temp <<= 12
                it.iternext()
                temp |= int(it[0])
                it.iternext()

                # At this moment two pixels are saved in the temp variable (at max 24 bit integer) those can be
                # directly converted into 2 bytes.
                byte_string = temp.to_bytes(3, 'big')
                byte_buffer.append(byte_string)

        return b''.join(byte_buffer)

    # #############
    # CLASS METHODS
    # #############

    @classmethod
    def from_jpeg(cls, file_path):
        """
        Given the path to a JPEG image file, this method will open the image and convert it into a numpy matrix, from
        which a new PhantomImage object is created. This PhantomImage object is returned.

        CHANGELOG

        Added 23.02.2019

        :param file_path:
        :return: PhantomImage
        """
        array = imageio.imread(file_path, pilmode='L')
        return cls(array)

    @classmethod
    def from_p16(cls, raw_bytes, resolution):
        """
        Given a byte string a resolution tuple of two ints, this method will convert it into a PhantomImage object and
        return that.

        CHANGELOG

        Added 23.02.2019

        Changed 18.03.2019
        Switched to using the struct packing to handle the byte strings.

        :param raw_bytes:
        :param resolution:
        :return: PhantomImage
        """
        pixels = []
        for i in range(0, len(raw_bytes), 2):
            bytes_16 = raw_bytes[i:i+2]

            # 18.03.2019
            # The format '<' tells, that it is little endian byte order and "H" is for "short", the datatype with
            # 2 bytes aka 16 bit.
            value = struct.unpack('<H', bytes_16)[0]
            pixels.append(value)
        array = np.array(pixels)
        array = array.reshape(resolution)
        return cls(array)

    @classmethod
    def from_p8(cls, raw_bytes, resolution):
        """
        Given a byte string a resolution tuple of two ints, this method will convert it into a PhantomImage object and
        return that.

        CHANGELOG

        Added 26.02.2019

        :param raw_bytes:
        :param resolution:
        :return:
        """
        pixels = []
        for byte in raw_bytes:
            pixels.append(byte)
        array = np.array(pixels)
        array = array.reshape(resolution)
        return cls(array)

    @classmethod
    def from_p10(cls, raw_bytes, resolution):
        """
        Converts the raw bytes in p10 format into PhantomImage object

        CHANGELOG

        Added 26.02.2019

        Changed 18.03.2019
        Switched to using the struct packing to handle the byte strings.

        :param raw_bytes:
        :param resolution:
        :return:
        """
        mask = 0b1111111111
        pixels = []

        index = 0
        while index < len(raw_bytes):
            _bytes = raw_bytes[index:index+20]
            bytes_value = int.from_bytes(_bytes, 'big')
            _temp = []
            for i in range(16):
                value = bytes_value & mask
                _temp.append(value)
                bytes_value >>= 10
            pixels += reversed(_temp)
            index += 20

        """
        for i in range(0, len(raw_bytes), 4):
            bits_32 = raw_bytes[i:i+4]

            # 18.03.2019
            # The format '>' tells that it is big endian byte order and the 'L' is for the "long" datatype which is
            # 4 byte aka 32 bit
            value = struct.unpack('!L', bits_32)[0]
            value >>= 2

            mask = 0b1111111111
            for i in range(0, 3, 1):
                pixel_value = (value >> 10 * i) & mask
                pixels.append(pixel_value)
        """

        array = np.array(pixels)
        array = array.reshape(resolution)
        return cls(array)

    @classmethod
    def from_p12l(cls, raw_bytes, resolution):
        """
        Returns a new PhantomImage object, which has been created from the given raw bytestring of the image data in
        P12L transfer format.

        CHANGELOG

        Added 12.07.2019

        :param raw_bytes:
        :param resolution:
        :return:
        """
        # This creates a mask with 12 "1"s
        mask = (1 << 12) - 1
        pixels = []
        index = 0
        while index < len(raw_bytes):
            _bytes = raw_bytes[index:index+3]
            _bytes_value = int.from_bytes(_bytes, 'big')
            _pixels = [
                ((_bytes_value >> 12) & mask),
                (_bytes_value & mask)
            ]
            pixels += _pixels
            index += 3

        array = np.array(pixels)
        array = array.reshape(resolution)

        return cls(array)

    @classmethod
    def from_transfer_format(cls, fmt, raw_bytes, resolution):
        """
        Given the raw bytes string received from the socket and the resolution of the image, this method will create
        a new PhantomImage object from that information using the format identified by the given string format token
        name "fmt"

        CHANGELOG

        Added 28.02.2019

        Changed 12.07.2019
        Added the 'P12L' format

        :param fmt:
        :param raw_bytes:
        :param resolution:
        :return:
        """
        _methods = {
            'P16':          cls.from_p16,
            'P16R':         cls.from_p16,
            'P8':           cls.from_p8,
            'P8R':          cls.from_p8,
            'P10':          cls.from_p10,
            'P12L':         cls.from_p12l()
        }
        return _methods[fmt](raw_bytes, resolution)

    @classmethod
    def random(cls, resolution):
        """
        Creates random PhantomImage.

        CHANGELOG

        Added 18.03.2019

        :param resolution:
        :return:
        """
        # This will create the correct base array, which only contains regular 8 bit pixel values (range 0 to 256)
        random_array = np.random.randint(0, 256, resolution)
        # Creating a new PhantomImage object from this array and then returning the Image object
        return cls(random_array)

    # ##############
    # HELPER METHODS
    # ##############

    @classmethod
    def downscale(cls, array, bits=8):
        """
        This method takes an array, which represents an image and scales all the values down to the range between 0
        and 128, which is needed to save the image in the common formats such as jpeg etc.

        :param array:
        :param bits:
        :return:
        """
        downscaled_array = array
        downscaled_array /= np.max(array)
        downscaled_array *= 2**(bits - 1)
        return downscaled_array


class PhantomMedia:
    """
    This class/object will act as the main point of interaction with the phantom imaging module.

    CHANGELOG

    Added 20.05.2019
    """

    def __init__(self):
        pass

    # IMAGE RELATED METHODS
    # ---------------------

    @classmethod
    def create_phantom_image(
            cls,
            data: ByteString,
            resolution: Tuple[int, int],
            transfer_format: str = "P16"
    ) -> PhantomImage:
        """
        Creates a new PhantomImage object from the given data using the given identifier string for the used format to
        correctly interpret the bytes as pixels and the given resolution to correctly set the linebreaks for the pixels
        to create a valid image

        CHANGELOG

        Added 20.05.2019

        :param data:
        :param resolution:
        :param transfer_format:
        :return:
        """
        # Here we simply create a new Phantom image object using the "from_transfer_format" class method the class
        # overs to directly create from raw data.
        phantom_image = PhantomImage.from_transfer_format(transfer_format, data, resolution)
        return phantom_image

    @classmethod
    def load_phantom_image(
            cls,
            path: str,
            resolution: Tuple[int, int],
            transfer_format: str = "P16"
    ) -> PhantomImage:
        """
        Creates a new PhantomImage object by reading the file with the given file path and interpreting the contents as
        a raw bytes string, using the given identifier string for the used format to correctly interpret the bytes as
        pixels and the given resolution to correctly set the linebreaks for the pixels to create a valid image.

        CHANGELOG

        Added 20.05.2019

        :param path:
        :param resolution:
        :param transfer_format:
        :return:
        """
        # First we will load the binary data from the given path and then we will calls the method to create a new
        # phantom image on the raw data
        with open(path, mode="rb") as file:
            data = file.read()
            phantom_image = cls.create_phantom_image(data, resolution, transfer_format)

        return phantom_image
