import time
import random
import logging

from typing import List, Any

from  heuristics import *
from  search import *


class Planner:
    def __init__(self, problem, simulator, init_time, iter_t, **kwargs):
        """
        :param problem: An instance of CARRIProblem
        :param simulator: An instance of CARRISimulator
        :param init_time: float, time of initialization
        :param iter_t: float, time allowed for each iteration
        """
        self.problem = problem
        self.simulator = simulator
        self.init_time = init_time
        self.iter_t = iter_t
        # Allow search algorithm and heuristic to be passed for flexibility
        self.search_algorithm = kwargs.get('search_algorithm', a_star_search())
        self.heuristics = [
            LMCutHeuristic(),
            HFFHeuristic(),
            HAddHeuristic(),
        ]
        self.heuristic_scores = {heuristic.__class__.__name__: 0 for heuristic in self.heuristics}
        self.heuristic = kwargs.get('heuristic', self.select_heuristic_on_the_fly())
        # Plan will be initialized within generate_plan()
        self.plan = []
        # Retrieve current state from simulator for more up-to-date information
        self.current_state = simulator.get_current_state() if hasattr(simulator, 'get_current_state') else self.problem.initial_state
        self.epsilon = kwargs.get('epsilon', 0.1)
        self.epsilon_decay = kwargs.get('epsilon_decay', 0.99)

    def select_heuristic_on_the_fly(self):
        """
        Dynamically select a heuristic based on its past performance.
        Uses an epsilon-greedy approach to balance exploration and exploitation.
        :return: A heuristic instance
        """
        self.epsilon = max(0.05, self.epsilon * self.epsilon_decay)  # Gradually reduce exploration rate
        if random.random() < self.epsilon:
            logging.info("Exploring: Randomly selecting a heuristic.")
            return random.choice(self.heuristics)
        else:
            # Use the heuristic with the highest score
            best_heuristic_name = max(self.heuristic_scores, key=self.heuristic_scores.get)
            logging.info(f"Exploiting: Selecting the best heuristic so far - {best_heuristic_name}.")
            for heuristic in self.heuristics:
                if heuristic.__class__.__name__ == best_heuristic_name:
                    return heuristic

    def update_heuristic_scores(self, success, heuristic_name, plan_quality, computation_time):
        """
        Update the score of the heuristic based on its performance.
        :param success: Boolean indicating if the plan was successful
        :param heuristic_name: Name of the heuristic used
        :param plan_quality: Quality metric for the plan (e.g., length or cost)
        :param computation_time: Time taken to generate the plan
        """
        reward = plan_quality / (computation_time + 1e-5)  # Higher quality and faster time yield better reward
        if success:
            self.heuristic_scores[heuristic_name] += reward
        else:
            self.heuristic_scores[heuristic_name] -= reward

    def generate_plan(self) -> List[Any]:
        """
        Generates a plan using the search algorithm and heuristic.
        The plan is generated for the next 10-15 iterations or as far as possible within the allocated time.
        :return: List of actions constituting the plan
        """
        # Setting up the time limit
        start_time = time.time()
        time_limit = self.init_time + self.iter_t
        # Update remaining time dynamically to avoid inaccuracies
        remaining_time = time_limit - time.time()

        heuristic_name = type(self.heuristic).__name__
        success = False

        # Perform the search until the time limit is reached or plan is fully formed
        while len(self.plan) < 15 and remaining_time > 0:
            # Call the search algorithm with the current state, goal, and heuristic
            result = self.search_algorithm.search(self.current_state, self.problem.goal_state, self.heuristic, remaining_time)
            
            # If a solution is found, append it to the plan
            if result:
                actions, next_state = result
                self.plan.extend(actions)
                self.current_state = next_state
                success = True
                plan_quality = len(actions)  # Assuming shorter plans are better
                computation_time = time.time() - start_time
                self.update_heuristic_scores(success, heuristic_name, plan_quality, computation_time)
            else:
                logging.warning("No further solution found in the given time limit.")
                break

            # Update the remaining time
            current_time = time.time()
            remaining_time = time_limit - current_time

        # Select a new heuristic for the next iteration based on updated scores
        self.heuristic = self.select_heuristic_on_the_fly()
        return self.plan

    def execute_plan(self):
        """
        Executes the generated plan in the simulator.
        The method tries to execute as many actions as possible within the allocated time.
        """
        for action in self.plan:
            # Check if the current action is valid in the simulator and execute
            if self.simulator.is_action_valid(self.current_state, action):
                print(f"Executing action: {action}")
                self.current_state = self.simulator.execute_action(self.current_state, action)
            else:
                print(f"Invalid action: {action}")
                break
        
        # Clear the plan once executed
        # Instead of clearing the plan, consider keeping a record for analysis
        executed_plan = self.plan.copy()
        self.plan.clear()

    def plan_iteration(self):
        """
        Plan and execute in iterations.
        This function will be called several times to mimic saturated planning where environment changes dynamically.
        """
        # Add a condition to break out of the loop if necessary
        while not self.problem.is_solved(self.current_state):
            # Generate a plan for 10-15 steps or until interrupted
            self.generate_plan()
            # Execute the generated plan
            self.execute_plan()
            # Pause to simulate time passing between iterations
            # Consider using a scheduler or timer for better precision
            time.sleep(self.iter_t)

# Example usage
# Proper instance creation for problem and simulator
if __name__ == "__main__":
    from CARRIRealm import CARRIProblem, CARRISimulator
    
    problem = CARRIProblem()  # Replace with proper initialization
    simulator = CARRISimulator()  # Replace with proper initialization
    init_time = 5.0
    iter_t = 1.0

    planner = Planner(problem, simulator, init_time, iter_t)
    planner.plan_iteration()
