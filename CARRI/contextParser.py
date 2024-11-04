from CARRI.expression import *
from CARRI.expressionParser import ExpressionParser
from typing import Union

class ContextParser:
    def __init__(self, parameters, paramExpressions, parsedEntities):
        self.parameters = parameters
        self.paramExpressions = paramExpressions
        self.parsedEntities = parsedEntities

# Pass the segment to a matching parsing function
    def parse(self, segment: List[str], type: str):
        if type == "conditions":
            return self.parse_conditions(segment, self.parameters, self.paramExpressions)
        elif type == "effects":
            return self.parse_effects(segment, self.parameters.copy(), self.paramExpressions.copy())
        elif type == "cost":
            return self.parse_cost(segment, self.parameters.copy(), self.paramExpressions.copy())

    def parse_expression(self, expression: str, parameters: List[str],
                         paramExpressions: List[ParameterNode]) -> ExpressionNode:
        parser = ExpressionParser(expression, parameters, paramExpressions, self.parsedEntities)
        expr_node = parser.parse_expression()
        return expr_node

    def parse_conditions(self, conditions: List[str], parameters: List[str],
                         paramExpressions: List[ParameterNode]) -> List[ExpressionNode]:
        parsed_conditions = []
        for condition_str in conditions:
            condition = self.parse_expression(condition_str, parameters, paramExpressions)
            parsed_conditions.append(condition)
        return parsed_conditions

    def parse_effects(self, effectsList: List, parameters: List[str],
                      paramExpressions: List[ParameterNode]) -> List[Update]:
        updates = []
        for effect in effectsList:
            if isinstance(effect, str):
                update = self.parse_effect_line(effect, parameters, paramExpressions)
                if update is not None:
                    updates.append(update)
            elif isinstance(effect, dict):
                block_updates = self.parse_effects_block(effect, parameters.copy(), paramExpressions.copy())
                updates.extend(block_updates)
            else:
                raise ValueError(f"Invalid effect: {effect}")
        return updates


    def parse_effect_line(self, effect: str, parameters: List[str],
                          paramExpressions: List[ParameterNode]) -> Update:
        effect = effect.strip()
        if effect.startswith('NewVal'):
            # Handle 'NewVal' statements
            _, rest = effect.split('NewVal', 1)
            rest = rest.strip()
            if ':' in rest:
                variable_name, expr_str = rest.split(':', 1)
                variable_name = variable_name.strip()
                expr_str = expr_str.strip()
                # Parse the expression
                expr_node = self.parse_expression(expr_str, parameters, paramExpressions)
                # Create a new ParameterNode with the expression's value and the expressionNode
                param_index = len(paramExpressions)
                new_param_node = NewValParameterNode(param_index)
                # Extend parameters and paramExpressions
                parameters.append(variable_name)
                paramExpressions.append(new_param_node)
                return ParameterUpdate(new_param_node, expr_node)
            else:
                raise SyntaxError(f"Invalid New Val syntax: {effect}")
        elif ' remove' in effect:
            entity_name, rest = effect.split('remove', 1)
            entity_name = entity_name.strip()
            rest = rest.strip()
            if ':' in rest:
                _, expr_str = rest.split(':', 1)
                expr_str = expr_str.strip()
                expr_node = self.parse_expression(expr_str, parameters, paramExpressions)
                entity_index = self.parsedEntities.get(entity_name)[0]
                if entity_index is None:
                    raise ValueError(f"Unknown entity: {entity_name}")
                return ExpressionRemoveUpdate(entity_index, expr_node)
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
                    expr_nodes = [self.parse_expression(expr_str, parameters, paramExpressions)
                                  for expr_str in expr_strs]
                    entity_index = self.parsedEntities.get(entity_name)[0]
                    if entity_index is None:
                        raise ValueError(f"Unknown entity: {entity_name}")
                    return ExpressionAddUpdate(entity_index, *expr_nodes)
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
                expr_id = self.parse_expression(expr_id_str, parameters, paramExpressions)
                # Parse expressions inside parentheses
                if expr_list_str.startswith('(') and expr_list_str.endswith(')'):
                    expr_list_str = expr_list_str[1:-1].strip()
                    expr_strs = [s.strip() for s in expr_list_str.split(',')]
                    expr_nodes = [self.parse_expression(expr_str, parameters, paramExpressions)
                                  for expr_str in expr_strs]
                    entity_index = self.parsedEntities.get(entity_name)[0]
                    if entity_index is None:
                        raise ValueError(f"Unknown entity: {entity_name}")
                    return ExpressionReplaceUpdate(entity_index, expr_id, *expr_nodes)
                else:
                    raise SyntaxError(f"Invalid replace syntax: {effect}")
        else:
            # Simple update
            return self.parse_update(effect, parameters, paramExpressions)

    def parse_effects_block(self, effect: dict, parameters: List[str],
                            paramExpressions: List[ParameterNode]) -> List[Update]:
        updates = []
        block_name = effect.get('name')
        if block_name == 'case':
            condition_str = effect['condition']
            condition = self.parse_expression(condition_str, parameters, paramExpressions)
            segment = effect['segment']
            updates_segment = self.parse_effects(segment, parameters, paramExpressions)
            else_segment = effect.get('else segment', [])
            updates_else = self.parse_effects(else_segment, parameters, paramExpressions)
            updates.append(CaseUpdate(condition, updates_segment, updates_else))
        elif block_name == 'all':
            entityIndex = self.parsedEntities[effect['entity']][0]
            parameter_name = effect['parameter']
            parameter_node = ValueParameterNode(len(paramExpressions))
            # Extend parameters and paramExpressions for the new scope
            parameters.append(parameter_name)
            paramExpressions.append(parameter_node)
            segment = effect['segment']
            condition_str = effect.get('condition')
            if condition_str:
                condition = self.parse_expression(condition_str, parameters, paramExpressions)
            else:
                condition = None
            updates_segment = self.parse_effects(segment, parameters, paramExpressions)
            updates.append(AllUpdate(entityIndex, parameter_node, updates_segment, condition))
        else:
            raise ValueError(f"Unknown block name: {block_name}")

        return updates

    def parse_update(self, update_str: str, parameters: List[str], paramExpressions: List[ParameterNode]) -> Update:
        if ':' not in update_str:
            raise SyntaxError(f"Invalid update syntax: {update_str}")
        lhs_str, rhs_str = map(str.strip, update_str.split(':', 1))
        # Parse LHS (should result in ValueNode or ValueIndexNode)
        lhs_parser = ExpressionParser(lhs_str, parameters, paramExpressions, self.parsedEntities)
        lhs_node = lhs_parser.parse_primary()
        # Parse RHS as an expression
        rhs_node = self.parse_expression(rhs_str, parameters, paramExpressions)
        # Create Update object
        if isinstance(lhs_node, ValueNode):
            return ExpressionUpdate(lhs_node.variableName, lhs_node.expression, rhs_node)
        elif isinstance(lhs_node, ValueIndexNode):
            return ExpressionIndexUpdate(lhs_node.variableName, lhs_node.index, rhs_node)
        elif isinstance(lhs_node, NewValParameterNode):
            return ParameterUpdate(lhs_node, rhs_node)
        else:
            raise SyntaxError(f"Invalid LHS in update: {lhs_str}")

    def parse_cost(self, cost_list: List, parameters: List[str],
                   paramExpressions: List[ParameterNode]) -> ExpressionNode:
        if not cost_list:
            return ConstNode(0)  # Default cost if none provided
        # The last line is the cost expression
        cost_expr_str = cost_list[-1]
        # Parse the cost expression
        # All preceding lines are updates
        updates_list = cost_list[:-1]
        # Check if there are updates in updates_list, return costExpression if not
        if not updates_list:
            costExpression = self.parse_expression(cost_expr_str, parameters, paramExpressions)
            return costExpression
        # Parse updates (may include 'NewVal' declarations)
        updates = self.parse_effects(updates_list, parameters, paramExpressions)
        costExpression = self.parse_expression(cost_expr_str, parameters, paramExpressions)
        # Return a structure that includes updates and the cost expression
        return CostExpression(updates, costExpression)