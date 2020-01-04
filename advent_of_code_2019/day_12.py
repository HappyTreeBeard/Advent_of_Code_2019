import copy
import math
import re
import unittest
from itertools import combinations
from pathlib import Path
from typing import List

from dataclasses import dataclass


@dataclass
class Moon(object):
    x: int
    y: int
    z: int
    dx: int = 0
    dy: int = 0
    dz: int = 0

    @property
    def potential_energy(self) -> int:
        # A moon's potential energy is the sum of the absolute values of its x, y, and z position coordinates.
        positions = [self.x, self.y, self.z]
        abs_positions = [abs(x) for x in positions]
        return sum(abs_positions)

    @property
    def kinetic_energy(self) -> int:
        # A moon's kinetic energy is the sum of the absolute values of its velocity coordinates.
        velocities = [self.dx, self.dy, self.dz]
        abs_velocities = [abs(x) for x in velocities]
        return sum(abs_velocities)

    @property
    def total_energy(self) -> int:
        # The total energy for a single moon is its potential energy multiplied by its kinetic energy.
        return self.potential_energy * self.kinetic_energy


def import_moon_from_string(definition: str) -> Moon:
    """ Create a moon object with a string with the following syntax: <x=14, y=15, z=-2>

    :param definition: The string defining the moon position
    :type definition: str
    :return: The constructed Moon object
    :rtype: Moon
    """
    match = re.match(r'<x=(?P<x_pos>-?\d+), y=(?P<y_pos>-?\d+), z=(?P<z_pos>-?\d+)>', definition)
    return Moon(
        x=int(match.group('x_pos')),
        y=int(match.group('y_pos')),
        z=int(match.group('z_pos')),
    )


def simulate(moon_list: List[Moon]) -> List[Moon]:
    """ Simulate the provided moons for one time step.

    :param moon_list: The list of Moon objects to simulate.
    :type moon_list: List[Moon]
    :return: The list of Moon objects after one time step.
    :rtype: List[Moon]
    """
    # Simulate the motion of the moons in time steps. Within each time step, first update the velocity of every moon
    # by applying gravity. Then, once all moons' velocities have been updated, update the position of every moon by
    # applying velocity. Time progresses by one step once all of the positions are updated.

    # To apply gravity, consider every pair of moons. On each axis (x, y, and z), the velocity of each moon changes
    # by exactly +1 or -1 to pull the moons together. For example, if Ganymede has an x position of 3, and Callisto
    # has a x position of 5, then Ganymede's x velocity changes by +1 (because 5 > 3) and Callisto's x velocity
    # changes by -1 (because 3 < 5). However, if the positions on a given axis are the same, the velocity on that
    # axis does not change for that pair of moons.
    for moon0, moon1 in combinations(moon_list, r=2):

        if moon0.x < moon1.x:
            moon0.dx += 1
            moon1.dx -= 1
        elif moon0.x > moon1.x:
            moon0.dx -= 1
            moon1.dx += 1

        if moon0.y < moon1.y:
            moon0.dy += 1
            moon1.dy -= 1
        elif moon0.y > moon1.y:
            moon0.dy -= 1
            moon1.dy += 1

        if moon0.z < moon1.z:
            moon0.dz += 1
            moon1.dz -= 1
        elif moon0.z > moon1.z:
            moon0.dz -= 1
            moon1.dz += 1

    # Once all gravity has been applied, apply velocity: simply add the velocity of each moon to its own position. 
    # For example, if Europa has a position of x=1, y=2, z=3 and a velocity of x=-2, y=0,z=3, then its new position 
    # would be x=-1, y=2, z=6. This process does not modify the velocity of any moon. 
    for moon in moon_list:
        moon.x += moon.dx
        moon.y += moon.dy
        moon.z += moon.dz

    return moon_list


