"""The game board: a real maze whose escape route is found with BFS."""
import functools
from collections import deque

from algos import make_maze, grid_adj

GAME_SEED, GAME_RC, GAME_CC = 15, 7, 12      # 15 x 25 grid, escape route of ~100 cells


@functools.lru_cache(maxsize=None)
def game_maze():
    g = make_maze(GAME_RC, GAME_CC, GAME_SEED, loops=0)
    R, C = len(g), len(g[0])
    adj = grid_adj(g)
    start, goal = 1 * C + 1, (R - 2) * C + (C - 2)
    parent, q = {start: None}, deque([start])
    while q:                                   # BFS = the route the agent runs along
        n = q.popleft()
        if n == goal:
            break
        for m, _ in adj[n]:
            if m not in parent:
                parent[m] = n
                q.append(m)
    path, n = [], goal
    while n is not None:
        path.append(n)
        n = parent[n]
    return g, path[::-1]


CSS = """<style>
.mz{display:grid;gap:1px;background:#0b1220;border-radius:12px;padding:6px;max-width:780px;margin:0 auto 6px;border:1px solid #1e293b}
.mz div{aspect-ratio:1;display:flex;align-items:center;justify-content:center;font-size:clamp(7px,1.45vw,15px);border-radius:2px;line-height:1}
.mz .w{background:#0b1220}.mz .r{background:#334155}.mz .t{background:#166534}.mz .e{background:#7f1d1d}
</style>"""


def render_maze(p_frac, gap, door_fracs=(), caught=False, escaped=False):
    g, path = game_maze()
    R, C = len(g), len(g[0])
    L = len(path)
    p_idx = L - 1 if escaped else int(round(p_frac * (L - 1)))
    if caught or gap <= 0:
        c_idx = p_idx
    else:
        c_idx = max(0, int(round(max(0.0, p_frac - 0.04 * gap) * (L - 1))))
        if c_idx >= p_idx:
            c_idx = max(0, p_idx - 1)
    pos = {n: i for i, n in enumerate(path)}
    doors = {int(round(f * (L - 1))) for f in door_fracs}
    cells = []
    for r in range(R):
        for c in range(C):
            n = r * C + c
            if n not in pos:
                cells.append('<div class="w"></div>')
                continue
            i = pos[n]
            cls, txt = "r", ""
            if i <= c_idx:
                cls = "e"
            elif i <= p_idx:
                cls = "t"
            if i in doors and i > p_idx:
                txt = "🚩"
            if i == L - 1:
                txt = "🎉" if escaped else "🚪"
            if i == 0 and p_idx > 0 and c_idx > 0:
                txt = "🧪"
            if i == c_idx and not escaped:
                txt = "🐛"
            if i == p_idx:
                txt = "💥" if (caught or gap <= 0) and not escaped else "🤖"
            cells.append(f'<div class="{cls}">{txt}</div>')
    return CSS + f'<div class="mz" style="grid-template-columns:repeat({C},1fr)">' + "".join(cells) + "</div>"
