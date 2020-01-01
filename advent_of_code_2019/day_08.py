import unittest
from collections import Counter
from enum import IntEnum
from pathlib import Path
from typing import Optional

import numpy as np
from dataclasses import dataclass


class PixelColor(IntEnum):
    BLACK = 0
    WHITE = 1
    TRANSPARENT = 2


@dataclass
class DecodedImage(object):
    image_data: np.ndarray

    def render(self) -> np.ndarray:
        num_layers, num_row, num_col = self.image_data.shape
        final_render = np.zeros(shape=(num_row, num_col), dtype=np.int)

        for col_i in range(num_col):
            for row_i in range(num_row):
                for layer_i in range(num_layers):
                    pixel = self.image_data[layer_i, row_i, col_i]
                    if pixel != PixelColor.TRANSPARENT:
                        # First non-transparent color
                        final_render[row_i, col_i] = pixel
                        # Additional layers will be occluded and can be skipped.
                        break
        return final_render


def decode_image_from_digital_sending_network(data: str, num_row: int, num_col: int) -> DecodedImage:
    # Images are sent as a series of digits that each represent the color of a single pixel. The digits fill each row
    # of the image left-to-right, then move downward to the next row, filling rows top-to-bottom until every pixel of
    # the image is filled.

    # Each image actually consists of a series of identically-sized layers that are filled in this way. So,
    # the first digit corresponds to the top-left pixel of the first layer, the second digit corresponds to the pixel
    # to the right of that on the same layer, and so on until the last digit, which corresponds to the bottom-right
    # pixel of the last layer.

    num_layers = len(data) / (num_row * num_col)
    if num_layers != int(num_layers):
        raise ValueError(f'The provided image data is not divisible by the specified number of rows and columns.'
                         f' num_row: {num_row}, num_col: {num_col}, len(data): {len(data)}, layers: {num_layers}')

    num_layers = int(num_layers)
    image_data = np.zeros(shape=(num_layers, num_row, num_col), dtype=np.int)

    row_index = 0
    col_index = 0
    layer_index = 0

    for pixel_str in data:
        image_data[layer_index, row_index, col_index] = int(pixel_str)
        col_index += 1
        if col_index >= num_col:
            col_index = 0
            row_index += 1
        if row_index >= num_row:
            row_index = 0
            layer_index += 1
    return DecodedImage(image_data=image_data)


class Day8Tests(unittest.TestCase):

    def test_part_1_example_1(self):
        data = '123456789012'
        num_row = 2
        num_col = 3
        expected_data = [
            [
                [1, 2, 3],
                [4, 5, 6],
            ],
            [
                [7, 8, 9],
                [0, 1, 2],
            ],
        ]
        expected_np_data = np.array(expected_data)
        decoded_image = decode_image_from_digital_sending_network(data=data, num_row=num_row, num_col=num_col)
        self.assertEqual(decoded_image.image_data.shape, expected_np_data.shape)
        actual_data = decoded_image.image_data.tolist()
        assert isinstance(actual_data, list)
        self.assertListEqual(actual_data, expected_data)
        self.assertListEqual(list(decoded_image.image_data[0].tolist()), expected_data[0])

    def test_part_2_example_1(self):
        data = '0222112222120000'
        num_row = 2
        num_col = 2
        expected_render = [
            [0, 1],
            [1, 0],
        ]
        decoded_image = decode_image_from_digital_sending_network(data=data, num_row=num_row, num_col=num_col)
        actual_render = decoded_image.render().tolist()
        assert isinstance(actual_render, list)
        self.assertListEqual(actual_render, expected_render)


def day_8(txt_path: Path) -> list:
    # Load puzzle input. Single string representing single digit pixel values
    with open(str(txt_path), mode='r', newline='') as f:
        row = f.readline()

    # Trim the newline characters or spaces
    data = row.strip()

    # The image you received is 25 pixels wide and 6 pixels tall.
    num_row = 6
    num_col = 25

    # Decode the image data into a stack of images.
    decoded_image = decode_image_from_digital_sending_network(data=data, num_row=num_row, num_col=num_col)

    # To make sure the image wasn't corrupted during transmission, the Elves would like you to find the layer that
    # contains the fewest 0 digits. On that layer, what is the number of 1 digits multiplied by the number of 2 digits?

    fewest_num_zero_layer_counter: Optional[Counter] = None
    fewest_num_zero_found = 0  # Number of zeros found in the layer with the fewest number of zeros

    num_layers, num_row, num_col = decoded_image.image_data.shape
    for layer_index in range(num_layers):
        layer: np.ndarray = decoded_image.image_data[layer_index]
        # Build a Counter object to build a dictionary to store the number of occurrences for each pixel value.
        pixels = layer.flatten()  # 2D to 1D array, order does not matter.
        counter = Counter(pixels)
        num_zeros_found = counter[0]

        if fewest_num_zero_layer_counter is None or num_zeros_found < fewest_num_zero_found:
            fewest_num_zero_layer_counter = counter
            fewest_num_zero_found = num_zeros_found

    # Part 1: What is the number of 1 digits multiplied by the number of 2 digits?
    part_1_answer = fewest_num_zero_layer_counter[1] * fewest_num_zero_layer_counter[2]

    image = decoded_image.render()

    # Part 2: What message is produced after decoding your image?
    print(image)
    # TODO: Convert a 6x5 binary image of an upper case letter into a string
    part_2_answer = None
    return [part_1_answer, part_2_answer]


def main():
    txt_path = Path(Path(__file__).parent, 'input_data', 'day_08_input.txt')

    answer = day_8(txt_path=txt_path)
    print(f'Day 8 Answers: {repr(answer)}')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Day8Tests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    main()
