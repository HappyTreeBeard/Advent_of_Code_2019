import copy
import unittest
from collections import defaultdict
from datetime import timedelta
from enum import IntEnum, Enum
from pathlib import Path
from queue import Queue
from typing import List, Optional, Dict

from dataclasses import dataclass

from advent_of_code_2019.intcode_computer import IntCodeProgram


class MovementCommand(IntEnum):
    NORTH = 1
    SOUTH = 2
    WEST = 3
    EAST = 4


@dataclass(frozen=True, order=True)
class Position(object):
    x: int
    y: int

    def __add__(self, other) -> 'Position':
        assert isinstance(other, MovementCommand)
        command = other
        dx = 0
        dy = 0
        if command == MovementCommand.NORTH:
            dy = 1
        elif command == MovementCommand.SOUTH:
            dy = -1
        elif command == MovementCommand.EAST:
            dx = 1
        elif command == MovementCommand.WEST:
            dx = -1
        return Position(x=self.x + dx, y=self.y + dy)


class TileStatus(Enum):
    EMPTY = '.'
    WALL = '#'
    OXYGEN = 'O'
    SPACE = ' '


@dataclass
class Tile(object):
    position: Position
    status: TileStatus


class StatusCode(IntEnum):
    WALL_HIT = 0
    """The repair droid hit a wall. Its position has not changed."""
    MOVE_SUCCESSFUL = 1
    """The repair droid has moved one step in the requested direction."""
    OXYGEN_DETECTED = 2
    """The repair droid has moved one step in the requested direction; 
    its new position is the location of the oxygen system."""


class Droid(object):
    def __init__(self, intcode: List[int]):
        self.program = IntCodeProgram(intcode=intcode)
        self.current_position = Position(x=0, y=0)
        self.prev_move_cmd: Optional[MovementCommand] = None
        self.move_history: List[MovementCommand] = list()

    def move(self, move_command: MovementCommand):
        self.prev_move_cmd = move_command
        self.program.program_input.append(move_command)
        self.program.run()


class DroidDispatcher(object):
    def __init__(self):
        self.tile_map: Dict[Position, Tile] = defaultdict()
        self.queue = Queue()
        self.successful_droids: List[Droid] = list()

    def run(self, droid: Droid):
        # Interpret the result from the previous droid movement
        # What was the last movement command send to this repair droid?
        if not droid.prev_move_cmd:
            # No commands have been send to this droid yet. We can assume the current position is empty
            if droid.current_position not in self.tile_map:
                self.tile_map[droid.current_position] = Tile(position=droid.current_position, status=TileStatus.EMPTY)
        else:
            status_code = StatusCode(droid.program.diagnostic_code)
            possible_position = droid.current_position + droid.prev_move_cmd

            # The robot position did not update if it hit a wall.
            if status_code != StatusCode.WALL_HIT:
                droid.current_position = possible_position
                droid.move_history.append(droid.prev_move_cmd)

            if status_code == StatusCode.WALL_HIT:
                status = TileStatus.WALL
            elif status_code == StatusCode.MOVE_SUCCESSFUL:
                status = TileStatus.EMPTY
            elif status_code == StatusCode.OXYGEN_DETECTED:
                status = TileStatus.OXYGEN
                self.successful_droids.append(copy.deepcopy(droid))
            else:
                raise ValueError(f'Unexpected {StatusCode}: {status_code}')

            self.tile_map[possible_position] = Tile(position=possible_position, status=status)

        # Send a droid in each possible direction
        for move_command in MovementCommand:
            next_position = droid.current_position + move_command
            if next_position in self.tile_map:
                # This position in this direction has already been visited and should be skipped.
                continue

            clone = copy.deepcopy(droid)
            clone.move(move_command=move_command)
            self.run(droid=clone)


class FlowSimulator(object):
    def __init__(self, tile_map: Dict[Position, Tile]):
        self.tile_map: Dict[Position, Tile] = tile_map

    def calculate_time_to_fill(self) -> timedelta:
        # Find all sources of oxygen
        oxygen_front_positions = [x.position for x in self.tile_map.values() if x.status == TileStatus.OXYGEN]
        delta_t = timedelta(minutes=0)
        # Continue simulating the flow of oxygen until the entire map has been filled
        while oxygen_front_positions:
            oxygen_front_positions = self.simulate_flow(oxygen_front_positions)
            if oxygen_front_positions:
                delta_t += timedelta(minutes=1)
        return delta_t

    def simulate_flow(self, oxygen_front_positions: List[Position]) -> List[Position]:
        new_oxygen_fronts = list()
        for position in oxygen_front_positions:
            # The oxygen can flow in any direction if it is empty
            for flow_direction in MovementCommand:
                next_position = position + flow_direction
                if self.tile_map[next_position].status == TileStatus.EMPTY:
                    # Fill this tile with oxygen and generate a new oxygen front
                    self.tile_map[next_position].status = TileStatus.OXYGEN
                    new_oxygen_fronts.append(next_position)
        return new_oxygen_fronts


class Day15Tests(unittest.TestCase):

    def test_part1_example1(self):
        # Test oxygen flow
        tile_str_list = [
            ' ##   ',
            '#..## ',
            '#.#..#',
            '#.O.# ',
            ' ###  ',
        ]
        # So, in this example, all locations contain oxygen after 4 minutes.
        expected = timedelta(minutes=4)
        tile_dict = dict()
        for y, tile_row in enumerate(tile_str_list):
            for x, tile_str in enumerate(tile_row):
                position = Position(x=x, y=y)
                status = TileStatus(tile_str)
                tile = Tile(position, status)
                tile_dict[position] = tile
        simulator = FlowSimulator(tile_map=tile_dict)
        actual = simulator.calculate_time_to_fill()
        self.assertEqual(actual, expected)


def day_15(txt_path: Path) -> list:
    # Load puzzle input. Single row with comma separated integers.
    with open(str(txt_path), mode='r', newline='') as f:
        row = f.readline()
    # Convert the puzzle input into the Intcode software, a List[int]
    intcode = [int(x) for x in row.split(',')]

    repair_droid = Droid(intcode=copy.copy(intcode))
    droid_dispatcher = DroidDispatcher()
    droid_dispatcher.run(droid=repair_droid)

    # Part 1: What is the fewest number of movement commands required to move the repair droid from its starting
    # position to the location of the oxygen system?
    steps_per_successful_droid = [len(x.move_history) for x in droid_dispatcher.successful_droids]
    part_1_answer = min(steps_per_successful_droid)

    # Part 2: How many minutes will it take to fill with oxygen?
    simulator = FlowSimulator(tile_map=droid_dispatcher.tile_map)
    time_delta = simulator.calculate_time_to_fill()
    part_2_answer = int(time_delta / timedelta(minutes=1))

    return [part_1_answer, part_2_answer]


def main():
    txt_path = Path(Path(__file__).parent, 'input_data', 'day_15_input.txt')
    answer = day_15(txt_path=txt_path)
    print(f'Day 15 Answers: {repr(answer)}')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Day15Tests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    main()
