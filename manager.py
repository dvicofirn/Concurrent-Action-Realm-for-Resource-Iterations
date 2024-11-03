import time
from planner import Planner
from business import Business

class Manager:
    def __init__(self, simulator, iterations, init_time, iter_time, **planner_kwargs):
        """
        :param problem: An instance of CARRIProblem
        :param simulator: An instance of CARRISimulator
        :param init_time: float, maximum time for planner initiation
        :param iter_t: float, time limit per iteration for planning
        """
        self.init_time = init_time
        self.iter_time = iter_time
        self.business = Business(simulator, iterations)
        self.planner = Planner(init_time, iter_time, **planner_kwargs)

    def run(self):
        """
        Init the planner with problem, execute plan for each iteration.
        """
        start_time = time.time()
        self.planner.init_plan(self.simulator)
        end_time = time.time()
        if end_time - start_time > self.init_time:
            raise Exception("Init time limit exceeded")
        # Initiate plan iteration within the init time limit
        while self.business.canAdvance():
            self.execute_iteration()
        print("Executed plan with total cost of " + self.business.cost)

    def execute_iteration(self):
        """
        Calls Planner to generate and execute the plan, enforcing iteration timing constraints.
        """
        iteration_start = time.time()

        # Call generate_plan, respecting iteration time limit
        if time.time() - iteration_start > self.iter_time:
            plan = self.planner.generate_plan(self.business.getState())
            self.business.advanceIteration(plan) # Raises exception

        elapsed_time = time.time() - iteration_start
        if elapsed_time > self.iter_time:
            raise Exception('Iteration time limit exceeded')

