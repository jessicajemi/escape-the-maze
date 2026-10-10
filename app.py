"""
🧠 Escape the Maze: AI Edition
DSC401-6 Artificial Intelligence · Units I & II interactive quiz game

Run:  streamlit run app.py
"""
import copy
import csv
import io
import datetime as dt
import random
import re
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from questions import QUESTIONS, ROOMS, KIND_LABEL, SYLLABUS_TOPICS
from maze import render_maze
from lab import lab_view, question_figure, run_lab, boss_results, boss_points, boss_show, BOSS_ALGOS

AUTHOR = "Jessica"                      # change this to your name / roll number
COURSE = "DSC401-6 · Artificial Intelligence · Units I & II"
BASE = Path(__file__).parent
BOARD = BASE / "leaderboard.csv"
BOARD_COLS = ["name", "mode", "level", "score", "accuracy", "correct", "answered", "result", "title", "date"]

st.set_page_config(page_title="Escape the Maze: AI Edition", page_icon="🧠", layout="wide")

# ───────────────────────────── game settings ─────────────────────────────

LEVELS = {
    "Easy":   dict(gap=6, time=50, ll=dict(prune=3, hint=4, skip=2, time=3), pool=("Easy", "Medium")),
    "Medium": dict(gap=5, time=40, ll=dict(prune=2, hint=3, skip=1, time=2), pool=("Easy", "Medium", "Hard")),
    "Hard":   dict(gap=4, time=30, ll=dict(prune=1, hint=2, skip=1, time=1), pool=("Medium", "Hard")),
}
MODES = {
    "Full Escape":  (75, "All 75 questions, room by room. The real thing."),
    "Quick Run":    (15, "15 random questions across all rooms. Good for a fast demo."),
    "Adaptive Run": (20, "20 questions. Difficulty goes up when you do well and down when you struggle."),
    "Viva Mode":    (10, "10 random questions, no timer, no Glitch. Practise for the class viva."),
}
DIFF_POINTS = {"Easy": 10, "Medium": 15, "Hard": 20}
KIND_EXTRA_TIME = {"tf": -10, "mcq": 0, "fib": 5, "ar": 10, "scenario": 15, "match": 20, "problem": 20}
ADAPTIVE_BASE = {"Easy": 45, "Medium": 40, "Hard": 30}
DIFF_ORDER = ["Easy", "Medium", "Hard"]
PLAY, LAB, BOARD_V, BANK = "🎮 Play", "🔬 Algorithm Lab", "🏆 Leaderboard", "📖 Question Bank"

ss = st.session_state
ss.setdefault("g", None)
ss.setdefault("view", PLAY)

st.markdown("""
<style>
.block-container{padding-top:2.2rem;max-width:1250px}
.chip{display:inline-block;background:#111c33;border:1px solid #243352;border-radius:999px;padding:3px 12px;margin:2px 6px 2px 0;font-size:.9rem;color:#e2e8f0}
.chip b{color:#fbbf24}
.badge{display:inline-block;border-radius:6px;padding:1px 9px;margin:0 6px 6px 0;font-size:.78rem;font-weight:600;background:#1e293b;color:#cbd5e1;border:1px solid #334155}
.badge.Easy{background:#052e1a;color:#4ade80;border-color:#14532d}
.badge.Medium{background:#3a2a05;color:#fbbf24;border-color:#6b4e0a}
.badge.Hard{background:#3b0d0d;color:#f87171;border-color:#7f1d1d}
.badge.rw{background:#0c2a3d;color:#7dd3fc;border-color:#164e63}
.hero{font-size:2.1rem;font-weight:800;margin:0}
.sub{color:#94a3b8;margin:0 0 .6rem}
[data-testid="stColumn"] .stButton button{padding:.35rem .4rem}
[data-testid="stColumn"] .stButton button p{font-size:.78rem;white-space:nowrap}
</style>""", unsafe_allow_html=True)


# ───────────────────────────── helpers ─────────────────────────────

def has_bug(g):
    return g["mode"] != "Viva Mode"


def cur_q(g):
    return g["qs"][g["idx"]]


def prep(q):
    q = copy.deepcopy(q)
    if q["kind"] == "match":
        q["rights"] = [b for _, b in q["pairs"]]
        random.shuffle(q["rights"])
    elif q.get("shuffle") and "options" in q:
        random.shuffle(q["options"])
    return q


