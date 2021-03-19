
# 3rd party Modules
from graph import Graph

# Built-in Modules
import numpy as np
import uuid
import logging

# User-defined Modules
from fantasycreator.Mechanics.flags import RELATIONSHIP

class DisplayGraph:

    class Node:

        def __init__(self, _id, data=None, valid=False):
            self._id = _id
            self.data = data
            self.valid = valid  # doesn't necessarily mean empty 

        def valid(self):
            return self.valid

        def getID(self):
            return self._id
        
        def getData(self):
            return self.data
        
        def __str__(self):
            return (str(self._id))
        
        def __eq__(self, value):
            if isinstance(value, Node):
                return self._id == value._id
            if isinstance(value, uuid.UUID):
                return self._id == value
            return self is value

##------------------- Graph Defs -------------------------##

    def __init__(self):
        self.graph = Graph()

    def __iter__(self):
        logging.critical("Not sure why I need this but this will let me know")

    def addNode(self, _id, data=None, valid=True):
        new_node = self.Node(_id, data, valid)
        self.graph.add_node(_id, new_node)
    
    def addEdge(self, node1, node2, cost = 0):
        if not isinstance(node1, uuid.UUID):
            node1 = node1.getID()

        if not isinstance(node2, uuid.UUID):
            node2 = node2.getID()

        if not node1 or not node2:
            return False
        
        self.graph.add_edge(node1, node2, cost, True)

    def getNode(self, _id):
        return self.graph.node(_id)
    
    def getNodeData(self, _id):
        return self.graph.node(_id).getData()
    
    def getConnections(self, _id):
        return self.graph.nodes(from_node=_id)
    
    def getWeight(self, _id1, _id2):
        return self.graph.edge(_id1, _id2)

    def clear(self):
        del self.graph
        self.graph = Graph()
