from typing import List, Iterable
from CARRI.problem import Problem
from CARRI.state import State
from CARRI.expression import ExpressionNode, ValueParameterNode, Update, CostExpression


class Step:
    """Represents a step in the simulation, consisting of effects to apply."""
    def __init__(self, effects: List[Update]):
        self.effects = effects  # List of Effect objects

    def __repr__(self):
        return str(self.effects)

    def __str__(self):
        return "Step effects: " + str(self.effects)

    def apply(self, problem, state):
        for effect in self.effects:
            effect.apply(problem, state)


class EnvStep(Step):
    """Represents an environmental step with a name, effects, and cost."""
    def __init__(self, name: str, effects: List[Update], cost: CostExpression):
        super().__init__(effects)
        self.name = name
        self.cost = cost

    def __str__(self):
        return self.name + ":\nEffects: " + str(self.effects) + "\n" + str(self.cost)

    def get_cost(self, problem, state):
        return self.cost.evaluate(problem, state)


class Action(EnvStep):
    """Represents an action that can be performed, with preconditions and effects."""
    def __init__(self, name: str, preconditions: List[ExpressionNode],
                 conflictingPreconditions: List[ExpressionNode],
                 effects: List[Update], cost: CostExpression, params: List[ValueParameterNode], baseAction):
        super().__init__(name, effects, cost)
        self.preconditions = preconditions  # List of precondition expressions
        self.conflictingPreconditions = conflictingPreconditions  # List of conflicting precondition expressions
        self.params = params  # List of parameter nodes
        self.baseAction = baseAction

    def validate(self, problem, state):
        """Check if action's preconditions and conflicting preconditions are satisfied in the current state."""
        return (all(precondition.evaluate(problem, state) for precondition in self.preconditions)
                and all(precondition.evaluate(problem, state) for precondition in self.conflictingPreconditions))

    def reValidate(self, problem, state):
        """Re-validate the conflicting preconditions in the current state."""
        return all(precondition.evaluate(problem, state) for precondition in self.conflictingPreconditions)

    def __str__(self):
        return str(self.name)


class ActionGenerator:
    """Generates actions based on parameters, preconditions, and effects."""
    def __init__(self, name, entities, params, preconditions,
                 conflictingPreconditions, effects, cost, paramExpressions: List[ValueParameterNode],
                 baseActionName):
        self.name = name
        self.entities = entities
        self.params = params  # List of parameter names
        self.preconditions = preconditions
        self.conflictingPreconditions = conflictingPreconditions
        self.effects = effects
        self.cost = cost
        self.paramExpressions = paramExpressions  # List of parameter expressions
        self.applicablePrecsRanges = []
        self.applicableConfPrecsRanges = []
        self.baseActionName = baseActionName

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return ("Action: " + self.name + "\nEntities: " + str(self.entities)
                + "\nParams: " + str(self.params) + "\nPreconditions: " + str(self.preconditions)
                + "\nConflictingPreconditions: " + str(self.conflictingPreconditions)
                + "\nEffects: " + str(self.effects) + "\nCost: " + str(self.cost)
                + "\nParamExpressions: " + str(self.paramExpressions)
                + "\nPrecsParamApplicableCount: " + str(self.applicablePrecsRanges)
                + "\nConflictingPreconditions: " + str(self.applicableConfPrecsRanges))

    def generate_action(self):
        """Generates an Action instance using the current parameter values."""
        # Create an Action instance using the parameter values
        newParams = [par.__copy__() for par in self.paramExpressions]
        preconditions = [pre.copies(newParams) for pre in self.preconditions]
        conflictingPreconditions = [conf.copies(newParams) for conf in self.conflictingPreconditions]
        effects = [eff.copies(newParams) for eff in self.effects]
        cost = self.cost.copies(newParams)
        action = Action(
            name=self.name,
            preconditions=preconditions,
            conflictingPreconditions=conflictingPreconditions,
            effects=effects,
            cost=cost,
            params=newParams,
            baseAction=self.baseActionName
        )
        return action

    def resetParams(self):
        """Reset all parameter expressions to None."""
        for param in self.paramExpressions:
            param.updateParam(None)

    def reArrangePreconditions(self):
        """
        Rearranges preconditions to optimize action production.

        Motivation: Action production involves parameter elimination process:
        inserting entity parameters one at a time and checking all preconditions
        applicable to the currently assigned parameters. To make this process
        more efficient, this function reorders the preconditions based on the
        necessity per index of the last parameter inserted. It also provides
        predefined ranges of precondition indexes to validate per index of the
        last parameter inserted.
        """
        applicablePrecsLens = [0]
        applicableConfPrecsLens = [0]
        newOrderPrecs = []
        newOrderConfPrecs = []
        for index, expression in enumerate(self.paramExpressions):
            expression.updateParam(0)
            notYet = []
            for precondition in self.preconditions:
                if precondition.applicable():
                    newOrderPrecs.append(precondition)
                else:
                    notYet.append(precondition)
            applicablePrecsLens.append(len(newOrderPrecs))
            self.preconditions = notYet
        self.resetParams()

        for index, expression in enumerate(self.paramExpressions):
            expression.updateParam(0)
            notYet = []
            for precondition in self.conflictingPreconditions:
                if precondition.applicable():
                    newOrderConfPrecs.append(precondition)
                else:
                    notYet.append(precondition)
            applicableConfPrecsLens.append(len(newOrderConfPrecs))
            self.conflictingPreconditions = notYet
        self.resetParams()

        self.applicablePrecsRanges = [range(applicablePrecsLens[i - 1], applicablePrecsLens[i])
                                      for i in range(1, len(applicablePrecsLens))]
        self.applicableConfPrecsRanges = [range(applicableConfPrecsLens[i - 1], applicableConfPrecsLens[i])
                                          for i in range(1, len(applicableConfPrecsLens))]
        self.preconditions = newOrderPrecs
        self.conflictingPreconditions = newOrderConfPrecs


