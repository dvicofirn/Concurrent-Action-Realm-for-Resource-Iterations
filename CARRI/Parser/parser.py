from CARRI.Parser.actionLinesParser import parse_action_segments, parse_action_header, parse_segment
from CARRI.Parser.problemParser import CARRIProblemParser
from CARRI.Parser.actionGeneratorParser import ActionGeneratorParser
from CARRI.stepsParser import EnvStepParser, IterParser
from CARRI.problem import Problem
from CARRI.simulator import Simulator


class Parser:
    def parse(self, carriDomainPath, carriProblemPath) -> tuple:
        self.domainFile = self.read_file(carriDomainPath)
        self.problemFile = self.read_file(carriProblemPath)
        """
        Split and send sections to their respective parsers.
        """
        sections = self.split_sections()
        parsedSections = {
            "Entities": {},
            "Variables": {},
            "Actions": {},
            "EnvSteps": {},
            "IterStep": {}
        }
        # Send sections to respective parsers
        if "Entities" in sections:
            parsedSections["Entities"] = self.parse_entities(sections["Entities"])
        if "Variables" in sections:
            parsedSections["Variables"] = self.parse_variables(sections["Variables"])
        if "Actions" in sections:
            parsedSections["Actions"] = self.parse_actions(sections["Actions"])
        if "EnvSteps" in sections:
            parsedSections["EnvSteps"] = self.parse_env_steps(sections["EnvSteps"])
        if "IterStep" in sections:
            parsedSections["IterStep"] = self.parse_iter_step(sections["IterStep"])

        actionGenerators = ActionGeneratorParser(parsedSections["Actions"],
                                                 parsedSections["Entities"]).parse()
        envSteps = EnvStepParser(parsedSections["EnvSteps"], parsedSections["Entities"]).parse()
        iterStep = IterParser(parsedSections["IterStep"], parsedSections["Entities"]).parse()

        # Parse the problem file to get initial values
        problem_text = self.extract_problem_text()
        problem_parser = CARRIProblemParser(problem_text, parsedSections["Entities"],
                                            parsedSections["Variables"])
        initial_values, iterations = problem_parser.parse()

        problem = Problem(initialValues=initial_values,
                          variablesInfo=parsedSections["Variables"],
                          entities=parsedSections["Entities"])
        simulator = Simulator(problem, actionGenerators, envSteps, iterStep, parsedSections["Entities"])

        return simulator, iterations

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

    def extract_problem_text(self):
        """
        Extracts the text between "Start Problem" and "End Problem".
        """
        problem_pattern = r"Start Problem:\n(.*?)\nEnd Problem"
        match = re.search(problem_pattern, self.problemFile, re.DOTALL)
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

    def parse_entities(self, entities_text):
        return CARRIEntitiesParser(entities_text).parse()

    def parse_variables(self, variables_text):
        """
        Pass the variables section to the Variables Parser.
        """
        return CARRIVariablesParser(variables_text).parse()

    def parse_actions(self, actions_text):
        """
        Pass the actions section to the Actions Parser.
        """
        return CARRIActionsParser(actions_text).parse()

    def parse_env_steps(self, envsStepsText):
        """
        Pass the actions section to the Actions Parser.
        """
        return CARRIEnvStepsParser(envsStepsText).parse()

    def parse_iter_step(self, envsStepsText):
        """
        Pass the actions section to the Actions Parser.
        """
        return CARRIIterStepParser(envsStepsText).parse()


class CARRIEntitiesParser:
    def __init__(self, entities_text):
        self.entities_text = entities_text
        self.entities = {}

    def parse(self):
        # Define a regex pattern to capture entities and their optional origins
        pattern = r'([a-zA-Z_][a-zA-Z0-9_\s]*)(?:\s*\(\s*([a-zA-Z_][a-zA-Z0-9_\s]*)\s*\))?(?=,|$)'

        # Use regex findall to match each entity and optional origin in the text
        matches = re.findall(pattern, self.entities_text)

        for entity, inherits in matches:
            entityName = entity.strip()
            if entityName != "":
                inherits = inherits.strip() if inherits else None
                if inherits == "":
                    inherits = None
                self.entities[entityName] = (len(self.entities), inherits)

        return self.entities


