from copy import copy
from CARRIRealm import CARRIProblem, CARRIState
from CARRILogic import ExpressionNode, ParameterNode, Update
from typing import List, Dict, Iterable


class Action:
    def __init__(self, name: str, preconditions: List[ExpressionNode],
                 conflictingPreconditions: List[ExpressionNode],
                 effects: List[Update], cost: ExpressionNode):
        self.name = name
        self.preconditions = preconditions  # List of Condition objects
        self.conflictingPreconditions = conflictingPreconditions
        self.effects = effects  # List of Effect objects
        self.cost = cost
        # self.entities = entities # Currently not implemented
        # self.params = params # Currently not implemented

    def validate(self, problem, state):
        return (all(precondition.evaluate(problem, state) for precondition in self.preconditions)
                and all(precondition.evaluate(problem, state) for precondition in self.conflictingPreconditions))

    def reValidate(self, problem, state):
        return all(precondition.evaluate(problem, state) for precondition in self.conflictingPreconditions)

    def apply(self, problem, state):
        for effect in self.effects:
            effect.apply(problem, state)

    def cost(self, problem, state):
        return self.cost.evaluate(problem, state)

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return self.__str__()

class ActionGenerator:
    def __init__(self, name, entities, params, preconditions,
                 conflictingPreconditions, effects, cost, paramExpressions: List[ParameterNode]):
        self.name = name
        self.entities = entities
        self.params = params # List of parameter names
        self.preconditions = preconditions
        self.conflictingPreconditions = conflictingPreconditions
        self.effects = effects
        self.cost = cost
        self.paramExpressions = paramExpressions # List of fitting expressions

    def generate_action(self):
        # Create an Action instance using the parameter values
        newParams = [copy(par) for par in self.paramExpressions]
        preconditions = self.preconditions.copies(newParams)
        conflictingPreconditions = self.conflictingPreconditions.copies(newParams)
        effects = self.effects.copies(newParams)
        cost = self.cost.copies(newParams)
        action = Action(
            name=self.name,
            preconditions=preconditions,
            conflictingPreconditions=conflictingPreconditions,
            effects=effects,
            cost=cost
        )
        return action

    """Currently not needed
    def resetParams(self):
        for param in self.paramExpressions:
            param.updateValue(None)
    """

class ActionProducer:
    def __init__(self, actionGenerators: List[ActionGenerator]):
        self.actionGenerators = actionGenerators  # List of ActionGenerators

    def produce_actions(self, problem, state, entityId, entityType):
        allActions = []
        for actionGenerator in self.actionGenerators:
            if actionGenerator.entities[0] == entityType:
                # Generate all valid actions for the given entity_id
                actions = []
                # Initialize parameter values with the fixed entity parameter (id)
                actionGenerator.paramExpressions[0].updateParam(entityId)
                if self.evaluate_partial_preconditions(actionGenerator, problem, state):
                    # Start recursive parameter assignment
                    self.assign_parameters_recursive(actionGenerator, problem, state, 1, actions)
                allActions.extend(actions)
                #actionGenerator.resetParams()
        return allActions

    def assign_parameters_recursive(self, actionGenerator: ActionGenerator,
                                    problem: CARRIProblem, state: CARRIState,
                                    paramIndex: int, actions: List[Action]):
        if paramIndex >= len(actionGenerator.params):
            # All parameters are assigned, create and validate action
            action = actionGenerator.generate_action()
            """If action was created after validating all parameters
            in evaluate_partial_preconditions, no such need for the if statement.
            if action.validate(problem, state):"""
            actions.append(action)
            return

        # Get the next parameter to assign
        paramName = actionGenerator.params[paramIndex]
        paramEntityIndex = actionGenerator.entities[paramIndex]

        # Get possible values for this parameter
        possible_values = problem.get_entity_ids(state, paramEntityIndex)

        # Filter possible values based on preconditions involving parameters assigned so far
        filtered_values = self.filter_parameter_values(actionGenerator, problem, state,
                                                       paramIndex, possible_values)

        parameterNode = actionGenerator.paramExpressions[paramIndex]
        # For each possible value, proceed to assign the next parameter
        for value in filtered_values:
            # Update the ParameterNode
            parameterNode.updateParam(value)

            # Recurse to assign the next parameter
            self.assign_parameters_recursive(actionGenerator, problem, state, paramIndex + 1, actions)

        # Clean up parameter values (backtrack)
        parameterNode.updateParam(None)

    def filter_parameter_values(self, actionGenerator: ActionGenerator,
                                problem: CARRIProblem, state: CARRIState,
                                paramIndex: int, possibleValues: Iterable):
        filtered_values = []
        parameterNode = actionGenerator.paramExpressions[paramIndex]

        for value in possibleValues:
            # Set current parameter value
            parameterNode.updateParam(value)

            # Evaluate preconditions involving parameters assigned so far
            if self.evaluate_partial_preconditions(actionGenerator, problem, state):
                filtered_values.append(value)

        return filtered_values

    def evaluate_partial_preconditions(self, actionGenerator, problem, state):

        # Evaluate preconditions
        all_preconditions_met = True
        for precondition in actionGenerator.preconditions + actionGenerator.conflictingPreconditions:
            if precondition.applicable():
                if not precondition.evaluate(problem, state):
                    all_preconditions_met = False
                    break
        # Clean up parameter values in ParameterNodes (if necessary)
        # (Not strictly necessary here, since we'll overwrite them in the next call)
        return all_preconditions_met