def build_questions(mode, level):
    pool_diffs = LEVELS[level]["pool"]
    if mode == "Full Escape":
        out = []
        for r in sorted(ROOMS):
            qs = [q for q in QUESTIONS if q["room"] == r]
            random.shuffle(qs)
            out += qs
        return [prep(q) for q in out]
    pool = [q for q in QUESTIONS if q["diff"] in pool_diffs]
    if mode == "Quick Run":
        chosen = []
        for r in sorted(ROOMS):
            rq = [q for q in pool if q["room"] == r]
            chosen += random.sample(rq, min(2, len(rq)))
        rest = [q for q in pool if q not in chosen]
        random.shuffle(rest)
        chosen += rest[:15 - len(chosen)]
        random.shuffle(chosen)
        return [prep(q) for q in chosen[:15]]
    if mode == "Viva Mode":
        return [prep(q) for q in random.sample(pool, 10)]
    return []   # adaptive builds one question at a time


def adaptive_next(g):
    order = [g["alevel"]] + [d for d in DIFF_ORDER if d != g["alevel"]]
    for d in order:
        if g["apool"][d]:
            return prep(g["apool"][d].pop())
    return None


def time_limit(g, q):
    base = ADAPTIVE_BASE[q["diff"]] if g["mode"] == "Adaptive Run" else LEVELS[g["level"]]["time"]
    return max(20, base + KIND_EXTRA_TIME[q["kind"]])


def start_question(g):
    q = cur_q(g)
    g["q_used"] = dict(prune=False, hint=False, time=0)
    g["pruned"], g["reveal"], g["fib_hint"], g["warn"] = [], None, "", False
    g["q_start"] = time.time()
    g["limit"] = time_limit(g, q)
    g["deadline"] = g["q_start"] + g["limit"]
    g["pause_t"] = None
    g["phase"] = "ask"


def new_game():
    name = (ss.get("p_name") or "").strip() or "Guest"
    mode, level = ss.p_mode, ss.p_level
    L = LEVELS[level]
    g = dict(name=name, mode=mode, level=level, N=MODES[mode][0], idx=0, score=0, streak=0, best_streak=0,
             gap=L["gap"], gap0=L["gap"], gapcap=L["gap"] + 1, correct=0, wrong=0, skipped=0, timeouts=0,
             ll=dict(L["ll"]), log=[], saved=False, caught=False, msg="", last=None,
             interval=11 if mode == "Full Escape" else 5, t0=time.time(), seen_checkpoint=0)
    if mode == "Adaptive Run":
        g["apool"] = {d: [q for q in QUESTIONS if q["diff"] == d] for d in DIFF_ORDER}
        for d in DIFF_ORDER:
            random.shuffle(g["apool"][d])
        g["alevel"], g["astreak"] = "Easy", 0
        g["qs"] = [adaptive_next(g)]
    else:
        g["qs"] = build_questions(mode, level)
    ss.g = g
    ss["boss_pick"] = None
    start_question(g)


def norm(s):
    s = (s or "").lower().strip()
    s = re.sub(r"[\"'“”‘’.,;:!?()]", "", s)
    return re.sub(r"\s+", " ", s)


def user_answer(g, q):
    i = g["idx"]
    if q["kind"] == "fib":
        return (ss.get(f"fib_{i}") or "").strip()
    if q["kind"] == "match":
        return "; ".join(f"{a} → {ss.get(f'm_{i}_{k}') or '—'}" for k, (a, _) in enumerate(q["pairs"]))
    return ss.get(f"ans_{i}") or ""


def is_correct(g, q):
    i = g["idx"]
    if q["kind"] == "fib":
        return norm(ss.get(f"fib_{i}")) in {norm(a) for a in q["accepted"]}
    if q["kind"] == "match":
        return all(ss.get(f"m_{i}_{k}") == b for k, (a, b) in enumerate(q["pairs"]))
    return ss.get(f"ans_{i}") == q["answer"]


def answered_something(g, q):
    i = g["idx"]
    if q["kind"] == "fib":
        return bool((ss.get(f"fib_{i}") or "").strip())
    if q["kind"] == "match":
        return all(ss.get(f"m_{i}_{k}") for k in range(len(q["pairs"])))
    return bool(ss.get(f"ans_{i}"))


