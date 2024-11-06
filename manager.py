import time
from planner import Planner
from business import Business

class Manager:
    def __init__(self, simulator, iterations, iter_time, transitions_per_iteration, **planner_kwargs):
        """
        :param Simulator: Simulator object with problem object in it.
        :param Iterations: List of iterations, with objects to add in each one of them.
        :param Iter_time: Time per each iteration.
        :param Transitions_per_iteration: number of transitions per iteration.
        :param planner_kwargs: Additional data.
        """
        self.iter_time = iter_time
        self.business = Business(simulator, iterations)
        self.transitions_per_iteration = transitions_per_iteration
        self.planner = Planner(simulator, iter_time, transitions_per_iteration, **planner_kwargs)

    def run(self):
        while self.business.canAdvance():
            self.execute_iteration()
        print("Executed plan with total cost of " + self.business.cost)

    def execute_iteration(self):
        """
        Calls Planner to generate and execute the plan, enforcing iteration timing constraints.
        """
        start_time = time.time()
        plan = self.planner.run_iteration(self.business.getState())
        end_time = time.time()
        if end_time - start_time > self.iter_time:
            raise Exception("Iteration time limit exceeded")
        try:
            if len(plan) < self.transitions_per_iteration:
                raise Exception("Plan is too short")
            self.business.advanceIteration(plan[:self.transitions_per_iteration]) # Raises exception
        except:
            print('ERROR - no plan')

