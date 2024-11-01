from queue import PriorityQueue
from typing import Callable, List, Tuple
from CARRIRealm import CARRIState
from CARRIAction import Step

def rational_lazy_a_star(initial_state: CARRIState, goal_test: Callable[[CARRIState], bool],
                         successors: Callable[[CARRIState], List[Tuple[CARRIState, Step, int]]],
                         heuristic: Callable[[CARRIState], float],
                         cost_adjustment: Callable[[float], float]) -> List[Step]:
    frontier = PriorityQueue()
    frontier.put((cost_adjustment(heuristic(initial_state)), 0, initial_state, []))
    while not frontier.empty():
        _, g, current_state, path = frontier.get()
        if goal_test(current_state):
            return path
        for next_state, action, cost in successors(current_state):
            new_g = g + cost
            f = cost_adjustment(new_g + heuristic(next_state))
            frontier.put((f, new_g, next_state, path + [action]))
    return []
