''' Responsible for the storage, manipulation, and display of characters.

The family object forms the backbone of the tree. Every character is placed
in a family (potentially of size 1). Characters can be added/removed, partners
can be added/removed, and various display options can be set. 

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

# 3rd Party
from tinydb import where

# User-defined Modules
from .character import Character
from fantasycreator.Data.treeGraph import TreeGraph
from fantasycreator.Data.displayGraph import DisplayGraph
from fantasycreator.Data.hashList import HashList
from fantasycreator.Mechanics.flags import FAM_TYPE, REL_TREE_POS, RELATIONSHIP


# TODO: Need to add more checks on incoming parameters. Too many assumptions 

class Family(qtw.QGraphicsObject):
    ''' Graphical object to store families. Responsible for maintaining relationships,
    character existence, and graphical positioning. Communicates with TreeView
    and TreeScene for displaying characters.
    '''

    ## Custom signals
    edit_char = qtc.pyqtSignal(uuid.UUID)
    add_descendant = qtc.pyqtSignal(uuid.UUID)
    remove_character = qtc.pyqtSignal(uuid.UUID)
    add_partner = qtc.pyqtSignal(uuid.UUID)
    remove_partnership = qtc.pyqtSignal([uuid.UUID], [uuid.UUID, uuid.UUID])

    add_parent = qtc.pyqtSignal(uuid.UUID)
    remove_parent = qtc.pyqtSignal(uuid.UUID)
    tree_moved = qtc.pyqtSignal()
    delete_fam = qtc.pyqtSignal(uuid.UUID)

    ROOT_ANCHOR = qtc.QPointF(5000, 150) # default "origin point"

    def __init__(self, first_gen, family_id, family_type=FAM_TYPE.NULL_TERM, family_name=None, pos=None, parent=None):
        ''' Constructor. Instantiates the family and declares member variables.
        Builds the family with the character(s) passed in as first_gen

        Args:
            first_gen - (Required) list of character(s) to be the head(s) of this family
            family_id - (Required) uuid of this family 
            family_type - optional flag indicating the type of this family
            family_name - optional string name tied to this family
            pos - optional graphical position for this tree's initial location
            parent - optional parent object of this family
        '''
        super(Family, self).__init__(parent)

        ## Create member variables
        self._name = family_name
        self._first_gen = first_gen
        self._id = family_id
        self._fam_type = family_type
        self._tree_loc = pos if pos else self.ROOT_ANCHOR

        self._display_root_partner = False
        self._explode = False
        
        self.tree = TreeGraph(first_gen[0])
        self.display_graph = DisplayGraph()

        self.midpoints = {}
        self.members = HashList()
        self.partners = HashList()
        self.filtered = HashList()

        # Member variables for graphics
        self.current_lines = []
        self.linePen = qtg.QPen(qtg.QColor('black'), 3)
        self.font = qtg.QFont('Didot', 45, italic=True)
        self.font_metric = qtg.QFontMetrics(self.font)
        self.name_graphic = qtw.QGraphicsTextItem()
        self.name_graphic.setFont(self.font)
        self.name_graphic.setParent(self)
        self.name_graphic.setParentItem(self)
        self._name_display = True

        self.setFlags(qtw.QGraphicsItem.ItemIsMovable)

        # Establish first generation
        self.members.add(self._first_gen[0])
        if len(first_gen) == 1:
            self._first_gen.append(None)
        else:
            # char_clone = first_gen[1].clone()
            self.tree.addMate(first_gen[1], family_id) # assume 2nd entry is partner!
            # self.partners.add(first_gen[1])
            # self.members.add(self._first_gen[1])
        self.initFirstGen()


    ## ------------------- Family Method Definitions ----------------- ##

    def initFirstGen(self):
        ''' Add first generation to the scene by declaring the family object
        as their parent. Checks for presence of two characters
        '''
        # self._first_gen[0].setZValue(2)
        self._first_gen[0].setParent(self)
        self._first_gen[0].setParentItem(self)
        if self._display_root_partner and self._first_gen[1]:
            # self._first_gen[1].setZValue(2)
            self._first_gen[1].setParent(self)
            self._first_gen[1].setParentItem(self)
        # self.setNameDisplay(self._name_display)


    ## --------------------- Adding character/mates ------------------ ##

    def addChild(self, child, parent):
        ''' Adds a child character to the supplied parent. Subsequently adds
        the new child to the scene

        Args:
            child - new character object to be added to this family
            parent - character that will be the parent of child
        '''
        self.tree.addNode(child, parent.getID())
        self.members.add(child)
        child.setTreeID(self._id) # fam_id is set by the caller
        child.setParent(self)
        child.setParentItem(self)
    
    def addParent(self, parent, child):
        ''' Adds a parent to a given child. Shifts the child's parents so
        they are now grandparents and the new parent has the childs old parents

        Args:
            parent - new character to serve as a parent to child
            child - character to be the dependent of parent
        '''
        logging.warning('This feature is under construction')
        # parent.setParent(self)
        # parent.setParentItem(self)
        # parent.setTreeID(self._id)
        # self.members.add(parent)
        # if child == self._first_gen[0]:
        #     self.tree.addParent(parent)
        #     self._first_gen[0] = parent
        #     if self._first_gen[1]:
        #         self.partners.add(self._first_gen[1])
        #         self._first_gen[1] = None
        #     if self.scene():
        #         self.installFilters()
        # else:
        #     self.tree.addParent(parent, self.tree.getNode(child))
    
    def addChildRelationship(self, child, parent):
        ''' Simple method to add a child to a parent by inserting child
        into the tree

        Args:
            child - new child character to be added to the tree
            parent - character in this tree to serve as the parent of child
        '''
        self.tree.addNode(child, parent.getID())
    
    def addMate(self, mate, r_id, fam_member):
        ''' Creates a partnership between the two supplied parents. Clones
        the first character passed in and adds the clone to this tree. Returns
        this new clone object

        Args:
            mate - character object to be cloned and paired with fam_member
            r_id - the id of the new relationship
            fam_member - character belonging to this tree that will be the new partner
        '''
        mate_clone = Character(mate.toDict())
        mate_clone.setTreeID(self._id)
        self.tree.addMate(mate_clone, fam_member.getID())
        if fam_member == self.tree.root.getData() and self._first_gen[1] is None:
            self._first_gen[1] = mate_clone
        else:
            self.partners.add(mate_clone)
        return mate_clone
    
    def addMateNoClone(self, mate, r_id, fam_member):
        ''' Specialized method to add a partnership without creating a clone.
        This is necessary when 

        Args:
            mate - character to be partnered with fam_member
            r_id - uuid assigned to this partnership
            fam_member - character belonging to this tree that will be partnered
        '''
        mate.setTreeID(self._id)
        self.tree.addMate(mate, fam_member.getID())
        if fam_member == self.tree.getRoot().getChar() and self._first_gen[1] is None:
            self._first_gen[1] = mate
        else:
            self.partners.add(mate)

    ## ----------------- Removing characters/relationships -------------- ##

    ## TODO: these two methods MUST be doing the same thing and if not, need to be renamed
    def removeMate(self, fam_member, mate):
        ''' Attempts to remove a partnership between two characters. 

        Args:
            fam_member - character in this tree involved in the partnership
            mate - other character in the partnership
        '''
        return self.tree.removeMate(fam_member, mate)
    
    def removePartnership(self, member_id, partner_id):
        ''' Given two character's ids remove their partnership

        Args:
            member_id - uuid of the character in this family
            partner_id - uuid of the partner
        '''
        if self._first_gen[0] == member_id or self._first_gen[1] == member_id:
            return self.splitFirstGen(member_id, partner_id)
        member = self.members.search(member_id)
        partner = self.partners.search(partner_id)
        if member and partner:
            member = member[0]
            partner = partner[0]
            self.scene().removeItem(partner)
            if self.removeMate(member, partner):
                print(f'Removed partnership {partner}')
                self.partners.remove(partner)
                if partner == self._first_gen[1]:
                    self._first_gen[1] = None
                partner.setParent(None)
                del partner
            else:
                return False
        return True
    
    def removeChild(self, child):
        ''' Method to remove a child from the tree. Attempts to access the 
        tree data structure and delete this child node

        Args:
            child - character object to be deleted
        '''
        return self.tree.removeNode(child)


    ## FIXME: this method needs some serious work. Very buggy, hard to follow, and inefficient
    def deleteCharacter(self, char_id):
        ''' Attempts to delete a character including instances in relationships.
        Handles edge cases of being head of family and any partner position.

        Args:
            char_id - uuid of the character to be deleted
        '''
        char_removal = True
        partner_removal = False
        
        if char_id in self.members:
            char = self.members.search(char_id)[0]
            print(f'Removing member: {char}')
            # char_node = self.tree.getNode(char)
            if char_id == self.tree.getRoot() and self._first_gen[1]:
            
                if not self.splitFirstGen(self._first_gen[1], char):
                    return False, False
                partner_removal = True
            
            else:
                # if char_node.getMates():
                if self.tree.getNumRelations(char_id, RELATIONSHIP.PARTNER):
                    # partners = [c.getData() for c in char_node.getMates()]
                    partners = self.tree.getRelations(char_id, RELATIONSHIP.PARTNER)
                    for target in partners:
                        self.scene().removeItem(target)
                        # partner_removal = self.removeMate(char, target)
                        # self.remove_partnership[uuid.UUID, uuid.UUID].emit(char_id, target.getID())
                        self.partners.remove(target)
                        target.setParent(None)
                        del target
                    partner_removal = True
                if self.removeChild(char_id):
                    self.scene().removeItem(char)
                    self.members.remove(char)
                    char.setParent(None)
                    del char
                    char_removal = True
                    
                else:
                    print('Could not remove character. Has children')
                    self.parent().temp_statusbar_msg.emit('Could not remove character. Has children.', 5000)
                    char_removal = False
            
            if self._size <= 0:
                self.delete_fam.emit(self._id)
            
        elif char_id in self.partners:
            char = self.partners.search(char_id)[0]
            # char_node = self.tree.getNode(char)
            if char_id in self.tree:
                print(f'Removing partner: {char}')
                self.scene().removeItem(char)
                # partners = [c.getData() for c in char_node.getMates()]
                partners = self.tree.getRelations(char_id, RELATIONSHIP.PARTNER)
                member = set(self.members.arr).intersection(partners).pop()
                partner_removal = self.removeMate(member, char)
                # self.remove_partnership[uuid.UUID, uuid.UUID].emit(char_id, char.getID())
                self.partners.remove(char)
                char.setParent(None)
                del char
                char_removal = True
            else:
                # return False
                char_removal = False

        elif char_id == self._first_gen[1]:
            char = self._first_gen[1]
            # char_node = self.tree.getNode(char)
            if char_id in self.tree:
                print(f'Removing family head: {char}')
                self.scene().removeItem(char)
                # partners = [c.getData() for c in char_node.getMates()]
                partners = self.tree.getRelations(char_id, RELATIONSHIP.PARTNER)
                member = set(self.members.arr).intersection(partners).pop()
                partner_removal = self.removeMate(member, char)
                # self.remove_partnership[uuid.UUID, uuid.UUID].emit(char_id, char.getID())
                self.partners.remove(char)
                self._first_gen[1] = None
                char.setParent(None)
                del char
                char_removal = True
            else:
                char_removal = False
                # return False
        
        return char_removal, partner_removal
    
    def splitFirstGen(self, remaining_char, removed_char):
        ''' Attempts to separate the heads of this family and delete the
        character that is being removed from the tree. Swaps the positions of
        the two characters if necessary to ensure there is still a head of family

        Args:
            remaining_char - first generation character that is to be kept
            removed_char - other first generation character that is to be deleted
        '''
        logging.fatal('This function is currently under construction until further notice.')
        # if remaining_char != self._first_gen[0]:
        #     self._first_gen[0], self._first_gen[1] = self._first_gen[1], self._first_gen[0]
        #     old_root = self.members.search(removed_char)[0]
        #     root_node = self.tree.getRoot()
        #     root_node.mates = [(x, y) for (x, y) in root_node.mates if x.getData() != self._first_gen[0]]
        #     ## FIXME
        #     # self.tree.replaceNode(removed_char, self._first_gen[0])
        #     self._first_gen[0].setTreeID(self._id)
        #     self._first_gen[0].setParent(self)
        #     self._first_gen[0].setParentItem(self)
        #     self.members.add(self._first_gen[0])
        #     self.members.remove(removed_char)

        # if self.scene():
        #     self.scene().removeItem(self._first_gen[1])

        # if self.removeMate(self._first_gen[0], self._first_gen[1]):
        #     print(f'Split family heads and remove {self._first_gen[1]}')
        #     self._first_gen[1].setParent(None)
        #     del self._first_gen[1]
        #     self._first_gen.append(None)
        #     if self.scene():
        #         self.installFilters()

        #     if self._size <= 1:
        #         self.delete_fam.emit(self._id)
        #     return True
        # return False

    # def updateFirstGen(self, parent):
    #     if parent in self._first_gen:
    #         self._tree_loc.setY(self._first_gen[0].y())
    #         # set midpoint
    #         self._tree_loc.setX((self._first_gen[0].x() + self._first_gen[1].x()) / 2)    

    # Getters & Setters
    def getID(self):
        return self._id
    
    def getName(self):
        return self._name
    
    def getSize(self):
        return len(self.tree.nodes())
    
    def getFirstGen(self):
        return self._first_gen
    
    def getChildren(self, parent):
        return self.tree.getRelations(parent, RELATIONSHIP.DESCENDANT)

    def getAllMembers(self):
        return self.tree.getFamily()

    def getMembersAndPartners(self):
        logging.fatal('Out of order')
        # if self._first_gen[1]:
        #     return self.members.arr + self.partners.arr + [self._first_gen[1]]
        # else:
        #     return self.members.arr + self.partners.arr

    def getMember(self, member):
        return self.tree.getNode(member)
    
    def getRoot(self):
        return self.tree.getFamHead()
    
    def getPartners(self):
        logging.fatal('Out of order')
        # return self.partners.arr

    def getRootPos(self):
        return self._tree_loc

    def setName(self, name):
        self._name = name
    
    def setType(self, _type):
        self._fam_type = _type

    def setRootPos(self, pos):
        self._tree_loc.setX(pos.x())
        self._tree_loc.setY(pos.y())

    def setFirstGen(self, index, char):
        if 0 <= index < 2:
            char_clone = Character(char.toDict())
            char_clone.setTreeID(self._id)
            self._first_gen[index] = char_clone
            self.tree.addMate(self._first_gen[1])
            return char_clone
    
    def setNameDisplay(self, state):
        self._name_display = state
        if not state and self.scene():
            self.scene().removeItem(self.name_graphic)
            self.name_graphic.setParentItem(None)
        else:
            self.name_graphic.setParentItem(self)
            self.name_graphic.installSceneEventFilter(self)
    
    def includeFirstGen(self, state):
        ''' Utility function to display the first generation partners if 
        applicable.

        Args:
            state - boolean value indicating the display of the heads of family
        '''
        logging.fatal('Stupid function. This crash is deserved')
        # self._display_root_partner = state
        # if not self._display_root_partner and self.scene() and self._first_gen[1]:
        #         self.scene().removeItem(self._first_gen[1])
        #         self._first_gen[1].setParent(None)
        #         self._first_gen[1].setParentItem(None)
        # else:
        #     if self._first_gen[1] and self.scene():
        #         self._first_gen[1].setParent(self)
        #         self._first_gen[1].setParentItem(self)
        #         self._first_gen[1].installSceneEventFilter(self)
    
    def explodeFamily(self, state):
        ''' Explodes the family be displaying all partners in this tree

        Args:
            state - boolean value indicating the display of all partners
        '''
        ## TODO: this needs to be revisited 
        self._explode = state
        if not self._explode and self.scene():
            for char in self.partners:
                self.scene().removeItem(char)
                char.setParent(None)
                char.setParentItem(None)
        else:
            for char in self.partners:
                char.setParent(self)
                char.setParentItem(self)

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
        


    ## ------------------- WORKHORSE, DRAWING FUNCTIONS ------------------- ##
    ## TODO: Aren't these set in preferences? Cause if so they should NOT be here
    FIXED_Y = 300 # mimic fixed/standardized character height?
    FIXED_X = 100 # mimic fixed image width
    DESC_DROPDOWN = 125
    PARTNER_SPACING = 200

    EXPAND_CONSTANT = 20 # used to stretch tree horizontally
    OFFSET_CONSTANT = 12 # used to streth each level based on number of sibs + height

    # Workhorse function to create graph struct from tree
    def set_grid(self):
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

    
    def offset_grid(self):
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


    def build_tree(self):
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
            

    def reset_family(self):
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

    def __contains__(self, x):
        return x in self.members

    def __eq__(self, other):
        if isinstance(other, uuid.UUID):
            return self._id == other
        elif isinstance(other, Family):
            return self._id == other._id
        else:
            return self is other

