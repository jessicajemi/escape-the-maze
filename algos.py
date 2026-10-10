"""
Real implementations of the algorithms in Units I & II.
Each function returns "frames": one dict per step, which the live visualiser
(player.py) plays back. The same code is used to double-check the quiz answers.

Frame keys (all optional except cur):
  cur    node being expanded / visited now
  fro    nodes currently waiting in the frontier
  note   one-line explanation of this step
  ds     text showing the data structure (queue / stack / open list ...)
  reset  True = start of a new iteration (clears the visited trail)
  path   final path (only on the last frame)
  sub    {node: text} small labels under nodes (e.g. f-values)
  col    {node: colour index}  (CSP only)
"""
from collections import deque
import heapq
import math
import random

# ───────────────────────── graphs used in the quiz ─────────────────────────

# A small tree. Children are expanded left to right.   Goal G is at depth 3.
TREE = dict(
    pos={"S": (0.50, 0.10), "A": (0.25, 0.38), "B": (0.75, 0.38),
         "C": (0.12, 0.68), "D": (0.38, 0.68), "E": (0.62, 0.68),
         "F": (0.88, 0.68), "G": (0.38, 0.94)},
    children={"S": ["A", "B"], "A": ["C", "D"], "B": ["E", "F"], "D": ["G"]},
    start="S", goal="G",
)

# A weighted graph where greedy search is fooled but A* is not.
WG = dict(
    pos={"S": (0.07, 0.50), "A": (0.33, 0.15), "C": (0.67, 0.15),
         "B": (0.38, 0.85), "G": (0.93, 0.50)},
    edges=[("S", "A", 1), ("S", "B", 4), ("A", "C", 2), ("C", "G", 10), ("B", "G", 4)],
    h={"S": 2, "A": 1, "B": 3, "C": 1, "G": 0},
    start="S", goal="G",
)

# 1-D landscape used in the hill-climbing question (state 0..9)
LANDSCAPE10 = [2, 4, 7, 5, 3, 6, 9, 8, 4, 1]

# Australia map colouring (+ a wheel that needs 4 colours, to show backtracking)
AUS = dict(
    pos={"WA": (0.12, 0.50), "NT": (0.40, 0.20), "SA": (0.45, 0.58), "Q": (0.78, 0.22),
         "NSW": (0.80, 0.55), "V": (0.65, 0.85), "T": (0.85, 0.92)},
    edges=[("WA", "NT"), ("WA", "SA"), ("NT", "SA"), ("NT", "Q"), ("SA", "Q"),
           ("SA", "NSW"), ("SA", "V"), ("Q", "NSW"), ("NSW", "V")],
    order=["WA", "NT", "SA", "Q", "NSW", "V", "T"],
)
WHEEL = dict(
    pos={"H": (0.50, 0.50), "P1": (0.50, 0.08), "P2": (0.88, 0.36),
         "P3": (0.74, 0.88), "P4": (0.26, 0.88), "P5": (0.12, 0.36)},
    edges=[("H", "P1"), ("H", "P2"), ("H", "P3"), ("H", "P4"), ("H", "P5"),
           ("P1", "P2"), ("P2", "P3"), ("P3", "P4"), ("P4", "P5"), ("P5", "P1")],
    order=["P1", "P2", "P3", "P4", "P5", "H"],
)
COLOUR_NAMES = ["Red", "Green", "Blue", "Yellow"]


def undirected(edges):
    adj = {}
    for e in edges:
        a, b = e[0], e[1]
        w = e[2] if len(e) > 2 else 1
        adj.setdefault(a, []).append((b, w))
        adj.setdefault(b, []).append((a, w))
    for k in adj:
        adj[k].sort(key=lambda t: str(t[0]))
    return adj


def tree_adj(children):
    return {k: [(c, 1) for c in v] for k, v in children.items()}


# ───────────────────────── generic uninformed / informed search ─────────────

