from typing import List
from CARRI.problem import Problem
from CARRI.state import State
import operator

# Map operator functions to their string representations
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

class Copies:
    """Abstract base class enforcing the implementation of the 'copies' method in subclasses."""
    def copies(self, params: List):
        """Create a copy of the object with given parameters."""
        raise NotImplementedError("Must be implemented by subclasses")

class ExpressionNode(Copies):
    """Abstract base class for expression nodes in the expression tree."""
    def evaluate(self, problem, state):
        """Evaluate the expression in the given problem and state context."""
        raise NotImplementedError("Must be implemented by subclasses")

    def applicable(self) -> bool:
        """Check if the expression is applicable (all required parameters are assigned)."""
        return NotImplemented("Must be implemented by subclasses")

    def __repr__(self):
        return self.__str__()

class ConstNode(ExpressionNode):
    """Represents a constant value in the expression tree."""
    def __init__(self, const):
        """Initialize with a constant value."""
        self.const = const

    def __str__(self):
        return str(self.const) + " "

    def evaluate(self, problem, state):
        """Return the constant value."""
        return self.const

    def copies(self, params: List):
        """
        No real benefit to create new instances of this class.
        """
        return self

    def applicable(self) -> bool:
        """Constants are always applicable."""
        return True

class ParameterNode(ExpressionNode):
    """Abstract class representing a parameter node in the expression tree."""
    def __init__(self, index):
        self.index = index

    def copies(self, params: List):
        """
        Returns the ParameterNode with the same index.
        If it's an action's parameter, returning a new object.
        If it's an All's parameter, returning the same object.
        """
        return params[self.index]

    def __copy__(self):
        return NotImplemented("Must be implemented by subclasses")

    def updateParam(self, newParam):
        """Update the parameter value."""
        raise NotImplementedError("Must be implemented by subclasses")

class ValueParameterNode(ParameterNode):
    """Represents a parameter with a value assigned."""
    def __init__(self, index, value=None):
        """Initialize the ValueParameterNode with index and optional value."""
        super().__init__(index)
        self.value = value

    def __str__(self):
        return "par: " + str(self.value) + " at " + str(self.index) + " "

    def __copy__(self):
        return ValueParameterNode(self.index, self.value)

    def updateParam(self, newParam):
        """Update the parameter's value."""
        self.value = newParam

    def evaluate(self, problem, state):
        """Return the parameter's value."""
        return self.value

    def applicable(self) -> bool:
        """Check if the parameter has a value assigned."""
        return self.value is not None

class NewValParameterNode(ParameterNode):
    """Represents a new value parameter node in the expression tree."""
    def __init__(self, index, value=None):
        """Initialize the NewValParameterNode with index and optional value."""
        super().__init__(index)
        self.value = value

    def __str__(self):
        return "par: " + str(self.value) + " at " + str(self.index) + " "

    def __copy__(self):
        return NewValParameterNode(self.index, self.value)

    def updateParam(self, newParam):
        """Update the parameter's value."""
        self.value = newParam

    def evaluate(self, problem, state):
        """Return the parameter's value."""
        return self.value

    def applicable(self) -> bool:
        """Check if the parameter has a value assigned."""
        return self.value is not None

    def copies(self, params):
        return self

class ValueIndexNode(ExpressionNode):
    """Represents a variable with a fixed index in the expression tree."""
    def __init__(self, variableName: str, index: int):
        self.variableName = variableName
        self.index = index

    def __str__(self):
        return "var: " + str(self.variableName) + " at " + str(self.index) + " "

    def evaluate(self, problem: Problem, state: State):
        """Retrieve the value of the variable at the given index."""
        return problem.get_value(state, self.variableName, self.index)

    def copies(self, params: List):
        """
        No real benefit to create new instances of this class.
        """
        return self

    def applicable(self) -> bool:
        """Always applicable since index is fixed."""
        return True

