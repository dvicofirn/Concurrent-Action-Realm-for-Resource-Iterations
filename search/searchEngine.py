from typing import List, Dict
from CARRI import State, Simulator
from CARRI.action import Action
class SearchEngine:
    def __init__(self, simulator: Simulator, **kwargs):
        self.simulator = simulator
    def search(self, state: State, plan_dict: Dict, **kwargs) -> List[List[Action]]:
        raise NotImplementedError("Must be implemented by subclasses")