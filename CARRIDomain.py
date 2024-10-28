import re
from typing import List, Tuple, Dict, Set, Callable


class CARRISimulator:
    def __init__(self):
        pass

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

    def apply_action(self, state, action):
        """
        Apply the action's effects to the state.
        """
        for effect in action['effects']:
            self.apply_effect(effect, state)

    def evaluate_condition(self, problem, state, condition):
        """
        Evaluate a condition against the state and problem.
        """
        # Placeholder for evaluating logical conditions (preconditions).
        # In a real implementation, you would parse the condition and check against the state.
        return True

    def apply_effect(self, state, effect):
        """
        Apply an effect to the state.
        """
        # Placeholder for applying effects to the state.
        # This would modify the state based on the effect.
        pass


class CARRIProblem:
    def __init__(self, constants):
        self.constants = constants  # Tuple of constant values
        self.constants_dict = {name: idx for idx, name in enumerate(constants)}

    def get_constant(self, name):
        """
        Get the value of a constant by name.
        """
        return self.constants[self.constants_dict[name]]

    def advanceState(self, simulator: CARRISimulator, state, action):
        advnaceState = state.copy()
        simulator.apply_action(advnaceState, action)
        return advnaceState


class CARRIState:
    def __init__(self, variables):
        self.variables = variables  # Tuple of variable values
        self.variables_dict = {name: idx for idx, name in enumerate(variables)}

    def get_variable(self, name):
        """
        Get the value of a variable by name.
        """
        return self.variables[self.variables_dict[name]]

    def set_variable(self, name, value):
        """
        Set the value of a variable by name.
        """
        variables_list = list(self.variables)
        variables_list[self.variables_dict[name]] = value
        self.variables = tuple(variables_list)


class CARRITranslator:
    def create_problem(self, carriDomainPath, carriProblemPath) -> tuple:
        self.domainFile = self.read_file(carriDomainPath)
        self.problemFile = self.read_file(carriProblemPath)

        """
        Split and send sections to their respective translators.
        """
        sections = self.split_sections()
        translated_sections = {}
        # Send sections to respective translators
        if "Variables" in sections:
            translated_sections["Variables"] = self.translate_variables(sections["Variables"])
            for name in translated_sections["Variables"]:
                print(f"{name}: {translated_sections['Variables'][name]}")
        if "Actions" in sections:
            print("actions:")
            translated_sections["Actions"] = self.translate_actions(sections["Actions"])
            print(translated_sections["Actions"])
        return translated_sections, self.problemFile

    def read_file(self, file_path):
        """
        Reads a .CARRI file from the given path and returns its content as a string.
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            return re.sub(r"#.*", "", file.read())

    def extract_domain_text(self):
        """
        Extracts the text between "Start Domain" and "End Domain".
        """
        domain_pattern = r"Start Domain:\n(.*?)\nEnd Domain"
        match = re.search(domain_pattern, self.domainFile, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def split_sections(self):
        """
        Splits the .CARRI text into sections.
        """
        domain_text = self.extract_domain_text()
        sections = {}

        # Regex to identify sections and their contents
        section_pattern = r"(?P<section_name>\w+):\s*\n(?P<section_content>.*?)(?=\n\w+:|$)"
        matches = re.finditer(section_pattern, domain_text, re.DOTALL)

        for match in matches:
            section_name = match.group("section_name")
            section_content = match.group("section_content").strip()
            sections[section_name] = section_content

        # Remove the last line from each section content if it starts with 'End'
        for section in sections:
            lines = sections[section].split('\n')
            if lines[-1].startswith("End"):
                sections[section] = '\n'.join(lines[:-1])

        return sections

    def translate_variables(self, variables_text):
        """
        Pass the variables section to the Variables Translator.
        """
        return CARRIVariablesTranslator(variables_text).translate()

    def translate_actions(self, actions_text):
        """
        Pass the actions section to the Actions Translator.
        """
        return CARRIActionsTranslator(actions_text).translate()


class CARRIVariablesTranslator:
    def __init__(self, variables_text):
        self.variables_text = variables_text

    def translate(self):
        """
        Translates the Variables section to a dictionary containing constants and non-constants.
        """
        variables = {}

        # Splitting lines and processing each line to distinguish between constants and non-constants
        lines = [line.strip() for line in self.variables_text.split("\n") if line.strip()]

        for line in lines:
            # Extract the variable type (const, var, items)
            parts = line.split()
            var_type = parts[0]
            name = parts[1]  # Extract the variable name
            entity = parts[-1].strip("()") if parts[-1].startswith("(") else ""  # Related entity without brackets

            # Default type to INT if not specified
            variable_type = parts[2] if len(parts) > 2 else "INT"

            # Determine the data structure type
            if variable_type == "MULTY":
                variable_type = Set[int]
            elif variable_type == "MATCH":
                variable_type = Dict[int, int]
            elif variable_type == "BOOL":
                variable_type = bool
            else:
                variable_type = int

            # Handle items differently to add 'key vars'
            if var_type == "items":
                key_vars_odd, key_vars_even = self.split_key_vars(parts[4:])
                structure_type = List if "var:" in line else Tuple
                details = {
                    "type": structure_type,
                    "entity": entity,
                    "key_vars_odd": key_vars_odd,
                    "key_vars_even": key_vars_even,
                    "is_constant": False
                }
            else:
                details = {
                    "type": variable_type,
                    "entity": entity,
                    "is_constant": var_type == "const"
                }

            # Determine if constant or non-constant
            variables[name] = details

        return variables

    def split_key_vars(self, parts_list):
        """
        Splits the parts list into two separate lists: one for the items at odd indexes and one for the even indexes.
        """
        key_vars_odd = []
        key_vars_even = []

        for i in range(0, len(parts_list), 2):
            if parts_list[i].startswith("("):
                break
            key_vars_odd.append(parts_list[i])
            if i + 1 < len(parts_list):
                key_vars_even.append(parts_list[i + 1])

        return tuple(key_vars_odd), tuple(key_vars_even)


class CARRIActionsTranslator:
    def __init__(self, actions_text):
        self.actions_text = actions_text
        print(actions_text)

    def extract_action_entity(self, action_text):
        """
        Extract the entity that the action is valid for.
        """
        lines = [line.strip() for line in action_text.split("\n") if line.strip()]
        for line in lines:
            if line.startswith("Entity"):
                return line.split()[1]
        return None

    def translate(self):
        """
        Translates the Actions section to a list of actions with preconditions and effects.
        """
        actions = []
        lines = [line.strip() for line in self.actions_text.split("\n") if line.strip()]
        current_action = {}
        for line in lines:
            if line.startswith("Action"):
                if current_action:
                    actions.append(current_action)
                current_action = {
                    "name": line.split()[1],
                    "entity": None,  # Add entity field
                    "parameters": [],
                    "preconditions": [],
                    "conflicting preconditions": [],
                    "effects": [],
                    "cost": 0
                }
            elif line.startswith("Entity"):
                current_action["entity"] = line.split()[1]  # Extract entity information
            elif line.startswith("Parameters"):
                current_action["parameters"] = line.split()[1:]
            elif line.startswith("Preconditions"):
                current_action["preconditions"].append(line.split()[1:])
            elif line.startswith("Conflicting Preconditions"):
                current_action["conflicting preconditions"].append(line.split()[2:])
            elif line.startswith("Effects"):
                current_action["effects"].append(line.split()[1:])
            elif line.startswith("Cost"):
                current_action["cost"] = int(line.split()[1])

        if current_action:
            actions.append(current_action)

        return actions
