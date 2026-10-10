"""
Algorithm Lab: every algorithm from Units I & II that can be shown, live.
Used in two places:
  * the "Algorithm Lab" page (full experiments with controls)
  * the "See it run" panel after answering a question (compact)
"""
import pandas as pd
import streamlit as st

from algos import (TREE, WG, LANDSCAPE10, AUS, WHEEL, COLOUR_NAMES, tree_adj, undirected,
                   search_frames, iddfs_frames, jug_bfs, make_maze, grid_run,
                   make_landscape, hill_frames, csp_frames, mea_frames)
from player import (render_player, tree_spec, wgraph_spec, landscape_spec, csp_spec,
                    grid_spec, trace_spec, jug_spec)


# ───────────────────────── static figures that go WITH a question ───────────

def question_figure(key):
    if key == "tree":
        render_player(tree_spec(static=True, title="The search tree (children are expanded left to right). Start S, goal G."), height=345)
    elif key == "wgraph":
        render_player(wgraph_spec(static=True, title="Weighted graph: edge costs are on the edges, h(n) is under each node. Start S, goal G."), height=320)
    elif key == "landscape10":
        render_player(landscape_spec(LANDSCAPE10, static=True, h=210, peaks=False,
                                     title="Landscape: the value of each state (higher is better)"), height=285)
    elif key == "csp_map":
        render_player(csp_spec(AUS, static=True, assigned={"WA": 0, "NT": 1},
                               title="Map colouring: WA = Red, NT = Green. Other regions are not coloured yet."), height=395)


# ───────────────────────── cached frame builders ────────────────────────────

@st.cache_data(show_spinner=False)
def _tree_frames(algo):
    if algo == "iddfs":
        return iddfs_frames(TREE["children"], "S", "G")
    return search_frames(tree_adj(TREE["children"]), "S", ["G"], algo)


@st.cache_data(show_spinner=False)
def _wg_frames(algo):
    return search_frames(undirected(WG["edges"]), "S", ["G"], algo, h=WG["h"])


@st.cache_data(show_spinner=False)
def _maze(rc, cc, seed, loops):
    return make_maze(rc, cc, seed, loops)


@st.cache_data(show_spinner=False)
def _grid(rc, cc, seed, loops, algo):
    g = _maze(rc, cc, seed, loops)
    fr, stats, s, gl = grid_run(g, algo)
    return fr, stats, s, gl


@st.cache_data(show_spinner=False)
def _hill(values, start, variant, radius, seed):
    return hill_frames(list(values), start, variant, radius, seed)


@st.cache_data(show_spinner=False)
def _csp(which, ncol, mrv, fc):
    return csp_frames(AUS if which == "Australia" else WHEEL, ncol, mrv, fc)


@st.cache_data(show_spinner=False)
def _mea():
    return mea_frames()


@st.cache_data(show_spinner=False)
def _jug():
    return jug_bfs()


def _grid_height(rc, cc):
    R, C = 2 * rc + 1, 2 * cc + 1
    return int(min(700 / C * R, 400)) + 270


# ───────────────────────── "See it run" after a question ────────────────────

def run_lab(key, uid="x"):
    """Compact live demo that matches the question that was just answered."""
    if key in ("bfs_tree", "dfs_tree", "iddfs_tree"):
        algo = key.split("_")[0]
        fr, st_ = _tree_frames(algo)
        names = {"bfs": "BFS (queue)", "dfs": "DFS (stack)", "iddfs": "Iterative deepening"}
        render_player(tree_spec(fr, title=f"{names[algo]} on the tree, press Play"), height=575)
    elif key in ("greedy_w", "astar_w"):
        algo = key.split("_")[0]
        fr, st_ = _wg_frames(algo)
        render_player(wgraph_spec(fr, title=("Greedy best-first" if algo == "greedy" else "A*") + " on the weighted graph, press Play"), height=585)
    elif key == "hill":
        fr = _hill(tuple(LANDSCAPE10), 1, "steepest", 1, 1)
        render_player(landscape_spec(LANDSCAPE10, fr, title="Steepest-ascent hill climbing from state 1", h=230), height=520)
    elif key == "csp":
        fr, st_ = _csp("Australia", 3, False, False)
        render_player(csp_spec(AUS, fr, title="Backtracking colouring of the map (3 colours)"), height=600)
    elif key == "mea":
        fr, st_ = _mea()
        render_player(trace_spec(fr, title="Means–end analysis: difference → operator → sub-goals"), height=560)
    elif key == "jug":
        fr, st_, pos, te, goals = _jug()
        render_player(jug_spec(fr, pos, te, goals, title="BFS over the water-jug state space (states shown as x,y)"), height=620)
    elif key == "grid":
        algo = st.radio("Algorithm", ["A*", "Greedy", "BFS", "DFS"], horizontal=True, key=f"labgrid_{uid}")
        a = {"A*": "astar", "Greedy": "greedy", "BFS": "bfs", "DFS": "dfs"}[algo]
        fr, stats, s, gl = _grid(5, 9, 4, 6, a)
        g = _maze(5, 9, 4, 6)
        render_player(grid_spec(g, fr, s, gl, title=f"{algo} on a small maze, press Play"), height=_grid_height(5, 9))


