import re
from typing import Dict, List, Set, Tuple
class CARRIProblemParser:
    def __init__(self, problem_text, entities, variables):
        self.problem_text = problem_text
        self.entities = entities  # From domain parsing
        self.variables = variables  # From domain parsing
        self.initial_values = {}
        self.iterations = []  # NEW: To store iterations
        self.entity_type_instances = {}  # {entity_name: [indices]}
        self.entity_counts = {}  # {entity_name: count}
        self.entity_max_indices = {}  # To keep track of maximum index used per entity
        self.last_item_indices = {}  # To keep track of last item index for each 'items' variable

    def parse(self):
        """
        Parses the problem text and initializes variables and entities, including iterations.
        """
        # Split the problem text into lines
        lines = self.problem_text.split('\n')
        # Remove comments and empty lines
        lines = [re.sub(r"#.*", "", line).strip() for line in lines]
        # Split lines into initial values and iterations based on '*'
        sections = self.split_into_sections(lines)

        # Parse initial values
        self.parse_initial_values(sections['initial'])

        # Parse iterations
        for iteration_lines in sections['iterations']:
            iteration_values = self.parse_iteration(iteration_lines)
            self.iterations.append(iteration_values)

        # Ensure all entities have at least one instance
        self.ensure_entity_instances()

        # Adjust entity counts and indices based on maximum indices used in variable initializations
        self.adjust_entity_counts_and_indices()

        # Set default values for variables not initialized
        self.set_default_values()

        # Convert lists to tuples where appropriate
        for var_name, variable in self.variables.items():
            if variable.get('is_items', False):
                if var_name in self.initial_values:
                    last_index = max(self.initial_values[var_name].keys(), default=-1)
                    self.last_item_indices[var_name] = last_index
                else:
                    self.last_item_indices[var_name] = -1

        return self.initial_values, self.iterations

    def split_into_sections(self, lines):
        """
        Splits the lines into initial values and iterations based on '*'
        """
        sections = {'initial': [], 'iterations': []}
        current_section = 'initial'
        current_iteration = None  # Start with None to detect the first iteration

        for line in lines:
            if line == '*':
                if current_section == 'initial':
                    current_section = 'iterations'
                    current_iteration = []
                    sections['iterations'].append(current_iteration)
                else:
                    # Append the current iteration and start a new one
                    current_iteration = []
                    sections['iterations'].append(current_iteration)
            else:
                if current_section == 'initial':
                    sections['initial'].append(line)
                else:
                    current_iteration.append(line)

        return sections

    def parse_initial_values(self, lines):
        """
        Parses the initial values from the given lines.
        """
        index = 0
        while index < len(lines):
            line = lines[index]
            # Check if the line is an entity quantity (Entity names start with uppercase letters)
            m = re.match(r"^([A-Z][a-zA-Z0-9_]*)\s*:\s*(\d+)", line)
            if m:
                entity_name = m.group(1)
                quantity = int(m.group(2))
                self.process_entity_quantity(entity_name, quantity)
                index += 1
                continue

            # Check if it's a variable initialization
            m = re.match(r"^(\w+)\s*:", line)
            if m:
                variable_name = m.group(1)
                index = self.process_variable_initialization(variable_name, lines, index + 1)
                continue

            index += 1

    def parse_iteration(self, lines):
        """
        Parses a single iteration from the given lines.
        Returns a dictionary of variables and their added items.
        """
        iteration_values = {}
        index = 0
        while index < len(lines):
            line = lines[index]
            # Check if it's a variable initialization
            m = re.match(r"^(\w+)\s*:", line)
            if m:
                variable_name = m.group(1)
                if variable_name not in self.variables:
                    print(f"Variable {variable_name} not found in domain variables.")
                    index += 1
                    continue
                variable = self.variables[variable_name]
                if not variable.get('is_items', False):
                    print(f"Variable {variable_name} is not an 'items' variable and cannot be added in iterations.")
                    index += 1
                    continue
                index = self.process_iteration_variable(variable_name, lines, index + 1, iteration_values)
                continue

            index += 1
        return iteration_values

    def process_iteration_variable(self, variable_name, lines, start_index, iteration_values):
        """
        Processes a variable within an iteration.
        """
        variable = self.variables[variable_name]
        var_type = variable['type']
        entity_name = variable['entity']

        # Initialize the iteration variable dictionary if not already
        if variable_name not in iteration_values:
            iteration_values[variable_name] = {}

        index = start_index

        # Collect all lines under this variable until we reach a new variable declaration
        value_lines = []
        while index < len(lines):
            line = lines[index]
            if re.match(r"^\w+\s*:", line) or line == '*':
                break  # New variable or end of iteration
            value_lines.append(line)
            index += 1

        # Process the value lines
        last_item_index = self.last_item_indices.get(variable_name, -1)
        for line in value_lines:
            line = line.strip()
            if not line:
                continue
            # Parse the value string based on the variable type
            value = self.parse_value(line, variable)
            # Increment the item index
            last_item_index += 1
            # Add the item to the iteration values
            iteration_values[variable_name][last_item_index] = value
        # Update the last_item_indices
        self.last_item_indices[variable_name] = last_item_index

        return index

    def process_entity_quantity(self, entity_name, quantity):
        if entity_name not in self.entities:
            print(f"Entity {entity_name} not found in domain entities.")
            return
        indices = list(range(quantity))
        self.entity_type_instances[entity_name] = indices
        self.entity_counts[entity_name] = quantity
        self.entity_max_indices[entity_name] = quantity - 1  # Initialize max index to quantity -1

    def process_variable_initialization(self, variable_name, lines, start_index):
        if variable_name not in self.variables:
            print(f"Variable {variable_name} not found in domain variables.")
            return start_index
        variable = self.variables[variable_name]
        var_type = variable['type']
        entity_name = variable['entity']
        is_items = variable.get('is_items', False)

        # Get the list of entity indices this variable applies to
        entity_indices = self.get_entity_indices_by_type(entity_name)
        if not entity_indices:
            # If no entities of this type, assume count is 1
            self.process_entity_quantity(entity_name, 0)
            entity_indices = self.entity_type_instances[entity_name]

        default_value = self.get_default_value(var_type)
        if variable_name not in self.initial_values:
            if is_items:
                self.initial_values[variable_name] = {}
            else:
                # Initialize with default values for existing entity indices
                self.initial_values[variable_name] = [default_value] * len(entity_indices)

        index = start_index

        # Collect all lines under this variable until we reach a new variable or entity declaration
        value_lines = []
        while index < len(lines):
            line = lines[index]
            if re.match(r"^\w+\s*:", line):
                break  # New variable or entity
            value_lines.append(line)
            index += 1

        # If no value lines, assign default values
        if not value_lines:
            return index

        # Now process value_lines
        # Check if it's a single value assignment
        if len(value_lines) == 1 and not re.match(r"^\d+\.", value_lines[0]):
            # Single value assignment
            value_str = value_lines[0].strip()
            value = self.parse_value(value_str, variable)
            if is_items:
                for entity_idx in entity_indices:
                    self.initial_values[variable_name][entity_idx] = value
            else:
                self.initial_values[variable_name] = [value] * len(entity_indices)
        else:
            # Multiple values
            last_entity_index = -1
            for line in value_lines:
                line = line.strip()
                if not line:
                    continue
                # Check for indexed value: e.g., "2. 1"
                m = re.match(r"(\d+)\.\s*(.*)", line)
                if m:
                    entity_idx = int(m.group(1))
                    value_str = m.group(2).strip()
                    last_entity_index = entity_idx
                else:
                    # No index specified, use last_entity_index +1
                    if last_entity_index == -1:
                        entity_idx = 0
                    else:
                        entity_idx = last_entity_index + 1
                    last_entity_index = entity_idx
                    value_str = line.strip()

                # Update entity_max_indices
                self.entity_max_indices[entity_name] = max(self.entity_max_indices.get(entity_name, -1), entity_idx)

                # Parse the value string based on the variable type
                value = self.parse_value(value_str, variable)
                # Assign the value to the variable for the entity
                if is_items:
                    self.initial_values[variable_name][entity_idx] = value
                else:
                    # Ensure initial_values[variable_name] is long enough
                    while len(self.initial_values[variable_name]) <= entity_idx:
                        self.initial_values[variable_name].append(default_value)
                    self.initial_values[variable_name][entity_idx] = value

        return index

    def adjust_entity_counts_and_indices(self):
        """
        Adjust entity counts and indices based on maximum indices used in variable initializations.
        """
        for entity_name in self.entities:
            max_index = self.entity_max_indices.get(entity_name, -1)
            current_count = self.entity_counts.get(entity_name, 0)
            if max_index >= current_count:
                # Need to adjust the entity count and indices
                new_count = max_index + 1
                self.entity_counts[entity_name] = new_count
                if entity_name in self.entity_type_instances:
                    current_indices = self.entity_type_instances[entity_name]
                    new_indices = list(range(new_count))
                    self.entity_type_instances[entity_name] = new_indices
                else:
                    self.entity_type_instances[entity_name] = list(range(new_count))
                # Also adjust initial_values for variables associated with this entity
                for var_name, variable in self.variables.items():
                    if variable['entity'] == entity_name:
                        if var_name not in self.initial_values:
                            # Initialize variable with default values
                            default_value = self.get_default_value(variable['type'])
                            if variable.get('is_items', False):
                                self.initial_values[var_name] = {}
                            else:
                                self.initial_values[var_name] = [default_value] * new_count
                        else:
                            var_values = self.initial_values[var_name]
                            default_value = self.get_default_value(variable['type'])
                            if isinstance(var_values, list):
                                while len(var_values) < new_count:
                                    var_values.append(default_value)
                                self.initial_values[var_name] = var_values[:new_count]  # Ensure length matches
            # For variables not yet initialized, set their initial values
            # self.set_default_values()  # Removed to prevent overwriting items added in iterations

    def get_entity_indices_by_type(self, entity_name):
        return self.entity_type_instances.get(entity_name, [])

    def get_default_value(self, var_type):
        if var_type == int:
            return 0
        elif var_type == bool:
            return False
        elif var_type == Set[int]:
            return set()
        elif var_type == Dict[int, int]:
            return {}
        elif var_type in (List, Tuple):
            return []
        else:
            return None

    def parse_value(self, value_str, variable):
        var_type = variable['type']
        if var_type == int:
            return int(value_str)
        elif var_type == bool:
            return value_str.lower() in ('true', '1')
        elif var_type == Set[int]:
            items = [int(x.strip()) for x in value_str.split(',') if x.strip()]
            return set(items)
        elif var_type == Dict[int, int]:
            d = {}
            pairs = value_str.split(',')
            for pair in pairs:
                pair = pair.strip()
                if not pair:
                    continue
                if '-' in pair:
                    key_str, value_str = pair.split('-', 1)
                    key = int(key_str.strip())
                    value = int(value_str.strip())
                    d[key] = value
            return d
        elif var_type in (List, Tuple):
            # For items variables
            key_types = variable.get('key types', [])
            key_names = variable.get('key names', [])
            values = [x.strip() for x in value_str.split(',') if x.strip()]
            # Convert values according to key types
            converted_values = []
            for value, key_type in zip(values, key_types):
                converted_value = self.convert_value_by_type(value, key_type.strip(','))
                converted_values.append(converted_value)
            return tuple(converted_values)
        else:
            return value_str

    def convert_value_by_type(self, value, key_type):
        if key_type == 'INT':
            return int(value)
        elif key_type == 'BOOL':
            return value.lower() in ('true', '1')
        else:
            # Handle other types as needed
            return value

    def set_default_values(self):
        """
        Sets default values for variables not initialized in the problem file.
        """
        for var_name, variable in self.variables.items():
            if var_name in self.initial_values:
                continue
            var_type = variable['type']
            entity_name = variable['entity']
            is_items = variable.get('is_items', False)
            entity_indices = self.get_entity_indices_by_type(entity_name)
            if not entity_indices:
                # No entities of this type instantiated yet, create one
                self.process_entity_quantity(entity_name, 0)
                entity_indices = self.entity_type_instances[entity_name]

            default_value = self.get_default_value(var_type)
            if is_items:
                self.initial_values[var_name] = {}
            else:
                self.initial_values[var_name] = [default_value] * len(entity_indices)

    def ensure_entity_instances(self):
        """
        Ensures that all entities have at least one instance.
        """
        for entity_name in self.entities:
            if entity_name not in self.entity_type_instances:
                # Create default instances for entities with no quantity specified
                self.process_entity_quantity(entity_name, 0)

