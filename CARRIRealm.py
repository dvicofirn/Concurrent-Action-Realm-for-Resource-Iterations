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
            if not self.evaluate_condition(problem, state, precondition):
                return False
        for precondition in action['conflicting preconditions']:
            if not self.evaluate_condition(problem, state, precondition):
                return False
        return True

    def revalidate_action(self, problem, state, action):
        """
        Revalidate action, checking for possibly conflicting actions.
        """
        for precondition in action['conflicting preconditions']:
            if not self.evaluate_condition(problem, state, precondition):
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
        # Implement logic to evaluate different types of conditions
        condition_type = condition['type']
        if condition_type == 'comparison':
            return self.evaluate_comparison(problem, state, condition)
        elif condition_type == 'existence':
            return self.evaluate_existence(problem, state, condition)
        # Add additional condition types as needed
        return False

    def evaluate_comparison(self, problem, state, condition):
        """
        Evaluate a comparison condition (e.g., >, <, ==) between variables or constants.
        """
        left = self.resolve_expression(problem, state, condition['left'])
        right = self.resolve_expression(problem, state, condition['right'])
        operator = condition['operator']

        if operator == '==':
            return left == right
        elif operator == '!=':
            return left != right
        elif operator == '>':
            return left > right
        elif operator == '<':
            return left < right
        elif operator == '>=':
            return left >= right
        elif operator == '<=':
            return left <= right
        return False

    def evaluate_existence(self, problem, state, condition):
        """
        Evaluate whether a specific entity exists in the state or problem context.
        """
        entity = condition['entity']
        if entity in state['entities']:
            return True
        return False

    def resolve_expression(self, problem, state, expression):
        """
        Resolve an expression, which could be a variable, constant, or computed value.
        """
        if isinstance(expression, str):
            # Resolve variable names to values in the state
            return state.get(expression, 0)
        elif isinstance(expression, (int, float)):
            return expression
        # Add logic for more complex expressions if needed
        return 0

    def apply_effect(self, problem, state, effect):
        """
        Apply an effect to the state.
        """
        effect_type = effect['type']
        if effect_type == 'assignment':
            self.apply_assignment(problem, state, effect)
        elif effect_type == 'increment':
            self.apply_increment(problem, state, effect)
        # Add additional effect types as needed

    def apply_assignment(self, problem, state, effect):
        """
        Apply an assignment effect, setting a variable to a value.
        """
        target = effect['target']
        value = self.resolve_expression(problem, state, effect['value'])
        state[target] = value

    def apply_increment(self, problem, state, effect):
        """
        Apply an increment effect, increasing or decreasing a variable's value.
        """
        target = effect['target']
        increment_value = self.resolve_expression(problem, state, effect['value'])
        if target in state:
            state[target] += increment_value
        else:
            state[target] = increment_value

    def simulate(self, iterations):
        """
        Simulate the environment over a series of iterations, applying actions and updating the state.
        """
        current_state = self.problem.initState.copy()
        for i in range(iterations):
            print(f"Iteration {i + 1}:")
            for action in self.action_generators:
                if self.validate_action(self.problem, current_state, action):
                    self.apply_action(self.problem, current_state, action)
            self.apply_environment_steps(current_state)
            print(f"State after iteration {i + 1}: {current_state}")

    def apply_environment_steps(self, state):
        """
        Apply environment steps to the current state, which may include dynamic changes.
        """
        for step in self.env_steps:
            self.apply_effect(self.problem, state, step)

        # Apply iteration step changes if necessary
        for effect in self.iter_step:
            self.apply_effect(self.problem, state, effect)




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




