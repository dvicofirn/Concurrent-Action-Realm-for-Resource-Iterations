import re
from typing import List, Tuple, Dict, Set
from CARRIActionLinesParser import parse_action_segments, parse_action_header

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
        if "Actions" in sections:
            translated_sections["Actions"] = self.translate_actions(sections["Actions"])
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

        # Define allowed section names explicitly
        allowed_section_names = [
            "Entities", "Variables", "Actions", "IterStep", "EnvSteps"
        ]

        # Regex to identify sections by allowed section names
        section_pattern = r"(?P<section_name>(" + "|".join(
            allowed_section_names) + r")):\s*\n(?P<section_content>.*?)(?=\n(" + "|".join(
            allowed_section_names) + r")|$)"
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

    def translate(self):
        """
        Translates the Actions section to a list of actions with preconditions, effects, and costs.
        """
        actions = {}
        # Split the entire actions text by "End Action" to isolate each action block
        action_blocks = self.actions_text.split("End Action")

        for action_block in action_blocks:
            action_block = action_block.strip()
            if not action_block:
                continue
            # Identify the start of an action using the line format "<action_name>: ..."
            lines = action_block.split("\n")
            actionHeader = lines[0].strip()
            actionName, entityParameter, entityType, parameters, inherits = parse_action_header(actionHeader)
            # Initialize the current action dictionary
            actions[actionName] = {
                "entity par": entityParameter,
                "entity type": entityType,
                "parameters": parameters,
                "inherits": inherits,
            }
            parse_action_segments(lines[1:], actions, actionName)
        return actions