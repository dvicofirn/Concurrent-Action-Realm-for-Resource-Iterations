from worldProblem import Heuristic, State

class HMaxHeuristic(Heuristic):
    def heurist(self, state: State) -> int:
        # Compute the maximum cost among all sub-goals.
        max_cost = 0
        for request in state.requests:
            for vehicle in state.vehicles.values():
                cost = abs(vehicle['location'][0] - request['loc'][0]) + \
                       abs(vehicle['location'][1] - request['loc'][1])
                max_cost = max(max_cost, cost)

        return max_cost
