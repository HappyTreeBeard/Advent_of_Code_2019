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


@dataclass
class Asteroid(object):
    x: int
    y: int


@dataclass
class AsteroidMonitoringStation(object):
    asteroid: Asteroid
    observed_asteroids: List[Asteroid]


@dataclass
class ObservedAsteroid(object):
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
        """Calculate the angle between the two asteroids in radians"""
        return math.atan2(self.dy, self.dx)

    @property
    def distance(self) -> float:
        """Calculate distance between the two asteroids using Pythagorean theorem"""
        return math.sqrt(pow(self.dx, 2) + pow(self.dy, 2))


@dataclass
class AsteroidCollection(object):
    asteroids: List[Asteroid]

    def build_monitor_station(self, asteroid: Asteroid) -> AsteroidMonitoringStation:
        """ Build a AsteroidMonitoringStation object showing which asteroids are observable.

        :param asteroid: The target location for the monitoring station
        :type asteroid: Asteroid
        :return: The AsteroidMonitoringStation
        :rtype: AsteroidMonitoringStation
        """
        # Build a ObservedAsteroid object for each asteroid pair.
        # This is used to calculate distance and angle between the asteroids.
        observed_asteroid_list = list()
        for other_asteroid in self.asteroids:
            if asteroid == other_asteroid:
                continue
            observed_asteroid = ObservedAsteroid(asteroid=asteroid, other_asteroid=other_asteroid)
            observed_asteroid_list.append(observed_asteroid)

        # Determine which asteroids will be occluded, i.e. blocked by closer asteroids
        # Track which asteroids are occluded using a dictionary where the key is the angle
        visible_asteroids: Dict[float, ObservedAsteroid] = dict()
        for observed_asteroid in observed_asteroid_list:
            angle = observed_asteroid.angle * 180 / math.pi

            if angle not in visible_asteroids:
                # No other asteroids share the same observation angle.
                visible_asteroids[angle] = observed_asteroid
            elif observed_asteroid.distance < visible_asteroids[angle].distance:
                # Two asteroids share the same observation angle.
                # The closer asteroid will occlude the other asteroid.
                visible_asteroids[angle] = observed_asteroid

        observed_asteroids = [x.other_asteroid for x in visible_asteroids.values()]
        monitoring_station = AsteroidMonitoringStation(asteroid=asteroid, observed_asteroids=observed_asteroids)
        return monitoring_station

    def find_all_monitor_locations(self) -> List[AsteroidMonitoringStation]:
        """ Find the all possible asteroid monitoring stations and which asteroids can be observed.

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
            elif len(monitoring_station.observed_asteroids) > len(best_monitoring_station.observed_asteroids):
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

    def test_asteroid_observation_count(self):
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
        self.assertEqual(len(monitor_station.observed_asteroids), expected_asteroid_count)

        # The asteroid at 4,2 should be able to detect 5 asteroids
        target_asteroid = Asteroid(x=4, y=2)
        expected_asteroid_count = 5
        asteroid_collection = build_asteroid_collection_from_map(asteroid_map=asteroid_map)
        monitor_station = asteroid_collection.build_monitor_station(asteroid=target_asteroid)
        self.assertEqual(monitor_station.asteroid, target_asteroid)
        self.assertEqual(len(monitor_station.observed_asteroids), expected_asteroid_count)

        # The asteroid at 4,2 should be able to detect 5 asteroids
        target_asteroid = Asteroid(x=1, y=2)
        expected_asteroid_count = 7
        asteroid_collection = build_asteroid_collection_from_map(asteroid_map=asteroid_map)
        monitor_station = asteroid_collection.build_monitor_station(asteroid=target_asteroid)
        self.assertEqual(monitor_station.asteroid, target_asteroid)

        self.assertEqual(len(monitor_station.observed_asteroids), expected_asteroid_count)

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
        observed_asteroid_count = 0  # Count the number of asteroids that should be observable
        for row in asteroid_occlusion_map:
            asteroid_row = list()
            for element in row:
                # Capital letters represent asteroids that can be observed
                if element.isupper():
                    observed_asteroid_count += 1
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
        self.assertEqual(len(monitor_station.observed_asteroids), observed_asteroid_count)

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
        expected_num_observed_asteroid = 8

        asteroid_collection = build_asteroid_collection_from_map(asteroid_map=asteroid_map)
        self.assertIn(Asteroid(x=1, y=0), asteroid_collection.asteroids)
        self.assertIn(expected_asteroid, asteroid_collection.asteroids)
        self.assertEqual(10, len(asteroid_collection.asteroids))

        self.check_monitor_station(asteroid_map, expected_asteroid, expected_num_observed_asteroid)

    def test_part1_large_example1(self):
        # Best is 5,8 with 33 other asteroids detected
        expected_asteroid = Asteroid(x=5, y=8)
        expected_num_observed_asteroid = 33
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
        self.check_monitor_station(asteroid_map, expected_asteroid, expected_num_observed_asteroid)

    def test_part1_large_example2(self):
        # Best is 1,2 with 35 other asteroids detected
        expected_asteroid = Asteroid(x=1, y=2)
        expected_num_observed_asteroid = 35
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
        self.check_monitor_station(asteroid_map, expected_asteroid, expected_num_observed_asteroid)

    def test_part1_large_example3(self):
        # Best is 6,3 with 41 other asteroids detected
        expected_asteroid = Asteroid(x=6, y=3)
        expected_num_observed_asteroid = 41
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
        self.check_monitor_station(asteroid_map, expected_asteroid, expected_num_observed_asteroid)

    def test_part1_large_example4(self):
        # Best is 11,13 with 210 other asteroids detected
        expected_asteroid = Asteroid(x=11, y=13)
        expected_num_observed_asteroid = 210
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
        self.check_monitor_station(asteroid_map, expected_asteroid, expected_num_observed_asteroid)

    def check_monitor_station(self, asteroid_map: List[str], asteroid: Asteroid, num_observed_asteroid: int):
        """ Verify the correct asteroid monitoring station is selected.

        :param asteroid_map: The asteroid map.
        :type asteroid_map: List[str]
        :param asteroid: The expected asteroid position for the best asteroid monitoring station.
        :type asteroid: Asteroid
        :param num_observed_asteroid: The number of asteroids that can be observed at the monitoring station.
        :type num_observed_asteroid: int
        """
        asteroid_collection = build_asteroid_collection_from_map(asteroid_map=asteroid_map)
        monitor_station = asteroid_collection.find_best_monitor_location()
        self.assertEqual(monitor_station.asteroid, asteroid)
        self.assertEqual(len(monitor_station.observed_asteroids), num_observed_asteroid)


def day_10(txt_path: Path) -> list:
    # Load puzzle input. Each row represents one string
    with open(str(txt_path), mode='r', newline='') as f:
        asteroid_map = [x.strip() for x in f.readlines()]

    # Find the best location for a new monitoring station.
    asteroid_collection = build_asteroid_collection_from_map(asteroid_map=asteroid_map)
    monitor_station = asteroid_collection.find_best_monitor_location()

    # Part 1: How many other asteroids can be detected from that location?
    part_1_answer = len(monitor_station.observed_asteroids)

    part_2_answer = None

    return [part_1_answer, part_2_answer]


def main():
    txt_path = Path(Path(__file__).parent, 'input_data', 'day_10_input.txt')
    answer = day_10(txt_path=txt_path)
    print(f'Day 10 Answers: {repr(answer)}')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Day10Tests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    main()
