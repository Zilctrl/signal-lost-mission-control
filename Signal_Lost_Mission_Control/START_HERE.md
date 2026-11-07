# Step-by-step guide: build and understand Signal Lost

You can run the complete prototype immediately, but this is the order you should **learn and rebuild** it for the hackathon. Don't try to memorize `ui.py` before you understand the core graph.

## Step 0 — Run the game (5 minutes)

1. Extract the ZIP onto your Windows computer.
2. VS Code → File → Open Folder → `Signal_Lost_Mission_Control`.
3. Terminal → New Terminal → `py main.py`.
4. Click **VEGA**, then **ATLAS**, then **MARS**.
5. Watch Dijkstra's purple exploration rings and the three cost comparisons.
6. Press **RETRY**; click **ORION → LYRA → NOVA → KEPLER → MARS**. See why greedy is more expensive.
7. Press **RETRY** again; click **TRIGGER SOLAR FLARE** before you reach Mars. You now have only 10 seconds.

Screenshot reference: `preview.png`, `disaster.png`, `debrief.png`.

## Step 1 — Learn the graph (`graph.py`)

Every satellite is a **node**. Each available two-way connection is an **edge** with a cost. On the training map:

```python
('EARTH', 'ORION', 2)
('EARTH', 'VEGA', 4)
```

From Earth you can go to Orion at cost 2 or Vega at cost 4. Taking the initially cheaper edge does **not** guarantee a cheaper whole trip.

The `Network` class stores edges in a dictionary and exposes:

- `neighbors(node, excluded)` — valid next stations and their connection costs.
- `weight(a, b)` — direct cost or `None` if disconnected.
- `remove_link(a, b)` — delete an edge after a flare.
- `route_cost(path)` — sum every edge in an already-chosen route.

**Exercise:** In `graph.py`, change `('EARTH', 'ORION', 2)` to `('EARTH', 'ORION', 9)` and predict what happens to greedy. Press **RETRY** or restart the app after saving.

## Step 2 — Understand greedy (`algorithms.py`)

Greedy does not look ahead. At each node it:

1. Collects all **unvisited neighboring stations**.
2. Chooses the link with the smallest **immediate** cost.
3. Moves there permanently.
4. Repeats until Mars or a dead end.

On the original training map it picks:

`EARTH → ORION → LYRA → NOVA → KEPLER → MARS = 2 + 2 + 9 + 3 + 4 = 20`

That greedy behavior is a deliberate simplification. In production networks, routing algorithms can use more information; this is an educational next-hop heuristic.

**Exercise:** Why does greedy pick Orion before Vega, even though the optimal route starts with Vega?

## Step 3 — Understand Dijkstra (`algorithms.py`)

Dijkstra maintains the lowest currently known cost to reach each node. It always expands the unprocessed node with the smallest current total cost.

```python
queue = [(0, start)]       # (current_cost, node)
heapq.heappush(queue, (new_dist, neighbor))
lowest_cost, node = heapq.heappop(queue)
```

The heap makes it efficient to retrieve the next cheapest candidate. `previous` remembers the predecessor that produces the best known cost, so the algorithm can reconstruct the finished route.

On the training map it finds:

`EARTH → VEGA → ATLAS → MARS = 4 + 5 + 5 = 14`

There is another 14-unit route through Nova and Kepler; tied routes are both optimal. Dijkstra's result is correct for this **positive-weight** graph.

**Exercise:** Temporarily print `result.explored` in a test. Compare the exploration order to the purple rings in the GUI.

## Step 4 — Implement player moves (`game.py`)

The `Mission` object is a **state machine**. Its most important fields:

```python
route             # list of stations visited, starts at EARTH
route_cost        # sum of costs already incurred
finished          # set when Mars is reached or timer expires
failed_links      # list of disconnected links
```

`legal_next()` returns adjacent unvisited nodes. `move(node)` validates the hop, adds its weight to your cost, and calls `finish()` when you reach Mars. Clicking a nonneighbor does nothing except log a message.