def finalize(g, q, result):
    """result: correct | wrong | timeout | skipped"""
    elapsed = time.time() - g["q_start"]
    pts, parts, msg = 0, [], ""
    if result == "correct":
        pts = DIFF_POINTS[q["diff"]]
        parts.append(f"{q['diff']} question: {pts}")
        if has_bug(g):
            frac = elapsed / g["limit"]
            if frac <= 0.4:
                pts += 5; parts.append("speed bonus: +5")
            elif frac <= 0.7:
                pts += 2; parts.append("speed bonus: +2")
        cost = (5 if g["q_used"]["prune"] else 0) + (3 if g["q_used"]["hint"] else 0) + 2 * g["q_used"]["time"]
        if cost:
            pts = max(2, pts - cost); parts.append(f"lifelines: −{cost}")
        g["streak"] += 1
        g["best_streak"] = max(g["best_streak"], g["streak"])
        mult = 1.5 if g["streak"] >= 5 else 1.2 if g["streak"] >= 3 else 1.0
        if mult > 1:
            pts = int(round(pts * mult)); parts.append(f"streak ×{mult}")
        g["correct"] += 1
        if has_bug(g) and g["streak"] % 3 == 0 and g["gap"] < g["gapcap"]:
            g["gap"] += 1; msg = "🔥 3 in a row! You gain a step on Glitch."
    elif result in ("wrong", "timeout"):
        g["wrong"] += 1
        g["streak"] = 0
        if result == "timeout":
            g["timeouts"] += 1
        if has_bug(g):
            g["gap"] -= 1
            msg = "🐛 Glitch moves closer!"
            if g["gap"] <= 0:
                g["caught"] = True
                msg = "💥 Glitch caught you!"
    else:
        g["skipped"] += 1
        msg = "↩️ Backtracked: question skipped, no penalty."
    g["score"] += pts
    g["log"].append(dict(id=q["id"], room=q["room"], topic=q["topic"], kind=q["kind"], diff=q["diff"], result=result,
                         pts=pts, secs=round(elapsed, 1), user=user_answer(g, q), answer=q["answer"],
                         why=q["why"], q=q["q"]))
    g["last"] = dict(result=result, pts=pts, parts=parts, msg=msg)
    # adaptive: choose the next question now
    if g["mode"] == "Adaptive Run" and result in ("correct", "wrong", "timeout") and len(g["qs"]) < g["N"]:
        if result == "correct":
            g["astreak"] += 1
            if g["astreak"] >= 2:
                g["alevel"] = DIFF_ORDER[min(2, DIFF_ORDER.index(g["alevel"]) + 1)]
                g["astreak"] = 0
        else:
            g["alevel"] = DIFF_ORDER[max(0, DIFF_ORDER.index(g["alevel"]) - 1)]
            g["astreak"] = 0
    if g["mode"] == "Adaptive Run" and len(g["qs"]) < g["N"] and not g["caught"]:
        nq = adaptive_next(g)
        if nq:
            g["qs"].append(nq)
    g["phase"] = "feedback"


# ── button callbacks ──
def cb_start():
    new_game()


def cb_submit():
    g = ss.g
    q = cur_q(g)
    if g["phase"] != "ask":
        return
    if not answered_something(g, q):
        g["warn"] = True
        return
    finalize(g, q, "correct" if is_correct(g, q) else "wrong")


def cb_timeout():
    g = ss.g
    if g and g["phase"] == "ask":
        finalize(g, cur_q(g), "timeout")


def cb_next():
    g = ss.g
    if g["caught"] or g["idx"] + 1 >= min(g["N"], len(g["qs"])):
        if not g["caught"] and has_bug(g) and not g.get("boss"):
            g["phase"] = "boss"
            return
        end_game(g)
        return
    g["idx"] += 1
    g["msg"] = ""
    if has_bug(g) and g["idx"] % g["interval"] == 0:
        g["gap"] = g["gap0"]
        g["msg"] = "🚩 Checkpoint reached! Glitch is pushed back to the start distance."
    start_question(g)


def cb_prune():
    g = ss.g
    q = cur_q(g)
    if g["ll"]["prune"] <= 0 or g["q_used"]["prune"] or q["kind"] == "tf":
        return
    g["ll"]["prune"] -= 1
    g["q_used"]["prune"] = True
    i = g["idx"]
    if q["kind"] in ("mcq", "scenario", "problem", "ar"):
        wrong = [o for o in q["options"] if o != q["answer"]]
        g["pruned"] = random.sample(wrong, 2)
        if ss.get(f"ans_{i}") in g["pruned"]:
            ss[f"ans_{i}"] = None
    elif q["kind"] == "fib":
        a = q["answer"]
        g["fib_hint"] = f"Starts with “{a[0].upper()}” and has {len(a.replace(' ', ''))} letters."
    elif q["kind"] == "match":
        k = random.randrange(len(q["pairs"]))
        ss[f"m_{i}_{k}"] = q["pairs"][k][1]
        g["reveal"] = k


def cb_hint():
    g = ss.g
    if g["ll"]["hint"] > 0 and not g["q_used"]["hint"]:
        g["ll"]["hint"] -= 1
        g["q_used"]["hint"] = True


def cb_skip():
    g = ss.g
    if g["ll"]["skip"] > 0 and g["phase"] == "ask":
        g["ll"]["skip"] -= 1
        finalize(g, cur_q(g), "skipped")