class ValueNode(ExpressionNode):
    """Represents a variable with an index determined by an expression."""
    def __init__(self, variableName: str, expression: ExpressionNode):
        self.variableName = variableName
        self.expression = expression

    def __str__(self):
        return "var: " + str(self.variableName) + " at (" + str(self.expression) + ") "

    def evaluate(self, problem: Problem, state: State):
        """Retrieve the value of the variable at the index evaluated from the expression."""
        index = self.expression.evaluate(problem, state)
        return problem.get_value(state, self.variableName, index)

    def copies(self, params: List):
        """
        Copies object's expression.
        """
        return ValueNode(self.variableName, self.expression.copies(params))

    def applicable(self) -> bool:
        """Applicable if the index expression is applicable."""
        return self.expression.applicable()

class ExistingExpressionNode(ExpressionNode):
    """Checks if an entity exists based on the evaluated expression."""
    def __init__(self, entityIndex: int, expression: ExpressionNode):
        self.entityIndex = entityIndex
        self.expression = expression

    def __str__(self):
        return "exists: " + str(self.entityIndex) + " at (" + str(self.expression) + ") "

    def evaluate(self, problem: Problem, state: State):
        """Check if the entity exists in the problem's entities."""
        value = self.expression.evaluate(problem, state)
        return value in problem.get_entity_ids(state, self.entityIndex)

    def copies(self, params: List):
        """
        Copies object's expression.
        """
        return ExistingExpressionNode(self.entityIndex, self.expression.copies(params))

    def applicable(self) -> bool:
        """Applicable if the expression is applicable."""
        return self.expression.applicable()

class OperatorNode(ExpressionNode):
    """Represents an operator applied to one or more operands."""
    def __init__(self, operator, *operands):
        self.operator = operator  # A callable operator (e.g., operator.add)
        self.operands = operands  # Tuple of operand nodes of ExpressionNode type

    def __str__(self):
        return " " + operatorStringMap[self.operator] + str([expression for expression in self.operands]) + " "

    def evaluate(self, problem, state):
        """Evaluate the operator with the evaluated operands."""
        evaluated_operands = [operand.evaluate(problem, state) for operand in self.operands]
        return self.operator(*evaluated_operands)

    def copies(self, params: List):
        """
        Copies object's expressions.
        """
        return OperatorNode(self.operator, *[expression.copies(params) for expression in self.operands])

    def applicable(self) -> bool:
        """Applicable if all operands are applicable."""
        return all(expression.applicable() for expression in self.operands)

class Update(Copies):
    """Abstract base class for updates to be applied to the state."""
    def apply(self, problem: Problem, state: State):
        """Apply the update to the given problem and state."""
        raise NotImplementedError("Must be implemented by subclasses")

    def copies(self, params: List):
        """Create a copy of the update with given parameters."""
        raise NotImplementedError("Must be implemented by subclasses")

    def __repr__(self):
        return self.__str__()

class ConstUpdate(Update):
    """Update that sets a variable at a given index to a constant value."""
    def __init__(self, variableName: str, index: int, const: int):
        self.variableName = variableName
        self.const = const
        self.index = index

    def __str__(self):
        return "const update: " + str(self.variableName) + " <- " + str(self.const) + " at " + str(self.index) + " "

    def apply(self, problem: Problem, state: State):
        """Set the variable at the index to the constant value."""
        problem.set_value(state, self.variableName, self.index, self.const)

    def copies(self, params: List):
        """
        No real benefit to create new instances of this class.
        """
        return self

class ExpressionIndexUpdate(Update):
    """Update that sets a variable at a fixed index to the result of an expression."""
    def __init__(self, variableName: str, index: int, expression: ExpressionNode):
        self.variableName = variableName
        self.index = index
        self.expression = expression

    def __str__(self):
        return ("exp idx update: " + str(self.variableName) + " <- ("
                + str(self.expression) + ") at " + str(self.index) + " ")

    def apply(self, problem: Problem, state: State):
        """Set the variable at the index to the evaluated expression."""
        value = self.expression.evaluate(problem, state)
        problem.set_value(state, self.variableName, self.index, value)

    def copies(self, params: List):
        """
        Copies object's expression.
        """
        return ExpressionIndexUpdate(self.variableName, self.index, self.expression.copies(params))

