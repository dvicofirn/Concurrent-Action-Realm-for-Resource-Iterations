from CARRI import State
from .heuristic import Heuristic

class TimeSensitiveHeuristic(Heuristic):
    def heurist(self, state: State) -> int:
        # Prioritize requests with high urgency (lower values mean more urgent)
        total_urgency = sum(req.get("urgency", 0) for req in state.requests)
        return total_urgency  # Lower values are better (more urgent)
