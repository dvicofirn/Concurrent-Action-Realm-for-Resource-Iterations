from CARRI.Parser.parser import Parser
from planner import SearchEngineBasedPlanner, GeneticPlanner
from search import IDAStarSearchEngine, UCTSearchEngine, GreedySearchEngine
from manager import Manager
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
        log = (manager_log_run(domainIndex, problemIndex, iterTime, transitionsPerIteration, **kwargs))
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
    while True:
        run_pipeline('Logs\\results', repetition=1, iterTime=120, transitionsPerIteration=10,
                     kwargs={'planner': GeneticPlanner, 'planner name': "Genetic"})

        run_pipeline('Logs\\results', repetition=1, iterTime=120, transitionsPerIteration=10,
                     kwargs={'planner': SearchEngineBasedPlanner, 'planner name': "Search Based",
                             "searchAlgorithm": UCTSearchEngine, "search engine name": "UCT"})

        run_pipeline('Logs\\results', repetition=1, iterTime=120, transitionsPerIteration=10,
                 kwargs={'planner': SearchEngineBasedPlanner, 'planner name': "Search Based",
                         "searchAlgorithm": GreedySearchEngine, "search engine name": "Greedy"})

if __name__ == '__main__':
    main()
