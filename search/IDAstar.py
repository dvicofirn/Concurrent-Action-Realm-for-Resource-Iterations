from typing import Callable, List, Tuple
from CARRIRealm import CARRIState
from CARRIAction import Step

def ida_star(initial_state: CARRIState, goal_test: Callable[[CARRIState], bool],
             successors: Callable[[CARRIState], List[Tuple[CARRIState, Step, int]]],
             heuristic: Callable[[CARRIState], float]) -> List[Step]:
    def search(path, g, bound):
        current_state = path[-1][0]
        f = g + heuristic(current_state)
        if f > bound:
            return f
        if goal_test(current_state):
            return path
        min_cost = float('inf')
        for next_state, action, cost in successors(current_state):
            if all(state[0] != next_state for state in path):  # Avoid cycles
                result = search(path + [(next_state, action)], g + cost, bound)
                if isinstance(result, list):
                    return result
                min_cost = min(min_cost, result)
        return min_cost

    bound = heuristic(initial_state)
    path = [(initial_state, None)]
    while True:
        result = search(path, 0, bound)
        if isinstance(result, list):
            return [action for _, action in result if action]
        if result == float('inf'):
            return []  # No solution
        bound = result
