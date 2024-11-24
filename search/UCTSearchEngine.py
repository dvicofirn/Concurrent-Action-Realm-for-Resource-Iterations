from .searchEngine import *
from .partialAssigner import PartialAssigner
from CARRI import Simulator, State
import random
import math
from typing import List, Tuple

class Node:
    def __init__(self, state, parent=None, action=None, g=0):
        self.state = state
        self.parent = parent
        self.action = action  # List of actions that led to this node from parent
        self.children = []
        self.visits = 0
        self.total_cost = 0
        self.g = g  # Accumulated cost from root to this node
        self.untried_actions = None  # Actions not yet tried from this node

class UCTSearchEngine(SearchEngine):

    def __init__(self, simulator: Simulator, **kwargs):
        super().__init__(simulator, **kwargs)
        self.maxSteps = kwargs.get('steps', 10)
        self.partialAssigner = kwargs.get('partialAssigner', PartialAssigner(simulator, **kwargs))
        self.rootNode = None
        self.bestPlan = None
        self.best_avg_cost = float('inf')
        self.exploration_constant = kwargs.get('exploration_constant', 1.0)

    def search(self, state: State, planDict: Dict, **kwargs):
        self.rootNode = Node(state)
        self.planDict = planDict
        self.node_map = {self.state_key(state): self.rootNode}

        while True:
            # Perform one iteration of the UCT search
            full_plan, total_cost, avg_cost = self.uct_search()
            if full_plan and total_cost is not None:
                if avg_cost < self.best_avg_cost:
                    self.best_avg_cost = avg_cost
                    self.bestPlan = full_plan
                    if self.planDict is not None:
                        self.planDict['plan'] = self.bestPlan
            # The search runs continuously until the planner is terminated externally

    def uct_search(self) -> Tuple[List[List[Action]], float, float]:
        path, node = self.tree_policy()
        if node is None:
            # No more nodes to explore
            return None, None, float('inf')
        rollout_plan, rollout_cost = self.rollout(node)
        total_cost = node.g + rollout_cost
        full_plan = self.construct_full_plan(path, rollout_plan)
        total_steps = len(full_plan)
        if total_steps == 0:
            avg_cost = float('inf')
        else:
            avg_cost = total_cost / total_steps
        self.backup(path, total_cost)
        return full_plan, total_cost, avg_cost

    def tree_policy(self) -> Tuple[List[Node], Node]:
        node = self.rootNode
        path = [node]
        while True:
            if node.visits == 0:
                # First time visiting this node, perform rollout
                return path, node
            if node.untried_actions is None:
                # Initialize untried actions using partialAssigner
                node.untried_actions = self.get_untried_actions(node)
            if node.untried_actions:
                # Expand a new child with an untried action
                actions, action_cost, next_state = node.untried_actions.pop()
                child_node = Node(next_state, parent=node, action=actions, g=node.g + action_cost)
                node.children.append(child_node)
                path.append(child_node)
                node = child_node
            else:
                # All actions tried, select the best child to explore further
                node = self.best_child(node)
                if node is None:
                    # No more nodes to explore
                    return path, node
                path.append(node)
        return path, node

    def get_untried_actions(self, node):
        # Use partialAssigner to generate possible actions from this node
        # Generate a few possible next steps
        paths = self.partialAssigner.produce_paths(node.state, steps=1, maxStates=10)
        untried_actions = []
        if not paths:
            return untried_actions
        for path in paths:
            # Each path is a tuple: ([state2[0], state], [transitions], [costs per action], [env costs per action])
            next_state = path[0][1]  # The resulting state after the action
            actions = path[1][0]      # Actions at step 0
            action_cost = path[2][0] + path[3][0]  # Sum of action cost and environment cost at step 0
            untried_actions.append((actions, action_cost, next_state))
        return untried_actions

    def best_child(self, node) -> Node:
        # Select the child using UCB formula
        best_value = -float('inf')
        best_child = None
        c = self.exploration_constant  # Exploration constant
        for child in node.children:
            if child.visits == 0:
                continue  # Skip unvisited children
            exploitation = - (child.total_cost / child.visits)
            exploration = c * math.sqrt(math.log(node.visits) / child.visits)
            ucb_value = exploitation + exploration
            if ucb_value > best_value:
                best_value = ucb_value
                best_child = child
        # If all children have zero visits, select one at random to encourage exploration
        if best_child is None and node.children:
            best_child = random.choice(node.children)
        return best_child

    def rollout(self, node) -> Tuple[List[List[Action]], float]:
        # Perform a simulation from the given node using partialAssigner
        plan, cost = self.partialAssigner.provideTransitionsAndCost(node.state, steps=self.maxSteps)
        return plan, cost

    def backup(self, path: List[Node], total_cost: float):
        # Update the visit count and total cost along the path
        for node in path:
            node.visits += 1
            # Calculate the cost from this node to the end
            node_cost = total_cost - node.g
            node.total_cost += node_cost

    def construct_full_plan(self, path: List[Node], rollout_plan: List[List[Action]]) -> List[List[Action]]:
        # Build the full plan starting from the root node
        full_plan = []
        for node in path[1:]:  # Skip the root node
            full_plan.append(node.action)
        full_plan.extend(rollout_plan)
        return full_plan

    def state_key(self, state: State) -> int:
        # Generate a unique key for the state (ensure State has __hash__ and __eq__ methods)
        return hash(state)
