import time
from planner import Planner

class Manager:
    def __init__(self, simulator, init_time, iter_t, **planner_kwargs):
        """
        :param problem: An instance of CARRIProblem
        :param simulator: An instance of CARRISimulator
        :param init_time: float, maximum time for planner initiation
        :param iter_t: float, time limit per iteration for planning
        """
        self.simulator = simulator
        self.init_time = init_time
        self.iter_t = iter_t
        self.planner = Planner(simulator.problem, simulator, init_time, iter_t, **planner_kwargs)
        self.execution_start_time = None

    def start_planning(self):
        """
        Start the planning process with an initiation time limit.
        """
        start_time = time.time()
        self.execution_start_time = start_time + self.init_time

        # Initiate plan iteration within the init time limit
        while time.time() < self.execution_start_time and not self.problem.is_solved(self.planner.current_state):
            self.execute_iteration()

    def execute_iteration(self):
        """
        Calls Planner to generate and execute the plan, enforcing iteration timing constraints.
        """
        iteration_start = time.time()

        # Call generate_plan, respecting iteration time limit
        if time.time() - iteration_start < self.iter_t:
            self.planner.generate_plan()
            self.planner.execute_plan()

        # Delay to ensure we’re within the iteration time limit
        elapsed_time = time.time() - iteration_start
        if elapsed_time < self.iter_t:
            time.sleep(self.iter_t - elapsed_time)

    def run(self):
        """
        Runs the manager’s planning and execution in controlled iterations.
        """
        self.start_planning()
        while not self.problem.is_solved(self.planner.current_state):
            self.execute_iteration()