def calculate_steps_until_state_resets(moon_list: List[Moon]) -> int:
    """ Use a faster method to determine when the moons will return to their initial state without simulating it.
    If the planets are periodic for all three dimensions, then they will be periodic for a single dimension.
        1) Find how long it takes for each dimension to revert to the initial position.
        2) Calculate the least common multiple of the periods to determine when all 3 dimensions will reset.

    :param moon_list: The list of Moon objects to simulate.
    :type moon_list: List[Moon]
    :return: The number of steps it would take for all moons to revert to their initial state.
    :rtype: int
    """
    moon_list_t0 = copy.deepcopy(moon_list)

    # The number of required steps for each attribute/dimension to reset to the t0 state.
    num_req_step_per_attr = list()

    # TODO: Is there a way to do the same thing without using setattr and getattr without code duplication?

    for pos_attr_name, vel_attr_name in [('x', 'dx'), ('y', 'dy'), ('z', 'dz')]:
        # The position and velocity attribute names

        num_steps = 0
        continue_simulation = True
        while continue_simulation:
            num_steps += 1

            for moon0, moon1 in combinations(moon_list, r=2):
                # if moon0.x < moon1.x:
                #      moon0.dx += 1
                #      moon1.dx -= 1
                #  elif moon0.x > moon1.x:
                #      moon0.dx -= 1
                #      moon1.dx += 1
                # The commented code above is equivalent to the code below
                # when pos_attr_name == 'x' and vel_attr_name == 'dy'

                vel_moon0 = getattr(moon0, vel_attr_name)
                vel_moon1 = getattr(moon1, vel_attr_name)

                pos_moon0 = getattr(moon0, pos_attr_name)
                pos_moon1 = getattr(moon1, pos_attr_name)

                if pos_moon0 < pos_moon1:
                    vel_moon0 += 1
                    vel_moon1 -= 1
                elif pos_moon0 > pos_moon1:
                    vel_moon0 -= 1
                    vel_moon1 += 1

                setattr(moon0, vel_attr_name, vel_moon0)
                setattr(moon1, vel_attr_name, vel_moon1)

            for moon in moon_list:
                # moon.x += moon.dx
                # moon.y += moon.dy
                # moon.z += moon.dz
                # The commented code above is equivalent to the code below
                # when pos_attr_name == 'x' and vel_attr_name == 'dy'
                vel = getattr(moon, vel_attr_name)
                pos = getattr(moon, pos_attr_name)
                setattr(moon, pos_attr_name, pos + vel)

            # End the simulation if attribute/dimension position and velocity match the t0 state.
            initial_states_matching = list()
            for moon, moon_t0 in zip(moon_list, moon_list_t0):
                match_pos = getattr(moon, pos_attr_name) == getattr(moon_t0, pos_attr_name)
                match_vel = getattr(moon, vel_attr_name) == getattr(moon_t0, vel_attr_name)
                is_match = match_pos and match_vel
                initial_states_matching.append(is_match)
            if all(initial_states_matching):
                continue_simulation = False

        num_req_step_per_attr.append(num_steps)

    # Find the least common multiple of every value in the list
    values = num_req_step_per_attr
    while len(values) > 1:
        lcm = compute_lcm(x=values.pop(), y=values.pop())
        values.append(lcm)
    return values.pop()


def compute_lcm(x: int, y: int) -> int:
    """Compute the least common multiple (LCM) of two numbers."""
    return x * y // math.gcd(x, y)


