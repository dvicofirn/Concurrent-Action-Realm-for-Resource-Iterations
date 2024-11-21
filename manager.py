import time
import psutil
from multiprocessing import Process, Manager as MPManager
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

    def run(self, printPlan=False):
        startTime = time.time()
        print(f"Start")
        print(self.business)
        print("----------")
        while self.business.canAdvanceIteration():
            try:
                self.execute_iteration()
            except Exception as e:
                print(e)
                break
            print(self.business)
            print("----------")

        pick_count, deliver_count = self.count_pick_deliver()

        print('\nTotal Planning and Execution time : ', time.time() - startTime)
        print("Executed plan with total cost of " + str(self.business.getCost()))
        print('Total Plan Length:', len(self.totalPlan))
        print("Total 'Pick' count:", pick_count)
        print("Total 'Deliver' count:", deliver_count)
        print('Plan :')

        if printPlan:
            self.print_plan()

    def logRun(self):
        costs = []
        times = []
        pickCounts = []
        deliverCounts = []
        completeRun = True
        startTime = time.time()
        while self.business.canAdvanceIteration():
            try:
                self.execute_iteration()
            except Exception as e:
                completeRun = False
                break
            costs.append(self.business.getCost())
            times.append(time.time() - startTime)
            pickCount, deliverCount = self.count_pick_deliver()
            pickCounts.append(pickCount)
            deliverCounts.append(deliverCount)

        return {'total plan length': len(self.totalPlan),
                'run success': completeRun,
                'costs': costs,
                'time measures': times,
                'pick counts': pickCounts,
                'deliver counts': deliverCounts}

    def planner_process(self, state, return_dict):
        self.planner.generate_plan(state, return_dict)

    def execute_iteration(self):
        # Create a Manager to handle shared data between processes
        plan_manager = MPManager()
        return_dict = plan_manager.dict()
        return_dict['plan'] = []

        # Start the planner process
        p = Process(target=self.planner_process, args=(self.business.getState(), return_dict))
        p.start()

        # Wait for the process to finish within the time limit
        p.join(self.iterTime)

        # Terminate the process if it's still running
        if p.is_alive():
            # Terminate the planner subprocess and all its child processes
            parent = psutil.Process(p.pid)
            for child in parent.children(recursive=True):
                child.terminate()
            parent.terminate()
            p.join()
        # Retrieve the plan from the shared dictionary
        plan = return_dict['plan']

        #plan = self.planner.getPlan()
        if len(plan) < self.transitionsPerIteration:
            raise Exception("Not enough transitions")

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