def cb_time():
    g = ss.g
    if g["ll"]["time"] > 0 and g["phase"] == "ask" and has_bug(g):
        g["ll"]["time"] -= 1
        g["q_used"]["time"] += 1
        g["deadline"] += 15
        g["limit"] += 15


def cb_boss_run():
    g = ss.g
    name = ss.get("boss_pick")
    if not name or g.get("boss"):
        return
    res = boss_results()
    pts = boss_points(name, res)
    g["boss"] = dict(algo=name, pts=pts, res=res)
    g["score"] += pts


def cb_boss_finish():
    end_game(ss.g)


def rank_title(acc, caught):
    if acc >= 90: t = "🥇 Optimal Escape (A*)"
    elif acc >= 75: t = "🥈 Smart Heuristic Hero"
    elif acc >= 60: t = "🥉 Greedy but Lucky"
    elif acc >= 40: t = "⛰️ Stuck in a Local Maximum"
    else: t = "🔦 Lost in the Blind Corridors"
    return t + (" (caught by Glitch)" if caught else "")


def accuracy(g):
    n = g["correct"] + g["wrong"]
    return round(100 * g["correct"] / n, 1) if n else 0.0


def end_game(g):
    g["phase"] = "end"
    g["t_end"] = time.time()
    g["acc"] = accuracy(g)
    g["title"] = rank_title(g["acc"], g["caught"])
    if g["mode"] != "Viva Mode" and not g["saved"]:
        save_score(g)
        g["saved"] = True


