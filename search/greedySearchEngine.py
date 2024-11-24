from .searchEngine import *
from .partialAssigner import PartialAssigner
from CARRI import Simulator, State
import random
from typing import List, Tuple
import time

class GreedySearchEngine(SearchEngine):
    def __init__(self, simulator: Simulator, **kwargs):
        super().__init__(simulator, **kwargs)
        self.maxSteps = kwargs.get('steps', 10)
        self.partialAssigner = kwargs.get('partialAssigner', PartialAssigner(simulator, **kwargs))
        self.best_avg_cost = float('inf')
        self.iterTime = kwargs.get('iterTime', 10)
        self.maxSearchSteps = kwargs.get('maxSearchSteps', self.maxSteps * 2)  # Limit maximum steps


    def search(self, state: State, planDict: Dict, **kwargs):
        startTime = kwargs.get('startTime', time.time())
        bestAvgCost = kwargs.get('bestCost', float('inf'))/self.maxSteps
        searchSteps = self.maxSteps
        while True:
            plan, cost = self.partialAssigner.provideTransitionsAndCost(state, steps=searchSteps,
                                                                        maxStates=max(searchSteps//2, 5))
            avgCost = cost/searchSteps
            if avgCost < bestAvgCost:
                bestAvgCost = avgCost
                planDict['plan'] = plan
                if time.time() - startTime > self.iterTime/5 and searchSteps < self.maxSearchSteps:
                    searchSteps += 1

