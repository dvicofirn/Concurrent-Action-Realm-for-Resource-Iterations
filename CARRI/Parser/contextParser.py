from CARRI.expression import *
from CARRI.Parser.expressionParser import ExpressionParser

class ContextParser:
    """Parses different segments (conditions, effects, cost) within a given context, utilizing parameters and entities."""

    def __init__(self, parameters, paramExpressions, parsedEntities):
        """Initialize the ContextParser with parameters, parameter expressions, and parsed entities."""
        self.parameters = parameters
        self.paramExpressions = paramExpressions
        self.parsedEntities = parsedEntities

    def parse(self, segment: List[str], type: str):
        """Pass the segment to a matching parsing function based on the type."""
        if type == "conditions":
            return self.parse_conditions(segment, self.parameters, self.paramExpressions)
        elif type == "effects":
            return self.parse_effects(segment, self.parameters.copy(), self.paramExpressions.copy())
        elif type == "cost":
            return self.parse_cost(segment, self.parameters.copy(), self.paramExpressions.copy())

    def parse_expression(self, expression: str, parameters: List[str],
                         paramExpressions: List[ParameterNode]) -> ExpressionNode:
        """Parse an expression string into an ExpressionNode."""
        parser = ExpressionParser(expression, parameters, paramExpressions, self.parsedEntities)
        exprNode = parser.parse_expression()
        return exprNode

    def parse_conditions(self, conditions: List[str], parameters: List[str],
                         paramExpressions: List[ParameterNode]) -> List[ExpressionNode]:
        """Parse a list of condition strings into a list of ExpressionNodes."""
        parsedConditions = []
        for conditionStr in conditions:
            condition = self.parse_expression(conditionStr, parameters, paramExpressions)
            parsedConditions.append(condition)
        return parsedConditions

    def parse_effects(self, effectsList: List, parameters: List[str],
                      paramExpressions: List[ParameterNode]) -> List[Update]:
        """Parse a list of effects into a list of Update objects."""
        updates = []
        for effect in effectsList:
            if isinstance(effect, str):
                update = self.parse_effect_line(effect, parameters, paramExpressions)
                if update is not None:
                    updates.append(update)
            elif isinstance(effect, dict):
                blockUpdates = self.parse_effects_block(effect, parameters.copy(), paramExpressions.copy())
                updates.extend(blockUpdates)
            else:
                raise ValueError(f"Invalid effect: {effect}")
        return updates

    def parse_effect_line(self, effect: str, parameters: List[str],
                          paramExpressions: List[ParameterNode]) -> Update:
        """Parse a single effect line into an Update object."""
        effect = effect.strip()
        if effect.startswith('NewVal'):
            # Handle 'NewVal' statements
            _, rest = effect.split('NewVal', 1)
            rest = rest.strip()
            if ':' in rest:
                variableName, exprStr = rest.split(':', 1)
                variableName = variableName.strip()
                exprStr = exprStr.strip()
                # Parse the expression
                exprNode = self.parse_expression(exprStr, parameters, paramExpressions)
                # Create a new ParameterNode with the expression's value and the expressionNode
                param_index = len(paramExpressions)
                newParamNode = NewValParameterNode(param_index)
                # Extend parameters and paramExpressions
                parameters.append(variableName)
                paramExpressions.append(newParamNode)
                return ParameterUpdate(newParamNode, exprNode)
            else:
                raise SyntaxError(f"Invalid NewVal syntax: {effect}")
        elif ' remove' in effect:
            entityName, rest = effect.split('remove', 1)
            entityName = entityName.strip()
            rest = rest.strip()
            if ':' in rest:
                _, exprStr = rest.split(':', 1)
                exprStr = exprStr.strip()
                exprNode = self.parse_expression(exprStr, parameters, paramExpressions)
                entityIndex = self.parsedEntities.get(entityName)[0]
                if entityIndex is None:
                    raise ValueError(f"Unknown entity: {entityName}")
                return ExpressionRemoveUpdate(entityIndex, exprNode)
            else:
                raise SyntaxError(f"Invalid remove syntax: {effect}")
        elif ' add' in effect:
            entityName, rest = effect.split('add', 1)
            entityName = entityName.strip()
            rest = rest.strip()
            if ':' in rest:
                _, exprListStr = rest.split(':', 1)
                exprListStr = exprListStr.strip()
                # Parse expressions inside parentheses
                if exprListStr.startswith('(') and exprListStr.endswith(')'):
                    exprListStr = exprListStr[1:-1].strip()
                    exprStrs = [s.strip() for s in exprListStr.split(',')]
                    exprNodes = [self.parse_expression(exprStr, parameters, paramExpressions)
                                 for exprStr in exprStrs]
                    entityIndex = self.parsedEntities.get(entityName)[0]
                    if entityIndex is None:
                        raise ValueError(f"Unknown entity: {entityName}")
                    return ExpressionAddUpdate(entityIndex, *exprNodes)
                else:
                    raise SyntaxError(f"Invalid add syntax: {effect}")
            else:
                raise SyntaxError(f"Invalid add syntax: {effect}")
        elif ' replace' in effect:
            entityName, rest = effect.split('replace', 1)
            entityName = entityName.strip()
            rest = rest.strip()
            if ':' in rest:
                exprIdStr, exprListStr = rest.split(':', 1)
                exprIdStr = exprIdStr.strip()
                exprListStr = exprListStr.strip()
                # Parse the ID expression
                exprId = self.parse_expression(exprIdStr, parameters, paramExpressions)
                # Parse expressions inside parentheses
                if exprListStr.startswith('(') and exprListStr.endswith(')'):
                    exprListStr = exprListStr[1:-1].strip()
                    exprStrs = [s.strip() for s in exprListStr.split(',')]
                    exprNodes = [self.parse_expression(exprStr, parameters, paramExpressions)
                                 for exprStr in exprStrs]
                    entityIndex = self.parsedEntities.get(entityName)[0]
                    if entityIndex is None:
                        raise ValueError(f"Unknown entity: {entityName}")
                    return ExpressionReplaceUpdate(entityIndex, exprId, *exprNodes)
                else:
                    raise SyntaxError(f"Invalid replace syntax: {effect}")
            else:
                raise SyntaxError(f"Invalid replace syntax: {effect}")
        else:
            # Simple update
            return self.parse_update(effect, parameters, paramExpressions)

    def parse_effects_block(self, effect: dict, parameters: List[str],
                            paramExpressions: List[ParameterNode]) -> List[Update]:
        """Parse an effect block (e.g., case, all, repeat) into a list of Update objects."""
        updates = []
        blockName = effect.get('name')
        if blockName == 'case':
            conditionStr = effect['condition']
            condition = self.parse_expression(conditionStr, parameters, paramExpressions)
            segment = effect['segment']
            updatesSegment = self.parse_effects(segment, parameters, paramExpressions)
            elseSegment = effect.get('else segment', [])
            updatesElse = self.parse_effects(elseSegment, parameters, paramExpressions)
            updates.append(CaseUpdate(condition, updatesSegment, updatesElse))

        elif blockName == 'all':
            entityIndex = self.parsedEntities[effect['entity']][0]
            parameterName = effect['parameter']
            parameterNode = ValueParameterNode(len(paramExpressions))
            # Extend parameters and paramExpressions for the new scope
            parameters.append(parameterName)
            paramExpressions.append(parameterNode)
            segment = effect['segment']
            conditionStr = effect.get('condition')
            if conditionStr:
                condition = self.parse_expression(conditionStr, parameters, paramExpressions)
            else:
                condition = None
            updatesSegment = self.parse_effects(segment, parameters, paramExpressions)
            updates.append(AllUpdate(entityIndex, parameterNode, updatesSegment, condition))

        elif blockName == 'repeat':
            conditionStr = effect['condition']
            condition = self.parse_expression(conditionStr, parameters, paramExpressions)
            segment = effect['segment']
            updatesSegment = self.parse_effects(segment, parameters, paramExpressions)
            updates.append(RepeatUpdate(condition, updatesSegment))
        else:
            raise ValueError(f"Unknown block name: {blockName}")

        return updates

    def parse_update(self, updateStr: str, parameters: List[str], paramExpressions: List[ParameterNode]) -> Update:
        """Parse an update string into an Update object."""
        if ':' not in updateStr:
            raise SyntaxError(f"Invalid update syntax: {updateStr}")
        lhsStr, rhsStr = map(str.strip, updateStr.split(':', 1))
        # Parse LHS (should result in ValueNode or ValueIndexNode)
        lhsParser = ExpressionParser(lhsStr, parameters, paramExpressions, self.parsedEntities)
        lhsNode = lhsParser.parse_primary()
        # Parse RHS as an expression
        rhsNode = self.parse_expression(rhsStr, parameters, paramExpressions)
        # Create Update object
        if isinstance(lhsNode, ValueNode):
            return ExpressionUpdate(lhsNode.variableName, lhsNode.expression, rhsNode)
        elif isinstance(lhsNode, ValueIndexNode):
            return ExpressionIndexUpdate(lhsNode.variableName, lhsNode.index, rhsNode)
        elif isinstance(lhsNode, NewValParameterNode):
            return ParameterUpdate(lhsNode, rhsNode)
        else:
            raise SyntaxError(f"Invalid LHS in update: {lhsStr}")

    def parse_cost(self, costList: List, parameters: List[str],
                   paramExpressions: List[ParameterNode]) -> ExpressionNode:
        """Parse the cost segment into an ExpressionNode, handling any updates if present."""
        if not costList:
            return ConstNode(0)  # Default cost if none provided
        # The last line is the cost expression
        costExprStr = costList[-1]
        # All preceding lines are updates
        updatesList = costList[:-1]
        # If there are no updates, parse and return the cost expression directly
        if not updatesList:
            costExpression = self.parse_expression(costExprStr, parameters, paramExpressions)
            return costExpression
        # Parse updates (may include 'NewVal' declarations)
        updates = self.parse_effects(updatesList, parameters, paramExpressions)
        costExpression = self.parse_expression(costExprStr, parameters, paramExpressions)
        # Return a structure that includes updates and the cost expression
        return CostExpression(updates, costExpression)
