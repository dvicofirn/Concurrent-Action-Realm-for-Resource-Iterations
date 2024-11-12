import random
from typing import List, Tuple
from collections import deque
from .searchEngine import SearchEngine
from CARRI import Simulator, Problem, State, Action


class PartialAssigner(SearchEngine):
    def __init__(self, simulator: Simulator, **kwargs):
        super().__init__(simulator, **kwargs)
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



    def successors_genetic(self, state, steps=1, max_states=1500):
        """
        Generate successors for the current state by using PartialAssigner's vehicle splitting
        and decompose the results to provide transitions, costs, and states for each step.
        """
        # Use PartialAssigner's `search` method to generate successors
        search_results = self.search(initState=state, steps=steps, maxStates=max_states)
        
        # Decompose the search results
        decomposed_successors = []

        for result_state, transitions, costs, ncosts in search_results:
            current_state = state.copy()
            stepwise_results = []

            for i, transition in enumerate(transitions):
                succeeded = True

                # Apply the transition to the current state
                for action in transition:
                    try:
                        if action.reValidate(self.problem, current_state):
                            action.apply(self.problem, current_state)
                        else:
                            succeeded = False
                            break
                    except Exception:
                        succeeded = False
                        break

                if succeeded:
                    # Append the transition, cost, and state after applying this transition
                    transition_cost = costs[i] if i < len(costs) else 0
                    stepwise_results.append((transition, transition_cost, deepcopy(current_state)))
                else:
                    # If any transition fails to apply, skip further processing
                    break

            if len(stepwise_results) == len(transitions):
                # If all transitions succeeded, add the full sequence to decomposed_successors
                decomposed_successors.append(stepwise_results)

        return decomposed_successors

    def search(self, state: State, **kwargs) -> List[List[Action]]:
        steps = kwargs.get('steps', 5)
        maxStates = kwargs.get('maxStates', 10)
        return self.produce_paths(state, steps, maxStates)[0][1]