def search_frames(adj, start, goals, algo, h=None, fmt=str):
    """BFS / DFS / Greedy best-first / A* on an adjacency dict {n: [(m, cost)]}.
    Returns (frames, stats). Goal test is done when a node is REMOVED from the
    frontier (that is when the textbook algorithms test it)."""
    goals = set(goals)
    frames = []
    parent = {}
    gcost = {start: 0}

    def path_to(n):
        p = []
        while n is not None:
            p.append(n)
            n = parent.get(n)
        return p[::-1]

    def finish(n, extra_note):
        p = path_to(n)
        cost = sum(dict(adj[a])[b] for a, b in zip(p, p[1:]))
        return p, cost

    expanded = 0

    if algo == "bfs":
        parent[start] = None
        frontier = deque([start])
        seen = {start}
        while frontier:
            n = frontier.popleft()
            expanded += 1
            if n in goals:
                p, cost = finish(n, "")
                frames.append(dict(cur=n, fro=list(frontier), path=p,
                                   note=f"Dequeue {fmt(n)}: it is the GOAL!",
                                   ds=f"Queue (front → back): [{', '.join(map(fmt, frontier))}]",
                                   result=f"Goal found · path length {len(p)-1} steps · {expanded} nodes expanded"))
                return frames, dict(expanded=expanded, path=p, cost=cost)
            new = []
            for m, _ in adj.get(n, []):
                if m not in seen:
                    seen.add(m)
                    parent[m] = n
                    frontier.append(m)
                    new.append(m)
            frames.append(dict(cur=n, fro=list(frontier),
                               note=f"Dequeue {fmt(n)}. Add {', '.join(map(fmt, new)) if new else 'nothing new'} to the BACK of the queue.",
                               ds=f"Queue (front → back): [{', '.join(map(fmt, frontier))}]"))
        return frames, dict(expanded=expanded, path=None, cost=None)

    if algo == "dfs":
        stack = [(start, None)]
        seen = set()
        while stack:
            n, par = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            parent[n] = par
            expanded += 1
            if n in goals:
                p, cost = finish(n, "")
                frames.append(dict(cur=n, fro=[x for x, _ in stack], path=p,
                                   note=f"Pop {fmt(n)} from the stack: it is the GOAL!",
                                   ds=f"Stack (top → bottom): [{', '.join(fmt(x) for x, _ in reversed(stack))}]",
                                   result=f"Goal found · path length {len(p)-1} steps · {expanded} nodes expanded"))
                return frames, dict(expanded=expanded, path=p, cost=cost)
            new = [m for m, _ in adj.get(n, []) if m not in seen]
            for m in reversed(new):
                stack.append((m, n))
            frames.append(dict(cur=n, fro=[x for x, _ in stack if x not in seen],
                               note=f"Pop {fmt(n)}. Push {', '.join(map(fmt, new)) if new else 'nothing new'} on TOP of the stack (leftmost on top).",
                               ds=f"Stack (top → bottom): [{', '.join(fmt(x) for x, _ in reversed(stack))}]"))
        return frames, dict(expanded=expanded, path=None, cost=None)

    # Greedy best-first and A*
    assert h is not None
    counter = 0
    heap = []
    best_g = {start: 0}
    parent[start] = None

    def prio(n, g):
        return h[n] if algo == "greedy" else g + h[n]

    heapq.heappush(heap, (prio(start, 0), counter, start, 0, None))
    closed = set()
    label = "h" if algo == "greedy" else "f"

    def open_list():
        items = sorted((p, c, n) for p, c, n, g, par in heap
                       if n not in closed and (algo == "greedy" or g <= best_g.get(n, math.inf)))
        seen_n, out = set(), []
        for p, c, n in items:
            if n in seen_n:
                continue
            seen_n.add(n)
            out.append((n, p))
        return out

    while heap:
        p_, _, n, g, par = heapq.heappop(heap)
        if n in closed:
            continue
        if algo == "astar" and g > best_g.get(n, math.inf):
            continue
        closed.add(n)
        parent[n] = par
        gcost[n] = g
        expanded += 1
        if n in goals:
            p, cost = finish(n, "")
            frames.append(dict(cur=n, fro=[x for x, _ in open_list()], path=p,
                               note=f"Remove {fmt(n)} ({label}={p_}): it is the GOAL!",
                               ds="Open list: " + ", ".join(f"{fmt(x)}({label}={v})" for x, v in open_list()),
                               result=f"Goal found · path cost {cost} · {expanded} nodes expanded"))
            return frames, dict(expanded=expanded, path=p, cost=cost)
        for m, w in adj.get(n, []):
            if m in closed:
                continue
            ng = g + w
            if algo == "astar" and ng >= best_g.get(m, math.inf):
                continue
            best_g[m] = ng
            counter += 1
            heapq.heappush(heap, (prio(m, ng), counter, m, ng, n))
        ol = open_list()
        if algo == "greedy":
            note = f"Remove {fmt(n)} (lowest h = {h[n]}). Add its neighbours to the open list ordered by h."
        else:
            note = (f"Remove {fmt(n)} (lowest f = g + h = {g} + {h[n]} = {g + h[n]}). "
                    f"Update neighbours with f = g + h.")
        frames.append(dict(cur=n, fro=[x for x, _ in ol], note=note,
                           ds="Open list: " + ", ".join(f"{fmt(x)}({label}={v})" for x, v in ol),
                           sub={x: f"{label}={v}" for x, v in ol}))
    return frames, dict(expanded=expanded, path=None, cost=None)


