from CARRI import Action, Simulator, State
from typing import List


class Planner:
    def __init__(self, simulator: Simulator, iterTime: int, transitionsPerIteration: int, **kwargs):
        """
        :param simulator: An instance of CARRISimulator
        :param iterTime: float, time allowed for each iteration
        :param transitionsPerIteration: int, maximum plan length per iteration
        """
        self.simulator = simulator
        self.iterTime = iterTime
        self.maxPlanLength = transitionsPerIteration

    def generate_plan(self, state: State, return_dict):
        """
        Generate a plan within the time limit using the provided search algorithm and heuristic (if needed).
        """
        raise NotImplementedError("Must be implemented by subclasses")





