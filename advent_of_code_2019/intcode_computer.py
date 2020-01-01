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
    ADJUST_RELATIVE_BASE = 9
    FINISHED = 99

    @property
    def expected_parameter_count(self) -> int:
        if self in [OpCode.ADD, OpCode.MULTIPLY]:
            # 3 parameters: number1, number2, result
            # Raw value or index of value
            return 3
        elif self in [OpCode.SAVE_TO_ADDRESS, OpCode.READ_FROM_ADDRESS, OpCode.ADJUST_RELATIVE_BASE]:
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
    RELATIVE = 2
    """Similar to position mode but the value is a 'relative base' instead of relative to the start of the program. """


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
        self.relative_base = 0
        """The address a relative mode parameter refers to is itself plus the current relative base. When the 
        relative base is 0, relative mode parameters and position mode parameters with the same value refer to the 
        same address. """

    @property
    def diagnostic_code(self) -> int:
        # An output followed immediately by a halt means the program finished.
        # If all outputs were zero except the diagnostic code, the diagnostic program ran successfully.

        # Non-zero outputs mean that a function is not working correctly; check the instructions that were run before
        # the output instruction to see which one failed.

        # Make sure the diagnostic code is removed from the program_output. If this is not done then feedback loop
        # programs, which halt/wait for user input and have multiple outputs, will incorrectly have non-zero values
        # left in their output.
        diagnostic_code = self.program_output.pop()
        for code in self.program_output:
            if code != 0:
                raise ValueError(f'Diagnostic program failed. Not all outputs were zero '
                                 f'expect for final value: {self.program_output}')
        return diagnostic_code

    def read_parameter_value(self, index: int, mode: ParameterMode) -> int:
        """ Resolve the parameter value based on the ParameterMode

        :param index: Index of the parameter within the intcode
        :type index: int
        :param mode: The ParameterMode for this parameter
        :type mode: ParameterMode
        :return: The parameter value
        :rtype: int
        """
        parameter = self.intcode[index]
        # How should the parameter be interpreted?
        if mode == ParameterMode.IMMEDIATE:
            parameter_value = parameter
        elif mode in [ParameterMode.POSITION, ParameterMode.RELATIVE]:
            # The parameter is an index of the intcode
            parameter_value_index = parameter
            if mode == ParameterMode.RELATIVE:
                # The parameter is a index of the intcode relative to the 'relative_base'
                # Apply the relative_base as an offset to find the index of the parameter_value
                parameter_value_index += self.relative_base
            self.extend_memory(index=parameter_value_index)
            parameter_value = self.intcode[parameter_value_index]
        else:
            raise ValueError(f'Unexpected {ParameterMode}: {mode}')

        return parameter_value

    def extend_memory(self, index: int):
        """ Extend the size of the intcode program to include the provided index. Any new elements in the array
        will be initialized to 0.

        :param index: Index that should be accessible in the intcode array
        :type index: int
        """
        # The computer's available memory should be much larger than the initial program. Memory beyond the initial
        # program starts with the value 0 and can be read or written like any other memory. (It is invalid to try to
        # access memory at a negative address, though.)
        indices_to_add = index + 1 - len(self.intcode)
        if indices_to_add > 0:
            self.intcode = self.intcode + [0] * indices_to_add

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
            parameter_index_list = list(range(param_i_start, param_i_end))
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
                num0 = self.read_parameter_value(index=parameter_index_list[0], mode=parameter_mode_list[0])
                num1 = self.read_parameter_value(index=parameter_index_list[1], mode=parameter_mode_list[1])

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

                result_parameter_index = parameter_index_list[2]
                result_mode = parameter_mode_list[2]
                if result_mode == ParameterMode.POSITION:
                    address = self.intcode[result_parameter_index]
                elif result_mode == ParameterMode.RELATIVE:
                    # address = result_parameter_index + self.relative_base
                    address = self.intcode[result_parameter_index] + self.relative_base
                else:
                    # TODO: Why is ParameterMode.IMMEDIATE never used?
                    raise ValueError(f'Unexpected {ParameterMode}: {repr(result_mode)}')

                self.extend_memory(index=address)
                self.intcode[address] = result

            elif instruction.op_code in [OpCode.SAVE_TO_ADDRESS, OpCode.READ_FROM_ADDRESS]:
                # num = self.read_parameter_value(parameter_index_list[0], parameter_mode_list[0])
                # parameter = parameter_list[0]
                mode = parameter_mode_list[0]

                if instruction.op_code == OpCode.SAVE_TO_ADDRESS:
                    # Opcode 3 takes a single integer as input and saves it to the position given by its only parameter.
                    # For example, the instruction 3,50 would take an input value and store it at address 50.
                    # num = self.read_parameter_value(index=parameter_index_list[0], mode=parameter_mode_list[0])

                    if mode == ParameterMode.POSITION:
                        num = self.intcode[parameter_index_list[0]]
                    elif mode == ParameterMode.RELATIVE:
                        parameter_value = self.intcode[parameter_index_list[0]]
                        index = parameter_value + self.relative_base
                        # index = parameter_index_list[0] + self.relative_base
                        self.extend_memory(index=index)
                        num = index
                        # num = self.intcode[index]
                    else:
                        raise ValueError(f'Unexpected {ParameterMode}: {mode}')

                    if not self.program_input:
                        # The program needs an input variable before it can continue. Break from the loop.
                        # The run() function can be called again to resume where it left off when a variable
                        # has been added to self.program_input
                        self.ran_to_completion = False
                        return
                    self.intcode[num] = self.program_input.pop(0)

                elif instruction.op_code == OpCode.READ_FROM_ADDRESS:
                    # Opcode 4 outputs the value of its only parameter. For example, the instruction 4,50 would output
                    # the value at address 50.
                    num = self.read_parameter_value(parameter_index_list[0], parameter_mode_list[0])
                    self.program_output.append(num)
                else:
                    raise ValueError(f'Unexpected {OpCode}: {instruction.op_code}')

            elif instruction.op_code in [OpCode.JUMP_IF_TRUE, OpCode.JUMP_IF_FALSE]:
                num0 = self.read_parameter_value(parameter_index_list[0], parameter_mode_list[0])
                num1 = self.read_parameter_value(parameter_index_list[1], parameter_mode_list[1])
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
            elif instruction.op_code == OpCode.ADJUST_RELATIVE_BASE:
                # Opcode 9 adjusts the relative base by the value of its only parameter. The relative base increases
                # (or decreases, if the value is negative) by the value of the parameter.
                num = self.read_parameter_value(parameter_index_list[0], parameter_mode_list[0])
                self.relative_base += num
            else:
                raise ValueError(f'Unsupported {OpCode}: {instruction.op_code}')

            if increment_by_parameter_count:
                # Increment the program index based on the parameter count
                self.i += 1 + instruction.op_code.expected_parameter_count
