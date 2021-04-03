''' 
This file contains all functions necessary to produce a graphically built
graph that can be displayed on the screen's coordinate system. 

Copyright (c) 2020 Peter C Gish

See the MIT License (MIT) for more information. You should have received a copy
of the MIT License along with this program. If not, see 
<https://www.mit.edu/~amini/LICENSE.md>.
'''
__author__ = "Peter C Gish"
__date__ = "3/30/21"
__maintainer__ = "Peter C Gish"
__version__ = "1.0.1"


# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

# Built-in Modules
import re
import csv # simply for debugging
from collections import Counter
from itertools import combinations


# 3rd Party
import numpy as np
from graph import Graph
from ordered_set import OrderedSet

# User-defined Modules
from fantasycreator.Data.treeGraph import invalidNode
from fantasycreator.Mechanics.flags import RELATIONSHIP as r_flags

# FIXME: need to adjust criteria to pull from character nodes instead of a dictionary

'''
Overview of relationship priority
======================================
Flag-defined:
 - Partner = 42
 - Descendant = 43
 - Sibling = 44
 - Parent = 45

Graphic-specific: 
 - Null = 10000
 - Partner = 1
 - Descendant = 2
 - Sibling = 3
 - Parent = 4
 - Virtual = 10000
'''
# represents the longest fork path until the path may involve a non-fork relationship
MAX_FORK_PATH = r_flags.PARTNER - 1 
NULL = 1000 # should be avoided through shortest path search
PARTNER_FORK = 1
DESCENDANT_FORK = 2
SIBLING_FORK = 3
PARENT_FORK = 4
VIRTUAL = 1000 # should be avoided through shortest path search

# Spacing constants
X_CONSTANT = 10
Y_CONSTANT = 100  

