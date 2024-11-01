from queue import Queue
from typing import Callable, List, Tuple
from CARRIRealm import CARRIState
from CARRIAction import Step


def bidirectional_search(initial_state: CARRIState, goal_state: CARRIState,
                         successors: Callable[[CARRIState], List[Tuple[CARRIState, Step, int]]]) -> List[Step]:
    front_queue = Queue()
    back_queue = Queue()
    front_queue.put((initial_state, []))
    back_queue.put((goal_state, []))
    front_visited = {initial_state: None}
    back_visited = {goal_state: None}
    
    while not front_queue.empty() and not back_queue.empty():
        if front_queue.qsize() <= back_queue.qsize():
            current_state, path = front_queue.get()
            for next_state, action, _ in successors(current_state):
                if next_state in back_visited:
                    return path + back_visited[next_state][::-1]
                if next_state not in front_visited:
                    front_visited[next_state] = path + [action]
                    front_queue.put((next_state, path + [action]))
        else:
            current_state, path = back_queue.get()
            for next_state, action, _ in successors(current_state):
                if next_state in front_visited:
                    return front_visited[next_state] + path[::-1]
                if next_state not in back_visited:
                    back_visited[next_state] = path + [action]
                    back_queue.put((next_state, path + [action]))
    return []
