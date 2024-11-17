from CARRI import State
from .heuristic import Heuristic

class TimeSensitiveGoalCountHeuristic(Heuristic):
    def heurist(self, state: State) -> int:
        return sum(req.get("urgency", 1) for req in state.requests if not req.is_satisfied())
