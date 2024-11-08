from CARRI.action import ActionProducer, ActionStringRepresentor, Action, EnvStep
from CARRI.problem import Problem
from collections import deque
from typing import List

class Simulator:
    def __init__(self, problem: Problem, actionGenerators, envSteps: List[EnvStep], iterStep, entities):
        self.problem = problem
        self.ActionProducer = ActionProducer(actionGenerators)
        self.actionStringRepresentor = ActionStringRepresentor(actionGenerators)
        self.action_generators = actionGenerators
        self.envSteps = envSteps
        self.iterStep = iterStep
        self.entities = entities
        self.current_state = problem.copyState(problem.initState)
        self.vehicle_keys = self.problem.vehicleEntities

    def get_state(self):
        return self.problem.copyState(self.current_state)

    def generate_all_valid_seperate_actions(self, state):
        """
        Generate all valid actions separately for each vehicle given the current state of the problem.
        :return: Dictionary of vehicles with each entity's valid actions.
        """
        valid_actions = {}
        # New thing from problem: vehicleEntities
        for vehicleEntityType in self.problem.vehicleEntities:
            entityActions = {}
            for entityId in self.problem.get_entity_ids(self.current_state, vehicleEntityType):
                actions = self.ActionProducer.produce_actions(self.problem, state,
                                                              entityId, vehicleEntityType)
                entityActions[entityId] = actions
            valid_actions[vehicleEntityType] = entityActions
        return valid_actions

    def generate_all_valid_partial_seperate_actions(self, state, partialVehciles):
        valid_actions = {}
        # New thing from problem: vehicleEntities
        for vehicleEntityType, vehicleEntityIds in zip(self.problem.vehicleEntities, partialVehciles):
            entityActions = {}
            for entityId in vehicleEntityIds:
                actions = self.ActionProducer.produce_actions(self.problem, state,
                                                              entityId, vehicleEntityType)
                entityActions[entityId] = actions
            valid_actions[vehicleEntityType] = entityActions
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
        ###Change!!!
        all_valid_actions = self.generate_all_valid_seperate_actions(self.problem.initState)
        vehicle_keys = self.problem.vehicleEntities
        all_combinations = self.generate_all_valid_actions_recursive(all_valid_actions, vehicle_keys)
        return all_combinations

    def validate_Transition_state(self, state, transition):
        for action in transition:
            if not action.validate(self.problem, state):
                return False
        return True

    def validate_Transition(self, transition):
        for action in transition:
            if not self.validate_action(action):
                return False
        return True

    def validate_action(self, action: Action):
        """
        Validate an action by checking its preconditions against the current state.
        :param action: The action to be validated.
        :return: True if the action is valid, False otherwise.
        """
        try:
            is_valid = action.validate(self.problem, self.current_state)
            #print(f"Validation for action {action}: {is_valid}")
            return is_valid
        except KeyError as e:
            #print(f"KeyError during validation of action {action}: {e}")
            return False
        except Exception as e:
            #print(f"Unexpected error during validation of action {action}: {e}")
            return False

    def revalidate_action(self, state, action):
        """
        Apply the action's effects to the given state.
        :param action: The action to be applied.
        :param state: The state on which the action is applied.
        :return: None
        """
        try:
            #print(f"Applying action: {action}")  # Debug statement
            action.apply(self.problem, state)
            #print(f"Action applied successfully: {action}")
        except KeyError as e:
            print(f"KeyError while applying action {action}: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error while applying action {action}: {e}")
            raise

    def generate_partial_successors(self, state, vehicleIds: List):
        currentQueue = deque()
        currentQueue.append((state, [], 0))
        validSeperates = self.generate_all_valid_partial_seperate_actions(state, vehicleIds)

        for vehicleType, vehicleTypeActions in validSeperates.items():
            for vehicleId, vehicleIdActions in vehicleTypeActions.items():

                nextQueue = deque()
                while currentQueue:
                    currentState, transition, cost = currentQueue.pop()
                    for action in vehicleIdActions:
                        if action.reValidate(self.problem, currentState):
                            nextState = currentState.__copy__()
                            action.apply(self.problem, nextState)
                            nextTransition = transition + [action]
                            nextCost = cost + action.get_cost(self.problem, nextState)
                            nextQueue.append((nextState, nextTransition, nextCost))

                currentQueue = nextQueue
        return currentQueue
    def applyEnvSteps(self, queue):
        # No envStep case
        if not self.envSteps:
            return ((item[0], item[1], item[2], 0) for item in queue)

        # Process each item in the deque by index
        for i in range(len(queue)):
            # Initialize the tuple elements
            state, transition, cost = queue[i]
            envCost = 0
            # Apply each envStep to afterEnvState and accumulate envCost
            for envStep in self.envSteps:
                envStep.apply(self.problem, state)
                envCost += envStep.get_cost(self.problem, state)

            # Replace the tuple in-place with the updated values
            queue[i] = (state, transition, cost, envCost)

        return queue
    def generate_successors(self, state):
        currentQueue = deque()
        currentQueue.append((state, [], 0))
        validSeperates = self.generate_all_valid_seperate_actions(state)

        for vehicleType, vehicleTypeActions in validSeperates.items():
            for vehicleId, vehicleIdActions in vehicleTypeActions.items():

                nextQueue = deque()
                while currentQueue:
                    currentState, transition, cost = currentQueue.pop()
                    for action in vehicleIdActions:
                        if action.reValidate(self.problem, currentState):
                            nextState = currentState.__copy__()
                            action.apply(self.problem, nextState)
                            nextTransition = transition + [action]
                            nextCost = cost + action.get_cost(self.problem, nextState)
                            nextQueue.append((nextState, nextTransition, nextCost))

                currentQueue = nextQueue

        for envStep in self.envSteps:
            # Iterate through each item in the deque by index
            for i in range(len(currentQueue)):
                state, transition, cost = currentQueue[i]

                # Apply the envStep function to the state and add to the cost
                envStep.apply(self.problem, state)
                cost += envStep.get_cost(self.problem, state)  # Adjust according to envStep logic
                # Replace the tuple in-place
                currentQueue[i] = (state, transition, cost)

        return currentQueue

    def advance_state(self, action: Action):
        """
        Advance the state by applying the given action, updating the current state.
        :param action: The action to be applied to advance the state.
        :return: None
        """
        cost = 0
        if self.validate_action(action):
            action.apply(self.problem, self.current_state)
            return action.get_cost(self.problem, self.current_state)

        else:
            raise ValueError("Invalid action attempted to be applied to the current state.")

    def apply_environment_steps(self, state):
        cost = 0
        state = state.__copy__()
        for envStep in self.envSteps:
            envStep.apply(self.problem, state)
            cost += envStep.get_cost(self.problem, state)
        return state, cost

    def apply_transition(self, state, transition):
        cost = 0
        state = state.__copy__()
        for action in transition:
            action.apply(self.problem, state)
            cost += action.get_cost(self.problem, state)
        return state, cost

    def addItems(self, entityName, entityList):
        entity_index = self.problem.entities[entityName][0]
        for itemImdex, param in entityList.items():
            self.problem.add_entity(self.current_state, entity_index, itemImdex, param)
        return self.current_state