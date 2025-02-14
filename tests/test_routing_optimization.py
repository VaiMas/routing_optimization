"""Test module for van routing optimization."""

import os
import sys
import unittest


# Add the parent directory of 'src' to the system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from routing_optimization import (  # noqa: E402
    find_optimal_route_for_single_van,
    find_optimal_route_for_multiple_vans,
)


class TestVanRouting(unittest.TestCase):
    """Test cases for van routing optimization."""

    def setUp(self):
        """Set up test cases."""
        self.basic_van_stats = [(10, 10), (9, 8)]
        self.basic_packages = [(-1, 5, 4), (6, 2, 9), (-2, 9, 3)]
        
        self.multiple_van_stats = [(10, 10), (11, 11), (12, 12), (9, 8)]
        self.multiple_packages = [
            (-1, 5, 4),
            (6, 2, 9),
            (-2, 9, 3),
            (7, 3, 2),
            (8, 4, 1),
            (10, 1, 5),
        ]

    def test_single_van_basic(self):
        """Test basic single van routing."""
        result = find_optimal_route_for_single_van(
            self.basic_van_stats,
            self.basic_packages,
            log_not_completed=False,
        )
        selected_van, route_length, fuel_consumption, optimal_route, _ = result
        
        self.assertEqual(selected_van, (9, 8))
        self.assertEqual(route_length, 22)
        self.assertEqual(fuel_consumption, 176)
        
        expected_route = [
            (0, "start"),
            (-1, "pick"),
            (-2, "pick"),
            (5, "drop"),
            (9, "drop"),
            (6, "pick"),
            (2, "drop"),
            (0, "end"),
        ]
        self.assertEqual(
            [(loc, action) for loc, action, _ in optimal_route],
            expected_route,
        )

    def test_multiple_vans_basic(self):
        """Test basic multiple van routing."""
        result = find_optimal_route_for_multiple_vans(
            self.multiple_van_stats, 
            self.multiple_packages
        )
        vans_used, total_distance, total_fuel, routes = result
        
        self.assertLessEqual(len(vans_used), 3)
        self.assertTrue(total_distance > 0)
        self.assertTrue(total_fuel > 0)
        self.assertEqual(len(routes), len(vans_used))
        
        # Verify each route starts at depot and ends at depot
        for route in routes:
            self.assertEqual(route[0][0], 0)  # starts at depot
            self.assertEqual(route[-1][0], 0)  # ends at depot

    def test_edge_cases(self):
        """Test edge cases."""
        # Test no vans
        result = find_optimal_route_for_single_van([], self.basic_packages)
        self.assertIsNone(result[0])
        self.assertEqual(result[1:4], (0, 0, []))
        
        # Test no packages
        result = find_optimal_route_for_single_van(self.basic_van_stats, [])
        self.assertEqual(result[0], self.basic_van_stats[0])
        self.assertEqual(result[1:4], (0, 0, [(0, "start", 0), (0, "end", 0)]))

    def test_capacity_constraints(self):
        """Test van capacity constraints."""
        # Test package too heavy for van
        heavy_package = [(-1, 5, 15)]  # Weight exceeds van capacity
        result = find_optimal_route_for_single_van(
            [(10, 10)],
            heavy_package,
            log_not_completed=False
        )
        self.assertIsNone(result[0])

    def test_route_validity(self):
        """Test route validity conditions."""
        _, _, _, route, _ = find_optimal_route_for_single_van(
            self.basic_van_stats,
            self.basic_packages,
            log_not_completed=False
        )
        
        # Check route structure
        self.assertEqual(route[0][1], "start")
        self.assertEqual(route[-1][1], "end")
        
        # Check pickup-delivery pairs
        pickups = {}
        for loc, action, weight in route[1:-1]:  # Skip start/end
            if action == "pick":
                pickups[weight] = loc
            elif action == "drop":
                self.assertIn(weight, pickups)


if __name__ == '__main__':
    unittest.main()