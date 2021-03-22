''' 

Copyright (c) 2020 Peter C Gish

See the MIT License (MIT) for more information. You should have received a copy
of the MIT License along with this program. If not, see 
<https://www.mit.edu/~amini/LICENSE.md>.
'''
__author__ = "Peter C Gish"
__date__ = "3/15/21"
__maintainer__ = "Peter C Gish"
__version__ = "1.0.1"


# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

# Built-in Modules
import uuid
import numpy as np
from collections import deque 
from itertools import groupby
from collections import defaultdict
import logging
import heapq

# 3rd Party
from tinydb import where

# User-defined Modules
from .character import Character
from fantasycreator.Data.treeGraph import TreeGraph
from fantasycreator.Data.displayGraph import DisplayGraph
from fantasycreator.Data.hashList import HashList
from fantasycreator.Mechanics.flags import FAM_TYPE, REL_TREE_POS, RELATIONSHIP

class FamilyGraphics(Family, qtw.QGraphicsObject):

    def __init__(self, parent=None):
        super(FamilyGraphics, self).__init__(parent)

    ## ------------------- WORKHORSE, DRAWING FUNCTIONS ------------------- ##
    ## TODO: Aren't these set in preferences? Cause if so they should NOT be here
    FIXED_Y = 300 # mimic fixed/standardized character height?
    FIXED_X = 100 # mimic fixed image width
    DESC_DROPDOWN = 125
    PARTNER_SPACING = 200

    EXPAND_CONSTANT = 20 # used to stretch tree horizontally
    OFFSET_CONSTANT = 12 # used to streth each level based on number of sibs + height

    # Workhorse function to create graph struct from tree
    def setGrid(self):
        ''' Behemoth function to create a graph structure from the tree. Calculates
        positioning of each node as well as the lines used to connect the characters.

        TODO: Simplify simplify simplify
        '''
        self.graph.clear()
        q = [] 
        fork_counter = 0
        char_pos = 0    # counter to store traversal order: needed for save/open

        bottom_x_pos = 0     
        current_x = 0
        current_height = 0
        current_x_spacer = 0
        root_relationship_node = False
        offset_col = []

        root_node = self.tree.getRoot()
        root_char = root_node.getChar()
        root_char.setPos(self._tree_loc)
        root_char.addYOffset(self.DESC_DROPDOWN)
        root_id = root_char.getID()

        # root relationships with no parent family
        if self._display_root_partner and self._first_gen[1]: 
            
            num_partners = self.tree.getNumRelations(root_id, RELATIONSHIP.PARTNER)

            start_x = int(-(0.5 * (num_partners) * self.PARTNER_SPACING))
            midpoint = ((num_partners) * self.PARTNER_SPACING)/2
            
            # Add node to graph and queue
            root_char.addXOffset(start_x)
            self.graph.addNode(root_id, root_char)
            q.insert(0, root_node)

            # Create fork and add to graph
            current_fork = f'fork{fork_counter}'
            loc = qtc.QPointF()
            loc.setX(root_char.x())
            loc.setY(root_char.y() + self.DESC_DROPDOWN)
            forkNode = TreeGraph.Node.invalidNode(data=loc, position=current_height)
            self.graph.addNode(current_fork, loc, False)
            q.insert(0, forkNode)
            # print(f'Fork0 at {loc}')

            self.graph.add_edge(root_id, current_fork, self.DESC_DROPDOWN)
            char_pos += 1
            
            bottom_x_pos = root_char.x() + midpoint
            # Midpoint fork
            middle_fork = self._id
            loc = qtc.QPointF()
            loc.setX(bottom_x_pos)
            loc.setY(root_char.y() + self.DESC_DROPDOWN)
            forkNode = TreeGraph.Node.invalidNode(data=loc, position=current_height)
            self.graph.addNode(middle_fork, loc, False)
            q.insert(0, forkNode)
            # print(f'Midpoint at {loc}')

            self.graph.add_edge(middle_fork, f'fork{fork_counter}', self.FIXED_X)
            fork_counter += 1

            for index, char in enumerate(self.tree.getRelations(root_id, RELATIONSHIP.PARTNER)):
                offset = ((index + 1) * self.PARTNER_SPACING)

                # Add node to graph and queue
                char.setX(root_char.x() + offset)
                char.setY(root_char.y())
                self.graph.addNode(char.getID(), char)


                # Create fork and add to graph
                current_fork = f'fork{fork_counter}'
                loc = qtc.QPointF()
                loc.setX(char.x())
                loc.setY(char.y() + self.DESC_DROPDOWN)
                forkNode = TreeGraph.Node.invalidNode(id=None, char=loc, pos=current_height, valid=False)
                self.graph.addNode(current_fork, loc, False)
                q.insert(0, forkNode)
                # print(f'Fork1 at {loc}')
                self.graph.addEdge(char.getID(), current_fork, self.DESC_DROPDOWN)
                self.graph.addEdge(middle_fork, current_fork, self.FIXED_X)
                fork_counter += 1
                root_relationship_node = True

        elif self._explode and self._first_gen[1]:
            self.graph.addNode(self._id, root_char)
            q.insert(0, self.tree.getRoot())
            root_relationship_node = True

        else:
            self.graph.addNode(root_id, root_char)
            q.insert(0, self.tree.getRoot())


        char_pos += 1 
        # current_height += 1

        while q != []: 
            count = len(q) 
            while count != 0: 
                count -= 1
                temp_node = q[-1] 

                q.pop()

                if isinstance(temp_node.getData(), Character):
                    offset_col.append(temp_node)
                
                if num_children := self.tree.getNumRelations(temp_node.getID(), RELATIONSHIP.DESCENDANT):
                    parent_char = temp_node.getData()
                    
                    if temp_node is root_node and root_relationship_node:
                        parent_id = self._id
                        parent_x = self.graph.getNodeData(parent_id).x()

                    
                    # elif self._explode and temp_node.mates:
                    #     # TODO: Only processes first partnership
                    #     parent_id = temp_node.getPartnerships()[0][1]
                    #     parent_x = self.graph.get_vertex(parent_id).get_data().x()
                    #     # print(f'Parent: {parent_id} @ {parent_x}')
                                    
                    else:
                        parent_id = parent_char.getID()
                        parent_x = parent_char.x()
    
                    current_height = temp_node.getHeight() + 1
                    
                    ratio_mult = - ((0.5) * (num_children - 1))

                    # Create fork for current descendants
                    current_fork = f'fork{fork_counter}'
                    loc = qtc.QPointF()
                    loc.setY(current_height * self.FIXED_Y + self._tree_loc.y())

                    forkNode = TreeGraph.Node.invalidNode(data=loc, position=current_height)
                    self.graph.addNode(current_fork, loc, False)

                    self.graph.addEdge(parent_id, current_fork, self.FIXED_Y)
                    loc.setX(parent_x)
                    q.insert(0, forkNode)
                    fork_counter += 1

                    current_x_spacer = self.calcXSpacer(current_height, num_children)

                    for index, child_node in enumerate(self.tree.getRelationNodes(temp_node, RELATIONSHIP.DESCENDANT)):
                        newFork = f'fork{fork_counter}'
                        loc = qtc.QPointF()
                        
                        current_x = (ratio_mult * current_x_spacer) + parent_x

                        loc.setY(current_height * self.FIXED_Y + self._tree_loc.y())
                        loc.setX(current_x)
                    
                        # Create Fork node and add to grid
                        forkNode = TreeGraph.Node.invalidNode(data=loc, position=current_height)
                        self.graph.addNode(newFork, loc, False)
                        q.insert(0, forkNode)
                        previous_fork = f'fork{fork_counter-1}'
                        fork_counter += 1

                        # Set child and add to grid
                        child_char = child_node.getData()
                        child_id = child_char.getID()
                        self.graph.addNode(child_id, child_char)
                        child_char.setX(current_x)
                        child_char.setY((current_height * self.FIXED_Y) + self._tree_loc.y())
                        child_char.addYOffset(self.DESC_DROPDOWN)
                        q.insert(0, child_node)

                        # Connect child to fork
                        self.graph.addEdge(newFork, child_id, self.DESC_DROPDOWN)
                        child_char.setParentID(parent_id)

                        if num_children % 2 != 0 and index == num_children // 2:
                            self.graph.addEdge(current_fork, newFork, self.FIXED_Y)
                            
                        else:
                            if index == num_children / 2 - 1:
                                # ratio_mult += 1  # "skipping" 0 
                                self.graph.addEdge(newFork, current_fork, self.DESC_DROPDOWN)
                            
                            elif index == num_children / 2:
                                self.graph.addEdge(newFork, current_fork, self.DESC_DROPDOWN)

                        if index != 0:
                            self.graph.addEdge(newFork, previous_fork, self.DESC_DROPDOWN)
                        
                        ratio_mult += 1
                        char_pos += 1
                        
                        logging.warning('This needs to be redone. Must figure out how to handle partners')
                        num_partners = self.tree.getNumRelations(child_id, RELATIONSHIP.PARTNER)
                        if self._explode and num_partners:
                            start_x = 0
                            midpoint = ((num_partners) * self.PARTNER_SPACING)/2
                            bottom_x_pos = child_char.x() + midpoint

                            # Midpoint fork
                            # TODO: Only processes first partnership
                            middle_fork = self.tree.getRelations(child_node, RELATIONSHIP.PARTNER)[0][1]
                            loc = qtc.QPointF()
                            loc.setX(bottom_x_pos)
                            loc.setY(child_char.y())
                            # print(f'Middle Fork: {middle_fork} @ {loc}')
                            forkNode = TreeGraph.Node.invalidNode(data=loc, position=current_height)
                            self.graph.addNode(middle_fork, loc, False)

                            q.insert(0, forkNode)
                            self.graph.addEdge(middle_fork, child_id, self.PARTNER_SPACING)

                            for index, char in enumerate(self.tree.getRelations(child_id, RELATIONSHIP.PARTNER)):
                                offset = start_x + ((index + 1) * self.PARTNER_SPACING)

                                 # Add node to graph and queue
                                char.setX(current_x)
                                char.setY(child_char.y())
                                char.addXOffset(offset)
                                self.graph.addNode(char.getID(), char)
                                # q.insert(0, char)
                                # char_pos += 1
                        #         self.graph.add_edge(char.getData().getID(), middle_fork, self.PARTNER_SPACING)


        # Only need to offset if large enough fam
        if self._size > 2:
            # Preprocess post-order list generated from above
            offset_col = list(reversed(sorted(offset_col, key=lambda x: x.position, reverse=True)))

            pivots = [i for i in range(1, len(offset_col)) if offset_col[i].height!=offset_col[i-1].height]
            pivots.insert(0, 0)

            offset_col = [list(reversed(offset_col[pivots[i-1]:pivots[i]])) 
                                if offset_col[pivots[i]].position==REL_TREE_POS.RIGHT 
                                else offset_col[pivots[i-1]:pivots[i]] for i in range(1, len(pivots))]
            offset_col = [item for sublist in offset_col for item in sublist]

            # Second walk to calculate offsets
            offset_dict = defaultdict(lambda: 0)
            current_orientation = -1 # -1 denotes left side of tree, 1 represents right
            parent_offset = 0
            current_height = 0
            level_offset = 0
            for parent, sibs_iter in groupby(offset_col, key=lambda x: x.parents[0]):
                sibs = list(sibs_iter)

                num_sibs = len(sibs)
                if num_sibs == 1 and sibs[0] == root_node:
                    continue
                if parent == root_node:
                    continue

                calc_offset = (self.calcXOffset(parent.getHeight()+1, num_sibs))

                if current_height != sibs[0].getHeight():
                    current_height = sibs[0].getHeight()
                    level_offset = 0

                if sibs[0].position == REL_TREE_POS.LEFT:
                    if current_orientation > 0:
                        current_orientation = -1
                        level_offset = 0
                    calc_offset *= -1
                
                else:
                    if current_orientation < 0:
                        current_orientation = 1
                        level_offset = 0

                new_fam = True
                middle_child = np.ceil(num_sibs / 2) - 1
                for index, node in enumerate(sibs):

                    if new_fam:
                        current_offset = level_offset + calc_offset
                        new_fam = False

                    children_offset = offset_dict[node]
                    offset_dict[node] += current_offset
                    
                    subtree = []
                    self.tree.getSubTree(node, subtree)
                    for child in subtree:
                        offset_dict[child] += current_offset

                    current_offset += children_offset

                    if index == middle_child:
                        parent_offset += offset_dict[node]

                if parent and parent != root_node:
                    offset_dict[parent] = parent_offset
                parent_offset = 0
                level_offset = (current_offset - level_offset)

                
            # Final walk to apply offsets
            for node, offset in reversed(offset_dict.items()):
                # print(f'Giving {node} an offset of {offset}')
                node.getData().addXOffset(offset)
                for mate in node.getMates():
                    mate.getData().addXOffset(offset)

            self.offset_grid()


    def calcXSpacer(self, height, num_kids): 
        ''' Helper method to calculate the horizontal distance between nodes
        based on the current height of the tree and the number of kids under that node.

        Args: 
            height - level in the tree
            num_kids - the number of characters for a given node
        '''
        return int((self.FIXED_X) / (height * num_kids) * self.EXPAND_CONSTANT)

    def calcXOffset(self, height, num_sibs):
        ''' Helper method to calculate the horizontal offset for each node to 
        account for less room further down the tree.

        Args: 
            height - level in the tree
            num_sibs - the number of siblings a given node has
        '''
        return int(((num_sibs)) * self.OFFSET_CONSTANT) + (self.FIXED_X / height * (num_sibs))

    
    def offsetGrid(self):
        ''' Corrects the graph so that everything is square and spacing
        looks astetically pleasing
        '''
        mid_points = set()
        root_node = self.tree.getRoot()
        if root_node.getPartnerships():
            mid_points.add(self._id)
        for v in self.graph:
            if v.valid(): # Character
                for w in self.graph.getConnections(v):
                    if not w.valid() and w.getID() not in mid_points: # Line
                        if (self.graph.getWeight(v, w) == self.PARTNER_SPACING):
                            mid = self.calcPartnerMidpoint(w)
                            w.getData().setX(mid)
                            mid_points.add(w.getID())
                        else:
                            w.getData().setX(v.getData().x())
            else: # Line
                for w in self.graph.getConnections(v):
                    if not w.valid(): # Line
                        if isinstance(w.getID(), uuid.UUID) and w.getID() not in mid_points:
                            v.getData().setX(w.getData().x())
                        elif w.getData().y() != v.getData().y():
                            w.getData().setX(v.getData().x())
                        


    # WARNING: ONLY CALCS FIRST PARTNERSHIP
    def calcPartnerMidpoint(self, vertex):
        ''' Calculates the graphical mid point between a provided vertex

        Args:
            vertex - the character with a partner
        '''
        chars = [x for x in self.graph.getConnections(vertex) if x.valid()]
        char1 = chars[0].getData()
        char2 = chars[1].getData()

        min_x = min(char1.x(), char2.x())
        del_x = abs(char1.x() - char2.x())
        return min_x + (del_x / 2)


    def buildTree(self):
        ''' Using the current graph of this tree, graphically build the structure.
        Draws the custom shape of this tree using the character's bounding
        boxes and adds the connecting lines.
        '''
        self.prepareGeometryChange()

        # NOTE: Only place where pos is used to retrieve Vertex
        if not self._display_root_partner and self._explode and self._first_gen[1]: 
            root_vertex = self.graph.getNode(self._id) # represents the root node

        else:
            root_vertex = self.graph.getNode(self._first_gen[0].getID()) # represents the root node

        visited = set()
        paths = set(frozenset())
        q = []
        q.append(root_vertex)
        visited.add(root_vertex)
        self._shape = qtg.QPainterPath()

        for char in self.members:
            if char not in self.filtered:
                self._shape.addRect(char.sceneBoundingRect())
        if self._display_root_partner and self._first_gen[1]:
            if self._first_gen not in self.filtered:
                self._shape.addRect(self._first_gen[1].sceneBoundingRect())
        # if self._explode:
        #     for char in self.partners:
        #         if char not in self.filtered:
        #             self._shape.addRect(char.sceneBoundingRect())

        while q != []:
            s = q.pop(0)
            for i in self.tree.getConnections(s):
                if i not in visited:
                    q.append(i)
                    visited.add(i)
                 # draw lines
                if {i, s} not in paths:
                    if s.valid():
                        if i.valid(): # Character -> Character
                            line = qtc.QLineF(s.getData().pos(), i.getData().pos())
                        else:   # Character -> Fork
                            line = qtc.QLineF(s.getData().pos(), i.getData())
                    else: 
                        if i.is_valid(): # Fork -> Character
                            line = qtc.QLineF(s.getData(), i.getData().pos())
                        else: # # Fork -> Fork
                            line = qtc.QLineF(s.getData(), i.getData())

                    self._shape.moveTo(line.p1())
                    self._shape.lineTo(line.p2())
                    self.current_lines.append(line)
                    paths.add(frozenset([i, s]))

        if self._name:
            self.name_graphic.setPlainText(self._name)
            size = qtc.QRectF(self.font_metric.boundingRect(self._name))
            root = root_vertex.get_data()
            self.name_graphic.setPos(root.x() - size.width() - root.getWidth(), 
                                            root.y() - size.height())
            self._shape.addRect(self.name_graphic.sceneBoundingRect())
            

    def resetFamily(self):
        ''' Clears all connecting lines.
        '''
        self.current_lines[:] = []
    
    def boundingRect(self):
        ''' Build a custom bounding rect based on this tree's children.
        '''
        rect = self.childrenBoundingRect()
        if self._size == 1:
            rect = rect.adjusted(0, 0, 0, 20)
        return rect
    
    def paint(self, painter, option, widget):
        ''' Custom paint method to draw all currently visible characters and 
        their connecting lines. Also draws the family name if the flag is set.

        Args:
            painter - system's painter object
            option - any options that apply to the painter
            widget - the widget to be painted
        '''
        painter.setRenderHint(qtg.QPainter.Antialiasing)
        painter.setPen(self.linePen)
        for line in self.current_lines:
            painter.drawLine(line)
        for char in self.members:
            if char not in self.filtered:
                char.paint(painter, option, widget)
        if self._display_root_partner and self._first_gen[1]:
            if self._first_gen[1] not in self.filtered:
                self._first_gen[1].paint(painter, option, widget)
        if self._explode:
            for char in self.partners.arr:
                if char not in self.filtered:
                    char.paint(painter, option, widget)
        if self._name_display and self._name:
            self.name_graphic.paint(painter, option, widget)

    def shape(self):
        return self._shape


class PriorityQ(object):
        def __init__(self, initial=None, key=lambda x:x):
            self.key = key
            self.index = 0
            if initial:
                self._data = [(key(item), i, item) for i, item in enumerate(initial)]
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

def traverseGraph(graph, start):
    """
    Args:
        start - start node
    return: generator for walk
    """
    TRAVERSE_ORDER = {RELATIONSHIP.SIBLING: 1, 
                        RELATIONSHIP.PARTNER: 0, 
                        RELATIONSHIP.DESCENDANT: 3, 
                        RELATIONSHIP.PARENT: 2}
    visited = set([start])
    q = PriorityQ([(0, start)], key=lambda x: x[0])
    while q:
        
        node = q.pop()[1]
        yield node

        L = graph.nodes(from_node=node)

        for next_node in L:
            if next_node not in visited:
                visited.add(next_node)
                q.push((TRAVERSE_ORDER[graph.edge(node, next_node)], next_node))