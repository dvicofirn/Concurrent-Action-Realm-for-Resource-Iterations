from CARRI.Parser.parser import Parser
from planner import SearchEngineBasedPlanner, GeneticPlanner
from search import PartialAssigner, IDAStarSearch, UCTSearchEngine, GreedySearchEngine
from heuristics import MoreCountHeuristic
from manager import Manager
import time
import csv
FOLDER_DOMAINS = "Examples\\Domains"
FOLDER_PROBLEMS = "Examples\\Problems"
DomainsDict = {0: "Trucks and Drones", 1: "Cars", 2: "MotorCycles and Letters",
               3: "Rail System Factory"}
DomainsProblemsDict = {"Trucks and Drones": ("Trucks and Drones 1", "Trucks and Drones 2", "Trucks and Drones 3"),
                       "Cars": ("Cars 1", "Cars 2"),
                       "MotorCycles and Letters": ("MotorCycles and Letters 1",),
                       "Rail System Factory": ("Rail System Factory 1",)}
def getDomainProblemFiles(domain, problem):
    domainName = DomainsDict[domain]
    problemName = DomainsProblemsDict[domainName][problem]
    return domainName + ".CARRI", problemName + ".CARRI"

def previousMain():
    parser = Parser()
    simulator, iterations = parser.parse(FOLDER_DOMAINS + "\\" + "Cars.CARRI",
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
    iter_t = 5.0


    planner = SearchEngineBasedPlanner(simulator, iter_t, 10)
    planner.run_iteration()
    """
    planner.run_iteration()
    """

def runMain():
    domainFile, problemFile = getDomainProblemFiles(0, 2)
    parser = Parser()
    simulator, iterations = parser.parse(FOLDER_DOMAINS + "\\" + domainFile,
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
            print(state)
            for action in transition:
                print(simulator.actionStringRepresentor.represent(action), end=", ")
            print()
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
    parser = Parser()
    simulator, iterations = parser.parse(FOLDER_DOMAINS + "\\" + "Trucks and Drones.CARRI",
                                             FOLDER_PROBLEMS + "\\" + DomainsProblemsDict["Trucks and Drones"][
                                                     1] + ".CARRI")
    partial = PartialAssigner(simulator)
    print(partial.split_vehicles())
    print(partial.vehicleTypes)

def managerMain():
    domainFile, problemFile = getDomainProblemFiles(1, 0)
    parser = Parser()
    simulator, iterations = parser.parse(FOLDER_DOMAINS + "\\" + domainFile,
                                             FOLDER_PROBLEMS + "\\" + problemFile)
    print(simulator.problem.constants)
    manager = Manager(simulator, iterations, 60, 10, planner=GeneticPlanner, searchAlgorithm=UCTSearchEngine, heuristic=MoreCountHeuristic)
    manager.run()
def doubleRunnerMain():
    domainFile, problemFile = getDomainProblemFiles(3, 0)
    parser = Parser()
    simulator, iterations = parser.parse(FOLDER_DOMAINS + "\\" + domainFile,
                                         FOLDER_PROBLEMS + "\\" + problemFile)
    print(simulator.problem.constants)

    print("----------run 1----------")
    manager = Manager(simulator, iterations, 10, 10, planner=SearchEngineBasedPlanner, searchAlgorithm=IDAStarSearch)
    manager.run()
    print("----------run 2----------")
    manager = Manager(simulator, iterations, 10, 10, planner=GeneticPlanner, searchAlgorithm=PartialAssigner)
    manager.run()

def managerLogRun(domainIndex, problemIndex, iterTime, transitionsPerIteration, **kwargs):
    domainFile, problemFile = getDomainProblemFiles(domainIndex, problemIndex)
    parser = Parser()
    simulator, iterations = parser.parse(FOLDER_DOMAINS + "\\" + domainFile,
                                         FOLDER_PROBLEMS + "\\" + problemFile)
    log = [-1 for _ in range(len(iterations))]
    searchAlgorithm = kwargs.get('searchAlgorithm', IDAStarSearch)
    manager = Manager(simulator, iterations, iterTime, transitionsPerIteration, **kwargs)
    log = manager.logRun()
    domainName = DomainsDict[domainIndex]
    ProblemName = DomainsProblemsDict[domainName][problemIndex]
    log['domain name'] = domainName
    log['problem name'] = ProblemName
    log['iteration time'] = iterTime
    log['transitions per iteration'] = transitionsPerIteration
    log['planner name'] = kwargs.get('planner name', 'Genetic Planner')
    log['search engine name'] = kwargs.get('search engine name', 'None')
    log['heuristic name'] = kwargs.get('heuristic name', 'None')
    return log

def managerRun(domainIndex, problemIndex, iterTime, transitionsPerIteration, **kwargs):
    domainFile, problemFile = getDomainProblemFiles(domainIndex, problemIndex)
    parser = Parser()
    simulator, iterations = parser.parse(FOLDER_DOMAINS + "\\" + domainFile,
                                         FOLDER_PROBLEMS + "\\" + problemFile)
    manager = Manager(simulator, iterations, iterTime, transitionsPerIteration, **kwargs)
    manager.run()

def runs():
    managerRun(0, 0, 45, 10,  planner=GeneticPlanner)
    managerRun(0, 1, 45, 10,  planner=GeneticPlanner)
    managerRun(0, 2, 45, 10,  planner=GeneticPlanner)
    managerRun(1, 0, 45, 10,  planner=GeneticPlanner)
    managerRun(1, 1, 45, 10,  planner=GeneticPlanner)
    managerRun(2, 0, 45, 10,  planner=GeneticPlanner)
    managerRun(3, 0, 45, 10,  planner=GeneticPlanner)

def addRowToCsv(fileName, dictRow):
    with open(fileName + ".csv", 'r') as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = reader.fieldnames

        # Append the new row to the CSV
    with open(fileName + ".csv", 'a', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writerow(dictRow)

def run_log(csvName, runData):
    for i in range(runData["repetition"]):
        domainIndex = runData["domainIndex"]
        problemIndex = runData["problemIndex"]
        iterTime = runData["iterTime"]
        transitionsPerIteration = runData["transitionsPerIteration"]
        kwargs = runData["kwargs"]
        log = (managerLogRun(domainIndex, problemIndex, iterTime, transitionsPerIteration, **kwargs))
        addRowToCsv(csvName, log)
        print(f'run #{i+1} of {log['domain name']}: {log['problem name']}'
              f'\nUsing {log["planner name"]}, with {log["search engine name"]} - {log["heuristic name"]}')

def run_pipeline(csvName, **kwargs):
    data = [{'domainIndex': 0, 'problemIndex': 0},
            {'domainIndex': 0, 'problemIndex': 1},
            {'domainIndex': 0, 'problemIndex': 2},
            {'domainIndex': 1, 'problemIndex': 0},
            {'domainIndex': 1, 'problemIndex': 1},
            {'domainIndex': 2, 'problemIndex': 0},
            {'domainIndex': 3, 'problemIndex': 0},]

    for runData in data:
        runData['repetition'] = kwargs.get('repetition', 1)
        runData['iterTime'] = kwargs.get('iterTime', 120)
        runData['transitionsPerIteration'] = kwargs.get('transitionsPerIteration', 10)
        runData['kwargs'] = kwargs.get('kwargs', {'planner': GeneticPlanner, 'planner name': "Genetic"})
        run_log(csvName, runData)

def main():
    run_pipeline('Logs\\results', repetition=4, iterTime=120, transitionsPerIteration=10,
                    kwargs={'planner': GeneticPlanner, 'planner name': "genetic"})
    run_pipeline('Logs\\results', repetition=1, iterTime=120, transitionsPerIteration=10,
                 kwargs={'planner': GeneticPlanner, 'planner name': "genetic"})

    run_pipeline('Logs\\results', repetition=1, iterTime=120, transitionsPerIteration=10,
                 kwargs={'planner': SearchEngineBasedPlanner, 'planner name': "search based",
                         "searchAlgorithm": GreedySearchEngine, "search engine name": "Greedy"})
    run_pipeline('Logs\\results', repetition=1, iterTime=120, transitionsPerIteration=10,
                 kwargs={'planner': SearchEngineBasedPlanner, 'planner name': "search based",
                         "searchAlgorithm": UCTSearchEngine, "search engine name": "UCT"})

if __name__ == '__main__':
    main()
