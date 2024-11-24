import re
from CARRI.expression import *

def tokenize(expression_str):
    """
    Tokenize the input expression string into a list of tokens.

    Args:
        expression_str (str): The expression string to tokenize.

    Returns:
        List[Tuple[str, Any]]: A list of tokens in the form (token_type, token_value).
    """
    token_specification = [
        ('NUMBER', r'\d+'),
        ('ID', r'[A-Za-z_][A-Za-z0-9_]*'),
        ('OP', r'==|!=|>=|<=|\?|@|[+\-*/=><!@:]'),
        ('LPAREN', r'\('),
        ('RPAREN', r'\)'),
        ('COMMA', r','),
        ('SKIP', r'[ \t]+'),
        ('MISMATCH', r'.'),
    ]
    keywords = {'and', 'or', 'not', 'true', 'false', 'exists', 'entity'}
    token_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    get_token = re.compile(token_regex, re.IGNORECASE).match  # Case-insensitive matching
    line = expression_str
    mo = get_token(line)
    tokens = []
    while mo is not None:
        kind = mo.lastgroup
        value = mo.group()
        if kind == 'NUMBER':
            value = int(value)
            tokens.append(('NUMBER', value))
        elif kind == 'ID':
            value_lower = value.lower()
            if value_lower in keywords:
                tokens.append(('KEYWORD', value_lower))
            else:
                tokens.append(('ID', value))
        elif kind == 'OP':
            tokens.append(('OP', value))
        elif kind in ('LPAREN', 'RPAREN', 'COMMA'):
            tokens.append((kind, value))
        elif kind == 'SKIP':
            pass  # Ignore whitespace
        else:
            raise RuntimeError(f'Unexpected character {value!r} in expression')
        pos = mo.end()
        mo = get_token(line, pos)
    return tokens

operatorMap = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
    '=': operator.eq,
    '==': operator.eq,
    '!=': operator.ne,
    '>': operator.gt,
    '<': operator.lt,
    '>=': operator.ge,
    '<=': operator.le,
    'and': operator.and_,
    'or': operator.or_,
    'not': operator.not_,
    '?': operator.contains,
    '@': operator.getitem
}

