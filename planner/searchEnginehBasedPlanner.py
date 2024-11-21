from planner import Planner
from search import PartialAssigner, IDAStarSearch
from CARRI import Simulator, State, Action
import time
from typing import List
import logging

class SearchEngineBasedPlanner(Planner):
    def __init__(self, simulator: Simulator, iterTime: float, transitionsPerIteration: int, **kwargs):
        super().__init__(simulator, iterTime, transitionsPerIteration, **kwargs)
        # Use the provided search algorithm (default is IDAStarSearch)
        searchAlgorithm = kwargs.get('searchAlgorithm', IDAStarSearch)
        self.searchEngine = searchAlgorithm(simulator, **kwargs)
        self.partialAssigner = PartialAssigner(simulator, **kwargs)

    def generate_plan(self, state: State, returnDict):
        self.startGenerateTime = time.time()
        # Generate a default plan with 'Wait' actions
        plan, cost = self.partialAssigner.provideTransitionsAndCost(state, steps=self.maxPlanLength)
        returnDict['plan'] = plan
        self.returnDict = returnDict
        self.initCost = cost
        self._generate_plan(state)

    def _generate_plan(self, state: State):
        self.searchEngine.search(
            state,
            steps=self.maxPlanLength,
            plan_dict=self.returnDict,  # Pass the plan dictionary directly
            partial_assigner=self.partialAssigner
        )
