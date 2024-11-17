from CARRI import State
from .heuristic import Heuristic

class RemainingRequestsHeuristic(Heuristic):
    def heurist(self, state: State) -> int:
        # Simple heuristic: count remaining requests
        return len(state.requests)
