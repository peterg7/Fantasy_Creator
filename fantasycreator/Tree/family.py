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
from fantasycreator.Tree.familyGraphics import FamilyGraphics
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

    def __init__(self, first_gen=None, family_id=None, family_type=FAM_TYPE.NULL_TERM, family_name=None, pos=None, parent=None):
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
        self.tree_pos = pos if pos else self.ROOT_ANCHOR

        self._display_root_partner = False
        self._explode = False
        
        self.tree = TreeGraph(first_gen[0])
        self.display = FamilyGraphics(self)

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
    #         self.tree_pos.setY(self._first_gen[0].y())
    #         # set midpoint
    #         self.tree_pos.setX((self._first_gen[0].x() + self._first_gen[1].x()) / 2)    

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

    def setGrid(self):
        self.display.setGrid()
    
    def buildTree(self):
        self.display.buildTree()
    
    def resetFamily(self):
        self.display.resetFamily()
    



    ## ----------------------- Getters & Setters -------------------- ##

    def getFamilyNodes(self):
        return self.tree.getGraphNodes()

    def getFamilyConnections(self):
        return self.tree.getGraphEdges()

    def getID(self):
        return self._id
    
    def getName(self):
        return self._name
    
    def getSize(self):
        return len(self.tree.nodes())
    
    def getRelationship(self, char1, char2):
        return self.tree.getRelationship(char1, char2)
    
    def getParents(self, char):
        return self.tree.getRelations(char,RELATIONSHIP.PARENT)
    
    def getPartners(self, char):
        return self.tree.getRelations(char, RELATIONSHIP.PARTNER)
    
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

    def getTreePos(self):
        return self.tree_pos

    def setName(self, name):
        self._name = name
    
    def setType(self, _type):
        self._fam_type = _type

    def setTreePos(self, pos):
        self.tree_pos.setX(pos.x())
        self.tree_pos.setY(pos.y())

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
        
    def boundingRect(self):
        return self.display.boundingRect()
    
    def shape(self):
        return self.display.shape()
    
    def paint(self, painter, option, widget):
        self.display.paint(painter, option, widget)

    def __contains__(self, x):
        return x in self.members

    def __eq__(self, other):
        if isinstance(other, uuid.UUID):
            return self._id == other
        elif isinstance(other, Family):
            return self._id == other._id
        else:
            return self is other

