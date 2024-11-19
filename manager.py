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

import time
import traceback
from business import Business
from genetic_planner import CARRIPlannerGA
import concurrent.futures
import time
from planner import Planner, SearchEngineBasedPlanner, GeneticPlanner, RoutingPlanner
from business import Business
from search import PartialAssigner
from CARRI import Simulator

class Manager:
    def __init__(self, simulator: Simulator, iterations, iterTime: int, transitionsPerIteration, **planner_kwargs):
        """
        :param Simulator: Simulator object with problem object in it.
        :param Iterations: List of iterations, with objects to add in each one of them.
        :param Iter_time: Time per each iteration.
        :param Transitions_per_iteration: number of transitions per iteration.
        :param planner_kwargs: Additional data.
        """
        self.iterTime = iterTime
        self.business = Business(simulator, iterations)
        self.transitionsPerIteration = transitionsPerIteration
        #self.planner = Planner(simulator, init_time, iter_time, transitions_per_iteration, **planner_kwargs)
        self.planner = GeneticPlanner(simulator, iterTime, transitionsPerIteration, PartialAssigner)
        #self.planner = SearchEngineBasedPlanner(simulator, iterTime, transitionsPerIteration, PartialAssigner)
        #self.planner = RoutingPlanner(simulator, iterTime, transitionsPerIteration, PartialAssigner)
        self.total_plan = []



    def run(self):

        total_time = time.time()

        print(f"Start")
        print(f"current {self.business.getState()}")
        print(f"current score {self.business.getCost()}")
        print("----------")
        iterationCount = 1
        while self.business.canAdvanceIteration():
            self.execute_iteration()
            #self.execute_iteration_gen()
            print(f"Iteration {iterationCount}:")
            print(f"current {self.business.getState()}")
            print(f"current score {self.business.getCost()}")
            print("----------")
            iterationCount += 1
        print("Executed plan with total cost of " + str(self.business.getCost()))


        pick_count, deliver_count = self.count_pick_deliver()

        print('\nTotal Planning and Execution time : ', time.time() - total_time)
        print("Executed plan with total cost of " + str(self.business.cost))
        print('Total Plan Length:', len(self.total_plan))
        print("Total 'Pick' count:", pick_count)
        print("Total 'Deliver' count:", deliver_count)
        print('Plan :')

        self.print_plan()

    def print_plan(self):
        for i, joint_action in enumerate(self.total_plan):
            print(f"{i}.[{[self.business.simulator.actionStringRepresentor.represent(a) for a in joint_action]}")


    def execute_iteration(self):
        plan = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self.planner.generate_plan, self.business.getState())
            try:
                plan = future.result(timeout=self.iterTime)
            except concurrent.futures.TimeoutError:
                future.cancel()

        plan = self.planner.plan_sequence

        self.total_plan.extend(plan[:self.transitionsPerIteration])

        #if len(plan) < self.transitionsPerIteration:
        #    raise Exception("Plan is too short")

        try:
            self.business.advanceIteration(plan[:self.transitionsPerIteration])
        except Exception as e:
            print(f'ERROR - Issue with plan execution: {e}')
            traceback.print_exc()
            exit()

    def count_pick_deliver(self):
        pick_count, deliver_count = 0, 0
        for joint_action in self.total_plan:
            actions = [self.business.simulator.actionStringRepresentor.represent(a) for a in joint_action]
            for sublist in actions:
                pick_count += 1 if 'Pick' in sublist else 0
                deliver_count += 1 if 'Deliver' in sublist else 0

        return pick_count, deliver_count
