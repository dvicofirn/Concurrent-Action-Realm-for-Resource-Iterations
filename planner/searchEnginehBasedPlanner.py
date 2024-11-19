from planner import Planner
from search import PartialAssigner
from CARRI import Simulator, State, Action
from typing import List
import logging
class SearchEnginehBasedPlanner(Planner):

    def __init__(self, simulator: Simulator, iterTime: int, transitionsPerIteration: int, **kwargs):
        """
        :param simulator: An instance of CARRISimulator
        :param iterTime: float, time allowed for each iteration
        :param transitionsPerIteration: int, maximum plan length per iteration
        """
        super().__init__(simulator, iterTime, transitionsPerIteration, **kwargs)
        # Store the search algorithm as a reference, not an instance
        searchAlgorithm = kwargs.get('searchAlgorithm', PartialAssigner)
        self.searchEngine = searchAlgorithm(simulator, **kwargs)

    def generate_plan(self, state: State) -> List[List[Action]]:
        """
        Generate a plan within the time limit using the provided search algorithm and heuristic.
        :return: A list representing the plan (sequence of actions).
        """
        try:
            # Initialize the search algorithm here
            plan = self.searchEngine.search(state, steps=round(self.maxPlanLength * 1.5),
                                            maxStates=self.maxPlanLength * 10,
                                            iterTime = self.iterTime - 5)
            return plan

        except Exception as e:
            logging.error(f"Error during planning: {e}", exc_info=True)