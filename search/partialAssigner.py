from CARRI import Simulator, Problem, State
from random import randint
class PartialAssigner:
    def __init__(self, simulator: Simulator):
        self.simulator = simulator
        self.problem = simulator.problem
        self.vehicleTypes = self.problem.vehicleEntities
        self.vehicleIds = []
        for type in self.vehicleTypes:
            self.vehicleIds.append(self.problem.get_entity_ids(self.problem.initState, type))