def iddfs_frames(children, start, goal, max_limit=8):
    """Iterative deepening DFS on a tree. Counts every visit (repeats included)."""
    frames = []
    visits = 0
    for limit in range(max_limit + 1):
        stack = [(start, 0, (start,))]
        first = True
        while stack:
            n, d, path = stack.pop()
            visits += 1
            if n == goal:
                frames.append(dict(
                    cur=n, fro=[x for x, _, _ in stack], reset=first, path=list(path),
                    note=f"Limit {limit}: visit {n} at depth {d}: it is the GOAL!",
                    ds=f"Depth limit = {limit} · total visits so far = {visits}",
                    result=f"Goal found at depth limit {limit} · {visits} node visits in total (repeats counted)"))
                return frames, dict(limit=limit, visits=visits, path=list(path))
            kids = children.get(n, [])
            if d < limit:
                for c in reversed(kids):
                    stack.append((c, d + 1, path + (c,)))
                what = f"push {', '.join(kids)}" if kids else "no children"
            else:
                what = "depth limit reached, do not go deeper"
            frames.append(dict(
                cur=n, fro=[x for x, _, _ in stack], reset=first,
                note=f"Limit {limit}: visit {n} at depth {d}: {what}.",
                ds=f"Depth limit = {limit} · stack (top → bottom): [{', '.join(x for x, _, _ in reversed(stack))}]"))
            first = False
        frames.append(dict(cur=None, fro=[], note=f"Goal NOT found within limit {limit}. Restart with limit {limit + 1}.",
                           ds=f"Depth limit = {limit} finished · total visits so far = {visits}"))
    return frames, dict(limit=None, visits=visits, path=None)


# ───────────────────────── water jug state space ────────────────────────────

def jug_moves(state, cap=(4, 3)):
    x, y = state
    a, b = cap
    out = [(a, y), (x, b), (0, y), (x, 0)]
    t = min(x, b - y)
    out.append((x - t, y + t))
    t = min(y, a - x)
    out.append((x + t, y - t))
    res = []
    for s in out:
        if s != state and s not in res:
            res.append(s)
    return res


def jug_bfs():
    """BFS over the water-jug state space. Returns (frames, stats, layout, tree_edges)."""
    start = (0, 0)
    sid = lambda s: f"{s[0]},{s[1]}"
    fmt = lambda s: f"({s[0]},{s[1]})"
    adj = {}
    seen = {start}
    q = deque([start])
    while q:
        s = q.popleft()
        adj[s] = [(m, 1) for m in jug_moves(s)]
        for m in jug_moves(s):
            if m not in seen:
                seen.add(m)
                q.append(m)
    goals = [s for s in adj if s[0] == 2]
    frames, stats = search_frames(adj, start, goals, "bfs", fmt=fmt)
    # BFS tree for layout
    depth, par = {start: 0}, {start: None}
    q = deque([start])
    while q:
        s = q.popleft()
        for m, _ in adj[s]:
            if m not in depth:
                depth[m] = depth[s] + 1
                par[m] = s
                q.append(m)
    by_depth = {}
    for s, d in depth.items():
        by_depth.setdefault(d, []).append(s)
    maxd = max(by_depth)
    pos = {}
    for d, lst in by_depth.items():
        lst.sort()
        for i, s in enumerate(lst):
            pos[s] = ((d + 0.5) / (maxd + 1), (i + 0.5) / len(lst))
    tree_edges = [(par[s], s) for s in par if par[s] is not None]
    return frames, stats, pos, tree_edges, goals


# ───────────────────────── grid maze ────────────────────────────────────────

