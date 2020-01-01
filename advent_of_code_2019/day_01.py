import math
import unittest
from pathlib import Path
from typing import List


def calculate_fuel_mass(module_mass: float) -> int:
    """ Calculate the fuel required for a module

    :param module_mass: The mass of the module
    :type module_mass: float
    :return: The fuel requirement
    :rtype: int
    """
    # Fuel required to launch a given module is based on its mass. Specifically, to find the fuel required for a module,
    # take its mass, divide by three, round down, and subtract 2.
    return math.floor(module_mass / 3) - 2


def calculate_total_fuel_mass(module_mass: float) -> int:
    """ Calculate the amount of fuel for the module and account for any additional fuel required due to the
     weight of the fuel.

    :param module_mass: The mass of the module
    :type module_mass: float
    :return: The total fuel requirement
    :rtype: int
    """
    fuel_mass = calculate_fuel_mass(module_mass=module_mass)
    if fuel_mass > 0:
        additional_fuel_mass = calculate_total_fuel_mass(module_mass=fuel_mass)
        return fuel_mass + additional_fuel_mass
    elif fuel_mass < 0:
        fuel_mass = 0
    return fuel_mass


class Day1Tests(unittest.TestCase):

    def test_calculate_fuel_mass(self):
        self.assertEqual(calculate_fuel_mass(12), 2)
        self.assertEqual(calculate_fuel_mass(14), 2)
        self.assertEqual(calculate_fuel_mass(1969), 654)
        self.assertEqual(calculate_fuel_mass(100756), 33583)

    def test_part_2_fuel(self):
        self.assertEqual(calculate_total_fuel_mass(12), 2)
        self.assertEqual(calculate_total_fuel_mass(14), 2)
        self.assertEqual(calculate_total_fuel_mass(1969), 966)
        self.assertEqual(calculate_total_fuel_mass(100756), 50346)


def day_1(txt_path: Path) -> List[int]:
    with open(str(txt_path), mode='r', newline='') as f:
        module_mass_list = [int(x) for x in f.readlines()]
    total_fuel_part_1 = 0
    total_fuel_part_2 = 0

    for module_mass in module_mass_list:
        fuel_mass = calculate_fuel_mass(module_mass=module_mass)
        total_fuel_part_1 += fuel_mass
        total_fuel_part_2 += fuel_mass

        # Part 2: Calculate the fuel required for the fuel that was just added
        while fuel_mass > 0:
            fuel_mass = calculate_fuel_mass(module_mass=fuel_mass)
            if fuel_mass > 0:
                total_fuel_part_2 += fuel_mass
    return [total_fuel_part_1, total_fuel_part_2]


def main():
    txt_path = Path(Path(__file__).parent, 'input_data', 'day_1_input.txt')
    answer = day_1(txt_path=txt_path)
    print(f'Day 1 Answers: {repr(answer)}')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Day1Tests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    main()
