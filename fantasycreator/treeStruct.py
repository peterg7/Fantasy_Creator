"""
Pure python implementation of a general tree
"""
from enum import IntFlag, unique

class Tree:
    
    @unique
    class TreePos(IntFlag):
        LEFT = 0
        RIGHT = 1
        MIDDLE = 2

    class Node:

        def __init__(self, data, pos, ht = 0, parent1=None, parent2=None):
            self.data = data
            self.position = pos
            self.parents = [parent1, parent2]
            self.children = []
            self.mates = []
            self.height = ht
        
        def getHeight(self):
            return self.height
        
        def setHeight(self, ht):
            if ht < -1:
                return False
            self.height = ht
            return True

        def offsetHeight(self, offset):
            self.height += offset

        def addNode(self, obj):
            if obj not in self.children:
                self.children.append(obj)
        
        def addMate(self, obj, r_id):
            if obj not in self.mates:
                self.mates.append((obj, r_id))

        
        def removeNode(self, obj):
            try:
                self.children.remove(obj)
                return True
            except ValueError:
                return False
        
        def setParents(self, index, obj):
            self.parents[index] = obj
        
        # def getParents(self, index):
        #     return self.parents[index]

        def getData(self):
            return self.data
        
        def getParents(self):
            return self.parents

        def getChildren(self):
            return self.children
        
        def getMates(self):
            return [char for (char, _id) in self.mates]
        
        def getPartnerships(self):
            return self.mates

        def find(self, val):
            if self.data == val:
                return self
            if [i for i in self.mates if i[0].getData() == val]:
                return [i for i in self.mates if i[0].getData() == val][0][0]
            for node in self.children:
                n = node.find(val)
                if n:
                    return n
            return None

        def getNumDescendants(self):
            count = 1
            for child in self.children:
                count += child.getNumDescendants()
            return count
        
        def getExtendedSubTree(self, nodeList):
            for child in self.children:
                nodeList.extend([mate for (mate, _id) in child.mates])
                if child.children:
                    child.getExtendedSubTree(nodeList)
                    nodeList.append(child)                
                else:
                    nodeList.append(child)
            nodeList.extend([mate for (mate, _id) in self.mates])
        
        def getSubTree(self, nodeList):
            for child in self.children:
                if child.children:
                    child.getSubTree(nodeList)
                    nodeList.append(child)
                else:
                    nodeList.append(child)
        

        def offsetSubTreeHeight(self, offset):
            for child in self.children:
                if child.children:
                    child.offsetSubTreeHeight(offset)
                    child.offsetHeight(offset)
                else:
                    child.offsetHeight(offset)

        
        def __str__(self):
            if self.data.__str__:
                return (f'NODE: {self.data.__str__()}')
            else:
                return self

