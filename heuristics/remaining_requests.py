from worldProblem import Heuristic, State

class RemainingRequestsHeuristic(Heuristic):
    def heurist(self, state: State) -> int:
        # Simple heuristic: count remaining requests
        return len(state.requests)
