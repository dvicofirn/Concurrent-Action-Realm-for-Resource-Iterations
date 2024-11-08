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
    simulator, iterations = translator.translate(FOLDER_DOMAINS + "\\" + "MotorCycles and Letters.CARRI",
            FOLDER_PROBLEMS + "\\" + DomainsProblemsDict["MotorCycles and Letters"][0] + ".CARRI")
    partial = PartialAssigner(simulator)
    results = partial.search(simulator.current_state, 20, 200)
    for stateBefore, stateAfter, transition in zip(results[0][0], results[0][1], results[0][2]):
        print(stateBefore)
        print("---------------- ")
        for action in transition:
            print(simulator.actionStringRepresentor.represent(action), end=', ')
        print("\n----------------")
        print(stateAfter)
        print("======================================")


    """print(results[0][3])
    print()
    print(results[0][4])
    print("--------------")"""
    #manager = Manager(simulator, iterations, 30, 10, {"search_algorithm": PartialAssigner})

    #manager.run()


if __name__ == '__main__':
    #runMain()
    main()