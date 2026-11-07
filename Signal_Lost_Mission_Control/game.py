"""Pure game state and fair head-to-head scoring; independent of Tkinter."""
from dataclasses import dataclass, field
import math
import random
from typing import List, Optional, Tuple

from algorithms import Route, dijkstra, greedy, score_ratio
from graph import Network, build_mission, edge_key


@dataclass
class Debrief:
    human_cost: float
    greedy_cost: float
    optimal_cost: float
    score: int
    greedy_route: Route
    optimal_route: Route
    divergence: Optional[str]
    extra_cost: float
    checkpoint: str


@dataclass
class Mission:
    number: int = 1
    seed: Optional[int] = None
    network: Network = field(init=False)
    route: List[str] = field(default_factory=lambda: ['EARTH'])
    route_cost: int = 0
    checkpoint_index: int = 0
    checkpoint_cost: int = 0
    failed_links: List[Tuple[str, str, int]] = field(default_factory=list)
    flare_triggered: bool = False
    remaining_seconds: Optional[int] = None
    finished: bool = False
    timed_out: bool = False
    result: Optional[Debrief] = None

    def __post_init__(self):
        self.network = build_mission(self.number, self.seed)

    @property
    def current(self):
        return self.route[-1]

    def legal_next(self):
        if self.finished:
            return []
        return [node for node, _ in self.network.neighbors(self.current, self.route)]

    def move(self, node):
        if self.finished:
            return False
        if node not in self.legal_next():
            return False
        weight = self.network.weight(self.current, node)
        self.route.append(node)
        self.route_cost += weight
        if node == 'MARS':
            self.finish()
        return True

    def undo(self):
        if self.finished or len(self.route) <= self.checkpoint_index + 1:
            return False
        previous = self.route.pop()
        self.route_cost -= self.network.weight(self.current, previous)
        return True

    def baseline(self):
        """Both computer bots restart at the same checkpoint as the player.

        Cost before the checkpoint is sunk and added equally to all totals.
        """
        start = self.route[self.checkpoint_index]
        excluded = set(self.route[:self.checkpoint_index])
        return (greedy(self.network, start, 'MARS', excluded),
                dijkstra(self.network, start, 'MARS', excluded))

    def trigger_flare(self):
        """Break one link ahead while guaranteeing an alternate valid route.

        The player's current position becomes the shared checkpoint. The
        already-traveled prefix is frozen for the rest of this mission.
        """
        if self.finished or self.flare_triggered or self.current == 'MARS':
            return None
        current = self.current
        excluded = set(self.route[:-1])
        optimum = dijkstra(self.network, current, 'MARS', excluded)
        if not optimum.reachable or len(optimum.path) < 2:
            return None
        # Pick the earliest link on the optimal suffix with a valid alternative.
        for a, b in zip(optimum.path, optimum.path[1:]):
            backup = self.network.copy()
            old_weight = backup.remove_link(a, b)
            alternative = dijkstra(backup, current, 'MARS', excluded)
            if alternative.reachable:
                self.network = backup
                self.failed_links.append((a, b, old_weight))
                self.flare_triggered = True
                self.checkpoint_index = len(self.route) - 1
                self.checkpoint_cost = self.route_cost
                self.remaining_seconds = 10
                return (a, b)
        return None

    def tick(self):
        if self.finished or self.remaining_seconds is None:
            return False
        self.remaining_seconds = max(0, self.remaining_seconds - 1)
        if self.remaining_seconds == 0:
            self.timed_out = True
            self.finished = True
            return True
        return False

    def finish(self):
        if self.finished or self.current != 'MARS':
            return None
        bot, optimum = self.baseline()
        frozen = self.route[:self.checkpoint_index]
        played_suffix = self.route[self.checkpoint_index:]
        opt_path = optimum.path
        divergence = None
        for i, (a, b) in enumerate(zip(played_suffix, opt_path)):
            if a != b:
                divergence = f'At step {i + 1}, you went to {a} instead of {b}.'
                break
        if divergence is None and len(played_suffix) != len(opt_path):
            divergence = 'Your route used a different number of hops.'
        if divergence is None:
            divergence = 'You followed an optimal route. Perfect navigation!'
        best_total = self.checkpoint_cost + optimum.cost
        greedy_total = self.checkpoint_cost + bot.cost if bot.reachable else math.inf
        result = Debrief(
            human_cost=self.route_cost,
            greedy_cost=greedy_total,
            optimal_cost=best_total,
            score=score_ratio(best_total, self.route_cost),
            greedy_route=bot,
            optimal_route=optimum,
            divergence=divergence,
            extra_cost=self.route_cost - best_total,
            checkpoint=self.route[self.checkpoint_index],
        )
        self.result = result
        self.finished = True
        self.remaining_seconds = None
        return result
