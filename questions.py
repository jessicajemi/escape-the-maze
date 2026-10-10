"""
Question bank for "Escape the Maze: AI Edition"  (DSC401-6, Units I & II)

75 questions, 7 formats, 7 rooms.
Every question has: room, syllabus topic, type, difficulty, hint, one-line "why".
`fig` = a picture shown WITH the question (tree / wgraph / landscape / csp_map)
`lab` = a live visualiser shown AFTER answering (so the student can watch it run)
"""

ROOMS = {
    1: ("Entry Hall", "🚪"),
    2: ("Agent Lab", "🧪"),
    3: ("Problem Vault", "🗝️"),
    4: ("Blind Corridors", "🔦"),
    5: ("Heuristic Hills", "⛰️"),
    6: ("Constraint Chamber", "🧩"),
    7: ("Boss Maze", "👾"),
}

SYLLABUS_TOPICS = [
    "Foundations and Applications of AI", "Turing Test", "Rational Agents",
    "Intelligent Agents", "Agents and Environments", "Good Behaviour",
    "Nature of Environments", "Problems and Problem Spaces", "State Space Search",
    "Production Systems", "Problem Characteristics", "Issues in Search Program Design",
    "BFS", "DFS", "Iterative Deepening", "Hill Climbing and its Variations",
    "Heuristic Search", "Best First Search", "Constraint Satisfaction Problems",
    "Means-End Analysis",
]

KIND_LABEL = {
    "mcq": "MCQ", "tf": "True / False", "ar": "Assertion–Reason",
    "fib": "Fill in the blank", "match": "Match the following",
    "scenario": "Scenario", "problem": "Problem solving",
}

AR_OPTS = [
    "Both A and R are true, and R is the correct explanation of A",
    "Both A and R are true, but R is NOT the correct explanation of A",
    "A is true, but R is false",
    "A is false, but R is true",
]

QUESTIONS = []


def _add(**kw):
    kw.setdefault("hint", "")
    kw.setdefault("why", "")
    kw.setdefault("rw", False)
    kw.setdefault("search", False)
    kw.setdefault("fig", None)
    kw.setdefault("lab", None)
    kw.setdefault("shuffle", True)
    kw["id"] = len(QUESTIONS) + 1
    QUESTIONS.append(kw)


def mc(room, topic, diff, q, correct, wrong, kind="mcq", **kw):
    """Multiple choice. `correct` is the right option, `wrong` the other three."""
    _add(room=room, topic=topic, diff=diff, kind=kind, q=q,
         options=[correct] + list(wrong), answer=correct, **kw)


def tf(room, topic, diff, q, is_true, **kw):
    _add(room=room, topic=topic, diff=diff, kind="tf", q=q,
         options=["True", "False"], answer="True" if is_true else "False",
         shuffle=False, **kw)


def ar(room, topic, diff, A, R, which, **kw):
    _add(room=room, topic=topic, diff=diff, kind="ar",
         q=f"**Assertion (A):** {A}\n\n**Reason (R):** {R}",
         options=list(AR_OPTS), answer=AR_OPTS[which], shuffle=False, **kw)


def fib(room, topic, diff, q, accepted, **kw):
    _add(room=room, topic=topic, diff=diff, kind="fib", q=q,
         accepted=[a.lower() for a in accepted], answer=accepted[0], **kw)


def match(room, topic, diff, q, pairs, **kw):
    _add(room=room, topic=topic, diff=diff, kind="match", q=q,
         pairs=list(pairs),
         answer="; ".join(f"{a} → {b}" for a, b in pairs), **kw)


# ════════════════════════════════════════════════════════════════
# ROOM 1 · ENTRY HALL — Foundations, applications, Turing Test
# ════════════════════════════════════════════════════════════════
mc(1, "Foundations and Applications of AI", "Easy",
   "AI is often defined in four ways. Which one describes a system that **does the right thing** given what it knows?",
   "Acting rationally",
   ["Thinking humanly", "Acting humanly", "Thinking rationally"],
   hint="Think of the phrase 'rational agent'.",
   why="The rational-agent view of AI is about acting rationally: choosing the best action for the goal.")

tf(1, "Turing Test", "Easy",
   "In the **standard** Turing Test, the human interrogator can **see** the machine while asking questions.",
   False,
   hint="Think about what the interrogator is allowed to use.",
   why="The test is text-only. The interrogator cannot see or hear the candidates, so only the conversation is judged.")

mc(1, "Turing Test", "Easy",
   "A machine is said to **pass the Turing Test** when...",
   "the interrogator cannot reliably tell whether the answers come from a machine or a human",
   ["it beats a human champion at chess",
    "it solves every problem in polynomial time",
    "it can see and move like a human"],
   hint="It is about being indistinguishable, not about being the best.",
   why="Passing means the interrogator cannot reliably tell the machine from the human.")

