from CARRI.action import ActionProducer, ActionStringRepresentor
class Simulator:
    def __init__(self, problem, actionGenerators, evnSteps, iterStep, entities):
        self.problem = problem
        self.ActionProducer = ActionProducer(actionGenerators)
        self.actionStringRepresentor = ActionStringRepresentor(actionGenerators)
        self.action_generators = actionGenerators
        self.evnSteps = evnSteps
        self.iterStep = iterStep
        self.entities = entities
        self.current_state = problem.initState.copy()

    def generate_all_valid_actions_seperatly(self):
        """
        Generate all valid actions separately for each vehicle given the current state of the problem.
        :return: Dictionary of vehicles with each entity's valid actions.
        """
        valid_actions = {}
        for vehicle_type, entity_info in self.entities.items():
            entity_type = entity_info[0]
            if entity_info[1] != 'Vehicle':
                continue
            entity_ids = self.problem.get_entity_ids(self.current_state, entity_type)
            entity_actions = {}
            for entity_id in entity_ids:
                actions = self.ActionProducer.produce_actions(self.problem, self.current_state, entity_id, entity_type)
                entity_actions[entity_id] = actions
            valid_actions[vehicle_type] = entity_actions
        return valid_actions

    def generate_all_valid_actions_recursive(self, all_valid_actions, vehicle_keys, partial_assignment=None):
        """
        Generate a complete assignment of actions recursively, choosing one valid action for each vehicle instance.
        Ensure that all chosen actions are compatible with each other.
        :param all_valid_actions: Dictionary of valid actions for each vehicle type and entity.
        :param vehicle_keys: List of vehicle types to be processed.
        :param partial_assignment: The partial assignment of actions validated so far.
        :return: List of valid combinations of actions for all entities.
        """
        if partial_assignment is None:
            partial_assignment = []

        if not vehicle_keys:
            return [partial_assignment]

        valid_combinations = []
        current_vehicle_type = vehicle_keys[0]
        entity_actions = all_valid_actions[current_vehicle_type]
        entity_ids = list(entity_actions.keys())

        def recurse_entity_actions(entity_index, current_partial_assignment):
            if entity_index >= len(entity_ids):
                valid_combinations.extend(self.generate_all_valid_actions_recursive(all_valid_actions, vehicle_keys[1:], current_partial_assignment))
                return

            current_entity_id = entity_ids[entity_index]
            actions_list = entity_actions[current_entity_id]

            for action in actions_list:
                if self.validate_action(action):
                    recurse_entity_actions(entity_index + 1, current_partial_assignment + [action])

        recurse_entity_actions(0, partial_assignment)
        return valid_combinations

    def generate_all_valid_actions(self):
        """
        Wrapper for generating all valid action combinations using the recursive method.
        :return: List of valid combinations of actions for all entities.
        """
        all_valid_actions = self.generate_all_valid_actions_seperatly()
        vehicle_keys = list(all_valid_actions.keys())
        all_combinations = self.generate_all_valid_actions_recursive(all_valid_actions, vehicle_keys)
        return all_combinations

    def validate_action(self, action: Action):
        """
        Validate an action by checking its preconditions against the current state.
        :param action: The action to be validated.
        :return: True if the action is valid, False otherwise.
        """
        try:
            is_valid = action.validate(self.problem, self.current_state)
            print(f"Validation for action {action}: {is_valid}")
            return is_valid
        except KeyError as e:
            print(f"KeyError during validation of action {action}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during validation of action {action}: {e}")
            return False

    def revalidate_action(self, problem, state, action):
        """
        Revalidate action, checking for possibly conflicting actions.
        """
        # Placeholder for revalidation logic, which checks for conflicts.
        # For now, assuming actions are always valid for simplicity.
        for precondition in action['conflicting preconditions']:
            if not self.evaluate_condition(precondition, state, problem):
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
        # Placeholder for evaluating logical conditions (preconditions).
        # In a real implementation, you would parse the condition and check against the state.
        return True

    def apply_effect(self, problem, state, effect):
        """
        Apply an effect to the state.
        """
        # Placeholder for applying effects to the state.
        # This would modify the state based on the effect.
        pass