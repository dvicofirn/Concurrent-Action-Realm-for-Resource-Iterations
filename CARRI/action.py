from typing import List, Iterable
from CARRI.problem import Problem
from CARRI.state import State
from CARRI.expression import ExpressionNode, ValueParameterNode, Update, CostExpression, OperatorNode
import operator  # Fixing the 'operator' reference issue

class Step:
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
    def __init__(self, name: str, effects: List[Update], cost: CostExpression):
        super().__init__(effects)
        self.name = name
        self.cost = cost

    def __str__(self):
        return self.name + ":\nEffects: " + str(self.effects) + "\n" + str(self.cost)

    def get_cost(self, problem, state):
        return self.cost.evaluate(problem, state)

class Action(EnvStep):
    def __init__(self, name: str, preconditions: List[ExpressionNode],
                 conflictingPreconditions: List[ExpressionNode],
                 effects: List[Update], cost: CostExpression, params: List[ValueParameterNode], baseAction):
        super().__init__(name, effects, cost)
        self.preconditions = preconditions  # List of Condition objects
        self.conflictingPreconditions = conflictingPreconditions
        self.params = params  # Currently not implemented
        self.baseAction = baseAction

    def validate(self, problem, state):
        return (all(precondition.evaluate(problem, state) for precondition in self.preconditions)
                and all(precondition.evaluate(problem, state) for precondition in self.conflictingPreconditions))

    def reValidate(self, problem, state):
        return all(precondition.evaluate(problem, state) for precondition in self.conflictingPreconditions)

    def __str__(self):
        return str(self.name)

class ActionGenerator:
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
        self.paramExpressions = paramExpressions  # List of fitting expressions
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
        for param in self.paramExpressions:
            param.updateParam(None)

    def reArrangePreconditions(self):
        """
        Motivation: Action production involves parameter elimination process:
        Inserting entity parameter at a time and checking all preconditions
        which are applicable on currently inserted set of parameters.
        To support this method, and to make it more efficient, the function
        reorders the preconditions by necessity per index of last parameter
        inserted. This function also provide predefined ranges of precondition
        indexes to validate per index of last parameter inserted.
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
    def __init__(self, actionGenerators: List[ActionGenerator]):
        self.actionGenerators = {actionGenerator.name: actionGenerator for actionGenerator in actionGenerators}

    def represent(self, action: Action) -> str:
        name = action.name
        generator = self.actionGenerators[name]
        return f"Action {name} {str([parName + ': ' + str(param.value) + ', ' for parName, param in zip(generator.params, action.params)])}"

class ActionProducer:
    def __init__(self, actionGenerators: List[ActionGenerator]):
        self.actionGenerators = actionGenerators  # List of ActionGenerators

    def produce_actions(self, problem, state, entityId, entityType):
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
        parameterNode = actionGenerator.paramExpressions[paramIndex]
        paramEntityIndex = actionGenerator.entities[paramIndex]

        # Get assigned parameters
        assigned_params = {index: actionGenerator.paramExpressions[index].value
                           for index in range(paramIndex)}

        # Extract constraints for current parameter
        constraints = self.extract_constraints(actionGenerator.preconditions, paramIndex, assigned_params)

        # Compute possible values based on constraints
        possibleValues = self.apply_constraints(constraints, problem, state, paramIndex, assigned_params,
                                                paramEntityIndex, actionGenerator)

        filtered_values = []
        for value in possibleValues:
            parameterNode.updateParam(value)
            if self.evaluate_partial_preconditions(actionGenerator, problem, state, paramIndex):
                filtered_values.append(value)
        parameterNode.updateParam(None)
        return filtered_values

    def extract_constraints(self, preconditions, current_param_index, assigned_params):
        constraints = []
        for prec in preconditions:
            involved_params = prec.get_parameters()
            if current_param_index in involved_params and all(
                    idx in assigned_params for idx in involved_params if idx != current_param_index):
                constraints.append(prec)
        return constraints

    def apply_constraints(self, constraints, problem, state, current_param_index, assigned_params, paramEntityIndex,
                          actionGenerator):
        possible_values = set(problem.get_entity_ids(state, paramEntityIndex))
        for constraint in constraints:
            possible_values &= self.compute_possible_values_from_constraint(constraint, problem, state,
                                                                            current_param_index, assigned_params,
                                                                            actionGenerator)
            if not possible_values:
                break
        return possible_values

    def compute_possible_values_from_constraint(self, constraint, problem, state, current_param_index, assigned_params,
                                                actionGenerator):
        # For simplicity, handle equality constraints where current_param == some_value
        if isinstance(constraint, OperatorNode) and constraint.operator == operator.eq:
            left, right = constraint.operands
            left_params = left.get_parameters()
            right_params = right.get_parameters()

            if current_param_index in left_params and all(idx in assigned_params for idx in right_params):
                right_value = right.evaluate_with_params(problem, state, assigned_params)
                return self.find_entities_with_value(problem, state, left, current_param_index, right_value,
                                                     actionGenerator, assigned_params)
            elif current_param_index in right_params and all(idx in assigned_params for idx in left_params):
                left_value = left.evaluate_with_params(problem, state, assigned_params)
                return self.find_entities_with_value(problem, state, right, current_param_index, left_value,
                                                     actionGenerator, assigned_params)
        # Handle other constraint types as needed
        return set(problem.get_entity_ids(state, actionGenerator.entities[current_param_index]))

    def find_entities_with_value(self, problem, state, expression, current_param_index, target_value, actionGenerator, assigned_params):
        entity_type = actionGenerator.entities[current_param_index]
        possible_entities = problem.get_entity_ids(state, entity_type)
        matching_entities = []
        for entity_id in possible_entities:
            # Create a new assigned_params dictionary including the current parameter assignment
            new_assigned_params = {**assigned_params, current_param_index: entity_id}
            # Evaluate the expression with the new assigned parameters
            value = expression.evaluate_with_params(problem, state, new_assigned_params)
            if value == target_value:
                matching_entities.append(entity_id)
        return set(matching_entities)

    def evaluate_partial_preconditions(self, actionGenerator, problem, state, paramIndex: int):
        # Evaluate applicable preconditions. Searches in pre-determined ranges.
        for index in actionGenerator.applicablePrecsRanges[paramIndex]:
            if not actionGenerator.preconditions[index].evaluate(problem, state):
                return False
        # Evaluate applicable conflicting preconditions.
        for index in actionGenerator.applicableConfPrecsRanges[paramIndex]:
            if not actionGenerator.conflictingPreconditions[index].evaluate(problem, state):
                return False
        return True
