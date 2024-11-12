from CARRI.translator import Translator
from manager import Manager
from CARRI.problem import Problem
import time
from search import PartialAssigner
FOLDER_DOMAINS = "Examples\\Domains"
FOLDER_PROBLEMS = "Examples\\Problems"
DomainsDict = {0: "Trucks and Drones", 1: "Cars", 2: "MotorCycles and Letters"}
DomainsProblemsDict = {"Trucks and Drones": ("Trucks and Drones 1", "Trucks and Drones 2"),
                        "Cars": ("Cars 1",),
                       "MotorCycles and Letters": ("MotorCycles and Letters 1",)}
def getDomainProblemFiles(domain, problem):
    domainName = DomainsDict[domain]
    problemName = DomainsProblemsDict[domainName][problem]
    return domainName + ".CARRI", problemName + ".CARRI"

def main():
    translator = Translator()
    simulator, iterations = translator.translate(FOLDER_DOMAINS + "\\" + instance + ".CARRI",
            FOLDER_PROBLEMS + "\\" + DomainsProblemsDict[instance][0] + ".CARRI")
    manager = Manager(simulator, iterations, 30, 10, )
    manager.run()


def runMain():
    domainFile, problemFile = getDomainProblemFiles(2, 0)
    translator = Translator()
    simulator, iterations = translator.translate(FOLDER_DOMAINS + "\\" + domainFile,
            FOLDER_PROBLEMS + "\\" + problemFile)
    partial = PartialAssigner(simulator)
    start = time.time()
    results = partial.produce_paths(simulator.current_state, 10, 50)
    end = time.time()
    #print(end - start)
    #print()
    for i in range(len(results)):
        transitions = results[i][1]
        state = simulator.get_state()
        cost = 0
        invalid = False
        for transition in transitions:
            """print(state)
            for action in transition:
                print(simulator.actionStringRepresentor.represent(action), end=", ")
            print()"""
            if not simulator.validate_Transition(state, transition):
                print(f"Problem, end Instance of {i}")
                invalid = True
                break
            state, actionCost = simulator.apply_transition(state, transition)
            state, envCost = simulator.apply_environment_steps(state)
            cost += actionCost + envCost
            #print(cost, actionCost, envCost)
            #print(state)
        if invalid:
            continue
        print(f"Success at {i}. {state}")
        print(cost)
        print("---")
    print(end - start)



def testMain():
    translator = Translator()
    simulator, iterations = translator.translate(FOLDER_DOMAINS + "\\" + "Trucks and Drones.CARRI",
                                                 FOLDER_PROBLEMS + "\\" + DomainsProblemsDict["Trucks and Drones"][
                                                     1] + ".CARRI")
    partial = PartialAssigner(simulator)
    print(partial.split_vehicles())
    print(partial.vehicleTypes)

def managerMain():
    domainFile, problemFile = getDomainProblemFiles(0, 0)
    translator = Translator()
    simulator, iterations = translator.translate(FOLDER_DOMAINS + "\\" + domainFile,
                                                 FOLDER_PROBLEMS + "\\" + problemFile)
    manager = Manager(simulator, iterations, 60, 10, )
    manager.run()

if __name__ == '__main__':
    managerMain()