
# 3rd party Modules
from graph import Graph

# Built-in Modules
import numpy as np
import uuid
import logging

# User-defined Modules
from fantasycreator.Mechanics.flags import RELATIONSHIP, REL_TREE_POS

class TreeGraph:

    class Node:
        ''' Node class for the graph-tree. Holds characters and associated
        information.
        '''

        def __init__(self, _id, data, pos=0, rel_pos=REL_TREE_POS.MIDDLE, ht = 0, valid=True):
            ''' Constructor

            Args:
                _id - the id of the stored character
                char - the data this node stores (a character)
                pos - the tree position of this node using the TreePos enum
                rel_pos - the relative position to the root (a REL_TREE_POS flag)
                ht - the height of this node
            '''
            self.id = _id
            self.data = data
            self.position = pos
            self.relative_pos = rel_pos
            self.height = ht
            self.valid = valid
            if valid and not _id:
                logging.error('This is soooooo dangerous')
        
        def build(self, pos, rel_pos, ht):
            self.position = pos
            self.relative_pos = rel_pos
            self.height = ht
        
        def setPos(self, pos):
            ''' Setter method for this node's relative position to its siblings. 
            Checks for validity and returns a boolean indicating if the passed 
            in value was accepted.

            Args:
                pos - the new position 
            '''
            if pos < 0:
                return False
            self.position = pos
            return True
        
        def offsetPos(self, offset):
            ''' Setter method to offset the position by adding `offset` to the
            existing value for position.

            Args:
                offset - the amount to offset position by adding it to the current
                            value.
            '''
            self.position += offset

        def setRelativePos(self, rel_pos):
            ''' Setter method for the relative position of this node to the
            tree's root. Checks for validity and returns a boolean indicating
            failure/success.

            Args: 
                rel_pos - the new relative position value (of type REL_TREE_POS)
            '''
            if REL_TREE_POS.exists(rel_pos):
                self.relative_pos = rel_pos
                return True
            return False


        def setHeight(self, ht):
            ''' Setter method for this node's "height". Checks for validity and
            returns a boolean value indicating if the argument was accepted.

            Args:
                ht - the new height value
            '''
            if ht < 0:
                return False
            self.height = ht
            return True

        def offsetHeight(self, offset):
            ''' Setter method to offset the existing value for the height of this
            node by adding the argument to it.

            Args:
                offset - the amount to offset height by adding it to the current
                            value.
            '''
            self.height += offset
        
        def getID(self):
            return self.id

        def getPos(self):
            ''' Getter method for this node's position
            '''
            return self.position
        
        def getRelativePos(self):
            ''' Getter method for this node's relative position to the root
            '''
            return self.relative_pos

        def getHeight(self):
            ''' Getter method for this node's height
            '''
            return self.height

        def getData(self):
            ''' Getter method for the character stored in this node
            '''
            return self.data
        
        def valid(self):
            return self.valid
        
        def __eq__(self, other):
            if isinstance(other, Node):
                return self.id == other.id
            if isinstance(other, uuid.UUID):
                return self.id == other
            return self is other
        
        def __str__(self):
            if self.data.__str__:
                return (f'NODE: {self.data.__str__()}')
            else:
                return self
        
        @staticmethod
        def invalidNode(data, position):
            node = Node(_id=None, data=data, pos=position, valid=False)
            return node
    

    def __init__(self, root=None):
        self.graph = Graph()
        if root:
            self.root = self.Node(root.getID(), root, 0, REL_TREE_POS.MIDDLE)
            self.graph.add_node(root.getID(), self.root)

    def addNode(self, char, target=None, relation=RELATIONSHIP.PARENT):
        if not target:
            target = self.root
        siblings = self.getRelationNodes(target, RELATIONSHIP.SIBLING)
        # pos = max([c.getPos() for c in siblings])
        new_node = self.Node(char.getID(), char)
        self.graph.add_node(char.getID(), new_node)

        ## TODO: Clean this up, must be a cleaner way to do this + make relative to parent, not root
        if target == self.root:
            midpoint = np.ceil(len(siblings)/2)
            if not siblings:
                rel_pos = REL_TREE_POS.MIDDLE
            else:
                for node in siblings:
                    if node.getPos() < midpoint:
                        node.setRelativePos(REL_TREE_POS.LEFT)
                    if node.getPos() == midpoint:
                        node.setRelativePos(REL_TREE_POS.MIDDLE)
                    else:
                        node.setRelativePos(REL_TREE_POS.RIGHT)
                    self.graph.add_edge(char.getID(), node.getID(), RELATIONSHIP.SIBLING, True)
                rel_pos = REL_TREE_POS.RIGHT
        
        else:
            rel_pos = target.getRelativePos()
        
        self.graph.node(char.getID()).build(len(siblings)+1, rel_pos, target.getHeight()+1)
        if relation == RELATIONSHIP.PARENT:
            self.graph.add_edge(char.getID(), target.getID(), RELATIONSHIP.PARENT)
            self.graph.add_edge(target.getID(), char.getID(), RELATIONSHIP.DESCENDANT)
        else:
            self.graph.add_edge(char.getID(), target.getID(), relation, True)
    

    def addMate(self, char, other_char=None):
        if not other_char:
            other_char = self.root
        elif isinstance(other_char, uuid.UUID):
            other_char = self.getNode(other_char)
        else: # Assume character
            other_char = self.getNode(other_char.getID())
        pos = self.getNumRelations(other_char, RELATIONSHIP.SIBLING) + 1
        # FIXME: need to determine the relative position here, shouldn't always be the
        #       same as other_char
        mate = self.Node(char.getID(), char, pos, other_char.getRelativePos(), other_char.getHeight())
        self.graph.add_node(char.getID(), mate)
        self.graph.add_edge(char.getID(), other_char.getID(), RELATIONSHIP.PARTNER, True)

    def removeMate(self, char, other_char):
        if isinstance(char, uuid.UUID):
            char_node = self.getNode(char)
        else: # Assuming character
            char_node = self.getNode(char.getID())

        if isinstance(other_char, uuid.UUID):
            other_node = self.getNode(other_char)
        else: # Assume character
            other_node = self.getNode(other_char.getID())
        if not char_node or not other_node:
            return False

        if self.getNumRelations(char_node, RELATIONSHIP.PARTNER):
            self.graph.del_edge(char_node.getID(), other_node.getID())
            other_char = other_node.getData()
            del other_char
            self.graph.del_node(other_node.getID())
            return True
        return False


    def addParent(self, parent, child=None):
        logging.fatal("Currently under construction")
        ## Old implementation
        # if child == None:
        #     child = self.root
        #     self.root = self.Node(parent, self.TreePos.MIDDLE)
        #     child.parents[0] = self.root
        #     self.root.addNode(child)
        #     self.root.offsetSubTreeHeight(1)
        # else:
        #     new_node = self.Node(parent, child.position, child.getHeight(), child.parents[0])
        #     grand_parent = child.parents[0]
        #     new_node.children = grand_parent.getChildren()
        #     grand_parent.children = [] 
        #     grand_parent.addNode(new_node)
        #     child.parents[0] = new_node
        #     child.parents[1] = None 
        #     # child.setHeight(node.getHeight() + 1)
        #     new_node.offsetSubTreeHeight(1)
            
    def removeNode(self, char):
        if isinstance(char, uuid.UUID):
            self.graph.del_node(char)
        else: # Assume to be character object
           self.graph.del_node(char.getID()) 


    def getSubTree(self, root, collection):
        for node in self.graph.nodes(from_node=root):
            if self.graph.edge(root, node) == RELATIONSHIP.DESCENDANT:
                collection.append(self.graph.node(node))
                self.getSubTree(node, collection)

    
    def getRoot(self):
        return self.root
    
    def getNode(self, target):
        if isinstance(target, uuid.UUID):
            return self.graph.node(target)
        # Assume to be character object
        return self.graph.node(target.getID()) 
    
    def getChar(self, target):
        return self.getNode().getData()

    def getFamHead(self):
        return self.root.getData()


    def getNumRelations(self, node_id, relation):
        return len([n for n in self.graph.edges(from_node=node_id) if n[2] == relation])
        

    def getRelationNodes(self, node_id, relation):
        return [self.graph.node(n[1]) for n in self.graph.edges(from_node=node_id) 
                if n[2] == relation]
    
    def getRelations(self, node_id, relation):
        return [self.graph.node(n[1]).getData() for n in self.graph.edges(from_node=node_id) 
                if n[2] == relation]
    
    def getFamily(self):
        return [self.graph.node(n[1]).getData() for n in self.nodes()]



