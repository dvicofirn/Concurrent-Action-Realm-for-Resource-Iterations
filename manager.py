import time
import traceback
from planner.planner import Planner  #, RoutingPlanner
from business import Business
from CARRI import Simulator
import concurrent.futures


class Manager:
    def __init__(self, simulator: Simulator, iterations, iterTime: int, transitionsPerIteration, **kwargs):
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
        plannerClass = kwargs.get("planner", Planner)
        self.planner = plannerClass(simulator, iterTime, transitionsPerIteration, **kwargs)
        #searchAlgorithm = kwargs.get('searchAlgorithm', PartialAssigner)
        #self.planner = SearchEnginehBasedPlanner(simulator, iterTime, transitionsPerIteration, searchAlgorithm=searchAlgorithm)
        #self.planner = planner(simulator, init_time, iter_time, transitions_per_iteration, **kwargs)
        #self.planner = GeneticPlanner(simulator, iterTime, transitionsPerIteration, PartialAssigner)
        self.totalPlan = []

    def run(self):
        startTime = time.time()
        print(f"Start")
        print(self.business)
        print("----------")
        while self.business.canAdvanceIteration():
            self.execute_iteration()
            print(self.business)
            print("----------")

        pick_count, deliver_count = self.count_pick_deliver()

        print('\nTotal Planning and Execution time : ', time.time() - startTime)
        print("Executed plan with total cost of " + str(self.business.cost))
        print('Total Plan Length:', len(self.totalPlan))
        print("Total 'Pick' count:", pick_count)
        print("Total 'Deliver' count:", deliver_count)
        print('Plan :')

        self.print_plan()
    def execute_iteration(self):
        plan = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self.planner.generate_plan, self.business.getState())
            try:
                plan = future.result(timeout=self.iterTime)
            except concurrent.futures.TimeoutError:
                future.cancel()

        #plan = self.planner.plan_sequence

        self.totalPlan.extend(plan[:self.transitionsPerIteration])
        # if len(plan) < self.transitionsPerIteration:
        #    raise Exception("Plan is too short")

        try:
            self.business.advanceIteration(plan[:self.transitionsPerIteration])
        except Exception as e:
            print(f'ERROR - Issue with plan execution: {e}')
            traceback.print_exc()
            exit()

    def print_plan(self):
        for i, transitionActions in enumerate(self.totalPlan):
            print(f"{i}.[{[self.business.simulator.actionStringRepresentor.represent(a) for a in transitionActions]}")

    def count_pick_deliver(self):
        pick_count, deliver_count = 0, 0
        for transitionActions in self.totalPlan:
            for action in transitionActions:
                if action.baseAction == "Pick":
                    pick_count += 1
                elif action.baseAction == "Deliver":
                    deliver_count += 1
        return pick_count, deliver_count



