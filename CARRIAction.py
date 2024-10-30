from itertools import product

class Action:
    def __init__(self, name, entityType, entityPar, params ,preconditions, conflictingPreconditions, effects, cost):
        self.name = name
        self.entityType = entityType
        self.entityPar = entityPar
        self.params = params
        self.preconditions = preconditions  # List of Condition objects
        self.conflictingPreconditions = conflictingPreconditions
        self.effects = effects  # List of Effect objects
        self.cost = cost

    def validate(self, problem, state):
        return (all(precondition.evaluate(problem, state) for precondition in self.preconditions)
                and all(precondition.evaluate(problem, state) for precondition in self.conflictingPreconditions))

    def reValidate(self, problem, state):
        return all(precondition.evaluate(problem, state) for precondition in self.conflictingPreconditions)

    def apply(self, state):
        for effect in self.effects:
            effect.apply(state)

    def __str__(self):
        return str(self.name, self.params)

    def __repr__(self):
        return self.__str__()

class ActionGenerator:
    def __init__(self, name, entityType, entityPar, params, preconditions,
                 conflictingPreconditions, effects, cost, parameters, paramExpressions):
        self.name = name
        self.entityType = entityType
        self.entityPar = entityPar  # The main entity parameter (e.g., 'id')
        self.params = params        # List of parameter names
        self.preconditions = preconditions
        self.conflictingPreconditions = conflictingPreconditions
        self.effects = effects
        self.cost = cost
        self.parameters = parameters # List of parameter names
        self.paramExpressions = paramExpressions # List of fitting expressions

    def generate_action(self, parameters):
        # Create an Action instance using the parameter values
        newParams = [parameters.copy() for parameters in parameters]
        preconditions = self.preconditions.copies(newParams)
        conflictingPreconditions = self.conflictingPreconditions.copies(newParams)
        effects = self.effects.copies(newParams)
        cost = self.cost.copies(newParams)
        action = Action(
            name=self.name,
            entityType=self.entityType,
            entityPar=self.entityPar,
            params=tuple(self.parameters.keys()),
            preconditions=preconditions,
            conflictingPreconditions=conflictingPreconditions,
            effects=effects,
            cost=cost
        )
        return action

class ActionProducer:
    def __init__(self, actionGenerators):
        self.actionGenerators = actionGenerators  # List of ActionGenerators

    def produce_actions(self, problem, state, entityId, entityType):
        actions = []
        for action_generator in self.actionGenerators:
            if action_generator.entityType == entityType:
                # Generate all valid actions for the given entity_id
                valid_actions = self.generate_valid_actions(action_generator, problem, state, entityId)
                actions.extend(valid_actions)
        return actions

    def generate_valid_actions(self, actionGenerator, problem, state, entityId):
        actions = []
        # Initialize parameter values with the fixed entity parameter
        entityParName = actionGenerator.entityPar
        parameterValues = {entityParName: entityId}

        # Generate parameter domains based on preconditions
        parameterDomains = self.get_parameter_domains(actionGenerator, problem, state)

        # Get other parameter names
        parameter_names = actionGenerator[1:]

        # Generate all combinations of parameter values
        domain_lists = [parameterDomains[p] for p in parameter_names]

        for values in product(*domain_lists):
            params = parameterValues.copy()
            params.update(dict(zip(parameter_names, values)))
            # Set parameter values in ParameterNodes
            for paramName, value in params.items():
                index = actionGenerator.parameters.index(paramName)
                actionGenerator.paramExpressions[index].updateVariable(value)
            action = actionGenerator.generate_action()
            if action.validate(problem, state):
                actions.append(action)

        return actions

    def get_parameter_domains(self, actionGenerator, problem, state):
        parameter_domains = {}
        # For each parameter, derive possible values based on preconditions
        for param in actionGenerator.params[1:]:
            # Derive possible values for 'param' based on preconditions
            possible_values = self.derive_possible_values(param, actionGenerator, problem, state)
            parameter_domains[param] = possible_values
        return parameter_domains

    def derive_possible_values(self, param, actionGenerator, problem, state):
        # Get parameter type if available
        param_type = actionGenerator.param_types.get(param)
        if param_type:
            possible_values = problem.get_entities_of_type(param_type)
        else:
            possible_values = problem.get_all_ids()
        filtered_values = []
        index = actionGenerator.parameters.index(param)
        parameter_node = actionGenerator.paramExpressions[index]
        for value in possible_values:
            # Set parameter value
            parameter_node.updateVariable(value)
            # Evaluate preconditions
            if all(precondition.evaluate(problem, state) for precondition in actionGenerator.preconditions + actionGenerator.conflictingPreconditions):
                filtered_values.append(value)
        return filtered_values


    # Todo: check if needed
    def check_precondition(self, precondition, param, value, parameter_values, problem, state):
        # Update parameter_values with the new value
        parameter_values[param] = value
        result = precondition.evaluate(problem, state, parameter_values)
        return result

    # You may need to adjust the evaluate methods to accept parameter_values
