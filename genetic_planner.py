import collections
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import time
import numpy as np
from typing import List, Tuple
from CARRI.parser import Translator

import random

from search.partialAssigner import PartialAssigner

class CARRIPlannerGA:
    def __init__(self, simulator, population_size=20, planning_horizon=5, generations=10):
        self.simulator = simulator
        self.population_size = population_size
        self.planning_horizon = planning_horizon
        self.generations = generations
        self.partial_assigner = PartialAssigner(self.simulator) 
        self.prev_state_chrom = self.simulator.current_state
        self.plan_sequence = []
        self.fitness_cache = {}  # Cache for storing fitness results
        self.onEntityIndexes = self.simulator.problem.get_onEntity_indexes()

    def initialize_population(self, initial_state):
        """Initializes a population with action selection based on estimated fitness impact."""
        self.prev_state_chrom = initial_state
        
        start = time.time()
        population = list(self.partial_assigner.successors_genetic(initial_state, self.planning_horizon, self.population_size))      
        #print("took :", time.time() - start )
        return population

    def fitness_function(self, chromosome):
        """Evaluates fitness based on task completion, cost, collision avoidance, and unnecessary waiting."""

        total_cost = sum(cost for _, cost, _ in chromosome)

        collision_penalty = 0
        pick_reward = 0
        deliver_reward = 0
        waiting_penalty = 0
        fuel_penalty = 0
        total_cost = 0
        actions = chromosome[0]
        _ = chromosome[1]
        state = chromosome[2]

        for actions, _, state in chromosome:
            package_picks = set()
            for i, action in enumerate(actions):
                if action.baseAction == 'Wait':
                    # Check if there are packages to pick up or if the vehicle is carrying something
                    if self.has_pending_packages(state) or self.is_vehicle_loaded(state, i, action):
                        waiting_penalty += 50  # Adjust the penalty value as needed

                if action.baseAction == 'Pick':
                    if tuple(action.params) not in package_picks:
                        pick_reward += 300
                        package_picks.add(tuple(action.params))
                    else:
                        collision_penalty += 100

                if action.baseAction == 'Deliver':
                    deliver_reward += 200

        # Fitness formula: reward task completion, penalize cost, collisions, and unnecessary waiting
        score = pick_reward + deliver_reward - total_cost - collision_penalty- waiting_penalty - fuel_penalty
        return score
    
    def has_pending_packages(self, state):
        """
        Checks if there are any packages in the state that are not yet delivered.
        
        :param state: The current state of the problem.
        :return: True if there are pending packages, False otherwise.
        """
        item_index, property_index = self.onEntityIndexes
        # Check if any package is not delivered
        x = state.items[item_index]
        for pack in state.items[item_index].values():
            if pack[property_index] == 0:
                return True
        return False
    
    def is_vehicle_loaded(self, state, index, action):
        inner_index , enititytype = self.indextype(index)

        for key, val in self.simulator.entities.items():
            if val == (enititytype, 'Vehicle'):
                vehicle_name = key.lower()

        cap_key = []
        for key in self.simulator.problem.varPositions.keys():
            if 'Cap' in key and vehicle_name in key:
                cap_key.append(key)

        for k in cap_key:
            cap_index = self.simulator.problem.varPositions[k]
            if state.variables[cap_index][inner_index] > 0:
                return True

        return False
    
    def indextype(self, index):
        relevant_ranges = []
        for EntityIndex in self.simulator.vehicle_keys:
            curr_range = self.simulator.problem.ranges[EntityIndex]
            if curr_range is not None:
                relevant_ranges.extend(curr_range)

        enititytype = None
        length = 0
        for EntityIndex in self.simulator.vehicle_keys:
            curr_range = self.simulator.problem.ranges[EntityIndex]
            length += len(curr_range) if curr_range is not None else 0
            if index < length:
                enititytype = EntityIndex
                break

        return relevant_ranges[index], enititytype


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
    
    def crossover_mutation(self, selected_population):
        # Modified Crossover: Sample one parent and regenerate the rest of the list concurrently
        num_to_generate = self.population_size - len(selected_population)
        parents = random.choices(selected_population, k=num_to_generate)
        crossover_points = random.choices(range(1, self.planning_horizon), k=num_to_generate)

        new_children = []
        with ThreadPoolExecutor() as executor:
            # Submit tasks in larger batches to reduce overhead
            futures = [executor.submit(self.generate_child, copy(parent), crossover_point) for parent, crossover_point in zip(parents, crossover_points)]

            for future in as_completed(futures):
                child = future.result()
                if child is not None:
                    new_children.append(child)

        selected_population.extend(new_children)
        return selected_population


    def generate_child(self, parent, crossover_point):
        # Use a new instance of PartialAssigner and deepcopy the simulator for thread safety
        start = time.time()
        partial_assigner = PartialAssigner(deepcopy(self.simulator))
        #print('took deepcopy: ' , time.time() - start)
        child = parent[:crossover_point]
        rest_of_child_candidates = list(partial_assigner.successors_genetic(self.simulator.problem.copyState(parent[crossover_point][2]), self.planning_horizon - crossover_point, 5))
        
        # Filter out invalid candidates early to reduce workload
        try:
            rest_of_child = random.choice(rest_of_child_candidates)
        except:
            return None
        child.extend(rest_of_child)

        return child if self.valid_child(child) else None
    
    def stochastic_universal_sampling(self, population, fitness_scores, k):
        pointers = np.linspace(0, sum(fitness_scores), k)
        fitness_sum = 0
        selected = []
        index = 0

        for pointer in pointers:
            while fitness_sum < pointer:
                fitness_sum += fitness_scores[index]
                index += 1
            selected.append(population[index - 1])

        return selected

    def run_ga(self, initial_state):
        population = self.initialize_population(initial_state)
        for generation in range(1, self.generations + 1):
            # Elitism: Preserve the best chromosomes before creating the new population
            elite_size = max(1, self.population_size // 3)  # Preserve top 10% as elites
            start = time.time()
            elites = sorted(population, key=self.fitness_function, reverse=True)[:elite_size]
            #print("took elit:", time.time() - start )
            if generation % 5 == 0:
                population.extend(self.initialize_population(self.simulator.current_state)[:self.population_size // 2])

            start = time.time()
            # Evaluate fitness concurrently
            with ThreadPoolExecutor() as executor:
                fitness_scores = list(executor.map(self.fitness_function, population))

            min_score = min(fitness_scores)
            if min_score <= 0:
                fitness_scores = [score - min_score + 1 for score in fitness_scores]

            total_fitness = sum(fitness_scores)
            fitness_scores = [score / total_fitness for score in fitness_scores]

            #print("took fitness:", time.time() - start )
            start = time.time()
            selected_population = self.stochastic_universal_sampling(population, fitness_scores, self.population_size // 2)
            #print("took selected:", time.time() - start )
            start = time.time()
            population = elites + self.crossover_mutation(selected_population)  # Include elites in new population
            #print("took mutation:", time.time() - start )
            
        
        joint_action, _, state = max(population, key=self.fitness_function)[0]
        self.simulator.current_state = state.copy()
        self.plan_sequence.append(joint_action)

    def plan(self, initial_state, iter_time,start_time):
        """Main planning loop with the GA integrated."""

        self.plan_sequence = []
        self.simulator.current_state = initial_state.copy()
        iteration = 0
        self.fitness_cache = {}
        
        while time.time() - start_time < iter_time:
        #for iteration in range(max_iterations):
            print(f"Planning Step : {iteration}")
            self.run_ga(self.simulator.current_state)
            iteration+= 1

        return self.plan_sequence
