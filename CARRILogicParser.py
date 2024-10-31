import operator
import re
from CARRILogic import *

def parse_expression(expression: str, parameters: List[str],
                     paramExpressions: List[ParameterNode], parsedEntities) -> ExpressionNode:
    parser = LogicParser(expression, parameters, paramExpressions, parsedEntities)
    expr_node = parser.parse_expression()
    return expr_node

def parse_conditions(conditions: List[str], parameters: List[str],
                     paramExpressions: List[ParameterNode], parsedEntities) -> List[ExpressionNode]:
    parsed_conditions = []
    for condition_str in conditions:
        condition = parse_expression(condition_str, parameters, paramExpressions, parsedEntities)
        parsed_conditions.append(condition)
    return parsed_conditions

def parse_effects(effects_list: List, parameters: List[str],
                  paramExpressions: List[ParameterNode], parsedEntities) -> List[Update]:
    updates = []
    for effect in effects_list:
        if isinstance(effect, str):
            # Check if it's a 'remove' or 'add' effect
            effect = effect.strip()
            if effect.startswith('NewVar'):
                # Handle 'NewVar' statements
                _, rest = effect.split('NewVar', 1)
                rest = rest.strip()
                if ':' in rest:
                    variable_name, expr_str = rest.split(':', 1)
                    variable_name = variable_name.strip()
                    expr_str = expr_str.strip()
                    # Parse the expression
                    expr_node = parse_expression(expr_str, parameters, paramExpressions, parsedEntities)
                    # Create a new ParameterNode with the expression's value
                    param_index = len(paramExpressions)
                    new_param_node = ParameterNode(param_index)
                    # Evaluate the expression and set the value
                    # Note: Since we can't evaluate here, we'll store the expression node
                    # and evaluate it when setting up the parameter values
                    new_param_node.expression = expr_node
                    # Extend parameters and paramExpressions
                    parameters = parameters + [variable_name]
                    paramExpressions = paramExpressions + [new_param_node]
                    # Optionally, store the new variable in a mapping if needed
                else:
                    raise SyntaxError(f"Invalid NewVar syntax: {effect}")
            elif ' remove' in effect:
                entity_name, rest = effect.split('remove', 1)
                entity_name = entity_name.strip()
                rest = rest.strip()
                if ':' in rest:
                    _, expr_str = rest.split(':', 1)
                    expr_str = expr_str.strip()
                    expr_node = parse_expression(expr_str, parameters, paramExpressions, parsedEntities)
                    entity_index = parsedEntities.get(entity_name)
                    if entity_index is None:
                        raise ValueError(f"Unknown entity: {entity_name}")
                    updates.append(ExpressionRemoveUpdate(entity_index, expr_node))
                else:
                    raise SyntaxError(f"Invalid remove syntax: {effect}")
            elif ' add' in effect:
                entity_name, rest = effect.split('add', 1)
                entity_name = entity_name.strip()
                rest = rest.strip()
                if ':' in rest:
                    _, expr_list_str = rest.split(':', 1)
                    expr_list_str = expr_list_str.strip()
                    # Parse expressions inside parentheses
                    if expr_list_str.startswith('(') and expr_list_str.endswith(')'):
                        expr_list_str = expr_list_str[1:-1].strip()
                        expr_strs = [s.strip() for s in expr_list_str.split(',')]
                        expr_nodes = [parse_expression(expr_str, parameters, paramExpressions, parsedEntities) for expr_str in expr_strs]
                        entity_index = parsedEntities.get(entity_name)
                        if entity_index is None:
                            raise ValueError(f"Unknown entity: {entity_name}")
                        updates.append(ExpressionAddUpdate(entity_index, *expr_nodes))
                    else:
                        raise SyntaxError(f"Invalid add syntax: {effect}")
                else:
                    raise SyntaxError(f"Invalid add syntax: {effect}")
            elif ' replace' in effect:
                entity_name, rest = effect.split('replace', 1)
                entity_name = entity_name.strip()
                rest = rest.strip()
                if ':' in rest:
                    expr_id_str, expr_list_str = rest.split(':', 1)
                    expr_id_str = expr_id_str.strip()
                    expr_list_str = expr_list_str.strip()
                    # Parse the ID expression
                    expr_id = parse_expression(expr_id_str, parameters, paramExpressions, parsedEntities)
                    # Parse expressions inside parentheses
                    if expr_list_str.startswith('(') and expr_list_str.endswith(')'):
                        expr_list_str = expr_list_str[1:-1].strip()
                        expr_strs = [s.strip() for s in expr_list_str.split(',')]
                        expr_nodes = [parse_expression(expr_str, parameters, paramExpressions, parsedEntities) for
                                      expr_str in expr_strs]
                        entity_index = parsedEntities.get(entity_name)
                        if entity_index is None:
                            raise ValueError(f"Unknown entity: {entity_name}")
                        updates.append(ExpressionReplaceUpdate(entity_index, expr_id, *expr_nodes))
                    else:
                        raise SyntaxError(f"Invalid replace syntax: {effect}")
            else:
                # Simple update
                update = parse_update(effect, parameters, paramExpressions, parsedEntities)
                updates.append(update)
        # Case and All blocks
        elif isinstance(effect, dict):
            block_name = effect.get('name')
            if block_name == 'case':
                condition_str = effect['condition']
                condition = parse_expression(condition_str, parameters, paramExpressions, parsedEntities)
                segment = effect['segment']
                updates_segment = parse_effects(segment, parameters, paramExpressions, parsedEntities)
                else_segment = effect.get('elseUpdates', [])
                updates_else = parse_effects(else_segment, parameters, paramExpressions, parsedEntities)
                updates.append(CaseUpdate(condition, updates_segment, updates_else))
            elif block_name == 'all':
                entityIndex = parsedEntities[effect['entity']][0]
                parameter_name = effect['parameter']
                parameter_node = ParameterNode(len(paramExpressions))
                # Extend parameters and paramExpressions for the new scope
                new_parameters = parameters + [parameter_name]
                new_paramExpressions = paramExpressions + [parameter_node]
                segment = effect['segment']
                condition_str = effect.get('condition')
                if condition_str:
                    condition = parse_expression(condition_str, new_parameters, new_paramExpressions, parsedEntities)
                else:
                    condition = None
                updates_segment = parse_effects(segment, new_parameters, new_paramExpressions, parsedEntities)
                updates.append(AllUpdate(entityIndex, parameter_node, updates_segment, condition))
            else:
                raise ValueError(f"Unknown block name: {block_name}")
        else:
            raise ValueError(f"Invalid effect: {effect}")
    return updates

