from typing import Dict, List
from CARRI.action import Step, EnvStep
from CARRI.expression import ConstNode
from CARRI.Parser.contextParser import ContextParser
class EnvStepParser:
    def __init__(self, parsedEnvSteps: Dict, parsedEntities: Dict) -> None:
        self.parsedEnvSteps = parsedEnvSteps
        self.parsedEntities = parsedEntities
        self.parser = ContextParser([], [], self.parsedEntities)

    def parse(self) -> List[EnvStep]:
        envSteps = []
        for envStepName, envStepData in self.parsedEnvSteps.items():
            effects = []
            cost = ConstNode(0)

            # Parse Effects
            if "effects" in envStepData:
                effects = self.parser.parse(envStepData["effects"], "effects")
            # Parse Cost
            if "cost" in envStepData:
                cost = self.parser.parse(envStepData["cost"], "cost")
            # Create EnvStep instance, insert to list.
            envSteps.append(EnvStep(
                name=envStepName,
                effects=effects,
                cost=cost
            ))
        return envSteps

class IterParser:
    def __init__(self, parsedIterStep: List[str], parsedEntities: Dict) -> None:
        self.parsedIterStep = parsedIterStep
        self.parsedEntities = parsedEntities
        self.parser = ContextParser([], [], self.parsedEntities)

    def parse(self) -> Step:
        effects = self.parser.parse(self.parsedIterStep, "effects")
        return Step(effects)
