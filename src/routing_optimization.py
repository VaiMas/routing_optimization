"""Van routing optimization module."""

from typing import Optional
import heapq
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def distance(a: int, b: int) -> int:
    """Calculate the absolute distance between two locations."""
    return abs(a - b)


class VanRouter:
    """Class for handling single van routing operations."""

    def __init__(
        self,
        van_stats: tuple[int, int],
        packages: list[tuple[int, int, int]],
    ):
        """
        Initialize the VanRouter with van statistics and packages.

        Args:
            van_stats: Tuple containing van capacity and fuel per unit distance.
            packages: List of packages as tuples (pickup, delivery, weight).
        """
        self.van_capacity, self.fuel_per_unit = van_stats
        self.route = [(0, "start", 0)]
        self.current_location = 0
        self.total_distance = 0
        self.total_fuel = 0
        self.current_load = 0
        self.picked_up_packages = 0
        self.delivered_packages = 0
        self.pickups = []
        self.deliveries = []
        self.not_completed = []

        # Use a min-heap to keep track of the closest packages
        heap = [(distance(0, p[0]), p) for p in packages]
        heapq.heapify(heap)

        # Select the closest 5 packages
        self.packages = [
            heapq.heappop(heap)[1] for _ in range(min(5, len(heap)))
        ]
        self.not_completed.extend([p for _, p in heap])
        self.pickups = [(p[0], p[2]) for p in self.packages]

    def find_nearest_valid_move(self) -> Optional[tuple[int, int, str, int]]:
        """
        Find the nearest valid pickup or delivery location.
        Prioritizes pickups if possible, otherwise selects the nearest delivery.

        Returns:
            Optional[tuple[int, int, str, int]]: The nearest valid move as a tuple
            (distance, location, action, weight), or None if no valid move is found.
        """
        # Create heaps for pickups and deliveries
        pickup_heap = [
            (distance(self.current_location, loc), loc, weight)
            for loc, weight in self.pickups
            if self.current_load + weight <= self.van_capacity
        ]
        delivery_heap = [
            (distance(self.current_location, loc), loc, weight)
            for loc, weight in self.deliveries
        ]

        # Heapify the lists
        heapq.heapify(pickup_heap)
        heapq.heapify(delivery_heap)

        # Get the nearest pickup and delivery
        nearest_pickup = heapq.heappop(pickup_heap) if pickup_heap else None
        nearest_delivery = heapq.heappop(delivery_heap) if delivery_heap else None

        # Determine the nearest move
        if nearest_pickup and (
            not nearest_delivery or nearest_pickup[0] <= nearest_delivery[0]
        ):
            return (nearest_pickup[0], nearest_pickup[1], "pick", nearest_pickup[2])
        elif nearest_delivery:
            return (
                nearest_delivery[0],
                nearest_delivery[1],
                "drop",
                nearest_delivery[2],
            )
        else:
            return None

    def construct_route(
        self,
    ) -> tuple[int, int, list[tuple[int, str, int]]]:
        """
        Constructs an efficient route using a greedy nearest-neighbor approach.

        Returns:
            tuple[int, int, list[tuple[int, str, int]]]: The total distance, total fuel
            consumption, and the route as a list of tuples (location, action, weight).
        """
        while (self.pickups or self.deliveries) and (
            self.picked_up_packages + self.delivered_packages < 10
        ):
            move = self.find_nearest_valid_move()
            if not move:
                self.not_completed.extend(
                    [(loc, loc, weight) for loc, weight in self.pickups]
                )
                self.not_completed.extend(
                    [(loc, loc, weight) for loc, weight in self.deliveries]
                )
                return (
                    self.total_distance,
                    self.total_fuel,
                    self.route,
                )  # No valid route found

            dist, loc, action, weight = move
            self.total_distance += dist
            self.total_fuel += dist * self.fuel_per_unit
            self.route.append((loc, action, weight))
            self.current_location = loc

            if action == "pick":
                self.current_load += weight
                self.pickups.remove((loc, weight))
                delivery_loc = next(d for p, d, w in self.packages if p == loc)
                self.deliveries.append((delivery_loc, weight))
                self.picked_up_packages += 1
            else:  # Drop
                self.current_load -= weight
                self.deliveries.remove((loc, weight))
                self.delivered_packages += 1

        # Return to the depot
        self.total_distance += distance(self.current_location, 0)
        self.total_fuel += distance(self.current_location, 0) * self.fuel_per_unit
        self.route.append((0, "end", 0))

        self.not_completed.extend([(loc, loc, weight) for loc, weight in self.pickups])
        self.not_completed.extend(
            [(loc, loc, weight) for loc, weight in self.deliveries]
        )

        return self.total_distance, self.total_fuel, self.route


