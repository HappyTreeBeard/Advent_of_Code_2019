import unittest
from pathlib import Path
from typing import List, Optional, DefaultDict

from dataclasses import dataclass, field


@dataclass
class DirectOrbit(object):
    m0: str
    m1: str
    """The m1 object orbits around the m0 object. """


@dataclass
class OrbitalNode(object):
    name: str
    parent_orbit: Optional['OrbitalNode'] = None
    satellites: List['OrbitalNode'] = field(default_factory=list)


class OrbitalNodeDict(DefaultDict[str, OrbitalNode]):
    """Override defaultdict so a OrbitalNode is created if the key is missing from the dictionary.
    Note: typing.DefaultDict was used instead of collections.defaultdict so type hinting can be implemented.
    """

    def __missing__(self, key):
        node = OrbitalNode(name=key)
        self[key] = node  # Make sure the OrbitalNode object is added to this dictionary for future use.
        return node

    def get_root_node(self) -> OrbitalNode:
        for orbital_node in self.values():
            while orbital_node.parent_orbit is not None:
                orbital_node = orbital_node.parent_orbit
            return orbital_node
        raise ValueError(f'No root node, i.e. Center of Mass (COM), was detected in the {OrbitalNodeDict}')


def build_orbital_node_dict(orbit_list: List[DirectOrbit]) -> OrbitalNodeDict:
    """ Build a OrbitalNodeDict composed of OrbitalNode as values and orbit names as keys.
    Each OrbitalNode will be linked to its parent and satellites.

    :param orbit_list: List of DirectOrbit objects
    :type orbit_list: List[DirectOrbit]
    :return: The constructed OrbitalNodeDict
    :rtype: OrbitalNodeDict
    """
    # Dictionary for easy access to each OrbitalNode based on the objects name
    # Use the defaultdict to create an empty OrbitalNode if it does not exist.
    node_dict = OrbitalNodeDict()
    for orbit in orbit_list:
        node0 = node_dict[orbit.m0]
        node1 = node_dict[orbit.m1]
        # Assign node1 as a satellite of node0
        node0.satellites.append(node1)
        # Assign node0 as the parent of node1
        node1.parent_orbit = node0

    return node_dict


def count_direct_and_indirect_orbits(root_node: OrbitalNode) -> int:
    """ Count the number of both direct and indirect orbits represented in the provided OrbitalNode

    :param root_node: The root OrbitalNode
    :type root_node: OrbitalNode
    :return: The number of direct and indirect orbits
    :rtype: int
    """
    num_orbits = 0
    # Count the number of direct and indirect orbits by counting the number of hops until the Center of Mass (COM),
    # is reached, i.e. when the parent_orbit is None.
    parent_node = root_node.parent_orbit
    while parent_node is not None:
        num_orbits += 1
        parent_node = parent_node.parent_orbit

    # Use recursion to count the orbits for each satellite
    for satellite in root_node.satellites:
        num_orbits += count_direct_and_indirect_orbits(root_node=satellite)
    return num_orbits


class NodeNotFoundError(ValueError):
    """Exception that is thrown if a specified OrbitalNode could not be found."""
    pass


# TODO: Share the OrbitalNodeDict so this function is not necessary
def find_specific_node(node_name: str, root_node: OrbitalNode) -> OrbitalNode:
    """ Search for the OrbitalNode with the matching name

    :param node_name: The name of the OrbitalNode to locate
    :type node_name: str
    :param root_node: The root node. The function will check this node and this node's satellites
    :type root_node: OrbitalNode
    :return: The OrbitalNode with the matching name
    """
    if root_node.name == node_name:
        return root_node
    for satellite in root_node.satellites:
        try:
            return find_specific_node(node_name=node_name, root_node=satellite)
        except NodeNotFoundError:
            pass
    raise NodeNotFoundError


def find_num_orbital_transfers(node0: OrbitalNode, node1: OrbitalNode) -> int:
    """ Find the number of orbital transfers required to place node0 in orbit around the parent of node1

    :param node0: The node that would be moved
    :type node1: OrbitalNode
    :param node1: The target node with the parent that node0 should orbit
    :type node1: OrbitalNode
    :return: The number of orbital transfers
    :rtype: int
    """

    # TODO: A much simpler algorithm with less complexity could be used.
    def build_parent_orbit_list(node: OrbitalNode) -> List[str]:
        """Build a list of OrbitalNode.name where the specified node is at index 0 and the root is at -1 """
        node_name_list = [node.name]
        parent_node = node.parent_orbit
        while parent_node is not None:
            node_name_list.append(parent_node.name)
            parent_node = parent_node.parent_orbit
        return node_name_list

    orbit_list_0 = build_parent_orbit_list(node=node0)
    orbit_list_1 = build_parent_orbit_list(node=node1)
    orbit_hop_list = list()
    for orbit0 in orbit_list_0:
        if orbit0 in orbit_list_1:
            i = orbit_list_1.index(orbit0)
            orbit_slice = orbit_list_1[0: i + 1]  # Add 1 to include the least common ancestor
            # Reverse the order so the hop list correct moves from node0 to node1
            orbit_slice = list(reversed(orbit_slice))
            orbit_hop_list.extend(orbit_slice)
            break
        else:
            # Include this orbit into the hop list
            orbit_hop_list.append(orbit0)

    num_hop = len(orbit_hop_list)
    num_hop -= 2  # Exclude the two hops represented by node0 and node1
    num_hop -= 1  # Exclude one hop so both node0 and node1 share the same orbit
    return num_hop