mc(1, "Turing Test", "Hard",
   "Which ability is needed **only** for the *Total* Turing Test and not for the standard Turing Test?",
   "Computer vision and robotics",
   ["Natural language processing", "Knowledge representation", "Machine learning"],
   hint="The standard test is just a text chat.",
   why="Vision and robotics (perceiving and moving objects) are added in the Total Turing Test. The text test needs language, knowledge, reasoning and learning.")

fib(1, "Turing Test", "Easy",
    "The Turing Test was proposed by ______ in his 1950 paper *Computing Machinery and Intelligence*.",
    ["Alan Turing", "Turing", "Alan M. Turing", "Alan Mathison Turing", "A. M. Turing"],
    hint="The test is named after him.",
    why="Alan Turing proposed it in 1950 as a practical way to answer 'Can machines think?'")

mc(1, "Turing Test", "Easy",
   "A bank's customer-care chatbot replies so naturally that a customer chats for 20 minutes without realising it is a program. Which approach to AI does this best show?",
   "Acting humanly",
   ["Thinking humanly", "Thinking rationally", "Acting rationally"],
   kind="scenario", rw=True,
   hint="The customer only judged the behaviour.",
   why="Behaviour that cannot be told apart from a human is the 'acting humanly' idea behind the Turing Test.")

match(1, "Foundations and Applications of AI", "Easy",
      "Match each everyday product with the AI area it mainly uses.",
      [("Google Maps route suggestion", "Search and planning"),
       ("Email spam filter", "Machine learning (classification)"),
       ("Alexa / Siri voice assistant", "Natural language processing"),
       ("Phone face unlock", "Computer vision")],
      rw=True,
      hint="Ask what the product takes as input: text, speech, images or a map?",
      why="Routes come from searching a map, spam is classified from examples, voice assistants process language, and face unlock processes images.")

tf(1, "Foundations and Applications of AI", "Easy",
   "A chess program that can do nothing except play chess is an example of **strong (general) AI**.",
   False,
   hint="General means it can do many different tasks.",
   why="It is narrow (weak) AI: it is built for one task only.")

ar(1, "Foundations and Applications of AI", "Medium",
   "Spam filters and chess engines are examples of narrow (weak) AI.",
   "Each of them is built for one specific task and cannot transfer its skill to unrelated tasks.",
   0, rw=True,
   hint="Ask: does R explain WHY they are narrow?",
   why="Narrow AI means good at one task only, which is exactly what R says.")

# ════════════════════════════════════════════════════════════════
# ROOM 2 · AGENT LAB — agents, rationality, good behaviour, environments
# ════════════════════════════════════════════════════════════════
mc(2, "Agents and Environments", "Easy",
   "An agent perceives its environment through ______ and acts on it through ______.",
   "sensors; actuators",
   ["actuators; sensors", "memory; processors", "goals; rules"],
   hint="Eyes and ears versus hands and legs.",
   why="Sensors give percepts in, actuators carry actions out.")

fib(2, "Agents and Environments", "Easy",
    "The agent function maps every percept ______ to an action.",
    ["sequence", "history", "percept sequence"],
    hint="Everything the agent has perceived so far.",
    why="The agent function takes the whole percept sequence (history) and returns an action.")

mc(2, "Rational Agents", "Easy",
   "A **rational agent** is best described as one that...",
   "chooses the action expected to maximise its performance measure, given what it has perceived and knows",
   ["always picks the action with the best actual outcome",
    "copies human reasoning step by step",
    "never makes a mistake"],
   hint="Rational is about expected results, not perfect results.",
   why="Rationality maximises expected performance with the information available.")

tf(2, "Rational Agents", "Medium",
   "A rational agent is the same thing as an omniscient agent.",
   False,
   hint="Can any agent know the future?",
   why="An omniscient agent knows the real outcome of its actions, which is impossible. A rational agent only does the best it can with what it knows.")

mc(2, "Good Behaviour", "Medium",
   "When designing the performance measure for a robot vacuum cleaner, it is best to measure...",
   "how clean the floor is over time",
   ["how much dirt the robot picks up per hour",
    "how many times the motor switches on",
    "how fast the robot moves"],
   rw=True,
   hint="Measure what you want in the world, not what the robot does.",
   why="Design the measure around the result you want (a clean floor), not around the robot's activity.")

