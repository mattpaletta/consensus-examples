from collections import namedtuple
from typing import Dict, List, NamedTuple
import copy

import networkx as nx
from graphviz import Digraph


class Task(object):
    def __init__(self, name: str):
        self.name = name
        self._my_counter = 0
        self._current_vector = {name: self._my_counter}
        self._my_counters = [self.get_vector()]

    def get_vector(self):
        return copy.deepcopy(self._current_vector)

    def get_counters(self):
        return self._my_counters

    def add_counter(self, vector: Dict[str, int]):
        self._current_vector = copy.deepcopy(vector)
        self._my_counters.append(copy.deepcopy(vector))

    def get_counter(self, name = None):
        if name is None:
            return self._my_counter
        elif name in self._current_vector.keys():
            return self._current_vector.get(name)
        else:
            return 0

    def increment_counter(self):
        self.set_counter(self.get_counter() + 1)

    def set_counter(self, counter: int):
        self._current_vector.update({self.name: counter})
        self._my_counter = counter

    def update_counter(self, name: str, counter: int):
       self._current_vector.update({name: max(self.get_counter(), counter)})

    def send_message(self, other):
        print("Task {0} sending to Task {1}".format(self.name, other.name))
        self.increment_counter()
        self.add_counter(self.get_vector())
        other.increment_counter()

        new_vector = self._merge_vectors(v1 = other.get_vector(),
                                                   v2 = self.get_vector())
        other.add_counter(new_vector)
        other.update_counter(name = other.name,
                             counter = self.get_counter(name = other.name))

    def _merge_vectors(self, v1: Dict[str, int], v2: Dict[str, int]):
        new_vector = {}
        for key in v1.keys():
            v1_val = v1.get(key)
            if key in v2.keys():
                v2_val = v2.get(key)
            else:
               v2_val = -v1_val

            new_vector.update({key: max(v1_val, v2_val)})

        for key in v2.keys():
            v2_val = v2.get(key)
            if key in v1.keys():
                v1_val = v1.get(key)
            else:
                v1_val = -v2_val
            new_vector.update({key: max(v1_val, v2_val)})
        return new_vector


def graph_vectors(*args: Task):
    graph_name = 'Vector_Clocks_Example'
    dot = Digraph(comment = graph_name)
    my_graph = nx.MultiDiGraph()

    Event = namedtuple('Event', ['process', 'vector', 'id'], verbose = False)

    all_events: List[Event] = []
    adjacency_list = {}

    # [A, B, C]
    all_tasks = list(map(lambda t: t.name, args))

    # {"A": [{A: 1}, {A: 2, B: 1}]}
    for task in args:
        adjacency_list.update({task.name: task.get_counters()})

    # Produce a list of events
    for key, value in adjacency_list.items():
        for e in value:
            new_vector = e
            for task in all_tasks:
                # Fill in 0's where there are missing values
                if task not in new_vector.keys():
                    new_vector.update({task: 0})

            # Since this is single-threaded, this will be monotonically incrementing.
            new_event = Event(process = key, vector = new_vector, id = len(all_events))
            all_events.append(new_event)

    happens_before = {}
    for process, vector, id in all_events:
        all_happens_before = []
        for process2, vector2, id2 in all_events:
            # We know the keys are the same, cause we filled them in earlier.
            did_happen_before = True
            for task in vector.keys():
                did_happen_before = did_happen_before and vector.get(task) >= vector2.get(task)

            if did_happen_before and id != id2:
                all_happens_before.append(id2)

        happens_before.update({id: all_happens_before})
    print(happens_before)

    # The nodes are just the list of [event.process]
    for id in happens_before.keys():
        event = all_events[id]
        dict_string = "{"
        for key in sorted(event.vector.keys()):
            dict_string += "{0}:{1} ".format(key, event.vector[key])
        dict_string += "}"
        dot.node(name = str(id), label = event.process + " : " + dict_string)
        my_graph.add_node(id)

    for id, children in happens_before.items():
        # event = all_events[id]
        for child in children:
            # child_event = all_events[child]
            # dot.edge(tail_name = str(child), head_name = str(id))
            my_graph.add_edge(child, id)

    for head, tail in my_graph.edges():
        dot.edge(tail_name = str(head), head_name = str(tail))

    dot.render(graph_name + ".gv", view = True)


if __name__ == "__main__":
    taskA = Task(name = "A")
    taskB = Task(name = "B")
    taskC = Task(name = "C")

    taskC.send_message(taskB)
    taskB.send_message(taskA)
    taskB.send_message(taskC)
    taskA.send_message(taskB)
    taskC.send_message(taskA)
    taskB.send_message(taskC)
    taskC.send_message(taskA)

    # print("A: " + str(taskA.get_counters()))
    # print("B: " + str(taskB.get_counters()))
    # print("C: " + str(taskC.get_counters()))

    graph_vectors(taskA, taskB, taskC)