import time
from planner import Planner, SearcEnginehBasedPlanner
from business import Business
from search import PartialAssigner
from CARRI import Simulator

class Manager:
    def __init__(self, simulator: Simulator, iterations, iterTime: int, transitionsPerIteration, **kwargs):
        """
        :param problem: An instance of CARRIProblem
        :param simulator: An instance of CARRISimulator
        :param init_time: float, maximum time for planner initiation
        :param iter_t: float, time limit per iteration for planning
        """
        self.iterTime = iterTime
        self.business = Business(simulator, iterations)
        self.transitionsPerIteration = transitionsPerIteration
        searchAlgorithm = kwargs.get('searchAlgorithm', PartialAssigner)
        self.planner = SearcEnginehBasedPlanner(simulator, iterTime,transitionsPerIteration, searchAlgorithm=searchAlgorithm)
        #self.planner = Planner(simulator, init_time, iter_time, transitions_per_iteration, **kwargs)

    def run(self):
        print(f"Start")
        print(self.business)
        print("----------")
        while self.business.canAdvanceIteration():
            self.execute_iteration()
            print(self.business)
            print("----------")
        print("Executed plan with total cost of " + str(self.business.getCost()))

    def execute_iteration(self):
        """
        Calls Planner to generate and execute the plan, enforcing iteration timing constraints.
        """
        iteration_start = time.time()

        # Call generate_plan, respecting iteration time limit
        start_time = time.time()
        plan = self.planner.generate_plan(self.business.getState())
        end_time = time.time()
        if end_time - start_time > self.iterTime:
            raise Exception("Iteration time limit exceeded")

        if len(plan) < self.transitionsPerIteration:
            raise Exception("Plan is too short")

        try:
            self.business.advanceIteration(plan[:self.transitionsPerIteration]) # Raises exception
        except Exception as e:
            print(e)

