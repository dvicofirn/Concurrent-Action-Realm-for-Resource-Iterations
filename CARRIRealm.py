from typing import Iterable, List, Dict, Tuple
from copy import copy

from CARRIAction import ActionProducer, ActionStringRepresentor, Action


class CARRIState:
    def __init__(self, variables: Tuple[List], items: Tuple[Dict]):
        self.variables = variables
        self.items = items

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "State:\nVariables: " + str(self.variables) +"\nEntities: " + str(self.items)

    def __eq__(self, other):
        return self.variables == other.variables and self.items == other.items

    def __hash__(self):
        return hash((
            tuple(tuple(var) for var in self.variables),
            tuple(frozenset(item) for item in self.items)
        ))

    # It works.
    def copy(self):
        """
        It works.
        Manual copy instead of deepcopy - hopefully it's faster.
        """
        return CARRIState(tuple(var.copy() for var in self.variables),
                          tuple({id: copy(item) for id, item in entity.items()} for entity in self.items))

    def get_variable_value(self, varIndex, index):
        return self.variables[varIndex][index]

    def get_item_value(self, entityIndex, keyIndex, index):
        # Pay attention: item -> entity -> key Package[pack][type]
        return self.items[entityIndex][index][keyIndex]

    def set_variable_value(self, varIndex, index, value):
        self.variables[varIndex][index] = value

    def set_item_value(self, entityIndex, keyIndex, index, value):
        # Pay attention: item -> entity -> key Package[pack][type]
        self.items[entityIndex][index][keyIndex] = value

    def get_items_ids(self, entityIndex) -> Iterable[int]:
        return self.items[entityIndex].keys()

    def add_entity(self, entityIndex, maxId, *params):
        # Add new item (tuple) with the max id
        self.items[entityIndex][maxId] = params

    def add_list_entity(self, entityIndex, maxId, *params):
        # Add new item (list) with the max id
        self.items[entityIndex][maxId] = list(params)

    def remove_entity(self, entityIndex, removeId):
        self.items[entityIndex].pop(removeId)

    def replace_entity(self, entityIndex, replaceId, *newVals):
        self.items[entityIndex][replaceId] = list(newVals)


class CARRISimulator:
    def __init__(self, problem, actionGenerators, evnSteps, iterStep, entities):
        self.problem = problem
        self.actionProducer = ActionProducer(actionGenerators)
        self.actionStringRepresentor = ActionStringRepresentor(actionGenerators)
        self.evnSteps = evnSteps
        self.iterSteps = iterStep
        self.entities = entities

    def validate_action(self, problem, state, action):
        """
        Validate that all preconditions of the action are met in the given state.
        """
        for precondition in action['regular preconditions']:
            if not self.evaluate_condition(precondition, state, problem):
                return False
        for precondition in action['conflicting preconditions']:
            if not self.evaluate_condition(precondition, state, problem):
                return False
        return True

    def revalidate_action(self, problem, state, action):
        """
        Revalidate action, checking for possibly conflicting actions.
        """
        # Placeholder for revalidation logic, which checks for conflicts.
        # For now, assuming actions are always valid for simplicity.
        for precondition in action['conflicting preconditions']:
            if not self.evaluate_condition(precondition, state, problem):
                return False
        return True

    def apply_action(self, problem, state, action):
        """
        Apply the action's effects to the state.
        """
        for effect in action['effects']:
            self.apply_effect(problem, state, effect)

    def evaluate_condition(self, problem, state, condition):
        """
        Evaluate a condition against the state and problem.
        """
        # Placeholder for evaluating logical conditions (preconditions).
        # In a real implementation, you would parse the condition and check against the state.
        return True

    def apply_effect(self, problem, state, effect):
        """
        Apply an effect to the state.
        """
        # Placeholder for applying effects to the state.
        # This would modify the state based on the effect.
        pass


