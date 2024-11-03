import time
import random
import logging
from typing import List, Any
from heuristics import RequestCountHeuristic
from search import *

class Planner:
    def __init__(self, simulator, init_time, iter_t, transitions_per_iteration, **kwargs):
        """
        :param simulator: An instance of CARRISimulator
        :param init_time: float, time of initialization
        :param iter_t: float, time allowed for each iteration
        """
        self.simulator = simulator
        self.init_time = init_time
        self.iter_t = iter_t
        # Allow search algorithm and heuristic to be passed for flexibility

        self.heuristic = kwargs.get('heuristic', RequestCountHeuristic(self.simulator.problem))
        # Store the search algorithm as a reference, not an instance
        self.search_algorithm_class = kwargs.get('search_algorithm', a_star_search)
        
        self.max_plan_length = transitions_per_iteration
        self.plan = None

    def init(self):
        return 

    def generate_plan(self):
        """
        Generate a plan within the time limit using the provided search algorithm and heuristic.
        :return: A list representing the plan (sequence of actions).
        """
        start_time = time.time()
        plan = []

        try:
            # Initialize the search algorithm here
            search = self.search_algorithm_class(self.simulator, self.heuristic, self.iter_t)
            return search
        
        except Exception as e:
            logging.error(f"Error during planning: {e}")

    def run_iteration(self, init_state):
        """
        Execute a planning iteration.
        :return: None
        """
        try:
            self.simulator.current_state = init_state
            plan = self.generate_plan()
        except e:
            print(e)
            logging.error("An error occurred during planning:", exc_info=True)  # Logs the full stack trace
        if not plan:
            logging.warning("No valid plan was generated.")
        else:
            for action in plan:
                try:
                    self.simulator.advance_state(action)
                except ValueError as e:
                    logging.warning(f"Failed to apply action {action}: {e}")
                    break
        
        return plan
