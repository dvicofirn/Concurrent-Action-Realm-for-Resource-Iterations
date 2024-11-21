from typing import Callable, List, Tuple, Dict
import time
from .searchEngine import SearchEngine
from heuristics import AllCountHeuristic
from CARRI import Simulator, Problem, State, Step, EnvStep, Action
import time
from typing import List

class IDAStarSearch(SearchEngine):
    def __init__(self, simulator: Simulator, **kwargs):
        super().__init__(simulator, **kwargs)
        # Use the provided heuristic or a default
        simulatorClass = kwargs.get("heuristic", AllCountHeuristic)
        self.heuristic = simulatorClass(simulator.problem)
        # Max number of successors to consider at each node
        self.max_successors = kwargs.get('max_successors', 5)
        self.best_plan = None
        self.best_cost = float('inf')
        self.max_steps = None
        self.plan_dict = None

    def search(self, state: State, plan_dict: Dict, **kwargs):
        self.max_steps = kwargs.get('steps', 10)
        self.plan_dict = plan_dict

        # Initialize the bound with heuristic value
        bound = self.heuristic.evaluate(state)
        path = []

        while True:
            result = self._search(state, path, 0, bound)
            if result == float('inf'):
                # No better solution found within current bound
                break
            bound = result  # Increase bound for next iteration

    def _search(self, state, path: List[List[Action]], g: float, bound: float):
        f = g + self.heuristic.evaluate(state)
        if f > bound:
            return f  # Return the minimal f-value that exceeds the bound

        if len(path) >= self.max_steps:
            # Plan length constraint met
            if g < self.best_cost:
                self.best_cost = g
                self.best_plan = path.copy()
                # Update the planner's plan
                if self.plan_dict is not None:
                    self.plan_dict['plan'] = self.best_plan
            # Continue searching for better plans

        min_bound = float('inf')
        successors = self.simulator.generate_successors(state)
        if not successors:
            return float('inf')  # Dead-end reached

        # Evaluate successors and sort them
        successor_list = []
        for successor_state, actions, cost in successors:
            h = self.heuristic.evaluate(successor_state)
            total_cost = g + cost + h
            successor_list.append((successor_state, actions, cost, total_cost))

        # Sort successors by total estimated cost (g + h)
        successor_list.sort(key=lambda x: x[3])

        # Prune successors to consider only the best ones
        pruned_successors = successor_list[:self.max_successors]

        for successor_state, actions, cost, _ in pruned_successors:
            path.append(actions)
            temp = self._search(successor_state, path, g + cost, bound)
            if temp < min_bound:
                min_bound = temp
            path.pop()

        return min_bound





def ida_star_old(initial_state: State, goal_test: Callable[[State], bool],
             successors: Callable[[State], List[Tuple[State, Step, int]]],
             heuristic: Callable[[State], float]) -> List[Step]:
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