def save_score(g):
    try:
        new = not BOARD.exists()
        with open(BOARD, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new:
                w.writerow(BOARD_COLS)
            w.writerow([g["name"], g["mode"], g["level"], g["score"], g["acc"], g["correct"],
                        g["correct"] + g["wrong"], "Caught" if g["caught"] else "Escaped", g["title"],
                        dt.datetime.now().strftime("%Y-%m-%d %H:%M")])
    except OSError:
        pass


def load_board():
    if not BOARD.exists():
        return pd.DataFrame(columns=BOARD_COLS)
    try:
        return pd.read_csv(BOARD)
    except Exception:
        return pd.DataFrame(columns=BOARD_COLS)


# ───────────────────────────── timer (live, every second) ─────────────────────────────

@st.fragment(run_every=1)
def timer_box():
    g = ss.get("g")
    if not g or g["phase"] != "ask" or not has_bug(g) or ss.get("view") != PLAY:
        return
    left = g["deadline"] - time.time()
    if left <= 0:
        cb_timeout()
        st.rerun()
        return
    st.progress(max(0.0, min(1.0, left / g["limit"])), text=f"⏱️ {int(left) + 1} s left")


# ───────────────────────────── views ─────────────────────────────

def hud(g, q):
    bug = ""
    if has_bug(g):
        bug = f'<span class="chip">🐛 Glitch distance <b>{"🟩" * max(0, g["gap"])}{"⬜" * max(0, g["gapcap"] - max(0, g["gap"]))}</b></span>'
    streak = f' <span style="color:#94a3b8">(×{1.5 if g["streak"] >= 5 else 1.2 if g["streak"] >= 3 else 1})</span>' if g["streak"] >= 3 else ""
    rname, remoji = ROOMS[q["room"]]
    lvl = f'<span class="chip">🎚️ Level <b>{g["alevel"]}</b></span>' if g["mode"] == "Adaptive Run" else ""
    st.markdown(
        f'<span class="chip">🏆 Score <b>{g["score"]}</b></span>'
        f'<span class="chip">🔥 Streak <b>{g["streak"]}</b>{streak}</span>{bug}{lvl}'
        f'<span class="chip">{remoji} Room {q["room"]}: <b>{rname}</b></span>', unsafe_allow_html=True)


def board_html(g, feedback):
    n_done = g["idx"] + (1 if feedback else 0)
    p_frac = 0.12 + 0.88 * n_done / g["N"]
    doors = [0.12 + 0.88 * (k * g["interval"]) / g["N"] for k in range(1, g["N"] // g["interval"] + 1) if k * g["interval"] < g["N"]]
    return render_maze(p_frac, g["gap"], doors, caught=g["caught"])


def start_view():
    st.markdown(f'<p class="hero">🧠 Escape the Maze: AI Edition</p><p class="sub">{COURSE} · built by {AUTHOR}</p>', unsafe_allow_html=True)
    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("#### The story")
        st.write("You are an AI agent trapped in a lab maze. **Glitch** is chasing you. Every correct answer keeps you ahead. "
                 "Every wrong answer or timeout lets Glitch get closer. Reach each 🚩 checkpoint to push Glitch back, "
                 "and escape through the 🚪 to win.")
        st.markdown("#### The 7 rooms")
        for r, (n, e) in ROOMS.items():
            cnt = sum(1 for q in QUESTIONS if q["room"] == r)
            topics = {1: "Foundations & applications of AI, Turing Test", 2: "Rational / intelligent agents, agents & environments, good behaviour, nature of environments",
                      3: "Problems & problem spaces, state space search, production systems, problem characteristics, issues in search design",
                      4: "BFS, DFS, iterative deepening", 5: "Heuristic search, best-first, hill climbing and variations",
                      6: "Constraint satisfaction problems, means–end analysis", 7: "Mixed boss questions on A*, greedy, IDDFS and heuristics, then the boss maze where you pick the algorithm"}[r]
            st.markdown(f"{e} **Room {r}: {n}** ({cnt} questions): {topics}")
    with right:
        with st.container(border=True):
            st.markdown("#### Start a run")
            st.text_input("Your name (for the leaderboard)", key="p_name", placeholder="e.g. Jessica")
            st.selectbox("Mode", list(MODES), key="p_mode", index=1,
                         format_func=lambda m: f"{m} ({MODES[m][0]} questions)")
            st.caption(MODES[ss.get("p_mode", "Quick Run")][1])
            st.select_slider("Difficulty level", ["Easy", "Medium", "Hard"], value="Medium", key="p_level",
                             help="Changes the timer, how far Glitch starts behind you, and how many lifelines you get.")
            L = LEVELS[ss.p_level]
            ll = L["ll"]
            st.caption(f"⏱️ {L['time']} s base timer · 🐛 Glitch starts {L['gap']} steps behind · lifelines: ✂️{ll['prune']} 💡{ll['hint']} ↩️{ll['skip']} ⏳{ll['time']}")
            st.button("🚀 Start the escape", type="primary", on_click=cb_start, use_container_width=True)
        with st.expander("Lifelines and scoring"):
            st.markdown(
                "- ✂️ **Pruning**: removes 2 wrong options (−5 points if you then get it right)\n"
                "- 💡 **Heuristic**: shows a hint (−3 points)\n"
                "- ↩️ **Backtrack**: skip the question, no penalty, no points\n"
                "- ⏳ **Iterative Deepening**: +15 seconds (−2 points)\n"
                "- Points: Easy 10 · Medium 15 · Hard 20, plus a speed bonus (+5 / +2), times a streak multiplier (×1.2 at 3, ×1.5 at 5).\n"
                "- 3 correct in a row gives you one step on Glitch.")


def ask_view(g):
    q = cur_q(g)
    i = g["idx"]
    hud(g, q)
    st.progress(i / g["N"], text=f"Question {i + 1} of {g['N']}")
    if g["msg"]:
        st.success(g["msg"])
    left, right = st.columns([1, 1.05], gap="large")
    with left:
        if has_bug(g):
            st.markdown(board_html(g, False), unsafe_allow_html=True)
            if g["gap"] <= 1:
                st.error("🐛 Glitch is right behind you! One more mistake and you are caught.")
            else:
                st.caption("🤖 you · 🐛 Glitch (the red path is already eaten) · 🚩 checkpoints · 🚪 exit")
        else:
            st.info("🎓 **Viva Mode**: no timer and no Glitch. Answer, read the explanation, and be ready to explain it in your own words.")
    with right:
        timer_box()
        with st.container(border=True):
            badges = (f'<span class="badge">{ROOMS[q["room"]][1]} {q["topic"]}</span>'
                      f'<span class="badge">{KIND_LABEL[q["kind"]]}</span>'
                      f'<span class="badge {q["diff"]}">{q["diff"]}</span>'
                      + ('<span class="badge rw">🌍 real-world</span>' if q["rw"] else "")
                      + ('<span class="badge rw">🔎 search / state space</span>' if q["search"] else ""))
            st.markdown(badges, unsafe_allow_html=True)
            st.markdown(f"**{q['q']}**" if q["kind"] not in ("ar",) else q["q"])
            if q["fig"]:
                question_figure(q["fig"])
            # ---- answer widgets ----
            if q["kind"] == "fib":
                st.text_input("Type your answer", key=f"fib_{i}", placeholder="your answer")
                if g["fib_hint"]:
                    st.info("✂️ " + g["fib_hint"])
            elif q["kind"] == "match":
                st.caption("Pick the matching item for each row.")
                for k, (a, b) in enumerate(q["pairs"]):
                    st.selectbox(a, q["rights"], index=None, placeholder="Choose...", key=f"m_{i}_{k}",
                                 disabled=(g["reveal"] == k))
            else:
                opts = [o for o in q["options"] if o not in g["pruned"]]
                st.radio("Your answer", opts, index=None, key=f"ans_{i}", label_visibility="collapsed")
            if g["q_used"]["hint"]:
                st.info("💡 " + q["hint"])
            if g["warn"]:
                st.warning("Choose or type an answer first.")
        # ---- lifelines ----
        L = g["ll"]
        c = st.columns(4)
        c[0].button(f"✂️ Pruning ({L['prune']})", on_click=cb_prune, key="b_prune",
                    disabled=(L["prune"] <= 0 or g["q_used"]["prune"] or q["kind"] == "tf"),
                    help="Removes two wrong options (or reveals a letter / a matching pair). −5 points if you still get it right.",
                    use_container_width=True)
        c[1].button(f"💡 Heuristic ({L['hint']})", on_click=cb_hint, key="b_hint",
                    disabled=(L["hint"] <= 0 or g["q_used"]["hint"]), help="Shows a hint. −3 points.",
                    use_container_width=True)
        c[2].button(f"↩️ Backtrack ({L['skip']})", on_click=cb_skip, key="b_skip", disabled=(L["skip"] <= 0),
                    help="Skip this question: no points, no penalty.", use_container_width=True)
        c[3].button(f"⏳ Iter. Deep. ({L['time']})", on_click=cb_time, key="b_time",
                    disabled=(L["time"] <= 0 or not has_bug(g)), help="+15 seconds. −2 points.",
                    use_container_width=True)
        st.button("🔒 Lock in answer", type="primary", on_click=cb_submit, key="b_submit", use_container_width=True)


def feedback_view(g):
    q = cur_q(g)
    last = g["last"]
    hud(g, q)
    st.progress((g["idx"] + 1) / g["N"], text=f"Question {g['idx'] + 1} of {g['N']}")
    left, right = st.columns([1, 1.05], gap="large")
    with left:
        if has_bug(g):
            st.markdown(board_html(g, True), unsafe_allow_html=True)
            if last["msg"]:
                (st.error if g["caught"] or "closer" in last["msg"] else st.success)(last["msg"])
    with right:
        res = last["result"]
        if res == "correct":
            st.success(f"✅ Correct! +{last['pts']} points" + (f"  ({', '.join(last['parts'])})" if last["parts"] else ""))
        elif res == "skipped":
            st.info("↩️ Skipped with Backtrack. Here is the answer so you still learn it.")
        else:
            st.error("⏰ Time is up!" if res == "timeout" else "❌ Not quite.")
        if res != "correct":
            st.markdown(f"**Correct answer:** {q['answer']}")
        st.markdown(f"**Why:** {q['why']}")
        if q["lab"]:
            with st.expander("🔬 See it run (live visualiser)", expanded=(q["kind"] == "problem")):
                run_lab(q["lab"], uid=g["idx"])
        done = g["caught"] or g["idx"] + 1 >= min(g["N"], len(g["qs"]))
        st.button(("👾 Face the boss maze ➜" if (has_bug(g) and not g["caught"]) else "🏁 See my result") if done else "Next question ➜",
                  type="primary", on_click=cb_next,
                  key="b_next", use_container_width=True)


def radar(by_room):
    labels = [f"R{r}\n{ROOMS[r][0]}" for r in by_room]
    vals = [by_room[r] for r in by_room]
    ang = np.linspace(0, 2 * np.pi, len(vals), endpoint=False).tolist()
    vals2, ang2 = vals + vals[:1], ang + ang[:1]
    fig = plt.figure(figsize=(4.6, 4.2), facecolor="none")
    ax = fig.add_subplot(111, polar=True)
    ax.set_facecolor("none")
    ax.plot(ang2, vals2, color="#f59e0b", linewidth=2)
    ax.fill(ang2, vals2, color="#f59e0b", alpha=0.25)
    ax.set_xticks(ang)
    ax.set_xticklabels(labels, color="#e2e8f0", fontsize=8)
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["25", "50", "75", "100"], color="#94a3b8", fontsize=7)
    ax.grid(color="#334155")
    ax.spines["polar"].set_color("#334155")
    return fig


def end_view(g):
    escaped = not g["caught"]
    if g["mode"] == "Viva Mode":
        st.markdown('<p class="hero">🎓 Viva practice complete</p>', unsafe_allow_html=True)
    elif escaped:
        st.markdown('<p class="hero">🎉 You escaped the maze!</p>', unsafe_allow_html=True)
        if g["acc"] >= 75:
            st.balloons()
    else:
        st.markdown('<p class="hero">💥 Glitch caught you!</p>', unsafe_allow_html=True)
    st.markdown(f"### {g['title']}")
    answered = g["correct"] + g["wrong"]
    m = st.columns(5)
    m[0].metric("Final score", g["score"])
    m[1].metric("Accuracy", f"{g['acc']}%")
    m[2].metric("Correct", f"{g['correct']} / {answered}")
    m[3].metric("Best streak", g["best_streak"])
    m[4].metric("Time", f"{int(g['t_end'] - g['t0']) // 60}m {int(g['t_end'] - g['t0']) % 60}s")
    if g["skipped"] or g["timeouts"]:
        st.caption(f"Skipped (Backtrack): {g['skipped']} · Timed out: {g['timeouts']}")
    if g.get("boss"):
        st.caption(f"👾 Boss maze: picked **{g['boss']['algo']}** (+{g['boss']['pts']} points, already included in the score)")
    if g["saved"]:
        st.success(f"Saved to the leaderboard as **{g['name']}**.")
    if has_bug(g) and escaped:
        st.markdown(render_maze(1.0, g["gap"], [], escaped=True), unsafe_allow_html=True)

    df = pd.DataFrame(g["log"])
    if not df.empty:
        att = df[df["result"].isin(["correct", "wrong", "timeout"])].copy()
        att["ok"] = (att["result"] == "correct").astype(int)
        c1, c2 = st.columns([1, 1.1], gap="large")
        with c1:
            st.markdown("#### Your strengths by room")
            by_room = {r: round(100 * d["ok"].mean()) for r, d in att.groupby("room")}
            if len(by_room) >= 3:
                fig_ = radar(by_room)
                buf_ = io.BytesIO()
                fig_.savefig(buf_, format="png", transparent=True, dpi=200, bbox_inches="tight")
                plt.close(fig_)
                st.image(buf_)
            else:
                st.bar_chart(pd.Series(by_room, name="accuracy %"))
        with c2:
            st.markdown("#### Topic-wise accuracy")
            t = att.groupby("topic").agg(Asked=("ok", "size"), Correct=("ok", "sum")).reset_index()
            t["Accuracy %"] = (100 * t["Correct"] / t["Asked"]).round()
            st.dataframe(t.sort_values("Accuracy %").rename(columns={"topic": "Topic"}), hide_index=True, width="stretch", height=260)
            weak = t[t["Accuracy %"] < 60]["topic"].tolist()
            if weak:
                st.warning("📚 **Revise first:** " + ", ".join(weak))
            else:
                st.success("No weak topics in this run. Nice.")
        wrong = df[df["result"].isin(["wrong", "timeout", "skipped"])]
        if not wrong.empty:
            st.markdown("#### Review: questions to learn from")
            for _, r in wrong.iterrows():
                with st.expander(f"Q{r['id']} · {r['topic']} · {r['result']}"):
                    st.markdown(r["q"])
                    st.markdown(f"**Your answer:** {r['user'] or '—'}")
                    st.markdown(f"**Correct answer:** {r['answer']}")
                    st.markdown(f"**Why:** {r['why']}")
    b = st.columns(2)
    b[0].button("🔁 Play again", type="primary", on_click=lambda: ss.update(g=None), use_container_width=True)
    b[1].button("🏆 See the leaderboard", on_click=lambda: ss.update(view=BOARD_V), use_container_width=True)


def boss_view(g):
    st.markdown('<p class="hero">👾 Boss maze</p>', unsafe_allow_html=True)
    st.write("Glitch has locked the exit. Your robot must find a path through the last maze. "
             "**Pick the search algorithm** that you think reaches the exit by a **shortest path** while exploring **as few cells as possible**. "
             "Then watch it run.")
    st.caption("Scoring: +5 for reaching the exit, +10 more for a shortest path, +5 more if it also explored fewer cells than BFS.")
    st.radio("Choose your algorithm", list(BOSS_ALGOS), key="boss_pick", horizontal=True, index=None,
             disabled=bool(g.get("boss")))
    if not g.get("boss"):
        st.button("▶ Run it", type="primary", on_click=cb_boss_run, key="b_boss_run", disabled=not ss.get("boss_pick"))
        return
    b = g["boss"]
    best = min(r["steps"] for r in b["res"].values())
    r = b["res"][b["algo"]]
    if r["steps"] == best:
        st.success(f"🎉 {b['algo']} found a shortest path ({r['steps']} steps) after exploring {r['expanded']} cells. Boss points: +{b['pts']}")
    else:
        st.warning(f"{b['algo']} reached the exit, but its path was {r['steps']} steps; the shortest is {best}. Boss points: +{b['pts']}")
    boss_show(b["algo"])
    df = pd.DataFrame([{"Algorithm": k, "Cells explored": v["expanded"], "Path length": v["steps"],
                        "Shortest path?": "✅" if v["steps"] == best else "❌"} for k, v in b["res"].items()])
    st.markdown("**How all four did on this maze**")
    st.dataframe(df, hide_index=True, width="stretch")
    st.info("**Why:** BFS and A* are optimal here. A* explores fewer cells than BFS because the Manhattan heuristic points it at the exit. "
            "DFS is cheap on memory but wanders into a long path. Greedy follows the heuristic and can be misled into a longer route.")
    st.button("🏁 See my result", type="primary", on_click=cb_boss_finish, key="b_boss_finish")


def play_view():
    g = ss.g
    if g is None:
        start_view()
        return
    if g["phase"] == "ask":
        ask_view(g)
    elif g["phase"] == "feedback":
        feedback_view(g)
    elif g["phase"] == "boss":
        boss_view(g)
    else:
        end_view(g)
    if g["phase"] in ("ask", "feedback", "boss"):
        st.button("✖ Quit this run", on_click=lambda: ss.update(g=None), key="b_quit")


def board_view():
    st.subheader("🏆 Leaderboard")
    df = load_board()
    if df.empty:
        st.info("No scores yet. Finish a Full Escape, Quick Run or Adaptive Run to appear here.")
        return
    c1, c2 = st.columns(2)
    mode = c1.selectbox("Mode", ["All"] + sorted(df["mode"].unique()))
    lvl = c2.selectbox("Level", ["All"] + sorted(df["level"].unique()))
    if mode != "All":
        df = df[df["mode"] == mode]
    if lvl != "All":
        df = df[df["level"] == lvl]
    df = df.sort_values(["score", "accuracy"], ascending=False).reset_index(drop=True)
    df.index += 1
    df.index.name = "Rank"
    st.dataframe(df.head(25), width="stretch")
    st.download_button("⬇️ Download as CSV", df.to_csv().encode(), "leaderboard.csv", "text/csv")
    st.caption("Scores are saved in leaderboard.csv next to the app.")


def bank_df():
    rows = []
    for q in QUESTIONS:
        txt = re.sub(r"[*]{2}", "", q["q"]).replace("\n\n", " | ")
        rows.append({"#": q["id"], "Room": f"{q['room']}. {ROOMS[q['room']][0]}", "Topic": q["topic"],
                     "Type": KIND_LABEL[q["kind"]], "Level": q["diff"],
                     "Real-world": "yes" if q["rw"] else "", "Search / state space": "yes" if q["search"] else "",
                     "Question": txt, "Correct answer": q["answer"], "Why": q["why"]})
    return pd.DataFrame(rows)


def bank_view():
    st.subheader("📖 Question bank with answers")
    df = bank_df()
    m = st.columns(5)
    m[0].metric("Questions", len(df))
    m[1].metric("Formats", df["Type"].nunique())
    m[2].metric("Real-world", int((df["Real-world"] == "yes").sum()))
    m[3].metric("Search / state space", int((df["Search / state space"] == "yes").sum()))
    m[4].metric("Syllabus topics", df["Topic"].nunique())
    f1, f2, f3, f4 = st.columns(4)
    t = f1.multiselect("Type", sorted(df["Type"].unique()))
    lv = f2.multiselect("Level", ["Easy", "Medium", "Hard"])
    tp = f3.multiselect("Topic", SYLLABUS_TOPICS)
    txt = f4.text_input("Search text")
    if t: df = df[df["Type"].isin(t)]
    if lv: df = df[df["Level"].isin(lv)]
    if tp: df = df[df["Topic"].isin(tp)]
    if txt: df = df[df.apply(lambda r: txt.lower() in " ".join(map(str, r.values)).lower(), axis=1)]
    st.dataframe(df, hide_index=True, width="stretch", height=480)
    st.download_button("⬇️ Download question bank (CSV)", df.to_csv(index=False).encode(), "question_bank.csv", "text/csv")


# ───────────────────────────── page shell ─────────────────────────────

VIEWS = [PLAY, LAB, BOARD_V, BANK]
if ss.get("view") not in VIEWS:
    ss.view = PLAY
st.segmented_control("Navigation", VIEWS, key="view", label_visibility="collapsed")
view = ss.get("view") or PLAY

# the question timer pauses while you look at other pages
g_ = ss.get("g")
if g_ and g_.get("phase") == "ask" and has_bug(g_):
    if view != PLAY and g_.get("pause_t") is None:
        g_["pause_t"] = time.time()
    elif view == PLAY and g_.get("pause_t"):
        g_["deadline"] += time.time() - g_["pause_t"]
        g_["pause_t"] = None

if view == PLAY:
    play_view()
elif view == LAB:
    lab_view()
elif view == BOARD_V:
    board_view()
else:
    bank_view()