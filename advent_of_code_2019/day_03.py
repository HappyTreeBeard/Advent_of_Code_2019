import unittest
from pathlib import Path
from typing import List, Optional

import dataclasses
from dataclasses import dataclass


@dataclass
class WireVector(object):
    value: str
    """The direction and distance of a wire segment, examples: 'R8' for right 8, 'U5' for up 5. """
    dx: int
    dy: int

    @classmethod
    def build_from_string(cls, value):
        direction = value[0]
        magnitude = int(value[1:])

        if direction == 'U':
            dx = 0
            dy = magnitude
        elif direction == 'D':
            dx = 0
            dy = -1 * magnitude
        elif direction == 'R':
            dx = magnitude
            dy = 0
        elif direction == 'L':
            dx = -1 * magnitude
            dy = 0
        else:
            raise ValueError(f"Unexpected direction: {direction}. Full string: {value}")

        return WireVector(
            value=value,
            dx=dx,
            dy=dy,
        )


@dataclass
class WirePoint(object):
    x: float
    y: float
    t_list: List[int] = dataclasses.field(default_factory=list)

    @property
    def manhattan_distance(self) -> int:
        return int(abs(self.x) + abs(self.y))


@dataclass(frozen=True, order=True)
class WireSegment(object):
    x0: float
    y0: float
    x1: float
    y1: float
    t0: Optional[int] = None
    t1: Optional[int] = None

    @property
    def a(self) -> float:
        return self.x0 - self.x1

    @property
    def b(self) -> float:
        return self.y1 - self.y0

    @property
    def c(self) -> float:
        return -1 * (self.y0 * self.x1 - self.y1 * self.x0)

    @property
    def x_list(self) -> List[float]:
        return [self.x0, self.x1]

    @property
    def y_list(self) -> List[float]:
        return [self.y0, self.y1]

    @property
    def t_list(self) -> List[int]:
        return [x for x in [self.t0, self.t1] if x]

    @property
    def distance(self) -> float:
        return abs(self.y1 - self.y0) + abs(self.x1 - self.x0)

    def intersection(self, other) -> Optional[WirePoint]:
        assert isinstance(other, WireSegment)
        d = self.a * other.b - self.b * other.a

        if d != 0:
            dx = self.a * other.c - self.c * other.a
            dy = self.c * other.b - self.b * other.c

            x = dx / d
            y = dy / d

            if (min(self.x_list) <= x <= max(self.x_list) and
                    min(self.y_list) <= y <= max(self.y_list) and
                    min(other.x_list) <= x <= max(other.x_list) and
                    min(other.y_list) <= y <= max(other.y_list)):
                t_list = self.t_list + other.t_list
                return WirePoint(x=x, y=y, t_list=t_list)
        return None


def build_segments_from_vectors(vector_list: List[WireVector]) -> List[WireSegment]:
    x = 0
    y = 0
    segment_list: List[WireSegment] = list()

    for t, vector in enumerate(vector_list):
        x0 = x
        y0 = y

        x += vector.dx
        y += vector.dy

        x1 = x
        y1 = y

        segment = WireSegment(x0=x0, y0=y0, x1=x1, y1=y1, t0=t, t1=t + 1)
        segment_list.append(segment)

    return segment_list


def find_intersection_points(segments_0: List[WireSegment], segments_1: List[WireSegment]) -> List[WirePoint]:
    intersections: List[WirePoint] = list()
    for s0 in segments_0:
        for s1 in segments_1:
            # Determine if the two segments intersect
            x_point = s0.intersection(other=s1)
            if x_point:
                intersections.append(x_point)
    return intersections


@dataclass
class WireLoop(object):
    segment_list: List[WireSegment]

    @property
    def num_steps(self) -> int:
        num_steps = 0
        for s in self.segment_list:
            num_steps += abs(s.x1 - s.x0)
            num_steps += abs(s.y1 - s.y0)
        return num_steps


