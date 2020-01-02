import copy
import math
import unittest
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional

from dataclasses import dataclass


class AsteroidMapElement(Enum):
    """The type of elements that can be found within an asteroid map, either empty space or an asteroid"""
    ASTEROID = '#'
    SPACE = '.'


@dataclass(frozen=True, order=True)
class Asteroid(object):
    x: int
    y: int


@dataclass
class VisibleAsteroid(object):
    asteroid: Asteroid
    other_asteroid: Asteroid

    @property
    def dx(self) -> float:
        return self.other_asteroid.x - self.asteroid.x

    @property
    def dy(self) -> float:
        return self.other_asteroid.y - self.asteroid.y

    @property
    def angle(self) -> float:
        """Calculate the angle between the two asteroids in degrees. """
        angle_rad = math.atan2(self.dy, self.dx)  # Radians between (-pi/2, pi/2]
        angle_degrees = angle_rad * 180 / math.pi
        # Convert to range between [0, 360) where 0 deg points to (x=1, y=0) and rotates clockwise with respect
        # to the asteroid maps because the Y axis goes from top to bottom.
        normalized_angle = (angle_degrees + 360) % 360

        # The laser uses a different orientation where 0 deg points to (x=0, y=-1) and rotates clockwise.
        # Convert this angle to match the orientation/direction of laser by rotating by 90 degrees.
        laser_angle = (normalized_angle + 90) % 360

        return laser_angle

    @property
    def distance(self) -> float:
        """Calculate distance between the two asteroids using Pythagorean theorem"""
        return math.sqrt(pow(self.dx, 2) + pow(self.dy, 2))


@dataclass
class AsteroidMonitoringStation(object):
    asteroid: Asteroid
    full_asteroid_list: List[Asteroid]
    _cached_visible_asteroid_list: Optional[List[VisibleAsteroid]] = None

    def vaporize_asteroids(self) -> List[Asteroid]:
        """ Vaporize all asteroids and return a list of asteroids in the order in which they were destroyed.

        :return: A list of Asteroid objects in the order in which they will be vaporized.
        :rtype: List[Asteroid]
        """
        vaporized_asteroids = list()
        visible_asteroids = self.find_visible_asteroids()
        while len(visible_asteroids) > 0:
            # Sort the visible asteroids by the angle of the laser
            sorted_visible_asteroids = sorted(visible_asteroids, key=lambda x: x.angle)
            sorted_asteroids = [x.other_asteroid for x in sorted_visible_asteroids]

            vaporized_asteroids.extend(sorted_asteroids)

            # Remove the asteroids as they are vaporized.
            for asteroid in sorted_asteroids:
                self.full_asteroid_list.remove(asteroid)

            # Clear the visible asteroid cache so find_visible_asteroids() will search for new asteroids
            self._cached_visible_asteroid_list = None
            visible_asteroids = self.find_visible_asteroids()

        return vaporized_asteroids

    def find_visible_asteroids(self) -> List[VisibleAsteroid]:
        if self._cached_visible_asteroid_list is not None:
            return self._cached_visible_asteroid_list

        # Determine which asteroids will be occluded/blocked by closer asteroids
        # Track which asteroids are occluded using a dictionary where the key is the angle
        visible_asteroid_dict: Dict[float, VisibleAsteroid] = dict()
        for other_asteroid in self.full_asteroid_list:
            if self.asteroid == other_asteroid:
                continue
            # Build a VisibleAsteroid object for each asteroid pair.
            # This is used to calculate distance and angle between the asteroids.
            visible_asteroid = VisibleAsteroid(asteroid=self.asteroid, other_asteroid=other_asteroid)
            angle = visible_asteroid.angle * 180 / math.pi

            if angle not in visible_asteroid_dict:
                # No other asteroids share the same observation angle.
                visible_asteroid_dict[angle] = visible_asteroid
            elif visible_asteroid.distance < visible_asteroid_dict[angle].distance:
                # Two asteroids share the same observation angle.
                # The closer asteroid will occlude the other asteroid.
                visible_asteroid_dict[angle] = visible_asteroid

        visible_asteroids = list(visible_asteroid_dict.values())
        self._cached_visible_asteroid_list = visible_asteroids
        return visible_asteroids

    def num_visible_asteroids(self) -> int:
        return len(self.find_visible_asteroids())