def filter_invalid_input(
    van_stats: list[tuple[int, int]], 
    packages: list[tuple[int, int, int]]
) -> tuple[list[tuple[int, int]], list[tuple[int, int, int]]]:
    """
    Filter out invalid van stats and packages.

    Args:
        van_stats: List of vans as tuples (capacity, fuel per unit distance).
        packages: List of packages as tuples (pickup, delivery, weight).

    Returns:
        tuple containing valid van stats and packages.
    """
    valid_van_stats = [
        (capacity, fuel)
        for capacity, fuel in van_stats
        if (isinstance(capacity, (int, float)) and capacity > 0)
        and (isinstance(fuel, (int, float)) and fuel > 0)
    ]
    valid_packages = [
        (pickup, delivery, weight)
        for pickup, delivery, weight in packages
        if all(isinstance(val, int) for val in (pickup, delivery, weight))
        and weight > 0
        and pickup != delivery
    ]
    invalid_packages = [
        (pickup, delivery, weight)
        for pickup, delivery, weight in packages
        if not (
            all(isinstance(val, int) for val in (pickup, delivery, weight))
            and weight > 0
            and pickup != delivery
        )
    ]

    for package in invalid_packages:
        logger.warning("Invalid package: %s", package)

    return valid_van_stats, valid_packages


def find_optimal_route_for_single_van(
    van_stats: list[tuple[int, int]],
    packages: list[tuple[int, int, int]],
    log_not_completed: bool = True,
) -> tuple[
    Optional[tuple[int, int]],
    int,
    int,
    list[tuple[int, str, int]],
    list[tuple[int, int, int]],
]:
    """
    Find the best van for the most efficient route.

    Args:
        van_stats: List of vans as tuples (capacity, fuel per unit distance).
        packages: List of packages as tuples (pickup, delivery, weight).
        log_not_completed: Flag to control logging of not completed pickups.

    Returns:
        Tuple containing the best van, total distance, total fuel consumption,
        the best route, and the remaining packages.
    """
    van_stats, packages = filter_invalid_input(van_stats, packages)

    if not packages:
        if van_stats:
            return van_stats[0], 0, 0, [(0, "start", 0), (0, "end", 0)], []
        else:
            return None, 0, 0, [], []

    best_van = None
    best_route = None
    best_distance = float("inf")
    best_fuel = float("inf")
    best_not_completed = []

    for van in van_stats:
        router = VanRouter(van, packages)
        dist, fuel, route = router.construct_route()
        if fuel < best_fuel and router.picked_up_packages > 0:
            best_van = van
            best_route = route
            best_distance = dist
            best_fuel = fuel
            best_not_completed = router.not_completed

    if best_not_completed and log_not_completed:
        logger.warning(
            "Not completed pickups/deliveries for single van: %s", best_not_completed
        )

    if best_route:
        return best_van, best_distance, best_fuel, best_route, best_not_completed
    else:
        return None, 0, 0, [], packages


def find_optimal_route_for_multiple_vans(
    van_stats: list[tuple[int, int]], packages: list[tuple[int, int, int]]
) -> tuple[
    list[tuple[int, int]],
    int,
    int,
    list[list[tuple[int, str, int]]],
]:
    """
    Find the most fuel-efficient routes combination for multiple vans.

    Args:
        van_stats (list[tuple[int, int]]): List of vans as tuples (capacity, fuel per
        unit distance).
        packages (list[tuple[int, int, int]]): List of packages as tuples (pickup
        location, delivery location, weight).

    Returns:
        tuple[list[tuple[int, int]], int, int, list[list[tuple[int, str, int]]]]:
        The list of vans used, total distance, total fuel consumption, and list of
        routes for each van.
    """
    van_stats, packages = filter_invalid_input(van_stats, packages)

    # Select the top 3 most fuel-efficient vans
    top_vans = sorted(van_stats, key=lambda x: x[1])[:3]

    total_fuel = 0
    total_distance = 0
    vans_used = []
    routes = []
    remaining_packages = packages.copy()

    for van in top_vans:
        if not remaining_packages:
            break
        best_van, dist, fuel, route, best_not_completed = (
            find_optimal_route_for_single_van(
                [van], remaining_packages, log_not_completed=False
            )
        )
        if best_van:
            vans_used.append(best_van)
            total_distance += dist
            total_fuel += fuel
            routes.append(route)
            remaining_packages = best_not_completed.copy()  # Ensure a copy is made
        else:
            break

    if remaining_packages:
        logger.warning(
            "Not completed pickups/deliveries for multiple vans: %s", remaining_packages
        )

    return vans_used, total_distance, total_fuel, routes

if __name__ == "__main__":
    # This is an example test for Base goal. When evaluating the task, more will be added:
    selected_van, route_length, fuel_consumption, optimal_route, not_completed = (
        find_optimal_route_for_single_van(
            [(10, 10), (9, 8)], [(-1, 5, 4), (6, 2, 9), (-2, 9, 3)]
        )
    )

    # Extract only the location and action for comparison
    optimal_route_simplified = [(loc, action) for loc, action, weight in optimal_route]

    assert selected_van == (9, 8)
    assert optimal_route_simplified == [
        (0, "start"),
        (-1, "pick"),
        (-2, "pick"),
        (5, "drop"),
        (9, "drop"),
        (6, "pick"),
        (2, "drop"),
        (0, "end"),
    ]
    assert route_length == 22
    assert fuel_consumption == 176

    print("ALL TESTS PASSED")