from CARRIAction import ActionProducer, ActionStringRepresentor, ActionGenerator, Action, ValueParameterNode
from CARRIRealm import CARRIProblem
from typing import List, Dict
from collections import defaultdict
import copy

class CARRISimulator:
    def __init__(self, problem: CARRIProblem, actionGenerators: List[ActionGenerator], evnSteps, iterStep, entities):
        """
        :param problem: The problem instance containing initial state and data.
        :param actionGenerators: List of action generators that define how actions are produced.
        :param evnSteps: Environment steps that need to be applied each iteration.
        :param iterStep: Iteration step count for simulation advancement.
        :param entities: List of entities present in the simulation.
        """
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

    def apply_action(self, action: Action, state):
        """
        Apply the action's effects to the given state.
        :param action: The action to be applied.
        :param state: The state on which the action is applied.
        :return: None
        """
        try:
            print(f"Applying action: {action}")  # Debug statement
            action.apply(self.problem, state)
            print(f"Action applied successfully: {action}")
        except KeyError as e:
            print(f"KeyError while applying action {action}: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error while applying action {action}: {e}")
            raise

    def generate_successor_states(self):
        """
        Generate all possible successor states given the current state by applying valid actions.
        :return: List of successor states.
        """
        successor_states = []
        valid_action_combinations = self.generate_all_valid_actions()

        for actions in valid_action_combinations:
            new_state = copy.deepcopy(self.current_state)  # Use deepcopy to ensure state isolation
            try:
                for action in actions:
                    self.apply_action(action, new_state)
                successor_states.append(new_state)
            except KeyError as e:
                print(f"KeyError encountered while applying actions: {e}")
                print(f"Problem with action: {action}")
                continue
            except Exception as e:
                print(f"Unexpected error: {e}")
                print(f"Problem with action: {action}")
                continue

        return successor_states

    def advance_state(self, action: Action):
        """
        Advance the state by applying the given action, updating the current state.
        :param action: The action to be applied to advance the state.
        :return: None
        """
        if self.validate_action(action):
            self.apply_action(action, self.current_state)
        else:
            raise ValueError("Invalid action attempted to be applied to the current state.")

    def apply_environment_steps(self):
        """
        Apply environment steps to the current state of the problem.
        :return: None
        """
        for step in self.evnSteps:
            try:
                step.apply(self.problem, self.current_state)
            except Exception as e:
                print(f"Error while applying environment step: {e}")
                continue
