from CARRIRealm import CARRIProblem, CARRIState
from typing import List
import operator

operatorStringMap = {
    operator.add: '+',
    operator.sub: '-',
    operator.mul: '*',
    operator.truediv: '/',
    operator.eq: '=',
    operator.ne: '!=',
    operator.gt: '>',
    operator.lt: '<',
    operator.ge: '>=',
    operator.le: '<=',
    operator.and_: 'and',
    operator.or_: 'or',
    operator.not_: 'not',
    operator.contains: '?',
    operator.getitem: '@'
}

class ExpressionNode:
    def evaluate(self, problem, state):
        raise NotImplementedError("Must be implemented by subclasses")
    def copies(self, params: List):
        raise NotImplementedError("Must be implemented by subclasses")
    def applicable(self) -> bool:
        return NotImplemented("Must be implemented by subclasses")
    def __repr__(self):
        return self.__str__()

class ConstNode(ExpressionNode):
    def __init__(self, const):
        self.const = const
    def __str__(self):
        return str(self.const) + " "

    def evaluate(self, problem, state):
        return self.const

    def copies(self, params: List):
        """
        No real benefit to create new instances of this class.
        """
        return self

    def applicable(self) -> bool:
        return True

class ParameterNode(ExpressionNode):
    def __init__(self, index, value=None):
        self.index = index
        self.value = value
    def __str__(self):
        return "par: "+ str(self.value) + " at " +str(self.index) + " "
    def __copy__(self):
        return ParameterNode(self.index, self.value)

    def updateValue(self, value):
        self.value = value
    def evaluate(self, problem, state):
        return self.value

    def copies(self, params: List):
        """
        Returns the ParameterNode with the same index.
        If it's an action's parameter, returning a new object.
        If it's an All's parameter, returning the same object.
        """
        return params[self.index]

    def applicable(self) -> bool:
        return self.value is not None

class ValueIndexNode(ExpressionNode):
    def __init__(self, variableName: str, index: int):
        self.variableName = variableName
        self.index = index
    def __str__(self):
        return "var: "+ str(self.variableName) + " at " +str(self.index) + " "

    def evaluate(self, problem: CARRIProblem, state: CARRIState):
        return problem.get_value(state, self.variableName, self.index)

    def copies(self, params: List):
        """
        No real benefit to create new instances of this class.
        """
        return self

    def applicable(self) -> bool:
        return True

class ValueNode(ExpressionNode):
    def __init__(self, variableName: str, expression: ExpressionNode):
        self.variableName = variableName
        self.expression = expression
    def __str__(self):
        return "var: "+ str(self.variableName) + " at (" +str(self.expression) + ") "

    def evaluate(self, problem: CARRIProblem, state: CARRIState):
        return problem.get_value(state, self.variableName, self.expression.evaluate(problem, state))

    def copies(self, params: List):
        """
        Copies object's expression
        """
        return ValueNode(self.variableName, self.expression.copies(params))

    def applicable(self) -> bool:
        return self.expression.applicable()

class ExistingParameterNode(ExpressionNode):
    def __init__(self, entityIndex: int, expression: ExpressionNode):
        self.entityIndex = entityIndex
        self.expression = expression
    def __str__(self):
        return "exists: "+ str(self.entityIndex) + " at (" +str(self.expression) + ") "
    def evaluate(self, problem: CARRIProblem, state: CARRIState):
        return self.expression.evaluate() in problem.get_entity_ids(state, self.entityIndex)

    def copies(self, params: List):
        """
        Copies object's expression
        """
        return ExistingParameterNode(self.entityIndex, self.expression.copies(params))

    def applicable(self) -> bool:
        return self.expression.applicable()

class OperatorNode(ExpressionNode):
    def __init__(self, operator, *operands):
        self.operator = operator  # A callable operator (e.g., operator.add)
        self.operands = operands  # List of operand nodes of ExpressionNode type
    def __str__(self):
        return " "+ operatorStringMap[self.operator] + str([expression for expression in self.operands]) + " "

    def evaluate(self, problem, state):
        evaluated_operands = [operand.evaluate(problem, state) for operand in self.operands]
        return self.operator(*evaluated_operands)

    def copies(self, params: List):
        """
        Copies object's expressions
        """
        return OperatorNode(self.operator, *[expression.copies(params) for expression in self.operands])

    def applicable(self) -> bool:
        return all(expression.applicable() for expression in self.operands)

class Update:
    def apply(self, problem: CARRIProblem, state: CARRIState):
        raise NotImplementedError("Must be implemented by subclasses")

    def copies(self, params: List):
        raise NotImplementedError("Must be implemented by subclasses")

