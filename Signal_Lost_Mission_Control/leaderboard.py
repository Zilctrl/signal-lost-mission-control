"""Local-only JSON scoreboard. Writing failures should never crash the game."""
import json
from pathlib import Path
from datetime import datetime

SCORE_FILE = Path(__file__).resolve().parent / 'leaderboard.json'


def get_scores(path=SCORE_FILE):
    try:
        value = json.loads(Path(path).read_text(encoding='utf-8'))
        return value if isinstance(value, list) else []
    except (FileNotFoundError, OSError, ValueError, TypeError):
        return []


def add_score(name, mission_number, score, player_cost, optimal_cost, path=SCORE_FILE):
    entries = get_scores(path)
    entries.append({
        'pilot': (name.strip() or 'PILOT')[:18],
        'mission': int(mission_number),
        'score': int(score),
        'human_cost': int(player_cost),
        'optimal_cost': int(optimal_cost),
        'date': datetime.now().strftime('%Y-%m-%d'),
    })
    entries.sort(key=lambda entry: (-entry['score'], entry['human_cost'], entry['date']))
    entries = entries[:20]
    try:
        Path(path).write_text(json.dumps(entries, indent=2), encoding='utf-8')
    except OSError:
        pass
    return entries
