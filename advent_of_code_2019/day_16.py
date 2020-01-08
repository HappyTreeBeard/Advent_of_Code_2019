import unittest
from itertools import cycle
from pathlib import Path
from typing import List


def generate_phase(input_list: List[int], base_pattern: List[int]) -> List[int]:
    phase_list = list()
    for index in range(len(input_list)):
        # Each element in the new list is built by multiplying every value in the input list by a value in a
        # repeating pattern and then adding up the results. So, if the input list were 9, 8, 7, 6, 5 and the pattern
        # for a given element were 1, 2, 3, the result would be 9*1 + 8*2 + 7*3 + 6*1 + 5*2 (with each input element
        # on the left and each value in the repeating pattern on the right of each multiplication). Then,
        # only the ones digit is kept: 38 becomes 8, -17 becomes 7, and so on.
        pattern = pattern_generator(pattern=base_pattern, index=index)

        # phase_sum = 0
        # for input_value, pattern_value in zip(input_list, pattern):
        #     phase_sum += input_value * pattern_value
        phase_sum = sum([x * y for x, y in zip(input_list, pattern)])

        phase = abs(phase_sum) % 10  # Only keep the 1s digit and ignore sign
        phase_list.append(phase)

    return phase_list


def pattern_generator(pattern: List[int], index: int) -> List[int]:
    # The base pattern is 0, 1, 0, -1. Then, repeat each value in the pattern a number of times equal to the position
    # in the output list being considered. Repeat once for the first element, twice for the second element,
    # three times for the third element, and so on. So, if the third element of the output list is being calculated,
    # repeating the values would produce: 0, 0, 0, 1, 1, 1, 0, 0, 0, -1, -1, -1.

    # When applying the pattern, skip the very first value exactly once. (In other words, offset the whole pattern
    # left by one.)

    pattern_cycle = cycle(pattern)
    offset = 1  # Offset to skip the first value
    while True:
        next_value = next(pattern_cycle)
        num_repeat_values = 1 + index - offset
        offset = 0  # The offset is only applied for the first index
        for _ in range(num_repeat_values):
            yield next_value


class Day16Tests(unittest.TestCase):

    @staticmethod
    def build_pattern_list(pattern: List[int], index: int, input_length: int):
        actual_pattern = list()
        for pattern_value in pattern_generator(pattern=pattern, index=index):
            actual_pattern.append(pattern_value)
            if len(actual_pattern) >= input_length:
                break
        return actual_pattern

    def test_generate_pattern_at_index(self):
        input_length = 8
        pattern = [0, 1, 0, -1]
        pattern_index_0 = [1, 0, -1, 0, 1, 0, -1, 0]
        pattern_index_1 = [0, 1, 1, 0, 0, -1, -1, 0]

        actual_pattern = self.build_pattern_list(pattern=pattern, index=0, input_length=input_length)
        self.assertListEqual(pattern_index_0, actual_pattern)

        actual_pattern = self.build_pattern_list(pattern=pattern, index=1, input_length=input_length)
        self.assertListEqual(pattern_index_1, actual_pattern)

    def test_part1_example1(self):
        input_signal = '12345678'
        input_list = [int(x) for x in input_signal]
        pattern = [0, 1, 0, -1]
        # After 1 phase: 48226158
        # After 2 phases: 34040438
        # After 3 phases: 03415518
        # After 4 phases: 01029498
        expected_phase_list = ['48226158', '34040438', '03415518', '01029498']
        for expected_phase_str in expected_phase_list:
            expected_phase = [int(x) for x in expected_phase_str]
            actual_phase = generate_phase(input_list=input_list, base_pattern=pattern)
            self.assertListEqual(expected_phase, actual_phase)
            input_list = actual_phase


def day_16(txt_path: Path) -> list:
    # Load puzzle input. Single row of digits representing a list of integers.
    with open(str(txt_path), mode='r', newline='') as f:
        row = f.readline()
    signal = [int(x) for x in row.strip()]

    # After 100 phases of FFT, what are the first eight digits in the final output list?
    base_pattern = [0, 1, 0, -1]
    for _ in range(100):
        signal = generate_phase(input_list=signal, base_pattern=base_pattern)
    first_8_digits = [str(x) for x in signal[0:8]]
    part_1_answer = ''.join(first_8_digits)
    part_2_answer = None

    return [part_1_answer, part_2_answer]


def main():
    txt_path = Path(Path(__file__).parent, 'input_data', 'day_16_input.txt')
    answer = day_16(txt_path=txt_path)
    print(f'Day 16 Answers: {repr(answer)}')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Day16Tests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    main()
