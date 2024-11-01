from queue import PriorityQueue
from typing import Callable, List, Tuple
from CARRIRealm import CARRIState  # Assuming this manages the problem state
from CARRIAction import Step  # Assuming steps/actions are defined in this module

def a_star_search(initial_state: CARRIState, goal_test: Callable[[CARRIState], bool],
                  successors: Callable[[CARRIState], List[Tuple[CARRIState, Step, int]]],
                  heuristic: Callable[[CARRIState], float]) -> List[Step]:
    """
    A* search algorithm with flexible heuristic input.
    
    Args:
    - initial_state: The starting state of the problem.
    - goal_test: A function that checks if a given state is a goal state.
    - successors: A function that returns a list of successor states for a given state, 
                  along with the action (Step) that leads to them and the cost.
    - heuristic: A heuristic function that estimates the cost to reach the goal from a given state.

    Returns:
    - A list of Steps (actions) that form the path to the goal, if found.
    """
    frontier = PriorityQueue()
    frontier.put((0, initial_state))
    
    g_costs = {initial_state: 0}
    came_from = {}

    while not frontier.empty():
        _, current_state = frontier.get()
        
        if goal_test(current_state):
            return reconstruct_path(came_from, current_state)

        for next_state, action, cost in successors(current_state):
            new_g_cost = g_costs[current_state] + cost
            
            if next_state not in g_costs or new_g_cost < g_costs[next_state]:
                g_costs[next_state] = new_g_cost
                f_cost = new_g_cost + heuristic(next_state)
                frontier.put((f_cost, next_state))
                came_from[next_state] = (current_state, action)

    return []

def reconstruct_path(came_from, end_state):
    path = []
    current = end_state
    while current in came_from:
        previous, action = came_from[current]
        path.append(action)
        current = previous
    path.reverse()
    return path