def make_maze(rc, cc, seed, loops=0):
    """Perfect maze (DFS carving) of rc x cc rooms -> grid (2rc+1) x (2cc+1).
    `loops` extra walls are knocked out so that there is more than one route."""
    rnd = random.Random(seed)
    R, C = 2 * rc + 1, 2 * cc + 1
    g = [[1] * C for _ in range(R)]
    stack = [(0, 0)]
    g[1][1] = 0
    visited = {(0, 0)}
    while stack:
        r, c = stack[-1]
        nb = [(r + dr, c + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
              if 0 <= r + dr < rc and 0 <= c + dc < cc and (r + dr, c + dc) not in visited]
        if not nb:
            stack.pop()
            continue
        nr, nc = rnd.choice(nb)
        visited.add((nr, nc))
        g[2 * nr + 1][2 * nc + 1] = 0
        g[r + nr + 1][c + nc + 1] = 0
        stack.append((nr, nc))
    walls = [(r, c) for r in range(1, R - 1) for c in range(1, C - 1)
             if g[r][c] == 1 and (
                 (r % 2 == 1 and c % 2 == 0 and g[r][c - 1] == 0 and g[r][c + 1] == 0) or
                 (r % 2 == 0 and c % 2 == 1 and g[r - 1][c] == 0 and g[r + 1][c] == 0))]
    rnd.shuffle(walls)
    for r, c in walls[:loops]:
        g[r][c] = 0
    return g


def grid_adj(g):
    R, C = len(g), len(g[0])
    adj = {}
    for r in range(R):
        for c in range(C):
            if g[r][c]:
                continue
            n = r * C + c
            lst = []
            for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):   # up, right, down, left
                rr, cc = r + dr, c + dc
                if 0 <= rr < R and 0 <= cc < C and not g[rr][cc]:
                    lst.append((rr * C + cc, 1))
            adj[n] = lst
    return adj


def manhattan_table(g, goal):
    R, C = len(g), len(g[0])
    gr, gc = divmod(goal, C)
    return {r * C + c: abs(r - gr) + abs(c - gc)
            for r in range(R) for c in range(C) if not g[r][c]}


def grid_run(g, algo):
    R, C = len(g), len(g[0])
    start, goal = 1 * C + 1, (R - 2) * C + (C - 2)
    adj = grid_adj(g)
    h = manhattan_table(g, goal) if algo in ("greedy", "astar") else None
    fmt = lambda n: f"({n // C},{n % C})"
    frames, stats = search_frames(adj, start, [goal], algo, h=h, fmt=fmt)
    for f in frames:                      # keep grid frames small
        f.pop("sub", None)
        if len(f.get("ds", "")) > 90:
            f["ds"] = f["ds"][:87] + "..."
    return frames, stats, start, goal


# ───────────────────────── hill climbing family ─────────────────────────────

def make_landscape(n=40):
    vals = []
    for x in range(n):
        v = (10 + 7 * math.sin(x / 3.2) + 4.5 * math.sin(x / 1.15 + 1.0)
             + 3.0 * math.cos(x / 6.0))
        vals.append(int(round(v)))
    for x in range(22, 27):               # a flat plateau
        vals[x] = vals[22]
    return vals


