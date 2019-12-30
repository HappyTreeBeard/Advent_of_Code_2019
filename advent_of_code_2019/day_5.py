import copy
import unittest
from enum import IntEnum
from pathlib import Path
from typing import List

from dataclasses import dataclass


class OpCode(IntEnum):
    """ Opcodes (like 1, 2, or 99) mark the beginning of an instruction. The values used immediately after an opcode,
    if any, are called the instruction's parameters."""
    ADD = 1
    MULTIPLY = 2
    SAVE_TO_ADDRESS = 3
    READ_FROM_ADDRESS = 4
    JUMP_IF_TRUE = 5
    JUMP_IF_FALSE = 6
    LESS_THAN = 7
    EQUALS = 8
    FINISHED = 99

    @property
    def expected_parameter_count(self) -> int:
        if self in [OpCode.ADD, OpCode.MULTIPLY]:
            # 3 parameters: number1, number2, result
            # Raw value or index of value
            return 3
        elif self in [OpCode.SAVE_TO_ADDRESS, OpCode.READ_FROM_ADDRESS]:
            # 1 parameters: address
            # Raw value or index of value
            return 1
        elif self == OpCode.FINISHED:
            return 0
        elif self in [OpCode.JUMP_IF_TRUE, OpCode.JUMP_IF_FALSE]:
            return 2
        elif self in [OpCode.LESS_THAN, OpCode.EQUALS]:
            return 3
        else:
            raise ValueError(f'Unknown parameter count. {OpCode}: {self}')


class ParameterMode(IntEnum):
    POSITION = 0
    """Interpret the parameter as an index position"""
    IMMEDIATE = 1
    """Interpret the parameter as a value"""


@dataclass(frozen=True)
class Instruction(object):
    op_code: OpCode
    parameter_mode_list: List[ParameterMode]

    @classmethod
    def build_from_instruction_int(cls, value: int):
        """ Build a Instruction object based on its integer representation."""
        # ABCDE
        #  1002  (Example instruction)
        #
        # DE - two-digit opcode,      02 == opcode 2
        #  C - mode of 1st parameter,  0 == position mode
        #  B - mode of 2nd parameter,  1 == immediate mode
        #  A - mode of 3rd parameter,  0 == position mode, omitted due to being a leading zero

        digits_str = str(value)

        # Extract the two-digit opcode
        op_code_int = int(digits_str[-2:])
        op_code = OpCode(op_code_int)

        # Extract the mode for each parameter
        param_modes_str = digits_str[:-2]  # Exclude the opcode
        if not param_modes_str:
            # Support legacy opcodes which did not specify any parameter mode
            param_mode_list = [ParameterMode.POSITION] * op_code.expected_parameter_count
            return Instruction(op_code=op_code, parameter_mode_list=param_mode_list)

        # Leading zeros of the integer will be trimmed.
        # The number of parameter modes, i.e. number of digits, is determined by the specific opcode
        # Pad the string with zeros to match the expected parameter count
        parameter_count = op_code.expected_parameter_count
        # # Option0
        # padded_zeros = '0' * (parameter_count - len(param_modes_str))
        # param_modes_str = padded_zeros + param_modes_str
        # Option1
        param_modes_str = f'{int(param_modes_str):0{parameter_count}d}'  # f'{123:04d}' -> '0123'

        # Build a list of ParameterMode
        # Parameter order increases from right to left
        param_mode_list = [ParameterMode(int(x)) for x in reversed(param_modes_str)]

        return Instruction(op_code=op_code, parameter_mode_list=param_mode_list)


