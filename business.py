from typing import List
from CARRI import Simulator, State, Action

class Business:
    def __init__(self, simulator: Simulator, iterationsList: List):
        # Initialize the business with a simulator and a list of iterations
        self.simulator = simulator  # Simulator instance
        self.iterationsList = iterationsList  # List of iteration items
        self.state = simulator.get_state()  # Current state of the business
        self.iteration = 0  # Current iteration count
        self.cost = 0  # Total cost incurred

    def __str__(self) -> str:
        # String representation of the business state
        return (f"Iteration: {self.iteration}\n"
                + self.simulator.problem.representState(self.state)
                + f"Cost: {self.cost}")

    def __repr__(self) -> str:
        # Representation method for printing
        return self.__str__()

    def getState(self) -> State:
        # Return a copy of the current state
        return self.state.__copy__()

    def getCost(self) -> int:
        # Return the total cost
        return self.cost

    def getIteration(self) -> int:
        # Return the current iteration number
        return self.iteration

    def canAdvanceIteration(self) -> bool:
        # Check if more iterations are available
        return self.iteration <= len(self.iterationsList)

    def advanceIteration(self, plan: List[List[Action]]) -> None:
        """
        Advance the business state by applying a plan of transition actions.
        Then apply the iteration step on the state.

        :param plan: List of transitions, where each transition is a list of actions.
        """
        state = self.state
        cost = self.cost
        # Apply each transition in the plan
        for i, transition in enumerate(plan):
            if not self.simulator.validate_Transition(state, transition):
                raise Exception(
                    f"Transition no. {i} is invalid:"
                    f"\nState: {self.simulator.current_state}"
                    f"\nTransition: {[self.simulator.actionStringRepresentor.represent(action) for action in transition]}"
                )
            # Apply the full transition and update cost
            state, cost = self.simulator.apply_full_transition(state, cost, transition)

        if self.iteration < len(self.iterationsList):
            # Apply iteration items if available
            currentIterationItems = self.iterationsList[self.iteration]
            self.simulator.apply_iter_step(state, currentIterationItems)

        # Update the state, cost, and iteration count
        self.state = state
        self.cost = cost
        self.iteration += 1
