# Standard library import
import os

from unittest import TestCase

# third party imports
import imageio
import numpy as np

# Package import
from phantomcli.network import PhantomSocket
from phantomcli.network import PhantomMockServer
from phantomcli.image import PhantomImage


class TestPhantomImage(TestCase):

    FOLDER_PATH = os.path.dirname(os.path.abspath(__file__))
    IMAGE_PATH = os.path.join(FOLDER_PATH, 'sample.jpg')

    def test_sample_image_correctly_read_from_jpeg(self):
        expected_image = imageio.imread(self.IMAGE_PATH, pilmode='L')
        phantom_image = PhantomImage.from_jpeg(self.IMAGE_PATH)
        self.assertTrue(np.alltrue(expected_image == phantom_image.array))

    def test_image_conversion_to_p16_working(self):
        image_array = np.array([8, 7])
        expected_bytes = b'\x00\x08\x00\x07'

        phantom_image = PhantomImage(image_array)
        actual_bytes = phantom_image.p16()
        self.assertEqual(expected_bytes, actual_bytes)

    def test_image_creation_from_p16_working(self):
        expected_array = np.array([[8, 7], [2, 4]])
        image_bytes = b'\x00\x08\x00\x07\x00\x02\x00\x04'

        phantom_image = PhantomImage.from_p16(image_bytes, (2, 2))
        self.assertTrue(np.alltrue(expected_array == phantom_image.array))

    def test_sample_image_conversion_between_p16_and_jpeg(self):
        expected_array = imageio.imread(self.IMAGE_PATH, pilmode='L')

        # First we create a phantom image from the file path, then convert it to p16 convert it back and see if it
        # still is the same image
        phantom_image = PhantomImage.from_jpeg(self.IMAGE_PATH)
        phantom_image = PhantomImage.from_p16(phantom_image.p16(), phantom_image.resolution)
        self.assertTrue(np.alltrue(expected_array == phantom_image.array))