mc(2, "Good Behaviour", "Hard",
   "A robot vacuum gets +1 for every unit of dirt it sucks up. It learns to suck up dirt, dump it back on the floor, and suck it up again. What went wrong?",
   "The performance measure rewards an activity instead of the result we want (a clean floor)",
   ["The robot's sensors are broken",
    "The environment is partially observable",
    "The robot is not rational"],
   kind="scenario", rw=True,
   hint="Is the robot really failing, or is the reward badly written?",
   why="The robot is rational for the reward it was given. The reward itself was badly designed.")

mc(2, "Nature of Environments", "Easy",
   "In the task-environment description **PEAS**, the letters stand for...",
   "Performance measure, Environment, Actuators, Sensors",
   ["Percept, Evaluation, Action, State",
    "Planning, Execution, Analysis, Search",
    "Problem, Example, Algorithm, Solution"],
   hint="Four things you must specify before designing an agent.",
   why="PEAS = Performance measure, Environment, Actuators, Sensors.")

match(2, "Nature of Environments", "Medium",
      "Match each PEAS element with an example for a self-driving taxi.",
      [("Performance measure", "Safe, fast, legal, comfortable trip"),
       ("Environment", "Roads, traffic, pedestrians"),
       ("Actuators", "Steering, accelerator, brake"),
       ("Sensors", "Cameras, GPS, speedometer")],
      rw=True,
      hint="Actuators act, sensors sense.",
      why="Performance = how we judge it, Environment = where it works, Actuators = what it controls, Sensors = what it reads.")

mc(2, "Nature of Environments", "Medium",
   "Which task environment is **fully observable, deterministic, static, discrete and single-agent**?",
   "Solving a crossword puzzle",
   ["Driving a taxi", "Playing poker", "Robot football"],
   hint="Nothing changes while you think and there is nobody else playing.",
   why="Poker hides cards, taxis change continuously, and football has other agents. A crossword has none of these.")

tf(2, "Nature of Environments", "Easy",
   "In a deterministic environment, the next state is completely decided by the current state and the agent's action.",
   True,
   hint="Deterministic means no randomness.",
   why="That is the definition of deterministic. If there is randomness, it is stochastic.")

ar(2, "Nature of Environments", "Hard",
   "Taxi driving is a static environment.",
   "Traffic and pedestrians keep changing while the agent is still deciding what to do.",
   3, rw=True,
   hint="Is the sentence R describing a static or a dynamic world?",
   why="R is true, but it is the reason taxi driving is DYNAMIC. So A is false.")

mc(2, "Intelligent Agents", "Medium",
   "Which agent type compares how 'happy' different outcomes would make it, for example a route planner balancing time, safety and cost?",
   "Utility-based agent",
   ["Simple reflex agent", "Model-based reflex agent", "Goal-based agent"],
   hint="'Happy' is another word for utility.",
   why="A utility-based agent scores outcomes and picks the best trade-off. A goal-based agent only checks goal reached or not.")

mc(2, "Intelligent Agents", "Easy",
   "A room thermostat switches the heater ON when the temperature is below 20°C and OFF otherwise, using only the current reading. Which agent type is it?",
   "Simple reflex agent",
   ["Goal-based agent", "Utility-based agent", "Learning agent"],
   kind="scenario", rw=True,
   hint="It uses condition-action rules and no memory.",
   why="It reacts to the current percept using condition-action rules, which is a simple reflex agent.")

# ════════════════════════════════════════════════════════════════
# ROOM 3 · PROBLEM VAULT — problems, state space, production systems,
#          problem characteristics, issues in search design
# ════════════════════════════════════════════════════════════════
mc(3, "Production Systems", "Easy",
   "Which of these is **NOT** a component of a production system?",
   "A gradient-descent optimiser",
   ["A set of production rules", "A global database (working memory)", "A control strategy"],
   hint="Think rules, data, and who picks the rule.",
   why="A production system has rules, a global database and a control strategy. Gradient descent is a learning technique.")

fib(3, "Problems and Problem Spaces", "Easy",
    "In a state space, applying a rule moves the system from one ______ to another.",
    ["state", "states", "node"],
    hint="The nodes of a state-space graph.",
    why="Nodes are states and rules (operators) are the moves between them.")

mc(3, "State Space Search", "Hard",
   "**Water jug problem:** a 4-litre jug and a 3-litre jug, no markings. Moves: fill a jug, empty a jug, or pour one into the other until the source is empty or the target is full. Starting from (0, 0), what is the **minimum number of moves** to get exactly 2 litres in the 4-litre jug?",
   "6", ["4", "5", "7"],
   kind="problem", search=True, lab="jug",
   hint="Try fill 3L → pour into 4L → fill 3L → pour... and keep going.",
   why="For example (0,0)→(0,3)→(3,0)→(3,3)→(4,2)→(0,2)→(2,0). BFS over the state space confirms nothing shorter exists.")

