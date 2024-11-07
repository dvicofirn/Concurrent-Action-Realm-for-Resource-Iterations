import time
import traceback
from business import Business
from genetic_planner import CARRIPlannerGA
import concurrent.futures

class Manager:
    def __init__(self, simulator, iterations, iter_time, transitions_per_iteration):
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
        #self.planner = Planner(simulator, init_time, iter_time, transitions_per_iteration, **planner_kwargs)
        self.genetic_planner = CARRIPlannerGA(simulator)
        self.total_plan = []



    def run(self):

        total_time = time.time()

        while self.business.canAdvance():
            self.execute_iteration()

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
        """
        Calls Planner to generate and execute the plan, enforcing iteration timing constraints.
        """
        start_time = time.time()

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

    def plan_fitness(self, plan):
        """
        Compute the fitness of a plan by aggregating the fitness scores of each chromosome in the plan.
        """
        return sum(self.genetic_planner.fitness_function(chromosome) for chromosome in plan)

    def create_and_run_genetic_planner(self, state, start_time):
        """
        Creates an isolated instance of the genetic planner and runs it with the provided state.
        """
        planner_instance = CARRIPlannerGA(self.business.simulator.copy())
        return planner_instance.plan(state.copy(), self.iter_time, start_time)


    def count_pick_deliver(self):
        pick_count, deliver_count = 0, 0
        for joint_action in self.total_plan:
            actions = [self.business.simulator.actionStringRepresentor.represent(a) for a in joint_action]
            for sublist in actions:
                pick_count += 1 if 'Pick' in sublist else 0 
                deliver_count += 1 if 'Deliver' in sublist else 0 

        return pick_count, deliver_count