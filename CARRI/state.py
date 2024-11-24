from typing import Tuple, List, Dict, Iterable
from copy import copy

class State:
    """
    Represents the state of the problem, including variables and items.
    Variables are stored as tuples of lists, and items are stored as tuples of dictionaries.
    """
    def __init__(self, variables: Tuple[List], items: Tuple[Dict]):
        """
        Initialize the State with variables and items.

        Args:
            variables (Tuple[List]): A tuple containing lists of variable values.
            items (Tuple[Dict]): A tuple containing dictionaries of items/entities.
        """
        self.variables = variables
        self.items = items

    def __repr__(self):
        """Return the string representation of the State."""
        return self.__str__()

    def __str__(self):
        """Return a readable string representation of the State."""
        return "State:\nVariables: " + str(self.variables) + "\nEntities: " + str(self.items)

    def __eq__(self, other):
        """
        Check if two State instances are equal.

        Args:
            other (State): Another State instance to compare with.

        Returns:
            bool: True if variables and items are equal, False otherwise.
        """
        return self.variables == other.variables and self.items == other.items

    def __hash__(self):
        """
        Compute a hash value for the State.

        Returns:
            int: The hash value of the State.
        """
        return hash((
            tuple(tuple(var) for var in self.variables),
            tuple(frozenset(item) for item in self.items)
        ))

    # It works.
    def __copy__(self):
        """
        Create a shallow copy of the State.

        It works.
        Manual copy instead of deepcopy - hopefully it's faster.

        Returns:
            State: A new State instance with copied variables and items.
        """
        return State(
            tuple(var.copy() for var in self.variables),
            tuple({id: copy(item) for id, item in entity.items()} for entity in self.items)
        )

    def get_variable_value(self, varIndex, index):
        """
        Get the value of a variable.

        Args:
            varIndex (int): The index of the variable in the variables tuple.
            index (int): The index within the variable list.

        Returns:
            Any: The value at the specified index.
        """
        return self.variables[varIndex][index]

    def get_item_value(self, entityIndex, keyIndex, index):
        """
        Get the value of an item.

        Pay attention: item -> entity -> key (e.g., Package[pack][type])

        Args:
            entityIndex (int): The index of the entity in the items tuple.
            keyIndex (int): The index of the key in the item.
            index (int): The ID of the item.

        Returns:
            Any: The value at the specified key and item ID.
        """
        # Pay attention: item -> entity -> key Package[pack][type]
        return self.items[entityIndex][index][keyIndex]

    def set_variable_value(self, varIndex, index, value):
        """
        Set the value of a variable.

        Args:
            varIndex (int): The index of the variable in the variables tuple.
            index (int): The index within the variable list.
            value (Any): The new value to set.
        """
        self.variables[varIndex][index] = value

    def set_item_value(self, entityIndex, keyIndex, index, value):
        """
        Set the value of an item.

        Pay attention: item -> entity -> key (e.g., Package[pack][type])

        Args:
            entityIndex (int): The index of the entity in the items tuple.
            keyIndex (int): The index of the key in the item.
            index (int): The ID of the item.
            value (Any): The new value to set.
        """
        # Pay attention: item -> entity -> key Package[pack][type]
        self.items[entityIndex][index][keyIndex] = value

    def get_items_ids(self, entityIndex) -> Iterable[int]:
        """
        Get the IDs of all items for a given entity.

        Args:
            entityIndex (int): The index of the entity in the items tuple.

        Returns:
            Iterable[int]: A tuple of item IDs.
        """
        return tuple(self.items[entityIndex].keys())

    def get_len_items(self, entityIndex) -> int:
        """
        Get the number of items for a given entity.

        Args:
            entityIndex (int): The index of the entity in the items tuple.

        Returns:
            int: The number of items.
        """
        return len(self.items[entityIndex])

    def add_entity_list(self, entityIndex, maxId, *params):
        """
        Add a new entity with parameters as a list.

        Args:
            entityIndex (int): The index of the entity in the items tuple.
            maxId (int): The ID to assign to the new entity.
            *params: Parameters of the new entity.
        """
        # Add new item (list) with the max id
        self.items[entityIndex][maxId] = list(params)

    def add_entity(self, entityIndex, maxId, *params):
        """
        Add a new entity with parameters as a tuple.

        Args:
            entityIndex (int): The index of the entity in the items tuple.
            maxId (int): The ID to assign to the new entity.
            *params: Parameters of the new entity.
        """
        # Add new item (tuple) with the max id
        self.items[entityIndex][maxId] = params

    def remove_entity(self, entityIndex, removeId):
        """
        Remove an entity by its ID.

        Args:
            entityIndex (int): The index of the entity in the items tuple.
            removeId (int): The ID of the entity to remove.
        """
        self.items[entityIndex].pop(removeId)

    def replace_entity(self, entityIndex, replaceId, *newVals):
        """
        Replace an existing entity's values with new values (as a tuple).

        Args:
            entityIndex (int): The index of the entity in the items tuple.
            replaceId (int): The ID of the entity to replace.
            *newVals: New values for the entity.
        """
        self.items[entityIndex][replaceId] = newVals

    def replace_entity_list(self, entityIndex, replaceId, *newVals):
        """
        Replace an existing entity's values with new values (as a list).

        Args:
            entityIndex (int): The index of the entity in the items tuple.
            replaceId (int): The ID of the entity to replace.
            *newVals: New values for the entity.
        """
        self.items[entityIndex][replaceId] = list(newVals)

    def __lt__(self, other):
        """
        Define a less-than comparison for State instances.

        Args:
            other (State): Another State instance to compare with.

        Returns:
            bool: True if this State is considered less than the other, False otherwise.
        """
        # In the future we might change how this method works
        # For example, based on an attribute like `self.cost`
        # As relying on has is not very informative.
        # Or we may just delete it.
        return self.__hash__() < other.__hash__()
