from copy import copy
from CARRI.action import ActionProducer, ActionStringRepresentor, ActionGenerator, Action, EnvStep, Step
from CARRI.problem import Problem
from CARRI.state import State
from collections import deque
from typing import List, Tuple, Dict

class Simulator:
    """
    Simulator class that manages the simulation of actions, environment steps, and iterations
    within the CARRI framework. It interfaces with the Problem, State, and Action classes to
    generate and apply actions, handle state transitions, and simulate the environment.
    """

    def __init__(self, problem: Problem, actionGenerators: List[ActionGenerator],
                 envSteps: List[EnvStep], iterStep: Step, entities: Dict[str, Tuple]):
        """
        Initialize the Simulator with the given problem definition, action generators,
        environment steps, iteration step, and entities.

        Args:
            problem (Problem): The problem instance containing the initial state and problem definition.
            actionGenerators (List[ActionGenerator]): List of action generators for producing actions.
            envSteps (List[EnvStep]): List of environment steps to apply at each iteration.
            iterStep (Step): The iteration step to apply during simulation.
            entities (Dict[str, Tuple]): Dictionary of entity names to their corresponding tuples.
        """
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
        """
        Create a copy of the Simulator instance.

        Returns:
            Simulator: A new instance of Simulator with copied attributes.
        """
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
        """
        Get a copy of the current state.

        Returns:
            State: A copy of the current state.
        """
        return self.problem.copyState(self.current_state)

    def generate_all_valid_seperate_actions(self, state):
        """
        Generate all valid actions separately for each vehicle given the current state of the problem.

        Args:
            state (State): The current state from which to generate actions.

        Returns:
            dict: A dictionary where keys are vehicle entity types and values are dictionaries
                  of entity IDs to their valid actions.
        """
        validActions = {}
        # Iterate over all vehicle entity types
        for vehicleEntityType in self.problem.vehicleEntities:
            entityActions = {}
            # Iterate over all entity IDs of the current vehicle type
            for entityId in self.problem.get_entity_ids(state, vehicleEntityType):
                # Produce actions for each entity
                actions = self.ActionProducer.produce_actions(self.problem, state,
                                                              entityId, vehicleEntityType)
                entityActions[entityId] = actions
            validActions[vehicleEntityType] = entityActions
        return validActions

    def generate_all_valid_partial_seperate_actions(self, state: State, vehicleType: int, partialVehciles):
        """
        Generate valid actions for a subset of vehicles of a specific type.

        Args:
            state (State): The current state.
            vehicleType (int): The type of the vehicles.
            partialVehciles (Iterable): An iterable of vehicle IDs to generate actions for.

        Returns:
            dict: A dictionary mapping vehicle IDs to their valid actions.
        """
        valid_actions = {}
        for entityId in partialVehciles:
            actions = self.ActionProducer.produce_actions(self.problem, state,
                                                          entityId, vehicleType)
            valid_actions[entityId] = actions
        return valid_actions

    def generate_all_valid_actions_recursive(self, all_valid_actions, vehicle_keys, partial_assignment=None):
        """
        Recursively generate all valid combinations of actions for all vehicles.

        Args:
            all_valid_actions (dict): Dictionary of valid actions for each vehicle type and entity.
            vehicle_keys (List[int]): List of vehicle types to be processed.
            partial_assignment (List[Action], optional): The partial assignment of actions validated so far.

        Returns:
            List[List[Action]]: List of valid combinations of actions for all entities.
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
                # Move on to the next vehicle type
                valid_combinations.extend(
                    self.generate_all_valid_actions_recursive(all_valid_actions, vehicle_keys[1:], current_partial_assignment)
                )
                return

            current_entity_id = entity_ids[entity_index]
            actions_list = entity_actions[current_entity_id]

            for action in actions_list:
                if self.validate_action(action):
                    # Add the action to the current partial assignment and recurse
                    recurse_entity_actions(entity_index + 1, current_partial_assignment + [action])

        recurse_entity_actions(0, partial_assignment)
        return valid_combinations

    def generate_all_valid_actions(self):
        """
        Wrapper for generating all valid action combinations using the recursive method.

        Returns:
            List[List[Action]]: List of valid combinations of actions for all entities.
        """
        all_valid_actions = self.generate_all_valid_seperate_actions(self.problem.initState)
        vehicle_keys = self.problem.vehicleEntities
        all_combinations = self.generate_all_valid_actions_recursive(all_valid_actions, vehicle_keys)
        return all_combinations

    def validate_Transition_shallow(self, state, transition):
        """
        Validate a sequence of actions in a shallow manner.

        Note:
            This validation method is not as reliable as thought.
            It doesn't take into consideration vehicles acting at the same time,
            e.g., in the domain of Drones and Trucks - it won't consider one drone
            existing and another one boarding instead.

        Args:
            state (State): The state to validate against.
            transition (List[Action]): The sequence of actions to validate.

        Returns:
            bool: True if all actions are valid in the given state, False otherwise.
        """
        for action in transition:
            if not action.validate(self.problem, state):
                return False
        return True

    def validate_Transition(self, state, transition):
        """
        Validate a sequence of actions by applying them to a copy of the state.

        Args:
            state (State): The state to validate against.
            transition (List[Action]): The sequence of actions to validate.

        Returns:
            bool: True if all actions are valid and can be applied sequentially, False otherwise.
        """
        state = state.__copy__()
        for j, action in enumerate(transition):
            if not action.validate(self.problem, state):
                print('in validate_Transition action ', j)
                return False
            action.apply(self.problem, state)
        return True

    def validate_action(self, action: Action):
        """
        Validate an action by checking its preconditions against the current state.

        Args:
            action (Action): The action to be validated.

        Returns:
            bool: True if the action is valid, False otherwise.
        """
        try:
            isValid = action.validate(self.problem, self.current_state)
            # print(f"Validation for action {action}: {isValid}")
            return isValid
        except KeyError as e:
            # print(f"KeyError during validation of action {action}: {e}")
            return False
        except Exception as e:
            # print(f"Unexpected error during validation of action {action}: {e}")
            return False

    def revalidate_action(self, state, action):
        """
        Apply the action's effects to the given state.

        Args:
            state (State): The state on which the action is applied.
            action (Action): The action to be applied.

        Returns:
            None
        """
        try:
            # print(f"Applying action: {action}")  # Debug statement
            action.apply(self.problem, state)
            # print(f"Action applied successfully: {action}")
        except KeyError as e:
            raise Exception(f"KeyError while applying action {action}: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error while applying action {action}: {e}")

    def generate_partial_successors(self, state: State, vehicleType: int, vehicleIds: Tuple):
        """
        Generate successors for a subset of vehicles of a specific type.

        Args:
            state (State): The current state.
            vehicleType (int): The type of the vehicles.
            vehicleIds (Tuple[int]): A tuple of vehicle IDs to generate successors for.

        Returns:
            deque: A deque containing tuples of (nextState, nextTransition, nextCost).
        """
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
        """
        Apply environment steps to each state in the queue.

        Args:
            queue (deque): A deque containing tuples of (state, transition, cost).

        Returns:
            deque: Updated queue with environment steps applied and envCost added.
        """
        # No envStep case
        if not self.envSteps:
            return ((item[0], item[1], item[2], 0) for item in queue)

        # Process each item in the deque by index
        for i in range(len(queue)):
            # Initialize the tuple elements
            state, transition, cost = queue[i]
            envCost = 0
            # Apply each envStep to the state and accumulate envCost
            for envStep in self.envSteps:
                envStep.apply(self.problem, state)
                envCost += envStep.get_cost(self.problem, state)

            # Replace the tuple in-place with the updated values
            queue[i] = (state, transition, cost, envCost)

        return queue

    def generate_successors(self, state):
        """
        Generate all possible successor states from the current state.

        Args:
            state (State): The current state.

        Returns:
            deque: A deque containing tuples of (nextState, nextTransition, nextCost).
        """
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

        # Apply environment steps to each state in the queue
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

        Args:
            action (Action): The action to be applied to advance the state.

        Returns:
            float: The cost of the action applied.

        Raises:
            ValueError: If the action is invalid in the current state.
        """
        if self.validate_action(action):
            action.apply(self.problem, self.current_state)
            return action.get_cost(self.problem, self.current_state)
        else:
            raise ValueError("Invalid action attempted to be applied to the current state.")

    def apply_environment_steps(self, state):
        """
        Apply all environment steps to the given state.

        Args:
            state (State): The state to apply environment steps to.

        Returns:
            Tuple[State, float]: The updated state and the total cost of environment steps.
        """
        cost = 0
        state = state.__copy__()
        for envStep in self.envSteps:
            envStep.apply(self.problem, state)
            cost += envStep.get_cost(self.problem, state)
        return state, cost

    def apply_transition(self, state, transition):
        """
        Apply a sequence of actions (transition) to the given state.

        Args:
            state (State): The state to apply the transition to.
            transition (List[Action]): The sequence of actions to apply.

        Returns:
            Tuple[State, float]: The updated state and the total cost of the transition.
        """
        cost = 0
        state = state.__copy__()
        for action in transition:
            action.apply(self.problem, state)
            cost += action.get_cost(self.problem, state)
        return state, cost

    def apply_full_transition(self, state, cost, transition):
        """
        Apply a sequence of actions and environment steps to the given state.

        Args:
            state (State): The state to apply the transition to.
            cost (float): The initial cost before applying the transition.
            transition (List[Action]): The sequence of actions to apply.

        Returns:
            Tuple[State, float]: The updated state and the total cost after applying the transition and environment steps.
        """
        for action in transition:
            action.apply(self.problem, state)
            cost += action.get_cost(self.problem, state)
        for envStep in self.envSteps:
            envStep.apply(self.problem, state)
            cost += envStep.get_cost(self.problem, state)
        return state, cost

    def addItems(self, entityName, entityList):
        """
        Add items (entities) to the current state.

        Args:
            entityName (str): The name of the entity type.
            entityList (Dict): A dictionary of item indices to their parameters.

        Returns:
            State: The updated current state.
        """
        entity_index = self.problem.entities[entityName][0]
        for itemImdex, params in entityList.items():
            self.problem.add_entity(self.current_state, entity_index, *params)
        return self.current_state

    def apply_iter_step(self, state, iterationItems):
        """
        Apply the iteration step and add iteration items to the state.

        Args:
            state (State): The state to apply the iteration step to.
            iterationItems (Dict[str, List]): A dictionary mapping entity names to lists of item parameters to add.

        Returns:
            State: The updated state after applying the iteration step and adding items.
        """
        self.iterStep.apply(self.problem, state)
        for entityName, entities in iterationItems.items():
            entityType = self.entities[entityName][0]
            for itemParams in entities:
                self.problem.add_entity(state, entityType, *itemParams)
        return state
