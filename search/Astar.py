from queue import PriorityQueue
from typing import Callable, List, Tuple
from CARRI.realm import State  # Assuming this manages the problem state
from CARRI.action import Step  # Assuming steps/actions are defined in this module
import time
import logging
from CARRIRealm import CARRIState  # Manages the problem state, containing relevant attributes of entities and their current status
from CARRIAction import Step  # Defines the possible actions or steps that can be taken in the problem domain
from CARRISimulator import CARRISimulator

def a_star_search(initial_state: CARRIState,
                  simulator: CARRISimulator,
                  heuristic: Callable[[CARRIState], float],
                  time_limit: float) -> Tuple[List[Step], CARRIState]:
    """
    A* search algorithm with flexible heuristic input.
    
    Args:
    - initial_state: The starting state of the problem.
    - simulator: An instance of CARRISimulator to generate successors.
    - heuristic: A heuristic function that estimates the cost to reach the goal from a given state.
    - time_limit: The maximum time allowed for this search.

    Returns:
    - A tuple of (List of Steps, final state). Returns the best partial solution found within the time limit.
    """
    start_time = time.time()
    frontier = PriorityQueue()
    frontier.put((0, initial_state))
    
    g_costs = {initial_state: 0}
    came_from = {}
    best_state = initial_state
    best_path = []

    while not frontier.empty() and (time.time() - start_time) < time_limit:
        _, current_state = frontier.get()
        
        if all_packages_delivered(current_state):  # Goal condition: all packages delivered
            return reconstruct_path(came_from, current_state), current_state

        for next_state, action, cost in simulator.generate_successor_states(current_state):
            new_g_cost = g_costs[current_state] + cost
            
            if next_state not in g_costs or new_g_cost < g_costs[next_state]:
                g_costs[next_state] = new_g_cost
                f_cost = new_g_cost + heuristic.evaluate(next_state)
                frontier.put((f_cost, next_state))
                came_from[next_state] = (current_state, action)

                # Update the best state and path if we find a better partial solution
                if heuristic.evaluate(next_state) < heuristic.evaluate(best_state):
                    best_state = next_state
                    best_path = reconstruct_path(came_from, next_state)

    logging.warning("A* search terminated without finding a complete solution within the time limit.")
    return best_path, best_state

def reconstruct_path(came_from, end_state):
    path = []
    current = end_state
    while current in came_from:
        previous, action = came_from[current]
        path.append(action)
        current = previous
    path.reverse()
    return path

def all_packages_delivered(state: CARRIState) -> bool:
    """
    Check if all packages have been delivered in the given state.
    :param state: The current state to check.
    :return: True if all packages are delivered, False otherwise.
    """
    # Assuming `state` has a method or attribute to check the status of packages
    #return state.get_len() == 0
    return False
