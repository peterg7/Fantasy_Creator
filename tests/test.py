
import heapq
from graph import Graph
from ordered_set import OrderedSet
from collections import Counter
import numpy as np
import csv

NULL = -1

# DESC_FORK = 9
# SIB_FORK = 8
# PARTNER_FORK = 6
# PARENT_FORK = 10

# DESC = 11
# SIB = 12
# PARTNER = 7
# PARENT = 13

DESC_FORK = 7
SIB_FORK = 8
PARTNER_FORK = 6
PARENT_FORK = 9

DESC = 11
SIB = 12
PARTNER = 10
PARENT = 13

VIRTUAL_LINK = 20

FORK_RELATIONS = [DESC_FORK, SIB_FORK, PARTNER_FORK, PARENT_FORK]
FAM_RELATIONS = [DESC, SIB, PARTNER, PARENT]

PRINT_ORDER = {k:v for v, k in enumerate(['NONE', 'A', 'ENTRY', 'B', 'FORK1',
                    'FORK2', 'FORK3', 'FORK4', 'FORK5', 'FORK6', 'C', 'D', 
                    'E', 'FORK7', 'FORK8', 'FORK9', 'F', 'G', 'FORK10', 
                    'H', 'FORK11', 'I', 'J'])}

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
    # OUTPUT.append(vert)
    print(vert, end="\n")

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

    # print(*[graph.node(x) for x in OUTPUT], sep='\n')
    # dump()


