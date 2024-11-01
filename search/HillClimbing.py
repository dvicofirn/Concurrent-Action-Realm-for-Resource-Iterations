from queue import PriorityQueue
from typing import Callable, List, Tuple
from CARRIRealm import CARRIState  # Assuming this manages the problem state
from CARRIAction import Step  # Assuming steps/actions are defined in this module


def gbfs(initial_state: CARRIState, goal_test: Callable[[CARRIState], bool],
         successors: Callable[[CARRIState], List[Tuple[CARRIState, Step, int]]],
         heuristic: Callable[[CARRIState], float]) -> List[Step]:
    frontier = PriorityQueue()
    frontier.put((heuristic(initial_state), initial_state, []))
    while not frontier.empty():
        _, current_state, path = frontier.get()
        if goal_test(current_state):
            return path
        for next_state, action, _ in successors(current_state):
            frontier.put((heuristic(next_state), next_state, path + [action]))
    return []