class IntCodeProgram(object):
    def __init__(self, intcode: List[int]):
        self.intcode: List[int] = intcode
        self.program_input: List[int] = list()
        self.program_output: List[int] = list()

    @property
    def diagnostic_code(self) -> int:
        # An output followed immediately by a halt means the program finished.
        # If all outputs were zero except the diagnostic code, the diagnostic program ran successfully.
        diagnostic_code = self.program_output[-1]
        for code in self.program_output[0:-1]:
            if code != 0:
                raise ValueError(f'Diagnostic program failed. Not all outputs were zero '
                                 f'expect for final value: {self.program_output}')
        return diagnostic_code

    def read_parameter_value(self, parameter_value: int, mode: ParameterMode) -> int:
        # Resolve the parameter value based on the ParameterMode
        if mode == ParameterMode.IMMEDIATE:
            return parameter_value
        elif mode == ParameterMode.POSITION:
            return self.intcode[parameter_value]
        else:
            raise ValueError(f'Unexpected {ParameterMode}: {mode}')

    def run(self):
        i = 0  # Start at index 0
        while True:
            value = self.intcode[i]
            try:
                instruction = Instruction.build_from_instruction_int(value)
            except ValueError:
                raise ValueError(f'Failed to construct {Instruction} from value: {repr(value)}')

            # Extract the parameters used by this instruction
            # The number of parameters is determined by the specific opcode
            param_i_start = i + 1
            param_i_end = param_i_start + instruction.op_code.expected_parameter_count
            parameter_list = self.intcode[param_i_start: param_i_end]
            parameter_mode_list = instruction.parameter_mode_list

            # Normally, after an instruction is finished, the instruction pointer increases by the number of values
            # in that instruction. However, if the instruction modifies the instruction pointer, that value is used
            # and the instruction pointer is not automatically increased.
            increment_by_parameter_count = True

            if instruction.op_code == OpCode.FINISHED:
                # 99 means that the program is finished and should immediately halt.
                break
            elif instruction.op_code in [OpCode.ADD, OpCode.MULTIPLY, OpCode.LESS_THAN, OpCode.EQUALS]:
                # Resolve which argument values will be used in the math operation
                # Should the value be intercepted as an index value or a raw value?
                num0 = self.read_parameter_value(parameter_list[0], parameter_mode_list[0])
                num1 = self.read_parameter_value(parameter_list[1], parameter_mode_list[1])

                if instruction.op_code == OpCode.ADD:
                    result = num0 + num1
                elif instruction.op_code == OpCode.MULTIPLY:
                    result = num0 * num1
                elif instruction.op_code == OpCode.LESS_THAN:
                    result = int(num0 < num1)
                elif instruction.op_code == OpCode.EQUALS:
                    result = int(num0 == num1)
                else:
                    raise ValueError(f'Unexpected {OpCode}: {instruction.op_code}')

                result_parameter = parameter_list[2]
                result_mode = parameter_mode_list[2]
                if result_mode == ParameterMode.IMMEDIATE:
                    address = i + 3  # TODO: Remove magic string
                elif result_mode == ParameterMode.POSITION:
                    address = result_parameter
                else:
                    raise ValueError(f'Unexpected {ParameterMode}: {result_mode}')

                self.intcode[address] = result

            elif instruction.op_code in [OpCode.SAVE_TO_ADDRESS, OpCode.READ_FROM_ADDRESS]:
                # num = self.read_parameter_value(parameter_list[0], parameter_mode_list[0])
                parameter = parameter_list[0]
                mode = parameter_mode_list[0]

                if instruction.op_code == OpCode.SAVE_TO_ADDRESS:
                    # Opcode 3 takes a single integer as input and saves it to the position given by its only parameter.
                    # For example, the instruction 3,50 would take an input value and store it at address 50.
                    if mode == ParameterMode.POSITION:
                        self.intcode[parameter] = self.program_input.pop(0)
                    else:
                        raise ValueError(f'Unexpected {ParameterMode}: {mode}')
                elif instruction.op_code == OpCode.READ_FROM_ADDRESS:
                    # Opcode 4 outputs the value of its only parameter. For example, the instruction 4,50 would output
                    # the value at address 50.
                    if mode == ParameterMode.IMMEDIATE:
                        value = self.intcode[i + 1]  # TODO: Remove magic string
                    elif mode == ParameterMode.POSITION:
                        value = self.intcode[parameter]
                    else:
                        raise ValueError(f'Unexpected {ParameterMode}: {mode}')
                    self.program_output.append(value)
                else:
                    raise ValueError(f'Unexpected {OpCode}: {instruction.op_code}')

            elif instruction.op_code in [OpCode.JUMP_IF_TRUE, OpCode.JUMP_IF_FALSE]:
                num0 = self.read_parameter_value(parameter_list[0], parameter_mode_list[0])
                num1 = self.read_parameter_value(parameter_list[1], parameter_mode_list[1])
                if instruction.op_code == OpCode.JUMP_IF_TRUE:
                    # If the first parameter is non-zero, it sets the instruction pointer to the value from the
                    # second parameter. Otherwise, it does nothing.
                    if num0 != 0:
                        increment_by_parameter_count = False
                        i = num1
                elif instruction.op_code == OpCode.JUMP_IF_FALSE:
                    # If the first parameter is zero, it sets the instruction pointer to the value from the
                    # second parameter. Otherwise, it does nothing.
                    if num0 == 0:
                        increment_by_parameter_count = False
                        i = num1
                else:
                    raise ValueError(f'Unexpected {OpCode}: {instruction.op_code}')
            else:
                raise ValueError(f'Unsupported {OpCode}: {instruction.op_code}')

            if increment_by_parameter_count:
                # Increment the program index based on the parameter count
                i += 1 + instruction.op_code.expected_parameter_count


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
