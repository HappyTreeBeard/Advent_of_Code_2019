import unittest
from pathlib import Path
from typing import List, Dict

from dataclasses import dataclass, field


@dataclass
class ProductionMethod(object):
    input_chemicals: List[str]
    input_quantities: List[int]
    output_chemical: str
    output_quantity: int

    @classmethod
    def build_from_reaction_str(cls, reaction: str) -> 'ProductionMethod':
        """ Create a ProductionMethod object from a reaction definition.
        Example:  '10 ORE => 10 A' or '7 A, 1 E => 1 FUEL'

        :param reaction: The reaction definition
        :type reaction: str
        :return: The ProductionMethod
        :rtype: ProductionMethod
        """
        # Split the string into inputs and output chemicals
        # '7 A, 1 E => 1 FUEL' to ['7 A, 1 E', '1 FUEL']
        multi_inputs_str, output_str = reaction.split(' => ')

        # Separate each chemical from the multi_inputs_str
        # '7 A, 1 E' to ['7 A', '1 E']
        input_str_list = multi_inputs_str.split(', ')

        # Split the input_str_list into a list of chemicals and a list of quantities
        input_chemicals = list()
        input_quantities = list()
        for input_str in input_str_list:
            # '7 A' to [7, 'A']
            quantity_str, chemical = input_str.split(' ')
            input_chemicals.append(chemical)
            input_quantities.append(int(quantity_str))

        output_quantity_str, output_chemical = output_str.split(' ')

        return ProductionMethod(
            input_chemicals=input_chemicals,
            input_quantities=input_quantities,
            output_chemical=output_chemical,
            output_quantity=int(output_quantity_str),
        )


@dataclass
class ChemicalSupply(object):
    chemical_name: str
    production_method: ProductionMethod
    total_production: int = 0
    total_consumption: int = 0

    @property
    def current_inventory(self) -> int:
        return self.total_production - self.total_consumption


@dataclass
class FuelFactory(object):
    inventory: Dict[str, ChemicalSupply] = field(default_factory=dict)

    def __post_init__(self):
        ore_production = ProductionMethod(
            input_chemicals=[],
            input_quantities=[],
            output_chemical='ORE',
            output_quantity=1,
        )
        self.add_production_method(method=ore_production)

    def add_production_method(self, method: ProductionMethod):
        chem_name = method.output_chemical
        assert chem_name not in self.inventory
        chem_supply = ChemicalSupply(
            chemical_name=chem_name,
            production_method=method,
            total_production=0,
            total_consumption=0,
        )
        self.inventory[chem_name] = chem_supply

    def produce_chemical(self, chemical_name: str, count: int):
        chem_supply = self.inventory[chemical_name]
        while chem_supply.current_inventory < count:
            # Produce and consume the required amount of the precursor / input chemical
            input_chemicals = chem_supply.production_method.input_chemicals
            input_quantities = chem_supply.production_method.input_quantities
            for input_chem, input_quantity in zip(input_chemicals, input_quantities):
                # Note a ProductionMethod could create more precursor than necessary
                self.produce_chemical(chemical_name=input_chem, count=input_quantity)
                self.consume_chemical(chemical_name=input_chem, count=input_quantity)

            # print(f"+{chem_supply.production_method.output_quantity} {chemical_name}")
            chem_supply.total_production += chem_supply.production_method.output_quantity

    def consume_chemical(self, chemical_name: str, count: int):
        chem_supply = self.inventory[chemical_name]
        if chem_supply.current_inventory < count:
            raise ValueError(f'Insufficient supply. Requested: {count}, Current inventory: '
                             f'{chem_supply.current_inventory}, {chem_supply}')
        # print(f"-{count} {chemical_name}")
        chem_supply.total_consumption += count