tf(3, "State Space Search", "Easy",
   "In a state space, the same state can be reached through more than one path.",
   True, search=True,
   hint="Think of two different routes to the same city.",
   why="That is why graph search keeps an explored set: to avoid expanding the same state again.")

match(3, "Problem Characteristics", "Medium",
      "Match each problem with the characteristic it shows.",
      [("Theorem proving (a useless step can be ignored)", "Ignorable steps"),
       ("8-puzzle (a wrong move can be undone)", "Recoverable steps"),
       ("Chess (a move cannot be taken back)", "Irrecoverable steps"),
       ("Symbolic integration of a sum of terms", "Decomposable problem")],
      hint="Can you undo it? Can you ignore it? Can you split it?",
      why="Ignorable: theorem proving. Recoverable: 8-puzzle. Irrecoverable: chess. Decomposable: integrating a sum term by term.")

mc(3, "Problem Characteristics", "Medium",
   "Google Maps must return the **fastest** route from Bengaluru to Mysuru, not just any route. Which problem characteristic does this show?",
   "A good solution is relative (we need the best path), not absolute",
   ["The steps of the problem are ignorable",
    "The problem is decomposable",
    "The task needs interaction with a person"],
   kind="scenario", rw=True, search=True,
   hint="Is 'any path' enough, or must it be the best one?",
   why="When only the best path is acceptable, the solution is relative, so we must compare paths.")

tf(3, "Problem Characteristics", "Medium",
   "Moves in chess are recoverable: a program can always take back a bad move.",
   False,
   hint="Can you un-play a move in a real game?",
   why="Chess moves cannot be undone, so chess is irrecoverable. The 8-puzzle is the recoverable example.")

mc(3, "Issues in Search Program Design", "Hard",
   "An automated theorem prover starts from the statement to be proved and works **backwards** towards the known axioms. Which design choice is this?",
   "Backward (goal-directed) reasoning",
   ["Forward (data-directed) reasoning",
    "Representing the search space as a graph",
    "Using a heuristic function"],
   kind="scenario", search=True,
   hint="Which end are we starting from: the facts or the goal?",
   why="Direction of search is a design issue. Starting from the goal and moving back to the facts is backward reasoning.")

ar(3, "Issues in Search Program Design", "Hard",
   "Representing the search space as a graph instead of a tree can save effort.",
   "A graph search can recognise a state it has already generated and avoid expanding it again.",
   0, search=True,
   hint="What happens when two paths reach the same state?",
   why="In a tree the same state may be expanded many times. A graph recognises repeats, at the cost of remembering visited states.")

fib(3, "Production Systems", "Medium",
    "A production system in which applying a rule never prevents the later use of another rule that was applicable at that time is called ______.",
    ["monotonic"],
    hint="The opposite of non-monotonic.",
    why="In a monotonic production system, applying a rule never blocks a rule that could have been applied before.")

mc(3, "Production Systems", "Hard",
   "A production system that is both **monotonic** and **partially commutative** is called a ______ production system.",
   "commutative",
   ["non-commutative", "irrecoverable", "decomposable"],
   hint="The order of the rules stops mattering.",
   why="In a commutative system the order of applying rules does not matter, so no backtracking is needed.")

mc(3, "Problems and Problem Spaces", "Medium",
   "The 8-puzzle has 9! = 362,880 ways to arrange the tiles, but any start state can reach only half of them. How many states are reachable?",
   "181,440", ["362,880", "40,320", "90,720"],
   kind="problem", search=True,
   hint="Half of 362,880.",
   why="Only half of the arrangements have the right parity, so 362,880 / 2 = 181,440 states are reachable.")

# ════════════════════════════════════════════════════════════════
# ROOM 4 · BLIND CORRIDORS — BFS, DFS, iterative deepening
# ════════════════════════════════════════════════════════════════
match(4, "BFS", "Easy",
      "Match each search strategy with its key feature.",
      [("BFS", "Frontier is a FIFO queue"),
       ("DFS", "Frontier is a LIFO stack"),
       ("Depth-limited search", "DFS that stops at a fixed depth"),
       ("Iterative deepening", "Repeats depth-limited search with limit 0, 1, 2, ...")],
      hint="Queue = first in, first out. Stack = last in, first out.",
      why="BFS uses a queue, DFS a stack, depth-limited search cuts off at a depth, and iterative deepening repeats it with a growing limit.")

mc(4, "BFS", "Medium",
   "Look at the tree (children are expanded left to right). In which order does **BFS** remove nodes from the queue until it reaches G?",
   "S, A, B, C, D, E, F, G",
   ["S, A, C, D, G", "S, B, F, E, A, D, C, G", "S, A, B, D, C, F, E, G"],
   kind="problem", search=True, fig="tree", lab="bfs_tree",
   hint="BFS goes level by level.",
   why="Level 0: S. Level 1: A, B. Level 2: C, D, E, F. Level 3: G.")

