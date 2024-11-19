import time
import random
import logging
from typing import List, Type
from overrides import override
import numpy as np
from CARRI import Action
from heuristics import *
from search import *
import logging
from typing import List, Type

class SearchEngineBasedPlanner:
    def __init__(self, simulator, iterTime: int, transitionsPerIteration: int, searchAlgorithmClass: Type['SearchEngine'], **kwargs):
        """
        :param simulator: An instance of CARRISimulator
        :param iterTime: float, time allowed for each iteration
        :param transitionsPerIteration: int, maximum plan length per iteration
        """
        self.simulator = simulator
        self.iterTime = iterTime
        self.maxPlanLength = transitionsPerIteration

        # Store the search algorithm as a reference, not an instance
        searchEngineClass = kwargs.get('searchAlgorithm', searchAlgorithmClass)
        self.searchEngine = searchEngineClass(simulator, **kwargs)

    def generate_plan(self, state) -> List[List['Action']]:
        """
        Generate a plan within the time limit using the provided search algorithm and heuristic.
        :return: A list representing the plan (sequence of actions).
        """
        try:
            # Initialize the search algorithm here
            plan = self.searchEngine.search(state, steps=round(self.maxPlanLength * 1.5),
                                            maxStates=self.maxPlanLength * 10,
                                            iterTime = self.iterTime - 5)
            return plan

        except Exception as e:
            logging.error(f"Error during planning: {e}", exc_info=True)


