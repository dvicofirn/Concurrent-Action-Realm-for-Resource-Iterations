from worldProblem import Heuristic, State

class OperatorCountingHeuristic(Heuristic):
    def __init__(self, operator_weights=1):
        self.operator_weights = operator_weights

    def evaluate(self, state: State) -> int:
        total_cost = 0
        
        #for transition in state.transitions:
         #   operator = transition.get('operator')
          #  total_cost += self.operator_weights.get(operator, 1)
        
        return total_cost
