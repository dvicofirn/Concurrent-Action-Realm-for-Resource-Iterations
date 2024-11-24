from CARRI.Parser.parser import Parser
from planner import SearchEngineBasedPlanner, GeneticPlanner
from search import PartialAssigner, IDAStarSearchEngine, UCTSearchEngine, GreedySearchEngine
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

def run_main():
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

def manager_main():
    domainFile, problemFile = getDomainProblemFiles(0, 2)
    parser = Parser()
    simulator, iterations = parser.parse(FOLDER_DOMAINS + "\\" + domainFile,
                                             FOLDER_PROBLEMS + "\\" + problemFile)
    print(simulator.problem.constants)
    manager = Manager(simulator, iterations, 30, 10, planner=GeneticPlanner, searchAlgorithm=UCTSearchEngine, heuristic=MoreCountHeuristic)
    manager.run()
def double_runner_main():
    domainFile, problemFile = getDomainProblemFiles(3, 0)
    parser = Parser()
    simulator, iterations = parser.parse(FOLDER_DOMAINS + "\\" + domainFile,
                                         FOLDER_PROBLEMS + "\\" + problemFile)
    print(simulator.problem.constants)

    print("----------run 1----------")
    manager = Manager(simulator, iterations, 10, 10, planner=SearchEngineBasedPlanner, searchAlgorithm=IDAStarSearchEngine)
    manager.run()
    print("----------run 2----------")
    manager = Manager(simulator, iterations, 10, 10, planner=GeneticPlanner, searchAlgorithm=PartialAssigner)
    manager.run()

def manager_log_run(domainIndex, problemIndex, iterTime, transitionsPerIteration, **kwargs):
    domainFile, problemFile = getDomainProblemFiles(domainIndex, problemIndex)
    parser = Parser()
    simulator, iterations = parser.parse(FOLDER_DOMAINS + "\\" + domainFile,
                                         FOLDER_PROBLEMS + "\\" + problemFile)
    log = [-1 for _ in range(len(iterations))]
    searchAlgorithm = kwargs.get('searchAlgorithm', IDAStarSearchEngine)
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

def manager_run(domainIndex, problemIndex, iterTime, transitionsPerIteration, **kwargs):
    domainFile, problemFile = getDomainProblemFiles(domainIndex, problemIndex)
    parser = Parser()
    simulator, iterations = parser.parse(FOLDER_DOMAINS + "\\" + domainFile,
                                         FOLDER_PROBLEMS + "\\" + problemFile)
    manager = Manager(simulator, iterations, iterTime, transitionsPerIteration, **kwargs)
    manager.run()

def runs():
    manager_run(0, 0, 45, 10, planner=GeneticPlanner)
    manager_run(0, 1, 45, 10, planner=GeneticPlanner)
    manager_run(0, 2, 45, 10, planner=GeneticPlanner)
    manager_run(1, 0, 45, 10, planner=GeneticPlanner)
    manager_run(1, 1, 45, 10, planner=GeneticPlanner)
    manager_run(2, 0, 45, 10, planner=GeneticPlanner)
    manager_run(3, 0, 45, 10, planner=GeneticPlanner)

if __name__ == '__main__':
    manager_main()