mc(4, "DFS", "Medium",
   "On the same tree, in which order does **DFS** (left to right) visit nodes until it reaches G?",
   "S, A, C, D, G",
   ["S, A, B, C, D, E, F, G", "S, B, E, F, A, C, D, G", "S, A, C, D, B, E, F, G"],
   kind="problem", search=True, fig="tree", lab="dfs_tree",
   hint="DFS goes as deep as it can first. C is a dead end.",
   why="DFS: S → A → C (dead end) → back to A → D → G. It stops as soon as G is found.")

tf(4, "BFS", "Easy",
   "When every step costs the same, BFS always finds the goal that is closest to the start (fewest steps).",
   True, search=True,
   hint="BFS explores in order of depth.",
   why="BFS reaches all nodes at depth d before any node at depth d+1, so the first goal it finds is the shallowest.")

tf(4, "DFS", "Medium",
   "DFS without a visited set can run forever on a graph that contains a cycle.",
   True, search=True,
   hint="What if A leads to B and B leads back to A?",
   why="Without remembering visited states, DFS can keep going around the cycle.")

mc(4, "DFS", "Medium",
   "Why is DFS preferred over BFS when memory is limited?",
   "It stores only the current path and the unexplored siblings, about O(bm), instead of a whole level, about O(b^d)",
   ["It always finds the shortest path",
    "It never revisits any state",
    "It needs no data structure at all"],
   hint="Compare how many nodes each keeps in memory.",
   why="BFS must remember an entire level which grows exponentially. DFS only remembers one branch.")

mc(4, "Iterative Deepening", "Medium",
   "Iterative deepening search combines...",
   "the low memory use of DFS with the completeness (and shallowest-goal guarantee) of BFS",
   ["the speed of greedy search with the optimality of A*",
    "hill climbing with random restarts",
    "BFS with a heuristic function"],
   hint="It is DFS repeated with a growing depth limit.",
   why="It runs depth-limited DFS with limit 0, 1, 2, ... so it uses DFS memory but finds the shallowest goal like BFS.")

mc(4, "Iterative Deepening", "Hard",
   "Iterative deepening runs on the same tree with depth limits 0, 1, 2, 3, ... At which depth limit is G **first found**?",
   "3", ["1", "2", "4"],
   kind="problem", search=True, fig="tree", lab="iddfs_tree",
   hint="Count the edges on the path S → A → D → G.",
   why="G is at depth 3 (S → A → D → G), so limits 0, 1 and 2 fail and limit 3 succeeds.")

ar(4, "Iterative Deepening", "Hard",
   "Iterative deepening regenerates the upper levels many times, yet its time complexity is still O(b^d).",
   "In a tree most nodes are at the deepest level, so repeating the shallow levels adds only a small overhead.",
   0, search=True,
   hint="Where are most of the nodes in a tree?",
   why="The last level has far more nodes than all the levels above it, so the repeated work is small.")

mc(4, "BFS", "Medium",
   "On a social network you want to show every person within 2 connections of a user ('friends of friends'), nearest first. Which search is the natural choice?",
   "BFS", ["DFS", "Hill climbing", "Means-end analysis"],
   kind="scenario", rw=True, search=True,
   hint="Nearest first means level by level.",
   why="BFS lists everyone at distance 1, then everyone at distance 2.")

mc(4, "Iterative Deepening", "Hard",
   "A game program must pick a move within a time limit. It does not know how deep it can search and memory is limited. Which strategy lets it keep a best-so-far answer after each finished depth?",
   "Iterative deepening",
   ["BFS storing every node",
    "Plain DFS with no depth limit",
    "Random-restart hill climbing"],
   kind="scenario", rw=True, search=True,
   hint="A growing depth limit gives a usable answer at every step.",
   why="Iterative deepening finishes depth 1, then 2, then 3. When time runs out, the last finished depth is still a valid answer. Game engines do exactly this.")

fib(4, "BFS", "Easy",
    "BFS expands nodes in increasing order of their ______ in the search tree.",
    ["depth", "level", "distance"],
    hint="Level by level.",
    why="BFS finishes every node at one depth before going deeper.")

# ════════════════════════════════════════════════════════════════
# ROOM 5 · HEURISTIC HILLS — heuristic search, best-first, hill climbing
# ════════════════════════════════════════════════════════════════
mc(5, "Heuristic Search", "Easy",
   "A heuristic function h(n) in search estimates...",
   "the cost of the cheapest path from node n to a goal",
   ["the cost of the path from the start to n",
    "the number of nodes in the tree",
    "the depth limit of the search"],
   hint="h looks forward to the goal. g looks back to the start.",
   why="h(n) is the estimated cost still left to reach the goal.")

