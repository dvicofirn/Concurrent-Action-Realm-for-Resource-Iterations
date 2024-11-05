# GeneticPlanner class for solving the vehicle routing problem using a genetic algorithm.
from typing import Tuple
from CARRI.simulator import Simulator
from CARRI.realm import Problem
import numpy as np
from typing import List, Tuple
from CARRI.translator import Translator

import random

class RollingPlanner:
    def __init__(self, simulation):
        self.simulation = simulation
        # Initialize drones as indices of their locations in the list
        self.drones = [*range(len(self.simulation.problem.initState.variables[0]))]
        
        successors = self.simulation.generate_partial_successors(self.simulation.current_state) 
        x=1

    def generate_feasible_actions(self, drone):
        # Generate all feasible actions for a drone based on current state
        actions = []
        for neighbor in self.simulation.get_neighbors(drone.location):
            if drone.fuel_level > 0:
                actions.append(("move", neighbor))
        # Add other actions like pick, deliver, boost, and emergency refuel as needed
        # Example placeholder actions for demonstration
        actions.append(("wait", None))
        actions.append(("boost", neighbor if drone.fuel_level >= 2 else None))
        return actions

    def fitness_function(self, chromosome):
        # Calculate fitness based on fuel usage, task completion, and adaptability
        fuel_used = sum([step[1].get("fuel_cost", 0) for step in chromosome])  # Hypothetical fuel cost extraction
        completed_tasks = sum([1 for step in chromosome if step[0] == "deliver"])
        adaptability_score = 1 / (1 + len(self.simulation.get_new_tasks()))  # Example: fewer new tasks penalized
        return completed_tasks * 10 - fuel_used + adaptability_score

    def select_and_execute_actions(self, population_size=10, generations=20):
        # Initialize population of chromosomes (action sequences for each drone)
        population = [
            [random.choice(self.generate_feasible_actions(drone)) for _ in range(5)]  # 5 steps per chromosome
            for _ in range(population_size)
            for drone in self.drones
        ]

        for generation in range(generations):
            # Evaluate fitness for each chromosome
            fitness_scores = [self.fitness_function(chromosome) for chromosome in population]
            # Select parents based on fitness
            selected = random.choices(population, weights=fitness_scores, k=population_size // 2)
            # Crossover and mutation to produce next generation
            new_population = []
            while len(new_population) < population_size:
                parent1, parent2 = random.sample(selected, 2)
                # Crossover: swap half of actions
                midpoint = len(parent1) // 2
                child1 = parent1[:midpoint] + parent2[midpoint:]
                child2 = parent2[:midpoint] + parent1[midpoint:]
                # Mutation: random action change
                if random.random() < 0.1:  # 10% mutation rate
                    child1[random.randint(0, len(child1) - 1)] = random.choice(self.generate_feasible_actions(self.drones[0]))
                if random.random() < 0.1:
                    child2[random.randint(0, len(child2) - 1)] = random.choice(self.generate_feasible_actions(self.drones[0]))
                new_population.extend([child1, child2])

            population = new_population

        # Select the best solution from the final population
        best_chromosome = max(population, key=self.fitness_function)
        # Execute the actions in the best chromosome
        for step, (action, target) in enumerate(best_chromosome):
            drone = self.drones[step % len(self.drones)]
            self.simulation.execute_action(drone, (action, target))

    def plan(self, max_iterations=100):
        for iteration in range(max_iterations):
            print(f"Iteration {iteration}: Planning Step")
            self.select_and_execute_actions()
            # Update environment to include new packages or requests if they appear
            # new_packages, new_requests = self.simulation.update_state_dynamic()  # Hypothetical method
            # if new_packages or new_requests:
            #     print("New tasks appeared! Re-evaluating actions.")


# Example usage
FOLDER_DOMAINS = "Examples\\Domains"
FOLDER_PROBLEMS = "Examples\\Problems"
DomainsProblemsDict = {"Trucks and Drones": ("Trucks and Drones 1",),
                        "Cars": ("Cars 1",),}

translator = Translator()
simulator, iterations = translator.translate(FOLDER_DOMAINS + "\\" + "Cars.CARRI",
                                                FOLDER_PROBLEMS + "\\" + DomainsProblemsDict["Cars"][0] + ".CARRI")
planner = RollingPlanner(simulator)
planner.plan(max_iterations=50)
