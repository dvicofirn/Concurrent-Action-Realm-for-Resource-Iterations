import collections
import time
import numpy as np

import random

class CARRIPlannerGA:
    def __init__(self, simulator, population_size=20, planning_horizon=5, generations=15):
        self.simulator = simulator
        self.population_size = population_size
        self.planning_horizon = planning_horizon
        self.generations = generations
        self.prev_state_chrom = self.simulator.current_state
        self.plan_sequence = []
        self.fitness_cache = {}  # Cache for storing fitness results
        self.itemKeysPositions = self.simulator.problem.itemKeysPositions

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
            if action.baseAction == 'Pick':
                score += 100  # Reward for picking up packages
            elif action.baseAction == 'Deliever':
                score += 100  # Reward for delivering
            elif action.baseAction == 'Wait':
                if self.has_pending_packages(state) or self.is_vehicle_loaded(state, joint_action.index(action)):
                    score -= 1000  # Penalize unnecessary waiting
            #elif 'Fuel' in action.name:
               # score += 50 if self.fuel_level(state, joint_action.index(action)) else -15  # Fueling has context-based score

        return score

    def chromosome_to_key(self, chromosome):
        """
        Converts a chromosome to a unique, immutable representation (tuple of tuples) to use as a cache key.
        """
        return tuple(tuple(action.name for action in actions) for actions, _, _ in chromosome)


    def fitness_function(self, chromosome):
        """Evaluates fitness based on task completion, cost, collision avoidance, and unnecessary waiting."""

        # Convert chromosome to a key and check cache
        key = self.chromosome_to_key(chromosome)
        if key in self.fitness_cache:
            return self.fitness_cache[key]  # Return cached fitness if available

        total_cost = sum(cost for _, cost, _ in chromosome)
        
        collision_penalty = 0
        pick_reward = 0
        deliver_reward = 0
        waiting_penalty = 0
        fuel_penalty = 0

        for actions, _, state in chromosome:
            package_picks = set()
            for i, action in enumerate(actions):
                if action.baseAction == 'Wait':
                    # Check if there are packages to pick up or if the vehicle is carrying something
                    if self.has_pending_packages(state) or self.is_vehicle_loaded(state, i, action):
                        waiting_penalty += 50  # Adjust the penalty value as needed

                #if 'Fuel' in action.name:
                   # if self.fuel_level(state, actions.index(action)):
                     #   fuel_penalty += 30
                  #  else:
                       # fuel_penalty -= 100

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
        self.fitness_cache[key] = score
        return score
    
    def has_pending_packages(self, state):
        """
        Checks if there are any packages in the state that are not yet delivered.
        
        :param state: The current state of the problem.
        :return: True if there are pending packages, False otherwise.
        """
        item_index, property_index = self.itemKeysPositions['Package onEntity']
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
                True

        return False
    
    def indextype(self, index):
        relevant_ranges = []
        for EntityIndex in self.simulator.vehicle_keys:
            curr_range = self.simulator.problem.ranges[EntityIndex]
            relevant_ranges.extend(curr_range)

        length = 0
        for EntityIndex in self.simulator.vehicle_keys:
            curr_range = self.simulator.problem.ranges[EntityIndex]
            length += len(curr_range)
            if index < length:
                enititytype = EntityIndex
                break

        return relevant_ranges[index], enititytype
    
    def fuel_level(self, state, index):
        return state.variables[1][index] > 2

    def mutation_helper(self, child, replace_index):
        prev_state = self.prev_state_chrom if replace_index == 0 else child[replace_index - 1][2]
        succ = list(self.simulator.generate_successors(prev_state))

        # Shuffle successors to reduce repeated random selection
        random.shuffle(succ)
        for new_state, joint_action, cost in succ:
            if new_state == child[replace_index][2]:
                return joint_action, cost, new_state

        return child[replace_index]  # Fallback if no suitable successor is found


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
        
        return selected_population

    def run_ga(self, initial_state):
        population = self.initialize_population(initial_state)
        for generation in range(1, self.generations + 1):
            # Elitism: Preserve the best chromosomes before creating the new population
            elite_size = max(1, self.population_size // 10)  # Preserve top 10% as elites
            elites = sorted(population, key=self.fitness_function, reverse=True)[:elite_size]

            if generation % 5 == 0:
                population.extend(self.initialize_population(self.simulator.current_state)[:self.population_size // 2])
            
            fitness_scores = np.array([self.fitness_function(chrom) for chrom in population])
            min_score = fitness_scores.min()
            if min_score <= 0:
                fitness_scores -= min_score - 1
            fitness_scores = fitness_scores / fitness_scores.sum()
            selected_population = random.choices(population, weights=fitness_scores, k=self.population_size // 2)
            population = elites + self.crossover_mutation(selected_population)  # Include elites in new population
        
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
            print(f"Iteration {iteration}: Planning Step")
            self.run_ga(self.simulator.current_state)
            iteration+= 1

        return self.plan_sequence
