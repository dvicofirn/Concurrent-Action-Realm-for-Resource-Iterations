import time
import traceback
from planner import Planner
from business import Business
from genetic_planner import CARRIPlannerGA
import concurrent.futures

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
        #self.planner = Planner(simulator, init_time, iter_time, transitions_per_iteration, **planner_kwargs)
        self.genetic_planner = CARRIPlannerGA(simulator)
        self.total_plan = []



    def run(self):

        total_time = time.time()

        while self.business.canAdvance():
            self.execute_iteration()

        print('\nTotal Planning and Execution time : ', time.time() - total_time)
        print("Executed plan with total cost of " + str(self.business.cost))
        print('Total Plan Length:', len(self.total_plan))
        print('Plan :')

        self.print_plan()

    def print_plan(self):
        for i, joint_action in enumerate(self.total_plan):
            print(f"{i}.[{[self.business.simulator.actionStringRepresentor.represent(a) for a in joint_action]}")

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


        # Execute genetic planner with timeout
        plan = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self.genetic_planner.plan, self.business.getState(), self.iter_time, start_time)
            try:
                plan = future.result(timeout=self.iter_time)  # Get the plan, with a timeout
            except concurrent.futures.TimeoutError:
                future.cancel()  # Cancel the future if it times out
        if len(plan) == 0:
            plan = self.genetic_planner.plan_sequence

        self.total_plan.extend(plan)
        # Advance iteration with the plan
        try:
            self.business.advanceIteration(plan[:self.transitions_per_iteration])  # Execute the truncated plan
        except Exception as e:
            # Print the detailed error message if there's an issue with the plan execution
            print(f'ERROR - Issue with plan execution: {e}')
            traceback.print_exc()
            exit()