class Day14Tests(unittest.TestCase):

    def test_build_from_reaction_str1(self):
        reaction_str = '10 ORE => 10 A'
        expected_production = ProductionMethod(
            input_chemicals=['ORE'],
            input_quantities=[10],
            output_chemical='A',
            output_quantity=10,
        )
        actual_method = ProductionMethod.build_from_reaction_str(reaction=reaction_str)
        self.assertEqual(expected_production, actual_method)

    def test_build_from_reaction_str2(self):
        reaction_str = '7 A, 1 E => 1 FUEL'
        expected_production = ProductionMethod(
            input_chemicals=['A', 'E'],
            input_quantities=[7, 1],
            output_chemical='FUEL',
            output_quantity=1,
        )
        actual_method = ProductionMethod.build_from_reaction_str(reaction=reaction_str)
        self.assertEqual(expected_production, actual_method)

    def test_part1_example1(self):
        reaction_str_list = [
            '10 ORE => 10 A',
            '1 ORE => 1 B',
            '7 A, 1 B => 1 C',
            '7 A, 1 C => 1 D',
            '7 A, 1 D => 1 E',
            '7 A, 1 E => 1 FUEL',
        ]

        fuel_factory = self.build_factory(reaction_str_list=reaction_str_list)

        production_methods = [ProductionMethod.build_from_reaction_str(reaction=x) for x in reaction_str_list]
        self.assertEqual(
            len(fuel_factory.inventory),
            len(reaction_str_list) + 1,  # This should include the additional ProductionMethod for ORE
        )

        fuel_factory = FuelFactory()
        for method in production_methods:
            fuel_factory.add_production_method(method=method)

        fuel_str = 'FUEL'
        fuel_supply = fuel_factory.inventory[fuel_str]
        self.assertEqual(fuel_supply.chemical_name, fuel_str)
        self.assertListEqual(fuel_supply.production_method.input_chemicals, ['A', 'E'])
        self.assertListEqual(fuel_supply.production_method.input_quantities, [7, 1])

        # To produce 1 FUEL, a total of 31 ORE is required
        expected_ore_requirement = 31
        fuel_factory.produce_chemical(chemical_name=fuel_str, count=1)
        actual_ore_requirement = fuel_factory.inventory['ORE'].total_consumption
        self.assertEqual(actual_ore_requirement, expected_ore_requirement)

    def test_part1_example2(self):
        reaction_str_list = [
            '9 ORE => 2 A',
            '8 ORE => 3 B',
            '7 ORE => 5 C',
            '3 A, 4 B => 1 AB',
            '5 B, 7 C => 1 BC',
            '4 C, 1 A => 1 CA',
            '2 AB, 3 BC, 4 CA => 1 FUEL',
        ]
        # The above list of reactions requires 165 ORE to produce 1 FUEL:
        expected_ore_requirement = 165

        fuel_factory = self.build_factory(reaction_str_list=reaction_str_list)

        fuel_factory.produce_chemical(chemical_name='FUEL', count=1)
        actual_ore_requirement = fuel_factory.inventory['ORE'].total_consumption
        self.assertEqual(actual_ore_requirement, expected_ore_requirement)

    def test_part1_example5(self):
        reaction_str_list = [
            '171 ORE => 8 CNZTR',
            '7 ZLQW, 3 BMBT, 9 XCVML, 26 XMNCP, 1 WPTQ, 2 MZWV, 1 RJRHP => 4 PLWSL',
            '114 ORE => 4 BHXH',
            '14 VRPVC => 6 BMBT',
            '6 BHXH, 18 KTJDG, 12 WPTQ, 7 PLWSL, 31 FHTLT, 37 ZDVW => 1 FUEL',
            '6 WPTQ, 2 BMBT, 8 ZLQW, 18 KTJDG, 1 XMNCP, 6 MZWV, 1 RJRHP => 6 FHTLT',
            '15 XDBXC, 2 LTCX, 1 VRPVC => 6 ZLQW',
            '13 WPTQ, 10 LTCX, 3 RJRHP, 14 XMNCP, 2 MZWV, 1 ZLQW => 1 ZDVW',
            '5 BMBT => 4 WPTQ',
            '189 ORE => 9 KTJDG',
            '1 MZWV, 17 XDBXC, 3 XCVML => 2 XMNCP',
            '12 VRPVC, 27 CNZTR => 2 XDBXC',
            '15 KTJDG, 12 BHXH => 5 XCVML',
            '3 BHXH, 2 VRPVC => 7 MZWV',
            '121 ORE => 7 VRPVC',
            '7 XCVML => 6 RJRHP',
            '5 BHXH, 4 VRPVC => 5 LTCX',
        ]
        # 2210736 ORE for 1 FUEL:
        expected_ore_requirement = 2210736

        fuel_factory = self.build_factory(reaction_str_list=reaction_str_list)

        fuel_factory.produce_chemical(chemical_name='FUEL', count=1)
        actual_ore_requirement = fuel_factory.inventory['ORE'].total_consumption
        self.assertEqual(actual_ore_requirement, expected_ore_requirement)

    @staticmethod
    def build_factory(reaction_str_list: List[str]) -> FuelFactory:
        production_methods = [ProductionMethod.build_from_reaction_str(reaction=x) for x in reaction_str_list]
        fuel_factory = FuelFactory()
        for method in production_methods:
            fuel_factory.add_production_method(method=method)
        return fuel_factory


def day_14(txt_path: Path) -> list:
    # Load puzzle input. Multiple rows with reaction definitions on each row.
    with open(str(txt_path), mode='r', newline='') as f:
        rows = [x.strip() for x in f.readlines()]

    production_methods = [ProductionMethod.build_from_reaction_str(reaction=x) for x in rows]
    fuel_factory = FuelFactory()
    for method in production_methods:
        fuel_factory.add_production_method(method=method)

    # Part 1: What is the minimum amount of ORE required to produce exactly 1 FUEL?
    fuel_factory.produce_chemical(chemical_name='FUEL', count=1)
    part_1_answer = fuel_factory.inventory['ORE'].total_consumption

    part_2_answer = None

    return [part_1_answer, part_2_answer]


def main():
    txt_path = Path(Path(__file__).parent, 'input_data', 'day_14_input.txt')
    answer = day_14(txt_path=txt_path)
    print(f'Day 14 Answers: {repr(answer)}')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Day14Tests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    main()
