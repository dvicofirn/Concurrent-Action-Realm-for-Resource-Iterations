import re
from CARRI.expression import *

def tokenize(expression_str):
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
            pass
        else:
            raise RuntimeError(f'Unexpected character {value!r} in expression')
        pos = mo.end()
        mo = get_token(line, pos)
    return tokens

operator_map = {
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
    def __init__(self, expression: str, parameters: List[str], paramExpressions: List[ParameterNode], parsedEntities):
        self.tokens = tokenize(expression)
        self.position = 0
        self.parameters = parameters
        self.paramExpressions = paramExpressions
        self.operator_map = operator_map  # Ensure operator_map is accessible
        self.parsedEntities = parsedEntities

    def parse_expression(self) -> ExpressionNode:
        return self.parse_or_expression()

    def parse_or_expression(self) -> ExpressionNode:
        node = self.parse_and_expression()
        while self.match('KEYWORD', 'or'):
            self.consume('KEYWORD', 'or')
            right = self.parse_and_expression()
            node = OperatorNode(self.operator_map['or'], node, right)
        return node

    def parse_and_expression(self) -> ExpressionNode:
        node = self.parse_not_expression()
        while self.match('KEYWORD', 'and'):
            self.consume('KEYWORD', 'and')
            right = self.parse_not_expression()
            node = OperatorNode(self.operator_map['and'], node, right)
        return node

    def parse_not_expression(self) -> ExpressionNode:
        if self.match('KEYWORD', 'not'):
            self.consume('KEYWORD', 'not')
            operand = self.parse_not_expression()
            node = OperatorNode(self.operator_map['not'], operand)
            return node
        else:
            return self.parse_comparison()

    def parse_comparison(self) -> ExpressionNode:
        node = self.parse_add_expr()
        while self.match('OP', ('=', '!=', '>', '<', '>=', '<=', '?')):
            op_token = self.consume('OP')
            operator_fn = self.operator_map[op_token[1]]
            right = self.parse_add_expr()
            node = OperatorNode(operator_fn, node, right)
        return node

    def parse_add_expr(self) -> ExpressionNode:
        node = self.parse_mul_expr()
        while self.match('OP', ('+', '-')):
            op_token = self.consume('OP')
            operator_fn = self.operator_map[op_token[1]]
            right = self.parse_mul_expr()
            node = OperatorNode(operator_fn, node, right)
        return node

    def parse_mul_expr(self) -> ExpressionNode:
        node = self.parse_unary_expr()
        while self.match('OP', ('*', '/')):
            op_token = self.consume('OP')
            operator_fn = self.operator_map[op_token[1]]
            right = self.parse_unary_expr()
            node = OperatorNode(operator_fn, node, right)
        return node

    def parse_unary_expr(self) -> ExpressionNode:
        if self.match('OP', ('+', '-')):
            op_token = self.consume('OP')
            operator_fn = self.operator_map[op_token[1]]
            operand = self.parse_unary_expr()
            node = OperatorNode(operator_fn, operand)
            return node
        else:
            return self.parse_postfix_expr()

    def parse_postfix_expr(self) -> ExpressionNode:
        node = self.parse_primary()
        while True:
            if self.match('OP', '@'):
                op_token = self.consume('OP')
                operator_fn = self.operator_map[op_token[1]]
                right = self.parse_primary()
                node = OperatorNode(operator_fn, node, right)
            else:
                break
        return node

    def parse_primary(self) -> ExpressionNode:
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
        id_token = self.consume('ID')
        name = id_token[1]

        # Check if 'exists' follows
        if self.match('KEYWORD', 'exists'):
            self.consume('KEYWORD', 'exists')
            # The next token should be a parameter
            if self.match('ID'):
                param_name = self.consume('ID')[1]
                if param_name in self.parameters:
                    index = self.parameters.index(param_name)
                    param_expr = self.paramExpressions[index]
                    # Get entity index from parsedEntities
                    entity_index = self.parsedEntities.get(name)[0]
                    if entity_index is None:
                        raise ValueError(f"Unknown entity: {name}")
                    return ExistingExpressionNode(entity_index, param_expr)
                else:
                    raise SyntaxError(f"Unknown parameter: {param_name}")
            else:
                raise SyntaxError('Expected parameter after "exists"')
        else:
            # Not an 'exists' condition, proceed as before
            return self.parse_variable_or_parameter_continued(name)

    def parse_variable_or_parameter_continued(self, name) -> ExpressionNode:
        if name in self.parameters:
            # It's a parameter
            index = self.parameters.index(name)
            return self.paramExpressions[index]

        # It's the start of a variable name
        name_parts = [name]
        while True:
            if self.match('ID'):
                next_token = self.tokens[self.position]
                next_name = next_token[1]
                if next_name in self.parameters or self.is_operator_ahead() or self.is_end_of_expression():
                    # Next ID is a parameter or an operator, so stop collecting variable name
                    break
                else:
                    # Consume and add to variable name
                    self.consume('ID')
                    name_parts.append(next_name)
            else:
                break
        variable_name = ' '.join(name_parts)

        # Now check for index expression
        index_expr = None
        if self.match('LPAREN'):
            self.consume('LPAREN')
            index_expr = self.parse_expression()
            self.consume('RPAREN')
        elif self.match('ID') or self.match('NUMBER') or self.match('LPAREN'):
            # Parse index expression
            index_expr = self.parse_primary()
        else:
            # No index expression
            index_expr = None

        if index_expr is None:
            # No index expression
            return ValueIndexNode(variable_name, 0)  # Default index if needed
        else:
            return ValueNode(variable_name, index_expr)

    def is_operator_ahead(self) -> bool:
        # Check if an operator is ahead
        if self.position < len(self.tokens):
            token_kind, token_value = self.tokens[self.position]
            return token_kind == 'OP' or (token_kind == 'KEYWORD' and token_value in self.operator_map)
        return False

    def is_end_of_expression(self) -> bool:
        # Check if end of tokens
        return self.position >= len(self.tokens)

    def get_parameter_expression(self, name):
        # Todo: check if redundant
        if name in self.parameters:
            index = self.parameters.index(name)
            return self.paramExpressions[index]
        else:
            # Variable without index (assuming index 0 or handle appropriately)
            return ValueIndexNode(name, 0)

    # Helper methods
    def match(self, kind, value=None):
        if self.position >= len(self.tokens):
            return False
        token_kind, token_value = self.tokens[self.position]
        if kind != token_kind:
            return False
        if value is None:
            return True
        if isinstance(value, tuple):
            return token_value in value
        else:
            return token_value == value

    def consume(self, kind, value=None):
        if not self.match(kind, value):
            expected = f"{kind} {value}" if value else kind
            actual_kind, actual_value = self.tokens[self.position] if self.position < len(self.tokens) else (None, None)
            actual = f"{actual_kind} {actual_value}" if actual_value else actual_kind
            raise SyntaxError(f'Expected {expected}, got {actual}')
        token = self.tokens[self.position]
        self.position += 1
        return token

