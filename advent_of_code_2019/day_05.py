import copy
import unittest
from pathlib import Path
from typing import List

from advent_of_code_2019.intcode_computer import IntCodeProgram, ParameterMode, Instruction


def run_intcode_program(intcode: List[int], program_input: List[int] = list) -> IntCodeProgram:
    p = IntCodeProgram(intcode=intcode)
    p.enable_legacy_support = True
    p.program_input = program_input
    p.run()
    return p


class Day5Tests(unittest.TestCase):

    def test_simple_day_2_int_code_program(self):
        values = [1, 0, 0, 0, 99]
        expected = [2, 0, 0, 0, 99]
        self.assertEqual(run_intcode_program(values).intcode, expected)

        values = [1, 0, 0, 0, 99]
        expected = [2, 0, 0, 0, 99]
        self.assertEqual(run_intcode_program(values).intcode, expected)

    def test_param_mode(self):
        value = 1002
        expected = [ParameterMode.POSITION, ParameterMode.IMMEDIATE, ParameterMode.POSITION]
        instruction = Instruction.build_from_instruction_int(value)
        actual = instruction.parameter_mode_list
        self.assertListEqual(expected, actual)

    def test_simple_int_code_program(self):
        values = [1002, 4, 3, 4, 33]
        expected = [1002, 4, 3, 4, 99]
        actual = run_intcode_program(values).intcode
        self.assertEqual(actual, expected)

    def test_int_code_program_0(self):
        values = [1, 9, 10, 3, 2, 3, 11, 0, 99, 30, 40, 50]
        expected = [3500, 9, 10, 70, 2, 3, 11, 0, 99, 30, 40, 50]
        self.assertEqual(run_intcode_program(values).intcode, expected)

    def test_int_code_program_1(self):
        self.assertEqual(run_intcode_program([1, 0, 0, 0, 99]).intcode, [2, 0, 0, 0, 99])
        self.assertEqual(run_intcode_program([2, 3, 0, 3, 99]).intcode, [2, 3, 0, 6, 99])
        self.assertEqual(run_intcode_program([2, 4, 4, 5, 99, 0]).intcode, [2, 4, 4, 5, 99, 9801])
        self.assertEqual(run_intcode_program([1, 1, 1, 4, 99, 5, 6, 0, 99]).intcode, [30, 1, 1, 4, 2, 5, 6, 0, 99])

    def test_negative_integers(self):
        values = [1101, 100, -1, 4, 0]
        expected = [1101, 100, -1, 4, 99]
        actual = run_intcode_program(values).intcode
        self.assertEqual(actual, expected)

    def test_opcode_3(self):
        program_input = [123]
        # Take the input value and store it at address 5
        values = [3, 5, 99, 0, 0, 0]
        expected_values = [3, 5, 99, 0, 0, 123]
        program = run_intcode_program(values, program_input=program_input)
        self.assertEqual(program.intcode, expected_values)

    def test_input_output(self):
        program_input = [123]
        values = [3, 0, 4, 0, 99]
        expected_output = [123]

        program = run_intcode_program(values, program_input=program_input)
        self.assertEqual(program.program_output, expected_output)

    def test_equal_position_mode(self):
        # Using position mode, consider whether the input is equal to 8; output 1 (if it is) or 0 (if it is not).
        values = [3, 9, 8, 9, 10, 9, 4, 9, 99, -1, 8]

        program_input = [7]  # 7 != 8
        expected_output = 0

        program = run_intcode_program(copy.copy(values), program_input=program_input)
        self.assertEqual(program.diagnostic_code, expected_output)

        program_input = [8]  # 8 == 8
        expected_output = 1

        program = run_intcode_program(copy.copy(values), program_input=program_input)
        self.assertEqual(program.diagnostic_code, expected_output)

    def test_less_than_position_mode(self):
        # Using position mode, consider whether the input is less than 8; output 1 (if it is) or 0 (if it is not).
        values = [3, 9, 7, 9, 10, 9, 4, 9, 99, -1, 8]

        program_input = [7]  # 7 < 8
        expected_output = 1

        program = run_intcode_program(copy.copy(values), program_input=program_input)
        self.assertEqual(program.diagnostic_code, expected_output)

        program_input = [8]  # 8 !< 8
        expected_output = 0

        program = run_intcode_program(copy.copy(values), program_input=program_input)
        self.assertEqual(program.diagnostic_code, expected_output)

    def test_equal_immediate_mode(self):
        # Using immediate mode, consider whether the input is equal to 8; output 1 (if it is) or 0 (if it is not).
        values = [3, 3, 1108, -1, 8, 3, 4, 3, 99]

        program_input = [7]  # 7 != 8
        expected_output = 0

        program = run_intcode_program(copy.copy(values), program_input=program_input)
        self.assertEqual(program.diagnostic_code, expected_output)

        program_input = [8]  # 8 == 8
        expected_output = 1

        program = run_intcode_program(copy.copy(values), program_input=program_input)
        self.assertEqual(program.diagnostic_code, expected_output)

    def test_less_than_immediate_mode(self):
        # Using position mode, consider whether the input is less than 8; output 1 (if it is) or 0 (if it is not).
        values = [3, 3, 1107, -1, 8, 3, 4, 3, 99]

        program_input = [7]  # 7 < 8
        expected_output = 1

        program = run_intcode_program(copy.copy(values), program_input=program_input)
        self.assertEqual(program.diagnostic_code, expected_output)

        program_input = [8]  # 8 !< 8
        expected_output = 0

        program = run_intcode_program(copy.copy(values), program_input=program_input)
        self.assertEqual(program.diagnostic_code, expected_output)

    def test_jump_position_mode(self):
        # Jump test that takes an input, then output 0 if the input was zero or 1 if the input was non-zero:
        values = [3, 12, 6, 12, 15, 1, 13, 14, 13, 4, 13, 99, -1, 0, 1, 9]

        program_input = [7]  # 7 is non-zero
        expected_output = 1

        program = run_intcode_program(copy.copy(values), program_input=program_input)
        self.assertEqual(program.diagnostic_code, expected_output)

        program_input = [0]  # Pass zero as input.
        expected_output = 0

        program = run_intcode_program(copy.copy(values), program_input=program_input)
        self.assertEqual(program.diagnostic_code, expected_output)

    def test_jump_immediate_mode(self):
        # Jump test that takes an input, then output 0 if the input was zero or 1 if the input was non-zero:
        values = [3, 3, 1105, -1, 9, 1101, 0, 0, 12, 4, 12, 99, 1]

        program_input = [7]  # 7 is non-zero
        expected_output = 1

        program = run_intcode_program(copy.copy(values), program_input=program_input)
        self.assertEqual(program.diagnostic_code, expected_output)

        program_input = [0]  # Pass zero as input.
        expected_output = 0

        program = run_intcode_program(copy.copy(values), program_input=program_input)
        self.assertEqual(program.diagnostic_code, expected_output)

    def test_large_example(self):
        # The above example program uses an input instruction to ask for a single number. The program will then
        # output 999 if the input value is below 8, output 1000 if the input value is equal to 8, or output 1001
        # if the input value is greater than 8.
        values = [3, 21, 1008, 21, 8, 20, 1005, 20, 22, 107, 8, 21, 20, 1006, 20, 31, 1106, 0, 36, 98, 0, 0, 1002, 21,
                  125, 20, 4, 20, 1105, 1, 46, 104, 999, 1105, 1, 46, 1101, 1000, 1, 20, 4, 20, 1105, 1, 46, 98, 99]

        program_input = [7]  # 7 < 8
        expected_output = 999
        program = run_intcode_program(copy.copy(values), program_input=program_input)
        self.assertEqual(program.diagnostic_code, expected_output)

        program_input = [8]  # 8 == 8
        expected_output = 1000
        program = run_intcode_program(copy.copy(values), program_input=program_input)
        self.assertEqual(program.diagnostic_code, expected_output)

        program_input = [11]  # 11 > 8
        expected_output = 1001
        program = run_intcode_program(copy.copy(values), program_input=program_input)
        self.assertEqual(program.diagnostic_code, expected_output)


