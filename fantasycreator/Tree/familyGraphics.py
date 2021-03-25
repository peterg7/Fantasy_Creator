''' 

Copyright (c) 2020 Peter C Gish

See the MIT License (MIT) for more information. You should have received a copy
of the MIT License along with this program. If not, see 
<https://www.mit.edu/~amini/LICENSE.md>.
'''
__author__ = "Peter C Gish"
__date__ = "3/21/21"
__maintainer__ = "Peter C Gish"
__version__ = "1.0.1"


# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

# Built-in Modules
import heapq
from collections import Counter
import numpy as np
import csv

# 3rd Party
from ordered_set import OrderedSet

# User-defined Modules
# from graph import Graph
from fantasycreator.Mechanics.flags import RELATIONSHIP as r_flags


'''
Overview of relationship priority
======================================
Flag-defined:
 - Partner = 42
 - Descendant = 43
 - Sibling = 44
 - Parent = 45

Graphic-specific: 
 - Null = 0
 - Partner = 1
 - Descendant = 2
 - Sibling = 3
 - Parent = 4
 - Virtual = 50
'''

NULL = 0
PARTNER_FORK = 1
DESCENDANT_FORK = 2
SIBLING_FORK = 3
PARENT_FORK = 4
VIRTUAL = 50

# Spacing constants
X_CONSTANT = 10
Y_CONSTANT = 100  


def DFS_Wrapper(graph, start):
    # Create a set to store visited vertices
    visited = OrderedSet()

    DFS(graph, start, visited)

    OUTPUT.sort(key=PRINT_ORDER.get)

    for x in OUTPUT:
        CSV_TABLE.append(graph.node(x)['g_pos'])

    print(*[graph.node(x) for x in OUTPUT], sep='\n')
    # dump()


def DFS(graph, vert, visited):
    # Mark the current node as visited
    # and print it

    if vert not in ['NONE', 'ENTRY']:
        previous_node = visited[-1]
        calcOffsetRatio(graph, previous_node, vert)

    visited.add(vert)

    OUTPUT.append(vert)
    # print(vert, end="\n")

    # Recur for all the vertices adjacent to this vertex
    L = graph.nodes(from_node=vert)
    L.sort(key=lambda x: (graph.edge(vert, x),
                          graph.node(x)['r_pos'],
                          graph.node(x)['height']))
    # Dont follow sibling edges
    L = [x for x in L if graph.edge(vert, x) not in r_flags]
    for neighbour in L:
        if neighbour not in visited:
            DFS(graph, neighbour, visited)
  

def calcOffsetRatio(graph, previous, target):
    # For debuggin:
    # if target == 'FORK5':
    #     print('here')

    data = graph.node(target)
    current_fam = data['fam']
    reference_x = 0
    new_fam = False
    sub_level_size = 1 # account for target node
    height = data['height']
    relative_pos = data['r_pos']

    neighbors = []
    weights = []

    [(neighbors.append(y), weights.append(z)) for x, y, z in graph.edges(from_node=target)]

    weight_counter = Counter(weights)

    level_neighbors = [x for x, y in zip(neighbors, weights) if y in [SIBLING_FORK, PARTNER_FORK, r_flags.SIB, r_flags.PARTNER]]
    sub_level_size += len(level_neighbors)

    if 'ENTRY' in neighbors:
        reference_x = graph.node('ENTRY')['g_pos'][0]
    
    # TODO: maybe use the nodes families for this distinction?
    elif (((weight_counter[PARENT_FORK] >= 1 and \
            neighbors[weights.index(PARENT_FORK)] in FORKES) or \
            weight_counter[NULL]) and \
            PARTNER_FORK in weights) or (weight_counter[PARTNER_FORK] == 2 and \
            neighbors[weights.index(PARTNER_FORK)] not in FORKES):

        if weight_counter[PARTNER_FORK] == 1:
            if weight_counter[PARENT_FORK]:
                reference_node = neighbors[weights.index(PARENT_FORK)]
            elif weight_counter[NULL]:
                reference_node = neighbors[weights.index(r_flags.PARTNER)]
        else:
            mid_index = sub_level_size // 2 

            if relative_pos == mid_index:
                reference_pos = mid_index
            elif relative_pos < mid_index:
                reference_pos = relative_pos + 1
            else:
                reference_pos = relative_pos - 1
            
            reference_node = next((x for x in level_neighbors if graph.node(x)['r_pos'] == reference_pos), target)

            if reference_node == target:
                reference_node = previous

        reference_x = graph.node(reference_node)['g_pos'][0]
        new_fam = True
    
    elif index := [i for i in range(len(weights)) if weights[i] in [PARENT_FORK, VIRTUAL]]:
        reference_node = neighbors[index[0]]
        reference_x = graph.node(reference_node)['g_pos'][0]

    else:
        mid_index = sub_level_size // 2 

        if relative_pos == mid_index:
            reference_pos = mid_index
        elif relative_pos < mid_index:
            reference_pos = relative_pos + 1
        else:
            reference_pos = relative_pos - 1

        reference_node = next((x for x in level_neighbors if graph.node(x)['r_pos'] == reference_pos), target)

        if reference_node == target:
            for i, node in enumerate(level_neighbors):
                current_x = graph.node(node)['g_pos'][0]
                if not i:
                    min_x, max_x = current_x, current_x
                if min_x > current_x:
                    min_x = current_x
                elif max_x < current_x:
                    max_x = current_x
            
            center = (abs(max_x) - abs(min_x)) / 2

            if center:
                reference_x = np.copysign(center + abs(min_x), min_x)
            else:
                reference_x = 0
        
        else:
            reference_x = graph.node(reference_node)['g_pos'][0]
    
    if new_fam:
        orientation = np.linspace(0, sub_level_size/2, sub_level_size)[relative_pos]

    else:
        orientation = np.linspace(-sub_level_size/2,
                                sub_level_size/2, sub_level_size)[relative_pos]

    if sub_level_size == 1:
        offset = 0
    else:
        offset = ((sub_level_size) * (height+1))

    offset *= abs(orientation)
    offset = np.copysign(offset, orientation)
    x_coord = reference_x + offset


    data['g_pos'] = (x_coord, height * Y_CONSTANT)


def dump():
    with open("/Users/petergish/Desktop/output.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerows(CSV_TABLE)


class PriorityQ(object):
    def __init__(self, initial=None, key=lambda x: x):
        self.key = key
        self.index = 0
        if initial:
            self._data = [(key(item), i, item)
                          for i, item in enumerate(initial)]
            self.index = len(self._data)
            heapq.heapify(self._data)
        else:
            self._data = []

    def push(self, item):
        heapq.heappush(self._data, (self.key(item), self.index, item))
        self.index += 1

    def pop(self):
        return heapq.heappop(self._data)[2]

    def __bool__(self):
        return bool(self._data)