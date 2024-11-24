from CARRI import Action, Simulator, State
from typing import Dict
from search import PartialAssigner
import time

class Planner:
    def __init__(self, simulator: Simulator, iterTime: float, transitionsPerIteration: int, **kwargs):
        """
        Base Planner class.

        :param simulator: An instance of CARRISimulator.
        :param iterTime: Time allowed for each iteration.
        :param transitionsPerIteration: Maximum plan length per iteration.
        """
        self.simulator = simulator
        self.iterTime = iterTime
        self.maxPlanLength = transitionsPerIteration
        self.kwargs = kwargs

    def generate_plan(self, state: State, returnDict: Dict):
        """
        Generate a plan within the time limit.

        Must be implemented by subclasses.
        """
        raise NotImplementedError("Must be implemented by subclasses")

class AssigningPlanner(Planner):
    def __init__(self, simulator: Simulator, iterTime: float, transitionsPerIteration: int, **kwargs):
        super().__init__(simulator, iterTime, transitionsPerIteration, **kwargs)
        self.partialAssigner = PartialAssigner(simulator, **kwargs)

    def generate_plan(self, state: State, planDict: Dict):
        self.startGenerateTime = time.time()
        # Generate a default plan with 'Wait' actions
        plan, cost = self.partialAssigner.provideTransitionsAndCost(state, steps=self.maxPlanLength)
        planDict['plan'] = plan
        self.planDict = planDict
        self.initCost = cost
        self._generate_plan(state)

    def _generate_plan(self, state: State):
        """
        Internal method to generate a plan.

        Must be implemented by subclasses.
        """
        raise NotImplementedError("Must be implemented by subclasses")
