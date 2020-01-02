import copy
import math
import unittest
from collections import defaultdict
from enum import IntEnum
from pathlib import Path
from typing import List, Dict

import numpy as np
from dataclasses import dataclass

from advent_of_code_2019.intcode_computer import IntCodeProgram


class Color(IntEnum):
    BLACK = 0
    WHITE = 1


class Rotation(IntEnum):
    LEFT_90 = 0
    RIGHT_90 = 1

    @property
    def rotation_matrix(self) -> np.ndarray:
        angle = math.pi / 2
        if self == self.RIGHT_90:
            angle *= -1

        return np.array([
            [np.cos(angle), -1 * np.sin(angle)],
            [np.sin(angle), np.cos(angle)],
        ])


@dataclass(frozen=True, order=True)
class Point(object):
    x: int
    y: int

    @property
    def ndarray(self) -> np.ndarray:
        return np.array([self.x, self.y])


@dataclass(frozen=True, order=True)
class Position(object):
    location: Point
    vector: Point


class HullPaintingRobot(object):
    def __init__(self, intcode: List[int]):
        self.program = IntCodeProgram(intcode=intcode)
        self.current_position = np.array([0, 0], dtype=np.int)  # [x,y]
        self.current_vector = np.array([0, 1], dtype=np.int)  # The robot starts facing up, i.e. pointing to (x=0, y=1)
        self.panel_color_map: Dict[Point, Color] = defaultdict(lambda: Color.BLACK)

    def run(self):
        continue_running = True

        while continue_running:
            # The program uses input instructions to access the robot's camera: provide 0 if the robot is over a
            # black panel or 1 if the robot is over a white panel.
            current_color = self.get_color_at_current_position()
            self.program.program_input.append(current_color)
            self.program.run()

            # First, it will output a value indicating the color to paint the panel the robot is over: 0 means to
            # paint the panel black, and 1 means to paint the panel white.
            new_color = Color(self.program.program_output.pop(0))
            self.apply_paint(color=new_color)

            # Second, it will output a value indicating the direction the robot should turn: 0 means it should turn
            # left 90 degrees, and 1 means it should turn right 90 degrees.
            rotation = Rotation(self.program.program_output.pop(0))
            # Turn the robot in the requested direction and move forward one panel
            self.apply_rotation_and_move(rotation=rotation)

            # Keep running until OpCode.FINISHED is hit.
            continue_running = not self.program.ran_to_completion

    def apply_paint(self, color: Color):
        x, y = self.current_position
        point = Point(x=x, y=y)
        self.panel_color_map[point] = color

    def apply_rotation_and_move(self, rotation: Rotation):
        # Apply the rotation by using a rotation matrix.
        self.current_vector = np.dot(rotation.rotation_matrix, self.current_vector).astype(dtype=np.int)
        # Apply the new vector to calculate the new position.
        # The magnitude of the vector is always 1 so the robot will only move one panel at a time.
        self.current_position = self.current_position + self.current_vector

    def get_color_at_current_position(self) -> Color:
        x, y = self.current_position
        point = Point(x=x, y=y)
        return self.panel_color_map[point]

    def _expand_panel_map(self):
        self.panel_color_map = np.full((1, 1), Color.BLACK)


class MockIntCodeProgram(IntCodeProgram):
    def __init__(self, colors: List[Color], rotations: List[Rotation], expected_input_list: list):
        super(MockIntCodeProgram, self).__init__(intcode=[])
        self.colors = colors
        self.rotations = rotations
        self.expected_input_list = expected_input_list

    def run(self):
        actual_input = self.program_input.pop(0)
        expected_input = self.expected_input_list.pop(0)
        if actual_input != expected_input:
            raise ValueError()

        self.program_output.extend([
            # First, it will output a value indicating the color to paint the panel the robot is over
            self.colors.pop(0),
            # Second, it will output a value indicating the direction the robot should turn
            self.rotations.pop(0),
        ])
        if not self.colors or not self.rotations:
            self.ran_to_completion = True


class Day9Tests(unittest.TestCase):

    def test_case(self):
        # 1) Suppose the robot eventually outputs 1 (paint white) and then 0 (turn left)
        # 2) Next, the robot might output 0 (paint black) and then 0 (turn left):
        # After more outputs (1,0, 1,0)
        expected_input_from_robot = [Color.BLACK, Color.BLACK, Color.BLACK, Color.BLACK]
        colors_from_program = [Color.WHITE, Color.BLACK, Color.WHITE, Color.WHITE]
        rotations_from_program = [Rotation.LEFT_90, Rotation.LEFT_90, Rotation.LEFT_90, Rotation.LEFT_90]

        # The robot is now back where it started, but because it is now on a white panel, input instructions should
        # be provided 1. After several more outputs (0,1, 1,0, 1,0), the area looks like this:
        # (paint, rotation), LEFT_90 = 0
        expected_input_from_robot.extend([Color.WHITE, Color.BLACK, Color.BLACK])
        colors_from_program.extend([Color.BLACK, Color.WHITE, Color.WHITE])
        rotations_from_program.extend([Rotation.RIGHT_90, Rotation.LEFT_90, Rotation.LEFT_90])

        # In the example above, the robot painted 6 panels at least once.
        expected_count = 6

        # .....
        # ..<#.
        # ...#.
        # .##..
        # .....
        expected_panel_color_map = {
            Point(x=0, y=0): Color.BLACK,
            Point(x=-1, y=0): Color.BLACK,
            Point(x=-1, y=-1): Color.WHITE,
            Point(x=0, y=-1): Color.WHITE,
            Point(x=1, y=0): Color.WHITE,
            Point(x=1, y=1): Color.WHITE,
        }

        robot = HullPaintingRobot(intcode=[])
        robot.program = MockIntCodeProgram(
            colors=colors_from_program,
            rotations=rotations_from_program,
            expected_input_list=expected_input_from_robot,
        )
        robot.run()

        self.assertEqual(len(robot.panel_color_map), expected_count)
        self.assertListEqual(robot.program.program_input, [])
        self.assertDictEqual(robot.panel_color_map, expected_panel_color_map)


def day_11(txt_path: Path) -> list:
    # Load puzzle input. Single row with comma separated integers.
    with open(str(txt_path), mode='r', newline='') as f:
        row = f.readline()
    # Convert the puzzle input into the Amplifier Controller Software, a List[int]
    intcode = [int(x) for x in row.split(',')]

    # Build a new emergency hull painting robot and run the Intcode program on it.
    robot = HullPaintingRobot(intcode=copy.copy(intcode))
    robot.run()

    # Part 1: How many panels does it paint at least once?
    part_1_answer = len(robot.panel_color_map)
    part_2_answer = None

    return [part_1_answer, part_2_answer]


def main():
    txt_path = Path(Path(__file__).parent, 'input_data', 'day_11_input.txt')
    answer = day_11(txt_path=txt_path)
    print(f'Day 11 Answers: {repr(answer)}')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Day9Tests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    main()