class CARRIProblem:
    def __init__(self, variables: Dict,variablesInfo: Dict, entities: Dict):
        """
        This doesn't look fancy at all, and it might not be so easy
        to debug.
        The point of all of this is to make action on state faster.
        Saves constants at problem, variables and entity items at self.initState.
        """
        self.constants = {} # Easy access to consts
        varbleTups = [] # Vars saved in eventually tuple
        self.varPositions = {} # Index to var by name
        itemTups = [] # Items saved in eventually tuple
        self.itemPositions = {} # Index to item by name
        # tuple of indexes for item - key combination
        self.itemKeysPositions = {}
        # tuple of indexes for item - key combination - for items applicable of set_value
        self.setAbleItemKeysPosition = {}
        self.setAbleEntities = set()
        self.entitiesMaxId = []

        # Save ranges for consts and vars, save entities
        ranges = {}
        self.entities = {}

        for name, variable in variables.items():
            info = variablesInfo[name]
            if info["is_constant"]:
                self.constants[name] = variable
                if entities[info["entity"]][0] not in self.entities:
                    self.entities[entities[info["entity"]][0]] = name
                    ranges[entities[info["entity"]][0]] = range(len(variable))
                continue

            if info["is_items"]:
                itemIndex = len(itemTups)
                self.itemPositions[name] = itemIndex
                for keyIndex, keyName in enumerate(info["key names"]):
                    itemKeyName = name + " " + keyName
                    self.itemKeysPositions[itemKeyName] = (itemIndex, keyIndex)
                    if info["type"] == List:
                        self.setAbleItemKeysPosition[itemKeyName] = (itemIndex, keyIndex)
                if info["type"] == List:
                    self.setAbleEntities.add(itemIndex)
                itemTups.append(variable)
                self.entitiesMaxId.append(len(variable) - 1)
                # There is only one "items" per entity
                self.entities[entities[info["entity"]][0]] = itemIndex
                ranges[entities[info["entity"]][0]] = None
                continue

            self.varPositions[name] = len(varbleTups)
            varbleTups.append(variable)
            if entities[info["entity"]][0] not in self.entities:
                self.entities[entities[info["entity"]][0]] = name
                ranges[entities[info["entity"]][0]] = range(len(variable))

        varbleTups = tuple(varbleTups)
        itemTups = tuple(itemTups)
        self.ranges = tuple([ranges[i] for i in range(len(ranges))])
        self.initState = CARRIState(varbleTups, itemTups)

    def get_entity_ids(self, state: CARRIState, entityIndex: int) -> Iterable[int]:
        if self.ranges[entityIndex] is not None:
            return self.ranges[entityIndex]
        return state.get_items_ids(self.entities[entityIndex])

    def add_entity(self, state: CARRIState, entityIndex: int, *params):
        entity = self.entities[entityIndex]
        maxId = self.entitiesMaxId[entity] + 1
        self.entitiesMaxId = maxId
        if entity in self.setAbleEntities:
            state.add_entity(entity, maxId, *params)
        else:
            state.add_list_entity(entity, maxId, *params)

    def remove_entity(self, state: CARRIState, entityIndex: int, entityId):
        state.remove_entity(self.entities[entityIndex], entityId)

    def replace_entity(self, state: CARRIState, entityIndex: int,
                       entityId: int, *newVals):
        state.replace_entity(self.entities[entityIndex], entityId, *newVals)

    def get_value(self, state: CARRIState, variableName: str, index: int):
        if variableName in self.constants:
            return self.constants[variableName][index]
        else:
            if variableName in self.varPositions:
                return state.get_variable_value(self.varPositions[variableName], index)
            else:
                return state.get_item_value(self.itemKeysPositions[variableName][0],
                                             self.itemKeysPositions[variableName][1],
                                             index)

    def set_value(self, state: CARRIState, variableName, index, value):
        """
        Set the value of a variable by name.
        """
        if variableName in self.varPositions:
            state.set_variable_value(self.varPositions[variableName], index, value)
        else:
            state.set_item_value(self.setAbleItemKeysPosition[variableName][0],
                                  self.setAbleItemKeysPosition[variableName][1],
                                  index, value)

    def copyState(self, state):
        return copy(state)


    #Todo: I argue it should be implemented in simulator instead of here.
    def advance_state(self, simulator: CARRISimulator, state, action):
        advnaceState = state.copy()
        simulator.apply_action(advnaceState, action)
        return advnaceState









