import copy
import unittest
from pathlib import Path

from advent_of_code_2019.intcode_computer import IntCodeProgram, Instruction, OpCode, ParameterMode


class Day9Tests(unittest.TestCase):

    def test_build_opcode_9(self):
        code = 109
        instruction = Instruction.build_from_instruction_int(value=code)
        self.assertEqual(instruction.op_code, OpCode.ADJUST_RELATIVE_BASE)
        self.assertEqual(instruction.parameter_mode_list, [ParameterMode.IMMEDIATE])

    def test_opcode_9_example_1(self):
        # For example, if the relative base is 2000, then after the instruction 109,19, the relative base would be 2019.
        # Instruction 109 -> OpCode.ADJUST_RELATIVE_BASE and ParameterMode.IMMEDIATE
        intcode = [109, 19, 99]
        start_relative_base = 2000
        expected_relative_base = 2019
        program = IntCodeProgram(intcode=intcode)
        program.relative_base = start_relative_base
        program.run()
        self.assertEqual(program.relative_base, expected_relative_base)

    def test_part_1_example_1(self):
        # This program takes no input and produces a copy of itself as output.
        intcode = [109, 1, 204, -1, 1001, 100, 1, 100, 1008, 100, 16, 101, 1006, 101, 0, 99]
        expected_output = copy.copy(intcode)
        program = IntCodeProgram(intcode=intcode)
        program.run()
        self.assertListEqual(program.program_output, expected_output)

    def test_part_1_example_2(self):
        # This should output a 16-digit number.
        intcode = [1102, 34915192, 34915192, 7, 4, 7, 99, 0]
        expected_length = 16
        program = IntCodeProgram(intcode=intcode)
        program.run()
        output = program.diagnostic_code
        self.assertEqual(len(str(output)), expected_length)

    def test_part_1_example_3(self):
        # This should output the large number in the middle.
        intcode = [104, 1125899906842624, 99]
        expected_output = 1125899906842624
        program = IntCodeProgram(intcode=intcode)
        program.run()
        output = program.diagnostic_code
        self.assertEqual(output, expected_output)


def day_9(txt_path: Path) -> list:
    # Load puzzle input. Single row with comma separated integers.
    with open(str(txt_path), mode='r', newline='') as f:
        row = f.readline()
    # Convert the puzzle input into the Amplifier Controller Software, a List[int]
    intcode = [int(x) for x in row.split(',')]

    program = IntCodeProgram(intcode=copy.copy(intcode))

    # The BOOST program will ask for a single input; run it in test mode by providing it the value 1.
    program.program_input = [1]

    # The BOOST program should report no malfunctioning opcodes when run in test mode; it should only output a single
    # value, the BOOST keycode. What BOOST keycode does it produce?
    program.run()

    # Part 1: What BOOST keycode does it produce?
    part_1_answer = program.diagnostic_code

    # The program runs in sensor boost mode by providing the input instruction the value 2.
    program = IntCodeProgram(intcode=copy.copy(intcode))
    program.program_input = [2]

    #  In sensor boost mode, the program will output a single value: the coordinates of the distress signal.
    program.run()

    # Part 2: What are the coordinates of the distress signal?
    part_2_answer = program.diagnostic_code

    return [part_1_answer, part_2_answer]


def main():
    txt_path = Path(Path(__file__).parent, 'input_data', 'day_09_input.txt')
    answer = day_9(txt_path=txt_path)
    print(f'Day 9 Answers: {repr(answer)}')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Day9Tests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    main()
