from typing import Tuple, List, Dict, Iterable
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
    def __copy__(self):
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
        return tuple(self.items[entityIndex].keys())

    def get_len(self, entityIndex) -> int:
        return len(self.items[entityIndex])

    def add_entity_list(self, entityIndex, maxId, *params):
        # Add new item (list) with the max id
        self.items[entityIndex][maxId] = list(params)
    def add_entity(self, entityIndex, maxId, *params):
        # Add new item (tuple) with the max id
        self.items[entityIndex][maxId] = params

    def remove_entity(self, entityIndex, removeId):
        self.items[entityIndex].pop(removeId)

    def replace_entity(self, entityIndex, replaceId, *newVals):
        self.items[entityIndex][replaceId] = newVals

    def replace_entity_list(self, entityIndex, replaceId, *newVals):
        self.items[entityIndex][replaceId] = list(newVals)

    def __lt__(self, other):
        # Define a way to compare `State` instances
        # For example, based on an attribute like `self.cost`
        return other #TODO