mc(5, "Best First Search", "Easy",
   "**Greedy best-first search** always expands the frontier node with the lowest...",
   "h(n)", ["g(n)", "g(n) + h(n)", "depth"],
   hint="Greedy only looks at how close it thinks the goal is.",
   why="Greedy uses only the heuristic h(n). A* uses g(n) + h(n).")

mc(5, "Best First Search", "Hard",
   "In the graph shown (edge costs on the edges, h(n) under each node), which path does **Greedy best-first search** return from S to G?",
   "S → A → C → G (cost 13)",
   ["S → B → G (cost 8)", "S → A → C → G (cost 7)", "S → B → G (cost 12)"],
   kind="problem", search=True, fig="wgraph", lab="greedy_w",
   hint="At S, compare h(A) and h(B). Greedy picks the smaller h.",
   why="h(A)=1 is smaller than h(B)=3, so greedy goes to A, then C, then G. That path costs 1+2+10 = 13, while S–B–G costs only 8.")

mc(5, "Heuristic Search", "Hard",
   "On the same graph, what is the cost of the path that **A\\* search** returns from S to G?",
   "8", ["6", "10", "13"],
   kind="problem", search=True, fig="wgraph", lab="astar_w",
   hint="A* uses f = g + h. Compare f for the two routes.",
   why="Route via A: f(G)=13. Route via B: f(B)=4+3=7 stays lower, so A* expands B and reaches G with cost 4+4 = 8.")

mc(5, "Heuristic Search", "Easy",
   "A* search evaluates a node n using f(n) = ...",
   "g(n) + h(n)", ["h(n) only", "g(n) only", "g(n) − h(n)"],
   hint="Cost so far plus estimated cost to go.",
   why="g(n) is the cost already paid and h(n) is the estimate of what remains.")

tf(5, "Heuristic Search", "Easy",
   "An admissible heuristic never overestimates the true cost of reaching the goal.",
   True,
   hint="Admissible means optimistic.",
   why="That is the definition. Admissible heuristics keep A* optimal.")

mc(5, "Heuristic Search", "Medium",
   "A navigation app uses the **straight-line distance** to the destination as h(n) in A*. Why is this heuristic admissible?",
   "No road route can be shorter than the straight line, so it never overestimates",
   ["Roads are always straight",
    "Because it is equal to g(n)",
    "Because it ignores the destination"],
   kind="scenario", rw=True, search=True,
   hint="Can a road be shorter than a straight line?",
   why="The straight line is the shortest possible distance, so the real route is never shorter.")

match(5, "Hill Climbing and its Variations", "Medium",
      "Match each hill-climbing term with its description.",
      [("Local maximum", "Better than all neighbours, but not the best overall"),
       ("Plateau", "A flat area where neighbouring states have equal value"),
       ("Ridge", "A line of local maxima that single moves cannot climb"),
       ("Global maximum", "The best state in the entire landscape")],
      hint="Local = only looks nearby. Global = the whole landscape.",
      why="These are the three classic problems of hill climbing (local maximum, plateau, ridge) plus the global maximum it is trying to reach.")

mc(5, "Hill Climbing and its Variations", "Hard",
   "The landscape is shown: the value of each state 0 to 9. **Steepest-ascent hill climbing** starts at state 1 (value 4) and may move only to an adjacent state. At which state does it stop?",
   "State 2 (value 7)",
   ["State 6 (value 9)", "State 4 (value 3)", "State 0 (value 2)"],
   kind="problem", search=True, fig="landscape10", lab="hill",
   hint="Neighbours of state 1 are states 0 and 2. Keep climbing until nothing is higher.",
   why="From state 1 (4) it moves to state 2 (7). Its neighbours, states 1 and 3, have values 4 and 5, both lower than 7. It stops at a local maximum, missing the global maximum 9 at state 6.")

mc(5, "Hill Climbing and its Variations", "Medium",
   "Which hill-climbing variation restarts from randomly chosen start states until it finds a goal?",
   "Random-restart hill climbing",
   ["Stochastic hill climbing", "First-choice hill climbing", "Steepest-ascent hill climbing"],
   hint="The name tells you.",
   why="Random-restart hill climbing runs many climbs from random starts, so one of them is likely to reach the global maximum.")

ar(5, "Hill Climbing and its Variations", "Hard",
   "Simulated annealing can escape a local maximum, but plain hill climbing cannot.",
   "Simulated annealing sometimes accepts a worse move, with a probability that shrinks as the 'temperature' falls.",
   0,
   hint="How can a climber get down off a small peak?",
   why="Accepting a worse move now and then lets the search leave a local maximum. Plain hill climbing never goes downhill.")

