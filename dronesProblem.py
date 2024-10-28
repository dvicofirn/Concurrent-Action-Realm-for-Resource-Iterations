from worldProblem import *

GENERAL_ACTION_COST = 1
EMERGENCY_CHARGE_COST = 20
MIN_CHARGE = 0
MAX_CHARGE = 10
class DronesState(State):
    def __init__(self, vehicles: dict = None, packages: list = None, requests: list = None,
                 transition: list = None, cost: int = 0):
        super().__init__(vehicles, packages, requests, transition, cost)


class Wait(Action):
    def __init__(self, vehicleId: int):
        super().__init__(actionType="Wait",
                         params={"vehicle Id": vehicleId},
                         cost=GENERAL_ACTION_COST)

class Travel(Action):
    def __init__(self, vehicleId: int, destiny: int):
        super().__init__(actionType="Travel",
                         params={"vehicle Id": vehicleId, "destiny": destiny},
                         cost=GENERAL_ACTION_COST)
class PickUp(Action):
    def __init__(self, vehicleId: int, packageIndex: int):
        super().__init__(actionType="Pick Up",
                         params={"vehicle Id": vehicleId, "package index": packageIndex},
                         cost=GENERAL_ACTION_COST)
class Deliver(Action):
    def __init__(self, vehicleId: int, packageIndex: int, requestIndex: int):
        super().__init__(actionType="Deliver",
                         params={"vehicle Id": vehicleId, "package index": packageIndex, "request index": requestIndex},
                         cost=GENERAL_ACTION_COST)

class Charge(Action):
    def __init__(self, vehicleId: int, chargeCost: int):
        super().__init__(actionType="Charge",
                         params={"vehicle Id": vehicleId},
                         cost=chargeCost)
class DronesProblem(Problem):
    def __init__(self, settings: dict):
        super().__init__(settings)
        self.stores = settings["stores"] # Set


    def generate_vehicle_actions(self, state: State, vehicleId: int) -> tuple:
        nonConflictionActions = []
        possibleConflictionActions = []
        
        if state.vehicles[vehicleId]["charge"] == MIN_CHARGE:
            if state.vehicles[vehicleId]["location"] in self.stores:
                nonConflictionActions.append(Charge(vehicleId, GENERAL_ACTION_COST))
            else:
                nonConflictionActions.append(Charge(vehicleId, EMERGENCY_CHARGE_COST))
            return nonConflictionActions, possibleConflictionActions
        if state.vehicles[vehicleId]["location"] in self.stores:
            pass
            



