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

            
    def addVarNames(self, varName, baseInfo, typeInfo):
        if baseInfo == "adjacency":
            self.adjacencyStatus.append(typeInfo)
            self.adjacencyVarNames.append(varName)
        elif baseInfo == "type":
            self.typeVarNames.append(varName)
        elif baseInfo == "location":
            self.locationVarNames.append(varName)
        elif baseInfo == "entity":
            self.entityVarNames.append(varName)

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
        self.itemsKeysNames = {}
        # items indexes that qualify for Package
        self.packagesIndexes = []
        # items indexes that qualify for Request
        self.requestsIndexes = []
        # None - no locAdj. Dict or Set - locAdj with that type.
        self.adjacencyStatus = []
        self.adjacencyVarNames = []
        self.typeVarNames = []
        self.locationVarNames = []
        self.entityVarNames = []


        self.entityBaseItemsKeysPosition = {}
        self.locationBaseItemsKeysPosition = {}
        self.typeBaseItemsKeysPosition = {}

        # Save ranges for consts and vars, save entities
        ranges = {}
        self.entityIdToItemId = {}

        # Get entity name and entity base by entity index
        self.entitiesReversed = {info[0]: (entity, info[1]) for entity, info in entities.items()}
        self.locationEntities = tuple(i for i, names in self.entitiesReversed.items() if names[1] == "Location")
        self.vehicleEntities = tuple(i for i, names in self.entitiesReversed.items() if names[1] == "Vehicle")
        self.packageEntities = tuple(i for i, names in self.entitiesReversed.items() if names[1] == "Package")
        self.requestEntities = tuple(i for i, names in self.entitiesReversed.items() if names[1] == "Request")

        for name, variable in initialValues.items():
            info = variablesInfo[name]
            constInfo = info["is_constant"]
            itemsInfo = info["is_items"]
            baseInfo = info["base_name"]
            typeInfo = info["type"]
            entityInfo = info["entity"]

            if constInfo:
                self.constants[name] = variable
                self.addVarNames(name, baseInfo, typeInfo)
                if entities[entityInfo][0] not in self.entityIdToItemId:
                    self.entityIdToItemId[entities[entityInfo][0]] = None
                    ranges[entities[entityInfo][0]] = range(len(variable))

                continue

            if itemsInfo:
                itemIndex = len(itemTups)
                self.itemPositions[name] = itemIndex
                self.itemsKeysNames[name] = info["key names"]

                for keyIndex, (keyName, keyBase) in enumerate(zip(info["key names"], info["key base names"])):
                    itemKeyName = name + " " + keyName
                    self.itemKeysPositions[itemKeyName] = (itemIndex, keyIndex)
                    if typeInfo == List:
                        self.setAbleItemKeysPosition[itemKeyName] = (itemIndex, keyIndex)
                    self.addVarNames(itemKeyName, baseInfo, typeInfo)
                    if keyBase == "entity":
                        self.entityBaseItemsKeysPosition[itemIndex] = keyIndex
                    elif keyBase == "location":
                        self.locationBaseItemsKeysPosition[itemIndex] = keyIndex
                    elif keyBase == "type":
                        self.typeBaseItemsKeysPosition[itemIndex] = keyIndex
                if typeInfo == List:
                    self.setAbleEntities.add(itemIndex)

                self.itemsMaxId.append(max(variable, key=variable.get))
                itemTups.append(variable)
                # There is only one "items" per entity
                self.entityIdToItemId[entities[entityInfo][0]] = itemIndex
                ranges[entities[entityInfo][0]] = None

                if entities[entityInfo][1] == "Package":
                    self.packagesIndexes.append(itemIndex)
                elif entities[entityInfo][1] == "Request":
                    self.requestsIndexes.append(itemIndex)
                continue

            varIndex = len(variableTups)
            self.varPositions[name] = varIndex
            variableTups.append(variable)
            self.addVarNames(name, baseInfo, typeInfo)
            if entities[entityInfo][0] not in self.entityIdToItemId:
                self.entityIdToItemId[entities[entityInfo][0]] = None
                ranges[entities[entityInfo][0]] = range(len(variable))


        variableTups = tuple(variableTups)
        itemTups = tuple(itemTups)
        self.ranges = tuple([ranges[i] for i in range(len(ranges))])
        self.initState = State(variableTups, itemTups)

        self.packagesIndexes = tuple(self.packagesIndexes)
        self.requestsIndexes = tuple(self.requestsIndexes)
        self.adjacencyStatus = tuple(self.adjacencyStatus)
        self.adjacencyVarNames = tuple(self.adjacencyVarNames)
        self.locationVarNames = tuple(self.locationVarNames)
        self.typeVarNames = tuple(self.typeVarNames)
        self.entityVarNames = tuple(self.entityVarNames)
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
        self.itemsKeysNames = kwargs.get("itemsKeysNames", {})
        self.packagesIndexes = kwargs.get("packagesIndexes", tuple())
        self.requestsIndexes = kwargs.get("requestsIndexes", tuple())
        self.entityIdToItemId = kwargs.get("entityIdToItemId", {})
        self.ranges = kwargs.get("ranges", tuple())
        self.requestsIndexes = kwargs.get("requestsIndexes", tuple())
        self.adjacencyStatus = kwargs.get("adjacencyStatus", tuple())
        self.adjacencyVarNames = kwargs.get("adjacencyVarNames", tuple())
        self.locationVarNames = kwargs.get("locationVarNames", tuple())
        self.typeVarNames = kwargs.get("typeVarNames", tuple())
        self.entityVarNames = kwargs.get("entityVarNames", tuple())
        self.locationEntities = kwargs.get("locationEntities", tuple())
        self.vehicleEntities = kwargs.get("vehicleEntities", tuple())
        self.packageEntities = kwargs.get("packageEntities", tuple())
        self.requestEntities = kwargs.get("requestEntities", tuple())
        self.entityBaseItemsKeysPosition = kwargs.get("entityBaseItemsKeysPosition", {})
        self.locationBaseItemsKeysPosition = kwargs.get("locationBaseItemsKeysPosition", {})
        self.typeBaseItemsKeysPosition = kwargs.get("typeBaseItemsKeysPosition", {})

        # Initialize initState if provided, otherwise default to empty State
        varbleTups = kwargs.get("variableTups", tuple())
        itemTups = kwargs.get("itemTups", tuple())
        self.initState = kwargs.get("initState", State(varbleTups, itemTups))

    def __copy__(self):
        """
        Returns a copy of the instance with all attributes.
        """
        # Collect all instance attributes
        attributes = vars(self).copy()
        # Create a new Problem instance using the copied attributes as kwargs
        return Problem(**attributes)
    def get_adjacency_names(self):
        return self.adjacencyVarNames
    def get_adjacency_status(self):
        return self.adjacencyStatus

    def countsPackagesOfEntities(self, state):
        """
        :return: two numbers - number of packages on vehicles,
        number of packages not on vehicles
        """
        countVehicles = 0
        countNotVehicles = 0
        vehiclelist = {}
        for packIndex in self.packagesIndexes:
            keyIndex = self.entityBaseItemsKeysPosition[packIndex]
            for entityId in state.get_items_ids(packIndex):
                if self.entitiesReversed[state.get_item_value(packIndex, keyIndex, entityId)][1] == "Vehicle":
                    countVehicles += 1
                    vehiclelist[entityId] = True
                else:
                    countNotVehicles += 1
                    vehiclelist[entityId] = False
        return countVehicles, countNotVehicles, vehiclelist

    def get_entity_ids(self, state: State, entityIndex: int) -> Iterable[int]:
        if self.ranges[entityIndex] is not None:
            return self.ranges[entityIndex]
        return state.get_items_ids(self.entityIdToItemId[entityIndex])

    def get_len_packages(self, state: State):
        count = 0
        for items in self.packagesIndexes:
            count += state.get_len_items(items)
        return count

    def get_len_requests(self, state: State):
        count = 0
        for items in self.requestsIndexes:
            count += state.get_len_items(items)
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
            
    def get_base_action_indexes(self, actionName):
        return self.itemKeysPositions[actionName]
    
    def get_onEntity_indexes(self):
        on_key = None
        for key in self.itemKeysPositions.keys():
            if 'onEntity' in key:
                on_key = key
                break
        return self.itemKeysPositions[on_key]


    def get_consts(self):
        return self.constants.values()
    
    def get_locations(self, state):
        locs = []
        for name, index in self.varPositions.items():
            if 'loc' in name.lower():
                locs.append(state.variables[index])
        return locs
    
    def get_vehicle_types(self):
        types = []
        for _, vals in self.entities.items():
            if vals[1] == 'Vehicle':
                types.append(vals[0])
        return types

    def copyState(self, state):
        return copy(state)

    def representState(self, state):
        txt = "State:\n"
        for name, index in self.varPositions.items():
            txt += " {}: {}\n".format(name, state.variables[index])
        for name, index in self.itemPositions.items():
            txt += " {}:".format(name)
            for i, keyName in enumerate(self.itemsKeysNames[name]):
                txt+= " {}. {}".format(i, keyName)
            txt += "\n  {}\n".format(state.items[index])
        return txt