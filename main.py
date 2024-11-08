from CARRI.translator import Translator
from manager import Manager
from CARRI.problem import Problem
import time
from search import PartialAssigner
FOLDER_DOMAINS = "Examples\\Domains"
FOLDER_PROBLEMS = "Examples\\Problems"
DomainsProblemsDict = {"Trucks and Drones": ("Trucks and Drones 1", "Trucks and Drones 2"),
                        "Cars": ("Cars 1",),
                       "MotorCycles and Letters": ("MotorCycles and Letters 1",)}

instance = "Trucks and Drones" #"Cars"  # #"" ##"MotorCycles and Letters"


def main():
    translator = Translator()
    simulator, iterations = translator.translate(FOLDER_DOMAINS + "\\" + instance + ".CARRI",
            FOLDER_PROBLEMS + "\\" + DomainsProblemsDict[instance][0] + ".CARRI")
    manager = Manager(simulator, iterations, 60, 10, )
    manager.run()


def runMain():
    translator = Translator()
    simulator, iterations = translator.translate(FOLDER_DOMAINS + "\\" + "Trucks and Drones.CARRI",
            FOLDER_PROBLEMS + "\\" + DomainsProblemsDict["Trucks and Drones"][1] + ".CARRI")
    partial = PartialAssigner(simulator)
    start = time.time()
    results = partial.search(simulator.current_state, 25, 500)
    end = time.time()
    print(end - start)
    print()
    for i in range(len(results)):
        transitions = results[i][1]
        state = simulator.get_state()
        cost = 0
        for transition in transitions:
            if not simulator.validate_Transition_state(state, transition):
                print(f"Problem with transition {transition}\nIndex {i}")
                break
            state, actionCost = simulator.apply_transition(state, transition)
            state, envCost = simulator.apply_environment_steps(state)
            cost += actionCost + envCost
        print(state)
        print(cost)
        print("---")
    print(end - start)




""" for transition, cost, nCost in zip(results[0][1], results[0][2], results[0][3]):
        for action in transition:
            print(simulator.actionStringRepresentor.represent(action), end=', ')
        print("\n-----")
        print(cost, nCost)
        print("======================================")
    print(simulator.getState())
    print(results[0][1])
    print()
    print(end - start)
    print("And")
    for i in range(len(results)):
        print(f"{i}. {results[i][2][-1]}, {results[i][3][-1]}")
    print(results[0][3])
    print()
    print(results[0][4])
    print("--------------")"""
    #manager = Manager(simulator, iterations, 30, 10, {"search_algorithm": PartialAssigner})

    #manager.run()


if __name__ == '__main__':
    #runMain()
    main()