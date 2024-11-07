from CARRI.problem import Heuristic
class action_based_delivery_heuristic(Heuristic):
    def evaluate(self, state) -> float:
        """
        Heuristic estimating the minimum number of actions required to deliver all undelivered packages
        in a discrete environment. Focuses on counting actions rather than physical distances.
        
        :param state: The current state of the problem.
        :return: Estimated action count to complete all deliveries.
        """
        estimated_actions = 0

        #estimated_actions += 2 *  len(state.items[0])

        for e in state.items[1]:
            if e == 0:
                estimated_actions += 2
            else:
                estimated_actions += 1
        return estimated_actions

    def __call__(self, state):
    # Make the instance callable by delegating to the `evaluate` method
        return self.evaluate(state)