class FamilyGraphics(Family, qtw.QGraphicsObject):

    TREE_ANCHORS = [] # user determined? 
    FORKS = set()
    ROOTS = set()
    LINES = set()

    # TODO: need methods for adding/removing characters + adjusting for filters and flags
    def __init__(self, graph, anchors, null_node, parent=None):
        super(FamilyGraphics, self).__init__(parent)
        self.TREE_ANCHORS = anchors
        self.NULL_NODE = null_node
        self.display_graph = Graph()
        for n in graph.nodes():
            self.display_graph.add_node(n, graph.node(n))
        self.display_graph.from_dict(graph.to_dict())
        self._shape = qtg.QPainterPath()
    
    # TODO: implement name tag
    # def setName(self, name):



    # def buildNameTag(self, root_pos, name):
    #     self.name_graphic.setPlainText(name)
    #     size = qtc.QRectF(self.font_metric.boundingRect(name))
    #     self.name_graphic.setPos(root_pos)
    #     self._shape.addRect(self.name_graphic.sceneBoundingRect())


    # NOTE: this is the entry point into the entire graphics function
    # TODO: don't rebuild tree. Detect forks/node removal/addition and adjust from there
    def buildTree(self, start):
        ''' Every node is responsible for placing all nodes between themself and
        their neighbor excluding connections that have already been forked.
        It is important that no fork is left with only one connection. This would
        make it invisible to subsequent nodes, specifically the node on the other
        end of the fork.
        '''
        # Create a set to store visited vertices
        visited = OrderedSet()

        # Call the recursive helper function build the tree
        DFS_Traverse(start, visited)


    # Recursive function used by DFS
    def DFS_Traverse(self, vert, visited):

        # TODO: replace with NULL equivalent
        if vert != self.NULL_NODE: 
            # Place forks in the graph between connections
            placeForks(vert, visited)
            # Determine the offest ratio for this node
            layoutGraphics(vert, visited)

        visited.add(vert)

        # Reoccur for all the vertices adjacent to this vertex
        # TODO: implement these for the family tree
        L = self.display_graph.nodes(from_node=vert)
        L.sort(key=lambda x: (self.display_graph.node(x).getHeight(),
                                self.display_graph.edge(vert, x),
                                self.display_graph.node(x).getPos()))

        for neighbour in L:
            if neighbour not in visited:
                DFS_Traverse(neighbour, visited)


    def placeForks(self, target, visited):
        data = self.display_graph.node(target)    
        neighbors = []
        weights = []

        # collect all neighbors and associated weights (excluding forks)
        [(neighbors.append(y), weights.append(z)) for x, y, z in self.display_graph.edges(from_node=target) if y not in FORKS]

        # will be needed when calculating offsets
        if target not in FORKS:

            # filter the relationships so that they don't include any "fork" paths
            relations = [(a, b) for a, b in zip(neighbors, weights)
                                        if not 0 < self.display_graph.shortest_path(target, a)[0] < MAX_FORK_PATH]
            if not relations:
                return
            neighbors, weights = zip(*relations)

            '''
            Check for exceptions
            '''
            if self.NULL_NODE in neighbors:
                # check that partner hasn't come through 
                new_relations = [(a, b) for a, b in relations if a not in visited]
                if not new_relations:
                    return

                # this parent is a head of a family
                if set([r_flags.PARTNER, r_flags.DESCENDANT]).issubset(weights):
                    # this family has a partnership at the head with children
                    # need to make the "square" dropdown

                    handleFirstChildren(target, data, relations)
                    return

            '''  
            Universally handled conditions
            '''
            if r_flags.PARTNER in weights:
                # this node has a partner
                partners = [x[0] for x in relations if x[1] == r_flags.PARTNER]
                handlePartners(target, data, partners)
                return
            
            if r_flags.DESCENDANT in weights:
                # this node has children
                children = [x[0] for x in relations if x[1] == r_flags.DESCENDANT]
                handleChildren(target, data, children)

            # NOTE: shouldnt need to worry about sibligns, they're handled by parents



    ''' Non Exceptions (not heads of family) '''
    def handleChildren(self, parent_node, current_data, children):
        # situation where node has at least 1 child
        # create forks and connect `current` + descendants to forks
        height = current_data.getHeight()
        fork_counter = len(FORKS)
        num_children = len(children)

        # sort children by position
        children.sort(key=lambda x: self.display_graph.node(x).getPos())

        # add fork directly below fork_counter
        self.display_graph.add_node(*self.forkFactory(fork_counter, (num_children // 2), (height+0.5)))
        self.display_graph.add_edge(parent_node, f'FORK{fork_counter}', DESCENDANT_FORK) 
        self.display_graph.add_edge(f'FORK{fork_counter}', parent_node, PARENT_FORK)
        center_fork = fork_counter
        self.FORKS.add(f'FORK{fork_counter}')
        fork_counter += 1

        # need to account for no center node meaning children after that index
        # need to be shifted
        middle_child = True
        if not num_children % 2:
            middle_child = False
            for i in range(num_children // 2, num_children):
                self.display_graph.node(children[i]).offsetPos(1)

        sib_forks = set([f'FORK{center_fork}'])
        for c_node in children:
            child_data = self.display_graph.node(c_node)

            # if odd number of children, connect middle child to upper center fork
            if middle_child and child_data.getPos() == (num_children // 2):
                self.display_graph.add_edge(f'FORK{center_fork}', c_node, DESCENDANT_FORK) 
                self.display_graph.add_edge(c_node, f'FORK{center_fork}', PARENT_FORK)    

            else:
                # insert node above child
                self.display_graph.add_node(*self.forkFactory(fork_counter, child_data.getPos(), (height+0.5)))
                self.display_graph.add_edge(f'FORK{fork_counter}', c_node, DESCENDANT_FORK) 
                self.display_graph.add_edge(c_node, f'FORK{fork_counter}', PARENT_FORK)
                sib_forks.add(f'FORK{fork_counter}')
                self.FORKS.add(f'FORK{fork_counter}')
                fork_counter += 1

        # connect all sibling forks to each other
        combos = set(combinations(sib_forks, 2))
        for pair in combos: # this is sexy
            self.display_graph.add_edge(pair[0], pair[1], SIBLING_FORK, True)



    def handlePartners(self, current_node, current_data, partners):
        # this node has 1+ partners but it does not have a null parent
        height = current_data.getHeight()
        pos = current_data.getPos()
        fork_counter = len(FORKS)
        # maybe find a way to not do this? like pass in relations
        children = [y for x, y, z in self.display_graph.edges(from_node=current_node) if z == r_flags.DESCENDANT] 

        # WARNING won't work for more than 1 partner currently
        for p_node in partners: 
            p_data = self.display_graph.node(p_node)

            # create new fork between partners
            root_fork_id = f'ROOT{len(ROOTS)}'
            root_fork = list(self.forkFactory(fork_counter, p_data.getPos(), height))
            root_fork[0] = root_fork_id
            root_fork[1].id = root_fork_id
            self.display_graph.add_node(root_fork[0], root_fork[1])
            self.display_graph.add_edge(root_fork_id, current_node, PARTNER_FORK, True)
            self.display_graph.add_edge(root_fork_id, p_node, PARTNER_FORK, True)
            self.ROOTS.add(root_fork_id)

            # WARNING definitely won't work for more than 1 partner as is
            if children: 
                self.handleChildren(root_fork[0], root_fork[1], children, self.display_graph)

                # add virtual link to lower node so the child(ren) is/are accessible
                self.display_graph.add_edge(current_node, f'FORK{fork_counter}', VIRTUAL)
                self.display_graph.add_edge(p_node, f'FORK{fork_counter}', VIRTUAL)


            if pos < p_data.getPos(): # moving to the right
                p_data.offsetPos(1)

            else:  # moving to the left
                p_data.offsetPos(-1)


    ''' Exceptions (null parents) 
    The first head is responsible for building the entire drop down
    Should only be called once per family at most
    Definitely can't handle more than 3 partners and even that is iffy
    '''
    def handleFirstChildren(self, current_node, current_data, relations):

        height = current_data.getHeight()
        pos = current_data.getPos()
        fork_counter = len(FORKS)
        partners = [x[0] for x in relations if x[1] == r_flags.PARTNER]

        # establish fork directly below current_node
        self.display_graph.add_node(*self.forkFactory(fork_counter, pos, (height+1)*(1/3)))
        self.display_graph.add_edge(current_node, f'FORK{fork_counter}', DESCENDANT_FORK)
        self.display_graph.add_edge(f'FORK{fork_counter}', current_node, PARENT_FORK)
        inline_drop = fork_counter
        self.FORKS.add(f'FORK{fork_counter}')
        fork_counter += 1

        # need to keep track of outer most lower nodes for virtual connection with descendants
        left_connect_fork, right_connect_fork = f'FORK{inline_drop}', f'FORK{inline_drop}'

        # WARNING: not confident this will work for multiple partners
        for p_node in partners:
            partner_data = self.display_graph.node(p_node)

            # insert node between partner and current node
            root_fork_id = f'ROOT{len(ROOTS)}'
            root_fork = list(self.forkFactory(fork_counter, partner_data.getPos(), height))
            root_fork[0] = root_fork_id
            root_fork[1].id = root_fork_id
            self.display_graph.add_node(root_fork[0], root_fork[1])
            self.display_graph.add_edge(root_fork_id, current_node, PARTNER_FORK, True)
            self.display_graph.add_edge(root_fork_id, p_node, PARTNER_FORK, True)
            self.ROOTS.add(root_fork_id)
            
            if pos < partner_data.getPos(): # moving to the right
                partner_data.offsetPos(1)
                right_connect_fork = f'FORK{fork_counter}'

            else:  # moving to the left
                partner_data.offsetPos(-1)
                left_connect_fork = f'FORK{fork_counter}'

            # add fork under this parent and connect to fork under current node
            self.display_graph.add_node(*self.forkFactory(fork_counter, partner_data.getPos(), (height+1)*(1/3)))
            self.display_graph.add_edge(p_node, f'FORK{fork_counter}', DESCENDANT_FORK) 
            self.display_graph.add_edge(f'FORK{fork_counter}', p_node, PARENT_FORK)
            self.display_graph.add_edge(f'FORK{fork_counter}', f'FORK{inline_drop}', PARTNER_FORK, True)
            self.FORKS.add(f'FORK{fork_counter}')
            fork_counter += 1

            # add lower fork between the nodes and connect lower nodes
            self.display_graph.add_node(*self.forkFactory(fork_counter, (abs(pos - partner_data.getPos()) // 2), (height+1)*(1/3)))
            self.display_graph.add_edge(f'FORK{inline_drop}', f'FORK{fork_counter}', PARTNER_FORK, True)
            self.display_graph.add_edge(f'FORK{fork_counter-1}', f'FORK{fork_counter}', PARTNER_FORK, True)
            self.display_graph.add_edge(f'FORK{fork_counter-1}', f'FORK{inline_drop}', PARTNER_FORK, True)
            self.FORKS.add(f'FORK{fork_counter}')
            fork_counter += 1
        
        
        # fork_counter-1 now represents the access point to the head of family's dropdown
        # add fork directly below fork_counter
        children = sorted([x[0] for x in relations if x[1] == r_flags.DESCENDANT], 
                                        key=lambda x:self.display_graph.node(x).getPos())
        access_fork_id = f'FORK{fork_counter-1}' 
        adjusted_height_data = dict(self.display_graph.node(access_fork_id))
        adjusted_height_data.setHeight(1/6) # account for handleChildren adding 1/2
        self.handleChildren(access_fork_id, adjusted_height_data, 
                                    children, self.display_graph)

        left_child, right_child = children[0], children[-1]

        left_desc_fork = next(y for x, y, z in self.display_graph.edges(from_node=left_child) if z == PARENT_FORK)
        right_desc_fork = next(y for x, y, z in self.display_graph.edges(from_node=right_child) if z == PARENT_FORK)

        self.display_graph.add_edge(left_desc_fork, left_connect_fork, VIRTUAL)
        self.display_graph.add_edge(right_desc_fork, right_connect_fork, VIRTUAL)

    # helper method to produce forks
    def forkFactory(self, _id, pos, height):
        fork_id = f'FORK{_id}'
        fork_data = qtc.QPointF()
        return(fork_id, invalidNode(fork_id, fork_data, pos, height))

    # Visualization adjustments (spacing)
    X_CONSTANT = 10
    Y_CONSTANT = 100
    SQUISH_SIBS = set()
    def layoutGraphics(self, target, visited):

        # don't adjust the anchors
        if target in TREE_ANCHORS:
            return

        data = self.display_graph.node(target)
        reference_x = 0
        new_fam = False
        sub_level_size = 1 # account for target node
        height = data.getHeight()
        relative_pos = data.getPos()
        neighbors = []
        weights = []

        [(neighbors.append(y), weights.append(z)) for x, y, z in self.display_graph.edges(from_node=target)]

        weight_counter = Counter(weights)

        # gather all neighbors that are on the same level
        level_neighbors = [x for x, y in zip(neighbors, weights) if y in 
                            [SIBLING_FORK, PARTNER_FORK, r_flags.SIBLING, r_flags.PARTNER]]
        sub_level_size += len(level_neighbors)
        
        # FIXME: this needs work (figure out spacing in even number of children)
        if not sub_level_size % 2 and relative_pos >= sub_level_size // 2 : # need to account for "empty" fork
            relative_pos -= 1
        
        
        # deal with roots
        if match := re.search(r"ROOT\d*", r"(?=(" + "|".join(neighbors) + "|" + target + r"))"):
            # first priority is determine reference from an anchor
            if match[0] in TREE_ANCHORS:
                reference_x = self.display_graph.node(match[0]).getData().x()

            # single exception? might be able to encoporate into another condition (the fork under non-anchor root)
            elif self.display_graph.edge(target, match[0]) == PARENT_FORK:
                reference_x = self.display_graph.node(match[0]).getData().x()

            # Detect that these nodes are partners connecting new families
            # that aren't anchors 
            else:
                if weight_counter[PARTNER_FORK] == 1:
                    if weight_counter[PARENT_FORK]:
                        reference_node = neighbors[weights.index(PARENT_FORK)]
                    elif weight_counter[NULL]:
                        reference_node = neighbors[weights.index(r_flags.PARTNER)]
                else:
                    mid_index = sub_level_size // 2 

                    # XXX: Not sure if these are necessary...
                    # if relative_pos == mid_index:
                    #     reference_pos = mid_index
                    # elif relative_pos < mid_index:
                    #     reference_pos = relative_pos + 1
                    # else:
                    #     reference_pos = relative_pos - 1
                    
                    reference_node = next((x for x in level_neighbors if self.display_graph.node(x).getPos() == mid_index), target)

                    if reference_node == target:
                        reference_node = visited[-1]

                reference_x = self.display_graph.node(reference_node).getData().x()
                new_fam = True
        
        # check if this node is a parent (or has a virtual link up to a head of family)
        elif set([PARENT_FORK, VIRTUAL]).intersection(set(weights)):
            node_index = weights.index(PARENT_FORK) if PARENT_FORK in weights else -1
            if node_index < 0:
                node_index = weights.index(VIRTUAL)
            reference_node = neighbors[node_index]
            reference_x = self.display_graph.node(reference_node).getData().x()
            if set([PARENT_FORK, r_flags.SIBLING]).issubset(set(weights)) and not set([DESCENDANT_FORK, PARTNER_FORK]).intersection(set(weights)): # center fork with no offspring
                SQUISH_SIBS.update([x for x, y in zip(neighbors, weights) if y == SIBLING_FORK])
                SQUISH_SIBS.add(target)

        # base case
        else:
            mid_index = sub_level_size // 2 # will be the one guarenteed to have been visited
            reference_node = next((x for x in level_neighbors if self.display_graph.node(x).getPos() == mid_index), target)

            if reference_node == target:
                for i, node in enumerate(level_neighbors):
                    current_x = self.display_graph.node(node).getData().x()
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
                reference_x = self.display_graph.node(reference_node).getData().x()
        
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

        # align parent fork with this node
        if PARENT_FORK in weights:
            parent_fork = self.display_graph.node(neighbors[weights.index(PARENT_FORK)])
            parent_fork['g_pos'][0] = x_coord


        data.getData().setPos(x_coord, height * Y_CONSTANT)
        drawable_connections = [x for x in self.display_graph.nodes(target) if x not in visited]
        target_point = data.getData().pos() if data.valid() else data.getData()
        for connector in drawable_connections:
            other_data = self.display_graph.node(connector)
            other_point = other_data.getData().pos() if other_data.valid() else other_data.getData()

            if connector not in LINES or target not in LINES:
                self._shape.moveTo(target_point)
                self._shape.lineTo(other_point)
                LINES.add(connector)
                LINES.add(target)


    def installFilters(self):
        ''' Simple function to add scene filters to the primary head of family
        enabling the tree to be moved by grabbing their graphics
        '''
        self._first_gen[0].installSceneEventFilter(self)
        self.setNameDisplay(self._name_display)
        

    def sceneEventFilter(self, source, event):
        ''' Creation of a sceneEventFilter to be installed to the head of
        family resulting in changing mouse images and moving the entire tree

        Args:
            source - the source of the captured event
            event - the specific event that was captured
        '''
        if event.type() == qtc.QEvent.GraphicsSceneHoverEnter:
            source.setCursor(qtc.Qt.OpenHandCursor)
            return False
        if event.type() == qtc.QEvent.GraphicsSceneMousePress:
            source.setCursor(qtc.Qt.ClosedHandCursor)
            return False
        if event.type() == qtc.QEvent.GraphicsSceneMouseMove:
            delta = event.pos() - event.lastPos()
            self.moveBy(delta.x(), delta.y())
            self.tree_moved.emit()
            return True
        if event.type() == qtc.QEvent.GraphicsSceneMouseRelease:
            source.setCursor(qtc.Qt.OpenHandCursor)
        return False
        

    ## Drawing mechanics

    def boundingRect(self):
        return self.childrenBoundingRect()
    
    def shape(self):
        return self._shape
    
    # FIXME: there's gotta be a better way to paint everything
    def paint(self, painter, option, widget):
        painter.setRenderHint(qtg.QPainter.Antialiasing)
        painter.setPen(self.linePen)
        for line in self.current_lines:
            painter.drawLine(line)
        for char_node in self.display_graph.nodes():
            self.display_graph(char_node).getData().paint(painter, option, widget)
        # if self._name_display and self._name:
        #     self.name_graphic.paint(painter, option, widget)