class Day6Tests(unittest.TestCase):
    def test_part_1_example(self):
        #         G - H       J - K - L
        #        /           /
        # COM - B - C - D - E - F
        #                \
        #                 I
        # The total number of direct and indirect orbits in this example is 42.
        expected_num_orbits = 42
        map_list = ['COM)B', 'B)C', 'C)D', 'D)E', 'E)F', 'B)G', 'G)H', 'D)I', 'E)J', 'J)K', 'K)L']
        orbits = self.build_direct_orbit_list(map_list=map_list)
        orbital_node_dict = build_orbital_node_dict(orbit_list=orbits)
        root_orbital_node = orbital_node_dict.get_root_node()
        self.assertEqual(root_orbital_node.name, 'COM')
        self.assertIsNone(root_orbital_node.parent_orbit)
        self.assertEqual(len(root_orbital_node.satellites), 1)
        satellite = root_orbital_node.satellites[0]
        self.assertEqual(satellite.name, 'B')

        num_orbits = count_direct_and_indirect_orbits(root_node=root_orbital_node)
        self.assertEqual(num_orbits, expected_num_orbits)

    def test_part_2_example(self):
        #                           YOU
        #                          /
        #         G - H       J - K - L
        #        /           /
        # COM - B - C - D - E - F
        #                \
        #                 I - SAN
        expected_num_transfers = 4
        map_list = ['COM)B', 'B)C', 'C)D', 'D)E', 'E)F', 'B)G', 'G)H', 'D)I', 'E)J', 'J)K', 'K)L', 'K)YOU', 'I)SAN']
        orbits = self.build_direct_orbit_list(map_list=map_list)
        orbital_node_dict = build_orbital_node_dict(orbit_list=orbits)

        # Find the node with the name 'YOU'
        you_node = orbital_node_dict['YOU']
        self.assertEqual(you_node.name, 'YOU')
        self.assertEqual(you_node.parent_orbit.name, 'K')

        # Find the node with the name 'SAN'
        santa_node = orbital_node_dict['SAN']
        self.assertEqual(santa_node.name, 'SAN')
        self.assertEqual(santa_node.parent_orbit.name, 'I')

        num_transfers = find_num_orbital_transfers(node0=you_node, node1=santa_node)
        self.assertEqual(num_transfers, expected_num_transfers)

    @staticmethod
    def build_direct_orbit_list(map_list: List[str]) -> List[DirectOrbit]:
        orbits: List[DirectOrbit] = list()
        for line in map_list:
            # Example: '6WF)DRK' where '6WF' is m0, and 'DRK' is m1
            obj_iter = iter(line.split(')'))
            direct_orbit = DirectOrbit(
                m0=next(obj_iter),
                m1=next(obj_iter),
            )
            orbits.append(direct_orbit)
        return orbits


def day_6(txt_path: Path) -> List[int]:
    # Load puzzle input as List[DirectOrbit]
    orbits: List[DirectOrbit] = list()
    with open(str(txt_path), mode='r', newline='') as f:
        for line in f.readlines():
            # Trim the newline characters: \r\n
            line = line.strip()
            # Example: '6WF)DRK' where '6WF' is m0, and 'DRK' is m1
            obj_iter = iter(line.split(')'))
            direct_orbit = DirectOrbit(
                m0=next(obj_iter),
                m1=next(obj_iter),
            )
            orbits.append(direct_orbit)

    # Build a OrbitalNode tree and get the node that represents the Center of Mass (COM)
    orbital_node_dict = build_orbital_node_dict(orbit_list=orbits)

    # Part 1: What is the total number of direct and indirect orbits in your map data?
    root_node = orbital_node_dict.get_root_node()
    part_1_answer = count_direct_and_indirect_orbits(root_node=root_node)

    # Part 2: What is the minimum number of orbital transfers required to move from the object YOU are orbiting to
    # the object SAN is orbiting? (Between the objects they are orbiting - not between YOU and SAN.)

    # Find the node with the name 'YOU' and 'SAN' and calculate the number of orbital transfers
    you_node = orbital_node_dict['YOU']
    santa_node = orbital_node_dict['SAN']
    part_2_answer = find_num_orbital_transfers(node0=you_node, node1=santa_node)

    return [part_1_answer, part_2_answer]


def main():
    txt_path = Path(Path(__file__).parent, 'input_data', 'day_6_input.txt')

    answer = day_6(txt_path=txt_path)
    print(f'Day 6 Answers: {repr(answer)}')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Day6Tests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    main()
