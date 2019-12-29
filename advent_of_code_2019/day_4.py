import unittest
from collections import defaultdict

from pathlib import Path
from typing import List, Dict


def is_valid_password_part_1(value: int) -> bool:
    # Rules
    # 1) It is a six-digit number.
    # 2) The value is within the range given in your puzzle input.
    # 3) Two adjacent digits are the same (like 22 in 122345).
    # 4) Going from left to right, the digits never decrease; they only ever increase or stay
    #    the same (like 111123 or 135679).

    # Break the integer value into a list of int representing each digit
    digits = [int(digit) for digit in str(value)]

    num_match_adjacent_digits = 0  # Number of adjacent digits that match

    # Iterate through each digit but skip the last digit
    for i in range(len(digits) - 1):
        x0 = digits[i]
        x1 = digits[i + 1]
        if x0 == x1:
            num_match_adjacent_digits += 1

        dx = x1 - x0
        # Going from left to right, the digits never decrease; they only ever increase or stay the same
        if dx < 0:
            # The digits decreased. This is not a valid password
            return False

    # At least 1 pair of adjacent digits should be equal
    return num_match_adjacent_digits >= 1


def is_valid_password_part_2(value: int) -> bool:
    # New rule for part 2
    # 5) The two adjacent matching digits are not part of a larger group of matching digits.

    # Break the integer value into a list of int representing each digit
    digits = [int(digit) for digit in str(value)]

    # Build a dictionary of adjacent matching digits and how many times the match is found
    # where the key is the digit value and the value is the number of occurrences.
    matching_digit_occurrence: Dict[int, int] = defaultdict(int)

    # Iterate through each digit but skip the last digit
    for i in range(len(digits) - 1):
        x0 = digits[i]
        x1 = digits[i + 1]
        if x0 == x1:
            # Increment the number of times an matching adjacent pair was found for this value
            matching_digit_occurrence[x0] += 1

        dx = x1 - x0
        # Going from left to right, the digits never decrease; they only ever increase or stay the same
        if dx < 0:
            # The digits decreased. This is not a valid password
            return False

    # Verify there is at least 1 pair of matching adjacent digits that only occurs ONCE
    for value, count in matching_digit_occurrence.items():
        if count == 1:
            return True
    return False


def find_possible_passwords(value_min: int, value_max: int) -> List[int]:
    valid_passwords = list()

    for int_value in range(value_min, value_max + 1):
        if is_valid_password_part_1(int_value):
            valid_passwords.append(int_value)

    return valid_passwords


class Day4Tests(unittest.TestCase):
    def test_part_1_examples(self):
        self.assertEqual(is_valid_password_part_1(111111), True)
        self.assertEqual(is_valid_password_part_1(223450), False)
        self.assertEqual(is_valid_password_part_1(123789), False)

    def test_part_2_examples(self):
        self.assertEqual(is_valid_password_part_2(112233), True)
        self.assertEqual(is_valid_password_part_2(123444), False)
        self.assertEqual(is_valid_password_part_2(111122), True)


def day_4(txt_path: Path) -> List[int]:
    with open(str(txt_path), 'r', newline='') as f:
        row = f.readline()

    values = row.split('-')
    value_min = int(values[0])
    value_max = int(values[1])

    # How many different passwords within the range given in your puzzle input meet these criteria?
    part_1_valid_passwords = list()
    part_2_valid_passwords = list()
    for int_value in range(value_min, value_max + 1):
        if is_valid_password_part_1(int_value):
            part_1_valid_passwords.append(int_value)
        if is_valid_password_part_2(int_value):
            part_2_valid_passwords.append(int_value)

    return [len(part_1_valid_passwords), len(part_2_valid_passwords)]


def main():
    txt_path = Path(Path(__file__).parent, 'input_data', 'day_4_input.txt')
    answer = day_4(txt_path=txt_path)
    print(f'Day 4 Answers: {repr(answer)}')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Day4Tests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    main()
