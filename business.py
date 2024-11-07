from typing import List
from CARRI.simulator import Simulator
from CARRI.problem import Problem, State
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
        #return self.iteration < len(self.iterationsList)
        #package_type = set([x[1] for x in self.state.items[0].values()])
        #request_type = set([x[0] for x in self.state.items[1].values()])

        return self.iteration < len(self.iterationsList) #or len(package_type.intersection(request_type)) !=0

    def advanceIteration(self, plan: List):
        """
        Advance business' state by Plan of transition actions.
        Then apply iteration step on state.
        return new state
        :param plan:
        :return:
        """
                        
        #for i, joint_action in enumerate(plan):
        #    print(f"{i}.[{[self.simulator.actionStringRepresentor.represent(a) for a in joint_action]}")
                
        state = self.state
        cost = self.cost
        # Advance state by each transition of actions.
        self.simulator.current_state = state.copy()
        for i, transition in enumerate(plan):
            if not self.simulator.validate_Transition(transition):
                raise Exception(
                    f"Transition no.{i} is invalid:"
                    f"\nState: {self.simulator.current_state}"
                    f"\nTransition: {[self.simulator.actionStringRepresentor.represent(action) for action in transition]}"
                )

            for action in transition: # updating cost and state
                cost += self.simulator.advance_state(action)

        # Add items to state.
        if self.iteration < len(self.iterationsList):
            currentIterationList = self.iterationsList[self.iteration] 

            for entityName in currentIterationList:
                state = self.simulator.addItems(entityName, currentIterationList[entityName])

        # Finalize
        self.state = self.simulator.current_state.copy()
        self.cost = cost

        #if self.iteration % 10 == 0:
        print(f'Iteration {self.iteration} ...')

        self.iteration += 1
