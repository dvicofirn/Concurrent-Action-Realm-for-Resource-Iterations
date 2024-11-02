from CARRIRealm import CARRIProblem, CARRIState, CARRISimulator

class ExpressionNode:
    def apply(self, params):
        pass
    def evaluate(self, problem, state):
        raise NotImplementedError("Must be implemented by subclasses")

class ConstNode(ExpressionNode):
    def __init__(self, const):
        self.const = const
    def apply(self, params):
        pass
    def evaluate(self, problem, state):
        return self.const
class ValueNode(ExpressionNode):
    def __init__(self, variableName):
        self.variableName = variableName
    def apply(self, params):
        self.index = params
    def evaluate(self, problem: CARRIProblem, state: CARRIState):
        # Retrieve variable value from problem or state if it's a variable name
        return problem.get_value(state, self.variableName, self.index)

class OperatorNodeUnUsed(ExpressionNode):
    def __init__(self, operator, matches, *operands):
        self.operator = operator  # A callable operator (e.g., operator.add)
        self.operands = operands  # List of operand nodes (can be ValueNode or OperatorNode)
        self.matches = matches # List of matching

    def apply(self, params):
        for opIndex, match in enumerate(self.matches):
            lenMatch = len(match)
            if lenMatch:
                operandParams = [0 for i in range(lenMatch)]
                for index in range(lenMatch):
                    operandParams[index] = params[match[index]]
                self.operands[opIndex].apply(operandParams)

    def evaluate(self, problem, state):
        evaluated_operands = [operand.evaluate(problem, state) for operand in self.operands]
        return self.operator(*evaluated_operands)

class Update:
    def apply(self, problem: CARRIProblem, state: CARRIState, *params):
        raise NotImplementedError("Must be implemented by subclasses")

class ConstUpdate(Update):
    def __init__(self, variableName: str, const: int):
        self.variableName = variableName
        self.const = const

    def apply(self, problem: CARRIProblem, state: CARRIState, *params):
        problem.set_value(state, self.variableName, params[0], self.const)

class ExpressionUpdate(Update):
    def __init__(self, variableName: str, expression: ExpressionNode):
        self.variableName = variableName
        self.expression = expression

    def apply(self, problem: CARRIProblem, state: CARRIState, *params):
        self.expression.apply(params)
        problem.set_value(state, self.variableName, params[0], self.expression.evaluate(problem, state))

class CaseUpdate(Update):
    def __init__(self, condition: OperatorNode, updates, elseUpdates=None):
        self.condition = condition
        self.updates = updates
        self.elseUpdates = elseUpdates if elseUpdates else []

    def apply(self, problem: CARRIProblem, state: CARRIState, *params):
        self.condition.apply(params)
        if self.condition.evaluate(problem, state):
            for update in self.updates:
                update.apply(problem, state, *params)
        else:
            for update in self.elseUpdates:
                update.apply(problem, state, *params)

class AllUpdate(Update):
    def __init__(self, variableName: str, updates, condition=None):
        self.variableName = variableName
        self.updates = updates
        self.condition = condition if condition else None

    def apply(self, problem: CARRIProblem, state: CARRIState, *params):
        for parameter in problem.get_variable(state, self.variableName):
            params = (parameter,) + params
            if self.condition is not None:
                self.condition.apply(params)
                if self.condition.evaluate(problem, state):
                    for update in self.updates:
                        update.apply(problem, state, *params)

class Action:
    def __init__(self, name, entity, preconditions, conflictingPreconditions, effects, cost=0):
        self.name = name
        self.entity = entity
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

