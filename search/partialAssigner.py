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
                split_size = min(random.randint(minSplitSize, maxSplitSize), len(vehicleList))

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

    def search(self, state, steps, maxStates):
        splits = self.split_vehicles()
        # Add initial states, transitions, costs
        split = splits[0]
        initSearchResult = self.simulator.generate_partial_successors(state, split)
        afterEnvResult = self.simulator.applyEnvSteps(initSearchResult)
        topSearchResult = sorted(afterEnvResult, key=lambda x: x[4])[:maxStates]
        searchQueue = deque()
        for resultItems in topSearchResult:
            searchQueue.append(([resultItems[0]], [resultItems[1]],
                                [resultItems[2]], [resultItems[3]], [resultItems[4]]))

        for step in range(1, steps):
            nextSearches = []
            while searchQueue:
                currentStates, currentAfterEnv, currentTransitions, currentCosts, currentNCosts = searchQueue.pop()
                currentSearch = self.simulator.generate_partial_successors(currentAfterEnv[-1], split)
                afterEnvResult = self.simulator.applyEnvSteps(currentSearch)
                topSearchResult = sorted(afterEnvResult, key=lambda x: x[4])[:maxStates]
                for state, afterEnv, transition, cost, nCost in topSearchResult:
                    nextSearches.append((
                        currentStates + [state],
                        currentAfterEnv + [afterEnv],
                        currentTransitions + [transition],
                        currentCosts + [cost + currentCosts[-1]],
                        currentNCosts + [nCost + currentNCosts[-1]]
                    ))
            searchQueue.extend(sorted(nextSearches, key=lambda x: x[3][-1] + x[4][-1])[:maxStates])

        for split in splits[1:]:
            for step in range(steps):
                nextSearches = []
                while searchQueue:
                    currentStates, currentAfterEnv, currentTransitions, currentCosts, currentNCosts = searchQueue.pop()
                    state = currentStates[step]
                    currentSearch = self.simulator.generate_partial_successors(state, split)
                    afterEnvResult = self.simulator.applyEnvSteps(currentSearch)
                    topSearchResult = sorted(afterEnvResult, key=lambda x: x[4])[:maxStates]
                    for state, afterEnv, transition, cost, nCost in topSearchResult:
                        nextTransitionStep = currentTransitions[step].copy()
                        nextTransitionStep.extend(transition)
                        nextSearches.append((
                            currentStates[:step] + [state] + currentStates[step + 1:],
                            currentAfterEnv[:step] + [afterEnv] + currentAfterEnv[step + 1:],
                            currentTransitions[:step] + [nextTransitionStep] + currentTransitions[step + 1:],
                            currentCosts[:step] + [cost + lastCost for lastCost in currentCosts[step:]],
                            currentNCosts[:step] + [nCost - currentNCosts[step] + lastCost for lastCost in currentNCosts[step:]]

                        ))
                searchQueue.extend(sorted(nextSearches, key=lambda x: x[3][-1] + x[4][-1])[:maxStates])

        return searchQueue


