from typing import List
from CARRI.simulator import Simulator
from CARRI.realm import Problem, State
class Business:
    def __init__(self, simulator, iterationsList: List):
        self.simulator = simulator
        self.iterationsList = iterationsList
        self.state = simulator.getState()
        self.iteration = 0
        self.cost = 0

    def getState(self):
        return self.state

    def getCost(self):
        return self.cost

    def getIteration(self):
        return self.iteration

    def canAdvance(self):
        return self.iteration < len(self.iterationsList)

    def advanceIteration(self, plan: List):
        """
        Advance business' state by Plan of transition actions.
        Then apply iteration step on state.
        return new state
        :param plan:
        :return:
        """
        state = self.state
        cost = self.cost
        # Advance state by each transition of actions.
        for i, transition in enumerate(plan):
            if not self.simulator.validateTransition(transition):
                raise Exception(
                    f"Transition no.{i} is invalid:"
                    f"\nState: {self.state}"
                    f"\nTransition: {[self.simulator.actionStringRepresentor.represent(action) for action in transition]}"
                )


            state, addCost = self.simulator.simulate(state, transition)
            cost += addCost

        # Add items to state.
        currentIterationList = self.iterationsList[self.iteration]
        for entityName in currentIterationList:
            state = self.simulator.addItems(entityName, currentIterationList[entityName])
        # Finalize
        self.state = state
        self.cost = cost
        return self.state
