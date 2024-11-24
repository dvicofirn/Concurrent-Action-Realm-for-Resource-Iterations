from CARRI.Parser.actionLinesParser import parse_action_segments, parse_action_header, parse_segment
from CARRI.Parser.problemParser import CARRIProblemParser
from CARRI.Parser.actionGeneratorParser import ActionGeneratorParser
from CARRI.Parser.stepsParser import EnvStepParser, IterParser
from CARRI.problem import Problem
from CARRI.simulator import Simulator


class Parser:
    """Main parser class to parse CARRI domain and problem files into a simulator and iterations."""

    def parse(self, carriDomainPath, carriProblemPath) -> tuple:
        """Parse the domain and problem files and return a simulator and the number of iterations."""
        self.domainFile = self.read_file(carriDomainPath)
        self.problemFile = self.read_file(carriProblemPath)

        # Split and send sections to their respective parsers.
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
        problemText = self.extract_problem_text()
        problemParser = CARRIProblemParser(problemText, parsedSections["Entities"],
                                           parsedSections["Variables"])
        initialValues, iterations = problemParser.parse()

        problem = Problem(initialValues=initialValues,
                          variablesInfo=parsedSections["Variables"],
                          entities=parsedSections["Entities"])
        simulator = Simulator(problem, actionGenerators, envSteps, iterStep, parsedSections["Entities"])

        return simulator, iterations

    def read_file(self, filePath):
        """
        Read a .CARRI file from the given path and return its content as a string.
        Removes comments starting with '#'.
        """
        with open(filePath, 'r', encoding='utf-8') as file:
            return re.sub(r"#.*", "", file.read())

    def extract_domain_text(self):
        """
        Extract the text between "Start Domain" and "End Domain" from the domain file.
        """
        domainPattern = r"Start Domain:\n(.*?)\nEnd Domain"
        match = re.search(domainPattern, self.domainFile, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def extract_problem_text(self):
        """
        Extract the text between "Start Problem" and "End Problem" from the problem file.
        """
        problemPattern = r"Start Problem:\n(.*?)\nEnd Problem"
        match = re.search(problemPattern, self.problemFile, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def split_sections(self):
        """
        Split the domain text into sections such as Entities, Variables, Actions, IterStep, and EnvSteps.
        """
        domainText = self.extract_domain_text()
        sections = {}

        # Define allowed section names explicitly
        allowedSectionNames = [
            "Entities", "Variables", "Actions", "IterStep", "EnvSteps"
        ]

        # Regex to identify sections by allowed section names
        sectionPattern = r"(?P<sectionName>(" + "|".join(
            allowedSectionNames) + r")):\s*\n(?P<sectionContent>.*?)(?=\n(" + "|".join(
            allowedSectionNames) + r")|$)"
        matches = re.finditer(sectionPattern, domainText, re.DOTALL)

        for match in matches:
            sectionName = match.group("sectionName")
            sectionContent = match.group("sectionContent").strip()
            sections[sectionName] = sectionContent

        # Remove the last line from each section content if it starts with 'End'
        for section in sections:
            lines = sections[section].split('\n')
            if lines[-1].startswith("End"):
                sections[section] = '\n'.join(lines[:-1])

        return sections

    def parse_entities(self, entitiesText):
        """Parse the Entities section using CARRIEntitiesParser."""
        return CARRIEntitiesParser(entitiesText).parse()

    def parse_variables(self, variablesText):
        """Parse the Variables section using CARRIVariablesParser."""
        return CARRIVariablesParser(variablesText).parse()

    def parse_actions(self, actionsText):
        """Parse the Actions section using CARRIActionsParser."""
        return CARRIActionsParser(actionsText).parse()

    def parse_env_steps(self, envsStepsText):
        """Parse the EnvSteps section using CARRIEnvStepsParser."""
        return CARRIEnvStepsParser(envsStepsText).parse()

    def parse_iter_step(self, envsStepsText):
        """Parse the IterStep section using CARRIIterStepParser."""
        return CARRIIterStepParser(envsStepsText).parse()


class CARRIEntitiesParser:
    """Parses the Entities section into a dictionary of entity names and their inheritance."""

    def __init__(self, entitiesText):
        """Initialize the parser with the entities text."""
        self.entitiesText = entitiesText
        self.entities = {}

    def parse(self):
        """
        Parse the entities text and return a dictionary with entity names as keys.
        Each entity is assigned a unique index and optional inheritance.
        """
        # Define a regex pattern to capture entities and their optional origins
        pattern = r'([a-zA-Z_][a-zA-Z0-9_\s]*)(?:\s*\(\s*([a-zA-Z_][a-zA-Z0-9_\s]*)\s*\))?(?=,|$)'

        # Use regex findall to match each entity and optional inheritance in the text
        matches = re.findall(pattern, self.entitiesText)

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
    """Parses the Variables section into a dictionary containing constants, variables, and items."""

    def __init__(self, variablesText):
        """Initialize the parser with the variables text."""
        self.variablesText = variablesText

    def parse(self):
        """
        Parse the variables text and return a dictionary with variable names as keys.
        Each variable includes details like type, entity, base name, and whether it is constant or items.
        """
        variables = {}
        lines = [line.strip() for line in self.variablesText.split("\n") if line.strip()]

        # Patterns to match variable and items definitions
        variablePattern = r'^(const|var)\s+(.+?)\s+([A-Z]+)\s*-\s*([A-Za-z0-9_]+)(?:\s*\(([^)]+)\))?$'
        itemsPattern = r'^items\s+(.+?)\s+(var|const)\s+(.*)$'

        for line in lines:
            variableMatch = re.match(variablePattern, line)
            itemsMatch = re.match(itemsPattern, line)
            if variableMatch:
                # Parse const or var line
                varType = variableMatch.group(1)   # 'const' or 'var'
                name = variableMatch.group(2).strip()
                variableTypeStr = variableMatch.group(3)  # 'INT', 'BOOL', 'MULTY', 'MATCH'
                entityName = variableMatch.group(4)   # Entity name after '-'
                baseName = line.split('(')
                if len(baseName) > 1:
                    baseName = baseName[1].strip(')')
                else:
                    baseName = None

                # Determine the data structure type
                if variableTypeStr == "MULTY":
                    variableType = Set
                elif variableTypeStr == "MATCH":
                    variableType = Dict
                elif variableTypeStr == "BOOL":
                    variableType = bool
                else:
                    variableType = int

                details = {
                    "type": variableType,
                    "entity": entityName,
                    "base name": baseName,
                    "is constant": varType == "const",
                    "is items": False
                }

                variables[name] = details

            elif itemsMatch:
                # Parse items line
                entityName = itemsMatch.group(1).strip()
                isVarConst = itemsMatch.group(2)  # 'var' or 'const'
                keyDefinitionsStr = itemsMatch.group(3)

                structureType = Tuple if isVarConst == 'const' else List

                keyNames = []
                keyTypes = []
                keyBaseNames = []

                # Split key definitions by commas
                keyParts = [kp.strip() for kp in keyDefinitionsStr.split(',') if kp.strip()]
                for keyPart in keyParts:
                    # Each keyPart may be: keyName type [ '(' base name ')' ]
                    keyPattern = r'(\w+)\s+([A-Z]+)(?:\s*\(([^)]+)\))?'
                    keyMatch = re.match(keyPattern, keyPart)
                    if keyMatch:
                        keyName = keyMatch.group(1)
                        keyTypeStr = keyMatch.group(2)
                        keyBaseName = keyMatch.group(3)  # Could be None
                        keyNames.append(keyName)
                        keyType = None
                        if keyTypeStr == "INT":
                            keyType = int
                        elif keyTypeStr == "BOOL":
                            keyType = bool
                        keyTypes.append(keyType)
                        keyBaseNames.append(keyBaseName)
                    else:
                        raise ValueError(f"Invalid key definition: {keyPart}")

                details = {
                    "type": structureType,
                    "entity": entityName,
                    "base name": None,
                    "key names": tuple(keyNames),
                    "key types": tuple(keyTypes),
                    "key base names": tuple(keyBaseNames),
                    "is constant": False,
                    "is items": True
                }

                variables[entityName] = details

            else:
                raise ValueError(f"Invalid line format: {line}")

        return variables


class CARRIActionsParser:
    """Parses the Actions section into a dictionary of actions with their details."""

    def __init__(self, actionsText):
        """Initialize the parser with the actions text."""
        self.actionsText = actionsText

    def parse(self):
        """
        Parse the actions text and return a dictionary with action names as keys.
        Each action includes parameters, entities, inherits, preconditions, effects, and costs.
        """
        actions = {}
        # Split the entire actions text by "End Action" to isolate each action block
        actionBlocks = self.actionsText.split("End Action")

        for actionBlock in actionBlocks:
            actionBlock = actionBlock.strip()
            if not actionBlock:
                continue
            # Identify the start of an action using the line format "<actionName>: ..."
            lines = actionBlock.split("\n")
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
    """Parses the EnvSteps section into a dictionary of environment steps with their effects and costs."""

    def __init__(self, envStepsText):
        """Initialize the parser with the environment steps text."""
        self.envStepsText = envStepsText

    def parse(self):
        """
        Parse the environment steps text and return a dictionary with step names as keys.
        Each step includes effects and costs.
        """
        envSteps = {}
        # Split the entire text by "End EnvStep" to isolate each env step block
        envStepsBlocks = self.envStepsText.split("End EnvStep")

        for envStepBlock in envStepsBlocks:
            envStepBlock = envStepBlock.strip()
            if not envStepBlock:
                continue
            # Identify the start of an env step using the line format "<step_name>: ..."
            lines = envStepBlock.split("\n")
            name = lines[0].split(":", 1)[0].strip()
            # Initialize the current envSteps dictionary
            envSteps[name] = {}
            parse_action_segments(lines[1:], envSteps, name)
        return envSteps


class CARRIIterStepParser:
    """Parses the IterStep section into a list of effects."""

    def __init__(self, iterStepText):
        """Initialize the parser with the iteration step text."""
        self.iterStepText = iterStepText

    def parse(self):
        """
        Parse the iteration step text and return a list of effects.
        """
        # Split the text into lines and remove empty lines
        lines = self.iterStepText.split("\n")
        segmentLines = []
        for line in lines:
            line = line.strip()
            if line:
                segmentLines.append(line)
        return parse_segment(segmentLines)