def hill_frames(values, start, variant, radius=2, seed=1):
    rnd = random.Random(seed)
    n = len(values)
    gmax = max(values)

    def nbrs(i):
        return [j for j in range(max(0, i - radius), min(n, i + radius + 1)) if j != i]

    def climb(i, mode, frames, reset):
        first = reset
        frames.append(dict(cur=i, reset=first, note=f"Start at state {i} (value {values[i]}).",
                           ds=f"value = {values[i]}"))
        steps = 0
        while steps < 60:
            steps += 1
            nb = nbrs(i)
            better = [j for j in nb if values[j] > values[i]]
            if not better:
                tag = "GLOBAL maximum" if values[i] == gmax else "LOCAL maximum (stuck!)"
                frames.append(dict(cur=i, note=f"No neighbour is better. Stop at state {i}: {tag}.",
                                   ds=f"value = {values[i]} · global max = {gmax}"))
                return i
            if mode == "simple":
                j = better[0]
                why = f"first better neighbour found (scanning left → right) is state {j}"
            elif mode == "steepest":
                j = max(better, key=lambda k: (values[k], -abs(k - i)))
                why = f"best of all neighbours is state {j} (value {values[j]})"
            elif mode == "stochastic":
                j = rnd.choice(better)
                why = f"picked a random uphill neighbour: state {j}"
            else:                              # first-choice
                order = nb[:]
                rnd.shuffle(order)
                j = None
                tried = 0
                for k in order:
                    tried += 1
                    if values[k] > values[i]:
                        j = k
                        break
                why = f"tried random neighbours, the first better one (after {tried} tries) is state {j}"
            if values[j] == values[i]:
                break
            i = j
            frames.append(dict(cur=i, note=f"Move to state {i} (value {values[i]}): {why}.",
                               ds=f"value = {values[i]}"))
        return i

    frames = []
    if variant in ("simple", "steepest", "stochastic", "first"):
        end = climb(start, {"first": "first"}.get(variant, variant), frames, True)
        frames[-1]["result"] = (f"Finished at value {values[end]} — "
                                f"{'the global maximum' if values[end] == gmax else 'a local maximum, global is ' + str(gmax)}")
    elif variant == "restart":
        tries, i0 = 0, start
        while tries < 8:
            tries += 1
            end = climb(i0, "steepest", frames, True)
            if values[end] == gmax:
                frames[-1]["result"] = f"Global maximum {gmax} reached after {tries} climb(s)."
                break
            frames.append(dict(cur=end, note=f"Stuck at a local maximum. RANDOM RESTART #{tries}.",
                               ds=f"climbs so far = {tries}"))
            i0 = rnd.randrange(n)
        else:
            frames[-1]["result"] = f"Best value found {values[end]} after {tries} climbs."
    elif variant == "anneal":
        i, T = start, 12.0
        best = i
        frames.append(dict(cur=i, reset=True, note=f"Start at state {i} (value {values[i]}), temperature T = {T:.1f}.",
                           ds=f"value = {values[i]}"))
        for step in range(70):
            j = rnd.choice(nbrs(i))
            d = values[j] - values[i]
            if d > 0:
                acc, why = True, f"better by {d}: always accept"
            else:
                p = math.exp(d / T)
                acc = rnd.random() < p
                why = f"worse by {-d}: accept with probability e^({d}/{T:.1f}) = {p:.2f} → {'ACCEPTED' if acc else 'rejected'}"
            if acc:
                i = j
                if values[i] > values[best]:
                    best = i
                frames.append(dict(cur=i, note=f"T={T:.1f}: neighbour state {j}, {why}.",
                                   ds=f"value = {values[i]} · best so far = {values[best]}"))
            T = max(0.05, T * 0.93)
        frames[-1]["result"] = (f"Best value seen: {values[best]} at state {best} "
                                f"(global max = {gmax}). Final state value {values[i]}.")
    return frames


# ───────────────────────── constraint satisfaction ──────────────────────────

def csp_frames(g, ncol=3, mrv=False, fc=False, cap=500):
    nodes = list(g["order"])
    nb = {n: set() for n in nodes}
    for a, b in g["edges"]:
        nb[a].add(b)
        nb[b].add(a)
    cols = list(range(ncol))
    frames = []
    state = dict(backtracks=0, solved=False)
    assign = {}

    def snap():
        return dict(assign)

    def doms_text(doms):
        return " · ".join(f"{n}:{''.join(COLOUR_NAMES[c][0] for c in sorted(doms[n]))}"
                          for n in nodes if n not in assign)

    def rec(doms):
        if len(frames) > cap:
            return False
        if len(assign) == len(nodes):
            state["solved"] = True
            return True
        un = [n for n in nodes if n not in assign]
        if mrv:
            var = min(un, key=lambda n: (len(doms[n]), -len(nb[n] - set(assign)), nodes.index(n)))
            why = f"MRV picks {var} (only {len(doms[var])} colour(s) left)"
        else:
            var = un[0]
            why = f"next variable in fixed order: {var}"
        for c in sorted(doms[var]):
            bad = [m for m in nb[var] if assign.get(m) == c]
            if bad:
                frames.append(dict(cur=var, col=snap(), note=f"{why}. Try {var} = {COLOUR_NAMES[c]}: clashes with {bad[0]} → skip.",
                                   ds=f"backtracks = {state['backtracks']}" + (f" · domains: {doms_text(doms)}" if fc else "")))
                continue
            assign[var] = c
            new = {k: set(v) for k, v in doms.items()}
            dead = None
            if fc:
                for m in nb[var]:
                    if m not in assign and c in new[m]:
                        new[m].discard(c)
                        if not new[m]:
                            dead = m
                            break
            frames.append(dict(cur=var, col=snap(), note=f"{why}. Assign {var} = {COLOUR_NAMES[c]}."
                               + (f" Forward checking: {dead} has NO colour left → backtrack!" if dead else ""),
                               ds=f"backtracks = {state['backtracks']}" + (f" · domains: {doms_text(new)}" if fc else "")))
            if not dead and rec(new):
                return True
            del assign[var]
            state["backtracks"] += 1
            frames.append(dict(cur=var, col=snap(), note=f"BACKTRACK: undo {var} = {COLOUR_NAMES[c]}.",
                               ds=f"backtracks = {state['backtracks']}" + (f" · domains: {doms_text(doms)}" if fc else "")))
        return False

    ok = rec({n: set(cols) for n in nodes})
    if ok:
        frames.append(dict(cur=None, col=snap(), note="All variables assigned and no constraint is broken. SOLVED!",
                           ds=f"backtracks = {state['backtracks']}",
                           result=f"Solved with {ncol} colours · {state['backtracks']} backtrack(s)"))
    else:
        frames.append(dict(cur=None, col={}, note=f"Every option failed. NO solution with {ncol} colours.",
                           ds=f"backtracks = {state['backtracks']}",
                           result=f"No solution with {ncol} colours · {state['backtracks']} backtrack(s)"))
    return frames, dict(solved=ok, backtracks=state["backtracks"])


