from queue import PriorityQueue
from typing import Callable, List, Tuple, Dict
from CARRI.realm import State
from CARRI.action import Step
import time
from CARRI.simulator import Simulator

def greedy_best_first_search(simulator: Simulator,
                             heuristic: Callable[[State], float],
                             time_limit: float) -> Tuple[List[Step], State]:
    """
    Greedy Best-First Search algorithm using a heuristic.
    
    Args:
    - simulator: An instance of CARRISimulator to generate successors lazily.
    - heuristic: A heuristic function that estimates the cost to reach the goal from a given state.
    - time_limit: The maximum time allowed for this search.

    Returns:
    - A tuple of (List of Steps, final state). Returns the best partial solution found within the time limit.
    """
    start_time = time.time()
    open_set = PriorityQueue()
    open_set.put((heuristic(simulator.current_state), simulator.current_state))
    came_from: Dict[State, Tuple[State, Step]] = {}
    best_path = []

    while not open_set.empty() and (time.time() - start_time) < time_limit:
        _, current_state = open_set.get()

        if all_packages_delivered(current_state):
            return reconstruct_path(simulator, came_from, current_state), current_state

        for next_state, action, _ in simulator.generate_successors(current_state):
            if next_state not in came_from:
                came_from[next_state] = (current_state, action)
                open_set.put((heuristic(next_state), next_state))
                best_path = reconstruct_path(simulator, came_from, next_state)

    return best_path, current_state


def all_packages_delivered(state: State) -> bool:
    """
    Check if all packages have been delivered in the given state.
    :param state: The current state to check.
    :return: True if all packages are delivered, False otherwise.
    """
    # Assuming `state` has a method or attribute to check the status of packages
    return len(state.items[0]) == 0


def reconstruct_path(simulator, came_from: Dict[State, State], current: State) -> List[Step]:
    """
    Reconstructs the path from the start state to the given state.
    :param came_from: Dictionary that maps each state to its predecessor.
    :param current: The current state from which to reconstruct the path.
    :return: The sequence of steps (actions) leading to the given state.
    """
    total_path = []
    while current in came_from:
        previous, action = came_from[current]

        act = []
        for a in action:
            x = simulator.actionStringRepresentor.represent(a)
            act.append(x)

        total_path.insert(0, act)  # Prepend the action to the total path
        current = previous

    i = 0
    for t in total_path:
        print(f' {i}. {t}')
        i += 1
    return total_path