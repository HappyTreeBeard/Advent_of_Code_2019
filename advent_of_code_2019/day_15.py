import copy
from collections import defaultdict
from enum import IntEnum, auto, Enum
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
    EMPTY = auto()
    WALL = auto()
    OXYGEN = auto()


@dataclass(frozen=True, order=True)
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


class RepairDroid(object):
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
        self.tile_map: Dict[Position, Tile] = dict()
        self.queue = Queue()
        self.successful_droids: List[RepairDroid] = list()

    def search_for_oxygen_leak(self, droid: RepairDroid):
        # Interpret the result from the previous droid movement
        # What was the last movement command send to this repair droid?
        if not droid.prev_move_cmd:
            # No commands have been send to this droid yet. We can assume the current position is empty
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
                self.successful_droids.append(droid)
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
            self.search_for_oxygen_leak(droid=clone)


def plot(dispatcher: DroidDispatcher):
    import matplotlib.pyplot as plt
    tiles_by_status = defaultdict(list)
    for tile in dispatcher.tile_map.values():
        tiles_by_status[tile.status].append(tile)

    for tile_status, tile_list in tiles_by_status.items():
        if tile_status == TileStatus.EMPTY:
            color = 'white'
        elif tile_status == TileStatus.WALL:
            color = 'black'
        else:
            color = 'green'

        x_list = list()
        y_list = list()
        for tile in tile_list:
            x_list.append(tile.position.x)
            y_list.append(tile.position.y)
        plt.scatter(x_list, y_list, c=color)

    current_position = Position(x=0, y=0)
    for successful_droid in dispatcher.successful_droids:
        x_list = list()
        y_list = list()
        x_list.append(current_position.x)
        y_list.append(current_position.y)
        for move_cmd in successful_droid.move_history:
            current_position = current_position + move_cmd
            x_list.append(current_position.x)
            y_list.append(current_position.y)
        plt.plot(x_list, y_list)
    plt.show()


def day_15(txt_path: Path) -> list:
    # Load puzzle input. Single row with comma separated integers.
    with open(str(txt_path), mode='r', newline='') as f:
        row = f.readline()
    # Convert the puzzle input into the Intcode software, a List[int]
    intcode = [int(x) for x in row.split(',')]

    repair_droid = RepairDroid(intcode=intcode)
    droid_dispatcher = DroidDispatcher()
    droid_dispatcher.search_for_oxygen_leak(droid=repair_droid)

    # Part 1: What is the fewest number of movement commands required to move the repair droid from its starting
    # position to the location of the oxygen system?
    steps_per_successful_droid = [len(x.move_history) for x in droid_dispatcher.successful_droids]
    part_1_answer = min(steps_per_successful_droid)

    part_2_answer = None

    return [part_1_answer, part_2_answer]


def main():
    txt_path = Path(Path(__file__).parent, 'input_data', 'day_15_input.txt')
    answer = day_15(txt_path=txt_path)
    print(f'Day 15 Answers: {repr(answer)}')


if __name__ == '__main__':
    main()
