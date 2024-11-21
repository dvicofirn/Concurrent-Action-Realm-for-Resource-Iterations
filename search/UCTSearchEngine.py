from .searchEngine import *
from .partialAssigner import PartialAssigner
from CARRI import Simulator, State
import random
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
        self.max_steps = kwargs.get('steps', 10)
        self.plan_dict = None
        self.partialAssigner = kwargs.get('partial_assigner', PartialAssigner(simulator, **kwargs))
        self.root_node = None
        self.best_plan = None
        self.best_avg_cost = float('inf')

    def search(self, state: State, plan_dict, **kwargs):
        self.max_steps = kwargs.get('steps', 10)
        self.plan_dict = plan_dict
        self.root_node = Node(state)
        self.node_map = {self.state_key(state): self.root_node}

        while True:
            # Perform one iteration of the UCT search
            full_plan, total_cost, avg_cost = self.uct_search()
            if full_plan:
                if avg_cost < self.best_avg_cost:
                    self.best_avg_cost = avg_cost
                    self.best_plan = full_plan
                    if self.plan_dict is not None:
                        self.plan_dict['plan'] = self.best_plan
            # The search runs continuously until the planner is terminated externally

    def uct_search(self) -> Tuple[List[List[Action]], float, float]:
        path, node = self.tree_policy()
        rollout_plan, rollout_cost = self.rollout(node)
        total_cost = node.g + rollout_cost
        full_plan = self.construct_full_plan(path, rollout_plan)
        total_steps = len(full_plan)
        avg_cost = total_cost / total_steps
        self.backup(path, total_cost)
        return full_plan, total_cost, avg_cost

    def tree_policy(self) -> Tuple[List[Node], Node]:
        node = self.root_node
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
                    break  # No more nodes to explore
                path.append(node)
        return path, node

    def get_untried_actions(self, node):
        # Use partialAssigner to generate possible actions from this node
        # Generate a few possible next steps
        paths = self.partialAssigner.produce_paths(node.state, steps=1, maxStates=10)
        untried_actions = []
        for path in paths:
            # Each path is a tuple: ([state2[0], state], [transitions], [costs per action], [env costs per action])
            next_state = path[0][1]  # The resulting state after the action
            actions = path[1][0]      # Actions at step 0
            action_cost = path[2][0] + path[3][0]  # Sum of action cost and environment cost at step 0
            untried_actions.append((actions, action_cost, next_state))
        return untried_actions

    def best_child(self, node) -> Node:
        # Select the child with the lowest average cost per visit
        best_avg_cost = float('inf')
        best_child = None
        for child in node.children:
            if child.visits == 0:
                continue  # Skip unvisited children
            avg_cost = child.total_cost / child.visits
            if avg_cost < best_avg_cost:
                best_avg_cost = avg_cost
                best_child = child
        # If all children have zero visits, select one at random to encourage exploration
        if best_child is None and node.children:
            best_child = random.choice(node.children)
        return best_child

    def rollout(self, node) -> Tuple[List[List[Action]], float]:
        # Perform a simulation from the given node using partialAssigner
        plan, cost = self.partialAssigner.provideTransitionsAndCost(node.state, steps=self.max_steps)
        return plan, cost

    def backup(self, path: List[Node], total_cost: float):
        # Update the visit count and total cost along the path
        for node in path:
            node.visits += 1
            node.total_cost += total_cost

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



