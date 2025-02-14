# Van Routing Optimization

A Python solution for optimizing van delivery routes, considering van capacity, 
fuel efficiency, and package weights.

## Project Structure
```
.
├── README.md
├── requirements.txt
├── src
│   ├── __init__.py
│   └── routing_optimization.py
└── tests
    ├── __init__.py
    └── test_routing_optimization.py
```

## Features
- Single van route optimization
- Multiple van fleet management
- Capacity and fuel efficiency consideration
- Package pickup and delivery scheduling

## Usage Example
```python
from routing_optimization import (
    find_optimal_route_for_single_van,
    find_optimal_route_for_multiple_vans,
)

# Single van routing
van_stats = [(10, 10), (9, 8)]  # (capacity, fuel_per_unit)
packages = [(-1, 5, 4), (6, 2, 9)]  # (pickup, delivery, weight)

selected_van, route_length, fuel, route, _ = find_optimal_route_for_single_van(
    van_stats, packages
)

# Multiple van routing
vans_used, total_distance, total_fuel, routes = find_optimal_route_for_multiple_vans(
    van_stats, packages
)
```

## Installation
1. Clone the repository:
```sh
git clone https://github.com/VaiMas/routing-optimization.git
cd routing-optimization
```

## Testing
Run the tests using:
```sh
python -m unittest discover -s tests