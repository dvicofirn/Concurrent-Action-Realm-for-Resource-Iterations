from .planner import *
import random
import numpy as np
from collections import Counter
from collections import defaultdict


class GeneticPlanner(AssigningPlanner):
    def __init__(self, simulator, iterTime: float, transitionsPerIteration: int, **kwargs):

        super().__init__(simulator, iterTime, transitionsPerIteration, **kwargs)
        self.population_size = kwargs.get('population_size', 20)
        self.planning_horizon = max(2, transitionsPerIteration)
        self.transitionsPerIteration = transitionsPerIteration
        self.generations = kwargs.get('generations', 3)
        self.prev_state_chrom = self.simulator.current_state
        self.planSequence = []
        self.population = []
        self.elite_size = max(1, self.population_size * 3 // 10)
        self.selected_size = self.population_size // 2
        self.best_sol = None
        self.best_fitness = (-1) * np.inf
        self.restart_counter = 0
        self.avg_cost = 0
        self.vehicle_types = self.simulator.problem.get_vehicle_types()

        try:
            self.loc_type, adjacency_tuple = self.simulator.problem.get_consts()
            # Compute type-based distances and sinks
            type_distances , self.type_sinks = self.compute_type_based_distances(self.loc_type, adjacency_tuple,
            																	 set(self.vehicle_types))

        except:
            self.type_sinks = {}
            self.loc_type = []

    def detect_dynamic_sinks(self, loc_type, adjacency_tuple, vehicle_types):
        """
        Identify sinks for each vehicle type dynamically by analyzing reachability.
        :param loc_type: Tuple defining the type of each location.
        :param adjacency_tuple: Adjacency list representation of the graph.
        :param vehicle_types: List of vehicle types.
        :return: Dictionary {vehicle_type: set(sink_locations)}
        """
        num_locations = len(adjacency_tuple)
        sinks = {v_type: set() for v_type in vehicle_types}

        for v_type in vehicle_types:
            accessible_nodes = {i for i, t in enumerate(loc_type) if t == 0 or t == v_type}

            for start_loc in range(num_locations):
                if start_loc not in accessible_nodes:
                    continue  # Skip locations not accessible to the current vehicle type

                visited = set()
                stack = [start_loc]
                is_sink = True

                while stack:
                    current = stack.pop()
                    if current in visited:
                        continue
                    visited.add(current)

                    neighbors = adjacency_tuple[current]
                    if isinstance(neighbors, dict):  # Weighted graph
                        neighbors = neighbors.keys()

                    valid_neighbors = [
                        n for n in neighbors if n in accessible_nodes and n not in visited
                    ]

                    if valid_neighbors:
                        is_sink = False  # Found a valid exit, not a sink
                        break
                    stack.extend(valid_neighbors)

                if is_sink:
                    sinks[v_type].add(start_loc)

        return sinks

    def compute_all_pairs_shortest_distances(self, adjacency_tuple):
        num_nodes = len(adjacency_tuple)

        if num_nodes == 0:
            return {}, set()  # Return an empty dictionary and no sinks

        first_entry = adjacency_tuple[0]
        is_weighted = isinstance(first_entry, dict)

        # Initialize distance matrix
        distance = defaultdict(lambda: defaultdict(lambda: float('inf')))
        outgoing_edges = {node: 0 for node in range(num_nodes)}  # Track outgoing edges

        for from_node in range(num_nodes):
            distance[from_node][from_node] = 0  # Distance to self is zero
            neighbors = adjacency_tuple[from_node]

            if is_weighted:
                for to_node, weight in neighbors.items():
                    distance[from_node][to_node] = weight
                    outgoing_edges[from_node] += 1
            else:
                for to_node in neighbors:
                    distance[from_node][to_node] = 1  # Unweighted edge has weight 1
                    outgoing_edges[from_node] += 1

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

        # Identify sinks (nodes with no outgoing edges)
        sinks = {node for node, out_degree in outgoing_edges.items() if out_degree == 0}

        # Construct the result dictionary
        distance_dict = {}
        for from_node in range(num_nodes):
            for to_node in range(num_nodes):
                dist = distance[from_node][to_node]
                if dist != float('inf'):
                    distance_dict[(from_node, to_node)] = dist
                else:
                    distance_dict[(from_node, to_node)] = None  # or use sys.maxsize or another indicator

        return distance_dict, sinks


    def compute_type_based_distances(self, locType, adjacency_tuple, vehicle_types):
        type_distance_dicts = {}
        type_sinks = {}

        num_nodes = len(adjacency_tuple)

        # Dynamic sinks detection
        dynamic_sinks = self.detect_dynamic_sinks(locType, adjacency_tuple, vehicle_types)

        for v_type in vehicle_types:
            # Determine accessible nodes: type 0 and the current vehicle type
            accessible_nodes = {node for node, t in enumerate(locType) if t == 0 or t == v_type}

            # Create a filtered adjacency tuple for the current vehicle type
            filtered_adjacency = []
            for from_node in range(num_nodes):
                if from_node not in accessible_nodes:
                    filtered_adjacency.append({})
                    continue  # Skip inaccessible nodes
                neighbors = adjacency_tuple[from_node]
                if isinstance(neighbors, dict):
                    # Weighted graph
                    filtered_neighbors = {to_node: weight for to_node, weight in neighbors.items() if to_node in accessible_nodes}
                else:
                    # Unweighted graph
                    filtered_neighbors = {to_node for to_node in neighbors if to_node in accessible_nodes}
                filtered_adjacency.append(filtered_neighbors)

            # Compute all pair shortest distances and static sinks for the filtered adjacency
            distance_dict, static_sinks = self.compute_all_pairs_shortest_distances(filtered_adjacency)

            # Merge static and dynamic sinks
            combined_sinks = static_sinks.union(dynamic_sinks[v_type])

            # Store in the result dictionaries
            type_distance_dicts[v_type] = distance_dict
            type_sinks[v_type] = combined_sinks

        return type_distance_dicts, type_sinks



    def initialize_population(self, initial_state, **kwargs):
        self.prev_state_chrom = initial_state
        horizon = kwargs.get('horizon', self.planning_horizon)
        size = kwargs.get('size', self.population_size)
        population =[]
        while not population:
            population = self.partialAssigner.produce_paths_heuristic(initial_state, horizon, size)
        self.avg_cost = sum(
            [sum(chromosome[2]) + sum(chromosome[3]) for chromosome in population]) / len(population)
        return population

    def fitness_function(self, chromosome, winner=False):
        total_cost = sum(chromosome[2]) + sum(chromosome[3])
        total_picks = 0
        total_delivers = 0
        total_waits = 0
        plan_length = len(chromosome[1])
        picked_packages = set()
        duplicate_pick_penalty = 0
        special_loc_reward = 0
        sink_penalty = 0

        for step_idx, transition in enumerate(chromosome[1]):
            for vehicle_idx, action in enumerate(transition):
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
                
                elif action.baseAction == 'Travel':
                    if len(self.type_sinks.values()) == 0 :
                        continue
                    destinations = [action.params[j].value for j in range(len(action.params))]
                    vehicle_type =self.vehicle_types[vehicle_idx]
 
                    for destination in destinations:
                        if destination in self.type_sinks.get(vehicle_type):
                            sink_penalty += 1

        locations = self.simulator.problem.get_locations(chromosome[0][0])
        #within
        same_loc = []
        for location in locations:
            frequency = Counter(location)
            duplicates = sum(count - 1 for count in frequency.values() if count > 1)
            same_loc.append(duplicates * len(location))
        duplicate_locations_penalty = sum(same_loc)

        #intra
        all_len = sum([len(x) for x in locations])
        duplicate_locations_reward = 0
        if len(locations) > 1:
                location_route_map = {}
                for route_idx, route in enumerate(locations):
                    unique_locs = set(route)
                    for loc in unique_locs:
                        if loc in location_route_map:
                            location_route_map[loc].add(route_idx)
                        else:
                            location_route_map[loc] = {route_idx}
        
                for loc, route_indices in location_route_map.items():
                    if len(route_indices) > 1:
                        # Total occurrences across all routes
                        total_occurrences = sum(route.count(loc) for route in locations)
                        reward = total_occurrences * all_len
                        duplicate_locations_reward += reward

        #special location 
        special_dict = {}
        keys = [special for special in self.loc_type if special != 0]
        special_dict = {key : [] for key in keys}
        for key in keys:
            for i, type in enumerate(self.loc_type):
                if type == key:
                    special_dict[key].append(i)

        if len(special_dict) > 0 :
            for j, vehicle_loc in enumerate(locations):
                dict_loc = special_dict[j+1]
                special_loc_reward += len(set(vehicle_loc).intersection(set(dict_loc)))
                    


        # Compute fitness
        unit = total_cost
        fitness = (
                - total_cost
                + 3* unit * total_picks
                + 8* unit * total_delivers
                - unit * 0.01 * total_waits
                - duplicate_pick_penalty
                - unit * 0.01 * duplicate_locations_penalty
                - unit * 0.5 * sink_penalty
        )

        try: n_fitness = fitness/ (100 * unit) 
        except: n_fitness = (-1) *np.inf

        return n_fitness / plan_length

    def valid_child(self, child):
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
        if num_to_mutate <= 0:
            return selected_population

        # Select parents and crossover points
        parents = random.choices(selected_population, k=num_to_mutate)
        crossover_points = random.choices(range(1, self.planning_horizon - 1), k=num_to_mutate)

        new_children = []
        for parent, crossover_point in zip(parents, crossover_points):
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

        # Evaluate fitness
        fitness_scores = [self.fitness_function(c) for c in population]
        fitnees_val = max(fitness_scores)

        threshold = 5
        best = population[fitness_scores.index(fitnees_val)]

        if fitnees_val > self.best_fitness:
            self.best_fitness = fitnees_val
            self.best_sol = best
            self.planSequence = best[1]
            self.restart_counter = 0
        else:
            self.restart_counter += 1

        if self.restart_counter > threshold:
            self.population = []
            self.restart_counter = 0
            self.planning_horizon += 1
            return

        # Selection
        selected_population = self.tournament_selection(population, fitness_scores, max(1, len(population) // 2))

        num_offspring = self.population_size - len(selected_population)
        offspring = self.crossover_mutation(selected_population, num_offspring)

        # New population
        population = selected_population + offspring

        # Elitism
        if self.best_sol not in population:
            population.append(self.best_sol)

        population = sorted(population, key=self.fitness_function, reverse=True)[:self.population_size]

    def _generate_plan(self, state: State):
        self.planSequence = []
        self.simulator.current_state = state.__copy__()
        self.generations = 0
        self.population = []
        self.best_fitness = (-1) * np.inf
        self.best_sol = None
        self.restart_counter = 0
        #self.planning_horizon = self.transitionsPerIteration

        while True:
            self.run_ga(self.simulator.current_state)
            self.generations += 1
            self.planDict['plan'] = self.planSequence