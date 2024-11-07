from queue import PriorityQueue
from queue import PriorityQueue
from typing import Callable, List, Tuple
from CARRI.problem import State
from CARRI.action import Step

def lazy_greedy(initial_state: State, goal_test: Callable[[State], bool],
                successors: Callable[[State], List[Tuple[State, Step, int]]],
                heuristic: Callable[[State], float]) -> List[Step]:
    frontier = PriorityQueue()
    frontier.put((heuristic(initial_state), initial_state, []))
    while not frontier.empty():
        _, current_state, path = frontier.get()
        if goal_test(current_state):
            return path
        for next_state, action, _ in successors(current_state):
            frontier.put((heuristic(next_state), next_state, path + [action]))
    return []
