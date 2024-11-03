from CARRI.realm import State, Heuristic

class RequestCountHeuristic(Heuristic):
    def evaluate(self, state: State) -> int:
        return self.problem.get_len_requests(state)