@dataclass
class AsteroidCollection(object):
    asteroids: List[Asteroid]

    def build_monitor_station(self, asteroid: Asteroid) -> AsteroidMonitoringStation:
        """ Build a AsteroidMonitoringStation object showing which asteroids are visible.

        :param asteroid: The target location for the monitoring station
        :type asteroid: Asteroid
        :return: The AsteroidMonitoringStation
        :rtype: AsteroidMonitoringStation
        """
        monitoring_station = AsteroidMonitoringStation(
            asteroid=asteroid,
            full_asteroid_list=copy.copy(self.asteroids),
        )
        return monitoring_station

    def find_all_monitor_locations(self) -> List[AsteroidMonitoringStation]:
        """ Find the all possible asteroid monitoring stations and which asteroids can be visible.

        :return: All possible AsteroidMonitoringStation
        :rtype: List[AsteroidMonitoringStation]
        """
        monitoring_station_list: List[AsteroidMonitoringStation] = list()
        for asteroid in self.asteroids:
            monitoring_station = self.build_monitor_station(asteroid=asteroid)
            monitoring_station_list.append(monitoring_station)
        return monitoring_station_list

    def find_best_monitor_location(self) -> AsteroidMonitoringStation:
        """ Find the best location for an asteroid monitoring station which can detect the largest number of other
        asteroids, i.e. has a direct line-of-sight.

        :return: The best location for an AsteroidMonitoringStation
        :rtype: AsteroidMonitoringStation
        """
        monitoring_station_list = self.find_all_monitor_locations()
        best_monitoring_station: Optional[AsteroidMonitoringStation] = None
        for monitoring_station in monitoring_station_list:
            if best_monitoring_station is None:
                best_monitoring_station = monitoring_station
            elif monitoring_station.num_visible_asteroids() > best_monitoring_station.num_visible_asteroids():
                best_monitoring_station = monitoring_station
        return best_monitoring_station


def build_asteroid_collection_from_map(asteroid_map: List[str]) -> AsteroidCollection:
    """ Build a AsteroidCollection object that tracks all asteroids found in the provided asteroid_map.

    :param asteroid_map: A list of strings where each string represents a map row and each digit of that string
    represents either space '.' or an asteroid '#'.
    :type asteroid_map: List[str]
    :return: The constructed AsteroidCollection
    :rtype: AsteroidCollection
    """
    asteroids = list()
    for y, map_row in enumerate(asteroid_map):
        for x, element in enumerate(map_row):
            # Ignore 'space' elements found in the asteroid map. Only add asteroids.
            if AsteroidMapElement(element) == AsteroidMapElement.ASTEROID:
                asteroids.append(Asteroid(x=x, y=y))
    return AsteroidCollection(asteroids=asteroids)