def find_intersection_loops(segments_0: List[WireSegment], segments_1: List[WireSegment]) -> List[WireLoop]:
    wire_loop_list: List[WireLoop] = list()
    for i, si in enumerate(segments_0):
        for j, sj in enumerate(segments_1):
            # Determine if the two segments intersect
            x_point = si.intersection(other=sj)
            if x_point:
                # Build a list of the previous segments for each wire
                # This will not include the two segments which intersect
                s0_to_si_minus_1 = segments_0[0:i]
                s1_to_sj_minus_1 = segments_1[0:j]

                # Build a segment from the start point to the intersection point for both wires
                s0_sub_segment = WireSegment(
                    x0=si.x0,
                    x1=x_point.x,
                    y0=si.y0,
                    y1=x_point.y,
                )
                s1_sub_segment = WireSegment(
                    x0=sj.x0,
                    x1=x_point.x,
                    y0=sj.y0,
                    y1=x_point.y,
                )

                # The WireLoop object is a list of connected WireSegment that eventually loops back to the start.
                segment_list = s0_to_si_minus_1
                segment_list.append(s0_sub_segment)
                segment_list.append(s1_sub_segment)
                # Reverse the segment list of the second wire
                segment_list.extend(list(reversed(s1_to_sj_minus_1)))
                wire_loop = WireLoop(segment_list=segment_list)
                wire_loop_list.append(wire_loop)
    return wire_loop_list


class Day3Tests(unittest.TestCase):

    def test_wire_vector(self):
        vector = WireVector.build_from_string(value='R998')
        self.assertEqual(vector.dx, 998)
        self.assertEqual(vector.dy, 0)

        vector = WireVector.build_from_string(value='U547')
        self.assertEqual(vector.dx, 0)
        self.assertEqual(vector.dy, 547)

        vector = WireVector.build_from_string(value='L780')
        self.assertEqual(vector.dx, -780)
        self.assertEqual(vector.dy, 0)

        vector = WireVector.build_from_string(value='D843')
        self.assertEqual(vector.dx, 0)
        self.assertEqual(vector.dy, -843)

    def test_segment_intersect_0(self):
        segment_0 = WireSegment(x0=0, y0=1, x1=1, y1=3)
        segment_1 = WireSegment(x0=-1, y0=4, x1=2, y1=0)
        x_point = segment_0.intersection(other=segment_1)
        self.assertIsInstance(x_point, WirePoint)
        self.assertEqual(
            WirePoint(x=0.5, y=2.0), x_point)

        segment_0 = WireSegment(x0=99, y0=2619, x1=-869, y1=2619)
        segment_1 = WireSegment(x0=-364, y0=3058, x1=-364, y1=2092)
        x_point = segment_0.intersection(other=segment_1)
        self.assertIsInstance(x_point, WirePoint)
        self.assertEqual(WirePoint(x=-364, y=2619), x_point)

        segment_0 = WireSegment(x0=0, y0=0, x1=0, y1=3)
        segment_1 = WireSegment(x0=0, y0=3, x1=0, y1=6)
        x_point = segment_0.intersection(other=segment_1)
        self.assertIsNone(x_point)

    def test_segment_intersect_1(self):
        self.assertIsNone(
            WireSegment(x0=0, y0=0, x1=998, y1=0).intersection(
                WireSegment(x0=-995, y0=0, x1=-995, y1=122))
        )

        self.assertIsNone(
            WireSegment(x0=998, y0=0, x1=998, y1=547).intersection(
                WireSegment(x0=0, y0=0, x1=-995, y1=0))
        )

    @staticmethod
    def str_to_segment_list(vector_list_str: str):
        wire_vector_list = []
        for vector_str in vector_list_str.split(','):
            vector = WireVector.build_from_string(value=vector_str)
            wire_vector_list.append(vector)
        wire_segment_list = build_segments_from_vectors(wire_vector_list)
        return wire_segment_list

    def process_example(self, vectors_str_0: str, vectors_str_1: str, expected_distance: int, expected_steps: int):
        """
        :param vectors_str_0: Comma separated vector strings for wire 0
        :param vectors_str_1: Comma separated vector strings for wire 1
        :param expected_distance: The expected Manhattan distance
        :param expected_steps: The expected number of steps for the shortest loop
        """
        segments_0 = self.str_to_segment_list(vectors_str_0)
        segments_1 = self.str_to_segment_list(vectors_str_1)

        intersections = find_intersection_points(
            segments_0=segments_0,
            segments_1=segments_1,
        )

        wire_point = find_smallest_manhattan_distance(wire_point_list=intersections)
        self.assertEqual(wire_point.manhattan_distance, expected_distance)

        wire_loop_list = find_intersection_loops(
            segments_0=segments_0,
            segments_1=segments_1,
        )
        shortest_loop = find_shortest_loop(wire_loop_list=wire_loop_list)
        self.assertEqual(shortest_loop.num_steps, expected_steps)

    def test_example_0(self):
        vectors_str_0 = 'R8,U5,L5,D3'
        vectors_str_1 = 'U7,R6,D4,L4'
        expected_distance = 6
        expected_steps = 30

        self.process_example(vectors_str_0, vectors_str_1, expected_distance, expected_steps)

    def test_example_1(self):
        vectors_str_0 = 'R75,D30,R83,U83,L12,D49,R71,U7,L72'
        vectors_str_1 = 'U62,R66,U55,R34,D71,R55,D58,R83'

        expected_distance = 159
        expected_steps = 610

        self.process_example(vectors_str_0, vectors_str_1, expected_distance, expected_steps)

    def test_example_2(self):
        vectors_str_0 = 'R98,U47,R26,D63,R33,U87,L62,D20,R33,U53,R51'
        vectors_str_1 = 'U98,R91,D20,R16,D67,R40,U7,R15,U6,R7'

        expected_distance = 135
        expected_steps = 410

        self.process_example(vectors_str_0, vectors_str_1, expected_distance, expected_steps)


