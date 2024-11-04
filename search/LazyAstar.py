from queue import PriorityQueue
from typing import Callable, List, Tuple, Dict
from CARRI.realm import State
from CARRI.action import Step
import time
from CARRI.simulator import Simulator

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

def lazy_a_star_search(simulator: Simulator,
                       heuristic: Callable[[State], float],
                       time_limit: float) -> Tuple[List[Step], State]:
    """
    Lazy A* search algorithm with flexible heuristic input.
    
    Args:
    - simulator: An instance of CARRISimulator to generate successors lazily.
    - heuristic: A heuristic function that estimates the cost to reach the goal from a given state.
    - time_limit: The maximum time allowed for this search.

    Returns:
    - A tuple of (List of Steps, final state). Returns the best partial solution found within the time limit.
    """
    start_time = time.time()

    # The open set containing discovered nodes that may need to be (re-)expanded
    open_set = PriorityQueue()
    open_set.put((heuristic(simulator.current_state), simulator.current_state))

    # Dictionary to reconstruct the path
    came_from: Dict[State, Tuple[State, Step]] = {}

    # Cost from start to a given node
    g_score = {simulator.current_state: 0}

    # Priority values for tracking the f_scores
    f_score = {simulator.current_state: heuristic(simulator.current_state)}

    best_state = simulator.current_state
    best_path = []

    while not open_set.empty() and (time.time() - start_time) < time_limit:
        # Get the node from open set with the lowest f_score value
        _, current_state = open_set.get()

        # Check if we reached the goal state
        if all_packages_delivered(current_state):
            return reconstruct_path(simulator, came_from, current_state), current_state

        # Generate successors of the current state lazily, only when current_state is expanded
        for next_state, action, cost in simulator.generate_successors(current_state):
            tentative_g_score = g_score[current_state] + cost

            # If we found a better path to the next_state
            if next_state not in g_score or tentative_g_score < g_score[next_state]:
                came_from[next_state] = (current_state, action)
                g_score[next_state] = tentative_g_score
                f_score[next_state] = tentative_g_score + heuristic.evaluate(next_state)

                # Add next_state to the open set if it is not already there
                if next_state not in [item[1] for item in open_set.queue]:
                    open_set.put((f_score[next_state], next_state))

                # Track the best partial solution
                best_state = next_state
                best_path = reconstruct_path(simulator, came_from, next_state)

        # Print the partial solution found so far
        print("\n\nPartial solution so far:")
        reconstruct_path(simulator, came_from, current_state)

    # If the search ends without finding the goal, return the best partial solution
    return best_path, best_state

def all_packages_delivered(state: State) -> bool:
    """
    Check if all packages have been delivered in the given state.
    :param state: The current state to check.
    :return: True if all packages are delivered, False otherwise.
    """
    # Assuming `state` has a method or attribute to check the status of packages
    return len(state.items[0]) == 0

