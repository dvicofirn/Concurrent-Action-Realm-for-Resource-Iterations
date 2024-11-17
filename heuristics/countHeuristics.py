from CARRI import Problem, State
from .heuristic import Heuristic

class RequestCountHeuristic(Heuristic):
    def evaluate(self, state: State) -> int:
        return self.problem.get_len_requests(state)

class AllCountHeuristic(Heuristic):

    def evaluate(self, state: State):
        # Use counts of packages and requests as heuristic components
        return self.problem.get_len_packages(state) + self.problem.get_len_requests(state)
