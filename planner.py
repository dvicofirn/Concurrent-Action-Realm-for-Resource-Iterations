import time
import random
import logging
from typing import List, Any
from heuristics import *
from search import *

class Planner:
    def __init__(self, simulator, init_time, iter_t, **kwargs):
        """
        :param simulator: An instance of CARRISimulator
        :param init_time: float, time of initialization
        :param iter_t: float, time allowed for each iteration
        """
        self.simulator = simulator
        self.init_time = init_time
        self.iter_t = iter_t
        # Allow search algorithm and heuristic to be passed for flexibility

        self.heuristic = kwargs.get('heuristic', OperatorCountingHeuristic())
        algo_args = [self.simulator.current_state,self.simulator, self.heuristic,self.iter_t]
        self.search_algorithm = kwargs.get('search_algorithm', a_star_search(*algo_args))
        
        self.max_plan_length = 15

    def generate_plan(self):
        """
        Generate a plan within the time limit using the provided search algorithm and heuristic.
        :return: A list representing the plan (sequence of actions).
        """
        start_time = time.time()
        plan = []

        try:
            search = self.search_algorithm(self.simulator, self.heuristic)
            while time.time() - start_time < self.iter_t and len(plan) < self.max_plan_length:
                next_step = search.step()
                if next_step is None:
                    logging.info("Search could not proceed further.")
                    break
                plan.append(next_step)
        except Exception as e:
            logging.error(f"Error during planning: {e}")

        logging.info(f"Generated plan with {len(plan)} steps.")
        return plan[:self.max_plan_length]

    def run_iteration(self):
        """
        Execute a planning iteration.
        :return: None
        """
        plan = self.generate_plan()
        if not plan:
            logging.warning("No valid plan was generated.")
        else:
            for action in plan:
                try:
                    self.simulator.advance_state(action)
                except ValueError as e:
                    logging.warning(f"Failed to apply action {action}: {e}")
                    break
