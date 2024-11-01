from worldProblem import Heuristic, State

class HAddHeuristic(Heuristic):
    def heurist(self, state: State) -> int:
        total_cost = 0
        
        for request in state.requests:
            req_loc = request.get('loc')
            for vehicle in state.vehicles.values():
                veh_loc = vehicle.get('location')
                
                if veh_loc and req_loc:
                    cost = abs(veh_loc[0] - req_loc[0]) + abs(veh_loc[1] - req_loc[1])
                    total_cost += cost
        return total_cost