class Day10Tests(unittest.TestCase):

    def test_asteroid_visible_count(self):
        asteroid_map = [
            '.#..#',
            '.....',
            '#####',
            '....#',
            '...##',
        ]
        # The asteroid at 1,0 should be able to detect 7 asteroids
        target_asteroid = Asteroid(x=1, y=0)
        expected_asteroid_count = 7
        asteroid_collection = build_asteroid_collection_from_map(asteroid_map=asteroid_map)
        monitor_station = asteroid_collection.build_monitor_station(asteroid=target_asteroid)
        self.assertEqual(monitor_station.asteroid, target_asteroid)
        self.assertEqual(monitor_station.num_visible_asteroids(), expected_asteroid_count)

        # The asteroid at 4,2 should be able to detect 5 asteroids
        target_asteroid = Asteroid(x=4, y=2)
        expected_asteroid_count = 5
        asteroid_collection = build_asteroid_collection_from_map(asteroid_map=asteroid_map)
        monitor_station = asteroid_collection.build_monitor_station(asteroid=target_asteroid)
        self.assertEqual(monitor_station.asteroid, target_asteroid)
        self.assertEqual(monitor_station.num_visible_asteroids(), expected_asteroid_count)

        # The asteroid at 4,2 should be able to detect 5 asteroids
        target_asteroid = Asteroid(x=1, y=2)
        expected_asteroid_count = 7
        asteroid_collection = build_asteroid_collection_from_map(asteroid_map=asteroid_map)
        monitor_station = asteroid_collection.build_monitor_station(asteroid=target_asteroid)
        self.assertEqual(monitor_station.asteroid, target_asteroid)

        self.assertEqual(monitor_station.num_visible_asteroids(), expected_asteroid_count)

    def test_asteroid_occlusion(self):
        # Here is an asteroid (#) and some examples of the ways its line of sight might be blocked. If there were
        # another asteroid at the location of a capital letter, the locations marked with the corresponding lowercase
        # letter would be blocked and could not be detected:

        asteroid_occlusion_map = [
            '#.........',
            '...A......',
            '...B..a...',
            '.EDCG....a',
            '..F.c.b...',
            '.....c....',
            '..efd.c.gb',
            '.......c..',
            '....f...c.',
            '...e..d..c',
        ]
        target_asteroid = Asteroid(x=0, y=0)

        asteroid_map = list()  # Converted asteroid map without letters
        visible_asteroid_count = 0  # Count the number of asteroids that should be observable
        for row in asteroid_occlusion_map:
            asteroid_row = list()
            for element in row:
                # Capital letters represent asteroids that are visible
                if element.isupper():
                    visible_asteroid_count += 1
                # Create a regular asteroid map by converting the letters into asteroid symbols
                if element.isalpha():
                    asteroid_row.append('#')
                else:
                    asteroid_row.append(element)
            asteroid_row_str = ''.join(asteroid_row)
            asteroid_map.append(asteroid_row_str)

        asteroid_collection = build_asteroid_collection_from_map(asteroid_map=asteroid_map)
        monitor_station = asteroid_collection.build_monitor_station(asteroid=target_asteroid)

        self.assertEqual(monitor_station.asteroid, target_asteroid)
        self.assertEqual(monitor_station.num_visible_asteroids(), visible_asteroid_count)

    def test_part1_simple_example(self):
        # The best location for a new monitoring station on this map is at 3,4 because it can detect 8 asteroids,
        asteroid_map = [
            '.#..#',
            '.....',
            '#####',
            '....#',
            '...##',
        ]
        expected_asteroid = Asteroid(x=3, y=4)
        expected_num_visible_asteroid = 8

        asteroid_collection = build_asteroid_collection_from_map(asteroid_map=asteroid_map)
        self.assertIn(Asteroid(x=1, y=0), asteroid_collection.asteroids)
        self.assertIn(expected_asteroid, asteroid_collection.asteroids)
        self.assertEqual(10, len(asteroid_collection.asteroids))

        self.check_monitor_station(asteroid_map, expected_asteroid, expected_num_visible_asteroid)

    def test_part1_large_example1(self):
        # Best is 5,8 with 33 other asteroids detected
        expected_asteroid = Asteroid(x=5, y=8)
        expected_num_visible_asteroid = 33
        asteroid_map = [
            '......#.#.',
            '#..#.#....',
            '..#######.',
            '.#.#.###..',
            '.#..#.....',
            '..#....#.#',
            '#..#....#.',
            '.##.#..###',
            '##...#..#.',
            '.#....####',
        ]
        self.check_monitor_station(asteroid_map, expected_asteroid, expected_num_visible_asteroid)

    def test_part1_large_example2(self):
        # Best is 1,2 with 35 other asteroids detected
        expected_asteroid = Asteroid(x=1, y=2)
        expected_num_visible_asteroid = 35
        asteroid_map = [
            '#.#...#.#.',
            '.###....#.',
            '.#....#...',
            '##.#.#.#.#',
            '....#.#.#.',
            '.##..###.#',
            '..#...##..',
            '..##....##',
            '......#...',
            '.####.###.',
        ]
        self.check_monitor_station(asteroid_map, expected_asteroid, expected_num_visible_asteroid)

    def test_part1_large_example3(self):
        # Best is 6,3 with 41 other asteroids detected
        expected_asteroid = Asteroid(x=6, y=3)
        expected_num_visible_asteroid = 41
        asteroid_map = [
            '.#..#..###',
            '####.###.#',
            '....###.#.',
            '..###.##.#',
            '##.##.#.#.',
            '....###..#',
            '..#.#..#.#',
            '#..#.#.###',
            '.##...##.#',
            '.....#.#..',
        ]
        self.check_monitor_station(asteroid_map, expected_asteroid, expected_num_visible_asteroid)

    def test_part1_large_example4(self):
        # Best is 11,13 with 210 other asteroids detected
        expected_asteroid = Asteroid(x=11, y=13)
        expected_num_visible_asteroid = 210
        asteroid_map = [
            '.#..##.###...#######',
            '##.############..##.',
            '.#.######.########.#',
            '.###.#######.####.#.',
            '#####.##.#.##.###.##',
            '..#####..#.#########',
            '####################',
            '#.####....###.#.#.##',
            '##.#################',
            '#####.##.###..####..',
            '..######..##.#######',
            '####.##.####...##..#',
            '.#####..#.######.###',
            '##...#.##########...',
            '#.##########.#######',
            '.####.#.###.###.#.##',
            '....##.##.###..#####',
            '.#.#.###########.###',
            '#.#.#.#####.####.###',
            '###.##.####.##.#..##',
        ]
        self.check_monitor_station(asteroid_map, expected_asteroid, expected_num_visible_asteroid)

    def check_monitor_station(self, asteroid_map: List[str], asteroid: Asteroid, num_visible_asteroid: int):
        """ Verify the correct asteroid monitoring station is selected.

        :param asteroid_map: The asteroid map.
        :type asteroid_map: List[str]
        :param asteroid: The expected asteroid position for the best asteroid monitoring station.
        :type asteroid: Asteroid
        :param num_visible_asteroid: The number of asteroids that are visible at the monitoring station.
        :type num_visible_asteroid: int
        """
        asteroid_collection = build_asteroid_collection_from_map(asteroid_map=asteroid_map)
        monitor_station = asteroid_collection.find_best_monitor_location()
        self.assertEqual(monitor_station.asteroid, asteroid)
        self.assertEqual(monitor_station.num_visible_asteroids(), num_visible_asteroid)

    def test_part2_vaporization1(self):
        # The asteroid with the new monitoring station (and laser) is marked X
        asteroid_station_map = [
            '.#....#####...#..',
            '##...##.#####..##',
            '##...#...#.#####.',
            '..#.....X...###..',
            '..#.#.....#....##',
        ]
        # Find the location of the monitoring station and replace it with an asteroid symbol
        asteroid_map = list()
        target_asteroid: Optional[Asteroid] = None
        for y, row in enumerate(asteroid_station_map):
            asteroid_row = list()
            for x, element in enumerate(row):
                if element == 'X':
                    target_asteroid = Asteroid(x=x, y=y)
                    element = '#'
                asteroid_row.append(element)
            asteroid_row_str = ''.join(asteroid_row)
            asteroid_map.append(asteroid_row_str)

        asteroid_collection = build_asteroid_collection_from_map(asteroid_map=asteroid_map)
        monitor_station = asteroid_collection.build_monitor_station(asteroid=target_asteroid)
        self.assertEqual(monitor_station.asteroid, target_asteroid)

        # The first nine asteroids to get vaporized, in order, would be:
        vaporize_map_0 = [
            '.#....###24...#..',
            '##...##.13#67..9#',
            '##...#...5.8####.',
            '..#.....X...###..',
            '..#.#.....#....##',
        ]
        vaporize_map_1 = [
            '.#....###.....#..',
            '##...##...#.....#',
            '##...#......1234.',
            '..#.....X...5##..',
            '..#.9.....8....76',
        ]
        vaporize_map_2 = [
            '.8....###.....#..',
            '56...9#...#.....#',
            '34...7...........',
            '..2.....X....##..',
            '..1..............',
        ]
        vaporize_map_3 = [
            '......234.....6..',
            '......1...5.....7',
            '.................',
            '........X....89..',
            '.................',
        ]

        # Process all vaporization maps to determine when each asteroid is vaporized.
        expected_vaporized_asteroids = \
            self.process_vaporization_map(vaporize_map_0) + \
            self.process_vaporization_map(vaporize_map_1) + \
            self.process_vaporization_map(vaporize_map_2) + \
            self.process_vaporization_map(vaporize_map_3)

        actual_vaporized_asteroids = monitor_station.vaporize_asteroids()

        self.assertListEqual(actual_vaporized_asteroids, expected_vaporized_asteroids)

    @staticmethod
    def process_vaporization_map(vaporize_map: List[str]) -> List[Asteroid]:
        """ Process the asteroid vaporization map with numbers indicating the order in which the asteroids were
        vaporized.

        :param vaporize_map: A list of asteroids in the order in which they will be vaporized.
        :type vaporize_map: List[str]
        :return: A list of Asteroid objects in the order in which they will be vaporized.
        :rtype: List[Asteroid]
        """

        @dataclass
        class VaporizedAsteroid(object):
            asteroid: Asteroid
            vaporization_order: int
            """The time point at which this asteroid was vaporized."""

        vaporized_asteroids: List[VaporizedAsteroid] = list()
        for y, row in enumerate(vaporize_map):
            for x, element in enumerate(row):
                assert isinstance(element, str)
                if element.isdigit():
                    # The digit represents the order in which the asteroids were vaporized.
                    asteroid = VaporizedAsteroid(
                        asteroid=Asteroid(x=x, y=y),
                        vaporization_order=int(element),
                    )
                    vaporized_asteroids.append(asteroid)

        # Sort the vaporized asteroids by the vaporization order
        vaporized_asteroids.sort(key=lambda x_: x_.vaporization_order)

        return [x.asteroid for x in vaporized_asteroids]


def day_10(txt_path: Path) -> list:
    # Load puzzle input. Each row represents one string
    with open(str(txt_path), mode='r', newline='') as f:
        asteroid_map = [x.strip() for x in f.readlines()]

    # Find the best location for a new monitoring station.
    asteroid_collection = build_asteroid_collection_from_map(asteroid_map=asteroid_map)
    monitor_station = asteroid_collection.find_best_monitor_location()

    # Part 1: How many other asteroids can be detected from that location?
    part_1_answer = monitor_station.num_visible_asteroids()

    # The Elves are placing bets on which will be the 200th asteroid to be vaporized.
    vaporized_asteroids = monitor_station.vaporize_asteroids()
    asteroid_200 = vaporized_asteroids[200 - 1]

    # Part 2: What do you get if you multiply its X coordinate by 100 and then add its Y coordinate?
    part_2_answer = asteroid_200.x * 100 + asteroid_200.y

    return [part_1_answer, part_2_answer]


def main():
    txt_path = Path(Path(__file__).parent, 'input_data', 'day_10_input.txt')
    answer = day_10(txt_path=txt_path)
    print(f'Day 10 Answers: {repr(answer)}')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Day10Tests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    main()
