from typing import Callable, List, Tuple
import time
from .searchEngine import SearchEngine
from heuristics import AllCountHeuristic
from CARRI import Simulator, Problem, State, Step, EnvStep, Action
import time
from typing import List

class IDAStarSearch(SearchEngine):
    def __init__(self, simulator: Simulator, **kwargs):
        super().__init__(simulator, **kwargs)
        self.heuristic = kwargs.get("heuristic", AllCountHeuristic(simulator.problem))

    def search(self, state: State, **kwargs) -> List[List[Action]]:
        steps = kwargs.get('steps', 10)
        iterTime = kwargs.get('iterTime', steps * 5)
        start_time = time.time()
        bound = float('inf')  # Set initial bound to infinity
        path = []
        self.best_path = None
        self.max_steps = steps

        while True:
            result = self._search(state, path, 0, bound, start_time, iterTime)
            if isinstance(result, list):
                return result
            if (time.time() - start_time) >= iterTime:
                # Time limit exceeded, return the best path found so far
                if self.best_path:
                    return self.best_path
                else:
                    return []  # No plan found
            bound = result

    def _search(self, state, path: List[List[Action]], g: float, bound: float, start_time: float, iterTime: float):
        if (time.time() - start_time) >= iterTime:
            return float('inf')
        if len(path) >= self.max_steps:
            # Plan length constraint met
            if not self.best_path or g < self.best_cost:
                self.best_path = path.copy()
                self.best_cost = g
            return g
        f = g + self.heuristic.evaluate(state)
        if f > bound:
            return f
        min_cost = float('inf')
        successors = self.simulator.generate_successors(state)
        if not successors:
            # No successors, possibly a dead-end
            return f
        for successor_state, actions, cost in successors:
            path.append(actions)
            t = self._search(successor_state, path, g + cost, bound, start_time, iterTime)
            if isinstance(t, float):
                if t < min_cost:
                    min_cost = t
            path.pop()
        return min_cost



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
