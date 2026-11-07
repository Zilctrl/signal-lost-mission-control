"""Tkinter mission-control dashboard. The routing algorithms live elsewhere."""
import math
import random
import tkinter as tk
from tkinter import font as tkfont

from algorithms import dijkstra
from game import Mission
from leaderboard import add_score, get_scores

BG = '#07101E'
PANEL = '#0C1A2D'
CARD = '#12243B'
BORDER = '#23415D'
WHITE = '#F2F8FF'
MUTED = '#9CB0C5'
CYAN = '#4AD9FF'
GREEN = '#4AE5AE'
AMBER = '#FFBE62'
RED = '#FF697C'
PURPLE = '#AD98FF'


class MissionControlApp:
    def __init__(self, root=None):
        self.root = root or tk.Tk()
        self.root.title('Signal Lost: Mission Control | Human vs Algorithms')
        self.root.configure(bg=BG)
        self.root.geometry('1290x840')
        self.root.minsize(1100, 760)
        self.mission_number = 1
        self._seed = 4401
        self.session = Mission(number=1, seed=self._seed)
        self.logs = []
        self.revealed = False
        self.animating = False
        self.explored = []
        self.hints = False
        self._animation_id = None
        self._timer_id = None
        self._stars = [(random.Random(i * 71 + 5).random(),
                        random.Random(i * 199 + 3).random(),
                        1 + (i % 3 == 0)) for i in range(100)]
        self._build_ui()
        self._bind_keys()
        self.message('Welcome, Pilot. Build the cheapest route from Earth to Mars.')
        self.message('Click a connected station. The bots reveal their routes at Mars.')
        self.refresh()

    def _text(self, parent, value, size=11, color=WHITE, bold=False, **kwargs):
        return tk.Label(parent, text=value, bg=parent.cget('bg'), fg=color,
                        font=('Segoe UI', size, 'bold' if bold else 'normal'),
                        anchor='w', **kwargs)

    def _button(self, parent, text, command, color=CYAN):
        button = tk.Button(parent, text=text, command=command, bg=CARD,
                           activebackground=BORDER, activeforeground=WHITE,
                           fg=color, font=('Segoe UI', 10, 'bold'),
                           borderwidth=1, relief='flat', padx=12, pady=12,
                           cursor='hand2', highlightthickness=0,
                           disabledforeground='#587080')
        return button

    def _build_ui(self):
        header = tk.Frame(self.root, bg=BG, height=88)
        header.pack(fill='x', padx=28, pady=(17, 8))
        header.pack_propagate(False)
        tk.Label(header, text='◈', bg=BG, fg=CYAN,
                 font=('Segoe UI Symbol', 28, 'bold')).pack(side='left', padx=(0, 13))
        title_frame = tk.Frame(header, bg=BG)
        title_frame.pack(side='left', anchor='center', pady=(5, 0))
        self._text(title_frame, 'SIGNAL LOST', size=25, bold=True).pack(anchor='w')
        self._text(title_frame, 'MISSION CONTROL  /  HUMAN  vs  GREEDY  vs  DIJKSTRA',
                   size=9, color=CYAN, bold=True).pack(anchor='w')
        self.header_status = self._text(header, '●  NETWORK ONLINE', size=10,
                                        color=GREEN, bold=True)
        self.header_status.pack(side='right', padx=4)

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill='both', expand=True, padx=25, pady=(0, 13))
        left = tk.Frame(body, bg=BG)
        left.pack(side='left', fill='both', expand=True, padx=(0, 15))
        right = tk.Frame(body, bg=PANEL, width=352, highlightbackground=BORDER,
                         highlightthickness=1)
        right.pack(side='right', fill='y')
        right.pack_propagate(False)

        map_header = tk.Frame(left, bg=BG)
        map_header.pack(fill='x', pady=(0, 8))
        self.map_title = self._text(map_header, 'MISSION 01  •  TRAINING NETWORK',
                                    size=12, bold=True)
        self.map_title.pack(side='left')
        self._text(map_header, 'LINK WEIGHTS = SIMULATED COST',
                   size=9, color=MUTED).pack(side='right')

        self.canvas = tk.Canvas(left, bg='#091529', highlightbackground=BORDER,
                                highlightthickness=1, bd=0, height=500,
                                cursor='crosshair')
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.canvas.bind('<Configure>', lambda _event: self.draw_network())

        legend = tk.Frame(left, bg=BG)
        legend.pack(fill='x', pady=(9, 14))
        for char, text, color in [('●', 'YOUR PATH', CYAN), ('●', 'DIJKSTRA', GREEN),
                                   ('●', 'GREEDY', AMBER), ('✕', 'BROKEN LINK', RED)]:
            self._text(legend, f'{char}  {text}', size=9, color=color,
                       bold=True).pack(side='left', padx=(0, 26))

        actions = tk.Frame(left, bg=BG)
        actions.pack(fill='x')
        self.flare_button = self._button(actions, '☀  TRIGGER SOLAR FLARE [F]',
                                          self.trigger_flare, AMBER)
        self.flare_button.pack(side='left', padx=(0, 8))
        self.undo_button = self._button(actions, '↶  UNDO [Z]', self.undo)
        self.undo_button.pack(side='left', padx=(0, 8))
        self.restart_button = self._button(actions, '⟳  RETRY', self.restart)
        self.restart_button.pack(side='left', padx=(0, 8))
        self.new_button = self._button(actions, '✦  NEXT MAP [N]', self.new_map, GREEN)
        self.new_button.pack(side='left', padx=(0, 8))
        self.skip_button = self._button(actions, 'SKIP REVEAL', self.skip_animation, PURPLE)
        self.skip_button.pack(side='left')

        tip = tk.Frame(left, bg=BG)
        tip.pack(fill='x', pady=(13, 0))
        self.tip = self._text(tip,
            'HOW TO PLAY   Select connected nodes • 10-second rescue after a flare • Reach Mars to compare',
            size=9, color=MUTED)
        self.tip.pack(anchor='w')

        content = tk.Frame(right, bg=PANEL)
        content.pack(fill='both', expand=True, padx=19, pady=18)
        self._text(content, 'PILOT CONSOLE', size=14, bold=True).pack(anchor='w')
        self._text(content, 'COMPETITOR TELEMETRY', size=9, color=MUTED,
                   bold=True).pack(anchor='w', pady=(4, 16))

        mission_card = tk.Frame(content, bg=CARD, highlightbackground=BORDER,
                                highlightthickness=1)
        mission_card.pack(fill='x', pady=(0, 12))
        self._text(mission_card, 'TARGET  ·  EARTH → MARS',
                   size=9, color=CYAN, bold=True).pack(anchor='w', padx=12, pady=(11, 1))
        self.human_label = self._text(mission_card, 'HUMAN  0 units', size=16, bold=True)
        self.human_label.pack(anchor='w', padx=12, pady=(4, 1))
        self.current_label = self._text(mission_card, 'CURRENT: EARTH', size=9, color=MUTED)
        self.current_label.pack(anchor='w', padx=12, pady=(0, 11))

        self._text(content, 'THE COMPETITION', size=9, color=MUTED,
                   bold=True).pack(anchor='w', pady=(0, 6))
        bot_card = tk.Frame(content, bg=CARD, highlightbackground=BORDER,
                            highlightthickness=1)
        bot_card.pack(fill='x', pady=(0, 12))
        self.greedy_label = self._text(bot_card, '●  GREEDY      — —',
                                       size=12, color=AMBER, bold=True)
        self.greedy_label.pack(anchor='w', padx=12, pady=(11, 6))
        self.dijkstra_label = self._text(bot_card, '●  DIJKSTRA   — —',
                                         size=12, color=GREEN, bold=True)
        self.dijkstra_label.pack(anchor='w', padx=12, pady=(0, 11))

        timer_card = tk.Frame(content, bg=CARD, highlightbackground=BORDER,
                              highlightthickness=1)
        timer_card.pack(fill='x', pady=(0, 12))
        self.timer_label = self._text(timer_card, '☀  DISASTER MODE  •  STANDBY',
                                      size=11, color=MUTED, bold=True)
        self.timer_label.pack(anchor='w', padx=11, pady=12)

        self._text(content, 'MISSION DEBRIEF', size=9, color=MUTED,
                   bold=True).pack(anchor='w', pady=(0, 5))
        debrief_frame = tk.Frame(content, bg=CARD, highlightbackground=BORDER,
                                 highlightthickness=1)
        debrief_frame.pack(fill='x', pady=(0, 12))
        self.score_label = self._text(debrief_frame, 'SCORE  —', size=17,
                                       color=WHITE, bold=True)
        self.score_label.pack(anchor='w', padx=12, pady=(10, 2))
        self.debrief_label = tk.Label(debrief_frame,
            text='Finish the route to see how your\nchoices compare with both bots.',
            bg=CARD, fg=MUTED, justify='left', wraplength=294,
            font=('Segoe UI', 9), anchor='w')
        self.debrief_label.pack(fill='x', padx=12, pady=(0, 12))

        name_row = tk.Frame(content, bg=PANEL)
        name_row.pack(fill='x', pady=(0, 8))
        self._text(name_row, 'PILOT NAME', size=9, color=MUTED).pack(side='left')
        self.name = tk.StringVar(value='PILOT')
        tk.Entry(name_row, textvariable=self.name, width=13,
                 bg=CARD, fg=WHITE, insertbackground=WHITE, relief='flat',
                 font=('Segoe UI', 10)).pack(side='right', ipady=4)
        self._text(content, 'LOCAL LEADERBOARD  /  TOP 4',
                   size=9, color=MUTED, bold=True).pack(anchor='w', pady=(0, 5))
        self.leaderboard_label = tk.Label(content, text='', bg=PANEL, fg=WHITE,
                                           justify='left', anchor='nw',
                                           font=('Consolas', 9))
        self.leaderboard_label.pack(fill='x', pady=(0, 9))

        self._text(content, 'EVENT LOG', size=9, color=MUTED,
                   bold=True).pack(anchor='w', pady=(0, 6))
        self.log_label = tk.Label(content, text='', bg=PANEL, fg=MUTED,
                                   justify='left', anchor='nw', wraplength=306,
                                   font=('Segoe UI', 9))
        self.log_label.pack(fill='x')
        self._show_leaderboard()

    def _bind_keys(self):
        self.root.bind('<KeyPress-z>', lambda _e: self.undo())
        self.root.bind('<KeyPress-f>', lambda _e: self.trigger_flare())
        self.root.bind('<KeyPress-n>', lambda _e: self.new_map())
        self.root.protocol('WM_DELETE_WINDOW', self.close)

    def close(self):
        self._stop_scheduled()
        self.root.destroy()

    def _stop_scheduled(self):
        for attr in ('_timer_id', '_animation_id'):
            value = getattr(self, attr)
            if value is not None:
                try:
                    self.root.after_cancel(value)
                except tk.TclError:
                    pass
                setattr(self, attr, None)

    def message(self, value):
        self.logs.insert(0, value)
        self.logs = self.logs[:5]
        if hasattr(self, 'log_label'):
            self.log_label.config(text='\n'.join('› ' + line for line in self.logs[:4]))

    def _show_leaderboard(self):
        scores = get_scores()
        lines = [f"{i + 1:>2}.  {e['pilot'][:11]:<11}  {e['score']:>3}%" for i, e in enumerate(scores[:4])]
        self.leaderboard_label.config(text='\n'.join(lines) if lines else 'No completed missions yet.')

    def new_map(self):
        self.mission_number += 1
        self.start_mission(self.mission_number, random.randrange(1000, 1000000))

    def start_mission(self, number, seed):
        self._stop_scheduled()
        self.mission_number = number
        self._seed = seed
        self.session = Mission(number=number, seed=seed)
        self.revealed = False
        self.animating = False
        self.explored = []
        self.logs = []
        self.message('New network online. Plan your route before the flare.')
        if number >= 2:
            self.message('AUTO FLARE ARMED: after two moves, 10 seconds to finish.')
        self.refresh()

    def restart(self):
        self.start_mission(self.mission_number, self._seed)

    def undo(self):
        if self.animating:
            return
        if self.session.undo():
            self.message(f'Last hop undone. Back at {self.session.current}.')
            self.refresh()

    def on_canvas_click(self, event):
        if self.animating or self.session.finished:
            return
        coords = self._coords()
        closest = min(coords, key=lambda n: (coords[n][0] - event.x) ** 2 +
                      (coords[n][1] - event.y) ** 2)
        x, y = coords[closest]
        if math.hypot(x - event.x, y - event.y) > 27:
            return
        if not self.session.move(closest):
            self.message(f'Invalid hop to {closest}. Choose a linked, unvisited station.')
            self.refresh()
            return
        self.message(f'Connected to {closest}. Total signal cost: {self.session.route_cost}.')
        if self.session.finished:
            self._on_finish()
        elif self.mission_number >= 2 and len(self.session.route) == 3 and not self.session.flare_triggered:
            self.trigger_flare()
        else:
            self.refresh()

    def trigger_flare(self):
        if self.animating:
            return
        broken = self.session.trigger_flare()
        if broken is None:
            if not self.session.flare_triggered and not self.session.finished:
                self.message('No safe alternate route from this position. Flare skipped.')
            self.refresh()
            return
        a, b = broken
        self.message(f'⚠ SOLAR FLARE! {a} ↔ {b} is OFFLINE. Rescue: 10 seconds!')
        self.message(f'Checkpoint locked at {self.session.current}; bots reroute from here.')
        self.refresh()
        self._schedule_tick()

    def _schedule_tick(self):
        if self.session.remaining_seconds is None or self.session.finished:
            return
        self._timer_id = self.root.after(1000, self._on_tick)

    def _on_tick(self):
        self._timer_id = None
        timed_out = self.session.tick()
        if timed_out:
            self.message('TIMEOUT! Communication failed before reaching Mars.')
            self.revealed = True
        else:
            self._schedule_tick()
        self.refresh()

    def _on_finish(self):
        result = self.session.result
        if result is None:
            return
        self._stop_scheduled()
        self.message('Destination reached. Dijkstra is scanning the network...')
        if result.score:
            add_score(self.name.get(), self.mission_number, result.score,
                      result.human_cost, result.optimal_cost)
            self._show_leaderboard()
        self.explored = []
        self.revealed = False
        self.animating = True
        self.refresh()
        self._animation_id = self.root.after(280, lambda: self._animate_step(0))

    def _animate_step(self, index):
        self._animation_id = None
        trace = self.session.result.optimal_route.explored
        if index >= len(trace):
            self.skip_animation()
            return
        node = trace[index]
        self.explored.append(node)
        self.message(f'DIJKSTRA EXPLORES: {node} ({index + 1}/{len(trace)})')
        self.refresh()
        self._animation_id = self.root.after(275, lambda: self._animate_step(index + 1))

    def skip_animation(self):
        if self._animation_id is not None:
            self.root.after_cancel(self._animation_id)
            self._animation_id = None
        if self.session.result:
            self.explored = list(self.session.result.optimal_route.explored)
        self.animating = False
        self.revealed = True
        if self.session.result:
            self.message(f'MISSION COMPLETE: {self.session.result.score}% efficiency. Compare all routes.')
        self.refresh()

    def _coords(self):
        width = max(800, self.canvas.winfo_width())
        height = max(400, self.canvas.winfo_height())
        return {name: (int(x * width), int(y * height))
                for name, (x, y) in self.session.network.positions.items()}

    def _draw_route(self, path, coords, color, width=3, dash=None):
        for a, b in zip(path, path[1:]):
            if a not in coords or b not in coords:
                continue
            x1, y1 = coords[a]
            x2, y2 = coords[b]
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width,
                                    dash=dash)

    def draw_network(self):
        c = self.canvas
        c.delete('all')
        w = max(800, c.winfo_width())
        h = max(400, c.winfo_height())
        coords = self._coords()
        for sx, sy, big in self._stars:
            x, y = sx * w, sy * h
            c.create_oval(x, y, x + big, y + big, fill='#30455C', outline='')
        for radius in (95, 165, 240):
            c.create_oval(0.09 * w - radius, 0.49 * h - radius,
                          0.09 * w + radius, 0.49 * h + radius,
                          outline='#14283A', width=1)
        c.create_text(20, 25, text='INTERPLANETARY RELAY GRID  /  SECTOR A',
                      anchor='w', fill='#526C8A', font=('Consolas', 9, 'bold'))

        for (a, b), cost in sorted(self.session.network.edges.items()):
            x1, y1 = coords[a]
            x2, y2 = coords[b]
            c.create_line(x1, y1, x2, y2, fill='#36506B', width=2)

        if self.revealed and self.session.result:
            res = self.session.result
            self._draw_route(res.greedy_route.path, coords, AMBER, 4, (5, 5))
            self._draw_route(res.optimal_route.path, coords, GREEN, 5, (8, 4))
        elif self.revealed and self.session.timed_out:
            _, best = self.session.baseline()
            self._draw_route(best.path, coords, GREEN, 5, (8, 4))

        self._draw_route(self.session.route, coords, CYAN, 5)
        for a, b, _weight in self.session.failed_links:
            x1, y1 = coords[a]
            x2, y2 = coords[b]
            c.create_line(x1, y1, x2, y2, fill=RED, width=4, dash=(5, 5))
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            c.create_text(mx, my - 20, text='✕', fill=RED,
                          font=('Segoe UI Symbol', 22, 'bold'))

        # Weight markers are redrawn after route highlights so numbers stay readable.
        for (a, b), cost in sorted(self.session.network.edges.items()):
            x1, y1 = coords[a]
            x2, y2 = coords[b]
            midx, midy = (x1 + x2) / 2, (y1 + y2) / 2
            c.create_rectangle(midx - 14, midy - 10, midx + 14, midy + 10,
                               fill='#0D1B2F', outline='#31526A', width=1)
            c.create_text(midx, midy, text=str(cost), fill=WHITE,
                          font=('Consolas', 10, 'bold'))

        legal_nodes = set(self.session.legal_next())
        for name, (x, y) in coords.items():
            is_current = name == self.session.current
            in_human = name in self.session.route
            explored = name in self.explored
            if explored:
                c.create_oval(x - 32, y - 32, x + 32, y + 32,
                              outline=PURPLE, width=2, dash=(4, 3))
            if is_current:
                c.create_oval(x - 30, y - 30, x + 30, y + 30,
                              outline=AMBER, width=3)
            if name in legal_nodes:
                c.create_oval(x - 27, y - 27, x + 27, y + 27,
                              outline='#397E8C', width=1)
            fill = '#184055' if in_human else '#153047'
            outline = CYAN if in_human else '#5B809D'
            if name == 'EARTH':
                fill, outline = '#134F77', CYAN
            elif name == 'MARS':
                fill, outline = '#713D42', RED
            c.create_oval(x - 21, y - 21, x + 21, y + 21,
                          fill=fill, outline=outline, width=2)
            symbol = 'E' if name == 'EARTH' else 'M' if name == 'MARS' else name[0]
            c.create_text(x, y - 1, text=symbol,
                          fill=WHITE, font=('Segoe UI', 16, 'bold'))
            c.create_text(x, y + 35, text=name, fill=WHITE if in_human else MUTED,
                          font=('Consolas', 9, 'bold'))

        if self.session.flare_triggered:
            c.create_text(w - 20, 24, text='⚠ SOLAR FLARE ACTIVE', anchor='e',
                          fill=RED, font=('Consolas', 10, 'bold'))
        else:
            c.create_text(w - 20, 24, text='● LINKS NOMINAL', anchor='e',
                          fill=GREEN, font=('Consolas', 10, 'bold'))

    @staticmethod
    def _fmt(value):
        return 'STUCK' if not math.isfinite(value) else f'{int(value)} units'

    def refresh(self):
        s = self.session
        self.map_title.config(text=f'MISSION {self.mission_number:02d}  •  '
                                   + ('TRAINING NETWORK' if self.mission_number == 1 else 'RANDOMIZED NETWORK'))
        self.human_label.config(text=f'HUMAN   {s.route_cost} units')
        self.current_label.config(text=f'CURRENT: {s.current}  •  HOPS: {len(s.route) - 1}')
        if self.revealed and s.result:
            r = s.result
            self.greedy_label.config(text=f'●  GREEDY      {self._fmt(r.greedy_cost)}')
            self.dijkstra_label.config(text=f'●  DIJKSTRA    {self._fmt(r.optimal_cost)}')
            self.score_label.config(text=f'SCORE   {r.score}%',
                                    fg=GREEN if r.score == 100 else AMBER)
            msg = (f'Checkpoint: {r.checkpoint}\n'
                   f'{r.divergence}\n'
                   f'Extra cost vs optimum: +{int(r.extra_cost)} units.')
            self.debrief_label.config(text=msg, fg=WHITE)
        elif self.revealed and s.timed_out:
            bot, optimal = s.baseline()
            self.greedy_label.config(text=f'●  GREEDY      {self._fmt(s.checkpoint_cost + bot.cost)}')
            self.dijkstra_label.config(text=f'●  DIJKSTRA    {self._fmt(s.checkpoint_cost + optimal.cost)}')
            self.score_label.config(text='SCORE   0%', fg=RED)
            self.debrief_label.config(text='Communication timed out.\nRetry and reach Mars before 0:00.', fg=RED)
        elif self.animating:
            self.greedy_label.config(text='●  GREEDY      computing...')
            self.dijkstra_label.config(text='●  DIJKSTRA    scanning...')
            self.score_label.config(text='ALGORITHM REVEAL', fg=PURPLE)
            self.debrief_label.config(text='Watch the purple rings: they show\nthe nodes Dijkstra settles in order.', fg=WHITE)
        else:
            self.greedy_label.config(text='●  GREEDY      ???')
            self.dijkstra_label.config(text='●  DIJKSTRA    ???')
            self.score_label.config(text='SCORE   —', fg=WHITE)
            self.debrief_label.config(text='Finish the route to see how your\nchoices compare with both bots.', fg=MUTED)

        if s.remaining_seconds is not None and not s.finished:
            self.timer_label.config(text=f'⚠  FLARE RESCUE   0:{s.remaining_seconds:02d}',
                                    fg=RED if s.remaining_seconds <= 3 else AMBER)
            self.header_status.config(text='●  LINK FAILURE / REROUTE', fg=RED)
        elif s.timed_out:
            self.timer_label.config(text='✕  CONNECTION TIMED OUT', fg=RED)
            self.header_status.config(text='●  MISSION FAILED', fg=RED)
        elif s.finished:
            self.timer_label.config(text='✓  MISSION COMPLETE', fg=GREEN)
            self.header_status.config(text='●  SIGNAL DELIVERED', fg=GREEN)
        elif s.flare_triggered:
            self.timer_label.config(text='☀  FLARE CLEARED', fg=AMBER)
            self.header_status.config(text='●  DAMAGED NETWORK', fg=AMBER)
        else:
            self.timer_label.config(text='☀  DISASTER MODE  •  STANDBY', fg=MUTED)
            self.header_status.config(text='●  NETWORK ONLINE', fg=GREEN)

        self.flare_button.config(state='normal' if not s.finished and not s.flare_triggered and not self.animating else 'disabled')
        self.undo_button.config(state='normal' if not s.finished and len(s.route) > s.checkpoint_index + 1 and not self.animating else 'disabled')
        self.skip_button.config(state='normal' if self.animating else 'disabled')
        self.draw_network()

    def run(self):
        self.root.mainloop()
