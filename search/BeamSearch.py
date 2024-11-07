from queue import PriorityQueue
from typing import Callable, List, Tuple, Dict
from CARRI.problem import State  # Assuming this manages the problem state
from CARRI.action import Step  # Assuming steps/actions are defined in this module
import time
import logging
from CARRI.simulator import Simulator

def beam_search(simulator: Simulator,
                heuristic: Callable[[State], float],
                time_limit: float,
                beam_width: int = 3) -> Tuple[List[Step], State]:
    """
    Beam Search algorithm using a heuristic.
    
    Args:
    - simulator: An instance of CARRISimulator to generate successors lazily.
    - heuristic: A heuristic function that estimates the cost to reach the goal from a given state.
    - time_limit: The maximum time allowed for this search.
    - beam_width: The number of nodes to keep at each level.

    Returns:
    - A tuple of (List of Steps, final state). Returns the best solution found within the time limit.
    """
    start_time = time.time()
    current_level = [(simulator.current_state, [])]  # List of (state, path) tuples

    while (time.time() - start_time) < time_limit and current_level:
        next_level = []

        for state, path in current_level:
            if all_packages_delivered(state):
                return path, state

            for next_state, action, _ in simulator.generate_successors(state):
                new_path = path + [action]
                next_level.append((next_state, new_path))

        # Keep only the best beam_width nodes
        next_level = sorted(next_level, key=lambda x: heuristic(x[0]))[:beam_width]
        current_level = next_level

    # Return the best partial solution found
    if current_level:
        best_state, best_path = min(current_level, key=lambda x: heuristic(x[0]))
        return best_path, best_state
    else:
        return [], simulator.current_state


def all_packages_delivered(state: State) -> bool:
    """
    Check if all packages have been delivered in the given state.
    :param state: The current state to check.
    :return: True if all packages are delivered, False otherwise.
    """
    # Assuming `state` has a method or attribute to check the status of packages
    return len(state.items[0]) == 0
