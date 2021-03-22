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


class TestGraphics(qtw.QGraphicsObject):

    FORK_PRIORITY = 0
    TRAVERSE_ORDER = {RELATIONSHIP.SIBLING: 1, 
                        RELATIONSHIP.PARTNER: 0,
                        FORK_PRIORITY: 0, 
                        RELATIONSHIP.DESCENDANT: 3, 
                        RELATIONSHIP.PARENT: 2}
    
    ## TODO: Aren't these set in preferences? Cause if so they should NOT be here
    FIXED_Y = 300 # mimic fixed/standardized character height?
    FIXED_X = 100 # mimic fixed image width
    DESC_DROPDOWN = 125
    PARTNER_SPACING = 200

    EXPAND_CONSTANT = 20 # used to stretch tree horizontally
    OFFSET_CONSTANT = 12 # used to streth each level based on number of sibs + height

    def __init__(self, parent=None):
        super(TestGraphics, self).__init__(parent)
        self.display_graph = DisplayGraph()
        self.showing_merged = True

    def setShowingMerged(self, control):
        self.showing_merged = control


    def setGrid(self, family_tree, root_pt):
        ''' Behemoth function to create a graph structure from the tree. Calculates
        positioning of each node as well as the lines used to connect the characters.
        '''
        
        self.display_graph.clear()
        fork_counter = 0
        current_midpoint = 0
        current_x = 0
        current_height = 0
        current_x_spacer = 0
        traverse_path = []
        visited = set()
        # set up a priority queue that stores the characters with their priority
        # being determined by their relationships
        q = PriorityQ(key=lambda x: x[0])
        tree_pos_y = family_tree.getTreePos().y()

        root_node = family_tree.tree.getRoot() # NOTE: must access underlying TreeGraph
        root_char = root_node.getChar()
        root_partners = family_tree.tree.getRelationNodes(root_node.getID(), RELATIONSHIP.PARTNER)
        root_char.setPos(root_pt)
        root_char.addYOffset(TestGraphics.DESC_DROPDOWN)

        # if root has a partner, assume it is merged 
        # Treat root + partner as special case because of drawing them "above" the tree
        if self.showing_merged and root_partners:
            num_partners = len(root_partners)
            start_x = int(-(0.5 * (num_partners) * self.PARTNER_SPACING))
            
            # Add root character to graph and priority queue
            root_char.addXOffset(start_x)
            self.display_graph.addNode(root_node.getID(), root_char)
            q.push([0, root_char]) # NOTE: allow root node to have a magic priority of 0

            # Create fork node and add it to the graph/queue
            current_fork_id = f'fork{fork_counter}'
            fork_pt = qtc.QPointF(root_char.x(), root_char.y() + TestGraphics.DESC_DROPDOWN)
            fork_node = TreeGraph.invalidNode(data=fork_pt, pos=current_height)
            self.display_graph.addNode(_id=current_fork_id, data=fork_pt, valid=False)
            self.display_graph.addEdge(node1=root_node.getID(), node2=current_fork_id, wt=TestGraphics.DESC_DROPDOWN)
            q.push((TestGraphics.FORK_PRIORITY, fork_node))

            # Create the midpoint fork
            middle_fork_id = f'midpoint{current_midpoint}'
            midpoint = ((num_partners) * self.PARTNER_SPACING)/2
            fork_pt = qtc.QPointF(root_char.x() + midpoint, root_char.y() + TestGraphics.DESC_DROPDOWN)
            fork_node = TreeGraph.invalidNode(data=fork_pt, pos=current_height)
            self.display_graph.addNode(_id=middle_fork_id, data=fork_pt, valid=False)
            self.display_graph.addEdge(node1=middle_fork_id, node2=current_fork_id, wt=TestGraphics.FIXED_X)
            q.push((TestGraphics.FORK_PRIORITY, fork_node))
            
            fork_counter += 1

            for index, char in enumerate(family_tree.getPartners()):
                offset = ((index + 1) * TestGraphics.PARTNER_SPACING)

                # Add partner node to graph
                char.setX(root_char.x() + offset)
                char.setY(root_char.y())
                self.display_graph.addNode(char.getID(), char)
                logging.debug('Do i need this?')
                # q.push((TestGraphics.TRAVERSE_ORDER[family_tree.getRelationship(root_char, char)], char))

                # Create fork node and add it to the graph/queue
                current_fork_id = f'fork{fork_counter}'
                fork_pt = qtc.QPointF(char.x(), char.y() + TestGraphics.DESC_DROPDOWN)
                fork_node = TreeGraph.invalidNode(data=fork_pt, pos=current_height)
                self.display_graph.addNode(_id=current_fork_id, data=fork_pt, valid=False)
                self.display_graph.addEdge(node1=char.getID(), node2=current_fork_id, wt=TestGraphics.DESC_DROPDOWN)
                self.display_graph.addEdge(node1=middle_fork_id, node2=current_fork_id, wt=TestGraphics.FIXED_X)
                q.push((TestGraphics.FORK_PRIORITY, fork_node))

                fork_counter += 1
        
        else:
            self.display_graph.addNode(_id=root_node.getID(), data=root_char)
            q.push([0, root_char]) # NOTE: allow root node to have a magic priority of 0
        
        # Enter loop to traverse through all characters in family_tree
        while q:
            current_node = q.pop()[1] # need to access the data, not priority level
            current_id = current_node.getID()
            if isinstance(current_node.getData(), Character):
                traverse_path.append(current_node)
            
            # Check if this node has children
            if num_children := len(family_tree.getChildren(current_id)):
                parent_char = current_node.getData()

                # Determine what the parent id needs to be for the children to connect to
                if current_node is root_node and current_midpoint:
                    parent_id = f'midpoint{current_midpoint}'
                    parent_x = self.display_graph.getNodeData(parent_id).x()
                    current_midpoint += 1

                # TODO: Is this necessary?
                # elif not self.showing_merged and family_tree.getPartners(current_id):
                #     parent_id = family_tree.getPartners(current_id)[0].getID() # WARNING: only processes first partner
                #     parent_x = self.display_graph.getNodeData(parent_id).x()

                else:
                    parent_id = parent_char.getID()
                    parent_x = parent_char.x()
            
                current_height = current_node.getHeight()
                # Needed for spreading siblings from eachother
                spread_multiplier = - ((0.5) * (num_children - 1))
                

                # Create a fork for current children
                current_fork_id = f'fork{fork_counter}'
                fork_pt = qtc.QPointF(0, current_height * TestGraphics.FIXED_Y + tree_pos_y)
                fork_node = TreeGraph.invalidNode(data=fork_pt, pos=current_height)
                self.display_graph.addNode(_id=current_fork_id, data=fork_pt, valid=False)
                self.display_graph.addEdge(node1=parent_id, node2=current_fork_id, wt=TestGraphics.FIXED_Y)

                logging.debug('Why do I set the x value here?')
                fork_pt.setX(parent_x)
                q.push((TestGraphics.FORK_PRIORITY, fork_node))

                fork_counter += 1  
                current_x_spacer = TestGraphics.calcXSpacer(current_height, num_children)

                # Loop through all of the children of the current node
                # NOTE: must access underlying TreeGraph
                for index, child_node in enumerate(family_tree.tree.getRelationNodes(current_id, RELATIONSHIP.DESCENDANT)):
                    current_x = spread_multiplier * current_x_spacer + parent_x
                    # Create a new fork for this child_node
                    child_fork_id = f'fork{fork_counter}'
                    fork_pt = qtc.QPointF(current_x, current_height * TestGraphics.FIXED_Y + tree_pos_y)
                    fork_node = TestGraphics.invalidNode(data=fork_pt, pos=current_height)
                    self.display_graph.addNode(_id=child_fork_id, data=fork_pt, valid=False)
                    q.push((TestGraphics.FORK_PRIORITY, fork_node))

                    previous_fork_id = f'fork{fork_counter-1}'
                    fork_counter += 1

                    # Position the child and add to display_graph
                    child_char = child_node.getData()
                    child_id = child_char.getID()
                    child_char.setX(current_x)
                    child_char.setY(current_height * TestGraphics.FIXED_Y + tree_pos_y + TestGraphics.DESC_DROPDOWN)
                    # TODO: This is sketch setting the parent id like this
                    # child_char.setParentID(parent_id)
                    self.display_graph.addNode(_id=child_id, data=child_char)
                    self.display_graph.addEdge(node1=child_fork_id, node2=child_id, wt=TestGraphics.DESC_DROPDOWN)
                    q.push(TestGraphics.TRAVERSE_ORDER[family_tree.getRelationship(current_id, child_id), child_node])

                    # Connect the created fork
                    if num_children % 2 and index == num_children // 2:
                        self.display_graph.addEdge(current_fork_id, child_fork_id, TestGraphics.FIXED_Y)
                    elif index in [num_children / 2 - 1, index == num_children / 2]:
                        self.display_graph.addEdge(child_fork_id, current_fork_id, TestGraphics.DESC_DROPDOWN)
                    
                    if index != 0:
                        self.graph.addEdge(child_fork_id, previous_fork_id, TestGraphics.DESC_DROPDOWN)
                    
                    spread_multiplier += 1

                    ## TODO: This needs SERIOUS attention
                    # Inspect this child's partners (if any)
                    num_partners = len(family_tree.tree.getRelationNodes(child_id, RELATIONSHIP.PARTNER))
                    if self.showing_merged and num_partners:
                        start_x = 0
                        midpoint = ((num_partners) * self.PARTNER_SPACING)/2
                        bottom_x_pos = child_char.x() + midpoint

                        # Create midpoint fork
                        middle_fork_id = f'midpoint{current_midpoint}'
                        fork_pt = qtc.QPointF(child_char.x() + midpoint, child_char.y())
                        fork_node = TreeGraph.invalidNode(data=fork_pt, pos=current_height)
                        self.display_graph.addNode(middle_fork_id, fork_pt, False)
                        self.display_graph.addEdge(middle_fork_id, child_id, TestGraphics.PARTNER_SPACING)
                        q.push(TestGraphics.FORK_PRIORITY, fork_node)

                        for index, partner in enumerate(family_tree.getPartners):
                            offset = start_x + ((index + 1) * TestGraphics.PARTNER_SPACING)

                            # Add partner to graph/queue
                            partner.setX(current_x + offset)
                            partner.setY(child_char.y())
                            self.display_graph.addNode(_id=partner.getID(), data=partner)
                            self.display_graph.addEdge(partner.getID(), middle_fork_id, TestGraphics.PARTNER_SPACING)
                            q.push((TestGraphics.TRAVERSE_ORDER[family_tree.getRelationship(child_char, partner)], partner))


        # Only apply offsets if tree is large enough
        ## TODO: This has some aspects of brilliance but it's WACK
        if len(family_tree.getSize()) > 2:
            # Preprocess post-order traversal
            traverse_path = list(reversed(sorted(traverse_path, key=lambda x: x.position, reverse=True)))

            pivots = [i for i in range(1, len(traverse_path)) if traverse_path[i].getHeight() != traverse_path[i-1].getHeight()]
            pivots.insert(0, 0)

            traverse_path = [list(reversed(traverse_path[pivots[i-1]:pivots[i]])) 
                                    if traverse_path[pivots[i]].position == REL_TREE_POS.RIGHT
                                    else traverse_path[pivots[i-1]:pivots[i]] for i in range(1, len(pivots))]
            traverse_path = [item for sublist in traverse_path for item in sublist]

            # Second walk to calculate offsets
            offset_dict = defaultdict(lambda: 0)
            current_orientation = -1 # denotes left side of tree, 1 represents right
            parent_offset = 0
            current_height = 0
            level_offset = 0
            for parent, sibs_iter in groupby(traverse_path, key=lambda x: family_tree.getParents()[0]):
                sibs = list(sibs_iter)
                num_sibs = len(sibs)

                if (num_sibs == 1 and sibs[0] == root_node) or parent == root_node:
                    continue
                
                x_offset = TestGraphics.calcXOffset(parent.getHeight() + 1, num_sibs)

                if current_height != sibs[0].getHeight():
                    current_height = sibs[0].getHeight()
                    level_offset = 0
                

                if sibs[0].position == REL_TREE_POS.LEFT:
                    if current_orientation != REL_TREE_POS.LEFT:
                        current_orientation = REL_TREE_POS.LEFT
                        level_offset = 0
                    x_offset *= -1
                elif current_orientation == REL_TREE_POS.LEFT:
                    current_orientation = REL_TREE_POS.RIGHT
                    level_offset = 0
                
                middle_child = np.ceil(num_sibs / 2.0) - 1
                for index, node in enumerate(sibs):
                    if not index:
                        current_offset = level_offset + x_offset
                    
                    children_offset = offset_dict[node]
                    offset_dict[node] += current_offset

                    subtree = []
                    family_tree.tree.getSubTree(node, subtree)
                    for child in subtree:
                        offset_dict[child] += current_offset
                    
                    current_offset += children_offset
                    if index == middle_child:
                        parent_offset += offset_dict[node]
                
                if parent and parent != root_node:
                    offset_dict[parent] = parent_offset
                parent_offset = 0
                level_offset = (current_offset - level_offset)
            
            for node, offset in reversed(offset_dict.items()):
                node.getData().addXOffset(offset)
                for mate in family_tree.getPartners(node):
                    mate.addXOffset(offset)
            
            self.offset_grid()
        
        
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


    
def calcXSpacer(height, num_kids): 
    ''' Helper method to calculate the horizontal distance between nodes
    based on the current height of the tree and the number of kids under that node.

    Args: 
        height - level in the tree
        num_kids - the number of characters for a given node
    '''
    return int((TestGraphics.FIXED_X) / (height * num_kids) * TestGraphics.EXPAND_CONSTANT)

def calcXOffset(height, num_sibs):
    ''' Helper method to calculate the horizontal offset for each node to 
    account for less room further down the tree.

    Args: 
        height - level in the tree
        num_sibs - the number of siblings a given node has
    '''
    return int(((num_sibs)) * TestGraphics.OFFSET_CONSTANT) + (TestGraphics.FIXED_X / height * (num_sibs))


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