fib(5, "Best First Search", "Medium",
    "Best-first search keeps its frontier in a ______ queue ordered by an evaluation function.",
    ["priority", "priority queue", "min-priority", "min priority"],
    hint="The best node should come out first.",
    why="A priority queue always returns the node with the best evaluation value.")

tf(5, "Best First Search", "Medium",
   "Greedy best-first search is guaranteed to find the cheapest path.",
   False, search=True,
   hint="It ignores the cost already travelled.",
   why="Greedy ignores g(n), so it can follow a path that looks close but costs more. The weighted graph shows this.")

mc(5, "Hill Climbing and its Variations", "Medium",
   "A warehouse robot layout tool uses hill climbing to place shelves and reduce walking distance. Over many runs it keeps ending in mediocre layouts where any single swap makes things worse. Which fix is most suitable?",
   "Random-restart hill climbing (or simulated annealing)",
   ["Stop after the first run",
    "Use BFS on all layouts",
    "Remove the evaluation function"],
   kind="scenario", rw=True,
   hint="The tool is stuck on a local maximum.",
   why="Restarting from new random layouts, or sometimes accepting worse moves, helps escape local maxima.")

# ════════════════════════════════════════════════════════════════
# ROOM 6 · CONSTRAINT CHAMBER — CSP and means-end analysis
# ════════════════════════════════════════════════════════════════
mc(6, "Constraint Satisfaction Problems", "Easy",
   "A constraint satisfaction problem (CSP) is defined by a set of ______, a domain of values for each, and a set of constraints.",
   "variables", ["operators", "heuristics", "agents"],
   hint="What do we assign values to?",
   why="A CSP = variables + domains + constraints.")

mc(6, "Constraint Satisfaction Problems", "Hard",
   "Map colouring with 3 colours (Red, Green, Blue). WA = Red and NT = Green, as in the picture. SA touches WA, NT and Q. Which colour can SA still take?",
   "Blue only",
   ["Red or Blue", "Green or Blue", "Any of the three"],
   kind="problem", search=True, fig="csp_map", lab="csp",
   hint="SA cannot match any neighbour that is already coloured.",
   why="SA touches WA (Red) and NT (Green), so it cannot be Red or Green. Only Blue is left.")

mc(6, "Constraint Satisfaction Problems", "Medium",
   "The **MRV** (minimum remaining values) heuristic chooses the next variable that...",
   "has the fewest legal values left in its domain",
   ["has the most legal values left",
    "is involved in the most constraints",
    "was assigned most recently"],
   hint="Pick the most stuck variable first.",
   why="Choosing the most constrained variable first fails early and saves time. (Most constraints is the degree heuristic.)")

tf(6, "Constraint Satisfaction Problems", "Easy",
   "Backtracking search for a CSP is a depth-first search that assigns one variable at a time and backs up when a variable has no legal value.",
   True, search=True,
   hint="Assign, check, undo if stuck.",
   why="That is exactly how backtracking search works.")

mc(6, "Constraint Satisfaction Problems", "Hard",
   "A college must schedule 12 exams in 5 time slots so that no student has two exams at the same time. How is this modelled as a CSP?",
   "Variables = exams, domains = time slots, constraint = exams that share a student must get different slots",
   ["Variables = students, domain = exams, constraint = every exam is different",
    "Variables = time slots, domain = students, no constraints",
    "It cannot be modelled as a CSP"],
   kind="scenario", rw=True,
   hint="What are we choosing a value for, and what values are allowed?",
   why="We assign a slot (value) to each exam (variable), and clashes between exams of the same student are the constraints.")

fib(6, "Constraint Satisfaction Problems", "Medium",
    "After each assignment, forward checking removes values from the domains of ______ variables that share a constraint with it.",
    ["neighbouring", "neighboring", "neighbour", "neighbor", "neighbours", "neighbors", "adjacent", "connected", "unassigned", "constrained", "related", "other", "future"],
    hint="The variables next to the one just assigned.",
    why="Forward checking prunes neighbours' domains right after an assignment, and backtracks early if any domain becomes empty.")

mc(6, "Means-End Analysis", "Easy",
   "Means–end analysis works by...",
   "repeatedly choosing an operator that reduces the difference between the current state and the goal",
   ["expanding nodes in order of depth",
    "choosing random uphill neighbours",
    "colouring regions with different colours"],
   hint="Find the difference, then find a way to reduce it.",
   why="MEA compares the current and goal states, picks an operator that reduces the difference, and sets sub-goals if needed.")

