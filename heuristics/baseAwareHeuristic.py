from CARRI import Problem, State
from heuristics import Heuristic
class BaseAwareHeuristic(Heuristic):
    def __init__(self, problem: Problem):
        super().__init__(problem)

        # Identify indices of base entities and variables
        self.package_indexes = problem.packagesIndexes  # Indices of package items
        self.vehicle_entities = problem.vehicleEntities  # Indices of vehicle entities
        self.location_var_names = problem.locationVarNames  # Variable names related to location
        self.vehicle_location_vars = self._get_vehicle_location_vars()

    def _get_vehicle_location_vars(self):
        # Get variable indices for vehicle locations
        vehicle_location_vars = {}
        for var_name in self.location_var_names:
            var_info = self.problem.variablesInfo.get(var_name, {})
            entity_type = var_info.get('entity')
            if entity_type in self.problem.entities:
                entity_index = self.problem.entities[entity_type][0]
                if entity_index in self.vehicle_entities:
                    var_index = self.problem.varPositions[var_name]
                    vehicle_location_vars[entity_index] = var_index
        return vehicle_location_vars

    def evaluate(self, state: State):
        heuristic_value = 0

        # Count undelivered packages
        num_packages = self.problem.get_len_packages(state)
        heuristic_value += num_packages * 2  # Weight for packages

        # Count pending requests
        num_requests = self.problem.get_len_requests(state)
        heuristic_value += num_requests * 3  # Weight for requests

        # Estimate minimal actions required based on vehicle capacities and locations
        minimal_actions = self._estimate_minimal_actions(state, num_packages)
        heuristic_value += minimal_actions

        return heuristic_value

    def _estimate_minimal_actions(self, state: State, num_packages: int):
        # Estimate minimal actions to deliver packages
        # Assumption: Each package requires at least 2 actions (pick and deliver)
        # Adjust based on vehicle capacities and locations

        actions_needed = 0

        # Get vehicle locations
        vehicle_locations = []
        for entity_index, var_index in self.vehicle_location_vars.items():
            locations = state.variables[var_index]
            vehicle_locations.extend(locations)

        # Assume that if a vehicle is at the same location as a package or request,
        # it can act immediately; otherwise, it needs to move there.

        # For simplicity, we'll assume each vehicle can deliver one package at a time
        # and ignore distances (since we lack adjacency data)

        # Number of packages that can be potentially picked up immediately
        potential_pickups = 0
        for package_index in self.package_indexes:
            for package_id in state.get_items_ids(package_index):
                package_location = self._get_item_location(state, package_index, package_id)
                if package_location in vehicle_locations:
                    potential_pickups += 1

        # Remaining packages require movement
        remaining_packages = num_packages - potential_pickups

        # Each package requires at least 2 actions
        actions_needed += num_packages * 2

        # Additional actions for moving to packages
        actions_needed += remaining_packages  # Assume 1 move action per package

        return actions_needed

    def _get_item_location(self, state: State, item_index: int, item_id: int):
        # Get the location of an item (package or request)
        item_keys = self.problem.itemsKeysNames[self.problem.entitiesReversed[item_index][0]]
        loc_key_index = item_keys.index('loc')
        return state.get_item_value(item_index, loc_key_index, item_id)
