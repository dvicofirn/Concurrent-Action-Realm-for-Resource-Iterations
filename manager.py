import time
import psutil
from multiprocessing import Process, Manager as MPManager
import traceback
from planner.planner import Planner
from business import Business
from CARRI import Simulator

class Manager:
    def __init__(self, simulator: Simulator, iterations, iterTime: int, transitionsPerIteration, **kwargs):
        """
        Manager class to coordinate planning and execution.

        :param simulator: Simulator object with the problem.
        :param iterations: List of iterations, each containing items to add.
        :param iterTime: Time allowed per iteration.
        :param transitionsPerIteration: Number of transitions per iteration.
        :param kwargs: Additional keyword arguments.
        """
        self.iterTime = iterTime  # Time limit per iteration
        self.business = Business(simulator, iterations)  # Business instance
        self.transitionsPerIteration = transitionsPerIteration  # Max transitions per iteration
        plannerClass = kwargs.get("planner", Planner)
        # Initialize the planner
        self.planner = plannerClass(simulator, iterTime, transitionsPerIteration, **kwargs)
        self.totalPlan = []  # Accumulate the total plan

    def run(self, printPlan=False):
        startTime = time.time()
        print(f"Start")
        print(self.business)
        print("----------")
        # Execute iterations as long as possible
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
        # Log details of the run for analysis
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

        return {
            'total plan length': len(self.totalPlan),
            'run success': completeRun,
            'costs': costs,
            'time measures': times,
            'pick counts': pickCounts,
            'deliver counts': deliverCounts
        }

    def planner_process(self, state, return_dict):
        # Generate a plan using the planner
        self.planner.generate_plan(state, return_dict)

    def execute_iteration(self):
        # Execute a single iteration
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
            # Terminate the planner subprocess and its children
            parent = psutil.Process(p.pid)
            for child in parent.children(recursive=True):
                child.terminate()
            parent.terminate()
            p.join()

        # Retrieve the plan from the shared dictionary
        plan = return_dict['plan']

        if len(plan) < self.transitionsPerIteration:
            raise Exception("Not enough transitions")

        # Add the plan to the total plan
        self.totalPlan.extend(plan[:self.transitionsPerIteration])

        try:
            # Advance the business state with the plan
            self.business.advanceIteration(plan[:self.transitionsPerIteration])
        except Exception as e:
            print(f'ERROR - Issue with plan execution: {e}')
            traceback.print_exc()
            exit()

    def print_plan(self):
        # Print the complete plan
        for i, transitionActions in enumerate(self.totalPlan):
            print(f"{i}.[{[self.business.simulator.actionStringRepresentor.represent(a) for a in transitionActions]}")

    def count_pick_deliver(self):
        # Count 'Pick' and 'Deliver' actions in the total plan
        pick_count, deliver_count = 0, 0
        for transitionActions in self.totalPlan:
            for action in transitionActions:
                if action.baseAction == "Pick":
                    pick_count += 1
                elif action.baseAction == "Deliver":
                    deliver_count += 1
        return pick_count, deliver_count
