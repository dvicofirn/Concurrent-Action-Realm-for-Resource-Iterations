from typing import Dict
from CARRIAction import ActionGenerator
from CARRILogic import *
from CARRILogicParser import parse_conditions, parse_effects

class CARRIActionParser:
    def __init__(self, parsedActions: Dict, parsedEntities: Dict,
                 implementedActions: Dict[str, ActionGenerator]) -> None:
        self.parsed_actions = parsedActions
        self.implementedActions = implementedActions
        self.parsedEntities = parsedEntities

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
                cost = 0

            entities = [self.parsedEntities[entity][0] for entity in actionData["entity par"]]
            parameters = actionData["parameters"]

            # Actions parameters, updated each time a new parameter is created
            paramExpressions = [ParameterNode(i) for i in range(len(parameters))]
            # Parse parameter types (you may need to define how parameter types are provided)
            # For this example, we'll assume parameter types are provided in actionData

            # Parse Preconditions and Effects
            # (Implement parse_conditions and parse_effects methods accordingly)
            if "preconditions" in actionData:
                preconditions=(parse_conditions(actionData["preconditions"],
                                                parameters, paramExpressions, self.parsedEntities))

            if "preconditions add" in actionData:
                preconditions.extend(parse_conditions(actionData["preconditions add"],
                                                      parameters, paramExpressions, self.parsedEntities))

            if "conflicting preconditions" in actionData:
                conflictingPreconditions=(parse_conditions(actionData["conflicting preconditions"],
                                                           parameters, paramExpressions, self.parsedEntities))

            if "conflicting preconditions add" in actionData:
                conflictingPreconditions.extend(parse_conditions(actionData["conflicting preconditions add"],
                                                                 parameters, paramExpressions, self.parsedEntities))

            if "effects" in actionData:
                effects=(parse_effects(actionData["effects"],
                                       parameters, paramExpressions, self.parsedEntities))

            if "effects add" in actionData:
                effects.extend(parse_effects(actionData["effects add"],
                                             parameters, paramExpressions, self.parsedEntities))

            # Parse Cost
            if "costs" in actionData:
                cost = int(actionData["costs"][0]) if actionData["costs"] else 0

            # Create ActionGenerator instance
            action_generator = ActionGenerator(
                name=actionName,
                entities=entities,
                params=parameters,
                preconditions=preconditions,
                conflictingPreconditions=conflictingPreconditions,
                effects=effects,
                cost=cost,
                paramExpressions=paramExpressions # Parameter objects
            )
            actionGenerators.append(action_generator)
            self.implementedActions[actionName] = action_generator

        return actionGenerators










