from CARRI import Action, Simulator, State
from typing import Dict
from search import PartialAssigner
import time


class Planner:
    def __init__(self, simulator: Simulator, iterTime: float, transitionsPerIteration: int, **kwargs):
        """
        :param simulator: An instance of CARRISimulator
        :param iterTime: float, time allowed for each iteration
        :param transitionsPerIteration: int, maximum plan length per iteration
        """
        self.simulator = simulator
        self.iterTime = iterTime
        self.maxPlanLength = transitionsPerIteration
        self.kwargs = kwargs


    def generate_plan(self, state: State, returnDict: Dict):
        """
        Generate a plan within the time limit using the provided search algorithm and heuristic (if needed).
        """
        raise NotImplementedError("Must be implemented by subclasses")

class AssigningPlanner(Planner):
    def __init__(self, simulator: Simulator, iterTime: float, transitionsPerIteration: int, **kwargs):
        super().__init__(simulator, iterTime, transitionsPerIteration, **kwargs)
        self.partialAssigner = PartialAssigner(simulator, **kwargs)

    def generate_plan(self, state: State, returnDict: Dict):
        self.startGenerateTime = time.time()
        # Generate a default plan with 'Wait' actions
        plan, cost = self.partialAssigner.provideTransitionsAndCost(state, steps=self.maxPlanLength)
        returnDict['plan'] = plan
        self.returnDict = returnDict
        self.initCost = cost
        self._generate_plan(state)

    def _generate_plan(self, state: State):
        raise NotImplementedError("Must be implemented by subclasses")





