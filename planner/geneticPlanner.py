from .planner import *
import logging
import random
import numpy as np
import time
from collections import Counter
from collections import defaultdict
import sys
class GeneticPlanner(AssigningPlanner):
    def __init__(self, simulator, iterTime: float, transitionsPerIteration: int, **kwargs):

        super().__init__(simulator, iterTime, transitionsPerIteration, **kwargs)
        self.population_size = kwargs.get('population_size', 20)
        self.planning_horizon = transitionsPerIteration
        self.generations = kwargs.get('generations', 3)
        self.prev_state_chrom = self.simulator.current_state
        self.planSequence = []
        self.population = []
        self.elite_size = max(1, self.population_size * 30  // 100)
        self.selected_size = self.population_size // 2
        self.best_sol = None
        self.best_fitness = (-1) * np.inf
        self.flag_h = kwargs.get('flag_h', True)
        self.restart_counter = 0

        adj_dict = self.simulator.problem.get_adj_dict()
        self.distances = self.compute_all_pairs_shortest_distances(adj_dict)

        print("Distances:")
        for key in sorted(self.distances.keys()):
            print(f"{key}: {self.distances[key]}")
        

    def initialize_population(self, initial_state, **kwargs):
        #populationTime = time.time()
        #print("start population")
        self.prev_state_chrom = initial_state

        horizon = kwargs.get('horizon', self.planning_horizon)
        size = kwargs.get('size', self.population_size)

        if self.flag_h:
            population = self.partialAssigner.produce_paths_heuristic(initial_state, horizon, size)
        else:
            population = self.partialAssigner.produce_paths(initial_state, horizon, size)

        #population = list(self.successors_genetic(initial_state, search_results, self.flag_h))

        #print("return population:", time.time() - populationTime)
        return population



    def compute_all_pairs_shortest_distances(self, adjacency_tuple):
        """
        Computes the shortest distance between every pair of nodes in a directed graph.

        Parameters:
        - adjacency_tuple: Tuple containing adjacency information.
            - Weighted Graph: Each element is a dict {to_node: weight, ...}
            - Unweighted Graph: Each element is a set {to_node, ...}

        Returns:
        - distance_dict: Dict with keys as (from_node, to_node) tuples and values as shortest distances.
        """
        num_nodes = len(adjacency_tuple)
        
        # Determine if the graph is weighted or not
        if num_nodes == 0:
            return {}
        
        first_entry = adjacency_tuple[0]
        is_weighted = isinstance(first_entry, dict)
        
        # Initialize distance matrix
        distance = defaultdict(lambda: defaultdict(lambda: float('inf')))
        
        for from_node in range(num_nodes):
            distance[from_node][from_node] = 0  # Distance to self is zero
            neighbors = adjacency_tuple[from_node]
            
            if is_weighted:
                for to_node, weight in neighbors.items():
                    distance[from_node][to_node] = weight
            else:
                for to_node in neighbors:
                    distance[from_node][to_node] = 1  # Unweighted edge has weight 1
        
        # Apply Floyd-Warshall Algorithm
        for k in range(num_nodes):
            for i in range(num_nodes):
                # Skip if there's no path from i to k
                if distance[i][k] == float('inf'):
                    continue
                for j in range(num_nodes):
                    # Skip if there's no path from k to j
                    if distance[k][j] == float('inf'):
                        continue
                    if distance[i][j] > distance[i][k] + distance[k][j]:
                        distance[i][j] = distance[i][k] + distance[k][j]
        
        # Construct the result dictionary
        distance_dict = {}
        for from_node in range(num_nodes):
            for to_node in range(num_nodes):
                dist = distance[from_node][to_node]
                if dist != float('inf'):
                    distance_dict[(from_node, to_node)] = dist
                else:
                    distance_dict[(from_node, to_node)] = None  # or use sys.maxsize or another indicator
        
        return distance_dict


    def fitness_function(self, chromosome, winner=False):
        """
        Evaluates fitness based on task completion, cost, collision avoidance, and unnecessary waiting.
        """
        #fitnessTime = time.time()
        #print("start fitness")
        total_cost = sum(chromosome[2]) + sum(chromosome[3])
        total_picks = 0
        total_delivers = 0
        total_waits = 0
        plan_length = len(chromosome[1])
        action_availability_bonus = 0
        picked_packages = set()
        duplicate_pick_penalty = 0

        # Save the current simulator state to restore it later
        #prev = self.simulator.current_state.__copy__()

        for transition in chromosome[1]:
            for action in transition:
                if action.baseAction == 'Pick':
                    package_id = action.params[1]
                    if package_id in picked_packages:
                        duplicate_pick_penalty += 10000  # Heavy penalty for duplicate picks

                    else:
                        picked_packages.add(package_id)
                        total_picks += 1

                elif action.baseAction == 'Deliver':
                    total_delivers += 1

                elif action.baseAction == 'Wait':
                    total_waits += 1

        # Restore the simulator's state
        #self.simulator.current_state = prev

        
        locations = self.simulator.problem.get_locations(chromosome[0][0])

        same_loc = []
        for location in locations:
            frequency = Counter(location)
            duplicates = sum(count - 1 for count in frequency.values() if count > 1)
            same_loc.append(duplicates * len(location))

        duplicate_locations = sum(same_loc)

        #scailing
        unit = total_cost
        # Compute fitness
        fitness = (
                -total_cost
                + 3* unit * total_picks
                + 8* unit * total_delivers
                - unit * 0.01 * total_waits
                # + action_availability_bonus
                - duplicate_pick_penalty
                - unit * 0.01 * duplicate_locations
        )

        if winner:
            print("Fitness Components:")
            print(f"Total Cost: {total_cost}")
            print(f"Total Picks: {total_picks}")
            print(f"Total Delivers: {total_delivers}")
            print(f"Total Waits: {total_waits}")
            print(f"Plan Length: {plan_length}")
            print(f"Action Availability Bonus: {action_availability_bonus}")
            print(f"Duplicate Pick Penalty: {duplicate_pick_penalty}")
            print(f"Duplicate Loction Penalty: {duplicate_locations}")
            print(f"Calculated Fitness: {fitness}")
            print("----------")
        #print("return fitness:", time.time() - fitnessTime)
        return fitness

    def print_picks(self, chromosome):
        """Evaluates fitness based on task completion, cost, collision avoidance, and unnecessary waiting."""
        a = []
        for transitions in chromosome[1]:
            for action in transitions:
                if action.baseAction == 'Pick':
                    a.append('Pick')

                elif action.baseAction == 'Deliver':
                    a.append('Deliver')
        print(a)

    def valid_child(self, child):
        """Validates the child plan by simulating transitions."""
        inner_state = self.simulator.current_state.__copy__()
        result = all(
            self.simulator.validate_Transition(
                child[index - 1][2] if index > 0 else self.prev_state_chrom.__copy__(),
                chrom[0]
            ) for index, chrom in enumerate(child)
        )
        self.simulator.current_state = inner_state
        return result

    def crossover_mutation(self, selected_population, num_to_mutate):
        """Performs crossover and mutation to generate new children for the population without using threads."""
        # num_to_generate = self.population_size - len(selected_population)
        if num_to_mutate <= 0:
            return selected_population

        # Select parents and crossover points
        parents = random.choices(selected_population, k=num_to_mutate)
        crossover_points = random.choices(range(1, self.planning_horizon - 1), k=num_to_mutate)

        new_children = []
        for parent, crossover_point in zip(parents, crossover_points):
            # Use copy.copy instead of deepcopy if possible to reduce overhead
            # Assuming generate_child handles necessary copying internally
            child = self.generate_child(parent, crossover_point)
            if child:
                new_children.append(child)

        selected_population.extend(new_children)
        return selected_population

    def generate_child(self, parent, crossover_point):
        """Generates a child plan by crossover and mutation."""
        seq = parent[1]
        child = seq[:crossover_point]


        #create_intermidiate state
        seq_initial_state = self.create_intermidiate_state(seq, crossover_point)
        if seq_initial_state is None:
            return None
        
        seed_mutation = [[seq_initial_state, seq_initial_state],
                         child, 
                         parent[2][:crossover_point],
                         parent[3][:crossover_point]]


        rest_of_child_candidates = list(
            self.initialize_population(
                seq_initial_state.__copy__(),
                horizon=self.planning_horizon - crossover_point,
                size=5, seed_mutation=seed_mutation
            )
        )

        if not rest_of_child_candidates:
            return None

        #TODO change to max heuristic value - make sure is different from parent
        chosen = random.choice(rest_of_child_candidates)

        # join
        child.extend(chosen[1])
        costs = parent[2][:crossover_point]
        add_costs = [costs[-1] + chosen[2][0]]
        if len(chosen[2]) > 1:
            for i in range(1,len(chosen[2])):
                add_costs.append(costs[-1] + chosen[2][i])
            
        costs.extend(add_costs)
        new_chromosone = [[chosen[0][0], chosen[0][0]],
                          child, 
                          costs,
                          parent[3]] 
        
        return new_chromosone
    

    def create_intermidiate_state(self, seq, crossover_point):
        state = self.simulator.current_state.__copy__()
        invalid =False
        for i in range(crossover_point):
            for action in seq[i]:
                try:
                    if action.validate(self.simulator.problem, state):
                        action.apply(self.simulator.problem, state)
                    else:
                        invalid = True
                        break
                except Exception as e:
                    invalid = True
                    break
        
        if invalid:
            return None

        return state

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

    def tournament_selection(self, population, fitness_scores, k, tournament_size=3):
        """
        Selects individuals for reproduction using tournament selection.
        """
        selected = []
        for _ in range(k):
            participants = random.sample(list(zip(population, fitness_scores)), tournament_size)
            winner = max(participants, key=lambda x: x[1])
            selected.append(winner[0])
        return selected

    def run_ga(self, initial_state):

        if len(self.population) == 0:
            population = self.initialize_population(initial_state)

        # if self.generations % 3 == 0:
        #    population.extend(self.initialize_population(self.simulator.current_state)[:self.population_size // 2])

        # Evaluate fitness
        fitness_scores = [self.fitness_function(c) for c in population]
        
        try:
            fitnees_val = max(fitness_scores)
        except ValueError:
            print("Error: Population is empty.")
            return
        

        
        best = population[fitness_scores.index(fitnees_val)]

        if fitnees_val > self.best_fitness:
            print("_____current_winner____")
            #self.print_picks(best)
            self.fitness_function(best, True)
            self.best_fitness = fitnees_val
            self.best_sol = best
            self.planSequence = best[1]

            self.restart_counter = 0
        else:
            self.restart_counter += 1

        # _, _, state  = best[-1]
        # self.simulator.current_state = state.__copy__()

        if self.restart_counter > 5:
            self.population = []
            self.restart_counter = 0
            print('restarting population....')
            return

            # Selection
        selected_population = self.tournament_selection(population, fitness_scores, self.population_size // 2)
        # elites = sorted(population, key=self.fitness_function, reverse=True)[:self.elite_size]

        num_offspring = self.population_size - len(selected_population)
        offspring = self.crossover_mutation(selected_population, num_offspring)

        # New population
        population = selected_population + offspring

        # Elitism
        if self.best_sol not in population:
            population.append(self.best_sol)

        population = sorted(population, key=self.fitness_function, reverse=True)[:self.population_size]

    def _generate_plan(self, state: State):
        """Main planning loop with the GA integrated."""
        self.planSequence = []
        self.simulator.current_state = state.__copy__()
        self.generations = 0
        self.fitness_cache = {}
        self.population = []
        self.best_fitness = (-1) * np.inf
        self.best_sol = None
        self.restart_counter = 0

        while True:
            # for iteration in range(max_iterations):
            print(f"Planning Step : {self.generations}")
            self.run_ga(self.simulator.current_state)
            self.generations += 1
            self.returnDict['plan'] = self.planSequence