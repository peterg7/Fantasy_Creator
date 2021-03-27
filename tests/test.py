
import heapq
from graph import Graph
from ordered_set import OrderedSet
from collections import Counter
import numpy as np
import csv
from itertools import combinations
from operator import attrgetter
import re


NULL = 1000 # want this path to never be travelled

# DESC_FORK = 9
# SIB_FORK = 8
# PARTNER_FORK = 6
# PARENT_FORK = 10

# DESC = 11
# SIB = 12
# PARTNER = 7
# PARENT = 13

PARTNER_FORK = 1
DESC_FORK = 2
SIB_FORK = 3
PARENT_FORK = 4

MAX_FORK_PATH = 40
PARTNER = 42
DESC = 43
SIB = 44
PARENT = 45

VIRTUAL_LINK = 50

FORK_RELATIONS = [DESC_FORK, SIB_FORK, PARTNER_FORK, PARENT_FORK]
FAM_RELATIONS = [DESC, SIB, PARTNER, PARENT]

PRINT_ORDER = {k:v for v, k in enumerate(['NONE', 'A', 'ROOT0', 'B', 'FORK0',
                    'FORK2', 'FORK1', 'FORK4', 'FORK3', 'FORK5', 'C', 'D', 
                    'E', 'FORK7', 'FORK6', 'FORK8', 'F', 'G', 'FORK9', 
                    'H', 'FORK10', 'I', 'FORK11', 'J'])}

OUTPUT = []
CSV_TABLE = []

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


def breadth_first_walk(graph, start, end=None, reversed_walk=False):
    """
    :param graph: Graph
    :param start: start node
    :param end: end node.
    :param reversed_walk: if True, the BFS traverse the graph backwards.
    :return: generator for walk.

    To walk all nodes use: `[n for n in g.breadth_first_walk(start)]`
    """
    TRAVERSE_ORDER = {NULL: -1, SIB: 1, PARTNER: 0, DESC: 3, PARENT: 2}
    # TRAVERSE_ORDER = {NULL: 1, FORK: 0, PARTNER: 2, SIB: 3, DESC: 4, PARENT: 5}
    visited = set([start])
    q = PriorityQ([(0, start)], key=lambda x: x[0])
    while q:

        node = q.pop()[1]
        yield node

        L = graph.nodes(from_node=node) if not reversed_walk else graph.nodes(
            to_node=node)

        if node == 'NULL':
            L = L[0]

        for next_node in L:
            if next_node not in visited:
                visited.add(next_node)
                q.push(
                    (TRAVERSE_ORDER[graph.edge(node, next_node)], next_node))

# TRAVERSE_ORDER = {NULL: 1, FORK: 0, PARTNER: 2, SIB: 4, DESC: 3, PARENT: 5}

# A function used by DFS


def DFSUtil(graph, vert, visited):
    # Mark the current node as visited
    # and print it
    
    if vert != 'NONE':
        buildTree(graph, visited, vert)
    # if vert not in ['NONE', 'ENTRY']:
    #     previous_node = visited[-1]
    #     calcOffsetRatio(graph, previous_node, vert)

    visited.add(vert)

    # print(graph.node(vert), end='\n')
    OUTPUT.append(vert)
    # print(vert, end="\n")

    # Recur for all the vertices
    # adjacent to this vertex
    L = graph.nodes(from_node=vert)
    L.sort(key=lambda x: (graph.edge(vert, x),
                          graph.node(x)['r_pos'],
                          graph.node(x)['height']))
    # Dont follow sibling edges
    # L = [x for x in L if graph.edge(vert, x) not in FAM_RELATIONS]
    for neighbour in L:
        if neighbour not in visited:
            DFSUtil(graph, neighbour, visited)

# The function to do DFS traversal. It uses
# recursive DFSUtil()


def DFS(graph, start):

    # Create a set to store visited vertices
    visited = OrderedSet()

    # Call the recursive helper function
    # to print DFS traversal
    DFSUtil(graph, start, visited)


    OUTPUT.sort(key=PRINT_ORDER.get)

    # for x in OUTPUT:
    #     CSV_TABLE.append(graph.node(x)['g_pos'])

    print(*[graph.node(x) for x in OUTPUT], sep='\n')
    # dump()