class Day12Tests(unittest.TestCase):

    def test_part1_example1(self):
        # For example, suppose your scan reveals the following positions:
        #
        # <x=-1, y=0, z=2>
        # <x=2, y=-10, z=-7>
        # <x=4, y=-8, z=8>
        # <x=3, y=5, z=-1>
        definition = [
            '<x=-1, y=0, z=2>',
            '<x=2, y=-10, z=-7>',
            '<x=4, y=-8, z=8>',
            '<x=3, y=5, z=-1>',
        ]
        moons_step0 = [import_moon_from_string(definition=x) for x in definition]
        expected_moons_step0 = [
            Moon(x=-1, y=0, z=2),
            Moon(x=2, y=-10, z=-7),
            Moon(x=4, y=-8, z=8),
            Moon(x=3, y=5, z=-1),
        ]
        self.assertListEqual(moons_step0, expected_moons_step0)
        step_count = 0

        # After 1 step:
        # pos=<x= 2, y=-1, z= 1>, vel=<x= 3, y=-1, z=-1>
        # pos=<x= 3, y=-7, z=-4>, vel=<x= 1, y= 3, z= 3>
        # pos=<x= 1, y=-7, z= 5>, vel=<x=-3, y= 1, z=-3>
        # pos=<x= 2, y= 2, z= 0>, vel=<x=-1, y=-3, z= 1>
        expected_moons_step1 = [
            Moon(x=2, y=-1, z=1, dx=3, dy=-1, dz=-1),
            Moon(x=3, y=-7, z=-4, dx=1, dy=3, dz=3),
            Moon(x=1, y=-7, z=5, dx=-3, dy=1, dz=-3),
            Moon(x=2, y=2, z=0, dx=-1, dy=-3, dz=1),
        ]
        moons_step1 = simulate(moon_list=moons_step0)
        step_count += 1
        self.assertListEqual(expected_moons_step1, moons_step1)

        # After 10 steps:
        # pos=<x= 2, y= 1, z=-3>, vel=<x=-3, y=-2, z= 1>
        # pos=<x= 1, y=-8, z= 0>, vel=<x=-1, y= 1, z= 3>
        # pos=<x= 3, y=-6, z= 1>, vel=<x= 3, y= 2, z=-3>
        # pos=<x= 2, y= 0, z= 4>, vel=<x= 1, y=-1, z=-1>
        expected_moons_step10 = [
            Moon(x=2, y=1, z=-3, dx=-3, dy=-2, dz=1),
            Moon(x=1, y=-8, z=0, dx=-1, dy=1, dz=3),
            Moon(x=3, y=-6, z=1, dx=3, dy=2, dz=-3),
            Moon(x=2, y=0, z=4, dx=1, dy=-1, dz=-1),
        ]
        moons_step10 = moons_step1
        while step_count < 10:
            moons_step10 = simulate(moon_list=moons_step10)
            step_count += 1
        self.assertListEqual(expected_moons_step10, moons_step10)

        # Energy after 10 steps:
        # pot: 2 + 1 + 3 =  6;   kin: 3 + 2 + 1 = 6;   total:  6 * 6 = 36
        # pot: 1 + 8 + 0 =  9;   kin: 1 + 1 + 3 = 5;   total:  9 * 5 = 45
        # pot: 3 + 6 + 1 = 10;   kin: 3 + 2 + 3 = 8;   total: 10 * 8 = 80
        # pot: 2 + 0 + 4 =  6;   kin: 1 + 1 + 1 = 3;   total:  6 * 3 = 18
        # Sum of total energy: 36 + 45 + 80 + 18 = 179
        expected_energy = 179
        total_energy = sum([x.total_energy for x in moons_step10])
        self.assertEqual(total_energy, expected_energy)

    def test_part1_example2(self):
        # Here's a second example:
        #
        # <x=-8, y=-10, z=0>
        # <x=5, y=5, z=10>
        # <x=2, y=-7, z=3>
        # <x=9, y=-8, z=-3>
        moons_step0 = [
            Moon(x=-8, y=-10, z=0),
            Moon(x=5, y=5, z=10),
            Moon(x=2, y=-7, z=3),
            Moon(x=9, y=-8, z=-3),
        ]
        step_count = 0

        # Energy after 100 steps:
        # pot:  8 + 12 +  9 = 29;   kin: 7 +  3 + 0 = 10;   total: 29 * 10 = 290
        # pot: 13 + 16 +  3 = 32;   kin: 3 + 11 + 5 = 19;   total: 32 * 19 = 608
        # pot: 29 + 11 +  1 = 41;   kin: 3 +  7 + 4 = 14;   total: 41 * 14 = 574
        # pot: 16 + 13 + 23 = 52;   kin: 7 +  1 + 1 =  9;   total: 52 *  9 = 468
        # Sum of total energy: 290 + 608 + 574 + 468 = 1940
        expected_energy = 1940
        moons_step100 = moons_step0
        while step_count < 100:
            moons_step100 = simulate(moon_list=moons_step100)
            step_count += 1
        total_energy = sum([x.total_energy for x in moons_step100])
        self.assertEqual(total_energy, expected_energy)

    def test_part2_example1(self):
        # Determine the number of steps that must occur before all of the moons' positions and velocities exactly
        # match a previous point in time.

        # For example, the first example above takes 2772 steps before they exactly match a previous point in time;
        # it eventually returns to the initial state:
        expected_steps = 2772

        # After 0 steps:
        # pos=<x= -1, y=  0, z=  2>, vel=<x=  0, y=  0, z=  0>
        # pos=<x=  2, y=-10, z= -7>, vel=<x=  0, y=  0, z=  0>
        # pos=<x=  4, y= -8, z=  8>, vel=<x=  0, y=  0, z=  0>
        # pos=<x=  3, y=  5, z= -1>, vel=<x=  0, y=  0, z=  0>
        definition = [
            '<x=-1, y=0, z=2>',
            '<x=2, y=-10, z=-7>',
            '<x=4, y=-8, z=8>',
            '<x=3, y=5, z=-1>',
        ]
        moons_step_0 = [import_moon_from_string(definition=x) for x in definition]
        moons_step_n = copy.deepcopy(moons_step_0)
        steps = 0
        positions_match_t0 = False
        while not positions_match_t0:
            steps += 1
            moons_step_n = simulate(moon_list=moons_step_n)
            positions_match_t0 = moons_step_n == moons_step_0
            if steps > expected_steps:
                break
        self.assertListEqual(moons_step_0, moons_step_n)
        self.assertEqual(expected_steps, steps)

    def test_simulate_until_state_resets_example1(self):
        definition = [
            '<x=-1, y=0, z=2>',
            '<x=2, y=-10, z=-7>',
            '<x=4, y=-8, z=8>',
            '<x=3, y=5, z=-1>',
        ]
        moons_step_0 = [import_moon_from_string(definition=x) for x in definition]
        moons_step_n = copy.deepcopy(moons_step_0)
        actual_steps = calculate_steps_until_state_resets(moon_list=moons_step_n)
        expected_steps = 2772
        self.assertEqual(expected_steps, actual_steps)

    def test_simulate_until_state_resets_example2(self):
        definition = [
            '<x=-8, y=-10, z=0>',
            '<x=5, y=5, z=10>',
            '<x=2, y=-7, z=3>',
            '<x=9, y=-8, z=-3>',
        ]
        moons_step_0 = [import_moon_from_string(definition=x) for x in definition]
        moons_step_n = copy.deepcopy(moons_step_0)
        actual_steps = calculate_steps_until_state_resets(moon_list=moons_step_n)
        expected_steps = 4686774924
        self.assertEqual(expected_steps, actual_steps)


