from typing import Dict, Set
from queue import PriorityQueue
from CARRI.problem import State, Problem, Heuristic

#Assumes problem has locAdj constant
def location_map(problem: Problem, startingLocation: int) -> Dict[int, int]:
    queue = PriorityQueue()
    queue.put((startingLocation, 0))
    map = dict()
    if problem.get_adjacency_status() == Dict:
        while queue:
            currentLocation, currentDistance = queue.get()
            map[currentLocation] = currentDistance
            adjacentLocations = problem.get_adjacency_status()[currentLocation]
            for location, distance in adjacentLocations.items():
                if location not in map:
                    queue.put((currentLocation, currentDistance + distance))

    elif problem.get_adjacency_status() == Set:
        while queue:
            currentLocation, currentDistance = queue.get()
            map[currentLocation] = currentDistance
            adjacentLocations = problem.get_adjacency_status()[currentLocation]
            for location in adjacentLocations:
                if location not in map:
                    queue.put((currentLocation, currentDistance + 1))
    return map

class DistanceHeuristic(Heuristic):
    def __init__(self, problem: Problem):
        super().__init__(problem)
        maps={}
        if problem.get_adjacency_status() != None:
            for location in problem.locationRanges():
                maps[location] = location_map(problem, location)

    def evaluate(self, state: State) -> int:
        return 1