# ───────────────────────── the full Algorithm Lab page ──────────────────────

EXPERIMENTS = [
    "🏁 Maze race: BFS vs DFS vs Greedy vs A*",
    "🌳 BFS, DFS and Iterative Deepening on a tree",
    "🧭 Greedy best-first vs A* (heuristic search)",
    "🫗 Water-jug state space (state space search)",
    "⛰️ Hill climbing and its variations",
    "🗺️ Map colouring (CSP: backtracking, MRV, forward checking)",
    "🤖 Means–end analysis (robot and box)",
]


def lab_view():
    st.subheader("🔬 Algorithm Lab")
    st.caption("Play with the algorithms from Units I & II. Press Play, drag the slider, or step one move at a time.")
    exp = st.selectbox("Choose an experiment", EXPERIMENTS, key="lab_exp")

    if exp == EXPERIMENTS[0]:
        c1, c2, c3, c4 = st.columns([1.3, 1, 1, 1])
        algo_name = c1.radio("Algorithm", ["BFS", "DFS", "Greedy (Manhattan)", "A* (Manhattan)"], key="lab_alg")
        size = c2.selectbox("Maze size", ["Small", "Medium", "Large"], index=1, key="lab_size")
        loops = c3.slider("Extra openings (loops)", 0, 30, 12, key="lab_loops",
                          help="More openings = more than one route, so the algorithms behave differently.")
        if "lab_seed" not in st.session_state:
            st.session_state.lab_seed = 7
        if c4.button("🎲 New maze", key="lab_new"):
            st.session_state.lab_seed += 1
        rc, cc = {"Small": (5, 9), "Medium": (8, 14), "Large": (11, 20)}[size]
        a = {"BFS": "bfs", "DFS": "dfs", "Greedy (Manhattan)": "greedy", "A* (Manhattan)": "astar"}[algo_name]
        seed = st.session_state.lab_seed
        g = _maze(rc, cc, seed, loops)
        fr, stats, s, gl = _grid(rc, cc, seed, loops, a)
        render_player(grid_spec(g, fr, s, gl, title=f"{algo_name} on a {size.lower()} maze (start S top-left, goal G bottom-right)"),
                      height=_grid_height(rc, cc))
        rows = []
        for nm, k in [("BFS", "bfs"), ("DFS", "dfs"), ("Greedy (Manhattan)", "greedy"), ("A* (Manhattan)", "astar")]:
            _, sts, _, _ = _grid(rc, cc, seed, loops, k)
            rows.append({"Algorithm": nm, "Nodes expanded": sts["expanded"], "Path length (steps)": len(sts["path"]) - 1})
        df = pd.DataFrame(rows)
        best = df["Path length (steps)"].min()
        df["Optimal path?"] = df["Path length (steps)"].apply(lambda x: "✅ yes" if x == best else "❌ longer")
        st.markdown("**Race results on this maze**")
        l, r = st.columns([1.2, 1])
        l.dataframe(df, hide_index=True, width="stretch")
        r.bar_chart(df.set_index("Algorithm")["Nodes expanded"], height=190)
        st.info("**What to notice:** BFS and A* both find a shortest path, but A* expands fewer nodes because the Manhattan "
                "heuristic points it at the goal. DFS expands the fewest in some mazes but its path is usually much longer. "
                "Greedy is fast but not always optimal.")

    elif exp == EXPERIMENTS[1]:
        algo = st.radio("Algorithm", ["BFS (queue)", "DFS (stack)", "Iterative deepening"], horizontal=True, key="lab_tree")
        a = {"BFS (queue)": "bfs", "DFS (stack)": "dfs", "Iterative deepening": "iddfs"}[algo]
        fr, stats = _tree_frames(a)
        render_player(tree_spec(fr, title=f"{algo} on the tree: goal G is at depth 3"), height=575)
        st.info({"bfs": "**BFS** goes level by level using a FIFO queue. It finds the shallowest goal but must remember a whole level.",
                 "dfs": "**DFS** dives down one branch using a LIFO stack. It uses little memory but may take a long way round.",
                 "iddfs": "**Iterative deepening** repeats depth-limited DFS with limit 0, 1, 2, 3. It gets BFS's shallowest-goal result "
                          "with DFS's small memory. The repeated shallow levels cost little."}[a])

    elif exp == EXPERIMENTS[2]:
        algo = st.radio("Algorithm", ["Greedy best-first (f = h)", "A* (f = g + h)"], horizontal=True, key="lab_wg")
        a = "greedy" if algo.startswith("Greedy") else "astar"
        fr, stats = _wg_frames(a)
        render_player(wgraph_spec(fr, title=f"{algo} from S to G"), height=585)
        st.info("**Greedy** only looks at h(n), so it runs straight at the goal and ends with cost 13. **A\\*** adds the cost already "
                "travelled, g(n), notices the cheaper route through B, and returns cost 8 (the optimum).")

    elif exp == EXPERIMENTS[3]:
        fr, stats, pos, te, goals = _jug()
        render_player(jug_spec(fr, pos, te, goals, title="BFS over the water-jug state space: each node is (litres in 4L jug, litres in 3L jug)"), height=620)
        st.info("Each **state** is a pair (x, y). Each **rule** (fill, empty, pour) is a move between states. BFS finds the fewest moves "
                "to any state with 2 litres in the 4-litre jug: **6 moves**. Red rings are goal states. Only BFS-tree edges are drawn, to keep the picture clear.")

    elif exp == EXPERIMENTS[4]:
        c1, c2, c3 = st.columns([1.4, 1, 1])
        var = c1.selectbox("Variation", ["Simple (first better neighbour)", "Steepest-ascent", "Stochastic (random uphill)",
                                         "First-choice (random neighbour)", "Random-restart", "Simulated annealing"], index=1, key="lab_hv")
        vkey = {"Simple (first better neighbour)": "simple", "Steepest-ascent": "steepest", "Stochastic (random uphill)": "stochastic",
                "First-choice (random neighbour)": "first", "Random-restart": "restart", "Simulated annealing": "anneal"}[var]
        vals = make_landscape(40)
        start = c2.slider("Start state", 0, 39, 6, key="lab_hs")
        radius = c3.slider("Neighbourhood size", 1, 3, 2, key="lab_hr", help="How many states to the left/right count as neighbours.")
        if "hill_seed" not in st.session_state:
            st.session_state.hill_seed = 1
        if st.button("🎲 Different random run", key="lab_hnew"):
            st.session_state.hill_seed += 1
        fr = _hill(tuple(vals), start, vkey, radius, st.session_state.hill_seed)
        render_player(landscape_spec(vals, fr, title=f"{var}: the AI climbs the landscape", h=260), height=545)
        st.info("Try **steepest-ascent** from different start states: it gets stuck on a local maximum or on the flat plateau. "
                "**Random-restart** and **simulated annealing** can escape because they try new starts or sometimes accept a worse move.")

    elif exp == EXPERIMENTS[5]:
        c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1])
        which = c1.selectbox("Map", ["Australia", "Wheel (needs 4 colours)"], key="lab_cm")
        ncol = c2.selectbox("Colours", [2, 3, 4], index=1, key="lab_cn")
        mrv = c3.checkbox("MRV heuristic", key="lab_mrv")
        fc = c4.checkbox("Forward checking", key="lab_fc")
        w = "Australia" if which == "Australia" else "Wheel"
        fr, stats = _csp(w, ncol, mrv, fc)
        g = AUS if w == "Australia" else WHEEL
        render_player(csp_spec(g, fr, title=f"Backtracking search, {ncol} colours" + (" + MRV" if mrv else "") + (" + forward checking" if fc else ""), ncol=ncol), height=600)
        st.info("Variables = regions, domain = colours, constraint = neighbours must differ. Try **2 colours** on Australia (impossible), "
                "or **3 colours** on the Wheel (impossible, so lots of backtracking). Switch on MRV and forward checking to see failures found sooner.")

    else:
        fr, stats = _mea()
        render_player(trace_spec(fr, title="Means–end analysis: robot in Room 1, box in Room 2, goal = box in Room 3"), height=560)
        st.info("MEA finds the **difference** between the current and goal states, picks an **operator** that reduces it, and turns any "
                "unmet preconditions into **sub-goals**. Here: to Drop the box in Room 3 you must hold it and be in Room 3, "
                "so Pick (needs the robot in Room 2) and Move become sub-goals.")