def parse_update(update_str: str, parameters: List[str], paramExpressions: List[ParameterNode], parsedEntities) -> Update:
    if ':' not in update_str:
        raise SyntaxError(f"Invalid update syntax: {update_str}")
    lhs_str, rhs_str = map(str.strip, update_str.split(':', 1))
    # Parse LHS (should result in ValueNode or ValueIndexNode)
    lhs_parser = LogicParser(lhs_str, parameters, paramExpressions, parsedEntities)
    lhs_node = lhs_parser.parse_primary()
    # Parse RHS as an expression
    rhs_node = parse_expression(rhs_str, parameters, paramExpressions, parsedEntities)
    # Create Update object
    if isinstance(lhs_node, ValueNode):
        return ExpressionUpdate(lhs_node.variableName, lhs_node.expression, rhs_node)
    elif isinstance(lhs_node, ValueIndexNode):
        return ExpressionIndexUpdate(lhs_node.variableName, lhs_node.index, rhs_node)
    else:
        raise SyntaxError(f"Invalid LHS in update: {lhs_str}")

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
    keywords = {'and', 'or', 'not', 'true', 'false', 'exists'}
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

class LogicParser:
    def __init__(self, expression: str, parameters: List[str], paramExpressions: List[ParameterNode], parsedEntities):
        self.tokens = tokenize(expression)
        self.position = 0
        self.parameters = parameters
        self.paramExpressions = paramExpressions
        self.operator_map = operator_map  # Ensure operator_map is accessible
        self.parsedEntities = parsedEntities

    def parse_expression(self):
        return self.parse_or_expression()

    def parse_or_expression(self):
        node = self.parse_and_expression()
        while self.match('KEYWORD', 'or'):
            self.consume('KEYWORD', 'or')
            right = self.parse_and_expression()
            node = OperatorNode(self.operator_map['or'], node, right)
        return node

    def parse_and_expression(self):
        node = self.parse_not_expression()
        while self.match('KEYWORD', 'and'):
            self.consume('KEYWORD', 'and')
            right = self.parse_not_expression()
            node = OperatorNode(self.operator_map['and'], node, right)
        return node

    def parse_not_expression(self):
        if self.match('KEYWORD', 'not'):
            self.consume('KEYWORD', 'not')
            operand = self.parse_not_expression()
            node = OperatorNode(self.operator_map['not'], operand)
            return node
        else:
            return self.parse_comparison()

    def parse_comparison(self):
        node = self.parse_add_expr()
        while self.match('OP', ('=', '!=', '>', '<', '>=', '<=', '?')):
            op_token = self.consume('OP')
            operator_fn = self.operator_map[op_token[1]]
            right = self.parse_add_expr()
            node = OperatorNode(operator_fn, node, right)
        return node

    def parse_add_expr(self):
        node = self.parse_mul_expr()
        while self.match('OP', ('+', '-')):
            op_token = self.consume('OP')
            operator_fn = self.operator_map[op_token[1]]
            right = self.parse_mul_expr()
            node = OperatorNode(operator_fn, node, right)
        return node

    def parse_mul_expr(self):
        node = self.parse_unary_expr()
        while self.match('OP', ('*', '/')):
            op_token = self.consume('OP')
            operator_fn = self.operator_map[op_token[1]]
            right = self.parse_unary_expr()
            node = OperatorNode(operator_fn, node, right)
        return node

    def parse_unary_expr(self):
        if self.match('OP', ('+', '-')):
            op_token = self.consume('OP')
            operator_fn = self.operator_map[op_token[1]]
            operand = self.parse_unary_expr()
            node = OperatorNode(operator_fn, operand)
            return node
        else:
            return self.parse_postfix_expr()

    def parse_postfix_expr(self):
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

    def parse_primary(self):
        if self.match('NUMBER'):
            value = self.consume('NUMBER')[1]
            return ConstNode(value)
        elif self.match('KEYWORD', ('true', 'false')):
            value = self.consume('KEYWORD')[1].lower() == 'true'
            return ConstNode(value)
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

    def parse_variable_or_parameter_or_exists(self):
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
                    entity_index = self.parsedEntities.get(name)
                    if entity_index is None:
                        raise ValueError(f"Unknown entity: {name}")
                    return ExistingParameterNode(entity_index, param_expr)
                else:
                    raise SyntaxError(f"Unknown parameter: {param_name}")
            else:
                raise SyntaxError('Expected parameter after "exists"')
        else:
            # Not an 'exists' condition, proceed as before
            return self.parse_variable_or_parameter_continued(name)

    def parse_variable_or_parameter_continued(self, name):
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

    def is_operator_ahead(self):
        # Check if an operator is ahead
        if self.position < len(self.tokens):
            token_kind, token_value = self.tokens[self.position]
            return token_kind == 'OP' or (token_kind == 'KEYWORD' and token_value in self.operator_map)
        return False

    def is_end_of_expression(self):
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

