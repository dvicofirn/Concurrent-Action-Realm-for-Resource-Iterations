import re
from typing import List, Tuple, Dict, Set
from CARRIActionLinesParser import parse_action_segments, parse_action_header, parse_segment
from ActionGeneratorParser import ActionGeneratorParser
from CARRIStepsParser import EnvStepParser, IterParser


class CARRITranslator:
    def translate(self, carriDomainPath, carriProblemPath) -> tuple:
        self.domainFile = self.read_file(carriDomainPath)
        self.problemFile = self.read_file(carriProblemPath)
        """
        Split and send sections to their respective translators.
        """
        sections = self.split_sections()
        translatedSections = {
            "Entities": {},
            "Variables": {},
            "Actions": {},
            "EnvSteps": {},
            "IterStep": {}
        }
        # Send sections to respective translators
        if "Entities" in sections:
            translatedSections["Entities"] = self.translate_entities(sections["Entities"])
        if "Variables" in sections:
            translatedSections["Variables"] = self.translate_variables(sections["Variables"])
        if "Actions" in sections:
            translatedSections["Actions"] = self.translate_actions(sections["Actions"])
        if "EnvSteps" in sections:
            translatedSections["EnvSteps"] = self.translate_env_steps(sections["EnvSteps"])
        if "IterStep" in sections:
            translatedSections["IterStep"] = self.translate_iter_step(sections["IterStep"])

        actionGenerators = ActionGeneratorParser(translatedSections["Actions"],
                                                 translatedSections["Entities"],
                                                 {}).parse()
        envSteps = EnvStepParser(translatedSections["EnvSteps"], translatedSections["Entities"]).parse()
        iterStep = IterParser(translatedSections["IterStep"], translatedSections["Entities"]).parse()

        print("*-*Action Generators*-*")
        for actionGenerator in actionGenerators:
            print(actionGenerator)
            print("---")
        print("*-*Env Steps*-*")
        for step in envSteps:
            print(str(step))
        print("*-*Iter step*-*")
        print(str(iterStep))

        return translatedSections, self.problemFile

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

    def translate_entities(self, entities_text):
        return CARRIEntitiesTranslator(entities_text).translate()

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

    def translate_env_steps(self, envsStepsText):
        """
        Pass the actions section to the Actions Translator.
        """
        return CARRIEnvStepsTranslator(envsStepsText).translate()

    def translate_iter_step(self, envsStepsText):
        """
        Pass the actions section to the Actions Translator.
        """
        return CARRIIterStepTranslator(envsStepsText).translate()


class CARRIEntitiesTranslator:
    def __init__(self, variables_text):
        self.variables_text = variables_text
        self.entities = {}

    def translate(self):
        # Define a regex pattern to capture entities and their optional origins
        pattern = r'([a-zA-Z\s]+?)(?:\s*\(\s*([a-zA-Z\s]+)\s*\))?(?=,|$)'

        # Use regex findall to match each entity and optional origin in the text
        matches = re.findall(pattern, self.variables_text)

        for entity, inherits in matches:
            entityName = entity.strip()
            if entityName != " ":
                inherits = inherits.strip() if inherits else None
                if inherits == " ":
                    inherits = None
                self.entities[entityName] = (len(self.entities), inherits)

        return self.entities


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
            entities = parts[-1].strip("()") if parts[-1].startswith("(") else ""  # Related entities without brackets

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
                    "entities": entities,
                    "key_vars_odd": key_vars_odd,
                    "key_vars_even": key_vars_even,
                    "is_constant": False
                }
            else:
                details = {
                    "type": variable_type,
                    "entities": entities,
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
        Translates the Actions section to a dictionary of actions with preconditions, effects, and costs.
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
            actionName, parameters, entities, inherits = parse_action_header(actionHeader)
            # Initialize the current action dictionary
            actions[actionName] = {
                "parameters": parameters,
                "entities": entities,
                "inherits": inherits,
            }
            parse_action_segments(lines[1:], actions, actionName)
        return actions


class CARRIEnvStepsTranslator:
    def __init__(self, envStepsText):
        self.envStepsText = envStepsText

    def translate(self):
        """
        Translates the EnvSteps section to a dictionary of env steps with effects, and costs.
        """
        envSteps = {}
        # Split the entire actions text by "End EnvStep" to isolate each action block
        envStepsBlocks = self.envStepsText.split("End EnvStep")

        for envStepBlock in envStepsBlocks:
            envStepBlock = envStepBlock.strip()
            if not envStepBlock:
                continue
            # Identify the start of an action using the line format "<action_name>: ..."
            lines = envStepBlock.split("\n")
            name = lines[0].split(":", 1)[0].strip()
            # Initialize the current envSteps dictionary
            envSteps[name] = {}
            parse_action_segments(lines[1:], envSteps, name)
        return envSteps

class CARRIIterStepTranslator:
    def __init__(self, iterStepText):
        self.iterStepText = iterStepText

    def translate(self):
        """
        Translates the IterStep section to a list of effects.
        """
        # Identify the start of an action using the line format "<action_name>: ..."
        lines = self.iterStepText.split("\n")
        segmentLines = []
        for line in lines:
            line = line.strip()
            if line:
                segmentLines.append(line)
        return parse_segment(segmentLines)
