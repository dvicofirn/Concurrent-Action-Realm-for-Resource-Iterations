import random
from typing import List, Tuple
from collections import deque
from .searchEngine import SearchEngine
from CARRI import Simulator, State, Action

class PartialAssigner:
    def __init__(self, simulator: Simulator, **kwargs):
        self.simulator = simulator
        self.problem = simulator.problem
        self.vehicleTypes = self.problem.vehicleEntities
        self.lenVehicleTypes = len(self.vehicleTypes)
        self.minSplitLen = kwargs.get('minSplitLen', 1)
        self.maxSplitLen = kwargs.get('maxSplitLen', 3)
        self.minAdvanceStep = kwargs.get('minAdvanceStep', 1)
        self.maxAdvanceStep = kwargs.get('maxAdvanceStep', 4)


    def split_vehicles(self, state) -> List[List[Tuple]]:
        # List to hold all the splits per vehicle type
        # Collect vehicle IDs per type
        vehicleIds = [] # List of iterables
        for type in self.vehicleTypes:
            # Convert keys to a list to enable slicing
            vehicleIds.append(list(self.problem.get_entity_ids(state, type)))
        all_splits = []

        # Iterate over each list of vehicle IDs for each type
        for ids in vehicleIds:
            type_splits = []
            i = 0

            # Group IDs into tuples of size 1-3
            while i < len(ids):
                # Choose a random size for the group (1-3) while respecting remaining ids
                group_size = min(random.randint(self.minSplitLen, self.maxSplitLen), len(ids) - i)
                type_splits.append(tuple(ids[i:i + group_size]))
                i += group_size

            # Append the split list for this vehicle type
            all_splits.append(type_splits)

        return all_splits

    def produce_paths(self, initState: State, steps: int, maxStates: int):
        splits = self.split_vehicles(initState)
        searchQueue = deque([([initState, None],
                              [[] for _ in range(steps)],
                              [0 for _ in range(steps)],
                              [0 for _ in range(steps)])])
        currentStep = 0
        while currentStep < steps:
            stopStep = currentStep + min(random.randint(self.minAdvanceStep, self.maxAdvanceStep), steps - currentStep)
            for typeIndex, (vehicleType, vehicleTypeSplit) in enumerate(zip(self.vehicleTypes, splits)):
                lenSplits = len(vehicleTypeSplit)
                for splitIndex, split in enumerate(vehicleTypeSplit):
                    for step in range(currentStep, stopStep):
                        nextSearches = []
                        while searchQueue:
                            state2, currentTransitions, currentCosts, currentNCosts = searchQueue.pop()
                            if step == currentStep:
                                state = state2[0].__copy__()
                            else:
                                state = state2[1]
                            invalid = False
                            for action in currentTransitions[step]:
                                try:
                                    if action.validate(self.problem, state):
                                        action.apply(self.problem, state)
                                    else:
                                        invalid = True
                                        break
                                except Exception as e:
                                    invalid = True
                                    break
                            if invalid:
                                continue
                            currentSearch = self.simulator.generate_partial_successors(state, vehicleType, split)
                            afterEnvResult = self.simulator.applyEnvSteps(currentSearch)
                            for state, transition, cost, nCost in afterEnvResult:
                                nextTransitionStep = currentTransitions[step].copy()
                                nextTransitionStep.extend(transition)
                                nextNCost = nCost + currentNCosts[step - 1] if step > 0 else nCost
                                lastNCost = currentNCosts[step]
                                if splitIndex == lenSplits - 1 and typeIndex == self.lenVehicleTypes - 1 and step == stopStep - 1:
                                    state2[0] = state
                                nextSearches.append((
                                    [state2[0], state],
                                    currentTransitions[:step] + [nextTransitionStep] + currentTransitions[step + 1:],
                                    currentCosts[:step] + [cost + lastCost for lastCost in currentCosts[step:]],
                                    currentNCosts[:step] + [nextNCost] + [nextNCost - lastNCost + cost for cost in
                                                                          currentNCosts[step + 1:]]
                                ))
                        if len(nextSearches) > maxStates:
                            nextSearches = random.sample(nextSearches, maxStates)
                        searchQueue.extend(nextSearches)
                    searchQueue = (sorted(searchQueue, key=lambda x: x[2][-1] + x[3][-1])[:maxStates])
            currentStep = stopStep
        return searchQueue


    def fitness_score(self, actions: List[Action]) -> int:
        """
        Calculates the fitness score based on the number of Pick and Deliver actions
        and penalizes Wait actions.
        """
        score = 0
        for action in actions:
            if action.baseAction == 'Pick':
                score -= 4  # Reward for Pick
            elif action.baseAction == 'Deliver':
                score -= 10  # Reward for Deliver
            elif action.baseAction == 'Wait':
                score += 6  # Penalty for Wait
        return score



    def produce_paths_heuristic(self, initState: State, steps: int, maxStates: int):
        splits = self.split_vehicles(initState)
        searchQueue = deque([([initState, None],
                              [[] for _ in range(steps)],
                              [0 for _ in range(steps)],
                              [0 for _ in range(steps)], 0.0)])
        currentStep = 0
        while currentStep < steps:
            stopStep = currentStep + min(random.randint(self.minAdvanceStep, self.maxAdvanceStep), steps - currentStep)
            for typeIndex, (vehicleType, vehicleTypeSplit) in enumerate(zip(self.vehicleTypes, splits)):
                lenSplits = len(vehicleTypeSplit)
                for splitIndex, split in enumerate(vehicleTypeSplit):
                    for step in range(currentStep, stopStep):
                        nextSearches = []
                        while searchQueue:
                            state2, currentTransitions, currentCosts, currentNCosts, h = searchQueue.pop()
                            if step == currentStep:
                                state = state2[0].__copy__()
                            else:
                                state = state2[1]
                            invalid = False
                            for action in currentTransitions[step]:
                                try:
                                    if action.validate(self.problem, state):
                                        action.apply(self.problem, state)
                                    else:
                                        invalid = True
                                        break
                                except Exception as e:
                                    invalid = True
                                    break
                            if invalid:
                                continue
                            currentSearch = self.simulator.generate_partial_successors(state, vehicleType, split)
                            afterEnvResult = self.simulator.applyEnvSteps(currentSearch)
                            for state, transition, cost, nCost in afterEnvResult:
                                nextTransitionStep = currentTransitions[step].copy()
                                nextTransitionStep.extend(transition)
                                nextNCost = nCost + currentNCosts[step - 1] if step > 0 else nCost
                                lastNCost = currentNCosts[step]

                                new_heuristic = h + 100* self.fitness_score(transition)

                                if splitIndex == lenSplits - 1 and typeIndex == self.lenVehicleTypes - 1 and step == stopStep - 1:
                                    state2[0] = state
                                nextSearches.append((
                                    [state2[0], state],
                                    currentTransitions[:step] + [nextTransitionStep] + currentTransitions[step + 1:],
                                    currentCosts[:step] + [cost + lastCost for lastCost in currentCosts[step:]],
                                    currentNCosts[:step] + [nextNCost] + [nextNCost - lastNCost + cost for cost in
                                                                          currentNCosts[step + 1:]], new_heuristic
                                ))
                        if len(nextSearches) > maxStates:
                            nextSearches = random.sample(nextSearches, maxStates)
                        searchQueue.extend(nextSearches)
                    searchQueue = (sorted(searchQueue, key=lambda x: x[2][-1] + x[3][-1] + x[4])[:maxStates])
            currentStep = stopStep
        return searchQueue

    def search(self, state: State, **kwargs) -> List[List[Action]]:
        paths = []
        steps = kwargs.get('steps', 5)
        maxStates = kwargs.get('maxStates', 10)
        multiplication = kwargs.get('multiplication', 1.25)
        while not paths:
            paths = self.produce_paths(state, steps, maxStates)
            maxStates = round(maxStates * multiplication)
        return paths[0][1]

    def provideTransitionsAndCost(self, state: State, **kwargs) -> Tuple[List[List[Action]], int]:
        paths = []
        steps = kwargs.get('steps', 5)
        maxStates = kwargs.get('maxStates', 10)
        multiplication = kwargs.get('multiplication', 1.25)
        while not paths:
            paths = self.produce_paths(state, steps, maxStates)
            maxStates = round(maxStates * multiplication)
        path = paths[0]
        return (path[1], sum(path[2]) + sum(path[3]))