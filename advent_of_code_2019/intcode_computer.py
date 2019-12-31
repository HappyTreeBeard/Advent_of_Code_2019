from enum import IntEnum
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
        self.i = 0
        """The current index position within the intcode program."""
        self.ran_to_completion = False
        """This value will be False if the program was never run or if the program is waiting for an input variable. """

    @property
    def diagnostic_code(self) -> int:
        # An output followed immediately by a halt means the program finished.
        # If all outputs were zero except the diagnostic code, the diagnostic program ran successfully.

        # Make sure the diagnostic code is removed from the program_output. If this is not done then feedback loop
        # programs, which halt/wait for user input and have multiple outputs, will incorrectly have non-zero values
        # left in their output.
        diagnostic_code = self.program_output.pop()
        for code in self.program_output:
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
        """Execute the intcode program or resume from the previous position if the program was waiting for
        additional input. """

        while True:
            value = self.intcode[self.i]
            try:
                instruction = Instruction.build_from_instruction_int(value)
            except ValueError:
                raise ValueError(f'Failed to construct {Instruction} from value: {repr(value)}')

            # Extract the parameters used by this instruction
            # The number of parameters is determined by the specific opcode
            param_i_start = self.i + 1
            param_i_end = param_i_start + instruction.op_code.expected_parameter_count
            parameter_list = self.intcode[param_i_start: param_i_end]
            parameter_mode_list = instruction.parameter_mode_list

            # Normally, after an instruction is finished, the instruction pointer increases by the number of values
            # in that instruction. However, if the instruction modifies the instruction pointer, that value is used
            # and the instruction pointer is not automatically increased.
            increment_by_parameter_count = True

            if instruction.op_code == OpCode.FINISHED:
                # 99 means that the program is finished and should immediately halt.
                self.ran_to_completion = True
                return
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
                    address = self.i + 3  # TODO: Remove magic string
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
                        try:
                            self.intcode[parameter] = self.program_input.pop(0)
                        except IndexError:
                            # The program needs an input variable before it can continue. Break from the loop.
                            # The run() function can be called again to resume where it left off when a variable
                            # has been added to self.program_input
                            self.ran_to_completion = False
                            return
                    else:
                        raise ValueError(f'Unexpected {ParameterMode}: {mode}')
                elif instruction.op_code == OpCode.READ_FROM_ADDRESS:
                    # Opcode 4 outputs the value of its only parameter. For example, the instruction 4,50 would output
                    # the value at address 50.
                    if mode == ParameterMode.IMMEDIATE:
                        value = self.intcode[self.i + 1]  # TODO: Remove magic string
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
                        self.i = num1
                elif instruction.op_code == OpCode.JUMP_IF_FALSE:
                    # If the first parameter is zero, it sets the instruction pointer to the value from the
                    # second parameter. Otherwise, it does nothing.
                    if num0 == 0:
                        increment_by_parameter_count = False
                        self.i = num1
                else:
                    raise ValueError(f'Unexpected {OpCode}: {instruction.op_code}')
            else:
                raise ValueError(f'Unsupported {OpCode}: {instruction.op_code}')

            if increment_by_parameter_count:
                # Increment the program index based on the parameter count
                self.i += 1 + instruction.op_code.expected_parameter_count
