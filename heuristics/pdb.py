from CARRI import State
from .heuristic import Heuristic

class PatternDatabaseHeuristic(Heuristic):
    """
    Not tested
    """
    def __init__(self, pattern_db):
        self.pattern_db = pattern_db

    def heurist(self, state: State) -> int:
        total_cost = 0
        
        for request in state.requests:
            req_loc = request.get('loc')
            for vehicle in state.vehicles.values():
                veh_loc = vehicle.get('location')
                
                if veh_loc and req_loc:
                    pattern_cost = self.pattern_db.get((veh_loc, req_loc), 0)
                    total_cost += pattern_cost
        return total_cost