**Exercise:** Add `print('HUMAN ROUTE:', self.route)` inside `move()` after appending a node, then play.

## Step 5 — Code the disaster (`game.py`)

`trigger_flare()`:

1. Records the satellite where the human is standing.
2. Computes the best **remaining** route to Mars.
3. Tries removing a link on that route.
4. Accepts the outage only if a different valid route to Mars still exists.
5. Freezes the already-traveled prefix as a checkpoint.
6. Starts a 10-second countdown.

**Why freeze the prefix?** The player has already paid those link costs; pretending that they never happened is misleading. The bots also start from the same checkpoint and cannot revisit the player's earlier stations. All three costs include the same pre-flare sunk cost, so the post-flare comparison is fair.

`tick()` decreases the remaining seconds. `ui.py` calls it every second with Tkinter's `after()` method, which does not freeze the screen.

**Exercise:** Change `remaining_seconds = 10` to `15` and test the rescue timer.

## Step 6 — Build the interface (`ui.py`)

Tkinter's `Canvas` draws nodes, edges, labels, and colored route overlays:

- gray = working link;
- blue = human path;
- dashed orange = greedy route (after reveal);
- dashed green = optimal route (after reveal);
- dashed red = disabled link;
- purple ring = node being explored by Dijkstra.

The click handler (`on_canvas_click`) finds the nearest satellite and sends that name to `Mission.move()`. `refresh()` redraws the screen from game state; `draw_network()` does not calculate shortest paths itself.

The animation uses `root.after(275, ...)`. This is much better than `time.sleep()` inside the UI, which would freeze button input and the countdown.

**Exercise:** Change the human route color `CYAN` at the top of `ui.py`.

## Step 7 — Score fairly (`game.py`)

When the player reaches Mars, `finish()` computes:

- `human_cost`: all edges the player actually traversed;
- `greedy_cost`: the same prefix cost, plus greedy's suffix from the checkpoint (or `STUCK`);
- `optimal_cost`: the same prefix cost, plus Dijkstra's suffix from the checkpoint;
- `score`: `round(100 * optimal_cost / human_cost)` — max 100%;
- `divergence`: the **first** station where the human suffix differed from one optimal path;
- `extra_cost`: `human_cost - optimal_cost`.

The first divergence is **not always the sole cause** of the extra cost, and more than one optimal route may exist. Debrief comparisons use the checkpoint, so after a flare the efficiency score measures rerouting from that moment onward (with prefix cost included), not a fresh hypothetical game from Earth.

**Exercise:** Give yourself a 100% run and a 70% run using the two routes in Step 0.

## Step 8 — Test before you polish

```powershell
py -m unittest discover -s tests -v
```

Fifteen tests cover the Dijkstra/greedy difference, shortest paths against brute force, dead ends, random map connectivity, valid moves, checkpoints, timeout, 100% score, and JSON leaderboard ordering.

**Exercise:** Write one new test asserting that you cannot undo past a flare checkpoint.

## Step 9 — Two-person workflow

- **Algorithms teammate:** `graph.py`, `algorithms.py`, `game.py`, tests.
- **UI teammate:** `ui.py`, screenshots, demo flow, colors, usability.

Don't both edit the same file at once. Commit after each small working change:

```
git add .
git commit -m "Implement flare-safe routing checkpoint"
```

There is no need to install `networkx`. The core algorithm is your own. If you add it for verification, compare results in tests only, not inside `dijkstra()`.

## Step 10 — Demo, then improve

1. Explain why greedy gets trapped (20 vs 14).
2. Click an optimal human route (100%).
3. Launch a new randomized mission and trigger a flare.
4. Show the red broken link, ten-second countdown, and reroute.
5. Reach Mars and let Dijkstra animate through its search.
6. Show the score and the saved leaderboard.

**If there is spare time:** add smooth packet-moving animation or a proper Dijkstra priority-queue visualization. **Do not** rush to add live NOAA data or Gemini before the core demo works.
