from queue import PriorityQueue
from typing import Callable, List, Tuple
from CARRI.realm import State  # Assuming this manages the problem state
from CARRI.action import Step  # Assuming steps/actions are defined in this module
import time
import logging

def a_star_search(initial_state: State,
                  successors: Callable[[State], List[Tuple[State, Step, int]]],
                  heuristic: Callable[[State], float],
                  cost_function: Callable[[State], float],
                  time_limit: float) -> Tuple[List[Step], State]:
    """
    A* search algorithm with flexible heuristic and cost function input.
    
    Args:
    - initial_state: The starting state of the problem.
    - successors: A function that returns a list of successor states for a given state, 
                  along with the action (Step) that leads to them and the cost.
    - heuristic: A heuristic function that estimates the cost to reach the goal from a given state.
    - cost_function: A function to evaluate the reward or cost of a given state.
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
        
        if cost_function(current_state) == 0:  # Assume zero cost represents an ideal goal condition
            return reconstruct_path(came_from, current_state), current_state

        for next_state, action, cost in successors(current_state):
            new_g_cost = g_costs[current_state] + cost
            
            if next_state not in g_costs or new_g_cost < g_costs[next_state]:
                g_costs[next_state] = new_g_cost
                f_cost = new_g_cost + heuristic(next_state)
                frontier.put((f_cost, next_state))
                came_from[next_state] = (current_state, action)

                # Update the best state and path if we find a better partial solution
                if heuristic(next_state) < heuristic(best_state):
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

class AStarSearch:
    def __init__(self, initial_state: State,
                 successors: Callable[[State], List[Tuple[State, Step, int]]],
                 heuristic: Callable[[State], float],
                 cost_function: Callable[[State], float]):
        self.initial_state = initial_state
        self.successors = successors
        self.heuristic = heuristic
        self.cost_function = cost_function

    def search(self, remaining_time: float) -> Tuple[List[Step], State]:
        """
        Execute the A* search within the remaining time limit.
        :param remaining_time: Time allowed to perform the search.
        :return: Tuple of (actions leading to the goal, final state) if a solution is found, otherwise the best partial plan found.
        """
        start_time = time.time()
        frontier = PriorityQueue()
        frontier.put((0, self.initial_state))

        g_costs = {self.initial_state: 0}
        came_from = {}
        best_state = self.initial_state
        best_path = []

        while not frontier.empty() and (time.time() - start_time) < remaining_time:
            _, current_state = frontier.get()

            if self.cost_function(current_state) == 0:  # Assume zero cost represents an ideal goal condition
                return reconstruct_path(came_from, current_state), current_state

            for next_state, action, cost in self.successors(current_state):
                new_g_cost = g_costs[current_state] + cost

                if next_state not in g_costs or new_g_cost < g_costs[next_state]:
                    g_costs[next_state] = new_g_cost
                    f_cost = new_g_cost + self.heuristic(next_state)
                    frontier.put((f_cost, next_state))
                    came_from[next_state] = (current_state, action)

                    # Update the best state and path if we find a better partial solution
                    if self.heuristic(next_state) < self.heuristic(best_state):
                        best_state = next_state
                        best_path = reconstruct_path(came_from, next_state)

        # If time limit is exceeded or frontier is empty without finding a complete solution
        logging.warning("A* search terminated without finding a complete solution within the time limit.")
        return best_path, best_state
