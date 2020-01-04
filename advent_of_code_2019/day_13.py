import unittest
from enum import IntEnum
from pathlib import Path
from typing import List

from dataclasses import dataclass

from advent_of_code_2019.intcode_computer import IntCodeProgram


class TileId(IntEnum):
    EMPTY = 0
    WALL = 1
    BLOCK = 2
    HORIZONTAL_PADDLE = 3
    BALL = 4


@dataclass
class GameTile(object):
    x: int
    y: int
    tile_id: TileId


class Arcade(object):
    def __init__(self, intcode: List[int]):
        self.program = IntCodeProgram(intcode=intcode)
        self.tile_list: List[GameTile] = list()

    def run(self):
        self.program.run()
        while self.program.program_output:
            # The software draws tiles to the screen with output instructions: every three output instructions
            # specify the x position (distance from the left), y position (distance from the top), and tile id.
            x = self.program.program_output.pop(0)
            y = self.program.program_output.pop(0)
            tile_id_int = self.program.program_output.pop(0)
            tile = GameTile(x=x, y=y, tile_id=TileId(tile_id_int))
            self.tile_list.append(tile)


class MockIntCodeProgram(IntCodeProgram):
    def __init__(self, program_output: List[int]):
        super(MockIntCodeProgram, self).__init__(intcode=[])
        self.program_output = program_output

    def run(self):
        pass


class Day13Tests(unittest.TestCase):

    def test_part1_example1(self):
        # For example, a sequence of output values like 1,2,3,6,5,4 would draw a horizontal paddle tile (1 tile from
        # the left and 2 tiles from the top) and a ball tile (6 tiles from the left and 5 tiles from the top).
        program_output = [1, 2, 3, 6, 5, 4]
        expected_tiles = [
            GameTile(x=1, y=2, tile_id=TileId.HORIZONTAL_PADDLE),
            GameTile(x=6, y=5, tile_id=TileId.BALL),
        ]
        arcade = Arcade(intcode=[])
        arcade.program = MockIntCodeProgram(program_output=program_output)
        arcade.run()
        self.assertListEqual(arcade.program.program_output, [])
        self.assertListEqual(arcade.tile_list, expected_tiles)
        pass


def day_13(txt_path: Path) -> list:
    # Load puzzle input. Single row with comma separated integers.
    with open(str(txt_path), mode='r', newline='') as f:
        row = f.readline()
    # Convert the puzzle input into the Intcode software, a List[int]
    intcode = [int(x) for x in row.split(',')]

    arcade = Arcade(intcode=intcode)
    arcade.run()

    # Part 1: How many block tiles are on the screen when the game exits?
    block_tiles = [x for x in arcade.tile_list if x.tile_id == TileId.BLOCK]
    part_1_answer = len(block_tiles)

    part_2_answer = None

    return [part_1_answer, part_2_answer]


def main():
    txt_path = Path(Path(__file__).parent, 'input_data', 'day_13_input.txt')
    answer = day_13(txt_path=txt_path)
    print(f'Day 13 Answers: {repr(answer)}')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Day13Tests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    main()
