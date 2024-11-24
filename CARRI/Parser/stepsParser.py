from typing import Dict, List
from CARRI.action import Step, EnvStep
from CARRI.expression import ConstNode
from CARRI.Parser.contextParser import ContextParser

class EnvStepParser:
    """Parses environment steps into EnvStep instances."""

    def __init__(self, parsedEnvSteps: Dict, parsedEntities: Dict) -> None:
        """Initialize the EnvStepParser with parsed environment steps and entities."""
        self.parsedEnvSteps = parsedEnvSteps
        self.parsedEntities = parsedEntities
        self.parser = ContextParser([], [], self.parsedEntities)

    def parse(self) -> List[EnvStep]:
        """Parse the environment steps and return a list of EnvStep instances."""
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
    """Parses iteration steps into Step instances."""

    def __init__(self, parsedIterStep: List[str], parsedEntities: Dict) -> None:
        """Initialize the IterParser with parsed iteration steps and entities."""
        self.parsedIterStep = parsedIterStep
        self.parsedEntities = parsedEntities
        self.parser = ContextParser([], [], self.parsedEntities)

    def parse(self) -> Step:
        """Parse the iteration step and return a Step instance."""
        effects = self.parser.parse(self.parsedIterStep, "effects")
        return Step(effects)