def day_5(txt_path: Path) -> List[int]:
    # Load puzzle input as List[int]
    with open(str(txt_path), mode='r', newline='') as f:
        base_intcode = [int(x) for x in f.readline().split(',')]

    # Part 1
    # The TEST diagnostic program will start by requesting from the user the ID of the system to test by running an
    # input instruction - provide it 1, the ID for the ship's air conditioner unit.
    program_input = [1]

    p = IntCodeProgram(intcode=copy.copy(base_intcode))
    p.program_input = program_input
    p.run()

    # Finally, the program will output a diagnostic code and immediately halt. This final output isn't an error; an
    # output followed immediately by a halt means the program finished. If all outputs were zero except the diagnostic
    # code, the diagnostic program ran successfully.
    part_1_diagnostic_code = p.diagnostic_code

    # Part 2
    # This time, when the TEST diagnostic program runs its input instruction to get the ID of the system to test,
    # provide it 5, the ID for the ship's thermal radiator controller. This diagnostic test suite only outputs one
    # number, the diagnostic code.
    # What is the diagnostic code for system ID 5?
    program_input = [5]

    p = IntCodeProgram(intcode=copy.copy(base_intcode))
    p.program_input = program_input
    p.run()
    part_2_diagnostic_code = p.diagnostic_code

    return [part_1_diagnostic_code, part_2_diagnostic_code]


def main():
    txt_path = Path(Path(__file__).parent, 'input_data', 'day_5_input.txt')

    answer = day_5(txt_path=txt_path)
    print(f'Day 5 Answers: {repr(answer)}')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Day5Tests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    main()
