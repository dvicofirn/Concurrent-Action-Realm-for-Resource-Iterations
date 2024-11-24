from typing import Dict
from CARRI.action import ActionGenerator
from CARRI.expression import *
from CARRI.Parser.contextParser import ContextParser

baseActionNames = ("Wait", "Travel", "Pick", "Deliver")

class ActionGeneratorParser:
    """Parses action definitions into ActionGenerator instances."""
    def __init__(self, parsedActions: Dict, parsedEntities: Dict) -> None:
        """Initialize the parser with parsed actions and entities."""
        self.parsedActions = parsedActions
        self.parsedEntities = parsedEntities
        self.implementedActions = {}  # Dict[str, ActionGenerator]
        self.baseActionsDict = {}  # baseActionsDict: Dict[str, str]

    def parse(self) -> List[ActionGenerator]:
        """Parse the actions and return a list of ActionGenerator instances."""
        actionGenerators = []
        for actionName, actionData in self.parsedActions.items():
            baseActionName = None
            inherits = actionData.get('inherits')
            if inherits and inherits in self.implementedActions:
                inheritedActionGeneartor = self.implementedActions[inherits]
                if inheritedActionGeneartor.name in self.baseActionsDict:
                    baseActionName = self.baseActionsDict[inheritedActionGeneartor.name]
                    self.baseActionsDict[actionName] = baseActionName

                """
                Copies should be shallow.
                Although inheriting generators might affect each other,
                in practice they do not, since each generator resets parameters after action.
                """
                paramExpressions = inheritedActionGeneartor.paramExpressions.copy()  # Should be shallow copy.
                preconditions = inheritedActionGeneartor.preconditions.copy()
                conflictingPreconditions = inheritedActionGeneartor.conflictingPreconditions.copy()
                effects = inheritedActionGeneartor.effects.copy()
                cost = inheritedActionGeneartor.cost
            else:
                paramExpressions = []
                preconditions = []
                conflictingPreconditions = []
                effects = []
                cost = ConstNode(0)
                if inherits and inherits in baseActionNames:
                    baseActionName = inherits
                    self.baseActionsDict[actionName] = baseActionName

            entities = [self.parsedEntities[entity][0] for entity in actionData["entities"]]
            parameters = actionData["parameters"]

            """
            Action parameters are updated each time a new parameter is created.
            For newly introduced entities, create new parameters.
            Do not rearrange the existing parameters' order.
            """
            paramExpressions.extend([ValueParameterNode(len(paramExpressions) + i)
                                     for i in range(len(parameters) - len(paramExpressions))])

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
                effects.extend(parser.parse(actionData["effects add"], "effects"))

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
                paramExpressions=paramExpressions,  # Parameter objects
                baseActionName=baseActionName
            )
            # Reorder the preconditions for more efficient valid action production.
            actionGenerator.reArrangePreconditions()
            actionGenerators.append(actionGenerator)
            # This allows next iterations to inherit from current action generator.
            self.implementedActions[actionName] = actionGenerator

        return actionGenerators
