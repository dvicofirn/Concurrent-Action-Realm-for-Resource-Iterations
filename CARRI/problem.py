from typing import Iterable, List, Dict
from copy import copy
from CARRI.state import State


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
        self.variablesInfo = variablesInfo
        self.entities = entities
        self.constants = {} # Constant name: Constant tuple
        variableTups = [] # Becomes: tuple of variables (state.variables)
        self.varPositions = {} # Variable name: index in tuple
        itemList = [] # Becomes: tuple of items (state.items)
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
        self.adjacencyStatus = None
        self.adjacencyConstName = None
        # Iterable of locations (only for Location with locAdj)
        self.locationRanges = tuple()
        # Tuple of all Entity Ids of vehicles.
        self.vehicleEntities = []

        self.entityBaseItemsKeysPosition = {}
        self.locationBaseItemsKeysPosition = {}

        # Save ranges for consts and vars, save entities
        ranges = {}
        self.entityIdToItemId = {}

        # Get entity name and entity base by entity index
        self.entitiesReversed = {info[0]: (entity, info[1]) for entity, info in entities.items()}

        for name, variable in initialValues.items():
            info = variablesInfo[name]
            constInfo = info["is_constant"]
            itemsInfo = info["is_items"]
            baseInfo = info["base_name"]
            typeInfo = info["type"]
            entityInfo = info["entity"]

            if constInfo:
                self.constants[name] = variable
                if baseInfo == "adjacency" and entities[entityInfo][1] == "Location":
                    self.adjacencyStatus = typeInfo
                    self.locationRanges = range(len(variable))
                    self.adjacencyConstName = name
                if entities[entityInfo][0] not in self.entityIdToItemId:
                    self.entityIdToItemId[entities[entityInfo][0]] = None
                    ranges[entities[entityInfo][0]] = range(len(variable))

                continue

            if itemsInfo:
                itemIndex = len(itemList)
                self.itemPositions[name] = itemIndex

                for keyIndex, (keyName, keyBase) in enumerate(zip(info["key names"], info["key base names"])):
                    itemKeyName = name + " " + keyName
                    self.itemKeysPositions[itemKeyName] = (itemIndex, keyIndex)
                    if typeInfo == List:
                        self.setAbleItemKeysPosition[itemKeyName] = (itemIndex, keyIndex)
                    if keyBase == "entity":
                        self.entityBaseItemsKeysPosition[itemIndex] = keyIndex
                    elif keyBase == "location":
                        self.locationBaseItemsKeysPosition[itemIndex] = keyIndex
                if typeInfo == List:
                    self.setAbleEntities.add(itemIndex)

                self.itemsMaxId.append(max(variable, key=variable.get))
                itemList.append(variable)
                # There is only one "items" per entity
                self.entityIdToItemId[entities[entityInfo][0]] = itemIndex
                ranges[entities[entityInfo][0]] = None

                if entities[entityInfo][1] == "Package":
                    self.packagesIndexes.append(itemIndex)
                elif entities[entityInfo][1] == "Request":
                    self.requestsIndexes.append(itemIndex)
                elif entities[entityInfo][1] == "Vehicle":
                    self.vehicleEntities.append(entities[entityInfo][0])
                continue

            varIndex = len(variableTups)
            self.varPositions[name] = varIndex
            variableTups.append(variable)
            if entities[entityInfo][0] not in self.entityIdToItemId:
                self.entityIdToItemId[entities[entityInfo][0]] = None
                ranges[entities[entityInfo][0]] = range(len(variable))
                if entities[entityInfo][1] == "Vehicle":
                    self.vehicleEntities.append(entities[entityInfo][0])

        variableTups = tuple(variableTups)
        itemList = itemList
        self.ranges = tuple([ranges[i] for i in range(len(ranges))])
        self.initState = State(variableTups, itemList)

        self.packagesIndexes = tuple(self.packagesIndexes)
        self.requestsIndexes = tuple(self.requestsIndexes)
        self.vehicleEntities = tuple(self.vehicleEntities)
        self.entities = entities 

    def _init_with_attributes(self, **kwargs):
        """
        Initialize with directly provided attributes.
        This method assumes that all necessary variables are provided as keyword arguments.
        """
        self.constants = kwargs.get("constants", {})
        self.variablesInfo = kwargs.get("variablesInfo", {})
        self.entities = kwargs.get("entities", {})
        self.entitiesReversed = kwargs.get("entitiesReversed", {})
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
        self.adjacencyStatus = kwargs.get("adjacencyStatus", None)
        self.adjacencyConstName = kwargs.get("adjacencyConstName", None)
        self.locationRanges = kwargs.get("requestsIndexes", tuple())
        self.vehicleEntities = kwargs.get("vehicleEntities", tuple())
        self.entityBaseItemsKeysPosition = kwargs.get("entityBaseItemsKeysPosition", {})
        self.locationBaseItemsKeysPosition = kwargs.get("locationBaseItemsKeysPosition", {})

        # Initialize initState if provided, otherwise default to empty State
        varbleTups = kwargs.get("variableTups", tuple())
        itemList = kwargs.get("itemList", [])
        self.initState = kwargs.get("initState", State(varbleTups, itemList))

    def __copy__(self):
        """
        Returns a copy of the instance with all attributes.
        """
        # Collect all instance attributes
        attributes = vars(self).copy()
        # Create a new Problem instance using the copied attributes as kwargs
        return Problem(**attributes)
    def get_locations(self):
        return self.locationRanges
    def get_adjacents(self, locId):
        return self.constants[self.adjacencyConstName][locId].copy()
    def get_adjacents_status(self):
        return self.adjacencyStatus

    def countsPackagesOfEntities(self, state):
        """
        :return: two numbers - number of packages on vehicles,
        number of packages not on vehicles
        """
        countVehicles = 0
        countNotVehicles = 0
        for packIndex in self.packagesIndexes:
            keyIndex = self.entityBaseItemsKeysPosition[packIndex]
            for entityId in state.get_items_ids(packIndex):
                if self.entitiesReversed[state.get_item_value(packIndex, keyIndex, entityId)][1] == "Vehicle":
                    countVehicles += 1
                else:
                    countNotVehicles += 1
        return countVehicles, countNotVehicles

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

    def add_entity(self, state: State, entityIndex: int,  *params):
        entity = self.entityIdToItemId[entityIndex]
        maxId = self.itemsMaxId[entity] + 1
        self.itemsMaxId[entity] = maxId
        if entity in self.setAbleEntities:
            state.add_entity_list(entity, maxId, *params)
        else:
            state.add_entity(entity, maxId, *params)

    def remove_entity(self, state: State, entityIndex: int, entityId):
        state.remove_entity(self.entityIdToItemId[entityIndex], entityId)

    def replace_entity(self, state: State, entityIndex: int,
                       entityId: int, *newVals):
        if entityIndex in self.setAbleEntities:
            state.replace_entity_list(self.entityIdToItemId[entityIndex], entityId, *newVals)
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