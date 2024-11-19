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
        self.population = []
        self.elite_size = max(1, self.population_size * 30 // 100) 
        self.selected_size = self.population_size // 2
        self.best_sol = None
        self.best_fitness = (-1) * np.inf
        self.flag_h = kwargs.get('flag_h', True)
        self.restart_counter = 0

    def initialize_population(self, initial_state, **kwargs):
        self.prev_state_chrom = initial_state

        horizon = kwargs.get('horizon',  self.planning_horizon)
        size = kwargs.get('size',  self.population_size)

        if isinstance(self.searchEngine, PartialAssigner):
            if self.flag_h:
                search_results = self.searchEngine.produce_paths_heuristic(initial_state, horizon, size)
            else:
                search_results = self.searchEngine.produce_paths(initial_state, horizon, size)
        else:
            try:
            # Initialize the search algorithm here
                search_results = self.searchEngine.search(initial_state, steps=round(self.maxPlanLength * 1.5),
                                                maxStates=self.maxPlanLength * 10,
                                                iterTime = self.iterTime - 5)
            except Exception as e:
                logging.error(f"Error during planning: {e}", exc_info=True)


        population = list(self.successors_genetic(initial_state, search_results, self.flag_h))  
        return population

    def successors_genetic(self, state, search_results, flag_h, steps=1, max_states=1500):
        """
        Generate successors for the current state by using PartialAssigner's vehicle splitting
        and decompose the results to provide transitions, costs, and states for each step.
        """
        
        decomposed_successors = []

        for succsesor in search_results:
            states_tuples, transitions, costs = succsesor[:3]
            init_state, new_state = states_tuples
            current_state = state.__copy__()
            stepwise_results = []

            for i, transition in enumerate(transitions):
                succeeded = True

                # Apply the transition to the current state
                for action in transition:
                    try:
                        if action.reValidate(self.searchEngine.problem, current_state):
                            action.apply(self.searchEngine.problem, current_state)
                        else:
                            succeeded = False
                            break
                    except Exception:
                        succeeded = False
                        break

                if succeeded:
                    # Append the transition, cost, and state after applying this transition
                    transition_cost = costs[i] if i < len(costs) else 0
                    stepwise_results.append((transition, transition_cost, current_state.__copy__()))
                else:
                    # If any transition fails to apply, skip further processing
                    break

            if len(stepwise_results) == len(transitions):
                # If all transitions succeeded, add the full sequence to decomposed_successors
                decomposed_successors.append(stepwise_results)
        return decomposed_successors

    '''
    def fitness_function(self, chromosome):
        """Evaluates fitness based on task completion, cost, collision avoidance, and unnecessary waiting."""

        score = (-1) * chromosome[-1][1]
        for actions, _, state in chromosome:
            countVehicles, countNotVehicles, vehiclelist = self.simulator.problem.countsPackagesOfEntities(state) 
            for i, action in enumerate(actions):
                if action.baseAction == 'Wait':
                    try:
                        if  countNotVehicles > 0 or vehiclelist[i]:
                            score -= 20* countNotVehicles
                    except:
                        x = 1 #(continue)
                elif action.baseAction == 'Pick':
                    score += 300 
                elif action.baseAction == 'Deliver':
                    score += 200
        return score
    '''
    

    def fitness_function(self, chromosome, winner=False):
        """
        Evaluates fitness based on task completion, cost, collision avoidance, and unnecessary waiting.
        """

        total_cost = chromosome[-1][1]
        total_picks = 0
        total_delivers = 0
        total_waits = 0
        plan_length = len(chromosome)
        action_availability_bonus = 0
        picked_packages = set()
        duplicate_pick_penalty = 0

        # Save the current simulator state to restore it later
        prev = self.simulator.current_state.__copy__()

        for transition, _, state in chromosome:
            # Set the simulator's current state to the state's copy
            self.simulator.current_state = state.__copy__()

            # Generate all valid transitions (list of transitions)
            valid_transitions = self.simulator.generate_all_valid_actions()

            # Flatten actions in all valid transitions for analysis
            available_actions = [action for trans in valid_transitions for action in trans]

            available_pick = any(act.baseAction == 'Pick' for act in available_actions)
            available_deliver = any(act.baseAction == 'Deliver' for act in available_actions)
            action_has_pick = any(act.baseAction == 'Pick' for act in transition)
            action_has_deliver = any(act.baseAction == 'Deliver' for act in transition)

            # Action availability bonus or penalty
            if available_pick:
                if action_has_pick:
                    action_availability_bonus += 100  # Bonus for picking when possible
                else:
                    action_availability_bonus -= 50   # Penalty for not picking when possible

            if available_deliver:
                if action_has_deliver:
                    action_availability_bonus += 100  # Bonus for delivering when possible

                else:
                    action_availability_bonus -= 50   # Penalty for not delivering when possible


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
        self.simulator.current_state = prev

        # Compute fitness
        fitness = (
            -total_cost
            + 300 * total_picks
            + 500 * total_delivers
            - 10 * total_waits
            #+ action_availability_bonus
            - duplicate_pick_penalty
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
            print(f"Calculated Fitness: {fitness}")
            print("----------")
        return fitness

    def print_picks(self, chromosome):
        """Evaluates fitness based on task completion, cost, collision avoidance, and unnecessary waiting."""
        a = []
        for actions, _, state in chromosome:
            for i, action in enumerate(actions):
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
            self.initialize_population(
                parent_state, 
                horizon=self.planning_horizon - crossover_point, 
                size=5
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

        if len(self.population) == 0 :
            population = self.initialize_population(initial_state)
        
        #if self.generations % 3 == 0:
        #    population.extend(self.initialize_population(self.simulator.current_state)[:self.population_size // 2])



        # Evaluate fitness
        
        fitness_scores = [self.fitness_function(c) for c in population]
        '''
        try:
            min_score = min(fitness_scores)
            if min_score <= 0:
                fitness_scores = [score - min_score + 1 for score in fitness_scores]
                total_fitness = sum(fitness_scores)
                fitness_scores = [score / total_fitness for score in fitness_scores]
        except ValueError:
            print("Error: Population is empty.")
            return
        '''

        fitnees_val = max(fitness_scores)
        best = population[fitness_scores.index(fitnees_val)]
        
        if fitnees_val > self.best_fitness:
            print("_____current_winner____")
            self.print_picks(best)
            self.fitness_function(best, True)
            self.best_fitness = fitnees_val
            self.best_sol = best
            self.plan_sequence = [joint_action for joint_action,_,_ in best]

            self.restart_counter = 0
        else:
            self.restart_counter += 1

        #_, _, state  = best[-1]
        #self.simulator.current_state = state.__copy__()

        if self.restart_counter > 5:
            self.population = []
            self.restart_counter = 0
            print('restarting population....')
            return 


        # Selection
        selected_population = self.tournament_selection(population, fitness_scores, self.population_size // 2)
        #elites = sorted(population, key=self.fitness_function, reverse=True)[:self.elite_size]
            
        num_offspring = self.population_size - len(selected_population)
        offspring = self.crossover_mutation(selected_population, num_offspring)

        # New population
        population = selected_population + offspring

        # Elitism
        if self.best_sol not in population:
            population.append(self.best_sol)

        population = sorted(population, key=self.fitness_function, reverse=True)[:self.population_size]
          

    @override
    def generate_plan(self, state)-> List[List['Action']]:
        """Main planning loop with the GA integrated."""

        start_time =  time.time()
        self.plan_sequence = []
        self.simulator.current_state = state.__copy__()
        self.generations = 0
        self.fitness_cache = {}
        self.population = []
        self.best_fitness = (-1) * np.inf
        self.best_sol = None
        self.restart_counter = 0

        while  time.time() - start_time < self.iterTime - 5:
        #for iteration in range(max_iterations):
            print(f"Planning Step : {self.generations}")
            self.run_ga(self.simulator.current_state)
            self.generations+= 1

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
