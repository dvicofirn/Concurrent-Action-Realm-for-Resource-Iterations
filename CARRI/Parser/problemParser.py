import re
from typing import Dict, List, Set, Tuple

class CARRIProblemParser:
    """Parses the problem text and initializes variables and entities, including iterations."""

    def __init__(self, problem_text, entities, variables):
        """
        Initialize the parser with problem text, entities, and variables.

        Args:
            problem_text (str): The text of the problem to parse.
            entities (dict): Dictionary of entities parsed from the domain.
            variables (dict): Dictionary of variables parsed from the domain.
        """
        self.problem_text = problem_text
        self.entities = entities  # From domain parsing
        self.variables = variables  # From domain parsing
        self.initialValues = {}
        self.iterations = []  # To store iterations
        self.entityTypeInstances = {}  # {entity_name: [indices]}
        self.entityCounts = {}  # {entity_name: count}
        self.entityMaxIndices = {}  # To keep track of maximum index used per entity
        self.lastItemIndices = {}  # To keep track of last item index for each 'items' variable

        # Create a mapping of entity names (case-insensitive) to indices
        self.entity_name_to_index = {name.lower(): index for name, (index, _) in self.entities.items()}

    def parse(self):
        """
        Parses the problem text and initializes variables and entities, including iterations.

        Returns:
            Tuple[dict, List[dict]]: A tuple containing initialValues and iterations.
        """
        # Split the problem text into lines
        lines = self.problem_text.split('\n')
        # Remove comments and empty lines
        lines = [re.sub(r"#.*", "", line).strip() for line in lines]
        lines = [line for line in lines if line]
        # Split lines into initial values and iterations based on '*'
        sections = self.split_into_sections(lines)

        # Parse initial values
        self.parse_initial_values(sections['initial'])

        # Parse iterations
        for iteration_lines in sections['iterations']:
            iteration_values = self.parse_iteration(iteration_lines)
            self.iterations.append(iteration_values)

        # Ensure all entities have instances based on usage in variables
        self.ensure_entity_instances()

        # Adjust entity counts and indices based on maximum indices used in variable initializations
        self.adjust_entity_counts_and_indices()

        # Set default values for variables not initialized
        self.set_default_values()

        # Convert constants associated with entities to tuples
        for varName, variable in self.variables.items():
            isItems = variable.get('is items', False)
            isConstant = variable.get('is constant', False)
            entityName = variable.get('entity', '')
            if varName in self.initialValues:
                if isConstant and not isItems and entityName:
                    # Constants associated with entities
                    if isinstance(self.initialValues[varName], list):
                        self.initialValues[varName] = tuple(self.initialValues[varName])
                elif isConstant and not entityName:
                    # Global constants
                    if not isinstance(self.initialValues[varName], tuple):
                        self.initialValues[varName] = (self.initialValues[varName],)

        return self.initialValues, self.iterations

    def split_into_sections(self, lines):
        """
        Splits the lines into initial values and iterations based on '*'.

        Args:
            lines (List[str]): List of lines from the problem text.

        Returns:
            Dict[str, List]: A dictionary with keys 'initial' and 'iterations' containing corresponding lines.
        """
        sections = {'initial': [], 'iterations': []}
        currentSection = 'initial'
        currentIteration = None

        for line in lines:
            if line == '*':
                # Start a new iteration section
                if currentSection == 'initial':
                    currentSection = 'iterations'
                    currentIteration = []
                    sections['iterations'].append(currentIteration)
                else:
                    currentIteration = []
                    sections['iterations'].append(currentIteration)
            else:
                if currentSection == 'initial':
                    sections['initial'].append(line)
                else:
                    currentIteration.append(line)

        return sections

    def parse_initial_values(self, lines):
        """
        Parses the initial values from the given lines.

        Args:
            lines (List[str]): List of lines containing initial values.
        """
        index = 0
        while index < len(lines):
            line = lines[index]
            # Check for entity quantities, e.g., 'EntityName: quantity'
            m = re.match(r"^([A-Z][a-zA-Z0-9_ ]*)\s*:\s*(\d+)", line)
            if m:
                entityName = m.group(1)
                quantity = int(m.group(2))
                self.process_entity_quantity(entityName, quantity)
                index += 1
                continue

            # Check for variable initialization with optional default value
            m = re.match(r"^(\w+)\s*:\s*(.*)", line)
            if m:
                variableName = m.group(1)
                defaultValueStr = m.group(2).strip()
                index = self.processVariableInitialization(variableName, defaultValueStr, lines, index + 1)
                continue

            index += 1

        # Update lastItemIndices for items variables
        for varName, variable in self.variables.items():
            if variable.get('is items', False):
                if varName in self.initialValues:
                    lastIndex = max(self.initialValues[varName].keys(), default=-1)
                    self.lastItemIndices[varName] = lastIndex
                else:
                    self.lastItemIndices[varName] = -1

    def parse_iteration(self, lines):
        """
        Parses a single iteration from the given lines.

        Args:
            lines (List[str]): List of lines representing an iteration.

        Returns:
            Dict[str, Any]: A dictionary of iteration values.
        """
        iterationValues = {}
        index = 0
        while index < len(lines):
            line = lines[index]
            # Check for variable initialization, e.g., 'variableName:'
            m = re.match(r"^(\w+)\s*:", line)
            if m:
                variableName = m.group(1)
                if variableName not in self.variables:
                    index += 1
                    continue
                variable = self.variables[variableName]
                if not variable.get('is items', False):
                    index += 1
                    continue
                index = self.processIterationVariable(variableName, lines, index + 1, iterationValues)
                continue
            index += 1
        return iterationValues

    def processIterationVariable(self, variableName, lines, startIndex, iterationValues):
        """
        Processes a variable within an iteration.

        Args:
            variableName (str): The name of the variable.
            lines (List[str]): List of lines representing the iteration.
            startIndex (int): The index to start processing from.
            iterationValues (Dict[str, Any]): The dictionary to store iteration values.

        Returns:
            int: The updated index after processing the variable.
        """
        variable = self.variables[variableName]
        if variableName not in iterationValues:
            iterationValues[variableName] = []

        index = startIndex
        valueLines = []
        while index < len(lines):
            line = lines[index]
            if re.match(r"^\w+\s*:", line) or line == '*':
                break
            valueLines.append(line)
            index += 1

        for line in valueLines:
            line = line.strip()
            if not line:
                continue
            value = self.parseValue(line, variable)
            iterationValues[variableName].append(value)

        return index

    def process_entity_quantity(self, entityName, quantity):
        """
        Processes the quantity of an entity.

        Args:
            entityName (str): The name of the entity.
            quantity (int): The number of instances to create.
        """
        entityName = entityName.strip()
        if entityName not in self.entities:
            return
        indices = list(range(quantity))
        self.entityTypeInstances[entityName] = indices
        self.entityCounts[entityName] = quantity
        self.entityMaxIndices[entityName] = max(self.entityMaxIndices.get(entityName, -1), quantity - 1)

    def processVariableInitialization(self, variableName, defaultValueStr, lines, startIndex):
        """
        Processes the initialization of a variable.

        Args:
            variableName (str): The name of the variable.
            defaultValueStr (str): The default value string.
            lines (List[str]): List of lines from the problem text.
            startIndex (int): The index to start processing from.

        Returns:
            int: The updated index after processing the variable.
        """
        if variableName not in self.variables:
            return startIndex
        variable = self.variables[variableName]
        entityName = variable.get('entity', '')
        isItems = variable.get('is items', False)

        # Get default value
        defaultValue = self.get_default_value(variable)
        if defaultValueStr:
            defaultValue = self.parseValue(defaultValueStr, variable)

        index = startIndex
        valueLines = []
        while index < len(lines):
            line = lines[index]
            if re.match(r"^\w+\s*:", line) or line == '*':
                break
            valueLines.append(line)
            index += 1

        if isItems:
            # Process items variable
            if variableName not in self.initialValues:
                self.initialValues[variableName] = {}
            lastItemIndex = self.lastItemIndices.get(variableName, -1)
            for line in valueLines:
                line = line.strip()
                if not line:
                    continue
                value = self.parseValue(line, variable)
                lastItemIndex += 1
                self.initialValues[variableName][lastItemIndex] = value
            self.lastItemIndices[variableName] = lastItemIndex
        else:
            # Process variables associated with entities
            if variableName not in self.initialValues:
                self.initialValues[variableName] = []
            values = self.initialValues[variableName]
            entityIndices = self.get_entity_indices_by_type(entityName)
            entityCount = max(len(entityIndices), self.entityCounts.get(entityName, 0))

            # Initialize values with default values
            while len(values) < entityCount:
                values.append(defaultValue)

            lastEntityIndex = -1
            for line in valueLines:
                line = line.strip()
                if not line:
                    continue
                m = re.match(r"(\d+)\.\s*(.*)", line)
                if m:
                    entityIdx = int(m.group(1))
                    valueStr = m.group(2).strip()
                    lastEntityIndex = entityIdx
                else:
                    if lastEntityIndex == -1:
                        entityIdx = 0
                    else:
                        entityIdx = lastEntityIndex + 1
                    lastEntityIndex = entityIdx
                    valueStr = line.strip()

                # Update entityMaxIndices
                if entityName:
                    self.entityMaxIndices[entityName] = max(self.entityMaxIndices.get(entityName, -1), entityIdx)

                # Parse the value
                value = self.parseValue(valueStr, variable)

                # Assign the value
                while len(values) <= entityIdx:
                    values.append(defaultValue)
                values[entityIdx] = value

            self.initialValues[variableName] = values

        return index

    def adjust_entity_counts_and_indices(self):
        """
        Adjust entity counts and indices based on maximum indices used.
        """
        for entityName in self.entities:
            maxIndex = self.entityMaxIndices.get(entityName, -1)
            currentCount = self.entityCounts.get(entityName, 0)
            newCount = max(maxIndex + 1, currentCount)
            self.entityCounts[entityName] = newCount
            self.entityTypeInstances[entityName] = list(range(newCount))

            for varName, variable in self.variables.items():
                if variable.get('entity') == entityName and not variable.get('is items', False):
                    varValues = self.initialValues.get(varName, [])
                    defaultValue = self.get_default_value(variable)
                    while len(varValues) < newCount:
                        varValues.append(defaultValue)
                    self.initialValues[varName] = varValues[:newCount]

    def get_entity_indices_by_type(self, entityName):
        """
        Retrieves the list of entity indices for a given entity type.

        Args:
            entityName (str): The name of the entity.

        Returns:
            List[int]: A list of indices for the entity.
        """
        return self.entityTypeInstances.get(entityName, [])

    def get_default_value(self, variable):
        """
        Returns the default value for a variable based on its type.

        Args:
            variable (dict): The variable definition.

        Returns:
            Any: The default value for the variable.
        """
        varType = variable['type']
        if varType == int:
            return 0
        elif varType == bool:
            return False
        elif varType == Set:
            return set()
        elif varType == Dict:
            return {}
        elif varType in (List, Tuple):
            return []
        else:
            return None

    def parseValue(self, valueStr, variable):
        """
        Parses a value string based on the variable's type.

        Args:
            valueStr (str): The string representation of the value.
            variable (dict): The variable definition.

        Returns:
            Any: The parsed value.
        """
        varType = variable['type']
        if varType == int:
            return self.convert_value_by_type(valueStr, int)
        elif varType == bool:
            return valueStr.lower() in ('true', '1', 'yes', 't')
        elif varType == Set:
            items = [self.convert_value_by_type(x.strip(), int) for x in valueStr.split(',') if x.strip()]
            return set(items)
        elif varType == Dict:
            d = {}
            pairs = valueStr.split(',')
            for pair in pairs:
                pair = pair.strip()
                if not pair:
                    continue
                if '-' in pair:
                    key_str, valueStr = pair.split('-', 1)
                    key = self.convert_value_by_type(key_str.strip(), int)
                    value = self.convert_value_by_type(valueStr.strip(), int)
                    d[key] = value
            return d
        elif varType == List:
            keyTypes = variable.get('key types', [])
            values = [x.strip() for x in valueStr.split(',') if x.strip()]
            convertedValues = [self.convert_value_by_type(val, kt) for val, kt in zip(values, keyTypes)]
            return convertedValues
        elif varType == Tuple:
            keyTypes = variable.get('key types', [])
            values = [x.strip() for x in valueStr.split(',') if x.strip()]
            convertedValues = [self.convert_value_by_type(val, kt) for val, kt in zip(values, keyTypes)]
            return tuple(convertedValues)
        else:
            return valueStr

    def convert_value_by_type(self, value, keyType):
        """
        Converts a value to the specified type.

        Args:
            value (str): The value to convert.
            keyType (type): The target type.

        Returns:
            Any: The converted value.

        Raises:
            ValueError: If the value cannot be converted.
        """
        if keyType == int:
            try:
                return int(value)
            except ValueError:
                # Attempt to interpret value as an entity name
                entityIndex = self.get_entity_index_by_name(value)
                if entityIndex is not None:
                    return entityIndex
                else:
                    raise ValueError(f"Cannot convert value '{value}' to int or known entity name")
        elif keyType == bool:
            return value.lower() in ('true', '1', 'yes', 't')
        else:
            # Handle other types as needed
            return value

    def get_entity_index_by_name(self, name):
        """
        Retrieves the index of an entity by its name.

        Args:
            name (str): The name of the entity.

        Returns:
            int or None: The index of the entity, or None if not found.
        """
        name = name.strip().lower()
        entityIndex = self.entity_name_to_index.get(name)
        if entityIndex is not None:
            return entityIndex
        else:
            return None

    def set_default_values(self):
        """
        Sets default values for variables that were not initialized.
        """
        for varName, variable in self.variables.items():
            if varName in self.initialValues:
                continue
            entityName = variable.get('entity', '')
            isItems = variable.get('is items', False)
            if entityName:
                entityIndices = self.get_entity_indices_by_type(entityName)
            else:
                entityIndices = []

            defaultValue = self.get_default_value(variable)
            if isItems:
                self.initialValues[varName] = {}
            else:
                if variable.get('is constant', False) and entityName:
                    self.initialValues[varName] = tuple([defaultValue] * len(entityIndices))
                elif variable.get('is constant', False):
                    self.initialValues[varName] = defaultValue
                else:
                    self.initialValues[varName] = [defaultValue] * len(entityIndices)

    def ensure_entity_instances(self):
        """
        Ensures that all entities have instances based on variable usage.
        """
        for entityName in self.entities:
            if entityName not in self.entityTypeInstances:
                maxIndex = self.entityMaxIndices.get(entityName, -1)
                quantity = maxIndex + 1 if maxIndex >= 0 else 0
                self.process_entity_quantity(entityName, quantity)