def day_12(txt_path: Path) -> list:
    # Load puzzle input. Multiple rows with moon position definitions on each row.
    with open(str(txt_path), mode='r', newline='') as f:
        rows = f.readlines()

    moons_step_0 = [import_moon_from_string(definition=x) for x in rows]

    # What is the total energy in the system after simulating the moons given in your scan for 1000 steps?
    final_step_count = 1000
    moons_step_1000 = copy.deepcopy(moons_step_0)
    step_count = 0
    while step_count < final_step_count:
        step_count += 1
        moons_step_1000 = simulate(moon_list=moons_step_1000)

    # Part 1: What is the total energy in the system?
    part_1_answer = sum([x.total_energy for x in moons_step_1000])

    # Determine the number of steps that must occur before all of the moons' positions and velocities exactly match a
    # previous point in time.
    moons_step_n = copy.deepcopy(moons_step_0)
    steps_to_reset = calculate_steps_until_state_resets(moon_list=moons_step_n)

    # Part 2: How many steps were required?
    part_2_answer = steps_to_reset

    return [part_1_answer, part_2_answer]


def main():
    txt_path = Path(Path(__file__).parent, 'input_data', 'day_12_input.txt')
    answer = day_12(txt_path=txt_path)
    print(f'Day 12 Answers: {repr(answer)}')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Day12Tests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    main()
