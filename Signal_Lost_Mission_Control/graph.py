"""Mission maps and the undirected, weighted relay network. No GUI code."""
from dataclasses import dataclass
import random
from typing import Dict, List, Optional, Tuple


POSITIONS = {
    'EARTH': (0.09, 0.49),
    'ORION': (0.27, 0.25),
    'VEGA': (0.27, 0.72),
    'LYRA': (0.46, 0.14),
    'NOVA': (0.47, 0.51),
    'ATLAS': (0.62, 0.79),
    'KEPLER': (0.69, 0.31),
    'MARS': (0.91, 0.49),
}

# This fixed training network deliberately tempts a locally greedy algorithm
# into taking the cheap EARTH -> ORION -> LYRA branch.
BASE_EDGES = [
    ('EARTH', 'ORION', 2), ('EARTH', 'VEGA', 4),
    ('ORION', 'LYRA', 2), ('ORION', 'NOVA', 7), ('ORION', 'VEGA', 8),
    ('LYRA', 'NOVA', 9), ('LYRA', 'KEPLER', 12),
    ('VEGA', 'NOVA', 3), ('VEGA', 'ATLAS', 5),
    ('NOVA', 'KEPLER', 3), ('NOVA', 'ATLAS', 6),
    ('ATLAS', 'KEPLER', 5), ('ATLAS', 'MARS', 5),
    ('KEPLER', 'MARS', 4),
]


def edge_key(a: str, b: str) -> Tuple[str, str]:
    if a == b:
        raise ValueError('Self-links are not supported')
    return tuple(sorted((a, b)))


@dataclass
class Network:
    positions: Dict[str, Tuple[float, float]]
    edges: Dict[Tuple[str, str], int]

    @classmethod
    def from_edges(cls, positions, edges):
        costs = {}
        for a, b, cost in edges:
            if a not in positions or b not in positions:
                raise ValueError(f'Unknown station: {a}, {b}')
            if not isinstance(cost, int) or cost <= 0:
                raise ValueError('Connection weights must be positive integers')
            costs[edge_key(a, b)] = cost
        return cls(dict(positions), costs)

    def copy(self):
        return Network(dict(self.positions), dict(self.edges))

    def neighbors(self, node: str, excluded=()):
        banned = set(excluded)
        result = []
        for (a, b), cost in self.edges.items():
            if a == node and b not in banned:
                result.append((b, cost))
            elif b == node and a not in banned:
                result.append((a, cost))
        return sorted(result, key=lambda p: p[0])

    def weight(self, a, b):
        return self.edges.get(edge_key(a, b))

    def remove_link(self, a, b):
        return self.edges.pop(edge_key(a, b), None)

    def route_cost(self, path):
        total = 0
        for a, b in zip(path, path[1:]):
            cost = self.weight(a, b)
            if cost is None:
                raise ValueError(f'Link {a}--{b} does not exist')
            total += cost
        return total


def build_mission(number=1, seed: Optional[int] = None) -> Network:
    """Training is deterministic; later missions vary but remain connected."""
    if number <= 1:
        return Network.from_edges(POSITIONS, BASE_EDGES)
    rng = random.Random(seed if seed is not None else random.randrange(1, 2**31))
    edges = []
    for a, b, cost in BASE_EDGES:
        edges.append((a, b, max(1, cost + rng.randint(-2, 3))))
    if number >= 3:
        extras = [('LYRA', 'ATLAS'), ('ORION', 'KEPLER'), ('VEGA', 'LYRA')]
        for a, b in rng.sample(extras, k=min(number - 2, len(extras))):
            edges.append((a, b, rng.randint(7, 12)))
    coords = dict(POSITIONS)
    for node in coords:
        if node not in ('EARTH', 'MARS'):
            x, y = coords[node]
            coords[node] = (x + rng.uniform(-.025, .025), y + rng.uniform(-.035, .035))
    return Network.from_edges(coords, edges)
