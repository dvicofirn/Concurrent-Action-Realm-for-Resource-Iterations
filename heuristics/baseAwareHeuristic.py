from CARRI import Problem, State
from heuristics import Heuristic
class BaseAwareHeuristic(Heuristic):
    def __init__(self, problem: Problem):
        super().__init__(problem)
        self.problem = problem

    def evaluate(self, state: State):
        # Count the number of undelivered packages
        num_packages = self.problem.get_len_packages(state)

        # Count the number of pending requests
        num_requests = self.problem.get_len_requests(state)

        # Estimate the heuristic value
        # Here, we assume each package requires at least 2 actions (pick and deliver)
        # We can also consider the number of vehicles available
        num_vehicles = sum(len(self.problem.get_entity_ids(state, vehicle_type))
                           for vehicle_type in self.problem.vehicleEntities)

        # Heuristic value is based on the number of packages and requests
        # We can adjust weights as needed
        heuristic_value = (num_packages + num_requests) * 2 / max(num_vehicles, 1)

        return heuristic_value

