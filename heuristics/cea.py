from CARRI import Problem, State
from .heuristic import Heuristic
class ContextEnhancedAdditiveHeuristic(Heuristic):
    def heurist(self, state: State) -> int:
        total_cost = 0
        for request in state.requests:
            request_loc = request.get('loc')
            for vehicle in state.vehicles.values():
                veh_loc = vehicle.get('location')
                if veh_loc and request_loc:
                    cost = abs(veh_loc[0] - request_loc[0]) + abs(veh_loc[1] - request_loc[1])
                    if vehicle.get('charge', 10) > 5:  # Context: Only consider high-charge vehicles
                        total_cost += cost
        return total_cost
