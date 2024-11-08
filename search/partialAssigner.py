from CARRI import Simulator, Problem, State
import random
import math
from collections import deque
from copy import deepcopy
class PartialAssigner:
    def __init__(self, simulator: Simulator):
        self.simulator = simulator
        self.problem = simulator.problem
        self.vehicleTypes = self.problem.vehicleEntities
        self.vehicleIds = []
        for type in self.vehicleTypes:
            self.vehicleIds.append(self.problem.get_entity_ids(self.problem.initState, type))

    def split_vehicles(self):
        # Find the maximum number of vehicles for any type
        splits = []
        for vehicleIndex, vehicleType in enumerate(self.vehicleIds):
            vehicleList = list(vehicleType)
            vehicleSplit = []

            base = math.log(len(vehicleList)) + 1
            factor = math.log(base)
            minSplitSize = round(base - factor)
            maxSplitSize = round(base)

            while len(vehicleList) >= minSplitSize:
                # Determine the split size for this segment
                # Todo: Handle split_size to be fit.
                #split_size = min(random.randint(minSplitSize, maxSplitSize), len(vehicleList))
                split_size = 1

                # Randomly sample unique items for the current segment
                segment = random.sample(vehicleList, split_size)
                vehicleSplit.append(segment)

                # Remove selected items from vehicle_list
                vehicleList = [v for v in vehicleList if v not in segment]

                # Add remaining items if any, or an empty tuple if none
            if vehicleList:
                vehicleSplit.append(vehicleList)

            lenSplits = len(splits)
            lenVehicleSplit = len(vehicleSplit)
            if lenVehicleSplit < lenSplits:
                for i in range(lenVehicleSplit):
                    splits[i].append(vehicleSplit[i])
                for i in range(lenVehicleSplit, lenSplits):
                    splits[i].append(())
            else:
                for i in range(lenSplits):
                    splits[i].append(vehicleSplit[i])
                for i in range(lenSplits, lenVehicleSplit):
                    splits.append([() for i in range(vehicleIndex)] + [vehicleSplit[i]])

        return splits

    def search(self, initState, steps, maxStates):
        splits = self.split_vehicles()

        # Add initial states, transitions, costs
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
                        state = initState.copy()
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

        return searchQueue


