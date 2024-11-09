from CARRI import Simulator, Problem, State
import random
import math
from collections import deque

class PartialAssigner:
    def __init__(self, simulator):
        self.simulator = simulator
        self.problem = simulator.problem
        self.vehicleTypes = self.problem.vehicleEntities
        self.vehicleIds = []  # List of iterables
        self.lenVehicleTypes = len(self.vehicleTypes)

        # Collect vehicle IDs per type
        for type in self.vehicleTypes:
            # Convert keys to a list to enable slicing
            self.vehicleIds.append(list(self.problem.get_entity_ids(self.problem.initState, type)))

    def split_vehicles(self):
        # List to hold all the splits per vehicle type
        all_splits = []

        # Iterate over each list of vehicle IDs for each type
        for ids in self.vehicleIds:
            type_splits = []
            i = 0

            # Group IDs into tuples of size 1-3
            while i < len(ids):
                # Choose a random size for the group (1-3) while respecting remaining ids
                group_size = min(random.randint(1, 3), len(ids) - i)
                type_splits.append(tuple(ids[i:i + group_size]))
                i += group_size

            # Append the split list for this vehicle type
            all_splits.append(type_splits)

        return all_splits

    def search(self, initState, steps, maxStates):
        splits = self.split_vehicles()
        searchQueue = deque([([initState, None],
                              [[] for _ in range(steps)],
                              [0 for _ in range(steps)],
                              [0 for _ in range(steps)])])
        currentStep = 0
        while currentStep < steps:
            stopStep = currentStep + min(random.randint(1, 4), steps - currentStep)
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



        """# Add initial states, transitions, costs
        split = splits[0]
        initSearchResult = self.simulator.generate_partial_successors(initState, split)
        afterEnvResult = self.simulator.applyEnvSteps(initSearchResult)
        searchQueue = deque()
        for resultItems in afterEnvResult:
            searchQueue.append((resultItems[0], [resultItems[1]],
                                [resultItems[2]], [resultItems[3]]))

        for step in range(1, steps):
            nextSearches = []
            while searchQueue:
                state, currentTransitions, currentCosts, currentNCosts = searchQueue.pop()
                currentSearch = self.simulator.generate_partial_successors(state, split)
                afterEnvResult = self.simulator.applyEnvSteps(currentSearch)
                for state, transition, cost, nCost in afterEnvResult:
                    nextSearches.append((
                        state,
                        currentTransitions + [transition],
                        currentCosts + [cost + currentCosts[-1]],
                        currentNCosts + [nCost + currentNCosts[-1]]
                    ))
            if len(nextSearches) > maxStates:
                nextSearches = random.sample(nextSearches, maxStates)
            searchQueue.extend(nextSearches)
        searchQueue = (sorted(searchQueue, key=lambda x: x[2][-1] + x[3][-1])[:maxStates])

        for split in splits[1:]:
            for step in range(steps):
                nextSearches = []
                while searchQueue:
                    state, currentTransitions, currentCosts, currentNCosts = searchQueue.pop()
                    if step == 0:
                        state = initState.__copy__()
                    succeeded = True
                    for action in currentTransitions[step]:
                        try:
                            if action.reValidate(self.problem, state):
                                action.apply(self.problem, state)
                            else:
                                succeeded = False
                                break
                        except Exception as e:
                            succeeded = False
                            break
                    if not succeeded:
                        continue
                    currentSearch = self.simulator.generate_partial_successors(state, split)
                    afterEnvResult = self.simulator.applyEnvSteps(currentSearch)
                    for state, transition, cost, nCost in afterEnvResult:
                        nextTransitionStep = currentTransitions[step].copy()
                        nextTransitionStep.extend(transition)
                        nextNCost = nCost + currentNCosts[step - 1] if step > 0 else nCost
                        lastNCost = currentNCosts[step]
                        nextSearches.append((
                            state,
                            currentTransitions[:step] + [nextTransitionStep] + currentTransitions[step + 1:],
                            currentCosts[:step] + [cost + lastCost for lastCost in currentCosts[step:]],
                            currentNCosts[:step] + [nextNCost] + [nextNCost - lastNCost + cost for cost in currentNCosts[step + 1:]]
                        ))
                if len(nextSearches) > maxStates:
                    nextSearches = random.sample(nextSearches, maxStates)
                searchQueue.extend(nextSearches)
            searchQueue = (sorted(searchQueue, key=lambda x: x[2][-1] + x[3][-1])[:maxStates])

        return searchQueue"""


