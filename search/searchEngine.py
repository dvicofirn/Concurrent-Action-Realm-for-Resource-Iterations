from typing import List
from CARRI import State, Simulator
from CARRI.action import Action
class SearchEngine:
    def __init__(self, simulator: Simulator, **kwargs):
        self.simulator = simulator
    def search(self, state: State, **kwargs) -> List[List[Action]]:
        raise NotImplementedError("Must be implemented by subclasses")