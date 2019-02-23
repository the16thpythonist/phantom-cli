# Standard library imports

# third party imports
import numpy as np
import imageio


class PhantomImage:
    """
    This class wraps functionality for dealing with phantom images. Most importantly the function to convert images
    to and from different file formats, including the protocol specific transmission formats

    CHANGELOG

    Added 23.02.2019
    """

    def __init__(self, array):
        self.array = array
        self.resolution = array.shape

    # ###############################
    # CONVERSION TO DIFFERENT FORMATS
    # ###############################

    def p16(self):
        """
        Converts the image to the P16 transfer format, which is essentially just a long byte string, with two bytes for
        each pixel in the image.

        CHANGELOG

        Added 23.02.2019

        :return:
        """
        byte_buffer = []
        with np.nditer(self.array, op_flags=['readwrite'], order='C') as it:
            for x in it:
                pixel_bytes = bytes([0, x])
                byte_buffer.append(pixel_bytes)
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

        :param raw_bytes:
        :param resolution:
        :return: PhantomImage
        """
        pixels = []
        for i in range(0, len(raw_bytes), 2):
            bytes_16 = raw_bytes[i:i+2]
            value = int.from_bytes(bytes_16, byteorder='big')
            pixels.append(value)
        array = np.array(pixels)
        array = array.reshape(resolution)
        return cls(array)