class ExpressionRemoveUpdate(Update):
    """Update that removes an entity based on the evaluated expression."""
    def __init__(self, entityIndex: int, expression: ExpressionNode):
        self.entityIndex = entityIndex
        self.expression = expression

    def __str__(self):
        return "remove from: " + str(self.entityIndex) + " <- (" + str(self.expression) + ") "

    def apply(self, problem: Problem, state: State):
        """Remove the entity evaluated from the expression."""
        entity_id = self.expression.evaluate(problem, state)
        problem.remove_entity(state, self.entityIndex, entity_id)

    def copies(self, params: List):
        """
        Copies object's expression.
        """
        return ExpressionRemoveUpdate(self.entityIndex, self.expression.copies(params))

class ExpressionAddUpdate(Update):
    """Update that adds entities based on evaluated expressions."""
    def __init__(self, entityIndex: int, *expressions: ExpressionNode):
        self.entityIndex = entityIndex
        self.expressions = expressions

    def __str__(self):
        return ("add to: " + str(self.entityIndex) + " <- ("
                + str([expression for expression in self.expressions]) + ") ")

    def apply(self, problem: Problem, state: State):
        """Add entities evaluated from the expressions."""
        values = [expression.evaluate(problem, state) for expression in self.expressions]
        problem.add_entity(state, self.entityIndex, *values)

    def copies(self, params: List):
        """
        Copies object's expressions.
        """
        return ExpressionAddUpdate(self.entityIndex,
                                   *[expression.copies(params) for expression in self.expressions])

class ExpressionReplaceUpdate(Update):
    """Update that replaces an entity with new values based on expressions."""
    def __init__(self, entityIndex: int, expressionId: ExpressionNode, *expressions: ExpressionNode):
        self.entityIndex = entityIndex
        self.expressionId = expressionId
        self.expressions = expressions

    def __str__(self):
        return ("replace in: " + str(self.entityIndex) + " instead (" + str(self.expressionId) + ") <- ("
                + str([expression for expression in self.expressions]) + ") ")

    def apply(self, problem: Problem, state: State):
        """Replace the entity with new values evaluated from the expressions."""
        entity_id = self.expressionId.evaluate(problem, state)
        new_values = [expr.evaluate(problem, state) for expr in self.expressions]
        problem.replace_entity(state, self.entityIndex, entity_id, *new_values)

    def copies(self, params: List):
        """
        Copies object's expressions.
        """
        return ExpressionReplaceUpdate(self.entityIndex, self.expressionId.copies(params),
                                       *[expression.copies(params) for expression in self.expressions])

class ExpressionUpdate(Update):
    """Update that sets a variable at an index evaluated from an expression to a value evaluated from another expression."""
    def __init__(self, variableName: str, expressionIndex: ExpressionNode, expressionValue: ExpressionNode):
        self.variableName = variableName
        self.expressionIndex = expressionIndex
        self.expressionValue = expressionValue

    def __str__(self):
        return ("exp update: " + str(self.variableName) + " at (" + str(self.expressionIndex) + ") <- ("
                + str(self.expressionValue) + ") ")

    def apply(self, problem: Problem, state: State):
        """Set the variable at the evaluated index to the evaluated value."""
        index = self.expressionIndex.evaluate(problem, state)
        value = self.expressionValue.evaluate(problem, state)
        problem.set_value(state, self.variableName, index, value)

    def copies(self, params: List):
        """
        Copies object's expressions.
        """
        return ExpressionUpdate(self.variableName,
                                self.expressionIndex.copies(params),
                                self.expressionValue.copies(params))

class ParameterUpdate(Update):
    """Update that sets a parameter to the evaluated result of an expression."""
    def __init__(self, parameter: NewValParameterNode, expression: ExpressionNode):
        self.parameter = parameter
        self.expression = expression

    def __str__(self):
        return "par update: " + str(self.parameter) + ") <- (" + str(self.expression) + ") "

    def apply(self, problem: Problem, state: State):
        """Update the parameter with the evaluated expression."""
        value = self.expression.evaluate(problem, state)
        self.parameter.updateParam(value)

    def copies(self, params: List):
        """
        Copies object's operator & expression.
        """
        return ParameterUpdate(self.parameter.copies(params), self.expression.copies(params))

