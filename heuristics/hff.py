from CARRI import State
from .heuristic import Heuristic

class HFFHeuristic(Heuristic):
    """
    Not tested
    """
    def heurist(self, state: State) -> int:
        total_cost = 0
        for request in state.requests:
            req_loc = request.get('loc')
            min_cost = float('inf')
            
            for vehicle in state.vehicles.values():
                veh_loc = vehicle.get('location')
                if veh_loc and req_loc:
                    cost = abs(veh_loc[0] - req_loc[0]) + abs(veh_loc[1] - req_loc[1])
                    min_cost = min(min_cost, cost)
                    
            total_cost += min_cost
        return total_cost
