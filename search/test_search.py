import unittest
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


from heuristics.hmax import HMaxHeuristic  # Example heuristic
from search.Astar import a_star_search
from CARRIRealm import State
from CARRITranslator import CARRITranslator

# Load the domain and problem files
DOMAIN_FILE = "Trucks and Drones Domain.CARRI"
PROBLEM_FILE = "Trucks and Drones Problem.CARRI"

from CARRIRealm import State

def initialize_state():
    # Define initial state components
    locations = {
        "loc_1": {"type": "normal", "adjacent": ["loc_2", "loc_3"]},
        "loc_2": {"type": "charging_station", "adjacent": ["loc_1", "loc_3"]},
        "loc_3": {"type": "normal", "adjacent": ["loc_1", "loc_2"]}
    }
    
    vehicles = {
        "truck_1": {"type": "truck", "location": "loc_1", "drone_capacity": 1, "package_capacity": 2},
        "drone_1": {"type": "drone", "location": "loc_2", "charge": 5, "capacity": 1, "board": False}
    }
    
    packages = {
        "package_1": {"location": "loc_1", "on_entity": 0},
        "package_2": {"location": "loc_3", "on_entity": 0}
    }
    
    requests = {
        "request_1": {"location": "loc_3", "urgency": 2},
        "request_2": {"location": "loc_1", "urgency": 1}
    }
    
    # Initialize State with the specified components
    initial_state = State(
        locations=locations,
        vehicles=vehicles,
        packages=packages,
        requests=requests
    )
    
    return initial_state


class TestAStarCARRIDomain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Parse the .CARRI files to initialize the domain and problem
        cls.translator = CARRITranslator()
        cls.domain, cls.problem = cls.translator.parse(DOMAIN_FILE, PROBLEM_FILE)
        
        # Initialize the initial state
        cls.initial_state = State(cls.problem["initial_state"])

    def goal_test(self, state):
        # Define a goal test based on the problem
        return state.is_goal(self.problem["goal"])

    def successors(self, state):
        # Generate successors for a given state
        return state.generate_successors()

    def test_a_star_with_hmax(self):
        # Choose a heuristic, in this case, HMaxHeuristic
        heuristic = HMaxHeuristic()

        # Run A* search
        path = a_star_search(
            initial_state=self.initial_state,
            goal_test=self.goal_test,
            successors=self.successors,
            heuristic=heuristic.heurist
        )

        # Check that a valid path was found
        self.assertIsNotNone(path, "A* did not return a valid path.")
        self.assertGreater(len(path), 0, "Path should contain at least one action.")

        # Optionally, verify that the path satisfies the goal condition by applying each action
        state = self.initial_state
        for action in path:
            state = state.apply_action(action)
        self.assertTrue(self.goal_test(state), "Final state does not satisfy the goal condition.")

if __name__ == "__main__":
    unittest.main()
