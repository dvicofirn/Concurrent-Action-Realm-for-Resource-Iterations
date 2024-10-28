from collections import deque
class State:
    def __init__(self, vehicles: dict = None, packages: list = None, requests: list = None,
                 transition: list = None, cost: int = 0):
        self.vehicles = vehicles if vehicles is not None else {}
        self.packages = packages if packages is not None else []
        self.requests = requests if requests is not None else []
        self.transition = transition if transition is not None else []
        self.cost = cost

    def __str__(self):
        return ("State: { vehicles: " + str(self.vehicles)
                + ", packages: " + str(self.packages)
                + ", requests: " + str(self.requests)
                + ", transition: " + str(self.transition)
                + ", cost: " + str(self.cost) + "}")

    def __repr__(self):
        return self.__str__()

    def __copy__(self):
        # TODO: implement.
        raise NotImplementedError

    def is_goal(self):
        # TODO: resolve (How should we represent goal).
        raise NotImplementedError

class Action:
    def __init__(self, actionType, params, cost):
        self.actionType = actionType
        self.params = params
        self.cost = cost

    def __str__(self):
        return f"{self.actionType} {self.params}"

    def __repr__(self):
        return self.__str__()

    def get_type(self):
        return self.actionType

class Problem:
    def __init__(self, settings: dict):
        self.settings = settings
        self.adjacency = self.settings["adjacency"]
    def generate_vehicle_actions(self, state: State, vehicleId: int) -> tuple:
        raise NotImplementedError

    def create_hypo_state(self, state: State) -> State:
        return State(vehicles=state.vehicles, packages=state.packages, requests=state.requests)

    def apply_environmental_step(self, state: State) -> None:
        raise NotImplementedError

    def apply_action(self, hypoState: State, action: Action) -> State:
        raise NotImplementedError

    def validate_action(self, hypoState: State, action: Action) -> bool:
        raise NotImplementedError

    def generate_state_successors(self, state: State) -> deque:
        currentQueue = deque()
        currentQueue.append(self.create_hypo_state(state))
        for vehicleId in state.vehicles:
            nonConflictingActions, possibleConflictingActions = self.generate_vehicle_actions(state, vehicleId)
            nextQueue = deque()
            while currentQueue:
                hypoState = currentQueue.pop()
                # Apply actions with no conflict
                for action in nonConflictingActions:
                    nextQueue.append(self.apply_action(hypoState, action))
                # Apply validatable actions if applicable on state.
                for action in possibleConflictingActions:
                    if self.validate_action(hypoState, action):
                        nextQueue.append(self.validate_action(hypoState, action))
            currentQueue = nextQueue
        for state in currentQueue:
            self.apply_environmental_step(state)
            state.sortDrones()

        return currentQueue

    def get_initial_state(self):
        raise NotImplementedError
    def get_cost(self, current: State, successor: State):
        return 1

class Heuristic:
    def __init__(self, problem: Problem):
        pass
    def heurist(self, state: State):
        return 0