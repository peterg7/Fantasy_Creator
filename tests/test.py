
import heapq
from graph import Graph
from ordered_set import OrderedSet
from collections import Counter
import numpy as np
import csv
from itertools import combinations
from operator import attrgetter
import re

# want these path to never be traveled
NULL = 1000 
VIRTUAL_LINK = 100

# Relative relationship weights
PARTNER_FORK = 1
DESC_FORK = 2
SIB_FORK = 3
PARENT_FORK = 4

MAX_FORK_PATH = 40
PARTNER = 42
DESC = 43
SIB = 44
PARENT = 45

FORK_RELATIONS = [DESC_FORK, SIB_FORK, PARTNER_FORK, PARENT_FORK]
FAM_RELATIONS = [DESC, SIB, PARTNER, PARENT]

TREE_ANCHORS = ['ROOT0']
OUTPUT = []
CSV_TABLE = []

# XXX: Purely for testing/visualization
PRINT_ORDER = {k:v for v, k in enumerate(['NONE', 'A', 'ROOT0', 'B', 'FORK0',
                    'FORK2', 'FORK1', 'FORK4', 'FORK3', 'FORK5', 'C', 'D', 
                    'E', 'FORK8', 'FORK9', 'FORK7', 'FORK10', 'FORK11', 'F', 'X', 'G', 'K', 
                    'FORK6', 'H', 'ROOT1', 'I', 'FORK13', 'FORK12', 'FORK14', 'J', 'Y', 'Z'])}

# Recursive function used by DFS
def DFSUtil(graph, vert, visited):

    if vert != 'NONE':
        buildTree(graph, visited, vert)

    visited.add(vert)

    OUTPUT.append(vert)

    # Reoccur for all the vertices adjacent to this vertex
    L = graph.nodes(from_node=vert)
    L.sort(key=lambda x: (graph.node(x)['height'],
                            graph.edge(vert, x),
                            graph.node(x)['r_pos']))

    for neighbour in L:
        if neighbour not in visited:
            DFSUtil(graph, neighbour, visited)