class GeneticPlanner(SearchEngineBasedPlanner):
    def __init__(self, simulator, iterTime: int, transitionsPerIteration: int, searchAlgorithmClass: Type['SearchEngine'],
                  population_size=20, generations=3, **kwargs):
        
        super().__init__(simulator, iterTime, transitionsPerIteration, searchAlgorithmClass, **kwargs)
        self.population_size = population_size
        self.planning_horizon = transitionsPerIteration
        self.generations = generations
        self.prev_state_chrom = self.simulator.current_state
        self.plan_sequence = []

    def initialize_population(self, initial_state):
        self.prev_state_chrom = initial_state
        population = list(self.searchEngine.successors_genetic(initial_state, self.planning_horizon, self.population_size, True))      
        return population


    def fitness_function(self, chromosome):
        """Evaluates fitness based on task completion, cost, collision avoidance, and unnecessary waiting."""

        score = (-1) * chromosome[-1][1]

        #print("___________")
        for actions, _, state in chromosome:
            countVehicles, countNotVehicles, vehiclelist = self.simulator.problem.countsPackagesOfEntities(state) 
            for i, action in enumerate(actions):
                if action.baseAction == 'Wait':
                    try:
                        if  countNotVehicles > 0 or vehiclelist[i]:
                            score -= 20* countNotVehicles
                    except:
                        x = 1
                elif action.baseAction == 'Pick':
                    score += 300 
                    #print('Pick')
                    '''
                        if tuple(action.params) not in package_picks:
                            package_picks.add(tuple(action.params))
                            score += 300   
                        else:
                            score -= 100
                    '''
                elif action.baseAction == 'Deliver':
                    score += 200
                    #print('Deliver')

        #print(score)
        return score
    

    def print_picks(self, chromosome):
        """Evaluates fitness based on task completion, cost, collision avoidance, and unnecessary waiting."""

        score = (-1) * chromosome[-1][1]
        a = []
        #print("___________")
        for actions, _, state in chromosome:
            countVehicles, countNotVehicles, vehiclelist = self.simulator.problem.countsPackagesOfEntities(state) 
            for i, action in enumerate(actions):
                if action.baseAction == 'Wait':
                    try:
                        if  countNotVehicles > 0 or vehiclelist[i]:
                            score -= 20* countNotVehicles
                    except:
                        x = 1
                elif action.baseAction == 'Pick':
                    score += 300 
                    a.append('Pick')
                    #print('Pick')
                    '''
                        if tuple(action.params) not in package_picks:
                            package_picks.add(tuple(action.params))
                            score += 300   
                        else:
                            score -= 100
                    '''
                elif action.baseAction == 'Deliver':
                    score += 200
                    a.append('Deliver')
                    #print('Deliver')

        a.append(score)
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
        #num_to_generate = self.population_size - len(selected_population)
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
        child = parent[:crossover_point]

        # Optimize state copying using shallow copy
        parent_state = parent[crossover_point][2].__copy__()

        rest_of_child_candidates = list(
            self.searchEngine.successors_genetic(
                parent_state, 
                self.planning_horizon - crossover_point, 
                5
            )
        )

        # Early filtering of invalid candidates
        #valid_candidates = [candidate for candidate in rest_of_child_candidates if self.valid_child(child + candidate)]

        if not rest_of_child_candidates:
           return None

        child.extend(random.choice(rest_of_child_candidates))
        return child

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
            print(generation)
            # Adjusted elite size to 30% of the population size
            elite_size = max(1, self.population_size * 30 // 100)
            
            # Select the elites based on fitness
            elites = sorted(population, key=self.fitness_function, reverse=True)[:elite_size]
            
            # Every two generations, extend the population with new random individuals
            if generation % 2 == 0:
                population.extend(self.initialize_population(self.simulator.current_state)[:self.population_size // 2])

            # Calculate fitness scores in parallel

            fitness_scores = []
            for c in population:
                fitness_scores.append(self.fitness_function(c))

            # Normalize fitness scores to avoid negatives
            try:
                min_score = min(fitness_scores)
            except ValueError:
                print("Error: Population is empty.")
                return
            
            if min_score <= 0:
                fitness_scores = [score - min_score + 1 for score in fitness_scores]

            total_fitness = sum(fitness_scores)
            fitness_scores = [score / total_fitness for score in fitness_scores]

            # Select 70% of the population for reproduction: 55% unmutated and 15% mutated
            selected_size = self.population_size * 70 // 100
            selected_population = self.stochastic_universal_sampling(population, fitness_scores, selected_size)

            # Apply mutation to 15% of the total population
            start = time.time()
            num_to_mutate = self.population_size * 15 // 100
            population_to_mutate = random.sample(selected_population, num_to_mutate)
            mutated_population = self.crossover_mutation(population_to_mutate, num_to_mutate)
            #print("took mutation:", time.time() - start)

            # Assemble the new population: elites, mutated, and remaining unmutated selected individuals
            unmutated_population = [ind for ind in selected_population if ind not in population_to_mutate][:self.population_size - elite_size - num_to_mutate]
            population = elites + unmutated_population + mutated_population

        # Select the best individual and update the simulator’s state
        best = max(population, key=self.fitness_function)
        print("_____winner____")
        self.print_picks(best)
        _, _, state  = best[-1]
        self.simulator.current_state = state.__copy__()
        self.plan_sequence.extend([joint_action for joint_action,_,_ in best])


    @override
    def generate_plan(self, state)-> List[List['Action']]:
        """Main planning loop with the GA integrated."""

        start_time =  time.time()
        self.plan_sequence = []
        self.simulator.current_state = state.__copy__()
        iteration = 0
        self.fitness_cache = {}
        
        #while  time.time() - start_time < self.iterTime - 0.5:
        #for iteration in range(max_iterations):
        print(f"Planning Step : {iteration}")
        self.run_ga(self.simulator.current_state)
        iteration+= 1

        return self.plan_sequence

        

class Planner:
    def __init__(self, simulator, iter_t, transitions_per_iteration, **kwargs):
        """
        :param simulator: An instance of CARRISimulator
        :param init_time: float, time of initialization
        :param iter_t: float, time allowed for each iteration
        """
        self.simulator = simulator
        self.iter_t = iter_t
        # Allow search algorithm and heuristic to be passed for flexibility

        self.heuristic = kwargs.get('heuristic', RequestCountHeuristic(self.simulator.problem))
        # Store the search algorithm as a reference, not an instance
        self.search_algorithm_class = kwargs.get('search_algorithm', a_star_search)
        
        self.max_plan_length = transitions_per_iteration
        self.plan = None

    def init(self):
        return 

    def generate_plan(self):
        """
        Generate a plan within the time limit using the provided search algorithm and heuristic.
        :return: A list representing the plan (sequence of actions).
        """
        start_time = time.time()
        plan = []

        try:
            # Initialize the search algorithm here
            search = self.search_algorithm_class(self.simulator, self.heuristic, self.iter_t)
            print(search)
            return search
        
        except Exception as e:
            logging.error(f"Error during planning: {e}", exc_info=True)

    def run_iteration(self, init_state):
        """
        Execute a planning iteration.
        :return: None
        """
        try:
            self.simulator.current_state = init_state
            plan = self.generate_plan()
        except Exception as e:
            print(e)
            logging.error("An error occurred during planning:", exc_info=True)  # Logs the full stack trace
        if not plan:
            logging.warning("No valid plan was generated.")
        else:
            for action in plan:
                try:
                    self.simulator.advance_state(action)
                except ValueError as e:
                    logging.warning(f"Failed to apply action {action}: {e}")
                    break
        
        return plan