class ActionStringRepresentor:
    """Provides string representations of actions based on their generators."""
    def __init__(self, actionGenerators: List[ActionGenerator]):
        self.actionGenerators = {actionGenerator.name: actionGenerator for actionGenerator in actionGenerators}

    def represent(self, action: Action) -> str:
        """Return a string representation of the given action."""
        name = action.name
        generator = self.actionGenerators[name]
        return f"Action {name} {str([parName + ': ' + str(param.value) + ', ' for parName, param in zip(generator.params, action.params)])}"


class ActionProducer:
    """Produces actions by generating and validating possible parameter combinations."""
    def __init__(self, actionGenerators: List[ActionGenerator]):
        self.actionGenerators = actionGenerators  # List of ActionGenerators

    def produce_actions(self, problem, state, entityId, entityType):
        """Produce all valid actions for a given entity in the current state."""
        allActions = []

        for actionGenerator in self.actionGenerators:
            if actionGenerator.entities[0] != entityType:
                continue  # Skip action generators that don't match the entity type

            # Initialize parameter values with the fixed entity parameter (id)
            actionGenerator.paramExpressions[0].updateParam(entityId)

            # Evaluate initial preconditions
            if not self.evaluate_partial_preconditions(actionGenerator, problem, state, 0):
                continue

            actions = []
            self.assign_parameters_recursive(actionGenerator, problem, state, 1, actions)
            allActions.extend(actions)

        return allActions

    def assign_parameters_recursive(self, actionGenerator: ActionGenerator,
                                    problem: Problem, state: State,
                                    paramIndex: int, actions: List[Action]):
        """Recursively assign parameters starting from paramIndex, collecting valid actions."""
        if paramIndex >= len(actionGenerator.params):
            # All parameters are assigned, create and validate action
            action = actionGenerator.generate_action()
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
                                problem: Problem, state: State,
                                paramIndex: int, possibleValues: Iterable):
        """Filter possible parameter values based on preconditions up to paramIndex."""
        filtered_values = []
        parameterNode = actionGenerator.paramExpressions[paramIndex]

        for value in possibleValues:
            # Set current parameter value
            parameterNode.updateParam(value)

            # Evaluate preconditions involving parameters assigned so far
            if self.evaluate_partial_preconditions(actionGenerator, problem, state, paramIndex):
                filtered_values.append(value)

        return filtered_values

    def evaluate_partial_preconditions(self, actionGenerator, problem, state, paramIndex: int):
        """Evaluate preconditions applicable for parameters up to paramIndex."""
        # Evaluate applicable preconditions. Searches in predetermined ranges.
        for index in actionGenerator.applicablePrecsRanges[paramIndex]:
            if not actionGenerator.preconditions[index].evaluate(problem, state):
                return False
        # Evaluate applicable conflicting preconditions.
        for index in actionGenerator.applicableConfPrecsRanges[paramIndex]:
            if not actionGenerator.conflictingPreconditions[index].evaluate(problem, state):
                return False
        return True
