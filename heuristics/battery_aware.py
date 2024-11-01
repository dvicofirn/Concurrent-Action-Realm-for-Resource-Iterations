from worldProblem import Heuristic, State

class BatteryAwareHeuristic(Heuristic):
    def heurist(self, state: State) -> int:
        total_cost = 0
        for vehicle in state.vehicles.values():
            if vehicle.get('type') == 'drone':
                charge = vehicle.get('charge', 10)
                total_cost += max(0, 10 - charge) * 5  # Penalize low battery heavily
        return total_cost