# Wrapper function for DFS
def DFS(graph, start):

    # Create a set to store visited vertices
    visited = OrderedSet()

    # Call the recursive helper function build the tree
    DFSUtil(graph, start, visited)

    # XXX: Just debugging
    OUTPUT.sort(key=PRINT_ORDER.get)
    for x in OUTPUT:
        CSV_TABLE.append(graph.node(x)['g_pos'])

    # print(*[graph.node(x) for x in OUTPUT], sep='\n')
    dump()


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
    # Place forks in the graph between connections
    placeForks(target, visited, graph)
    # Determine the offest ratio for this node
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

    # sort children by position
    children.sort(key=lambda x: graph.node(x)['r_pos'])

    # add fork directly below fork_counter
    graph.add_node(*forkFactory(fork_counter, (num_children // 2), (height+0.5)))
    graph.add_edge(parent_node, f'FORK{fork_counter}', DESC_FORK) 
    graph.add_edge(f'FORK{fork_counter}', parent_node, PARENT_FORK)
    center_fork = fork_counter
    FORKS.add(f'FORK{fork_counter}')
    fork_counter += 1

    # need to account for no center node meaning children after that index
    # need to be shifted
    middle_child = True
    if not num_children % 2:
        middle_child = False
        for i in range(num_children // 2, num_children):
            graph.node(children[i])['r_pos'] += 1

    sib_forks = set([f'FORK{center_fork}'])
    for c_node in children:
        child_data = graph.node(c_node)

        # if odd number of children, connect middle child to upper center fork
        if middle_child and child_data['r_pos'] == (num_children // 2):
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

    # WARNING won't work for more than 1 partner currently
    for p_node in partners: 
        p_data = graph.node(p_node)

        # create new fork between partners
        root_fork_id = f'ROOT{len(ROOTS)}'
        root_fork = list(forkFactory(fork_counter, p_data['r_pos'], height))
        root_fork[0] = root_fork_id
        root_fork[1]['name'] = root_fork_id
        graph.add_node(root_fork[0], root_fork[1])
        graph.add_edge(root_fork_id, current_node, PARTNER_FORK, True)
        graph.add_edge(root_fork_id, p_node, PARTNER_FORK, True)
        ROOTS.add(root_fork_id)

        # WARNING definitely won't work for more than 1 partner as is
        if children: 
            handleChildren(root_fork[0], root_fork[1], children, graph)

            # add virtual link to lower node so the child(ren) is/are accessible
            graph.add_edge(current_node, f'FORK{fork_counter}', VIRTUAL_LINK)
            graph.add_edge(p_node, f'FORK{fork_counter}', VIRTUAL_LINK)


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
    left_connect_fork, right_connect_fork = f'FORK{inline_drop}', f'FORK{inline_drop}'

    # WARNING: not confident this will work for multiple partners
    # XXX: Try and combine this with handlePartners to consolidate 
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
        graph.add_edge(f'FORK{fork_counter}', f'FORK{inline_drop}', PARTNER_FORK, True)
        FORKS.add(f'FORK{fork_counter}')
        fork_counter += 1

        # add lower fork between the nodes and connect lower nodes
        graph.add_node(*forkFactory(fork_counter, (abs(pos - partner_data['r_pos']) // 2), (height+1)*(1/3)))
        graph.add_edge(f'FORK{inline_drop}', f'FORK{fork_counter}', PARTNER_FORK, True)
        graph.add_edge(f'FORK{fork_counter-1}', f'FORK{fork_counter}', PARTNER_FORK, True)
        graph.add_edge(f'FORK{fork_counter-1}', f'FORK{inline_drop}', PARTNER_FORK, True)
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
                'g_pos': [0, 0],
                'fam': 0}
    return(fork_id, fork_data)

# Visualization adjustments (spacing)
X_CONSTANT = 10
Y_CONSTANT = 100
SQUISH_SIBS = set()
def calcOffsetRatio(target, previous, graph):
    # For debuggin:
    if target == 'FORK7':
        print('here')

    # don't adjust the anchors
    if target in TREE_ANCHORS:
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
    
    # FIXME: this needs work (figure out spacing in even number of children)
    if not sub_level_size % 2 and relative_pos >= sub_level_size // 2 : # need to account for "empty" fork
        relative_pos -= 1
    
    
    # deal with roots
    if match := re.search(r"ROOT\d*", r"(?=(" + "|".join(neighbors) + "|" + target + r"))"):
        # first priority is determine reference from an anchor
        if match[0] in TREE_ANCHORS:
            reference_x = graph.node(match[0])['g_pos'][0]

        # single exception? might be able to encoporate into another condition (the fork under non-anchor root)
        elif graph.edge(target, match[0]) == PARENT_FORK:
            reference_x = graph.node(match[0])['g_pos'][0]

        # Detect that these nodes are partners connecting new families
        # that aren't anchors 
        else:
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
    
    # check if this node is a parent (or has a virtual link up to a head of family)
    elif set([PARENT_FORK, VIRTUAL_LINK]).intersection(set(weights)):
        node_index = weights.index(PARENT_FORK) if PARENT_FORK in weights else -1
        if node_index < 0:
            node_index = weights.index(VIRTUAL_LINK)
        reference_node = neighbors[node_index]
        reference_x = graph.node(reference_node)['g_pos'][0]
        if set([PARENT_FORK, SIB_FORK]).issubset(set(weights)) and not set([DESC_FORK, PARTNER_FORK]).intersection(set(weights)): # center fork with no offspring
            SQUISH_SIBS.update([x for x, y in zip(neighbors, weights) if y == SIB_FORK])
            SQUISH_SIBS.add(target)

    # base case
    else:
        mid_index = sub_level_size // 2 # will be the one guarenteed to have been visited
        reference_node = next((x for x in level_neighbors if graph.node(x)['r_pos'] == mid_index), target)

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
    
    if target in SQUISH_SIBS:
        sub_level_size -= 1
        orientation = np.insert(np.linspace(-sub_level_size/2,
                                sub_level_size/2, sub_level_size), sub_level_size // 2, 0)[relative_pos]

    elif new_fam:
        orientation = np.linspace(0, sub_level_size/2, sub_level_size)[relative_pos]

    else:
        orientation = np.linspace(-sub_level_size/2,
                                sub_level_size/2, sub_level_size)[relative_pos]

    if sub_level_size == 1:
        offset = 0
    else:
        offset = (2 * sub_level_size * X_CONSTANT) + (X_CONSTANT) / ((height+1) * sub_level_size)

    offset *= abs(orientation)
    offset = np.copysign(offset, orientation)
    x_coord = reference_x + offset

    # # align parent fork with this node
    if PARENT_FORK in weights:
        parent_fork = graph.node(neighbors[weights.index(PARENT_FORK)])
        parent_fork['g_pos'][0] = x_coord


    data['g_pos'] = [x_coord, height * Y_CONSTANT]


g = Graph()

NONE = {'name': 'NONE', 'r_pos': -1, 'height': -1, 'g_pos': [0, 0], 'fam': -1}
ENTRY = {'name': 'ENTRY', 'r_pos': 1, 'height': 0, 'g_pos': [100, 0], 'fam': -1}
FORK1 = {'name': 'FORK1', 'r_pos': 0, 'height': 0.33, 'g_pos': [0, 0], 'fam': 0}
FORK2 = {'name': 'FORK2', 'r_pos': 1, 'height': 0.33, 'g_pos': [0, 0], 'fam': 0}
FORK3 = {'name': 'FORK3', 'r_pos': 2, 'height': 0.33, 'g_pos': [0, 0], 'fam': 0}
FORK4 = {'name': 'FORK4', 'r_pos': 0, 'height': 0.66, 'g_pos': [0, 0], 'fam': 0}
FORK5 = {'name': 'FORK5', 'r_pos': 1, 'height': 0.66, 'g_pos': [0, 0], 'fam': 0}
FORK6 = {'name': 'FORK6', 'r_pos': 2, 'height': 0.66, 'g_pos': [0, 0], 'fam': 0}
FORK7 = {'name': 'FORK7', 'r_pos': 0, 'height': 1.5, 'g_pos': [0, 0], 'fam': 0}
FORK8 = {'name': 'FORK8', 'r_pos': 1, 'height': 1.5, 'g_pos': [0, 0], 'fam': 0}
FORK9 = {'name': 'FORK9', 'r_pos': 2, 'height': 1.5, 'g_pos': [0, 0], 'fam': 0}
FORK10 = {'name': 'FORK10', 'r_pos': 0, 'height': 1.5, 'g_pos': [0, 0], 'fam': 0}
FORK11 = {'name': 'FORK11', 'r_pos': 1, 'height': 2.5, 'g_pos': [0, 0], 'fam': 0}

FORKES = ['FORK1', 'FORK2', 'FORK3', 'FORK4', 'FORK5', 'FORK6', 'FORK7',
          'FORK8', 'FORK9', 'FORK10', 'FORK11']

A = {'name': 'A', 'r_pos': 0, 'height': 0, 'g_pos': [0, 0], 'fam': 1}
B = {'name': 'B', 'r_pos': 1, 'height': 0, 'g_pos': [0, 0], 'fam': 2}

C = {'name': 'C', 'r_pos': 0, 'height': 1, 'g_pos': [0, 0], 'fam': 1}
D = {'name': 'D', 'r_pos': 1, 'height': 1, 'g_pos': [0, 0], 'fam': 1}
E = {'name': 'E', 'r_pos': 2, 'height': 1, 'g_pos': [0, 0], 'fam': 1}

F = {'name': 'F', 'r_pos': 0, 'height': 2, 'g_pos': [0, 0], 'fam': 1}
X = {'name': 'X', 'r_pos': 1, 'height': 2, 'g_pos': [0, 0], 'fam': 1}
G = {'name': 'G', 'r_pos': 2, 'height': 2, 'g_pos': [0, 0], 'fam': 1}
K = {'name': 'K', 'r_pos': 3, 'height': 2, 'g_pos': [0, 0], 'fam': 1} 

H = {'name': 'H', 'r_pos': 0, 'height': 2, 'g_pos': [0, 0], 'fam': 1}
I = {'name': 'I', 'r_pos': 1, 'height': 2, 'g_pos': [0, 0], 'fam': 3}
J = {'name': 'J', 'r_pos': 0, 'height': 3, 'g_pos': [0, 0], 'fam': 4}
Y = {'name': 'Y', 'r_pos': 1, 'height': 3, 'g_pos': [0, 0], 'fam': 4}
Z = {'name': 'Z', 'r_pos': 2, 'height': 3, 'g_pos': [0, 0], 'fam': 4}


g.add_node('NONE', NONE)
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
g.add_node('X', X)
g.add_node('Y', Y)
g.add_node('Z', Z)
g.add_node('K', K)

g.add_edge('NONE', 'A', NULL, True)
g.add_edge('NONE', 'B', NULL, True)
g.add_edge('NONE', 'I', NULL, True)

g.add_edge('A', 'B', PARTNER, True)
g.add_edge('A', 'C', DESC)
g.add_edge('A', 'D', DESC)
g.add_edge('A', 'E', DESC)

g.add_edge('B', 'C', DESC)
g.add_edge('B', 'D', DESC)
g.add_edge('B', 'E', DESC)

g.add_edge('C', 'A', PARENT)
g.add_edge('C', 'B', PARENT)
g.add_edge('C', 'D', SIB, True)
g.add_edge('C', 'E', SIB, True)
g.add_edge('C', 'F', DESC)
g.add_edge('C', 'G', DESC)
g.add_edge('C', 'X', DESC)
g.add_edge('C', 'K', DESC)

g.add_edge('D', 'A', PARENT)
g.add_edge('D', 'B', PARENT)
g.add_edge('D', 'E', SIB, True)

g.add_edge('E', 'A', PARENT)
g.add_edge('E', 'B', PARENT)
g.add_edge('E', 'H', DESC)

g.add_edge('F', 'C', PARENT)
g.add_edge('F', 'G', SIB, True)
g.add_edge('F', 'X', SIB, True)
g.add_edge('F', 'K', SIB, True)

g.add_edge('G', 'C', PARENT)
g.add_edge('G', 'X', SIB, True)
g.add_edge('G', 'K', SIB, True)

g.add_edge('X', 'C', PARENT)
g.add_edge('X', 'K', SIB, True)

g.add_edge('K', 'C', PARENT)

g.add_edge('H', 'E', PARENT)
g.add_edge('H', 'I', PARTNER, True)
g.add_edge('H', 'J', DESC)
g.add_edge('H', 'Y', DESC)
g.add_edge('H', 'Z', DESC)

g.add_edge('I', 'J', DESC)
g.add_edge('I', 'Y', DESC)
g.add_edge('I', 'Z', DESC)

g.add_edge('J', 'H', PARENT)
g.add_edge('J', 'I', PARENT)
g.add_edge('J', 'Y', SIB, True)
g.add_edge('J', 'Z', SIB, True)

g.add_edge('Y', 'H', PARENT)
g.add_edge('Y', 'I', PARENT)
g.add_edge('Y', 'Z', SIB, True)

g.add_edge('Z', 'H', PARENT)
g.add_edge('Z', 'I', PARENT)


DFS(g, 'NONE')






















