from worldProblem import Heuristic, State

class GoalCountHeuristic(Heuristic):
    def heurist(self, state: State) -> int:
        # Counts the number of unmet goals for a given state
        unsatisfied_goals = sum(1 for req in state.requests if not req.is_satisfied())
        return unsatisfied_goals
