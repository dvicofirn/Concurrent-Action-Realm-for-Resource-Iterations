from typing import Iterable, List, Dict, Tuple, Set
from copy import copy

class State:
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
        return State(tuple(var.copy() for var in self.variables),
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

    def get_len(self, entityIndex) -> int:
        return len(self.items[entityIndex])

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

    def __lt__(self, other):
        # Define a way to compare `State` instances
        # For example, based on an attribute like `self.cost`
        return other #TODO

class Problem:
    def __init__(self, **kwargs):
        """
        Supports two types of initialization:
        - By passing `variables`, `variablesInfo`, and `entities` dictionaries.
        - By directly passing the attributes as keyword arguments.
        """
        if "initialValues" in kwargs and "variablesInfo" in kwargs and "entities" in kwargs:
            # Initialize using the first method with data dictionaries
            self._init_with_data_dicts(kwargs["initialValues"], kwargs["variablesInfo"], kwargs["entities"])
        else:
            # Initialize using the second method with directly provided attributes
            self._init_with_attributes(**kwargs)
    def _init_with_data_dicts(self, initialValues: Dict, variablesInfo: Dict, entities: Dict):
        """
        Initialize with `variables`, `variablesInfo`, and `entities` dictionaries.
        This doesn't look fancy at all, and it might not be so easy
        to debug.
        The point of all of this is to make action on state faster.
        Saves constants at problem, variables and entity items at self.initState.
        """
        self.constants = {} # Constant name: Constant tuple
        variableTups = [] # Becomes: tuple of variables (state.variables)
        self.varPositions = {} # Variable name: index in tuple
        itemTups = [] # Becomes: tuple of items (state.items)
        self.itemPositions = {} # Items name: index in tuple
        # Items & key name: (items index, key index)
        self.itemKeysPositions = {}
        # Items & key name: (items index, key index) for mutable items
        self.setAbleItemKeysPosition = {}
        # Set of mutable items
        self.setAbleEntities = set()
        # {items index: Max id for items}
        self.itemsMaxId = []
        # items indexes that qualify for Package
        self.packagesIndexes = []
        # items indexes that qualify for Request
        self.requestsIndexes = []
        # None - no locAdj. Dict or Set - locAdj with that type.
        self.locAdjStatus = None
        # Iterable of locations (only for Location with locAdj)
        self.locationRanges = tuple()
        # Tuple of all Entity Ids of vehicles.
        self.vehicleEntities = []

        # Save ranges for consts and vars, save entities
        ranges = {}
        self.entityIdToItemId = {}

        for name, variable in initialValues.items():
            info = variablesInfo[name]

            if info["is_constant"]:
                self.constants[name] = variable
                if name == "locAdj" and entities[info["entity"]][1] == "Location":
                    self.locAdjStatus = info["type"] == Dict
                    self.locationRanges = range(len(variable))
                if entities[info["entity"]][0] not in self.entityIdToItemId:
                    self.entityIdToItemId[entities[info["entity"]][0]] = None
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

                self.itemsMaxId.append(itemIndex)
                itemTups.append(variable)
                # There is only one "items" per entity
                self.entityIdToItemId[entities[info["entity"]][0]] = itemIndex
                ranges[entities[info["entity"]][0]] = None

                if entities[info["entity"]][1] == "Package":
                    self.packagesIndexes.append(itemIndex)
                elif entities[info["entity"]][1] == "Request":
                    self.requestsIndexes.append(itemIndex)
                elif entities[info["entity"]][1] == "Vehicle":
                    self.vehicleEntities.append(itemIndex)
                continue

            varIndex = len(variableTups)
            self.varPositions[name] = varIndex
            variableTups.append(variable)
            if entities[info["entity"]][0] not in self.entityIdToItemId:
                self.entityIdToItemId[entities[info["entity"]][0]] = None
                ranges[entities[info["entity"]][0]] = range(len(variable))
                if entities[info["entity"]][1] == "Vehicle":
                    self.vehicleEntities.append(entities[info["entity"]][0])

        variableTups = tuple(variableTups)
        itemTups = tuple(itemTups)
        self.ranges = tuple([ranges[i] for i in range(len(ranges))])
        self.initState = State(variableTups, itemTups)

        self.packagesIndexes = tuple(self.packagesIndexes)
        self.requestsIndexes = tuple(self.requestsIndexes)
        self.vehicleEntities = tuple(self.vehicleEntities)

    def _init_with_attributes(self, **kwargs):
        """
        Initialize with directly provided attributes.
        This method assumes that all necessary variables are provided as keyword arguments.
        """
        self.constants = kwargs.get("constants", {})
        self.varPositions = kwargs.get("varPositions", {})
        self.itemPositions = kwargs.get("itemPositions", {})
        self.itemKeysPositions = kwargs.get("itemKeysPositions", {})
        self.setAbleItemKeysPosition = kwargs.get("setAbleItemKeysPosition", {})
        self.setAbleEntities = kwargs.get("setAbleEntities", set())
        self.itemsMaxId = kwargs.get("itemsMaxId", [])
        self.packagesIndexes = kwargs.get("packagesIndexes", tuple())
        self.requestsIndexes = kwargs.get("requestsIndexes", tuple())
        self.entityIdToItemId = kwargs.get("entityIdToItemId", {})
        self.ranges = kwargs.get("ranges", tuple())
        self.requestsIndexes = kwargs.get("requestsIndexes", tuple())
        self.locAdjStatus = kwargs.get("requestsIndexes", None)
        self.locationRanges = kwargs.get("requestsIndexes", tuple())
        self.vehicleEntities = kwargs.get("vehicleItemsEntities", tuple())

        # Initialize initState if provided, otherwise default to empty State
        varbleTups = kwargs.get("variableTups", tuple())
        itemTups = kwargs.get("itemTups", tuple())
        self.initState = kwargs.get("initState", State(varbleTups, itemTups))

    def getVehicleIndexes(self):
        return self.vehicleVariableEntities
    def get_locations(self):
        return self.locationRanges
    def get_adjacents(self, locId):
        return self.constants["locAdj"][locId].copy()
    def get_adjacents_status(self):
        return self.locAdjStatus
    def get_entity_ids(self, state: State, entityIndex: int) -> Iterable[int]:
        if self.ranges[entityIndex] is not None:
            return self.ranges[entityIndex]
        return state.get_items_ids(self.entityIdToItemId[entityIndex])

    def get_len_packages(self, state: State):
        count = 0
        for item in self.packagesIndexes:
            count += state.get_len(item)
        return count

    def get_len_requests(self, state: State):
        count = 0
        for item in self.requestsIndexes:
            count += state.get_len(item)
        return count

    def add_entity(self, state: State, entityIndex: int, *params):
        entity = self.entityIdToItemId[entityIndex]
        maxId = self.itemsMaxId[entity] + 1
        self.itemsMaxId = maxId
        if entity in self.setAbleEntities:
            state.add_entity(entity, maxId, *params)
        else:
            state.add_list_entity(entity, maxId, *params)

    def remove_entity(self, state: State, entityIndex: int, entityId):
        state.remove_entity(self.entityIdToItemId[entityIndex], entityId)

    def replace_entity(self, state: State, entityIndex: int,
                       entityId: int, *newVals):
        state.replace_entity(self.entityIdToItemId[entityIndex], entityId, *newVals)

    def get_value(self, state: State, variableName: str, index: int):
        if variableName in self.constants:
            return self.constants[variableName][index]
        else:
            if variableName in self.varPositions:
                return state.get_variable_value(self.varPositions[variableName], index)
            else:
                return state.get_item_value(self.itemKeysPositions[variableName][0],
                                             self.itemKeysPositions[variableName][1],
                                             index)

    def set_value(self, state: State, variableName, index, value):
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

class Heuristic:
    def __init__(self, problem: Problem):
        self.problem = problem

    def evaluate(self, state: State):
        raise NotImplementedError("Must be implemented by subclasses")