from copy import copy
from CARRI.action import ActionProducer, ActionStringRepresentor, ActionGenerator, Action, EnvStep, Step
from CARRI.problem import Problem
from CARRI.state import State
from collections import deque
from typing import List, Tuple, Dict

class Simulator:
    def __init__(self, problem: Problem, actionGenerators: List[ActionGenerator],
                 envSteps: List[EnvStep], iterStep: Step, entities: Dict[str, Tuple]):
        self.problem = problem
        self.ActionProducer = ActionProducer(actionGenerators)
        self.actionStringRepresentor = ActionStringRepresentor(actionGenerators)
        self.action_generators = actionGenerators
        self.envSteps = envSteps
        self.iterStep = iterStep
        self.entities = entities
        self.current_state = problem.copyState(problem.initState)
        self.vehicle_keys = self.problem.vehicleEntities

    def __copy__(self):
        # Create a new Simulator instance with shallow copies where appropriate
        new_simulator = type(self)(
            problem=self.problem.__copy__(),  # Assuming Problem has its own __copy__ method
            actionGenerators=self.action_generators.copy(),  # Shallow copy of the list
            envSteps=self.envSteps.copy(),  # Shallow copy of the list
            iterStep=self.iterStep,  # Assuming Step is immutable or can be shared
            entities=self.entities.copy()  # Shallow copy of the dict
        )
        # Assign other attributes that should not be deeply copied
        new_simulator.ActionProducer = self.ActionProducer  # Assuming ActionProducer is stateless
        new_simulator.actionStringRepresentor = self.actionStringRepresentor
        new_simulator.current_state = self.current_state.__copy__()  # Shallow copy of State
        new_simulator.vehicle_keys = copy(self.vehicle_keys)  # Shallow copy if it's a list or similar
        return new_simulator

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
            for entityId in self.problem.get_entity_ids(state, vehicleEntityType):
                actions = self.ActionProducer.produce_actions(self.problem, state,
                                                              entityId, vehicleEntityType)
                entityActions[entityId] = actions
            valid_actions[vehicleEntityType] = entityActions
        return valid_actions

    def generate_all_valid_partial_seperate_actions(self, state: State, vehicleType: int, partialVehciles):
        valid_actions = {}
        for entityId in partialVehciles:
            actions = self.ActionProducer.produce_actions(self.problem, state,
                                                              entityId, vehicleType)
            valid_actions[entityId] = actions
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

    def validate_Transition_shallow(self, state, transition):
        """
        This validation method is not as reliable as thought.
        It doesn't take into consideration vehicle's action at the same time,
        For example in the domain of Drones and Trucks - it won't take
        into consideration one drone existing and another one boarding instead.
        """
        for action in transition:
            if not action.validate(self.problem, state):
                return False
        return True

    def validate_Transition(self, state, transition):
        state = state.__copy__()
        for j, action in enumerate(transition):
            if not action.validate(self.problem, state):
                print('action ', j)
                return False
            action.apply(self.problem, state)
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
            raise Exception(f"KeyError while applying action {action}: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error while applying action {action}: {e}")


    def generate_partial_successors(self, state: State, vehicleType: int, vehicleIds: Tuple):
        currentQueue = deque()
        currentQueue.append((state, [], 0))
        validSeperates = self.generate_all_valid_partial_seperate_actions(state, vehicleType, vehicleIds)

        for vehicleId, vehicleIdActions in validSeperates.items():
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

    def apply_full_Transition(self, state, cost, transition):
        for action in transition:
            action.apply(self.problem, state)
            cost += action.get_cost(self.problem, state)
        for envStep in self.envSteps:
            envStep.apply(self.problem, state)
            cost += envStep.get_cost(self.problem, state)
        return state, cost


    def addItems(self, entityName, entityList):
        entity_index = self.problem.entities[entityName][0]
        for itemImdex, params in entityList.items():
            self.problem.add_entity(self.current_state, entity_index, *params)
        return self.current_state

    def apply_iter_step(self, state, iterationItems):
        self.iterStep.apply(self.problem, state)
        for entityName, entities in iterationItems.items():
            entityType = self.entities[entityName][0]
            for itemParams in entities:
                self.problem.add_entity(state, entityType, *itemParams)
        return state