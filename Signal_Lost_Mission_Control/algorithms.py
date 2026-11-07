"""Implementations of Dijkstra and greedy next-hop routing.

Dijkstra is written from scratch using heapq; no networkx is needed.
"""
from dataclasses import dataclass
import heapq
import math
from typing import Tuple


@dataclass(frozen=True)
class Route:
    path: Tuple[str, ...]
    cost: float
    explored: Tuple[str, ...] = ()

    @property
    def reachable(self):
        return bool(self.path) and math.isfinite(self.cost)


def dijkstra(network, start='EARTH', goal='MARS', excluded=()) -> Route:
    """Find the global minimum-cost simple route with positive edge weights.

    `excluded` is used after a flare to prevent returning to an already
    visited station in the human's frozen route prefix.
    """
    forbidden = set(excluded) - {start}
    if start not in network.positions or goal not in network.positions or goal in forbidden:
        return Route((), math.inf)
    distances = {start: 0}
    previous = {}
    queue = [(0, start)]
    explored = []
    settled = set()

    while queue:
        dist, node = heapq.heappop(queue)
        if node in settled or dist != distances[node]:
            continue
        settled.add(node)
        explored.append(node)
        if node == goal:
            path = [goal]
            while path[-1] != start:
                path.append(previous[path[-1]])
            return Route(tuple(reversed(path)), dist, tuple(explored))
        for neighbor, weight in network.neighbors(node, forbidden):
            if neighbor in settled:
                continue
            new_dist = dist + weight
            if new_dist < distances.get(neighbor, math.inf):
                distances[neighbor] = new_dist
                previous[neighbor] = node
                heapq.heappush(queue, (new_dist, neighbor))
    return Route((), math.inf, tuple(explored))


def greedy(network, start='EARTH', goal='MARS', excluded=()) -> Route:
    """Always choose the cheapest unvisited adjacent edge. Can get stuck."""
    if start not in network.positions or goal not in network.positions or goal in set(excluded) - {start}:
        return Route((), math.inf)
    visited = set(excluded) - {start}
    path = [start]
    total = 0
    while path[-1] != goal:
        current = path[-1]
        visited.add(current)
        options = [(cost, neighbor) for neighbor, cost in network.neighbors(current, visited)]
        if not options:
            return Route(tuple(path), math.inf, tuple(path))
        cost, nxt = min(options)
        path.append(nxt)
        total += cost
    return Route(tuple(path), total, tuple(path))


def score_ratio(optimal_cost, player_cost) -> int:
    if not math.isfinite(optimal_cost) or not math.isfinite(player_cost) or player_cost <= 0:
        return 0
    return min(100, max(0, round(100 * optimal_cost / player_cost)))