##------------------- Tree Defs -------------------------##

    def __init__(self, root):
        self.root = self.Node(root, self.TreePos.MIDDLE)
        self.Nodes = []

    def addNode(self, obj, node=None):
        if node == None:
            node = self.root
        if node == self.root:
            num_kids = len(node.children)
            if not num_kids:
                pos = self.TreePos.MIDDLE
            else:
                middle_child = num_kids / 2
                for index, child in enumerate(node.children):
                    if index < middle_child:
                        child.position = self.TreePos.LEFT
                    elif index == middle_child:
                        child.position = self.TreePos.MIDDLE
                    else:
                        child.position = self.TreePos.RIGHT
                pos = self.TreePos.RIGHT
            
        else:
            pos = node.position
        
        node.addNode(self.Node(obj, pos, node.getHeight() + 1, node))
    
    def addMate(self, obj, r_id, node=None):
        if node == None:
            node = self.root
        mate = self.Node(obj, node.position, node.getHeight(), node)
        node.addMate(mate, r_id)
        mate.addMate(node, r_id)
    
    def addParent(self, obj, node=None):
        if node == None:
            node = self.root
            self.root = self.Node(obj, self.TreePos.MIDDLE)
            node.parents[0] = self.root
            self.root.addNode(node)
            self.root.offsetSubTreeHeight(1)
        else:
            new_node = self.Node(obj, node.position, node.getHeight(), node.parents[0])
            grand_parent = node.parents[0]
            new_node.children = grand_parent.getChildren()
            grand_parent.children = [] 
            grand_parent.addNode(new_node)
            node.parents[0] = new_node
            node.parents[1] = None 
            # node.setHeight(node.getHeight() + 1)
            new_node.offsetSubTreeHeight(1)

        

    def replaceNode(self, obj, newData):
        node = self.root.find(obj)
        node.data = newData
    
    def removeNode(self, obj):
        node = self.getNode(obj)
        if node.children == []:
            if node.parents[0]:
                node.parents[0].removeNode(node)
            if node.parents[1]:
                node.parents[1].removeNode(node)
            del node
            return True
        else:
            return False
    
    def removeMate(self, obj, partner):
        node = self.getNode(obj)
        if not node:
            return False
        if node.mates != 0:
            node.mates = [(x, y) for (x, y) in node.mates if x.getData() != partner]
            del partner
            return True
        else:
            return False


    def setRoot(self, new_root):
        self.root = new_root
    
    def getRoot(self):
        return self.root
    
    def getNode(self, obj):
        return self.root.find(obj)
    
    def get_depth(self):
        return self.get_max_depth(self.root)

    def get_max_depth(self, root):
        height = 0
        if root is None:
            return height 
        if root.getChildren() is None:
            return 1
        for child in root.getChildren():
            height = max(height, self.get_max_depth(child))
        return height + 1
    
    def get_width(self):
        return self.get_max_width(self.root)
    
    def get_max_width(self, root): 
        if root is None: 
            return 0
        q = [] 
        maxWidth = 0
        q.insert(0,root) 

        while q != []: 
            count = len(q) 
            maxWidth = max(count, maxWidth) 
            
            while count != 0: 
                count -= 1
                temp = q[-1]   
                q.pop()
                if temp.getChildren() is not None:
                    for child in temp.getChildren():
                        q.insert(0, child)
        return maxWidth

    def getAllNodes(self):
        self.Nodes = []
        self.Nodes.append(self.root)
        for child in self.root.getChildren():
            self.Nodes.append(child)
        for child in self.root.getChildren():
            if child.getSubTree(self.Nodes) != None:
                child.getSubTree(self.Nodes)
        return self.Nodes
    
    def getAllNodeswMates(self):
        self.Nodes = []
        self.Nodes.append(self.root)
        for child in self.root.getChildren():
            self.Nodes.append(child)
        self.Nodes.extend([mate for (mate, _id) in self.root.mates])
        for child in self.root.getChildren():
            if child.getExtendedSubTree(self.Nodes) != None:
                child.getExtendedSubTree(self.Nodes)
        return self.Nodes
    
    def getAllDatawMates(self):
        self.getAllNodeswMates()
        return [x.getData() for x in self.Nodes]
    
    def getAllData(self):
        self.getAllNodes()  ### UGLY UGLY UGLY  : dont always need to call
        return [x.getData() for x in self.Nodes]
        #print(*self.Nodes, sep = "\n")
        # for node in self.Nodes:
        #     print((node[1] * '\t') + node[0].name)
        # print('Tree Size: ' + str(len(self.Nodes)))
    def getCurrentIDList(self):
        self.getAllNodes()
        return [x.getData().getID() for x in self.Nodes]


# # Add a bunch of nodes
# FunCorp =  Tree('Head Honcho')
# FunCorp.addNode(Tree.Node('VP of Stuff'))
# FunCorp.addNode(Tree.Node('VP of Shenanigans'))
# FunCorp.addNode(Tree.Node('VP of Hootenanny'))
# FunCorp.children[0].addNode(Tree.Node('General manager of Fun'))
# FunCorp.children[1].addNode(Tree.Node('General manager Shindings'))
# FunCorp.children[0].children[0].addNode(Tree.Node('Sub manager of Fun'))
# FunCorp.children[0].children[0].children[0].addNode(Tree.Node('Employee of the month'))
# print(FunCorp.root.getChildNodes(FunCorp,0))
# # Get all nodes (unordered):
# FunCorp.getAllNodes()