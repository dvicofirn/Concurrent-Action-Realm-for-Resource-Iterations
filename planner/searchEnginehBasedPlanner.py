from .planner import *
from search import UCTSearchEngine

class SearchEngineBasedPlanner(AssigningPlanner):
    def __init__(self, simulator: Simulator, iterTime: float, transitionsPerIteration: int, **kwargs):
        super().__init__(simulator, iterTime, transitionsPerIteration, **kwargs)
        # Use the provided search algorithm (default is UCTSearchEngine)
        searchAlgorithm = kwargs.get('searchAlgorithm', UCTSearchEngine)
        self.searchEngine = searchAlgorithm(simulator, **kwargs)

    def _generate_plan(self, state: State):
        self.searchEngine.search(
            state,
            plan_dict=self.returnDict,  # Pass the plan dictionary directly
            steps=self.maxPlanLength,
            partial_assigner=self.partialAssigner,
            startGenerateTime=self.startGenerateTime,
            **self.kwargs
        )
