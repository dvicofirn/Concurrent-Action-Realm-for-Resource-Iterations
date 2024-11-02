from CARRIRealm import CARRIState
from CARRIRealm import CARRIProblem, CARRISimulator, CARRIState
from CARRITranslator import CARRITranslator
from planner import Planner

if __name__ == "__main__":
    FILEPATH_DOMAIN = "Trucks and Drones Domain.CARRI"
    FILEPATH_PROBLEM = "Trucks and Drones Problem.CARRI"

    translator = CARRITranslator()
    simulator, problem, iterations = translator.translate(FILEPATH_DOMAIN, FILEPATH_PROBLEM)
    x = 1

    init_time = 5.0
    iter_t = 1.0

    planner = Planner(problem, simulator, init_time, iter_t)
    planner.plan_iteration()
