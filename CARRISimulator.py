from CARRIAction import ActionProducer, ActionStringRepresentor, Action

class CARRISimulator:
    def __init__(self, problem, actionGenerators, evnSteps, iterStep, entities):
        self.problem = problem
        self.actionProducer = ActionProducer(actionGenerators)
        self.actionStringRepresentor = ActionStringRepresentor(actionGenerators)
        self.evnSteps = evnSteps
        self.iterSteps = iterStep
        self.entities = entities

    def validate_action(self, problem, state, action):
        """
        Validate that all preconditions of the action are met in the given state.
        """
        for precondition in action['regular preconditions']:
            if not self.evaluate_condition(problem, state, precondition):
                return False
        for precondition in action['conflicting preconditions']:
            if not self.evaluate_condition(problem, state, precondition):
                return False
        return True

    def revalidate_action(self, problem, state, action):
        """
        Revalidate action, checking for possibly conflicting actions.
        """
        for precondition in action['conflicting preconditions']:
            if not self.evaluate_condition(problem, state, precondition):
                return False
        return True

    def apply_action(self, problem, state, action):
        """
        Apply the action's effects to the state.
        """
        for effect in action['effects']:
            self.apply_effect(problem, state, effect)

    def evaluate_condition(self, problem, state, condition):
        """
        Evaluate a condition against the state and problem.
        """
        # Implement logic to evaluate different types of conditions
        condition_type = condition['type']
        if condition_type == 'comparison':
            return self.evaluate_comparison(problem, state, condition)
        elif condition_type == 'existence':
            return self.evaluate_existence(problem, state, condition)
        # Add additional condition types as needed
        return False

    def evaluate_comparison(self, problem, state, condition):
        """
        Evaluate a comparison condition (e.g., >, <, ==) between variables or constants.
        """
        left = self.resolve_expression(problem, state, condition['left'])
        right = self.resolve_expression(problem, state, condition['right'])
        operator = condition['operator']

        if operator == '==':
            return left == right
        elif operator == '!=':
            return left != right
        elif operator == '>':
            return left > right
        elif operator == '<':
            return left < right
        elif operator == '>=':
            return left >= right
        elif operator == '<=':
            return left <= right
        return False

    def evaluate_existence(self, problem, state, condition):
        """
        Evaluate whether a specific entity exists in the state or problem context.
        """
        entity = condition['entity']
        if entity in state['entities']:
            return True
        return False

    def resolve_expression(self, problem, state, expression):
        """
        Resolve an expression, which could be a variable, constant, or computed value.
        """
        if isinstance(expression, str):
            # Resolve variable names to values in the state
            return state.get(expression, 0)
        elif isinstance(expression, (int, float)):
            return expression
        # Add logic for more complex expressions if needed
        return 0

    def apply_effect(self, problem, state, effect):
        """
        Apply an effect to the state.
        """
        effect_type = effect['type']
        if effect_type == 'assignment':
            self.apply_assignment(problem, state, effect)
        elif effect_type == 'increment':
            self.apply_increment(problem, state, effect)
        # Add additional effect types as needed

    def apply_assignment(self, problem, state, effect):
        """
        Apply an assignment effect, setting a variable to a value.
        """
        target = effect['target']
        value = self.resolve_expression(problem, state, effect['value'])
        state[target] = value

    def apply_increment(self, problem, state, effect):
        """
        Apply an increment effect, increasing or decreasing a variable's value.
        """
        target = effect['target']
        increment_value = self.resolve_expression(problem, state, effect['value'])
        if target in state:
            state[target] += increment_value
        else:
            state[target] = increment_value

    def simulate(self, iterations):
        """
        Simulate the environment over a series of iterations, applying actions and updating the state.
        """
        current_state = self.problem.initState.copy()
        for i in range(iterations):
            print(f"Iteration {i + 1}:")
            for action in self.action_generators:
                if self.validate_action(self.problem, current_state, action):
                    self.apply_action(self.problem, current_state, action)
            self.apply_environment_steps(current_state)
            print(f"State after iteration {i + 1}: {current_state}")

    def apply_environment_steps(self, state):
        """
        Apply environment steps to the current state, which may include dynamic changes.
        """
        for step in self.env_steps:
            self.apply_effect(self.problem, state, step)

        # Apply iteration step changes if necessary
        for effect in self.iter_step:
            self.apply_effect(self.problem, state, effect)


