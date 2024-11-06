# GeneticPlanner class for solving the vehicle routing problem using a genetic algorithm.
import collections
from typing import Tuple
from CARRI.simulator import Simulator
from CARRI.realm import Problem
import numpy as np
from typing import List, Tuple
from CARRI.translator import Translator

import random


class CARRIPlannerGA:
    def __init__(self, simulation, population_size=20, planning_horizon=7, generations=20):
        self.simulation = simulation
        self.population_size = population_size
        self.planning_horizon = planning_horizon
        self.generations = generations
        self.prev_state_chrom = self.simulation.current_state

    def initialize_population(self, initial_state):
        """Initializes a population of chromosomes with valid action sequences from generate_successors."""
        self.prev_state_chrom = initial_state
        population = []
        for _ in range(self.population_size):
            chromosome = []
            state = initial_state.copy()
            for _ in range(self.planning_horizon):
                successors = list(self.simulation.generate_successors(state))
                if not successors:
                    break  # No further actions available
                # Choose a random valid joint action and update the state
                next_state, joint_action, cost = random.choice(successors)

                '''
                for i, a in enumerate(joint_action):
                    print(f"{_}/{i} . {self.simulation.actionStringRepresentor.represent(a)}")
                print("\n")
                '''
                chromosome.append((joint_action, cost, next_state))  # Store action and its cost
                state = next_state  # Update state for next time step

            #if self.simulation.valid_sequence(chromosome, state):
               # population.append(chromosome)
            population.append(chromosome)
        return population

    def action_type(self, transition):
        return 'Pick' in transition.name or 'Deliver' in transition.name

    def fitness_function(self, chromosome):
        """Evaluates fitness based on task completion, cost, collision avoidance, and unnecessary waiting."""
        total_cost = sum(cost for _, cost, _ in chromosome)
        
        # Count completed deliveries in the chromosome
        task_completion_score = sum(
            1 for actions, _, _ in chromosome if any(self.action_type(action) for action in actions)
        )
        
        # Apply collision penalties
        collision_penalty = self.check_for_collisions(chromosome)


        # Apply waiting penalty if waiting is unnecessary
        waiting_penalty = 0
        fuel_penalty = 0
        for actions, _, state in chromosome:
            for i, action in enumerate(actions):
                if 'Wait' in action.name:
                    # Check if there are packages to pick up or if the vehicle is carrying something
                    if self.has_pending_packages(state) or self.is_vehicle_loaded(state, i):
                        waiting_penalty += 20  # Adjust the penalty value as needed

                if 'Fuel' in action.name:
                    if self.fuel_level(state, i):
                        waiting_penalty += 30

        # Fitness formula: reward task completion, penalize cost, collisions, and unnecessary waiting
        score = task_completion_score * 300 - total_cost - collision_penalty*10- waiting_penalty*10 - fuel_penalty
        return score
    
    def has_pending_packages(self, state):
        for pack in state.items[0].values():
            if pack[2]== False:
                return True
        return False 
    
    def is_vehicle_loaded(self, state, index):
        return state.variables[2][index] > 0
    
    def fuel_level(self, state, index):
        return state.variables[1][index] > 2

    def check_for_collisions(self, chromosome):
        """Penalizes chromosomes where multiple drones attempt to pick the same package at the same time."""
        penalty = 0
        for joint_action, _, _ in chromosome:
            package_picks = set()
            for action in joint_action:
                # Check if the action is a "pick" and track package targets
                if  "Pick" in action.name:
                    pars = str(action.params)
                    if pars in package_picks:
                        # Penalize if another drone is already picking this package
                        penalty += 10
                    else:
                        package_picks.add(pars)
        return penalty

    def mutation_helper(self, child, replace_index):
        if replace_index == 0:
            prev_state = self.prev_state_chrom
        else:
            prev_state = child[replace_index - 1][2]

        succ = self.simulation.generate_successors(prev_state)
        succ = list(collections.deque(succ))
        new_state, joint_action, cost = random.choice(succ)
        #apply -> get new state 
        # is it the same state?
        # yes - valid ? 
        # need different mutation - more safisticated
        while new_state != child[replace_index][2]:
            succ.remove((new_state, joint_action, cost))
            if len(succ) == 0:
                return child[replace_index]
            new_state, joint_action, cost = random.choice(succ)
            

        #child[replace_index] = (joint_action, cost, new_state)
        return (joint_action, cost, new_state)

    def run_ga(self, initial_state):
        """Runs the GA to optimize action sequences over the planning horizon."""
        population = self.initialize_population(initial_state)
        
        for generation in range(self.generations):
            # Periodically reintroduce diversity
            if generation % 5 == 0:
                new_random_chromosomes = self.initialize_population(self.simulation.current_state)
                population.extend(new_random_chromosomes[:self.population_size // 2])

            fitness_scores = [self.fitness_function(chromosome) for chromosome in population]
            
            # Adjust scores to make them all positive for selection, if necessary
            min_score = min(fitness_scores)
            if min_score <= 0:
                fitness_scores = [score - min_score + 1 for score in fitness_scores]  # Shift all scores to be positive

            # Ensure weights are non-zero for selection
            if sum(fitness_scores) == 0:
                fitness_scores = [1] * len(fitness_scores)  # Default to uniform weights if all are zero


            selected_population = random.choices(population, weights=fitness_scores, k=self.population_size // 2)
            new_population = []

            while len(new_population) < self.population_size:
                parent1, parent2 = random.sample(selected_population, 2)
                # Crossover: Swap segments of action sequences

                #TODO: check validity
                crossover_point = random.randint(1, self.planning_horizon - 1)

                while parent1[crossover_point][2] != parent1[crossover_point][2]: #state comprassion
                    parent1, parent2 = random.sample(selected_population, 2)

                
                child1 = parent1[:crossover_point] + parent2[crossover_point:]
                child2 = parent2[:crossover_point] + parent1[crossover_point:]

                # Mutation: Modify a random gene (action sequence) in each child
                if random.random() < 0.3:  # 10% mutation rate
                    replace_index = random.randint(0, len(child1) - 1)
                    child1[replace_index] = self.mutation_helper(child1, replace_index)

                if random.random() < 0.3:
                    replace_index = random.randint(0, len(child2) - 1)
                    child2[replace_index] = self.mutation_helper(child2, replace_index)


                new_population.extend([child1, child2])

            population = new_population

        # Select the best solution
        best_chromosome = max(population, key=self.fitness_function)
        # Execute the best action sequence
        """
        print("_________best chromozone_____________")
        for _, val in enumerate(best_chromosome):
            act, cost, state = val
            for i, a in enumerate(act):
                print(f"{_}/{i} . {self.simulation.actionStringRepresentor.represent(a)}")

            print("\n")
        """

        joint_action, _, state = best_chromosome[0]
        #self.simulation.advance_state(joint_action, state)
        self.simulation.current_state = state.copy()

        action_str = []
        for i, a in enumerate(joint_action):
            action_str.append(self.simulation.actionStringRepresentor.represent(a))

        print('selected action: ', action_str)
        print('new_state simulation:', self.simulation.current_state)
        print('\n')
        x = 1

    def plan(self, max_iterations=100, initial_state=None):
        """Main planning loop with the GA integrated."""
        for iteration in range(max_iterations):
            print(f"Iteration {iteration}: Planning Step")
            self.run_ga(self.simulation.current_state)
            # Check for new tasks and update environment
            #new_packages, new_requests = self.simulation.update_state_dynamic()
            #if new_packages or new_requests:
               # print("New tasks appeared! Re-evaluating actions.")


# Example usage
FOLDER_DOMAINS = "Examples\\Domains"
FOLDER_PROBLEMS = "Examples\\Problems"
DomainsProblemsDict = {"Trucks and Drones": ("Trucks and Drones 1",),
                        "Cars": ("Cars 1",),}

translator = Translator()
simulator, iterations = translator.translate(FOLDER_DOMAINS + "\\" + "Cars.CARRI",
                                                FOLDER_PROBLEMS + "\\" + DomainsProblemsDict["Cars"][0] + ".CARRI")
planner = CARRIPlannerGA(simulator)
planner.plan(max_iterations=25)
