import re
from typing import Dict, List, Set, Tuple, Any

class CARRIProblemParser:
    def __init__(self, problem_text, entities, variables):
        self.problem_text = problem_text
        self.entities = entities  # From domain parsing
        self.variables = variables  # From domain parsing
        self.initial_values = {}
        self.iterations = []  # To store iterations
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
        for var_name, variable in self.variables.items():
            is_items = variable.get('is_items', False)
            is_constant = variable.get('is_constant', False)
            entity_name = variable.get('entity', '')
            if var_name in self.initial_values:
                if is_constant and not is_items and entity_name:
                    # Constants associated with entities
                    if isinstance(self.initial_values[var_name], list):
                        self.initial_values[var_name] = tuple(self.initial_values[var_name])
                elif is_constant and not entity_name:
                    # Global constants
                    if not isinstance(self.initial_values[var_name], tuple):
                        self.initial_values[var_name] = (self.initial_values[var_name],)

        return self.initial_values, self.iterations

    def split_into_sections(self, lines):
        """
        Splits the lines into initial values and iterations based on '*'
        """
        sections = {'initial': [], 'iterations': []}
        current_section = 'initial'
        current_iteration = None

        for line in lines:
            if line == '*':
                if current_section == 'initial':
                    current_section = 'iterations'
                    current_iteration = []
                    sections['iterations'].append(current_iteration)
                else:
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
            # Check for entity quantities
            m = re.match(r"^([A-Z][a-zA-Z0-9_]*)\s*:\s*(\d+)", line)
            if m:
                entity_name = m.group(1)
                quantity = int(m.group(2))
                self.process_entity_quantity(entity_name, quantity)
                index += 1
                continue

            # Check for variable initialization with optional default value
            m = re.match(r"^(\w+)\s*:\s*(.*)", line)
            if m:
                variable_name = m.group(1)
                default_value_str = m.group(2).strip()
                index = self.process_variable_initialization(variable_name, default_value_str, lines, index + 1)
                continue

            index += 1

        # Update last_item_indices for items variables
        for var_name, variable in self.variables.items():
            if variable.get('is_items', False):
                if var_name in self.initial_values:
                    last_index = max(self.initial_values[var_name].keys(), default=-1)
                    self.last_item_indices[var_name] = last_index
                else:
                    self.last_item_indices[var_name] = -1

    def parse_iteration(self, lines):
        """
        Parses a single iteration from the given lines.
        """
        iteration_values = {}
        index = 0
        while index < len(lines):
            line = lines[index]
            m = re.match(r"^(\w+)\s*:", line)
            if m:
                variable_name = m.group(1)
                if variable_name not in self.variables:
                    index += 1
                    continue
                variable = self.variables[variable_name]
                if not variable.get('is_items', False):
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
        if variable_name not in iteration_values:
            iteration_values[variable_name] = {}

        index = start_index
        value_lines = []
        while index < len(lines):
            line = lines[index]
            if re.match(r"^\w+\s*:", line) or line == '*':
                break
            value_lines.append(line)
            index += 1

        last_item_index = self.last_item_indices.get(variable_name, -1)
        for line in value_lines:
            line = line.strip()
            if not line:
                continue
            value = self.parse_value(line, variable)
            last_item_index += 1
            iteration_values[variable_name][last_item_index] = value
        self.last_item_indices[variable_name] = last_item_index

        return index

    def process_entity_quantity(self, entity_name, quantity):
        if entity_name not in self.entities:
            return
        indices = list(range(quantity))
        self.entity_type_instances[entity_name] = indices
        self.entity_counts[entity_name] = quantity
        self.entity_max_indices[entity_name] = max(self.entity_max_indices.get(entity_name, -1), quantity - 1)

    def process_variable_initialization(self, variable_name, default_value_str, lines, start_index):
        if variable_name not in self.variables:
            return start_index
        variable = self.variables[variable_name]
        entity_name = variable.get('entity', '')
        is_items = variable.get('is_items', False)

        # Get default value
        default_value = self.get_default_value(variable)
        if default_value_str:
            default_value = self.parse_value(default_value_str, variable)

        index = start_index
        value_lines = []
        while index < len(lines):
            line = lines[index]
            if re.match(r"^\w+\s*:", line) or line == '*':
                break
            value_lines.append(line)
            index += 1

        if is_items:
            # Process items variable
            if variable_name not in self.initial_values:
                self.initial_values[variable_name] = {}
            last_item_index = self.last_item_indices.get(variable_name, -1)
            for line in value_lines:
                line = line.strip()
                if not line:
                    continue
                value = self.parse_value(line, variable)
                last_item_index += 1
                self.initial_values[variable_name][last_item_index] = value
            self.last_item_indices[variable_name] = last_item_index
        else:
            # Process variables associated with entities
            if variable_name not in self.initial_values:
                self.initial_values[variable_name] = []
            values = self.initial_values[variable_name]
            entity_indices = self.get_entity_indices_by_type(entity_name)
            entity_count = max(len(entity_indices), self.entity_counts.get(entity_name, 0))

            # Initialize values with default values
            while len(values) < entity_count:
                values.append(default_value)

            last_entity_index = -1
            for line in value_lines:
                line = line.strip()
                if not line:
                    continue
                m = re.match(r"(\d+)\.\s*(.*)", line)
                if m:
                    entity_idx = int(m.group(1))
                    value_str = m.group(2).strip()
                    last_entity_index = entity_idx
                else:
                    if last_entity_index == -1:
                        entity_idx = 0
                    else:
                        entity_idx = last_entity_index + 1
                    last_entity_index = entity_idx
                    value_str = line.strip()

                # Update entity_max_indices
                if entity_name:
                    self.entity_max_indices[entity_name] = max(self.entity_max_indices.get(entity_name, -1), entity_idx)

                # Parse the value
                value = self.parse_value(value_str, variable)

                # Assign the value
                while len(values) <= entity_idx:
                    values.append(default_value)
                values[entity_idx] = value

            self.initial_values[variable_name] = values

        return index

    def adjust_entity_counts_and_indices(self):
        """
        Adjust entity counts and indices based on maximum indices used.
        """
        for entity_name in self.entities:
            max_index = self.entity_max_indices.get(entity_name, -1)
            current_count = self.entity_counts.get(entity_name, 0)
            new_count = max(max_index + 1, current_count)
            self.entity_counts[entity_name] = new_count
            self.entity_type_instances[entity_name] = list(range(new_count))

            for var_name, variable in self.variables.items():
                if variable.get('entity') == entity_name and not variable.get('is_items', False):
                    var_values = self.initial_values.get(var_name, [])
                    default_value = self.get_default_value(variable)
                    while len(var_values) < new_count:
                        var_values.append(default_value)
                    self.initial_values[var_name] = var_values[:new_count]

    def get_entity_indices_by_type(self, entity_name):
        return self.entity_type_instances.get(entity_name, [])

    def get_default_value(self, variable):
        """
        Returns the default value for a variable based on its type.
        """
        var_type = variable['type']
        if var_type == int:
            return 0
        elif var_type == bool:
            return False
        elif var_type == Set:
            return set()
        elif var_type == Dict:
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
            return value_str.lower() in ('true', '1', 'yes', 't')
        elif var_type == Set:
            items = [int(x.strip()) for x in value_str.split(',') if x.strip()]
            return set(items)
        elif var_type == Dict:
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
        elif var_type == List:
            key_types = variable.get('key types', [])
            values = [x.strip() for x in value_str.split(',') if x.strip()]
            converted_values = [self.convert_value_by_type(val, kt) for val, kt in zip(values, key_types)]
            return converted_values
        elif var_type == Tuple:
            key_types = variable.get('key types', [])
            values = [x.strip() for x in value_str.split(',') if x.strip()]
            converted_values = [self.convert_value_by_type(val, kt) for val, kt in zip(values, key_types)]
            return tuple(converted_values)
        else:
            return value_str

    def convert_value_by_type(self, value, key_type):
        if key_type == 'INT':
            return int(value)
        elif key_type == 'BOOL':
            return value.lower() in ('true', '1', 'yes', 't')
        else:
            return value

    def set_default_values(self):
        """
        Sets default values for variables not initialized.
        """
        for var_name, variable in self.variables.items():
            if var_name in self.initial_values:
                continue
            entity_name = variable.get('entity', '')
            is_items = variable.get('is_items', False)
            if entity_name:
                entity_indices = self.get_entity_indices_by_type(entity_name)
            else:
                entity_indices = []

            default_value = self.get_default_value(variable)
            if is_items:
                self.initial_values[var_name] = {}
            else:
                if variable.get('is_constant', False) and entity_name:
                    self.initial_values[var_name] = tuple([default_value] * len(entity_indices))
                elif variable.get('is_constant', False):
                    self.initial_values[var_name] = default_value
                else:
                    self.initial_values[var_name] = [default_value] * len(entity_indices)

    def ensure_entity_instances(self):
        """
        Ensures that all entities have instances based on variable usage.
        """
        for entity_name in self.entities:
            if entity_name not in self.entity_type_instances:
                max_index = self.entity_max_indices.get(entity_name, -1)
                quantity = max_index + 1 if max_index >= 0 else 0
                self.process_entity_quantity(entity_name, quantity)