def dump():
    with open("/Users/petergish/Desktop/output.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerows(CSV_TABLE)


FORKS = []
def buildTree(graph, visited, target):
    ''' Every node is responsible for placing all nodes between themself and
    their neighbor excluding connections that have already been forked.
    It is important that no fork is left with only one connection. This would
    make it invisible to subsequent nodes, specifically the node on the other
    end of the fork.
    '''
    data = graph.node(target)
    height = data['height']
    fork_counter = len(FORKS)
    previous = visited[-1]
    neighbors = []
    weights = []

    # collect all neighbors and associated weights
    [(neighbors.append(y), weights.append(z)) for x, y, z in graph.edges(from_node=target)]

    # collect forks that are already connected
    neighbor_forks = [x for x in neighbors if x in FORKS] # collect all neighboring forks
    forked_connections = [y for f in neighbor_forks for x, y, z in f.edges(from_node=target)] # collect all fork connecting nodes
    neighbors, weights = zip(*((a, b) for a, b in zip(neighbors, weights) if a not in forked_connections)) # remove these nodes from neighbor as they've already been forked


    # check if this node has any descendants
    if DESC in weights:
        ''' This node has 1+ children
        '''

        # check if this node has partners
        if PARTNER in weights:
            ''' This node has at least one partner
            '''
            
            # check if this node is a head of family
            if 'NONE' in neighbors:
                ''' This node is a head of family with 1+ partner(s) and 1+ children.
                REQUIRES DROPDOWN
                '''

                # check for siblings (only place necessary because of lack of parents) 
                if SIB in weights:
                    ''' This character has siblings as a head of family. Treat like
                    a normal partner without any dropdown
                    '''

            # this node is not a head of family and has at least 1 descendant and partner
            else:
                ''' Placed in the right spot, nothing should be needed. Simply
                a summation of operations for having descendants and aprtners. 
                '''


        # this node is an only parent with 1+ children
        else:
            ''' Add fork below this node. Then place fork above all descendants
            and connect all forks + children 
            '''
        
    
    # this node does not have any descendants
    else:
        ''' No need to check for siblings, they SHOULD be handled by the parents.
        '''

        # check if this node has partners
        if PARTNER in weights:
            ''' This node is partnered with no children. Handle like normal
            partnership without a dropdown
        
            '''

        # this node is either the only member of the family or a sibling
        else:
            print('Nothing to do. Family of 1')

















































    

    #     if PARTNER in weights:
    #         fork_id = f'FORK{fork_counter}'
    #         fork_data = {'name': fork_id, 'g_pos': (0, 0), 'fam': 0}
    #         partner = neighbors[weights.index(PARTNER)]
    #         partner_data = graph.node(partner)
    #         if graph.edge(partner, 'NONE') and partner not in visited:
    #             # means both partner nodes have null parents and are heads of the family
    #             current_fork = dict(fork_data)
    #             current_fork['r_pos'] = data['r_pos']+1
    #             current_fork['height'] =  height

    #             graph.add_node(fork_id, current_fork)
    #             graph.add_edge(fork_id, target, PARTNER_FORK, True)
    #             graph.add_edge(fork_id, partner, PARTNER_FORK, True)
    #             FORKS.append(fork_id)
    #             fork_counter += 1

    #             # account for connecting fork
    #             partner_data['r_pos'] += 1

    #             if DESC in weights:
    #                 # add fork under first family head
    #                 fork_id = f'FORK{fork_counter}'
    #                 current_fork = dict(fork_data)
    #                 current_fork['r_pos'] = data['r_pos']
    #                 current_fork['height'] =  (height+1) / 3
    #                 current_fork['name'] = fork_id
    #                 graph.add_node(fork_id, current_fork)
    #                 graph.add_edge(target, fork_id, DESC_FORK)
    #                 graph.add_edge(fork_id, target, PARENT_FORK)
    #                 FORKS.append(fork_id)
    #                 fork_counter += 1

    #                 # add fork under second family head
    #                 fork_id = f'FORK{fork_counter}'
    #                 current_fork = dict(fork_data)
    #                 current_fork['r_pos'] = partner_data['r_pos']
    #                 current_fork['height'] =  (height+1) / 3
    #                 current_fork['name'] = fork_id
    #                 graph.add_node(fork_id, current_fork)
    #                 graph.add_edge(partner, fork_id, DESC_FORK)
    #                 graph.add_edge(fork_id, partner, PARENT_FORK)
    #                 FORKS.append(fork_id)
    #                 fork_counter += 1

    #                 # add lower connecting fork
    #                 fork_id = f'FORK{fork_counter}'
    #                 current_fork = dict(fork_data)
    #                 current_fork['r_pos'] = abs(data['r_pos'] - partner_data['r_pos']) / 2
    #                 current_fork['height'] =  (height+1) / 3
    #                 current_fork['name'] = fork_id
    #                 graph.add_node(fork_id, current_fork)
    #                 graph.add_edge(f'FORK{fork_counter-2}', fork_id, PARTNER_FORK, True)
    #                 graph.add_edge(f'FORK{fork_counter-1}', fork_id, PARTNER_FORK, True)
    #                 FORKS.append(fork_id)
    
        # Need to handle general case (i.e. siblings, descendants, etc)


        #     else:
        #         data['r_pos'] += 1
        #         fork_data = {'name': fork_id, 'r_pos': graph.node(previous)['r_pos']+1, 'height': height, 'g_pos': (0, 0), 'fam': 0}

        #     graph.add_node(fork_id, fork_data)
        #     graph.add_edge(fork_id, target, PARTNER_FORK, True)
        #     FORKS.append(fork_id)
        #     fork_counter += 1

        # if DESC in weights:
        #     fork_id = f'FORK{fork_counter}'

        #     fork_data = {'name': fork_id, 'r_pos': data['r_pos'], 'height': (height+1) / 3, 'g_pos': (0, 0), 'fam': 0}

        #     graph.add_node(fork_id, fork_data)
        #     graph.add_edge(fork_id, target, PARENT_FORK)
        #     graph.add_edge(target, fork_id, DESC_FORK)
        #     FORKS.append(fork_id)
        #     fork_counter += 1






X_CONSTANT = 10
Y_CONSTANT = 100
def calcOffsetRatio(graph, previous, target):
    # For debuggin:
    if target == 'C':
        print('here')

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

    # neighbors, weights = OrderedSet(zip(*connections))[0], OrderedSet(zip(*connections))[1]

    level_neighbors = [x for x, y in zip(neighbors, weights) if y in [SIB_FORK, PARTNER_FORK, SIB, PARTNER]]
    sub_level_size += len(level_neighbors)

    if 'ENTRY' in neighbors:
        reference_x = graph.node('ENTRY')['g_pos'][0]
    
    # if any(x in weights for x in [PARENT_FORK, PARENT])
    # elif PARENT_FORK in weights:
    #     reference_node = neighbors[weights.index(PARENT_FORK)]
    #     reference_x = graph.node(reference_node)['g_pos'][0]
    
    # elif VIRTUAL_LINK in weights:
    #     reference_node = neighbors[weights.index(PARENT_FORK)]
    #     reference_x = graph.node(reference_node)['g_pos'][0]
    
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
    
    elif index := [i for i in range(len(weights)) if weights[i] in [PARENT_FORK, VIRTUAL_LINK]]:
        reference_node = neighbors[index[0]]
        reference_x = graph.node(reference_node)['g_pos'][0]

    else:
        # any(x in [PARTNER_FORK, SIB_FORK] for x in weights):
    
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
        # orientation = np.linspace(0, 1, sub_level_size)[relative_pos]
        # orientation = range(sub_level_size)[relative_pos]
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
g.add_node('ENTRY', ENTRY)
g.add_node('FORK1', FORK1)
g.add_node('FORK2', FORK2)
g.add_node('FORK3', FORK3)
g.add_node('FORK4', FORK4)
g.add_node('FORK5', FORK5)
g.add_node('FORK6', FORK6)
g.add_node('FORK7', FORK7)
g.add_node('FORK8', FORK8)
g.add_node('FORK9', FORK9)
g.add_node('FORK10', FORK10)
g.add_node('FORK11', FORK11)
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
