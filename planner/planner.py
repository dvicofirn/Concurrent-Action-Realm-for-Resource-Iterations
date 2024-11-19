import time
import random
import logging
from overrides import override
import numpy as np
from CARRI import Action, Simulator, State
from heuristics import *
from search import *
import logging
from typing import List


class Planner:
    def __init__(self, simulator: Simulator, iterTime: int, transitionsPerIteration: int, **kwargs):
        """
        :param simulator: An instance of CARRISimulator
        :param iterTime: float, time allowed for each iteration
        :param transitionsPerIteration: int, maximum plan length per iteration
        """
        self.simulator = simulator
        self.iterTime = iterTime
        self.maxPlanLength = transitionsPerIteration

    def generate_plan(self, state: State) -> List[List[Action]]:
        """
        Generate a plan within the time limit using the provided search algorithm and heuristic (if needed).
        :return: A list of transition actions the plan (sequence of actions).
        """
        raise NotImplementedError("Must be implemented by subclasses")





