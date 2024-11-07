# GeneticPlanner class for solving the vehicle routing problem using a genetic algorithm.
import collections
import time
from typing import Tuple
from CARRI.simulator import Simulator
from CARRI.problem import Problem
import numpy as np
from typing import List, Tuple
from CARRI.translator import Translator

import random


class CARRIPlannerGA:
    def __init__(self, simulator, population_size=20, planning_horizon=3, generations=15):
        self.simulator = simulator
        self.population_size = population_size
        self.planning_horizon = planning_horizon
        self.generations = generations
        self.prev_state_chrom = self.simulator.current_state
        self.plan_sequence = []

    def initialize_population(self, initial_state):
        """Initializes a population of chromosomes with valid action sequences from generate_successors."""
        self.prev_state_chrom = initial_state
        population = []
        for _ in range(self.population_size):
            chromosome = []
            state = initial_state.copy()

            for _ in range(self.planning_horizon):
                successors = list(self.simulator.generate_successors(state))
                if not successors:
                    break  # No further actions available
                # Choose a random valid joint action and update the state
                #next_state, joint_action, cost = random.choice(successors)

                '''
                for i, a in enumerate(joint_action):
                    print(f"{_}/{i} . {self.simulator.actionStringRepresentor.represent(a)}")
                print("\n")
                '''

                # Filter to prioritize pick or deliver actions if available
                task_successors = [
                    (next_state, joint_action, cost) for next_state, joint_action, cost in successors
                    if any('Pick' in action.name or 'Deliver' in action.name for action in joint_action)
                ]
                
                # Choose a task-oriented action if available, otherwise fallback to random choice
                if task_successors:
                    next_state, joint_action, cost = random.choice(task_successors)
                else:
                    next_state, joint_action, cost = random.choice(successors)
                
                chromosome.append((joint_action, cost, next_state))  # Store action and its cost
                state = next_state.copy()  # Update state for next time step

            #if self.simulator.valid_sequence(chromosome, state):
               # population.append(chromosome)
            population.append(chromosome)
        return population


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
                    if self.has_pending_packages(state) or self.is_vehicle_loaded(state, i):
                        waiting_penalty += 20  # Adjust the penalty value as needed

                if 'Fuel' in action.name:
                    if self.fuel_level(state, i):
                        fuel_penalty += 30
                    else:
                        fuel_penalty -= 100

                if 'Pick' in action.name:
                    if tuple(action.params) not in package_picks:
                        pick_reward += 300
                        package_picks.add(tuple(action.params))
                    else:
                        collision_penalty += 100

                if'Deliver' in action.name:
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
        """Runs the GA to optimize action sequences over the planning horizon."""
        population = self.initialize_population(initial_state)

        for generation in range(self.generations):
            # Periodically reintroduce diversity
            if generation % 5 == 0:
                new_random_chromosomes = self.initialize_population(self.simulator.current_state)
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

                while not self.valid_parent_split(crossover_point, parent1, parent2): #state comprassion
                    parent1, parent2 = random.sample(selected_population, 2)

                
                #print('valid parent 1 : ', self.valid_child(parent1))
                #print('valid parent 2 : ', self.valid_child(parent2))

                child1 = parent1[:crossover_point] + parent2[crossover_point:]
                child2 = parent2[:crossover_point] + parent1[crossover_point:]

                #print('valid child 1 : ', self.valid_child(child1))
                #print('valid child 2 : ', self.valid_child(child2))


                # Mutation: Modify a random gene (action sequence) in each child
                if random.random() < 0.3:  # 10% mutation rate
                    replace_index = random.randint(0, len(child1) - 1)
                    child1[replace_index] = self.mutation_helper(child1, replace_index)

                    #print('valid child 1 mutation: ', self.valid_child(child1))

                if random.random() < 0.3:
                    replace_index = random.randint(0, len(child2) - 1)
                    child2[replace_index] = self.mutation_helper(child2, replace_index)

                    #print('valid child 2 mutation: ', self.valid_child(child2))

                if self.valid_child(child1):
                    new_population.extend([child1])
                if self.valid_child(child2):
                    new_population.extend([child2])

            population = new_population

        # Select the best solution
        best_chromosome = max(population, key=self.fitness_function)
        # Execute the best action sequence
        """
        print("_________best chromozone_____________")
        for _, val in enumerate(best_chromosome):
            act, cost, state = val
            for i, a in enumerate(act):
                print(f"{_}/{i} . {self.simulator.actionStringRepresentor.represent(a)}")

            print("\n")
        """

        joint_action, _, state = best_chromosome[0]
        #self.simulator.advance_state(joint_action, state)
        self.simulator.current_state = state.copy()

        self.plan_sequence.append(joint_action)

        action_str = []
        for i, a in enumerate(joint_action):
            action_str.append(self.simulator.actionStringRepresentor.represent(a))

        #print('selected action: ', action_str)
        #print('new_state simulator:', self.simulator.current_state)
        #print('\n')
        x = 1


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