from queue import PriorityQueue
from typing import Callable, List, Tuple
from CARRI.realm import State
from CARRI.action import Step

def weighted_a_star(initial_state: State, goal_test: Callable[[State], bool],
                    successors: Callable[[State], List[Tuple[State, Step, int]]],
                    heuristic: Callable[[State], float], weight: float = 1.5) -> List[Step]:
    from queue import PriorityQueue
    
    frontier = PriorityQueue()
    frontier.put((heuristic(initial_state) * weight, 0, initial_state, []))
    g_costs = {initial_state: 0}
    
    while not frontier.empty():
        _, g, current_state, path = frontier.get()
        if goal_test(current_state):
            return path
        for next_state, action, cost in successors(current_state):
            new_g = g + cost
            f = new_g + weight * heuristic(next_state)
            if next_state not in g_costs or new_g < g_costs[next_state]:
                g_costs[next_state] = new_g
                frontier.put((f, new_g, next_state, path + [action]))
    return []