# ───────────────────────── boss maze (end of every run) ─────────────────────

BOSS_MAZE = (8, 14, 3, 14)          # rows, cols, seed, loops -> BFS 44 steps, DFS 92, Greedy 48, A* 44
BOSS_ALGOS = {"BFS": "bfs", "DFS": "dfs", "Greedy (Manhattan)": "greedy", "A* (Manhattan)": "astar"}


def boss_results():
    rc, cc, seed, loops = BOSS_MAZE
    res = {}
    for name, k in BOSS_ALGOS.items():
        _, sts, _, _ = _grid(rc, cc, seed, loops, k)
        res[name] = dict(expanded=sts["expanded"], steps=len(sts["path"]) - 1)
    return res


def boss_points(name, res):
    """+5 for reaching the exit, +10 more for a shortest path, +5 more if it also explored fewer cells than BFS."""
    best = min(r["steps"] for r in res.values())
    r = res[name]
    pts = 5
    if r["steps"] == best:
        pts += 10
        if r["expanded"] < res["BFS"]["expanded"]:
            pts += 5
    return pts


def boss_show(name):
    rc, cc, seed, loops = BOSS_MAZE
    g = _maze(rc, cc, seed, loops)
    fr, stats, s, gl = _grid(rc, cc, seed, loops, BOSS_ALGOS[name])
    render_player(grid_spec(g, fr, s, gl, title=f"{name}: Glitch's boss maze, press Play"), height=_grid_height(rc, cc))