import re
from typing import Set, Dict, List, Tuple

class CARRIVariablesParser:
    def __init__(self, variables_text):
        self.variables_text = variables_text

    def parse(self):
        """
        Parses the Variables section to a dictionary containing constants, variables, and items.
        """
        variables = {}
        lines = [line.strip() for line in self.variables_text.split("\n") if line.strip()]

        # Patterns to match variable and items definitions
        variable_pattern = r'^(const|var)\s+(.+?)\s+([A-Z]+)\s*-\s*([A-Za-z0-9_]+)(?:\s*\(([^)]+)\))?$'
        items_pattern = r'^items\s+(.+?)\s+(var|const)\s+(.*)$'

        for line in lines:
            variable_match = re.match(variable_pattern, line)
            items_match = re.match(items_pattern, line)
            if variable_match:
                # Parse const or var line
                var_type = variable_match.group(1)   # 'const' or 'var'
                name = variable_match.group(2).strip()
                variable_type_str = variable_match.group(3)  # 'INT', 'BOOL', 'MULTY', 'MATCH'
                entity_name = variable_match.group(4)   # '-'
                base_name = line.split('(')
                if len(base_name) > 1:
                    base_name = base_name[1].strip(')')
                else:
                    base_name = None

                # Determine the data structure type
                if variable_type_str == "MULTY":
                    variable_type = Set
                elif variable_type_str == "MATCH":
                    variable_type = Dict
                elif variable_type_str == "BOOL":
                    variable_type = bool
                else:
                    variable_type = int

                details = {
                    "type": variable_type,
                    "entity": entity_name,
                    "base_name": base_name,
                    "is_constant": var_type == "const",
                    "is_items": False
                }

                variables[name] = details

            elif items_match:
                # Parse items line
                entity_name = items_match.group(1).strip()
                is_var_const = items_match.group(2)  # 'var' or 'const'
                key_definitions_str = items_match.group(3)

                structure_type = Tuple if is_var_const == 'const' else List

                key_names = []
                key_types = []
                key_base_names = []

                # Split key definitions by commas
                key_parts = [kp.strip() for kp in key_definitions_str.split(',') if kp.strip()]
                for key_part in key_parts:
                    # Each key_part may be: keyName type [ '(' baseName ')' ]
                    key_pattern = r'(\w+)\s+([A-Z]+)(?:\s*\(([^)]+)\))?'
                    key_match = re.match(key_pattern, key_part)
                    if key_match:
                        key_name = key_match.group(1)
                        key_type_str = key_match.group(2)
                        key_base_name = key_match.group(3)  # May be None
                        key_names.append(key_name)
                        key_type = None
                        if key_type_str == "INT":
                            key_type = int
                        elif key_type_str == "BOOL":
                            key_type = bool
                        key_types.append(key_type)
                        key_base_names.append(key_base_name)
                    else:
                        raise ValueError(f"Invalid key definition: {key_part}")

                details = {
                    "type": structure_type,
                    "entity": entity_name,
                    "base_name": None,
                    "key names": tuple(key_names),
                    "key types": tuple(key_types),
                    "key base names": tuple(key_base_names),
                    "is_constant": False,
                    "is_items": True
                }

                variables[entity_name] = details

            else:
                raise ValueError(f"Invalid line format: {line}")

        return variables



class CARRIActionsParser:
    def __init__(self, actions_text):
        self.actions_text = actions_text

    def parse(self):
        """
        Parses the Actions section to a dictionary of actions with preconditions, effects, and costs.
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


class CARRIEnvStepsParser:
    def __init__(self, envStepsText):
        self.envStepsText = envStepsText

    def parse(self):
        """
        Parses the EnvSteps section to a dictionary of env steps with effects, and costs.
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


class CARRIIterStepParser:
    def __init__(self, iterStepText):
        self.iterStepText = iterStepText

    def parse(self):
        """
        Parses the IterStep section to a list of effects.
        """
        # Identify the start of an action using the line format "<action_name>: ..."
        lines = self.iterStepText.split("\n")
        segmentLines = []
        for line in lines:
            line = line.strip()
            if line:
                segmentLines.append(line)
        return parse_segment(segmentLines)


