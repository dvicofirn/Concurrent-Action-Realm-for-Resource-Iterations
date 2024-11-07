import re
from typing import List, Tuple, Dict, Set
from CARRI.actionLinesParser import parse_action_segments, parse_action_header, parse_segment
from CARRI.problemParser import CARRIProblemParser
from CARRI.actionGeneratorParser import ActionGeneratorParser
from CARRI.stepsParser import EnvStepParser, IterParser
from CARRI.problem import Problem
from CARRI.simulator import Simulator


class Translator:
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

        # Parse the problem file to get initial values
        problem_text = self.extract_problem_text()
        problem_parser = CARRIProblemParser(problem_text, translatedSections["Entities"],
                                            translatedSections["Variables"])
        initial_values, iterations = problem_parser.parse()

        problem = Problem(initialValues=initial_values,
                          variablesInfo=translatedSections["Variables"],
                          entities=translatedSections["Entities"])
        simulator = Simulator(problem, actionGenerators, envSteps, iterStep, translatedSections["Entities"])
        return simulator, iterations

        """print(problem.initState)
        # problem.set_value(problem.initState, "droneCharge", 3, 5)
        # print(problem.initState)
        # Todo: Need to create Simulator, return Simulator, problem and Iterations to Manager.
        # actionGenerators should be given to simulator

        print("-----Entities-----")
        for entity in translatedSections["Entities"]:
            print(f"{entity}: {translatedSections["Entities"][entity]}")
        print("-----Variables-----")
        for variable in translatedSections["Variables"]:
            print(f"{variable}:\n{translatedSections["Variables"][variable]}")
        print("-----Action Generators-----")
        print(type(actionGenerators))
        for actionGenerator in actionGenerators:
            print(actionGenerator)
            print("---")
        print("-----Env Steps-----")
        for step in envSteps:
            print(str(step))
        print("-----Iter step-----")
        print(str(iterStep))
        print("-----Initial Values-----")
        for var_name, values in initial_values.items():
            print(f"{var_name}: {values}")

        print("-----Iterations-----")
        for idx, iteration in enumerate(iterations):
            print(f"Iteration {idx + 1}:")
            for var_name, values in iteration.items():
                print(f"  {var_name}: {values}")

        return translatedSections, initial_values"""

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
    def __init__(self, entities_text):
        self.entities_text = entities_text
        self.entities = {}

    def translate(self):
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
                variable_type = Set
            elif variable_type == "MATCH":
                variable_type = Dict
            elif variable_type == "BOOL":
                variable_type = bool
            else:
                variable_type = int

            # Handle items differently to add 'key types' and 'key names'
            if var_type == "items":
                key_names, key_types = self.split_key_vars(parts[3:])
                structure_type = List if "var:" in line else Tuple
                details = {
                    "type": structure_type,
                    "entity": name,
                    "key types": key_types,
                    "key names": key_names,
                    "is_constant": False,
                    "is_items": True
                }
            else:
                details = {
                    "type": variable_type,
                    "entity": entities,
                    "is_constant": var_type == "const",
                    "is_items": False
                }

            # Add the variable to the dictionary
            variables[name] = details

        return variables

    def split_key_vars(self, parts_list):
        """
        Splits the parts list into two separate lists: one for the key types and one for the key names.
        """
        key_names = []
        key_types = []

        for i in range(0, len(parts_list), 2):
            if parts_list[i].startswith("("):
                break
            key_names.append(parts_list[i].strip(','))
            if i + 1 < len(parts_list):
                key_types.append(parts_list[i + 1].strip(','))

        return tuple(key_names), tuple(key_types)


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