class ExpressionParser:
    """Parses expressions into ExpressionNode objects using recursive descent parsing."""

    def __init__(self, expression: str, parameters: List[str], paramExpressions: List[ParameterNode], parsedEntities):
        """
        Initialize the ExpressionParser.

        Args:
            expression (str): The expression string to parse.
            parameters (List[str]): A list of parameter names.
            paramExpressions (List[ParameterNode]): A list of ParameterNode objects corresponding to the parameters.
            parsedEntities (Dict): A dictionary of parsed entities.
        """
        self.tokens = tokenize(expression)
        self.position = 0
        self.parameters = parameters
        self.paramExpressions = paramExpressions
        self.operatorMap = operatorMap  # Ensure operatorMap is accessible
        self.parsedEntities = parsedEntities

    def parse_expression(self) -> ExpressionNode:
        """Parse an expression and return the root ExpressionNode."""
        return self.parse_or_expression()

    def parse_or_expression(self) -> ExpressionNode:
        """Parse an 'or' expression."""
        node = self.parse_and_expression()
        while self.match('KEYWORD', 'or'):
            self.consume('KEYWORD', 'or')
            right = self.parse_and_expression()
            node = OperatorNode(self.operatorMap['or'], node, right)
        return node

    def parse_and_expression(self) -> ExpressionNode:
        """Parse an 'and' expression."""
        node = self.parse_not_expression()
        while self.match('KEYWORD', 'and'):
            self.consume('KEYWORD', 'and')
            right = self.parse_not_expression()
            node = OperatorNode(self.operatorMap['and'], node, right)
        return node

    def parse_not_expression(self) -> ExpressionNode:
        """Parse a 'not' expression."""
        if self.match('KEYWORD', 'not'):
            self.consume('KEYWORD', 'not')
            operand = self.parse_not_expression()
            node = OperatorNode(self.operatorMap['not'], operand)
            return node
        else:
            return self.parse_comparison()

    def parse_comparison(self) -> ExpressionNode:
        """Parse a comparison expression."""
        node = self.parse_add_expr()
        while self.match('OP', ('=', '!=', '>', '<', '>=', '<=', '?')):
            opToken = self.consume('OP')
            operatorFn = self.operatorMap[opToken[1]]
            right = self.parse_add_expr()
            node = OperatorNode(operatorFn, node, right)
        return node

    def parse_add_expr(self) -> ExpressionNode:
        """Parse an addition or subtraction expression."""
        node = self.parse_mul_expr()
        while self.match('OP', ('+', '-')):
            opToken = self.consume('OP')
            operatorFn = self.operatorMap[opToken[1]]
            right = self.parse_mul_expr()
            node = OperatorNode(operatorFn, node, right)
        return node

    def parse_mul_expr(self) -> ExpressionNode:
        """Parse a multiplication or division expression."""
        node = self.parse_unary_expr()
        while self.match('OP', ('*', '/')):
            opToken = self.consume('OP')
            operatorFn = self.operatorMap[opToken[1]]
            right = self.parse_unary_expr()
            node = OperatorNode(operatorFn, node, right)
        return node

    def parse_unary_expr(self) -> ExpressionNode:
        """Parse a unary expression with optional '+' or '-' operators."""
        if self.match('OP', ('+', '-')):
            opToken = self.consume('OP')
            operatorFn = self.operatorMap[opToken[1]]
            operand = self.parse_unary_expr()
            node = OperatorNode(operatorFn, operand)
            return node
        else:
            return self.parse_postfix_expr()

    def parse_postfix_expr(self) -> ExpressionNode:
        """Parse a postfix expression, handling the '@' operator."""
        node = self.parse_primary()
        while True:
            if self.match('OP', '@'):
                opToken = self.consume('OP')
                operatorFn = self.operatorMap[opToken[1]]
                right = self.parse_primary()
                node = OperatorNode(operatorFn, node, right)
            else:
                break
        return node

    def parse_primary(self) -> ExpressionNode:
        """Parse a primary expression, which could be a number, boolean, entity reference, variable, or expression in parentheses."""
        if self.match('NUMBER'):
            value = self.consume('NUMBER')[1]
            return ConstNode(value)
        elif self.match('KEYWORD', ('true', 'false')):
            value = self.consume('KEYWORD')[1].lower() == 'true'
            return ConstNode(value)
        elif self.match('KEYWORD', 'entity'):
            return self.parse_entity_reference()
        elif self.match('ID'):
            # Check if this is an 'exists' condition
            return self.parse_variable_or_parameter_or_exists()
        elif self.match('LPAREN'):
            self.consume('LPAREN')
            node = self.parse_expression()
            self.consume('RPAREN')
            return node
        else:
            raise SyntaxError('Expected expression at token position {}'.format(self.position))

    def parse_entity_reference(self) -> ExpressionNode:
        """Parse an entity reference."""
        self.consume('KEYWORD', 'entity')
        # Collect the entity name, which may consist of multiple IDs
        entity_name_parts = []
        while self.match('ID'):
            entity_name_parts.append(self.consume('ID')[1])
        if not entity_name_parts:
            raise SyntaxError('Expected entity name after "entity"')
        entity_name = ' '.join(entity_name_parts)
        # Get entity index from parsedEntities
        entity_entry = self.parsedEntities.get(entity_name)
        if entity_entry is None:
            raise ValueError(f"Unknown entity: {entity_name}")
        entity_index = entity_entry[0]
        return ConstNode(entity_index)

    def parse_variable_or_parameter_or_exists(self) -> ExpressionNode:
        """Parse a variable, parameter, or 'exists' condition."""
        idToken = self.consume('ID')
        name = idToken[1]

        # Check if 'exists' follows
        if self.match('KEYWORD', 'exists'):
            self.consume('KEYWORD', 'exists')
            # The next token should be a parameter
            if self.match('ID'):
                paramName = self.consume('ID')[1]
                if paramName in self.parameters:
                    index = self.parameters.index(paramName)
                    paramExpr = self.paramExpressions[index]
                    # Get entity index from parsedEntities
                    entityIndex = self.parsedEntities.get(name)[0]
                    if entityIndex is None:
                        raise ValueError(f"Unknown entity: {name}")
                    return ExistingExpressionNode(entityIndex, paramExpr)
                else:
                    raise SyntaxError(f"Unknown parameter: {paramName}")
            else:
                raise SyntaxError('Expected parameter after "exists"')
        else:
            # Not an 'exists' condition, proceed as variable or parameter
            return self.parse_variable_or_parameter_continued(name)

    def parse_variable_or_parameter_continued(self, name) -> ExpressionNode:
        """Continue parsing a variable or parameter, possibly with an index expression."""
        if name in self.parameters:
            # It's a parameter
            index = self.parameters.index(name)
            return self.paramExpressions[index]

        # It's the start of a variable name
        nameParts = [name]
        while True:
            if self.match('ID'):
                nextToken = self.tokens[self.position]
                nextName = nextToken[1]
                if nextName in self.parameters or self.is_operator_ahead() or self.is_end_of_expression():
                    # Next ID is a parameter or an operator, so stop collecting variable name
                    break
                else:
                    # Consume and add to variable name
                    self.consume('ID')
                    nameParts.append(nextName)
            else:
                break
        variableName = ' '.join(nameParts)

        # Now check for index expression
        indexExpr = None
        if self.match('LPAREN'):
            self.consume('LPAREN')
            indexExpr = self.parse_expression()
            self.consume('RPAREN')
        elif self.match('ID') or self.match('NUMBER') or self.match('LPAREN'):
            # Parse index expression
            indexExpr = self.parse_primary()
        else:
            # No index expression
            indexExpr = None

        if indexExpr is None:
            # No index expression
            return ValueIndexNode(variableName, 0)  # Default index if needed
        else:
            return ValueNode(variableName, indexExpr)

    def is_operator_ahead(self) -> bool:
        """Check if an operator token is ahead."""
        if self.position < len(self.tokens):
            tokenKind, token_value = self.tokens[self.position]
            return tokenKind == 'OP' or (tokenKind == 'KEYWORD' and token_value in self.operatorMap)
        return False

    def is_end_of_expression(self) -> bool:
        """Check if the end of the token list has been reached."""
        return self.position >= len(self.tokens)

    # Helper methods
    def match(self, kind, value=None):
        """Check if the next token matches the expected kind and value."""
        if self.position >= len(self.tokens):
            return False
        tokenKind, tokenValue = self.tokens[self.position]
        if kind != tokenKind:
            return False
        if value is None:
            return True
        if isinstance(value, tuple):
            return tokenValue in value
        else:
            return tokenValue == value

    def consume(self, kind, value=None):
        """Consume the next token if it matches the expected kind and value."""
        if not self.match(kind, value):
            expected = f"{kind} {value}" if value else kind
            actualKind, actualValue = self.tokens[self.position] if self.position < len(self.tokens) else (None, None)
            actual = f"{actualKind} {actualValue}" if actualValue else actualKind
            raise SyntaxError(f'Expected {expected}, got {actual}')
        token = self.tokens[self.position]
        self.position += 1
        return token
