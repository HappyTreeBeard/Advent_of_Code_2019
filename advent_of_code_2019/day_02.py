import copy
import unittest
from enum import IntEnum
from pathlib import Path
from typing import List


class OpCode(IntEnum):
    """ Opcodes (like 1, 2, or 99) mark the beginning of an instruction. The values used immediately after an opcode,
    if any, are called the instruction's parameters."""
    ADD = 1
    MULTIPLY = 2
    FINISHED = 99


def run_intcode_program(intcode: List[int]):
    i = 0  # Start at index 0
    while True:
        opt_code_int = intcode[i]
        try:
            opt_code = OpCode(opt_code_int)
        except ValueError:
            # Encountering an unknown opcode means something went wrong.
            raise ValueError(f'Unexpected OpCode: {opt_code_int}')

        if opt_code == OpCode.FINISHED:
            # 99 means that the program is finished and should immediately halt.
            i += 1
            break
        else:
            # Extract the two values to use in the operation
            num0_i = intcode[i + 1]
            num1_i = intcode[i + 2]
            result_i = intcode[i + 3]  # Index of where the result will be stored
            num0 = intcode[num0_i]
            num1 = intcode[num1_i]

            if opt_code == OpCode.ADD:
                result = num0 + num1
            elif opt_code == OpCode.MULTIPLY:
                result = num0 * num1
            else:
                raise ValueError(f'Unhandled OpCode: {opt_code}')

            intcode[result_i] = result

            # Once you're done processing an opcode, move to the next one by stepping forward 4 positions.
            i += 4
    return intcode


class Day2Tests(unittest.TestCase):

    def test_int_code_program_0(self):
        values = [1, 9, 10, 3, 2, 3, 11, 0, 99, 30, 40, 50]
        expected = [3500, 9, 10, 70, 2, 3, 11, 0, 99, 30, 40, 50]
        self.assertEqual(run_intcode_program(values), expected)

    def test_int_code_program_1(self):
        values = [1, 0, 0, 0, 99]
        expected = [2, 0, 0, 0, 99]
        self.assertEqual(run_intcode_program(values), expected)

        values = [1, 0, 0, 0, 99]
        expected = [2, 0, 0, 0, 99]
        self.assertEqual(run_intcode_program(values), expected)

        self.assertEqual(run_intcode_program([1, 0, 0, 0, 99]), [2, 0, 0, 0, 99])
        self.assertEqual(run_intcode_program([2, 3, 0, 3, 99]), [2, 3, 0, 6, 99])
        self.assertEqual(run_intcode_program([2, 4, 4, 5, 99, 0]), [2, 4, 4, 5, 99, 9801])
        self.assertEqual(run_intcode_program([1, 1, 1, 4, 99, 5, 6, 0, 99]), [30, 1, 1, 4, 2, 5, 6, 0, 99])


def day_2(txt_path: Path) -> List[int]:
    # Load puzzle input as List[int]
    with open(str(txt_path), mode='r', newline='') as f:
        base_intcode = [int(x) for x in f.readline().split(',')]

    # Part 1
    # Once you have a working computer, the first step is to restore the gravity assist program (your puzzle input)
    # to the "1202 program alarm" state it had just before the last computer caught fire. To do this, before running
    # the program, replace position 1 with the value 12 and replace position 2 with the value 2.
    intcode = copy.copy(base_intcode)
    intcode[1] = 12  # Noun
    intcode[2] = 2  # Verb
    result_data = run_intcode_program(intcode=intcode)

    # What value is left at position 0 after the program halts?
    part_1_answer = result_data[0]

    # Part 2
    # Determine what pair of inputs produces the output 19690720. What is 100 * noun + verb?
    # The inputs should still be provided to the program by replacing the values at addresses 1 and 2, just like before.
    # In this program, the value placed in address 1 is called the noun, and the value placed in address 2 is called the
    # verb. Each of the two input values will be between 0 and 99, inclusive.
    expected_output = 19690720
    match_found = False
    part_2_answer = None
    for noun in range(99):
        for verb in range(99):
            intcode = copy.copy(base_intcode)
            intcode[1] = noun
            intcode[2] = verb
            result_data = run_intcode_program(intcode=intcode)
            result = result_data[0]
            if result == expected_output:
                match_found = True
                answer = 100 * noun + verb
                part_2_answer = answer
                break
        if match_found:
            break

    return [part_1_answer, part_2_answer]


def main():
    txt_path = Path(Path(__file__).parent, 'input_data', 'day_2_input.txt')
    answer = day_2(txt_path=txt_path)
    print(f'Day 1 Answers: {repr(answer)}')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Day2Tests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    main()