class ConstUpdate(Update):
    def __init__(self, variableName: str, index: int, const: int):
        self.variableName = variableName
        self.const = const
        self.index = index

    def apply(self, problem: CARRIProblem, state: CARRIState):
        problem.set_variable(state, self.variableName, self.index, self.const)

    def copies(self, params: List):
        """
        No real benefit to create new instances of this class.
        """
        return self

class ExpressionIndexUpdate(Update):
    def __init__(self, variableName: str, index: int, expression: ExpressionNode):
        self.variableName = variableName
        self.index = index
        self.expression = expression

    def apply(self, problem: CARRIProblem, state: CARRIState):
        problem.set_variable(state, self.variableName, self.index, self.expression.evaluate(problem, state))

    def copies(self, params: List):
        """
        Copies object's expression
        """
        return ExpressionIndexUpdate(self.variableName, self.index, self.expression.copies(params))

class ExpressionRemoveUpdate(Update):
    def __init__(self, entityIndex: int, expression: ExpressionNode):
        self.entityIndex = entityIndex
        self.expression = expression

    def apply(self, problem: CARRIProblem, state: CARRIState):
        problem.remove_entity(state, self.entityIndex, self.expression.evaluate(problem, state))

    def copies(self, params: List):
        """
        Copies object's expression
        """
        return ExpressionRemoveUpdate(self.entityIndex, self.expression.copies(params))

class ExpressionAddUpdate(Update):
    def __init__(self, entityIndex: int, *expressions: ExpressionNode):
        self.entityIndex = entityIndex
        self.expressions = expressions

    def apply(self, problem: CARRIProblem, state: CARRIState):
        problem.add_entity(state, self.entityIndex,
                           *[expression.evaluate(problem, state) for expression in self.expressions])

    def copies(self, params: List):
        """
        Copies object's expressions
        """
        return ExpressionAddUpdate(self.entityIndex,
                                   *[expression.copies(params) for expression in self.expressions])

class ExpressionReplaceUpdate(Update):
    def __init__(self, entityIndex: int, expressionId: ExpressionNode, *expressions: ExpressionNode):
        self.entityIndex = entityIndex
        self.expressionId = expressionId
        self.expressions = expressions

    def apply(self, problem: CARRIProblem, state: CARRIState):
        problem.replace_entity(state, self.entityIndex,
                               self.expressionId.evaluate(problem, state),
                               *[expr.evaluate(problem, state) for expr in self.expressions])

    def copies(self, params: List):
        """
        Copies object's expressions
        """
        return ExpressionAddUpdate(self.entityIndex, self.expressionId.copies(params),
                                   *[expression.copies(params) for expression in self.expressions])


class ExpressionUpdate(Update):
    def __init__(self, variableName: str, expressionIndex: ExpressionNode, expressionValue: ExpressionNode):
        self.variableName = variableName
        self.expressionIndex = expressionIndex
        self.expressionValue = expressionValue

    def apply(self, problem: CARRIProblem, state: CARRIState):
        problem.set_variable(state, self.variableName,
                             self.expressionIndex.evaluate(problem, state),
                             self.expressionValue.evaluate(problem, state))

    def copies(self, params: List):
        """
        Copies object's expressions
        """
        return ExpressionUpdate(self.variableName,
                                self.expressionIndex.copies(params),
                                self.expressionValue.copies(params))

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

    def copies(self, params: List):
        """
        Copies object's expressions
        """
        return CaseUpdate(self.condition.copies(params),
                          [expression.copies(params) for expression in self.updates],
                          [expression.copies(params) for expression in self.elseUpdates])


class AllUpdate(Update):
    def __init__(self, entityIndex: int, parameter: ParameterNode, updates, condition: ExpressionNode = None):
        self.entityIndex = entityIndex
        # TODO: validate parameter's index is correct
        # Must have the id of len(Action's param) + position of nesting (starting at 0).
        self.parameter = parameter
        self.updates = updates
        self.condition = condition  # Optional condition to filter items

    def apply(self, problem: CARRIProblem, state: CARRIState):
        if self.condition is None:
            for entity in problem.get_entity_ids(state, self.entityIndex):
                self.parameter.updateValue(entity)
                for update in self.updates:
                    update.apply(problem, state)
        else:
            for entity in problem.get_entity_ids(state, self.entityIndex):
                self.parameter.updateValue(entity)
                if self.condition.evaluate(problem, state):
                    for update in self.updates:
                        update.apply(problem, state)

    def copies(self, params: List):
        """
        Copies object's expressions, makes sure uses the same AllUpdate's parameter
        """
        # Using the same parameter for all expressions and updates in block.
        params = params.copy()
        params.append(self.parameter)
        return AllUpdate(self.entityIndex, self.parameter,
                         [expression.copies(params) for expression in self.updates],
                         self.condition.copies(params) if self.condition else None)
