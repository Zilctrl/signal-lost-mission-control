"""Run: python -m unittest discover -s tests -v"""
import json
import math
import random
import tempfile
import unittest
from pathlib import Path

from algorithms import dijkstra, greedy, score_ratio
from game import Mission
from graph import Network, build_mission
from leaderboard import add_score, get_scores


class AlgorithmTests(unittest.TestCase):
    def test_first_map_has_greedy_trap(self):
        network = build_mission(1)
        self.assertEqual(greedy(network).cost, 20)
        self.assertEqual(dijkstra(network).cost, 14)

    def test_dijkstra_route_cost_matches_network(self):
        network = build_mission(1)
        result = dijkstra(network)
        self.assertEqual(network.route_cost(result.path), result.cost)
        self.assertEqual(result.path[0], 'EARTH')
        self.assertEqual(result.path[-1], 'MARS')

    def test_dijkstra_handles_unreachable(self):
        graph = Network.from_edges({'A': (0, 0), 'B': (1, 0), 'C': (2, 0)},
                                   [('A', 'B', 3)])
        result = dijkstra(graph, 'A', 'C')
        self.assertFalse(result.reachable)
        self.assertEqual(result.path, ())
        self.assertTrue(math.isinf(result.cost))

    def test_greedy_can_get_stuck(self):
        graph = Network.from_edges({'A': (0, 0), 'B': (1, 0), 'C': (2, 0), 'D': (3, 0)},
                                   [('A', 'B', 1), ('A', 'C', 3), ('C', 'D', 1)])
        self.assertFalse(greedy(graph, 'A', 'D').reachable)
        self.assertEqual(dijkstra(graph, 'A', 'D').cost, 4)

    def test_excluded_nodes(self):
        graph = build_mission(1)
        route = dijkstra(graph, 'VEGA', 'MARS', {'EARTH', 'ORION'})
        self.assertTrue(route.reachable)
        self.assertFalse(set(route.path) & {'EARTH', 'ORION'})

    def test_random_maps_are_solvable(self):
        for seed in range(60):
            for number in (2, 3, 4):
                self.assertTrue(dijkstra(build_mission(number, seed)).reachable)

    def test_algorithm_matches_brute_force_small_graphs(self):
        for seed in range(30):
            rng = random.Random(seed)
            nodes = {x: (i, 0) for i, x in enumerate('ABCDE')}
            edges = [('A', 'B', rng.randint(1, 9)),
                     ('B', 'C', rng.randint(1, 9)),
                     ('C', 'D', rng.randint(1, 9)),
                     ('D', 'E', rng.randint(1, 9))]
            for a, b in [('A', 'C'), ('B', 'D'), ('A', 'D'), ('C', 'E')]:
                if rng.random() > 0.35:
                    edges.append((a, b, rng.randint(1, 9)))
            net = Network.from_edges(nodes, edges)
            paths = []
            def visit(node, path, weight):
                if node == 'E':
                    paths.append(weight)
                    return
                for nxt, w in net.neighbors(node, path):
                    visit(nxt, path + [nxt], weight + w)
            visit('A', ['A'], 0)
            self.assertEqual(dijkstra(net, 'A', 'E').cost, min(paths))

    def test_scoring(self):
        self.assertEqual(score_ratio(14, 14), 100)
        self.assertEqual(score_ratio(14, 20), 70)
        self.assertEqual(score_ratio(14, math.inf), 0)


class MissionTests(unittest.TestCase):
    def test_human_route_finishes_with_three_results(self):
        session = Mission()
        for node in ['ORION', 'LYRA', 'NOVA', 'KEPLER', 'MARS']:
            self.assertTrue(session.move(node))
        self.assertTrue(session.finished)
        self.assertEqual(session.result.human_cost, 20)
        self.assertEqual(session.result.greedy_cost, 20)
        self.assertEqual(session.result.optimal_cost, 14)
        self.assertEqual(session.result.score, 70)
        self.assertIn('At step', session.result.divergence)

    def test_optimal_human_gets_100(self):
        session = Mission()
        for node in ['VEGA', 'ATLAS', 'MARS']:
            self.assertTrue(session.move(node))
        self.assertEqual(session.result.score, 100)

    def test_invalid_moves_do_not_change_route(self):
        session = Mission()
        self.assertFalse(session.move('MARS'))
        self.assertFalse(session.move('EARTH'))
        self.assertEqual(session.route, ['EARTH'])
        self.assertEqual(session.route_cost, 0)

    def test_flare_reroutes_from_current_and_preserves_checkpoint(self):
        mission = Mission()
        self.assertTrue(mission.move('ORION'))
        fail = mission.trigger_flare()
        self.assertIsNotNone(fail)
        self.assertEqual(mission.checkpoint_index, 1)
        self.assertEqual(mission.checkpoint_cost, 2)
        self.assertEqual(mission.remaining_seconds, 10)
        self.assertIsNone(mission.network.weight(*fail))
        bot, opt = mission.baseline()
        self.assertTrue(opt.reachable)
        self.assertEqual(opt.path[0], 'ORION')
        self.assertNotIn('EARTH', opt.path)
        self.assertFalse(mission.undo())  # past path is frozen
        for node in opt.path[1:]:
            self.assertTrue(mission.move(node))
        self.assertEqual(mission.result.score, 100)
        self.assertEqual(mission.result.optimal_cost, mission.route_cost)

    def test_flare_timeout(self):
        mission = Mission()
        self.assertIsNotNone(mission.trigger_flare())
        for _ in range(9):
            self.assertFalse(mission.tick())
        self.assertTrue(mission.tick())
        self.assertTrue(mission.finished)
        self.assertTrue(mission.timed_out)
        self.assertFalse(mission.move('ORION'))

    def test_random_maps_support_outages(self):
        for number in range(1, 6):
            for seed in range(20):
                m = Mission(number, seed)
                fail = m.trigger_flare()
                self.assertIsNotNone(fail)
                self.assertTrue(m.baseline()[1].reachable)

    def test_leaderboard_persists_sorted(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'leaderboard.json'
            add_score('A', 1, 70, 20, 14, path)
            add_score('B', 1, 100, 14, 14, path)
            self.assertEqual([x['pilot'] for x in get_scores(path)], ['B', 'A'])
            self.assertEqual(json.loads(path.read_text())[0]['score'], 100)


if __name__ == '__main__':
    unittest.main()
