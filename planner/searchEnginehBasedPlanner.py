from .planner import *
from search import UCTSearchEngine

class SearchEngineBasedPlanner(AssigningPlanner):
    def __init__(self, simulator: Simulator, iterTime: float, transitionsPerIteration: int, **kwargs):
        super().__init__(simulator, iterTime, transitionsPerIteration, **kwargs)
        # Use the provided search algorithm (default is UCTSearchEngine)
        searchAlgorithm = kwargs.get('searchAlgorithm', UCTSearchEngine)
        self.searchEngine = searchAlgorithm(simulator, steps=self.maxPlanLength, iterTime=self.iterTime, partialAssigner=self.partialAssigner, **kwargs)

    def _generate_plan(self, state: State):
        self.searchEngine.search(
            state,
            planDict=self.planDict,
            startTime=self.startGenerateTime,
            cost=self.initCost,
            **self.kwargs
        )
