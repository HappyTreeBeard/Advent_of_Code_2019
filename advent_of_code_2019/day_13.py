import copy
import unittest
from enum import IntEnum
from pathlib import Path
from typing import List, Optional

from dataclasses import dataclass

from advent_of_code_2019.intcode_computer import IntCodeProgram


class TileId(IntEnum):
    EMPTY = 0
    WALL = 1
    BLOCK = 2
    HORIZONTAL_PADDLE = 3
    BALL = 4


class Joystick(IntEnum):
    NEUTRAL = 0
    TILT_LEFT = -1
    TILT_RIGHT = 1


@dataclass
class GameTile(object):
    x: int
    y: int
    tile_id: TileId


class Arcade(object):
    def __init__(self, intcode: List[int]):
        self.program = IntCodeProgram(intcode=intcode)
        self.tile_list: List[GameTile] = list()
        self.player_score = 0
        self.ball: Optional[GameTile] = None
        self.ball_history: List[GameTile] = list()
        self.paddle: Optional[GameTile] = None

    def poll_joystick(self) -> Joystick:
        # Move the paddle in the direction of the ball
        if self.paddle and self.ball:
            # Do not move if the ball is one pixel above the paddle.
            if self.ball.y + 1 == self.paddle.y and self.ball.x == self.paddle.x:
                return Joystick.NEUTRAL

            if len(self.ball_history) > 1:
                ball_t0 = self.ball_history[-2]
                ball_t1 = self.ball_history[-1]

                # If the ball is moving toward the paddle, the dY will be positive
                # If the ball is moving away from the paddle, the dY will be negative
                y0 = ball_t0.y
                y1 = ball_t1.y
                dy = y1 - y0
                if dy > 0:
                    # Ball is moving towards the paddle
                    # If the ball continues on this path, what is the ball's next X position?
                    # Move the paddle toward the ball's next X position
                    x0 = ball_t0.x
                    x1 = ball_t1.x
                    dx = x1 - x0
                    x2 = dx + x1
                else:
                    # Ball is moving away from the paddle. Attempt to say under the balls.
                    x2 = ball_t1.x

                if self.paddle.x < x2:
                    return Joystick.TILT_RIGHT  # Move right to increase the X position
                elif self.paddle.x > x2:
                    return Joystick.TILT_LEFT  # Move left to decrease the X position

        return Joystick.NEUTRAL

    def run(self):
        while not self.program.ran_to_completion:
            self.program.run()

            # Read from the program output to update positions of game tiles
            while self.program.program_output:
                # The software draws tiles to the screen with output instructions: every three output instructions
                # specify the x position (distance from the left), y position (distance from the top), and tile id.
                x = self.program.program_output.pop(0)
                y = self.program.program_output.pop(0)
                tile_id_int = self.program.program_output.pop(0)

                # When three output instructions specify X=-1, Y=0, the third output instruction is not a tile; the
                # value instead specifies the new score to show in the segment display.
                if x == -1 and y == 0:
                    self.player_score = tile_id_int
                else:
                    tile = GameTile(x=x, y=y, tile_id=TileId(tile_id_int))
                    # Cache the locations of the ball and paddle. Assumes only 1 ball and paddle are ever created.
                    if tile.tile_id == TileId.BALL:
                        self.ball_history.append(tile)
                        self.ball = tile
                    elif tile.tile_id == TileId.HORIZONTAL_PADDLE:
                        self.paddle = tile
                    self.tile_list.append(tile)

            if not self.program.ran_to_completion:
                # The program is waiting for the joystick input
                joystick_position = self.poll_joystick()
                self.program.program_input.append(joystick_position)


class MockIntCodeProgram(IntCodeProgram):
    def __init__(self, program_output: List[int]):
        super(MockIntCodeProgram, self).__init__(intcode=[])
        self.program_output = program_output

    def run(self):
        self.ran_to_completion = True


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


def day_13(txt_path: Path) -> list:
    # Load puzzle input. Single row with comma separated integers.
    with open(str(txt_path), mode='r', newline='') as f:
        row = f.readline()
    # Convert the puzzle input into the Intcode software, a List[int]
    intcode = [int(x) for x in row.split(',')]

    arcade = Arcade(intcode=copy.copy(intcode))
    arcade.enable_screen_render = False
    arcade.run()

    # Part 1: How many block tiles are on the screen when the game exits?
    block_tiles = [x for x in arcade.tile_list if x.tile_id == TileId.BLOCK]
    part_1_answer = len(block_tiles)

    # Memory address 0 represents the number of quarters that have been inserted; set it to 2 to play for free.
    arcade = Arcade(intcode=copy.copy(intcode))
    arcade.program.intcode[0] = 2
    arcade.enable_screen_render = False
    arcade.cheat_mode = True
    arcade.run()

    # Beat the game by breaking all the blocks. What is your score after the last block is broken?
    part_2_answer = arcade.player_score

    return [part_1_answer, part_2_answer]


def main():
    txt_path = Path(Path(__file__).parent, 'input_data', 'day_13_input.txt')
    answer = day_13(txt_path=txt_path)
    print(f'Day 13 Answers: {repr(answer)}')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Day13Tests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    main()
