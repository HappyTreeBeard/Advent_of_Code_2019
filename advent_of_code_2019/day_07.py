import copy
import unittest
from itertools import permutations
from pathlib import Path
from typing import List

from dataclasses import dataclass

from advent_of_code_2019.day_05 import IntCodeProgram


@dataclass(frozen=True, order=True)
class AmplificationProgram(object):
    amp_ctrl_software: List[int]
    """The amplifier controller software that will run on each amplifier."""
    amp_phase_list: List[int]
    """The phase settings for each amplifier"""

    def run(self) -> int:
        """ Run the Amplifier Controller Software for each amplifier phase setting to calculate
        the total signal amplification.

        :return: The total signal amplification
        :rtype: int
        """
        # Provide each amplifier its phase setting at its first input instruction; all further input/output
        # instructions are for signals.
        # All signals sent or received in this process will be between pairs of amplifiers except the very first signal
        # and the very last signal. To start the process, a 0 signal is sent to amplifier A's input exactly once.

        # Initialize each IntCodeProgram object for each amplifier
        program_list: List[IntCodeProgram] = list()
        for amp_phase in self.amp_phase_list:
            program = IntCodeProgram(intcode=copy.copy(self.amp_ctrl_software))
            program.program_input = [amp_phase]
            program_list.append(program)

        signal_amplitude = 0
        all_programs_finished = False
        while not all_programs_finished:
            for program in program_list:
                program.program_input.append(signal_amplitude)
                program.run()
                signal_amplitude = program.diagnostic_code
                # The diagnostic_code is not valid
                # signal_amplitude = program.program_output[-1]
            all_programs_finished = all([x.ran_to_completion for x in program_list])
        return signal_amplitude


class Day7Tests(unittest.TestCase):

    def test_part_1_example_1(self):
        intcode = [3, 15, 3, 16, 1002, 16, 10, 16, 1, 16, 15, 15, 4, 15, 99, 0, 0]
        amp_phase_list = [4, 3, 2, 1, 0]
        expected_amplitude = 43210
        program = AmplificationProgram(amp_ctrl_software=intcode, amp_phase_list=amp_phase_list)
        signal_amplitude = program.run()
        self.assertEqual(signal_amplitude, expected_amplitude)

    def test_part_1_example_2(self):
        intcode = [3, 23, 3, 24, 1002, 24, 10, 24, 1002, 23, -1, 23, 101, 5, 23, 23, 1, 24, 23, 23, 4, 23, 99, 0, 0]
        amp_phase_list = [0, 1, 2, 3, 4]
        expected_amplitude = 54321
        program = AmplificationProgram(amp_ctrl_software=intcode, amp_phase_list=amp_phase_list)
        signal_amplitude = program.run()
        self.assertEqual(signal_amplitude, expected_amplitude)

    def test_part_1_example_3(self):
        intcode = [3, 31, 3, 32, 1002, 32, 10, 32, 1001, 31, -2, 31, 1007, 31, 0, 33, 1002, 33, 7, 33, 1, 33, 31, 31, 1,
                   32, 31, 31, 4, 31, 99, 0, 0, 0]
        amp_phase_list = [1, 0, 4, 3, 2]
        expected_amplitude = 65210
        program = AmplificationProgram(amp_ctrl_software=intcode, amp_phase_list=amp_phase_list)
        signal_amplitude = program.run()
        self.assertEqual(signal_amplitude, expected_amplitude)

    def test_part_2_example_1(self):
        intcode = [3, 26, 1001, 26, -4, 26, 3, 27, 1002, 27, 2, 27, 1, 27, 26,
                   27, 4, 27, 1001, 28, -1, 28, 1005, 28, 6, 99, 0, 0, 5]
        amp_phase_list = [9, 8, 7, 6, 5]
        expected_amplitude = 139629729
        program = AmplificationProgram(amp_ctrl_software=intcode, amp_phase_list=amp_phase_list)
        signal_amplitude = program.run()
        self.assertEqual(signal_amplitude, expected_amplitude)

    def test_part_2_example_2(self):
        intcode = [3, 52, 1001, 52, -5, 52, 3, 53, 1, 52, 56, 54, 1007, 54, 5, 55, 1005, 55, 26, 1001, 54,
                   -5, 54, 1105, 1, 12, 1, 53, 54, 53, 1008, 54, 0, 55, 1001, 55, 1, 55, 2, 53, 55, 53, 4,
                   53, 1001, 56, -1, 56, 1005, 56, 6, 99, 0, 0, 0, 0, 10]
        amp_phase_list = [9, 7, 8, 5, 6]
        expected_amplitude = 18216
        program = AmplificationProgram(amp_ctrl_software=intcode, amp_phase_list=amp_phase_list)
        signal_amplitude = program.run()
        self.assertEqual(signal_amplitude, expected_amplitude)


def day_7(txt_path: Path) -> List[int]:
    # Load puzzle input. Single row with comma separated integers.
    with open(str(txt_path), mode='r', newline='') as f:
        row = f.readline()
    # Convert the puzzle input into the Amplifier Controller Software, a List[int]
    amp_ctrl_software = [int(x) for x in row.split(',')]

    # When a copy of the program starts running on an amplifier, it will first use an input instruction to ask the
    # amplifier for its current phase setting (an integer from 0 to 4). Each phase setting is used exactly once,
    # but the Elves can't remember which amplifier needs which phase setting.
    amp_phase_permutations = permutations(iterable=range(5), r=5)

    # Part 1: Find the largest output signal that can be sent to the thrusters
    largest_signal = 0
    for amp_phase_tuple in amp_phase_permutations:

        program = AmplificationProgram(
            amp_ctrl_software=copy.copy(amp_ctrl_software),  # Do not modify the original program
            amp_phase_list=list(amp_phase_tuple),  # Convert the tuple into a list
        )
        signal_amplitude = program.run()
        if signal_amplitude > largest_signal:
            largest_signal = signal_amplitude

    part_1_answer = largest_signal

    # In feedback loop mode, the amplifiers need totally different phase settings:
    # integers from 5 to 9, again each used exactly once.
    feedback_amp_phase_permutations = permutations(iterable=range(5, 10), r=5)

    # Try every combination of the new phase settings on the amplifier feedback loop.
    # What is the highest signal that can be sent to the thrusters?
    largest_feedback_signal = 0
    for amp_phase_tuple in feedback_amp_phase_permutations:

        program = AmplificationProgram(
            amp_ctrl_software=copy.copy(amp_ctrl_software),  # Do not modify the original program
            amp_phase_list=list(amp_phase_tuple),  # Convert the tuple into a list
        )
        signal_amplitude = program.run()
        if signal_amplitude > largest_feedback_signal:
            largest_feedback_signal = signal_amplitude
    part_2_answer = largest_feedback_signal

    return [part_1_answer, part_2_answer]


def main():
    txt_path = Path(Path(__file__).parent, 'input_data', 'day_7_input.txt')

    answer = day_7(txt_path=txt_path)
    print(f'Day 7 Answers: {repr(answer)}')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Day7Tests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    main()