def find_smallest_manhattan_distance(wire_point_list: List[WirePoint]) -> WirePoint:
    closest_point: Optional[WirePoint] = None
    for x_point in wire_point_list:
        # Ignore intersections that occur at the origin
        if x_point.manhattan_distance == 0:
            continue
        if closest_point:
            if x_point.manhattan_distance < closest_point.manhattan_distance:
                closest_point = x_point
        else:
            closest_point = x_point
    return closest_point


def find_shortest_loop(wire_loop_list: List[WireLoop]) -> WireLoop:
    shortest_loop: Optional[WireLoop] = None
    for wire_loop in wire_loop_list:
        # Ignore loops where the intersections of wires occur at the origin
        if wire_loop.num_steps == 0:
            continue
        if shortest_loop:
            if wire_loop.num_steps < shortest_loop.num_steps:
                shortest_loop = wire_loop
        else:
            shortest_loop = wire_loop
    return shortest_loop


def day_3(txt_path: Path) -> Optional[List[int]]:
    with open(str(txt_path), 'r', newline='') as f:
        row_list = [row for row in f.readlines()]

    multi_wire_segments: List[List[WireSegment]] = list()
    for row in row_list:
        wire_vector_list = [WireVector.build_from_string(x) for x in row.split(',')]
        wire_segment_list = build_segments_from_vectors(wire_vector_list)
        multi_wire_segments.append(wire_segment_list)

    segments_0 = multi_wire_segments[0]
    segments_1 = multi_wire_segments[1]

    # Find the intersection points between both wire segments
    intersections = find_intersection_points(
        segments_0=segments_0,
        segments_1=segments_1,
    )

    # Find the intersection with the smallest Manhattan distance
    closest_intersection = find_smallest_manhattan_distance(wire_point_list=intersections)

    # Build a loop that connects both wires at the intersection point
    wire_loop_list = find_intersection_loops(
        segments_0=segments_0,
        segments_1=segments_1,
    )

    # Determine which loop has the fewest number of steps
    shortest_loop = find_shortest_loop(wire_loop_list=wire_loop_list)

    # Part 1: What is the Manhattan distance from the central port to the closest intersection?
    part_1 = closest_intersection.manhattan_distance
    # Part 2: What is the fewest combined steps the wires must take to reach an intersection?
    part_2 = shortest_loop.num_steps
    answer = [part_1, part_2]

    return answer


def main():
    txt_path = Path(Path(__file__).parent, 'input_data', 'day_3_input.txt')
    answer = day_3(txt_path=txt_path)
    print(f'Day 3 Answers: {repr(answer)}')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Day3Tests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    main()
