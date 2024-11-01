from worldProblem import Heuristic, State

class MaxPairwiseDistanceHeuristic(Heuristic):
    def heurist(self, state: State) -> int:
        max_distance = 0
        for req in state.requests:
            req_loc = req.get('loc')
            for vehicle in state.vehicles.values():
                veh_loc = vehicle.get('location')
                if req_loc and veh_loc:
                    distance = abs(veh_loc[0] - req_loc[0]) + abs(veh_loc[1] - req_loc[1])
                    max_distance = max(max_distance, distance)
        return max_distance
