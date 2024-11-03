from queue import PriorityQueue
from typing import Callable, List, Tuple
from CARRI.realm import State
from CARRI.action import Step


def adaptive_a_star(initial_state: State, goal_test: Callable[[State], bool],
                    successors: Callable[[State], List[Tuple[State, Step, int]]],
                    heuristic: Callable[[State], float]) -> List[Step]:
    frontier = PriorityQueue()
    frontier.put((heuristic(initial_state), 0, initial_state, []))
    g_costs = {initial_state: 0}
    heuristic_values = {initial_state: heuristic(initial_state)}
    
    while not frontier.empty():
        _, g, current_state, path = frontier.get()
        if goal_test(current_state):
            return path
        for next_state, action, cost in successors(current_state):
            new_g = g + cost
            h = heuristic_values.get(next_state, heuristic(next_state))
            f = new_g + h
            if next_state not in g_costs or new_g < g_costs[next_state]:
                g_costs[next_state] = new_g
                heuristic_values[next_state] = h
                frontier.put((f, new_g, next_state, path + [action]))
                # Update heuristic adaptively
                heuristic_values[next_state] = min(h, heuristic(current_state))
    return []