# ───────────────────────── means–end analysis ───────────────────────────────

def _mea_ops():
    ops = []
    rooms = [1, 2, 3]
    for a in rooms:
        for b in rooms:
            if abs(a - b) == 1:
                ops.append(dict(name=f"Move({a}→{b})", pre=[f"robot_in_{a}"],
                                add=[f"robot_in_{b}"], dele=[f"robot_in_{a}"]))
    for r in rooms:
        ops.append(dict(name=f"Pick(box, room {r})",
                        pre=[f"robot_in_{r}", f"box_in_{r}", "hand_empty"],
                        add=["holding_box"], dele=[f"box_in_{r}", "hand_empty"]))
        ops.append(dict(name=f"Drop(box, room {r})",
                        pre=["holding_box", f"robot_in_{r}"],
                        add=[f"box_in_{r}", "hand_empty"], dele=["holding_box"]))
    return ops


def mea_frames(start=("robot_in_1", "box_in_2", "hand_empty"), goal=("box_in_3",)):
    ops = _mea_ops()
    frames = []
    nice = lambda f: f.replace("_", " ")

    def log(note, indent, typ, state):
        frames.append(dict(cur=None, note=note, indent=indent, type=typ, state=sorted(state)))

    def achieve(fact, state, stack, depth):
        """Return (new_state, plan) or None."""
        if fact in state:
            return state, []
        if fact in stack or depth > 7:
            return None
        cands = [o for o in ops if fact in o["add"]]
        cands.sort(key=lambda o: sum(p not in state for p in o["pre"]))
        mark = len(frames)
        for o in cands:
            del frames[mark:]
            log(f"DIFFERENCE: need “{nice(fact)}”. Operator that reduces it: {o['name']}.", depth, "diff", state)
            s, plan, ok = set(state), [], True
            unmet = [p for p in o["pre"] if p not in s]
            if unmet:
                log(f"{o['name']} cannot be applied yet. Unmet: {', '.join(nice(p) for p in unmet)} → new SUB-GOALS.", depth, "sub", s)
            for p in o["pre"]:
                r = achieve(p, s, stack + [fact], depth + 1)
                if r is None:
                    ok = False
                    break
                s, pl = r
                plan += pl
            if not ok or any(p not in s for p in o["pre"]):
                continue
            s = (s - set(o["dele"])) | set(o["add"])
            plan.append(o["name"])
            log(f"APPLY {o['name']}.", depth, "apply", s)
            return s, plan
        del frames[mark:]
        return None

    state = set(start)
    plan = []
    log("Start state and goal compared.", 0, "start", state)
    for g in goal:
        r = achieve(g, state, [], 0)
        if r is None:
            log("Could not reach the goal.", 0, "fail", state)
            return frames, dict(plan=None)
        state, pl = r
        plan += pl
    log("GOAL REACHED. Plan: " + " → ".join(plan), 0, "goal", state)
    frames[-1]["result"] = "Plan: " + " → ".join(plan)
    return frames, dict(plan=plan)
