from CARRI.translator import Translator
from planner import Planner
from planner import Planner
from manager import Manager
from CARRI.problem import Problem
import time
from search import PartialAssigner
FOLDER_DOMAINS = "Examples\\Domains"
FOLDER_PROBLEMS = "Examples\\Problems"
DomainsProblemsDict = {"Trucks and Drones": ("Trucks and Drones 1", "Trucks and Drones 2"),
                        "Cars": ("Cars 1",),}
def main():
    translator = Translator()
    simulator, iterations = translator.translate(FOLDER_DOMAINS + "\\" + "Cars.CARRI",
            FOLDER_PROBLEMS + "\\" + DomainsProblemsDict["Cars"][0] + ".CARRI")
    manager = Manager(simulator, iterations, 30, 10, )
    manager.run()

    """
    actions = simulator.generate_all_valid_actions_seperatly()
    """
    actions = simulator.generate_all_valid_actions_seperatly()

    for _ in actions.keys():
        for act in actions[_].values():
            for a in act:
                x = simulator.actionStringRepresentor.represent(a)
                print(x)

    actions = simulator.generate_all_valid_actions()
    i = 0
    for act in actions :
        print('\n')
        print(f'full reduced action {i}')
        for a in act:
            x = simulator.actionStringRepresentor.represent(a)
            print(x)
        i += 1

    """
    """
    i = 0
    succesors = simulator.generate_successor_states(simulator.current_state)
    for next_state, action, cost in succesors:
        print(i)
        print(next_state)
        i+= 1
    """
    """
    i = 0
    succesors = simulator.generate_successor_states(simulator.current_state)
    for next_state, action, cost in succesors:
        print(i)
        print(next_state)
        i+= 1
    init_time = 5.0
    iter_t = 5.0


    planner = Planner(simulator, init_time, iter_t)
    planner.run_iteration()
    """
    planner.run_iteration()
    """

def runMain():
    translator = Translator()
    simulator, iterations = translator.translate(FOLDER_DOMAINS + "\\" + "Trucks and Drones.CARRI",
            FOLDER_PROBLEMS + "\\" + DomainsProblemsDict["Trucks and Drones"][1] + ".CARRI")
    partial = PartialAssigner(simulator)
    results = partial.search(simulator.current_state, 5, 5)
    for item in results:
        print(item[1])
        print()
        print(item[2])
        print()
        for transition in item[2]:
            for action in transition:
                print(simulator.actionStringRepresentor.represent(action), end=', ')
            print("--")
        print(item[3])
        print()
        print(item[4])
        print()
    #manager = Manager(simulator, iterations, 30, 10, {"search_algorithm": PartialAssigner})

    #manager.run()


if __name__ == '__main__':
    runMain()