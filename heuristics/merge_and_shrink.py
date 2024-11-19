from CARRI import State
from .heuristic import Heuristic

class MergeAndShrinkHeuristic(Heuristic):
    def heurist(self, state: State) -> int:
        total_cost = 0
        
        for request in state.requests:
            req_loc = request.get('loc')
            for vehicle in state.vehicles.values():
                veh_loc = vehicle.get('location')
                charge = vehicle.get('charge', 0)
                
                if veh_loc and req_loc:
                    cost = abs(veh_loc[0] - req_loc[0]) + abs(veh_loc[1] - req_loc[1])
                    total_cost += cost + max(0, 10 - charge)  # Adds penalty if charge is low
        return total_cost
