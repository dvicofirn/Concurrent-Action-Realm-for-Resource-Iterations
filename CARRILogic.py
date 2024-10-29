from CARRIDomain import CARRIProblem, CARRIState, CARRISimulator

class ExpressionNode:
    def evaluate(self, problem, state):
        raise NotImplementedError("Must be implemented by subclasses")

class ConstNode(ExpressionNode):
    def __init__(self, const):
        self.const = const
    def evaluate(self, problem, state):
        return self.const

class ParameterNode(ExpressionNode):
    def updateVariable(self, value):
        self.value = value
    def evaluate(self, problem, state):
        return self.value

class ValueIndexNode(ExpressionNode):
    def __init__(self, variableName: str, index: int):
        self.variableName = variableName
        self.index = index
    def evaluate(self, problem: CARRIProblem, state: CARRIState):
        return problem.get_value(state, self.variableName, self.index)

class ValueNode(ExpressionNode):
    def __init__(self, variableName: str, expression: ExpressionNode):
        self.variableName = variableName
        self.expression = expression

    def evaluate(self, problem: CARRIProblem, state: CARRIState):
        return problem.get_value(state, self.variableName, self.expression.evaluate(problem, state))

class OperatorNode(ExpressionNode):
    def __init__(self, operator, *operands):
        self.operator = operator  # A callable operator (e.g., operator.add)
        self.operands = operands  # List of operand nodes (can be ValueNode or OperatorNode)

    def evaluate(self, problem, state):
        evaluated_operands = [operand.evaluate(problem, state) for operand in self.operands]
        return self.operator(*evaluated_operands)

class Update:
    def apply(self, problem: CARRIProblem, state: CARRIState):
        raise NotImplementedError("Must be implemented by subclasses")

class ConstUpdate(Update):
    def __init__(self, variableName: str, index: int, const: int):
        self.variableName = variableName
        self.const = const
        self.index = index

    def apply(self, problem: CARRIProblem, state: CARRIState):
        problem.set_variable(state, self.variableName, self.index, self.const)

class ExpressionIndexUpdate(Update):
    def __init__(self, variableName: str, index: int, expression: ExpressionNode):
        self.variableName = variableName
        self.index = index
        self.expression = expression

    def apply(self, problem: CARRIProblem, state: CARRIState):
        problem.set_variable(state, self.variableName, self.index, self.expression.evaluate(problem, state))

class ExpressionUpdate(Update):
    def __init__(self, variableName: str, expressionIndex: ExpressionNode, expressionValue: ExpressionNode):
        self.variableName = variableName
        self.expressionIndex = expressionIndex
        self.expressionValue = expressionValue

    def apply(self, problem: CARRIProblem, state: CARRIState):
        problem.set_variable(state, self.variableName,
                             self.expressionIndex.evaluate(problem, state),
                             self.expressionValue.evaluate(problem, state))

class CaseUpdate(Update):
    def __init__(self, condition: ExpressionNode, updates, elseUpdates=None):
        self.condition = condition
        self.updates = updates
        self.elseUpdates = elseUpdates if elseUpdates else []

    def apply(self, problem: CARRIProblem, state: CARRIState):
        if self.condition.evaluate(problem, state):
            for update in self.updates:
                update.apply(problem, state)
        else:
            for update in self.elseUpdates:
                update.apply(problem, state)

class AllUpdate(Update):
    def __init__(self, variableName: str, parameter: ParameterNode, updates, condition: ExpressionNode = None):
        self.variableName = variableName
        self.parameter = parameter
        self.updates = updates
        self.condition = condition  # Optional condition to filter items

    def apply(self, problem: CARRIProblem, state: CARRIState):
        if self.condition is None:
            for p in problem.get_variable(state, self.variableName):
                self.parameter.updateVariable(p)
                for update in self.updates:
                    update.apply(problem, state)
        else:
            for p in problem.get_variable(state, self.variableName):
                self.parameter.updateVariable(p)
                if self.condition is None or self.condition.evaluate(problem, state):
                    for update in self.updates:
                        update.apply(problem, state)

class Action:
    def __init__(self, name, entity, preconditions, conflictingPreconditions, effects, cost=0):
        #self.params = params
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

