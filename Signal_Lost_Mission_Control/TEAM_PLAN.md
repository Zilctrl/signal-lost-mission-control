# Team of two: build and present Signal Lost

## Elevator pitch (20 seconds)

> "Can you beat the algorithms that route a message through a damaged satellite network? In Signal Lost, you're mission control: choose a route from Earth to Mars, compete against a greedy next-hop bot and Dijkstra's shortest-path algorithm, then recover when a solar flare knocks out a relay. The game animates Dijkstra's decisions and shows what your route cost you."

This is a fictional learning game. The phrase "route the internet" is just an analogy: real Internet routing is more involved, and satellite communication here uses made-up edge costs.

## File ownership

| Owner | Edit these files | Deliverables |
|---|---|---|
| Person A — logic | `graph.py`, `algorithms.py`, `game.py`, `tests/test_logic.py` | Verified Dijkstra, greedy traps, randomized connected maps, fair flare checkpoint |
| Person B — presentation | `ui.py`, `README.md`, screenshots and Devpost | Clickable game, clear timer, animation, testable demo, slides/video |
| Both | `TEAM_PLAN.md` | Live playtesting and judge Q&A |

**Shared contract:** stations are uppercase strings; network edges are positive integer weights in a dict keyed by a sorted pair; `dijkstra()` and `greedy()` return `Route(path, cost, explored)`; the UI can call `Mission.move(name)`, `Mission.trigger_flare()`, `Mission.tick()`, and read `Mission.result`.

## Realistic work order

1. **First playable checkpoint:** graph, click to create route, algorithms compute costs, results visible. DONE in starter.
2. **Disaster checkpoint:** fail a link mid-route, guarantee alternate connection, countdown and fair rerouting. DONE in starter.
3. **Dijkstra reveal:** animate explored nodes with `after()` and explain divergence. DONE in starter.
4. **Repeatability:** randomized graph, JSON leaderboard, automated tests. DONE in starter.
5. **Stretch:** move visual packets along chosen links, better Dijkstra queue visualization, audio, NOAA data with offline fallback. NOT in starter.

## Example demo (60–90 seconds)

- **0:00:** "This graph is our fictional relay network. Each number is a connection cost."
- **0:10:** "Greedy chooses Orion first because 2 is cheaper than 4. It ends up costing 20; Dijkstra can find a 14-unit route."
- **0:25:** Click **VEGA → ATLAS → MARS** and show the 100% result as nodes animate.
- **0:40:** Click **NEXT MAP**, take two hops, then explain the solar flare turning a link red.
- **0:50:** Recover within 10 seconds; show fair checkpoint and the debrief.
- **1:10:** Show saved leaderboard and mention that algorithms were implemented and tested in Python.

## Explain these questions confidently

**Q: Can a human actually beat Dijkstra's path cost?** No. With the same static positive-weight graph, a correct Dijkstra run is optimal. The challenge is to match it before time runs out.

**Q: Isn't greedy also an algorithm?** Yes. The point is to compare a local heuristic with a globally optimal algorithm and a human.

**Q: What happens if a network is disconnected by a solar flare?** The game only chooses a flare link when a replacement route still exists, because it is meant to be a solvable challenge. Real routing could fail completely.

**Q: Is this AI/ML?** No. This uses classical graph algorithms. Do not submit it as AI/ML without adding and evaluating an actual ML component.

**Q: Are the delays physically accurate?** No. They are abstract relative costs. Earth-to-Mars physics and orbital motion are not modeled.

**Q: Why does score change after the flare?** The comparison is restarted fairly at the player's current station. The already-traveled prefix cost is included for all three contenders.
