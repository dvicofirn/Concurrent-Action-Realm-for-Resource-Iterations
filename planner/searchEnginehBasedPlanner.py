from planner import Planner
from search import PartialAssigner, IDAStarSearch
from CARRI import Simulator, State, Action
import time
from typing import List
import logging

class SearchEngineBasedPlanner(Planner):
    def __init__(self, simulator: Simulator, iterTime: int, transitionsPerIteration: int, **kwargs):
        super().__init__(simulator, iterTime, transitionsPerIteration, **kwargs)
        # Use the provided search algorithm (default is IDAStarSearch)
        searchAlgorithm = kwargs.get('searchAlgorithm', IDAStarSearch)
        self.searchEngine = searchAlgorithm(simulator, **kwargs)

    def generate_plan(self, state: State, returnDict):
        self.startGenerateTime = time.time()
        # Generate a default plan with 'Wait' actions
        returnDict['plan'] = self._generate_default_plan(state)
        self.returnDict = returnDict
        self._generate_plan(state)

    def _generate_plan(self, state: State):
        try:
            # Start generating the plan using the search engine
            plan = self.searchEngine.search(state, steps=self.maxPlanLength)
            self.returnDict['plan'] = plan  # Update the plan if successful
        except Exception as e:
            logging.error(f"Error during planning: {e}", exc_info=True)
            # Keep the default plan if an error occurs

    def _generate_default_plan(self, state: State) -> List[List[Action]]:
        return PartialAssigner(self.simulator).search(state, steps=self.maxPlanLength)
