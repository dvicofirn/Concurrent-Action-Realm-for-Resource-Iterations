from typing import List
from CARRI import Simulator, Problem, State, Action
class Business:
    def __init__(self, simulator: Simulator, iterationsList: List):
        self.simulator = simulator#.__copy__()
        self.iterationsList = iterationsList
        self.state = simulator.get_state()
        self.iteration = 0
        self.cost = 0

    def __str__(self) -> str:
        return (f"Iteration: {self.iteration}\n"
                + self.simulator.problem.representState(self.state)
                + f"Cost: {self.cost}")

    def __repr__(self) -> str:
        return self.__str__()

    def getState(self) -> State:
        return self.state.__copy__()

    def getCost(self) -> int:
        return self.cost

    def getIteration(self) -> int:
        return self.iteration

    def canAdvance(self):
        #return self.iteration < len(self.iterationsList)
        #package_type = set([x[1] for x in self.state.items[0].values()])
        #request_type = set([x[0] for x in self.state.items[1].values()])

        return len(package_type.intersection(request_type)) !=0

    def canAdvanceIteration(self) -> bool:
        return self.iteration < len(self.iterationsList)

    def advanceIteration(self, plan: List[List[Action]]) -> None:
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
            if not self.simulator.validate_Transition(state, transition):
                raise Exception(
                    f"Transition no. {i} is invalid:"
                    f"\nState: {self.simulator.current_state}"
                    f"\nTransition: {[self.simulator.actionStringRepresentor.represent(action) for action in transition]}"
                )
            state, cost = self.simulator.apply_full_Transition(state, cost, transition)

        currentIterationItems = self.iterationsList[self.iteration]


        self.simulator.apply_iter_step(state, currentIterationItems)

        # Finalize
        self.state = state
        self.cost = cost

        self.iteration += 1
