from queue import PriorityQueue
from typing import Callable, List, Tuple
from CARRI.realm import State
from CARRI.action import Step


def lazy_a_star(initial_state: State, goal_test: Callable[[State], bool],
                successors: Callable[[State], List[Tuple[State, Step, int]]],
                heuristic: Callable[[State], float]) -> List[Step]:
    frontier = PriorityQueue()
    frontier.put((heuristic(initial_state), 0, initial_state, []))
    while not frontier.empty():
        _, g, current_state, path = frontier.get()
        if goal_test(current_state):
            return path
        for next_state, action, cost in successors(current_state):
            new_g = g + cost
            f = new_g + heuristic(next_state)
            frontier.put((f, new_g, next_state, path + [action]))
    return []
