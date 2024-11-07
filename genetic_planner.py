# GeneticPlanner class for solving the vehicle routing problem using a genetic algorithm.
import collections
import time
from typing import Tuple
from CARRI.simulator import Simulator
from CARRI.realm import Problem
import numpy as np
from typing import List, Tuple
from CARRI.translator import Translator

import random
from concurrent.futures import ProcessPoolExecutor

class CARRIPlannerGA:
    def __init__(self, simulator, population_size=20, planning_horizon=5, generations=15):
        self.simulator = simulator
        self.population_size = population_size
        self.planning_horizon = planning_horizon
        self.generations = generations
        self.prev_state_chrom = self.simulator.current_state
        self.plan_sequence = []


    def initialize_population(self, initial_state):
        """Initializes a population with action selection based on estimated fitness impact."""
        self.prev_state_chrom = initial_state
        population = []
        for _ in range(self.population_size):
            chromosome = []
            state = initial_state

            for _ in range(self.planning_horizon):
                successors = list(self.simulator.generate_successors(state))
                if not successors:
                    break

                # Estimate fitness impact for each action and prioritize
                fitness_scored_actions = [
                    (ns, ja, cost, self.estimate_action_fitness(ja, cost, ns))
                    for ns, ja, cost in successors
                    if any(a.name in ('Pick', 'Deliver') for a in ja)
                ]

                if fitness_scored_actions:
                    # Sort based on estimated fitness (higher is better)
                    fitness_scored_actions.sort(key=lambda x: -x[3])  # Sort by descending fitness
                    next_state, joint_action, cost, _ = fitness_scored_actions[0]
                else:
                    next_state, joint_action, cost = random.choice(successors)

                chromosome.append((joint_action, cost, next_state))
                state = next_state

            population.append(chromosome)
        return population

    def estimate_action_fitness(self, joint_action, cost, state):
        """Estimates the fitness impact of an action sequence, mirroring the main fitness criteria."""
        score = -cost  # Start with negative cost to minimize

        for action in joint_action:
            # Add rewards or penalties similar to main fitness function
            if 'Pick' in action.name:
                score += 100  # Reward for picking up packages
            elif 'Deliver' in action.name:
                score += 100  # Reward for delivering
            elif 'Wait' in action.name:
                if self.has_pending_packages(state) or self.is_vehicle_loaded(state, joint_action.index(action)):
                    score -= 100  # Penalize unnecessary waiting
            elif 'Fuel' in action.name:
                score += 50 if self.fuel_level(state, joint_action.index(action)) else -15  # Fueling has context-based score

        return score


    def fitness_function(self, chromosome):
        """Evaluates fitness based on task completion, cost, collision avoidance, and unnecessary waiting."""
        total_cost = sum(cost for _, cost, _ in chromosome)
        
        collision_penalty = 0
        pick_reward = 0
        deliver_reward = 0
        waiting_penalty = 0
        fuel_penalty = 0

        for actions, _, state in chromosome:
            package_picks = set()
            for i, action in enumerate(actions):
                if 'Wait' in action.name:
                    # Check if there are packages to pick up or if the vehicle is carrying something
                    if self.has_pending_packages(state) or self.is_vehicle_loaded(state, actions.index(action)):
                        waiting_penalty += 20  # Adjust the penalty value as needed

                if 'Fuel' in action.name:
                    if self.fuel_level(state, actions.index(action)):
                        fuel_penalty += 30
                    else:
                        fuel_penalty -= 100

                if 'Pick' in action.name:
                    if tuple(action.params) not in package_picks:
                        pick_reward += 300
                        package_picks.add(tuple(action.params))
                    else:
                        collision_penalty += 100

                if 'Deliver' in action.name:
                    deliver_reward += 200

        # Fitness formula: reward task completion, penalize cost, collisions, and unnecessary waiting
        score = pick_reward + deliver_reward - total_cost - collision_penalty- waiting_penalty - fuel_penalty
        return score
    
    def has_pending_packages(self, state):
        for pack in state.items[0].values():
            if pack[2]== False:
                return True
        return False 
    
    def is_vehicle_loaded(self, state, index):
        if index >= len(state.variables[2]):
            x = 1
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

        succ = self.simulator.generate_successors(prev_state)
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


    def valid_child(self, child):
        valid = True
        inner_state = self.simulator.current_state.copy()
        for index, chrom in enumerate(child):
            action, _, _ = chrom
            state = self.prev_state_chrom.copy() if index == 0 else child[index - 1][2]
            self.simulator.current_state = state.copy()
            if not self.simulator.validate_Transition(action):
                valid = False
                break
        self.simulator.current_state = inner_state
        return valid
    
    def valid_parent_split(self, crossover_point, parent1, parent2):
        child1 = parent1[:crossover_point] + parent2[crossover_point:]
        child2 = parent2[:crossover_point] + parent1[crossover_point:]

        return self.valid_child(child1) and self.valid_child(child2)


    def run_ga(self, initial_state):
        population = self.initialize_population(initial_state)
        for generation in range(1, self.generations+1):
            if generation % 5 == 0:
                population.extend(self.initialize_population(self.simulator.current_state)[:self.population_size // 2])
            fitness_scores = np.array([self.fitness_function(chrom) for chrom in population])
            min_score = fitness_scores.min()
            if min_score <= 0:
                fitness_scores -= min_score - 1
            fitness_scores = fitness_scores / fitness_scores.sum()
            selected_population = random.choices(population, weights=fitness_scores, k=self.population_size // 2)
            population = self.crossover_mutation(selected_population)
        
        joint_action, _, state = max(population, key=self.fitness_function)[0]
        self.simulator.current_state = state.copy()
        self.plan_sequence.append(joint_action)


    def crossover_mutation(self, selected_population):
        # Crossover: Swap segments of action sequences

        while len(selected_population) < self.population_size:
            parent1, parent2 = random.sample(selected_population, 2)
            crossover_point = random.randint(1, self.planning_horizon - 1)
            child1 = parent1[:crossover_point] + parent2[crossover_point:]
            child2 = parent2[:crossover_point] + parent1[crossover_point:]

            for child in [child1, child2]:
                if random.random() < 0.3:
                    replace_index = random.randint(0, len(child) - 1)
                    child[replace_index] = self.mutation_helper(child, replace_index)
                if self.valid_child(child):
                    selected_population.append(child)
        
        
        """
        while len(selected_population) < self.population_size:
            parent1, parent2 = random.sample(selected_population, 2)
            crossover_point = random.randint(1, self.planning_horizon - 1)

            while not self.valid_parent_split(crossover_point, parent1, parent2): #state comprassion
                parent1, parent2 = random.sample(selected_population, 2)

            child1 = parent1[:crossover_point] + parent2[crossover_point:]
            child2 = parent2[:crossover_point] + parent1[crossover_point:]

            # Mutation: Modify a random gene (action sequence) in each child
            if random.random() < 0.3:  # 30% mutation rate
                replace_index = random.randint(0, len(child1) - 1)
                child1[replace_index] = self.mutation_helper(child1, replace_index)

            if random.random() < 0.3:
                replace_index = random.randint(0, len(child2) - 1)
                child2[replace_index] = self.mutation_helper(child2, replace_index)

            if self.valid_child(child1):
                selected_population.extend([child1])
            if self.valid_child(child2):
                selected_population.extend([child2])
        """
        return selected_population


    def plan(self, initial_state, iter_time,start_time, max_iterations=100,):
        """Main planning loop with the GA integrated."""

        self.plan_sequence = []
        self.simulator.current_state = initial_state.copy()
        iteration = 0
        
        while time.time() - start_time < iter_time:
        #for iteration in range(max_iterations):
            #print(f"Iteration {iteration}: Planning Step")
            self.run_ga(self.simulator.current_state)
            iteration+= 1

        return self.plan_sequence

'''
# Example usage
FOLDER_DOMAINS = "Examples\\Domains"
FOLDER_PROBLEMS = "Examples\\Problems"
DomainsProblemsDict = {"Trucks and Drones": ("Trucks and Drones 1",),
                        "Cars": ("Cars 1",),}

translator = Translator()
simulator, iterations = translator.translate(FOLDER_DOMAINS + "\\" + "Cars.CARRI",
                                                FOLDER_PROBLEMS + "\\" + DomainsProblemsDict["Cars"][0] + ".CARRI")
planner = CARRIPlannerGA(simulator)
start_time = time.time()
planner.plan(planner.simulator.current_state, 3, start_time)
'''