def dump():
    with open("/Users/petergish/Desktop/output.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerows(CSV_TABLE)


FORKS = OrderedSet()
ROOTS = OrderedSet()
def buildTree(graph, visited, target):
    ''' Every node is responsible for placing all nodes between themself and
    their neighbor excluding connections that have already been forked.
    It is important that no fork is left with only one connection. This would
    make it invisible to subsequent nodes, specifically the node on the other
    end of the fork.
    '''
    previous = visited[-1]
    placeForks(target, visited, graph)
    calcOffsetRatio(target, previous, graph)


def placeForks(target, visited, graph):
    data = graph.node(target)    
    neighbors = []
    weights = []

    # collect all neighbors and associated weights (excluding forks)
    [(neighbors.append(y), weights.append(z)) for x, y, z in graph.edges(from_node=target) if y not in FORKS]

    # will be needed when calculating offsets
    if target not in FORKS:

        # filter the relationships so that they don't include any "fork" paths
        relations = [(a, b) for a, b in zip(neighbors, weights) if not 0 < g.shortest_path(target, a)[0] < MAX_FORK_PATH ]
        if not relations:
            return
        neighbors, weights = zip(*relations)

        '''
        Check for exceptions
        '''
        if 'NONE' in neighbors:
            # check that partner hasn't come through 
            new_relations = [(a, b) for a, b in relations if a not in visited]
            if not new_relations:
                return

            # this parent is a head of a family
            if set([PARTNER, DESC]).issubset(weights):
                # this family has a partnership at the head with children
                # need to make the "square" dropdown

                handleFirstChildren(target, data, relations, graph)
                return
                # need to break from conditions (return here?)

        '''  
        Universally handled conditions
        '''
        if PARTNER in weights:
            # this node has a partner
            partners = [x[0] for x in relations if x[1] == PARTNER]
            handlePartners(target, data, partners, graph)
            return
        
        if DESC in weights:
            # this node has children
            children = [x[0] for x in relations if x[1] == DESC]
            handleChildren(target, data, children, graph)

        # NOTE: shouldnt need to worry about sibligns, they're handled by parents



''' Non Exceptions (not heads of family) '''
def handleChildren(parent_node, current_data, children, graph):
    # situation where node has at least 1 child
    # create forks and connect `current` + descendants to forks
    height = current_data['height']
    fork_counter = len(FORKS)
    num_children = len(children)

    if num_children < 1: # sanity check
        return

    # add fork directly below fork_counter
    graph.add_node(*forkFactory(fork_counter, (num_children // 2), (height+0.5)))
    graph.add_edge(parent_node, f'FORK{fork_counter}', DESC_FORK) 
    graph.add_edge(f'FORK{fork_counter}', parent_node, PARENT_FORK)
    center_fork = fork_counter
    FORKS.add(f'FORK{fork_counter}')
    fork_counter += 1

    # need to account for no center node meaning children after that index
    # need to be shifted
    if not num_children % 2:
        mid_index = num_children // 2
        for i in range(mid_index, num_children):
            graph.node(children[i])['r_pos'] += 1

    sib_forks = set([f'FORK{center_fork}'])
    for c_node in children:
        child_data = graph.node(c_node)

        # if odd number of children, connect middle child to upper center fork
        if child_data['r_pos'] == (num_children // 2):
            graph.add_edge(f'FORK{center_fork}', c_node, DESC_FORK) 
            graph.add_edge(c_node, f'FORK{center_fork}', PARENT_FORK)    

        else:
            # insert node above child
            graph.add_node(*forkFactory(fork_counter, child_data['r_pos'], (height+0.5)))
            graph.add_edge(f'FORK{fork_counter}', c_node, DESC_FORK) 
            graph.add_edge(c_node, f'FORK{fork_counter}', PARENT_FORK)
            sib_forks.add(f'FORK{fork_counter}')
            FORKS.add(f'FORK{fork_counter}')
            fork_counter += 1

    # connect all sibling forks to each other
    combos = set(combinations(sib_forks, 2))
    for pair in combos: # this is sexy
        graph.add_edge(pair[0], pair[1], SIB_FORK, True)



def handlePartners(current_node, current_data, partners, graph):
    # this node has 1+ partners but it does not have a null parent
    height = current_data['height']
    pos = current_data['r_pos']
    fork_counter = len(FORKS)
    # maybe find a way to not do this? like pass in relations
    children = [y for x, y, z in graph.edges(from_node=current_node) if z == DESC] 

    for p_node in partners: # WARNING won't work for more than 1 partner currently
        p_data = graph.node(p_node)

        # create new fork between partners
        graph.add_node(*forkFactory(fork_counter, p_data['r_pos'], height))
        graph.add_edge(f'FORK{fork_counter}', current_node, PARTNER_FORK, True)
        graph.add_edge(f'FORK{fork_counter}', p_node, PARTNER_FORK, True)
        FORKS.add(f'FORK{fork_counter}')
        fork_counter += 1

        if children: # WARNING definitely won't work for more than 1 partner as is
            anchor_fork_data = graph.node(f'FORK{fork_counter-1}')
            handleChildren(f'FORK{fork_counter-1}', anchor_fork_data, children, graph)

        if pos < p_data['r_pos']: # moving to the right
            p_data['r_pos'] += 1

        else:  # moving to the left
            p_data['r_pos'] -= 1


''' Exceptions (null parents) '''
# The first head is responsible for building the entire drop down
# Should only be called once per family at most
# Definitely can't handle more than 3 partners and even that is iffy
def handleFirstChildren(current_node, current_data, relations, graph):

    height = current_data['height']
    pos = current_data['r_pos']
    fork_counter = len(FORKS)
    partners = [x[0] for x in relations if x[1] == PARTNER]
    

    # establish fork directly below current_node
    graph.add_node(*forkFactory(fork_counter, pos, (height+1)*(1/3)))
    graph.add_edge(current_node, f'FORK{fork_counter}', DESC_FORK)
    graph.add_edge(f'FORK{fork_counter}', current_node, PARENT_FORK)
    inline_drop = fork_counter
    FORKS.add(f'FORK{fork_counter}')
    fork_counter += 1

    # need to keep track of outer most lower nodes for virtual connection with descendants
    left_connect_fork, right_connect_fork = f'ROOT{inline_drop}', f'ROOT{inline_drop}'

    # WARNING: not confident this will work for multiple partners
    for p_node in partners:
        partner_data = graph.node(p_node)

        # insert node between partner and current node
        root_fork_id = f'ROOT{len(ROOTS)}'
        root_fork = list(forkFactory(fork_counter, partner_data['r_pos'], height))
        root_fork[0] = root_fork_id
        root_fork[1]['name'] = root_fork_id
        graph.add_node(root_fork[0], root_fork[1])
        graph.add_edge(root_fork_id, current_node, PARTNER_FORK, True)
        graph.add_edge(root_fork_id, p_node, PARTNER_FORK, True)
        ROOTS.add(root_fork_id)
        # FORKS.add(f'FORK{fork_counter}')
        # fork_counter += 1 
        
        if pos < partner_data['r_pos']: # moving to the right
            partner_data['r_pos'] += 1
            right_connect_fork = f'FORK{fork_counter}'

        else:  # moving to the left
            partner_data['r_pos'] -= 1
            left_connect_fork = f'FORK{fork_counter}'

        # add fork under this parent and connect to fork under current node
        graph.add_node(*forkFactory(fork_counter, partner_data['r_pos'], (height+1)*(1/3)))
        graph.add_edge(p_node, f'FORK{fork_counter}', DESC_FORK) 
        graph.add_edge(f'FORK{fork_counter}', p_node, PARENT_FORK)
        graph.add_edge(f'FORK{fork_counter}', f'ROOT{inline_drop}', PARTNER_FORK, True)
        FORKS.add(f'FORK{fork_counter}')
        fork_counter += 1

        # add lower fork between the nodes
        graph.add_node(*forkFactory(fork_counter, (abs(pos - partner_data['r_pos']) // 2), (height+1)*(1/3)))
        graph.add_edge(f'ROOT{inline_drop}', f'FORK{fork_counter}', PARTNER_FORK, True)
        graph.add_edge(f'FORK{fork_counter-1}', f'FORK{fork_counter}', PARTNER_FORK, True)
        FORKS.add(f'FORK{fork_counter}')
        fork_counter += 1
    
    # fork_counter-1 now represents the access point to the head of family's dropdown
    # add fork directly below fork_counter

    children = [x[0] for x in relations if x[1] == DESC]
    access_fork_id = f'FORK{fork_counter-1}' 
    adjusted_height_data = dict(graph.node(access_fork_id))
    adjusted_height_data['height'] = 1/6 # account for handleChildren adding 1/2
    handleChildren(access_fork_id, adjusted_height_data, 
                                children, graph)
    
    # FIXME very inefficient
    left_child, right_child = min(children, key=lambda x:graph.node(x)['r_pos']), \
                                max(children, key=lambda x:graph.node(x)['r_pos'])

    left_desc_fork = next(y for x, y, z in graph.edges(from_node=left_child) if z == PARENT_FORK)
    right_desc_fork = next(y for x, y, z in graph.edges(from_node=right_child) if z == PARENT_FORK)

    graph.add_edge(left_desc_fork, left_connect_fork, VIRTUAL_LINK)
    graph.add_edge(right_desc_fork, right_connect_fork, VIRTUAL_LINK)

# helper method to produce forks
def forkFactory(_id, pos, height):
    fork_id = f'FORK{_id}'
    fork_data = {'name': fork_id,
                'r_pos':pos, 
                'height': height,
                'g_pos': (0, 0),
                'fam': 0}
    return(fork_id, fork_data)


X_CONSTANT = 10
Y_CONSTANT = 100
def calcOffsetRatio(target, previous, graph):
    # For debuggin:
    if target == 'G':
        print('here')

    # don't adjust the root
    if re.match(r'ROOT\d*', target):
        return

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

    # gather all neighbors that are on the same level
    level_neighbors = [x for x, y in zip(neighbors, weights) if y in [SIB_FORK, PARTNER_FORK, SIB, PARTNER]]
    sub_level_size += len(level_neighbors)
    if not sub_level_size % 2: # need to account for "empty" fork
         sub_level_size += 1
    
    

    # first priority is get reference from the root of the tree
    if match := re.search(r"ROOT\d*", r"(?=(" + "|".join(neighbors) + r"))"):
        reference_x = graph.node(match[0])['g_pos'][0]
    
    # Detect that these nodes are partners connecting new families
    # that aren't roots 
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
                reference_node = neighbors[weights.index(PARTNER)]
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
    
    # check if this node is a descendent (or has a virtual link up to a head of family)
    elif index := [i for i in range(len(weights)) if weights[i] in [PARENT_FORK, VIRTUAL_LINK]]:
        reference_node = neighbors[index[0]]
        reference_x = graph.node(reference_node)['g_pos'][0]

    # base case
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
        # offset = ((sub_level_size/X_SPACER) * (height+1) * X_SPACER)
        offset = ((sub_level_size) * (height+1))
    
    # if not reference_x:
    #     reference_x = 1
    # offset *= reference_x
    offset *= abs(orientation)
    # offset *= X_CONSTANT
    offset = np.copysign(offset, orientation)
    x_coord = reference_x + offset


    data['g_pos'] = (x_coord, height * Y_CONSTANT)



g = Graph()

NONE = {'name': 'NONE', 'r_pos': -1, 'height': -1, 'g_pos': (0, 0), 'fam': -1}
ENTRY = {'name': 'ENTRY', 'r_pos': 1, 'height': 0, 'g_pos': (100, 0), 'fam': -1}
FORK1 = {'name': 'FORK1', 'r_pos': 0, 'height': 0.33, 'g_pos': (0, 0), 'fam': 0}
FORK2 = {'name': 'FORK2', 'r_pos': 1, 'height': 0.33, 'g_pos': (0, 0), 'fam': 0}
FORK3 = {'name': 'FORK3', 'r_pos': 2, 'height': 0.33, 'g_pos': (0, 0), 'fam': 0}
FORK4 = {'name': 'FORK4', 'r_pos': 0, 'height': 0.66, 'g_pos': (0, 0), 'fam': 0}
FORK5 = {'name': 'FORK5', 'r_pos': 1, 'height': 0.66, 'g_pos': (0, 0), 'fam': 0}
FORK6 = {'name': 'FORK6', 'r_pos': 2, 'height': 0.66, 'g_pos': (0, 0), 'fam': 0}
FORK7 = {'name': 'FORK7', 'r_pos': 0, 'height': 1.5, 'g_pos': (0, 0), 'fam': 0}
FORK8 = {'name': 'FORK8', 'r_pos': 1, 'height': 1.5, 'g_pos': (0, 0), 'fam': 0}
FORK9 = {'name': 'FORK9', 'r_pos': 2, 'height': 1.5, 'g_pos': (0, 0), 'fam': 0}
FORK10 = {'name': 'FORK10', 'r_pos': 0, 'height': 1.5, 'g_pos': (0, 0), 'fam': 0}
FORK11 = {'name': 'FORK11', 'r_pos': 1, 'height': 2.5, 'g_pos': (0, 0), 'fam': 0}

FORKES = ['FORK1', 'FORK2', 'FORK3', 'FORK4', 'FORK5', 'FORK6', 'FORK7',
          'FORK8', 'FORK9', 'FORK10', 'FORK11']

A = {'name': 'A', 'r_pos': 0, 'height': 0, 'g_pos': (0, 0), 'fam': 1}
B = {'name': 'B', 'r_pos': 1, 'height': 0, 'g_pos': (0, 0), 'fam': 2}

C = {'name': 'C', 'r_pos': 0, 'height': 1, 'g_pos': (0, 0), 'fam': 1}
D = {'name': 'D', 'r_pos': 1, 'height': 1, 'g_pos': (0, 0), 'fam': 1}
E = {'name': 'E', 'r_pos': 2, 'height': 1, 'g_pos': (0, 0), 'fam': 1}

F = {'name': 'F', 'r_pos': 0, 'height': 2, 'g_pos': (0, 0), 'fam': 1}
G = {'name': 'G', 'r_pos': 1, 'height': 2, 'g_pos': (0, 0), 'fam': 1}

H = {'name': 'H', 'r_pos': 0, 'height': 2, 'g_pos': (0, 0), 'fam': 1}
I = {'name': 'I', 'r_pos': 1, 'height': 2, 'g_pos': (0, 0), 'fam': 3}
J = {'name': 'J', 'r_pos': 0, 'height': 3, 'g_pos': (0, 0), 'fam': 4}

g.add_node('NONE', NONE)
# g.add_node('ENTRY', ENTRY)
# g.add_node('FORK1', FORK1)
# g.add_node('FORK2', FORK2)
# g.add_node('FORK3', FORK3)
# g.add_node('FORK4', FORK4)
# g.add_node('FORK5', FORK5)
# g.add_node('FORK6', FORK6)
# g.add_node('FORK7', FORK7)
# g.add_node('FORK8', FORK8)
# g.add_node('FORK9', FORK9)
# g.add_node('FORK10', FORK10)
# g.add_node('FORK11', FORK11)
g.add_node('A', A)
g.add_node('B', B)
g.add_node('C', C)
g.add_node('D', D)
g.add_node('E', E)
g.add_node('F', F)
g.add_node('G', G)
g.add_node('H', H)
g.add_node('I', I)
g.add_node('J', J)

g.add_edge('NONE', 'A', NULL, True)
g.add_edge('NONE', 'B', NULL, True)
g.add_edge('NONE', 'I', NULL, True)

# g.add_edge('A', 'ENTRY', PARTNER_FORK, True)
# g.add_edge('B', 'ENTRY', PARTNER_FORK, True)

# g.add_edge('FORK1', 'FORK3', PARTNER_FORK, True)
# g.add_edge('FORK1', 'FORK2', PARTNER_FORK, True)
# g.add_edge('FORK1', 'A', PARENT_FORK)

# g.add_edge('FORK2', 'FORK3', PARTNER_FORK, True)
# g.add_edge('FORK2', 'FORK5', DESC_FORK, True)

# g.add_edge('FORK3', 'B', PARENT_FORK, True)

# g.add_edge('FORK4', 'FORK1', VIRTUAL_LINK)
# g.add_edge('FORK4', 'FORK6', SIB_FORK, True)
# g.add_edge('FORK4', 'FORK5', SIB_FORK, True)
# g.add_edge('FORK4', 'C', DESC_FORK)

# g.add_edge('FORK5', 'FORK2', PARENT_FORK)
# g.add_edge('FORK5', 'FORK6', SIB_FORK, True)
# g.add_edge('FORK5', 'D', DESC_FORK)

# g.add_edge('FORK6', 'FORK3', VIRTUAL_LINK)
# g.add_edge('FORK6', 'E', DESC_FORK)

# g.add_edge('FORK7', 'FORK8', SIB_FORK, True)
# g.add_edge('FORK7', 'FORK9', SIB_FORK, True)
# g.add_edge('FORK7', 'F', DESC_FORK)

# g.add_edge('FORK8', 'FORK9', SIB_FORK, True)
# g.add_edge('FORK8', 'C', PARENT_FORK)

# g.add_edge('FORK9', 'G', DESC_FORK)

# g.add_edge('FORK10', 'E', PARENT_FORK)
# g.add_edge('FORK10', 'H', DESC_FORK)

# g.add_edge('FORK11', 'H', PARTNER_FORK, True)
# g.add_edge('FORK11', 'I', PARTNER_FORK, True)
# g.add_edge('FORK11', 'J', DESC_FORK)

# g.add_edge('A', 'FORK1', DESC_FORK)
g.add_edge('A', 'B', PARTNER, True)
g.add_edge('A', 'C', DESC)
g.add_edge('A', 'D', DESC)
g.add_edge('A', 'E', DESC)

# g.add_edge('B', 'FORK3', DESC_FORK)
g.add_edge('B', 'C', DESC)
g.add_edge('B', 'D', DESC)
g.add_edge('B', 'E', DESC)

# g.add_edge('C', 'FORK4', PARENT_FORK)
# g.add_edge('C', 'FORK8', DESC_FORK)
g.add_edge('C', 'A', PARENT)
g.add_edge('C', 'B', PARENT)
g.add_edge('C', 'D', SIB, True)
g.add_edge('C', 'E', SIB, True)
g.add_edge('C', 'F', DESC)
g.add_edge('C', 'G', DESC)

# g.add_edge('D', 'FORK5', PARENT_FORK)
g.add_edge('D', 'A', PARENT)
g.add_edge('D', 'B', PARENT)
g.add_edge('D', 'E', SIB, True)

# g.add_edge('E', 'FORK6', PARENT_FORK)
# g.add_edge('E', 'FORK10', DESC_FORK)
g.add_edge('E', 'A', PARENT)
g.add_edge('E', 'B', PARENT)
g.add_edge('E', 'H', DESC)

# g.add_edge('F', 'FORK7', PARENT_FORK)
g.add_edge('F', 'C', PARENT)
g.add_edge('F', 'G', SIB, True)

# g.add_edge('G', 'FORK9', PARENT_FORK)
g.add_edge('G', 'C', PARENT)

# g.add_edge('H', 'FORK10', PARENT_FORK)
g.add_edge('H', 'E', PARENT)
g.add_edge('H', 'I', PARTNER, True)
g.add_edge('H', 'J', DESC)

g.add_edge('I', 'J', DESC)

# g.add_edge('J', 'FORK11', PARENT_FORK)
g.add_edge('J', 'H', PARENT)
g.add_edge('J', 'I', PARENT)

DFS(g, 'NONE')
# print()
# print(g.edges())
# print()
# print(g.nodes())
# for x in breadth_first_walk(g, 'NONE'):
#     print(x)























