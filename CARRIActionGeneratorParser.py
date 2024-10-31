from typing import Dict
from CARRIAction import ActionGenerator
from CARRILogic import *
from CARRIContextParser import ContextParser

class CARRIActionParser:
    def __init__(self, parsedActions: Dict, parsedEntities: Dict,
                 implementedActions: Dict[str, ActionGenerator]) -> None:
        self.parsed_actions = parsedActions
        self.parsedEntities = parsedEntities
        self.implementedActions = implementedActions


    def parse(self) -> List[ActionGenerator]:
        actionGenerators = []
        for actionName, actionData in self.parsed_actions.items():
            inherits = actionData.get('inherits')
            if inherits and inherits in self.implementedActions:
                inheritedAction = self.implementedActions[inherits]
                preconditions = inheritedAction.preconditions.copy()
                conflictingPreconditions = inheritedAction.conflictingPreconditions.copy()
                effects = inheritedAction.effects.copy()
                cost = inheritedAction.cost
            else:
                preconditions = []
                conflictingPreconditions = []
                effects = []
                cost = ConstNode(0)

            entities = [self.parsedEntities[entity][0] for entity in actionData["entity par"]]
            parameters = actionData["parameters"]

            # Actions parameters, updated each time a new parameter is created
            paramExpressions = [ValueParameterNode(i) for i in range(len(parameters))]
            # Parse parameter types (you may need to define how parameter types are provided)
            # For this example, we'll assume parameter types are provided in actionData

            # Parse Preconditions, Effects & Cost
            parser = ContextParser(parameters, paramExpressions, self.parsedEntities)
            if "preconditions" in actionData:
                preconditions = parser.parse(actionData["preconditions"], "conditions")

            if "preconditions add" in actionData:
                preconditions.extend(parser.parse(actionData["preconditions add"], "conditions"))

            if "conflicting preconditions" in actionData:
                conflictingPreconditions = parser.parse(actionData["conflicting preconditions"], "conditions")

            if "conflicting preconditions add" in actionData:
                conflictingPreconditions.extend(parser.parse(actionData["conflicting preconditions add"], "conditions"))

            if "effects" in actionData:
                effects = parser.parse(actionData["effects"], "effects")

            if "effects add" in actionData:
                effects.extendparser.parse(actionData["effects add"], "effects")

            # Parse Cost
            if "cost" in actionData:
                cost = parser.parse(actionData["cost"], "cost")

            # Create ActionGenerator instance
            actionGenerator = ActionGenerator(
                name=actionName,
                entities=entities,
                params=parameters,
                preconditions=preconditions,
                conflictingPreconditions=conflictingPreconditions,
                effects=effects,
                cost=cost,
                paramExpressions=paramExpressions # Parameter objects
            )
            # Reorder the preconditions for more efficient valid action production.
            actionGenerator.reArrangePreconditions()
            actionGenerators.append(actionGenerator)
            # This allows next iterations to inherit from current action generator.
            self.implementedActions[actionName] = actionGenerator

        return actionGenerators










