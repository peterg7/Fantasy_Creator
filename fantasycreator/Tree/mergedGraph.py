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
from itertools import chain
from collections import defaultdict
import logging
import heapq

# 3rd Party
from tinydb import where

# User-defined Modules
from fantasycreator.Tree.family import Family
from fantasycreator.Data.treeGraph import TreeGraph
from fantasycreator.Data.hashList import HashList
from fantasycreator.Mechanics.flags import FAM_TYPE, REL_TREE_POS, RELATIONSHIP


class MergedFamily(qtw.QGraphicsObject):


    def __init__(self, families, start_node, parent=None):
        # TODO: this isn't very elegant
        super(MergedFamily, self).__init__(parent)
        self.families = families
        self.graph = TreeGraph()
        self.start = start_node
        
    
    def build(self):
        total_nodes = list(chain.from_iterable([fam.getFamilyNodes() for fam in families]))
        total_connections = list(chain.from_iterable([fam.getFamilyConnections() for fam in families]))

        for node in total_nodes:
            self.graph.add_node(node[0], node[1])
        
        for node1, node2, weight in total_connections:
            self.graph.add_edge
        

    
    def split(self):
        return self.families

    def getStart(self):
        return self.start
    