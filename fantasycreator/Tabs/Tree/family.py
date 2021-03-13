
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

# 3rd Party
from tinydb import where

# User-defined Modules
from treeStruct import Tree
from graphStruct import Graph
from hashList import HashList
from character import Character
from flags import FAM_TYPE


class Family(qtw.QGraphicsObject):

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
        super(Family, self).__init__(parent)
        self._name = family_name
        self._first_gen = first_gen
        self._id = family_id
        self._term_type = family_type
        self._tree_loc = pos if pos else self.ROOT_ANCHOR
        # self._size = len(first_gen)
        self._size = 1
        self._display_root_partner = False
        self._explode = False
        self.tree = Tree(first_gen[0])
        self.graph = Graph()
        self.midpoints = {}
        self.members = HashList()
        self.partners = HashList()
        self.filtered = HashList()

        self.current_lines = []
        self.linePen = qtg.QPen(qtg.QColor('black'), 3)
        # self.namePen = qtg.QPen(qtg.QColor('black'), 2)
        self.font = qtg.QFont('Didot', 45, italic=True)
        self.font_metric = qtg.QFontMetrics(self.font)
        self.name_graphic = qtw.QGraphicsTextItem()
        self.name_graphic.setFont(self.font)
        self.name_graphic.setParent(self)
        self.name_graphic.setParentItem(self)
        self._name_display = True

        self.setFlags(qtw.QGraphicsItem.ItemIsMovable)

        self.members.add(self._first_gen[0])
        
        if len(first_gen) == 1:
            self._first_gen.append(None)
        else:
            # char_clone = first_gen[1].clone()
            self.tree.addMate(first_gen[1], family_id) # assume 2nd entry is partner!
            # self.partners.add(first_gen[1])
            # self.members.add(self._first_gen[1])
        self.initFirstGen()

    def initFirstGen(self):
        # self._first_gen[0].setZValue(2)
        self._first_gen[0].setParent(self)
        self._first_gen[0].setParentItem(self)
        if self._display_root_partner and self._first_gen[1]:
            # self._first_gen[1].setZValue(2)
            self._first_gen[1].setParent(self)
            self._first_gen[1].setParentItem(self)
        # self.setNameDisplay(self._name_display)


    def addChild(self, child, parent):
        self.tree.addNode(child, self.tree.getNode(parent))
        self.members.add(child)
        child.setTreeID(self._id)
        child.setParent(self)
        child.setParentItem(self)
        self._size += 1

    def addChildRelationship(self, child, parent):
        self.tree.addNode(child, self.tree.getNode(parent))
        # self.members.add(child)
        # child.setTreeID(self._id)
        # child.setParent(self)
        # child.setParentItem(self)
        # self._size += 1
    
    def removeChild(self, child):
        if self.tree.removeNode(child):
            self._size -= 1
            return True
        return False

    def addMate(self, mate, r_id, fam_member):
        mate_clone = Character(mate.toDict())
        mate_clone.setTreeID(self._id)
        self.tree.addMate(mate_clone, r_id, self.tree.getNode(fam_member))
        if fam_member == self.tree.root.getData() and self._first_gen[1] is None:
            self._first_gen[1] = mate_clone
        else:
            self.partners.add(mate_clone)
        return mate_clone
    
    def addMateNoClone(self, mate, r_id, fam_member):
        mate.setTreeID(self._id)
        self.tree.addMate(mate, r_id, self.tree.getNode(fam_member))
        if fam_member == self.tree.root.getData() and self._first_gen[1] is None:
            self._first_gen[1] = mate
        else:
            self.partners.add(mate)
    
    def removeMate(self, fam_member, mate):
        if self.tree.removeMate(fam_member, mate):
            return True
        return False

    # def updateFirstGen(self, parent):
    #     if parent in self._first_gen:
    #         self._tree_loc.setY(self._first_gen[0].y())
    #         # set midpoint
    #         self._tree_loc.setX((self._first_gen[0].x() + self._first_gen[1].x()) / 2)

    def addParent(self, parent, child):
        parent.setParent(self)
        parent.setParentItem(self)
        parent.setTreeID(self._id)
        self.members.add(parent)
        if child == self._first_gen[0]:
            self.tree.addParent(parent)
            self._first_gen[0] = parent
            if self._first_gen[1]:
                self.partners.add(self._first_gen[1])
                self._first_gen[1] = None
            if self.scene():
                self.installFilters()
        else:
            self.tree.addParent(parent, self.tree.getNode(child))
        
        

    # Getters & Setters
    def getID(self):
        return self._id
    
    def getName(self):
        return self._name
    
    def getSize(self):
        return self._size
    
    def getFirstGen(self):
        return self._first_gen
    
    def getChildren(self, parent):
        return self.tree.getNode(parent).getChildren()

    def getAllMembers(self):
        return self.members.arr

    def getMembersAndPartners(self):
        if self._first_gen[1]:
            return self.members.arr + self.partners.arr + [self._first_gen[1]]
        else:
            return self.members.arr + self.partners.arr

    def getMember(self, member):
        return self.tree.getNode(member)
    
    def getRoot(self):
        return self.tree.getRoot()
    
    def getPartners(self):
        return self.partners.arr

    def getRootPos(self):
        return self._tree_loc

    def setName(self, name):
        self._name = name
    
    def setType(self, _type):
        self._term_type = _type

    def setRootPos(self, pos):
        self._tree_loc.setX(pos.x())
        self._tree_loc.setY(pos.y())

    
    def setRootHeight(self, height):
        self.tree.root.setHeight(height)

    def setFirstGen(self, index, char, r_id):
        if 0 <= index < 2:
            char_clone = Character(char.toDict())
            char_clone.setTreeID(self._id)
            self._first_gen[index] = char_clone
            self.tree.addMate(self._first_gen[1], r_id)
            return char_clone
    
    def setChildren(self, children):
        for child in tuple(children):
            self.tree.addNode(child, self.tree.getRoot())
            self.members.add(child)
            self._size += 1
    
    def setNameDisplay(self, state):
        self._name_display = state
        if not state and self.scene():
            self.scene().removeItem(self.name_graphic)
            self.name_graphic.setParentItem(None)
        else:
            self.name_graphic.setParentItem(self)
            self.name_graphic.installSceneEventFilter(self)
    
    def includeFirstGen(self, state):
        self._display_root_partner = state
        if not self._display_root_partner and self.scene() and self._first_gen[1]:
                self.scene().removeItem(self._first_gen[1])
                self._first_gen[1].setParent(None)
                self._first_gen[1].setParentItem(None)
        else:
            if self._first_gen[1] and self.scene():
                self._first_gen[1].setParent(self)
                self._first_gen[1].setParentItem(self)
                self._first_gen[1].installSceneEventFilter(self)
    
    def explodeFamily(self, state):
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
    

    def delete_character(self, char_id):

        char_removal = True
        partner_removal = False
        
        if char_id in self.members:
            char = self.members.search(char_id)[0]
            print(f'Removing member: {char}')
            char_node = self.tree.getNode(char)
            if char_node == self.tree.getRoot() and self._first_gen[1]:
                if not self.splitFirstGen(self._first_gen[1], char):
                    return False, False
                partner_removal = True
                    
            
            else:
                if char_node.getMates():
                    partners = [c.getData() for c in char_node.getMates()]
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
            char_node = self.tree.getNode(char)
            if char_node:
                print(f'Removing partner: {char}')
                self.scene().removeItem(char)
                partners = [c.getData() for c in char_node.getMates()]
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
            char_node = self.tree.getNode(char)
            if char_node:
                print(f'Removing family head: {char}')
                self.scene().removeItem(char)
                partners = [c.getData() for c in char_node.getMates()]
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
    
    def removePartnership(self, member_id, partner_id):
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
    
    def splitFirstGen(self, remaining_char, removed_char):
        
        if remaining_char != self._first_gen[0]:
            self._first_gen[0], self._first_gen[1] = self._first_gen[1], self._first_gen[0]
            old_root = self.members.search(removed_char)[0]
            root_node = self.tree.getRoot()
            root_node.mates = [(x, y) for (x, y) in root_node.mates if x.getData() != self._first_gen[0]]
            self.tree.replaceNode(removed_char, self._first_gen[0])
            self._first_gen[0].setTreeID(self._id)
            self._first_gen[0].setParent(self)
            self._first_gen[0].setParentItem(self)
            self.members.add(self._first_gen[0])
            self.members.remove(removed_char)

        if self.scene():
            self.scene().removeItem(self._first_gen[1])

        if self.removeMate(self._first_gen[0], self._first_gen[1]):
            print(f'Split family heads and remove {self._first_gen[1]}')
            self._first_gen[1].setParent(None)
            del self._first_gen[1]
            self._first_gen.append(None)
            if self.scene():
                self.installFilters()

            if self._size <= 1:
                self.delete_fam.emit(self._id)
            return True
        return False
        

    def installFilters(self):
        self._first_gen[0].installSceneEventFilter(self)
        self.setNameDisplay(self._name_display)
        

    def sceneEventFilter(self, source, event):
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
        


    ## WORKHORSE, DRAWING FUNCTIONS
    FIXED_Y = 300 # mimic fixed/standardized character height?
    FIXED_X = 100 # mimic fixed image width
    DESC_DROPDOWN = 125
    PARTNER_SPACING = 200

    EXPAND_CONSTANT = 20 # used to stretch tree horizontally
    OFFSET_CONSTANT = 12 # used to streth each level based on number of sibs + height


    # Workhorse function to create graph struct from tree
    def set_grid(self):
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
        root_char = root_node.getData()
        root_char.setPos(self._tree_loc)
        root_char.addYOffset(self.DESC_DROPDOWN)
        root_id = root_char.getID()
        root_char.setTreePos(char_pos)

        # root relationships with no parent family
        if self._display_root_partner and self._first_gen[1]: 
            
            num_partners = len(root_node.getMates())

            start_x = int(-(0.5 * (num_partners) * self.PARTNER_SPACING))
            midpoint = ((num_partners) * self.PARTNER_SPACING)/2
            
            # Add node to graph and queue
            root_char.addXOffset(start_x)
            self.graph.add_vertex(root_id, root_char)
            q.insert(0, root_node)

            # Create fork and add to graph
            current_fork = f'fork{fork_counter}'
            loc = qtc.QPointF()
            loc.setX(root_char.x())
            loc.setY(root_char.y() + self.DESC_DROPDOWN)
            forkNode = Tree.Node(loc, current_height)
            self.graph.add_vertex(current_fork, loc, False)
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
            forkNode = Tree.Node(loc, current_height)
            self.graph.add_vertex(middle_fork, loc, False)
            q.insert(0, forkNode)
            # print(f'Midpoint at {loc}')

            self.graph.add_edge(middle_fork, f'fork{fork_counter}', self.FIXED_X)
            fork_counter += 1

            for index, char in enumerate(root_node.getMates()):
                offset = ((index + 1) * self.PARTNER_SPACING)

                # Add node to graph and queue
                char.getData().setX(root_char.x() + offset)
                char.getData().setY(root_char.y())
                self.graph.add_vertex(char.getData().getID(), char.getData())


                # Create fork and add to graph
                current_fork = f'fork{fork_counter}'
                loc = qtc.QPointF()
                loc.setX(char.getData().x())
                loc.setY(char.getData().y() + self.DESC_DROPDOWN)
                forkNode = Tree.Node(loc, current_height)
                self.graph.add_vertex(current_fork, loc, False)
                q.insert(0, forkNode)
                # print(f'Fork1 at {loc}')
                self.graph.add_edge(char.getData().getID(), current_fork, self.DESC_DROPDOWN)
                self.graph.add_edge(middle_fork, current_fork, self.FIXED_X)
                fork_counter += 1
                root_relationship_node = True

        elif self._explode and self._first_gen[1]:
            self.graph.add_vertex(self._id, root_char)
            q.insert(0, self.tree.getRoot())
            root_relationship_node = True

        else:
            self.graph.add_vertex(root_id, root_char)
            q.insert(0, self.tree.getRoot())


        char_pos += 1 
        # current_height += 1

        while q != []: 
            count = len(q) 
            while count != 0: 
                count -= 1
                temp_node = q[-1] 

                # print(f'{q.pop()}')
                q.pop()

                if isinstance(temp_node.getData(), Character):
                    offset_col.append(temp_node)
                
                if temp_node.getChildren() != []:
                    parent_char = temp_node.getData()
                    
                    if temp_node is root_node and root_relationship_node:
                        parent_id = self._id
                        parent_x = self.graph.get_vertex(parent_id).get_data().x()

                    
                    elif self._explode and temp_node.mates:
                        # TODO: Only processes first partnership
                        parent_id = temp_node.getPartnerships()[0][1]
                        parent_x = self.graph.get_vertex(parent_id).get_data().x()
                        # print(f'Parent: {parent_id} @ {parent_x}')
                    
                    
                    else:
                        parent_id = parent_char.getID()
                        parent_x = parent_char.x()
    
                    
                    
                    num_children = len(temp_node.getChildren()) 
                    current_height = temp_node.getHeight() + 1
                    
                    ratio_mult = - ((0.5) * (num_children - 1))

                    # Create fork for current descendants
                    current_fork = f'fork{fork_counter}'
                    loc = qtc.QPointF()
                    loc.setY(current_height * self.FIXED_Y + self._tree_loc.y())

                    forkNode = Tree.Node(loc, current_height)
                    self.graph.add_vertex(current_fork, loc, False)

                    self.graph.add_edge(parent_id, current_fork, self.FIXED_Y)
                    loc.setX(parent_x)
                    q.insert(0, forkNode)
                    fork_counter += 1

                    current_x_spacer = self.calcXSpacer(current_height, num_children)

                    for index, child_node in enumerate(temp_node.getChildren()):
                        newFork = f'fork{fork_counter}'
                        loc = qtc.QPointF()
                        
                        current_x = (ratio_mult * current_x_spacer) + parent_x


                        loc.setY(current_height * self.FIXED_Y + self._tree_loc.y())
                        loc.setX(current_x)
                    
                        # Create Fork node and add to grid
                        forkNode = Tree.Node(loc, current_height)
                        self.graph.add_vertex(newFork, loc, False)
                        q.insert(0, forkNode)
                        previous_fork = f'fork{fork_counter-1}'
                        fork_counter += 1

                        # Set child and add to grid
                        child_char = child_node.getData()
                        self.graph.add_vertex(child_char.getID(), child_char)
                        child_char.setX(current_x)
                        child_char.setY((current_height * self.FIXED_Y) + self._tree_loc.y())
                        child_char.addYOffset(self.DESC_DROPDOWN)
                        q.insert(0, child_node)

                        # Connect child to fork
                        self.graph.add_edge(newFork, child_char.getID(), self.DESC_DROPDOWN)
                        child_char.setTreePos(char_pos)
                        child_char.setParentID(parent_id)

                        if num_children % 2 != 0 and index == num_children // 2:
                            self.graph.add_edge(current_fork, newFork, self.FIXED_Y)
                            
                        else:
                            if index == num_children / 2 - 1:
                                # ratio_mult += 1  # "skipping" 0 
                                self.graph.add_edge(newFork, current_fork, self.DESC_DROPDOWN)
                            
                            elif index == num_children / 2:
                                self.graph.add_edge(newFork, current_fork, self.DESC_DROPDOWN)

                        if index != 0:
                            self.graph.add_edge(newFork, previous_fork, self.DESC_DROPDOWN)
                        
                        ratio_mult += 1
                        char_pos += 1
                        
                    
                        if self._explode and child_node.getMates() != []:
                            num_partners = len(child_node.getMates())
                            start_x = 0
                            midpoint = ((num_partners) * self.PARTNER_SPACING)/2
                            bottom_x_pos = child_char.x() + midpoint

                            # Midpoint fork
                            # TODO: Only processes first partnership
                            middle_fork = child_node.getPartnerships()[0][1]
                            loc = qtc.QPointF()
                            loc.setX(bottom_x_pos)
                            loc.setY(child_char.y())
                            # print(f'Middle Fork: {middle_fork} @ {loc}')
                            forkNode = Tree.Node(loc, current_height)
                            self.graph.add_vertex(middle_fork, loc, False)

                            q.insert(0, forkNode)
                            self.graph.add_edge(middle_fork, child_char.getID(), self.PARTNER_SPACING)

                            for index, char in enumerate(child_node.getMates()):
                                offset = start_x + ((index + 1) * self.PARTNER_SPACING)

                                 # Add node to graph and queue
                                char.getData().setX(current_x)
                                char.getData().setY(child_char.y())
                                char.getData().addXOffset(offset)
                                self.graph.add_vertex(char.getData().getID(), char.getData())
                                # q.insert(0, char)
                                # char_pos += 1
                                self.graph.add_edge(char.getData().getID(), middle_fork, self.PARTNER_SPACING)


        # Only need to offset if large enough fam
        if self._size > 2:
            # Preprocess post-order list generated from above
            offset_col = list(reversed(sorted(offset_col, key=lambda x: x.position, reverse=True)))

            pivots = [i for i in range(1, len(offset_col)) if offset_col[i].height!=offset_col[i-1].height]
            pivots.insert(0, 0)

            offset_col = [list(reversed(offset_col[pivots[i-1]:pivots[i]])) 
                                if offset_col[pivots[i]].position==Tree.TreePos.RIGHT 
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

                if sibs[0].position == Tree.TreePos.LEFT:
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
                    node.getSubTree(subtree)
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
        return int((self.FIXED_X) / (height * num_kids) * self.EXPAND_CONSTANT)

    def calcXOffset(self, height, num_sibs):
        # return int((8 * descendants + 4 * num_sibs) / np.square(height)) * self.OFFSET_CONSTANT
        return int(((num_sibs)) * self.OFFSET_CONSTANT) + (self.FIXED_X / height * (num_sibs))

    # def applyOffsets(self, node, parent_offset):
    #     if node is None:
    #         return
    #     num_kids = len(node.getChildren())
    #     # middle_child = False
        
    #     # if num_kids > 1 and num_kids % 2 != 0:
    #     #     middle_child = True
    #     midline = num_kids // 2
    #     ratio_mult = - ((0.5) * (num_kids - 1))
    #     for index, child in enumerate(node.getChildren()):
    #         # if middle_child and index == midline:
    #         #         #print(f"I'm the middle child!: {child} with parent offset: {parent_offset}")
    #         #         child.getData().addXOffset(parent_offset)
    #         #         self.applyOffsets(child, parent_offset)
    #         #         continue
    #         descs = child.getNumDescendants()
    #         # offset = (self.calcXOffset(descs, child.getHeight(), num_kids) * ratio_mult) + parent_offset
    #         # if index < midline:
    #         #     offset *= -1
    #         for partner in child.getMates():
    #             partner.getData().addXOffset(offset)
    #         child.getData().addXOffset(offset)
    #         #print(f'I"m: {child} and I have {descs} descendants and am applying this offset: {offset}')
    #         ratio_mult += 1
    #         self.applyOffsets(child, offset)
    
    def offset_grid(self):
        mid_points = set()
        root_node = self.tree.getRoot()
        if root_node.getPartnerships():
            mid_points.add(self._id)
        for v in self.graph:
            if v.is_valid(): # Character
                for w in v.get_connections():
                    if not w.is_valid() and w.get_id() not in mid_points: # Line
                        if (v.get_weight(w) == self.PARTNER_SPACING):
                            mid = self.calcPartnerMidpoint(w)
                            w.get_data().setX(mid)
                            mid_points.add(w.get_id())
                        else:
                            w.get_data().setX(v.get_data().x())
            else: # Line
                for w in v.get_connections():
                    if not w.is_valid(): # Line
                        if isinstance(w.get_id(), uuid.UUID) and w.get_id() not in mid_points:
                            v.get_data().setX(w.get_data().x())
                        elif w.get_data().y() != v.get_data().y():
                            w.get_data().setX(v.get_data().x())
                        


    # WARNING: ONLY CALCS FIRST PARTNERSHIP
    def calcPartnerMidpoint(self, mid):
        chars = [x for x in mid.get_connections() if x.is_valid()]
        char1 = chars[0].get_data()
        char2 = chars[1].get_data()

        min_x = min(char1.x(), char2.x())
        del_x = abs(char1.x() - char2.x())
        return min_x + (del_x / 2)


    def build_tree(self):
        self.prepareGeometryChange()

        # NOTE: Only place where pos is used to retrieve Vertex
        if not self._display_root_partner and self._explode and self._first_gen[1]: 
            root_vertex = self.graph.get_vertex(self._id) # represents the root node

        else:
            root_vertex = self.graph.get_vertex(self._first_gen[0].getID()) # represents the root node

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
        if self._explode:
            for char in self.partners:
                if char not in self.filtered:
                    self._shape.addRect(char.sceneBoundingRect())

        while q != []:
            s = q.pop(0)
            for i in s.get_connections():
                if i not in visited:
                    q.append(i)
                    visited.add(i)
                 # draw lines
                if {i, s} not in paths:
                    if s.is_valid():
                        if i.is_valid(): # Character -> Character
                            line = qtc.QLineF(s.get_data().pos(), i.get_data().pos())
                        else:   # Character -> Fork
                            line = qtc.QLineF(s.get_data().pos(), i.get_data())
                    else: 
                        if i.is_valid(): # Fork -> Character
                            line = qtc.QLineF(s.get_data(), i.get_data().pos())
                        else: # # Fork -> Fork
                            line = qtc.QLineF(s.get_data(), i.get_data())

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
        self.current_lines[:] = []
    

    def boundingRect(self):
        rect = self.childrenBoundingRect()
        if self._size == 1:
            rect = rect.adjusted(0, 0, 0, 20)
        return rect
    
    def paint(self, painter, option, widget):
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