class CaseUpdate(Update):
    """Conditional update that applies different updates based on a condition."""
    def __init__(self, condition: ExpressionNode, updates, elseUpdates=None):
        self.condition = condition
        self.updates = updates
        self.elseUpdates = elseUpdates if elseUpdates else []

    def __str__(self):
        return ("case by (" + str(self.condition) + ") updates (" + str([exp for exp in self.updates]) + ") otherwise ("
                + str([exp for exp in self.elseUpdates]) + ") ")

    def apply(self, problem: Problem, state: State):
        """Apply updates based on the evaluated condition."""
        if self.condition.evaluate(problem, state):
            for update in self.updates:
                update.apply(problem, state)
        else:
            for update in self.elseUpdates:
                update.apply(problem, state)

    def copies(self, params: List):
        """
        Copies object's expressions.
        """
        return CaseUpdate(self.condition.copies(params),
                          [expression.copies(params) for expression in self.updates],
                          [expression.copies(params) for expression in self.elseUpdates])

class AllUpdate(Update):
    """Update that applies a set of updates to all entities of a certain type, optionally filtered by a condition."""
    def __init__(self, entityIndex: int, parameter: ValueParameterNode, updates, condition: ExpressionNode = None):
        self.entityIndex = entityIndex
        # Must have the id of len(Action's param) + position of nesting (starting at 0).
        self.parameter = parameter
        self.updates = updates
        self.condition = condition  # Optional condition to filter items

    def __str__(self):
        return ("all " + str(self.entityIndex) + " by (" + str(self.condition)
                + ") updates (" + str([exp for exp in self.updates]) + ") ")

    def apply(self, problem: Problem, state: State):
        """Apply updates to all entities, optionally filtering by the condition."""
        for entity in problem.get_entity_ids(state, self.entityIndex):
            self.parameter.updateParam(entity)
            if self.condition is None or self.condition.evaluate(problem, state):
                for update in self.updates:
                    update.apply(problem, state)

    def copies(self, params: List):
        """
        Copies object's expressions, ensures the same AllUpdate's parameter is used.
        """
        # Using the same parameter for all expressions and updates in block.
        params = params.copy()
        params.append(self.parameter)
        return AllUpdate(self.entityIndex, self.parameter,
                         [expression.copies(params) for expression in self.updates],
                         self.condition.copies(params) if self.condition else None)

class RepeatUpdate(Update):
    """Update that repeatedly applies a set of updates while a condition holds."""
    def __init__(self, condition: ExpressionNode, updates):
        self.condition = condition
        self.updates = updates

    def __str__(self):
        return ("repeat by (" + str(self.condition) + ") updates (" + str([exp for exp in self.updates]) + ") ")

    def apply(self, problem: Problem, state: State):
        """Repeatedly apply updates while the condition evaluates to True."""
        while self.condition.evaluate(problem, state):
            for update in self.updates:
                update.apply(problem, state)

    def copies(self, params: List):
        """
        Repeat object's expressions.
        """
        return RepeatUpdate(self.condition.copies(params),
                            [expression.copies(params) for expression in self.updates])

class CostExpression(ExpressionNode):
    """Represents a cost expression that may include updates to the state."""
    def __init__(self, updates: List[Update], costExpression: ExpressionNode):
        self.updates = updates
        self.costExpression = costExpression

    def __str__(self):
        return ("Cost Segment:\nUpdate: " + str([update for update in self.updates])
                + "\nCost: " + str(self.costExpression) + " ")

    def evaluate(self, problem, state):
        """Apply updates and then evaluate the cost expression."""
        # First, apply updates (e.g., 'NewVar' assignments)
        for update in self.updates:
            update.apply(problem, state)
        # Then evaluate the cost expression
        return self.costExpression.evaluate(problem, state)

    def copies(self, params: List):
        """
        Copies object's expressions.
        """
        return CostExpression([expression.copies(params) for expression in self.updates],
                              self.costExpression.copies(params))

    def applicable(self) -> bool:
        """Applicable if the cost expression is applicable."""
        return self.costExpression.applicable()
