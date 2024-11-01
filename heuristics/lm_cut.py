from worldProblem import Heuristic, State

class LMCutHeuristic(Heuristic):
    def heurist(self, state: State) -> int:
        total_cost = 0
        landmarks = []
        
        for request in state.requests:
            if request.get('urgency', 0) < 3:
                landmarks.append(request)
        
        for landmark in landmarks:
            req_loc = landmark.get('loc')
            min_cost = float('inf')
            
            for vehicle in state.vehicles.values():
                veh_loc = vehicle.get('location')
                if veh_loc and req_loc:
                    cost = abs(veh_loc[0] - req_loc[0]) + abs(veh_loc[1] - req_loc[1])
                    min_cost = min(min_cost, cost)
                    
            total_cost += min_cost
        return total_cost
