from queue import Queue
from typing import Callable, List, Tuple
from CARRIRealm import CARRIState
from CARRIAction import Step


def enforced_hill_climbing(initial_state: CARRIState, goal_test: Callable[[CARRIState], bool],
                           successors: Callable[[CARRIState], List[Tuple[CARRIState, Step, int]]],
                           heuristic: Callable[[CARRIState], float]) -> List[Step]:
    def bfs(state):
        queue = Queue()
        queue.put((state, []))
        while not queue.empty():
            current_state, path = queue.get()
            for next_state, action, _ in successors(current_state):
                if heuristic(next_state) < heuristic(state):
                    return path + [action]
                queue.put((next_state, path + [action]))
        return None

    current_state = initial_state
    path = []
    while not goal_test(current_state):
        next_steps = sorted(successors(current_state), key=lambda s: heuristic(s[0]))
        if not next_steps or heuristic(next_steps[0][0]) >= heuristic(current_state):
            result = bfs(current_state)
            if result is None:
                return []  # No solution or stuck in local minima
            path.extend(result)
            current_state = path[-1][0]
        else:
            next_state, action, _ = next_steps[0]
            path.append(action)
            current_state = next_state
    return path