mc(6, "Means-End Analysis", "Hard",
   "A robot is in Room 1, a box is in Room 2 and the goal is the box in Room 3 (rooms in a line 1–2–3). Operators: Move to an adjacent room, Pick (robot and box in the same room, hand empty), Drop. Which plan does **means–end analysis** build?",
   "Move 1→2, Pick, Move 2→3, Drop",
   ["Pick, Move 1→2, Move 2→3, Drop",
    "Move 1→2, Move 2→3, Pick, Drop",
    "Drop, Move 1→2, Pick, Move 2→3"],
   kind="problem", search=True, lab="mea",
   hint="To Drop in Room 3 you need to hold the box and be in Room 3. Work back from there.",
   why="Difference: box not in Room 3. Operator Drop(R3) needs 'holding box' and 'robot in R3'. Holding needs Pick, which needs the robot in R2. So: Move 1→2, Pick, Move 2→3, Drop.")

ar(6, "Means-End Analysis", "Medium",
   "Means–end analysis may create sub-goals before applying an operator.",
   "It picks an operator that reduces the difference even when that operator's preconditions are not yet true, and the missing preconditions become new sub-goals.",
   0, search=True, lab="mea",
   hint="What happens when you pick an operator you cannot use yet?",
   why="Unmet preconditions are turned into sub-goals, solved first, and then the operator is applied.")

# ════════════════════════════════════════════════════════════════
# ROOM 7 · BOSS MAZE — mixed, hard, search-heavy
# ════════════════════════════════════════════════════════════════
mc(7, "Heuristic Search", "Hard",
   "In a grid maze with moves up, down, left and right, why is the **Manhattan distance** |Δrow| + |Δcol| an admissible heuristic for A*?",
   "Every move changes the row or column by only 1, and walls can only make the real path longer, so it never overestimates",
   ["Because it also counts diagonal moves",
    "Because it equals the exact cost in every maze",
    "Because it ignores both the walls and the goal"],
   search=True, lab="grid",
   hint="Think about the shortest path in an empty grid, then add walls.",
   why="In an empty grid you need at least |Δrow| + |Δcol| moves. Walls can only add more moves, so the estimate is never too high.")

mc(7, "Heuristic Search", "Hard",
   "A game developer sets h(n) = 0 for every node in the A* pathfinding for NPCs. What happens?",
   "A* behaves like uniform-cost search (Dijkstra): still optimal, but it explores many more nodes",
   ["It becomes greedy best-first search",
    "It becomes depth-first search",
    "It fails to find any path"],
   kind="scenario", rw=True, search=True, lab="grid",
   hint="f(n) = g(n) + 0.",
   why="With h = 0, f(n) = g(n), so nodes are expanded by cost so far. That is uniform-cost search: still optimal but with no guidance.")

mc(7, "Heuristic Search", "Hard",
   "On the weighted graph shown, in which order does **A\\*** expand nodes until it finishes (goal included)?",
   "S, A, C, B, G",
   ["S, B, G", "S, A, C, G", "S, A, B, C, G"],
   kind="problem", search=True, fig="wgraph", lab="astar_w",
   hint="Always expand the lowest f = g + h. Watch f(G) via C: it is large.",
   why="f(A)=2, f(B)=7 → expand A. f(C)=3+1=4 → expand C. Now f(G via C)=13 and f(B)=7 → expand B. f(G via B)=8 → expand G.")

ar(7, "Best First Search", "Hard",
   "Greedy best-first search can be faster than A*, but it may return a longer path.",
   "Greedy search uses only h(n) and ignores the cost g(n) already travelled.",
   0, search=True,
   hint="What does greedy ignore?",
   why="Ignoring g(n) makes it quick and focused, but it can walk into an expensive route.")

mc(7, "Iterative Deepening", "Hard",
   "On the tree shown, count **every node visit** (repeats included) made by iterative deepening with limits 0, 1, 2, 3 until G is reached. How many visits?",
   "16", ["12", "14", "20"],
   kind="problem", search=True, fig="tree", lab="iddfs_tree",
   hint="Limit 0 visits 1 node, limit 1 visits 3 nodes, and so on.",
   why="Limit 0: 1 visit. Limit 1: 3. Limit 2: 7. Limit 3: S, A, C, D, G = 5. Total 1 + 3 + 7 + 5 = 16.")

tf(7, "Heuristic Search", "Hard",
   "Every consistent heuristic is also admissible.",
   True,
   hint="Consistency is the stronger property.",
   why="Consistency means h(n) ≤ cost(n, n') + h(n') for every step. Adding this along any path to the goal (where h = 0) gives h(n) ≤ true cost.")

assert len(QUESTIONS) == 75, len(QUESTIONS)
