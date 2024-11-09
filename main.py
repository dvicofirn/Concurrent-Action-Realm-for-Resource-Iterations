from CARRI.translator import Translator
from planner import Planner
from planner import Planner
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
    domainFile, problemFile = getDomainProblemFiles(0, 0)
    translator = Translator()
    simulator, iterations = translator.translate(FOLDER_DOMAINS + "\\" + domainFile,
            FOLDER_PROBLEMS + "\\" + problemFile)
    partial = PartialAssigner(simulator)
    start = time.time()
    results = partial.search(simulator.current_state, 10, 50)
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
            if not simulator.validate_Transition_state(state, transition):
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

def testMain():
    translator = Translator()
    simulator, iterations = translator.translate(FOLDER_DOMAINS + "\\" + "Trucks and Drones.CARRI",
                                                 FOLDER_PROBLEMS + "\\" + DomainsProblemsDict["Trucks and Drones"][
                                                     1] + ".CARRI")
    partial = PartialAssigner(simulator)
    print(partial.split_vehicles())
    print(partial.vehicleTypes)

if __name__ == '__main__':
    runMain()