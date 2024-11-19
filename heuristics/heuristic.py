from CARRI import Problem, State
class Heuristic:
    def __init__(self, problem: Problem):
        self.problem = problem

    def evaluate(self, state: State):
        raise NotImplementedError("Must be implemented by subclasses")