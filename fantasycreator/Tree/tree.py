'''Object that contains the inner workings of the tree.

Module for mechanics of the tree. Controls aspects of the tree including
adding/removing characters, creating relationships, creating families, etc. All
data is synced with the database and therefore all other tabs. 

Copyright (c) 2020 Peter C Gish

See the MIT License (MIT) for more information. You should have received a copy
of the MIT License along with this program. If not, see 
<https://www.mit.edu/~amini/LICENSE.md>.
'''
__author__ = "Peter C Gish"
__date__ = "3/16/21"
__maintainer__ = "Peter C Gish"
__version__ = "1.0.1"


# PyQt 
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

# Built-in Modules
import sys
import uuid
import re
import numpy as np
from itertools import groupby
from fractions import Fraction
from collections import deque 
import logging

# 3rd Party
from tinydb import where

# User-defined Modules
from .family import Family
from .treeAccessories import PartnerSelect, ParentSelect, CharacterTypeSelect, CharacterView, CharacterCreator
from .character import Character
from fantasycreator.Dialogs.pictureEditor import PictureEditor 
import fantasycreator.Mechanics.flags as flags
from fantasycreator.Data.graphStruct import Graph
from fantasycreator.Data.hashList import HashList
from fantasycreator.Data.database import DataFormatter

# External resources
from fantasycreator.resources import resources


class Tree(qtc.QObject):
    ''' Object to handle the non-graphical aspects of managing families such as
    creating/removing characters and families.
    '''

    # Custom signals
    addedChars = qtc.pyqtSignal(list)
    removedChars = qtc.pyqtSignal(list)
    updatedChars = qtc.pyqtSignal(list)
    tempStatusbarMsg = qtc.pyqtSignal(str, int)
    familiesRemoved = qtc.pyqtSignal(int, list)
    familiesAdded = qtc.pyqtSignal(int, list)
    kingdomsAdded = qtc.pyqtSignal(int, list)
    kingdomsRemoved = qtc.pyqtSignal(int, list)
    requestFilterChange = qtc.pyqtSignal(int, int)
    hideAddCharacter = qtc.pyqtSignal(bool)

    MasterFamilies = {}
    CharacterList = HashList() # Stores all CHARACTER objects
    #TODO: FIX THESE -> need a better location 
    CURRENT_FAMILY_FLAGS = set()
    CURRENT_FAMILIES = set()
    CURRENT_KINGDOMS = set()

    TREE_DISPLAY = flags.TREE_ICON_DISPLAY.IMAGE


    def __init__(self, parent=None, size=None):
        '''
        Constructor - initialize TreeScene, set window settings, and establish 
        global constants

        Args:
            parent - widget for this object
            size - initial size of the graphics port
        '''
        super(Tree, self).__init__(parent)

        # Local variables
        # TODO: is this necessary?
        self.previous_families = set()
        self.families_in_scene = []
        self.char_selection_timeout = 10000 # in ms


    ##----------------------- Initializaiton Methods ------------------------##

    def initTree(self):
        '''
        Connect signals to each stored family and add each one to the scene
        '''
        logging.debug('Building tree...')
        self.assembleTrees()

        if not Tree.MasterFamilies:
            self.hideAddCharacter.emit(False)
        else:
            self.hideAddCharacter.emit(True)
            for fam_id, family in Tree.MasterFamilies.items():
                family.setParent(self)
                family.edit_char.connect(self.parent().addCharacterEdit)
                family.add_descendant.connect(lambda x: self.parent().createCharacter(flags.CHAR_TYPE.DESCENDANT, x))
                family.remove_character.connect(self.removeCharacter)
                family.add_partner.connect(self.createPartnership)
                family.remove_partnership.connect(self.divorceProctor)
                family.add_parent.connect(self.addParent)
                family.delete_fam.connect(self.deleteFamily)
                
                family.set_grid()
                family.build_tree()
                # self.scene.addFamToScene(family)
                self.parent().scene.addFamToScene(family)
                self.families_in_scene.append(family)
                self.addedChars.emit([char.getID() for char in family.getAllMembers()])
                Tree.CharacterList.add(*family.getMembersAndPartners())
        
        self.setTreeSpacing()
        self.parent().updateView()
    

    def initCharCombos(self):
        '''
        Using the information in the database, extract provided options for
        the combo boxes in character creation and pass them to CharacterCreator
        '''
        sexes = set()
        races = set()
        kingdoms = set()
        families = set()
        for char in self.character_db:
            sexes.add(char['sex'])
            races.add(char['race'])
        for kingdom in self.kingdoms_db:
            kingdoms.add(kingdom['kingdom_name'])
        for fam in self.families_db:
            families.add(fam['fam_name'])

        if '' in sexes:
            sexes.remove('')
        if '' in races:
            races.remove('')
        if '' in kingdoms:
            kingdoms.remove('')
        if '' in families:
            families.remove('')

        CharacterCreator.SEX_ITEMS.extend(sexes)
        CharacterCreator.SEX_ITEMS.append('Other...')
        CharacterCreator.RACE_ITEMS.extend(races)
        CharacterCreator.RACE_ITEMS.append('Other...')
        CharacterCreator.KINGDOM_ITEMS.extend(kingdoms)
        CharacterCreator.KINGDOM_ITEMS.append('New...')
        CharacterCreator.FAMILY_ITEMS.extend(families)
        CharacterCreator.FAMILY_ITEMS.append('None')
    

    def assembleTrees(self):
        '''
        Workhorse function to build the trees stored in the database. Extracts
        all characters and organizes them into families. Establishes all 
        necessary relationships
        '''
        for char_dict in self.character_db:
            graphic_char = Character(char_dict)

            rom_fam_ids = [x['rom_id'] for x in char_dict['partnerships']]
            blood_fam_id = char_dict['fam_id']

            # Create romance family
            for rom_fam_id in rom_fam_ids:
                if rom_fam_id and self.families_db.contains(where('fam_id') == rom_fam_id):
                    if rom_fam_id not in Tree.MasterFamilies.keys():
                        graphic_char.setTreeID(rom_fam_id)
                        Tree.MasterFamilies[rom_fam_id] = Family([graphic_char], rom_fam_id)
                    
                    if graphic_char not in Tree.MasterFamilies[rom_fam_id].getFirstGen():
                        root_char = Tree.MasterFamilies[rom_fam_id].getRoot()
                        Tree.MasterFamilies[rom_fam_id].setFirstGen(1, graphic_char, rom_fam_id)
                
            # Create blood family
            if blood_fam_id and self.families_db.contains(where('fam_id') == blood_fam_id):
                if blood_fam_id not in Tree.MasterFamilies.keys(): #NOTE: Assume sorted order
                    graphic_char.setTreeID(blood_fam_id)
                    Tree.MasterFamilies[blood_fam_id] = Family([graphic_char], blood_fam_id)


            if char_dict['parent_0'] == self.meta_db.all()[0]['NULL_ID']:
                continue

            if char_dict['parent_0']:
                Tree.MasterFamilies[blood_fam_id].addChild(graphic_char, char_dict['parent_0'])

            if char_dict['parent_1']:
                Tree.MasterFamilies[blood_fam_id].addChildRelationship(graphic_char, char_dict['parent_1'])

        for f_id, fam in Tree.MasterFamilies.items():
            fam_record = self.families_db.get(where('fam_id') == f_id)
            if fam_record:
                fam.setName(fam_record['fam_name'])
                fam.setType(fam_record['fam_type'])

        self.connectFamilies()

    def connectFamilies(self):
        '''
        Helper function of assembleTrees() to connect families that have 
        partnerships
        '''
        couples_record = self.character_db.search((where('partnerships') != []))
        relationships = [x['partnerships'] for x in couples_record]
        relationships = [couple for couples in relationships for couple in couples]
        relationships.sort(key=lambda x: x['rom_id'])

        for rom_id, couple in groupby(relationships, key=lambda x:x['rom_id']):
            couple = tuple(couple)
            partner1 = couple[0]
            partner2 = couple[1]

            fam1_id = self.character_db.get(where('char_id') == partner2['p_id'])['fam_id']
            if fam1_id not in Tree.MasterFamilies.keys():
                fam1_id = rom_id
            
            fam2_id = self.character_db.get(where('char_id') == partner1['p_id'])['fam_id']
            if fam1_id not in Tree.MasterFamilies.keys():
                fam2_id = rom_id

            graphics_p1 = Tree.MasterFamilies[fam1_id].getMember(partner2['p_id'])
            graphics_p2 = Tree.MasterFamilies[fam2_id].getMember(partner1['p_id'])

            if rom_id in Tree.MasterFamilies.keys():
                if graphics_p2.getData() in graphics_p1.getMates():
                    Tree.MasterFamilies[fam1_id].addMate(graphics_p2.getData(), rom_id, graphics_p1.getData())
                else:
                    Tree.MasterFamilies[fam2_id].addMate(graphics_p1.getData(), rom_id, graphics_p2.getData())
                continue

            # print(f'connecting {graphics_p1} and {graphics_p2} in {fam1_id}')
            Tree.MasterFamilies[fam1_id].addMate(graphics_p2.getData(), rom_id, graphics_p1.getData())
            Tree.MasterFamilies[fam2_id].addMate(graphics_p1.getData(), rom_id, graphics_p2.getData())



    def connectDB(self, database):
        '''
        Connects to the global database and establishes necessary tables

        Args:
            database - instance of global database
        '''
        # Create tables
        self.meta_db = database.table('meta')
        self.character_db = database.table('characters')
        self.families_db = database.table('families')
        self.kingdoms_db = database.table('kingdoms')
        self.preferences_db = database.table('preferences')
        self.entry_formatter = DataFormatter()

        for family in self.families_db:
            self.CURRENT_FAMILIES.add(family['fam_id'])
        for kingdom in self.kingdoms_db:
            self.CURRENT_KINGDOMS.add(kingdom['kingdom_id'])
        
    def setTreeSpacing(self):
        '''
        Establishes the graphical spacing between multiple trees
        '''
        fam_sizes = [(k, v.boundingRect()) for k,v in Tree.MasterFamilies.items()]
        fam_sizes.sort(key=lambda x: x[1].width(), reverse=True)
        root_y = 0
        root_x = 0
        x_offset = 0
        count = 0
        for fam_id, size in fam_sizes:
            root_loc = qtc.QPoint(root_x, root_y)
            Tree.MasterFamilies[fam_id].setPos(root_loc)
            x_offset = np.power(-1, count) * (abs(x_offset) + size.width()*(2/3))
            root_x = x_offset
            count += 1

    def updatePreferences(self):
        '''
        Upon a change in preferences determine what, if anything, must be changed
        in the tree
        '''
        if pref_record := self.preferences_db.get(where('tab') == 'tree'):
            if val := pref_record.get('generation_spacing', None):
                Family.FIXED_Y = val
            if val := pref_record.get('sibling_spacing', None):
                Family.FIXED_X = val
            if val := pref_record.get('desc_dropdown', None):
                Family.DESC_DROPDOWN = val
            if val := pref_record.get('partner_spacing', None):
                Family.PARTNER_SPACING = val
            if val := pref_record.get('expand_factor', None):
                Family.EXPAND_CONSTANT = val
            if val := pref_record.get('offset_factor', None):
                Family.OFFSET_CONSTANT = val
            if val := pref_record.get('ruler_crown_size', None) and \
                val != Character.CROWN_HEIGHT:
                    Character.CROWN_HEIGHT = val         
            if pref_record.get('ruler_crown_img', None):
                pass # TODO: needs implementation
            if val := pref_record.get('char_img_width', None):
                PictureEditor.CHAR_IMAGE_WIDTH = val
            if val := pref_record.get('char_img_height', None):
                PictureEditor.CHAR_IMAGE_HEIGHT = val
            self.update_tree()

    def update_tree(self):
        '''
        Examines which characters are currently visible and adds/removes them
        from the scene
        '''
        # self.scene.resetScene()
        self.parent().scene.resetScene()
        if not Tree.MasterFamilies:
            self.hideAddCharacter.emit(False)
        else:
            self.hideAddCharacter.emit(True)
            for fam_id, family in Tree.MasterFamilies.items():
                if fam_id in Tree.CURRENT_FAMILIES: #WARNING: not good place for constant
                    family.set_grid()  
                    family.build_tree()
                    # if family not in self.scene.current_families:
                    if family not in self.families_in_scene:
                        # family.initFirstGen()
                        family.setParent(self)
                        # self.addedChars.emit([char.getID() for char in family.getAllMembers()])
                        family.initFirstGen()
                        # self.scene.addFamToScene(family)
                        self.parent().scene.addFamToScene(family)
                else:
                    # if family in self.scene.current_families:
                    if family in self.families_in_scene:
                        # self.removedChars.emit([char.getID() for char in family.getAllMembers()])
                        # self.scene.removeFamFromScene(family) 
                        self.parent().scene.removeFamFromScene(family)
                        family.setParent(None)
        # self.scene.update()
        # self.viewport().update()
        self.parent().updateView()


    ##-------------------- Adding/Modifying Characters ---------------------##

    @qtc.pyqtSlot(list)
    def updateChars(self, char_list):
        '''
        Slot that recieves a list of characters who have been modified and
        need to have their instances updated

        Args: 
            char_list - list of modified character objects
        '''
        for char_id in char_list:
            char_record = self.character_db.get(where('char_id') == char_id)
            char_occurences = Tree.CharacterList.search(char_id)
            for char in char_occurences:
                char.parseDict(char_record)
                char_view = self.findChild(CharacterView, 'view{}'.format(char_id))
                if char_view:
                    char_view.updateView()

    @qtc.pyqtSlot(dict)
    def receiveCharacterUpdate(self, char_dict):
        '''
        Recieves a dictionary representing a character who has been modified. 
        Validates the information and updates the database.

        Args:
            char_dict: dictionary storing a character's information
        '''
        family_name = char_dict.pop('family', None)
        kingdom_name = char_dict.pop('kingdom', None)
        # # Merge dicts
        updated_dict = {**self.character_db.get(where('char_id') == char_dict['char_id']), **char_dict}        
        # TODO: Assert the user wants to change the ENTIRE family name (or check to start a new one)
        if not self.families_db.contains(where('fam_name') == family_name):
            self.families_db.update({'fam_name': family_name}, 
                                where('fam_id') == updated_dict['fam_id'])

        # TODO: Assert the user wants to change the ENTIRE kingdom name (or check to start a new one)
        if not self.kingdoms_db.contains(where('kingdom_name') == kingdom_name):
            self.kingdoms_db.update({'kingdom_name': kingdom_name},
                                where('kingdom_id') == updated_dict['kingdom_id'])
        elif not updated_dict['kingdom_id']:
            updated_dict['kingdom_id'] = self.kingdoms_db.get(where('kingdom_name') == kingdom_name)['kingdom_id']

        formatted_dict = self.entry_formatter.char_entry(updated_dict)
        update = self.character_db.update(formatted_dict, where('char_id') == formatted_dict['char_id'])

        if update:
            self.updatedChars.emit([formatted_dict['char_id']])
            char_occurences = Tree.CharacterList.search(formatted_dict['char_id'])
            for char in char_occurences:
                char.parseDict(formatted_dict)
                char_view = self.findChild(CharacterView, 'view{}'.format(formatted_dict['char_id']))
                if char_view:
                    char_view.updateView()


    @qtc.pyqtSlot(dict, int, Character)
    @qtc.pyqtSlot(dict, int, uuid.UUID)
    def addNewCharacter(self, char_dict, char_type, parent=None):
        '''
        Workhorse for character creation. Creates a new character object
        using the provided character dictionary and specific character type.
        Connects the new character to partners/family members if applicable

        Args: 
            char_dict - Dictionary representation of the new character
            char_type - Character type of the new character (Normal/Partner)
            parent - optional parent (or partner) character of the new one
        '''
        added_partner = False
        if char_type == flags.CHAR_TYPE.DESCENDANT:
            if isinstance(parent, uuid.UUID):
                parent_id = parent
            elif isinstance(parent, Character):
                parent_id = parent.getID()
            elif not parent:
                parent = self.parent().requestCharacter('Please select a parent')
                if isinstance(parent, Character):
                    parent_id = parent.getID()
                elif isinstance(parent, qtc.QPointF):
                    self.newFamilyWrapper([char_dict], fam_type=flags.FAM_TYPE.NULL_TERM, root_pt=parent)
                    return # Parent selection timeout, empty list returned
                else:
                    return
            
            parent_dict = self.character_db.get(where('char_id') == parent_id)
            parent_char_instances = Tree.CharacterList.search(parent_id)
            parent_tree_ids = [instance.getTreeID() for instance in parent_char_instances]
            fam_id = parent_dict['fam_id']
            other_parent_dict = None
            other_parent_tree_ids = []

            # Add to relationship families (if exists)
            if parent_dict['partnerships']:
                if len(parent_dict['partnerships']) > 1:
                    # Need to launch dialog to select which relationship to place the desc. (or discern based on selection)
                    logging.error("More than 1 partner is currently unsupported")
                    return
                else:
                    fam_id = parent_dict['partnerships'][0]['rom_id']
                    other_parent_dict = self.character_db.get(where('char_id') == parent_dict['partnerships'][0]['p_id'])
                    char_dict['parent_1'] = other_parent_dict['char_id']

                    # check to see if this is the first offspring of a partnership
                    if not self.families_db.get(where('fam_id') == fam_id):
                        if response := self.spawnFamily(parent1_id=parent_dict['char_id'],
                                        parent2_id=other_parent_dict['char_id'],
                                        fam1_id=parent_dict['fam_id'], 
                                        fam2_id=other_parent_dict['fam_id'], 
                                        rom_id=fam_id):
                            fam_id = response
                        
                    other_parent_instances = Tree.CharacterList.search(other_parent_dict['char_id'])
                    for instance in other_parent_instances:
                        other_parent_tree_ids.append(instance.getTreeID())

            char_dict['fam_id'] = fam_id
            char_dict['parent_0'] = parent_dict['char_id']

            kingdom_id = self.getKingdom(kingdom_name=char_dict['kingdom'])
            formatted_dict = self.entry_formatter.char_entry(char_dict, kingdom_id=kingdom_id)
            
            fam_record = self.families_db.get(where('fam_id') == fam_id)
            if not fam_record:
                first_gen = [parent_dict]
                if other_parent_dict:
                    first_gen.append(other_parent_dict)
                if not self.newFamilyWrapper(first_gen, fam_id=fam_id):
                    return
                # added_partner = True
                
            # if added_partner:
            #     new_char = Tree.CharacterList.search(formatted_dict['char_id'])[0]
            # else:
            new_char = Character(formatted_dict)
            new_char.setParentID(formatted_dict['parent_0'])
            if other_parent_tree_ids:
                formatted_dict['parent_1'] = other_parent_dict['char_id']
                new_char.setParentID(formatted_dict['parent_1'], 1)
            
            instance_ids = set(parent_tree_ids + other_parent_tree_ids)
            instance_ids.add(fam_id)

            print(instance_ids)

            for f_id in instance_ids:
                if other_parent_dict:
                    if f_id == other_parent_dict['fam_id']:
                        Tree.MasterFamilies[f_id].addChild(new_char, other_parent_dict['char_id'])
                        Tree.MasterFamilies[f_id].addChildRelationship(new_char, parent_dict['char_id'])
                    else:
                        Tree.MasterFamilies[f_id].addChild(new_char, parent_dict['char_id'])
                        Tree.MasterFamilies[f_id].addChildRelationship(new_char, other_parent_dict['char_id'])

                else:
                    Tree.MasterFamilies[f_id].addChild(new_char, parent_dict['char_id'])
                    # Tree.MasterFamilies[f_id].addChild(new_char,
                new_char.setTreeID(f_id)
                Tree.CharacterList.add(new_char)
                # CREATE CLONE
                new_char = Character(new_char.toDict())
            
        elif char_type == flags.CHAR_TYPE.PARTNER:
            if isinstance(parent, uuid.UUID):
                existing_char = Tree.CharacterList.search(parent)[0]
            elif isinstance(parent, list): # assume to be selectionList
                existing_char = parent[0] # get first character
            elif isinstance(parent, Character):
                existing_char = parent
            elif not parent:
                partner = self.parent().requestCharacter('Please select a partner')
                if isinstance(partner, Character):
                    existing_char = partner
                else:
                    print('No partner selected!')
                    return
            
            existing_dict = self.character_db.get(where('char_id') == existing_char.getID())
            
            fam_name = char_dict['family']
            kingdom_id = self.getKingdom(kingdom_name=char_dict['kingdom'])
            formatted_dict = self.entry_formatter.char_entry(char_dict, kingdom_id=kingdom_id)
            
            if not formatted_dict['parent_0']:
                formatted_dict['parent_0'] = self.meta_db.all()[0]['NULL_ID']
                formatted_dict['parent_1'] = self.meta_db.all()[0]['NULL_ID']    
        
            romance_entry = self.entry_formatter.partnership_entry(existing_dict['char_id'])
            formatted_dict['partnerships'] = [romance_entry]
            existing_dict['partnerships'].append(self.entry_formatter.partnership_entry(formatted_dict['char_id'], romance_entry['rom_id']))
            
            # NOTE: set family to NULL if not entered in CharacterCreator
            if not fam_name or char_dict['family'] == 'None':
                create_new_fam = self.parent().confirmNewFamily()
                if create_new_fam == qtw.QMessageBox.Yes:
                    self.newFamilyWrapper([formatted_dict, existing_dict], fam_type=flags.FAM_TYPE.NULL_TERM)
                    added_partner = True
                else:
                    formatted_dict['fam_id'] = self.meta_db.all()[0]['NULL_ID']
                    formatted_dict['parent_0'] = self.meta_db.all()[0]['NULL_ID']
            else: # the partner selected an existing family when created
                fam_id = self.getFamily(fam_name=fam_name)
                if fam_id:
                    formatted_dict['fam_id'] = fam_id
                    parent = self.parent().requestCharacter('Please select a parent')
                    if not isinstance(parent, Character):
                        print("No parent selected! Assigning NULL.")
                        formatted_dict['fam_id'] = self.meta_db.all()[0]['NULL_ID']
                        formatted_dict['parent_0'] = self.meta_db.all()[0]['NULL_ID']

                    else:
                        formatted_dict['parent_0'] = parent.getID()

                    # Don't make a new family if this character is an endpoint
                elif formatted_dict['parent_0'] == self.meta_db.all()[0]['NULL_ID']:
                    fam_entry = self.entry_formatter.family_entry(fam_name, flags.FAM_TYPE.NULL_TERM)
                    formatted_dict['fam_id'] = fam_entry['fam_id']
                    self.families_db.insert(fam_entry)

                else:
                    self.newFamilyWrapper([formatted_dict, existing_dict], fam_name)
                    added_partner = True

            if added_partner:
                new_char = Tree.CharacterList.search(formatted_dict['char_id'])[0]
                new_char_fam = self.character_db.get(where('char_id') == new_char.getID())
                new_char_fam = new_char_fam['fam_id']
            else:
                new_char = Character(formatted_dict)
                new_char_fam = formatted_dict['fam_id']
            
            
            for instance in Tree.CharacterList.search(existing_char.getID()):
                # if formatted_dict['fam_id'] not in Tree.MasterFamilies.keys():
                fam_id = instance.getTreeID()
                if fam_id == existing_dict['fam_id']:
                    if not added_partner:
                        Tree.MasterFamilies[fam_id].addMateNoClone(new_char, romance_entry['rom_id'], existing_char)
                    else:
                        # MAKE CLONE
                        new_char = Tree.MasterFamilies[fam_id].addMate(new_char, romance_entry['rom_id'], existing_char)
                    # Tree.MasterFamilies[fam_id].addMateNoClone(existing_char, romance_entry['rom_id'], new_char)
                    Tree.CharacterList.add(new_char)

                elif fam_id == new_char_fam:
                    continue

                else:
                # instance_ids.append(instance.getTreeID())
                    mate = Tree.MasterFamilies[fam_id].addMate(new_char, romance_entry['rom_id'], instance)
                    Tree.CharacterList.add(mate)
            
            self.character_db.update(existing_dict, where('char_id') == existing_dict['char_id'])
                
            # if flags.FAMILY_FLAGS.INCLUDE_PARTNERS not in self.CURRENT_FAMILY_FLAGS:
            #     self.requestFilterChange.emit(flags.FAMILY_FLAGS.BASE, flags.FAMILY_FLAGS.INCLUDE_PARTNERS)
            # else:
            #     self.CURRENT_FAMILY_FLAGS.remove(flags.FAMILY_FLAGS.INCLUDE_PARTNERS)
            #     self.filterTree(flags.FAMILY_FLAGS.BASE, flags.FAMILY_FLAGS.INCLUDE_PARTNERS)
        else:
            logging.debug('Unknown character type...')
            return

        # print()
        # for char in Tree.CharacterList:
        #     print(char, char.getTreeID())

        # Apply current flags
        target_char = Tree.CharacterList.search(formatted_dict['char_id'])
        if flags.FAMILY_FLAGS.DISPLAY_RULERS in self.CURRENT_FAMILY_FLAGS:
            for char in target_char:
                char.setRulerDisplay(True)              
        else:
            for char in target_char:
                char.setRulerDisplay(False)              

        if Tree.TREE_DISPLAY == flags.TREE_ICON_DISPLAY.IMAGE:
            for char in target_char:
                char.setDisplayMode(flags.TREE_ICON_DISPLAY.IMAGE)              

        elif Tree.TREE_DISPLAY == flags.TREE_ICON_DISPLAY.NAME:
            for char in target_char:
                char.setDisplayMode(flags.TREE_ICON_DISPLAY.NAME)
        # self.scene.update()
        # self.sceneUpdate.emit()

        # enter character into db
        if not added_partner:
            self.character_db.insert(formatted_dict)
            self.addedChars.emit([new_char.getID()])

        # if char_type != CHAR_TYPE.PARTNER:
        self.update_tree()
    
    # Calling signatures
    # 1. list(dict), fam_type, root_pt
    # 2. list(dict), fam_id
    # 3. list(dict, dict) fam_type
    # 4. list(dict, dict) fam_name
    def newFamilyWrapper(self, first_gen, fam_name=None, fam_id=None, fam_type=flags.FAM_TYPE.SUBSET, root_pt=None):    
        if not fam_name and isinstance(first_gen[0], dict):
            fam_name = first_gen[0].get('family', None)
            if not fam_name:
                self.parent().gatherFamName(first_gen, fam_id, fam_type, root_pt)
            return
        self.addNewFamily(first_gen, fam_name, fam_id, fam_type, root_pt)
                

    def addNewFamily(self, first_gen, fam_name, fam_id=None, fam_type=flags.FAM_TYPE.SUBSET, root_pt=None):
        '''
        Workhorse function to build a new family. Collects information on
        family name, generates a family id, and stores the family. Also connects
        family's signals and applies current flags

        Args:
            first_gen - list of characters forming the first generation of the 
                        family
            fam_name - optional parameter to be used as the family name (will
                        be collected using a popup if not provided) 
            fam_id - optional id (will be generated if not provided)
            fam_type - the type of family to be created based on flags
            root_pt - optional parameter of where, graphically, the root of
                        this family will be
        '''
        fam_entry = self.entry_formatter.family_entry(fam_name, fam_type, fam_id)
        fam_id = fam_entry['fam_id'] 
        family_heads = []
        self.families_db.insert(fam_entry) 

        if isinstance(first_gen[0], Character):
            for char in first_gen:
                char_clone = Character(char.toDict())
                char_clone.setTreeID(fam_id)
                family_heads.append(char_clone) # CREATE CLONE

        elif isinstance(first_gen[0], dict):
            for index, char_dict in enumerate(first_gen):
                formatted_dict = self.entry_formatter.char_entry(char_dict)
                char_id = formatted_dict['char_id']

                if self.character_db.contains(where('char_id') == char_id):
                    # CREATE CLONE
                    new_char = Character(formatted_dict)
                    Tree.CharacterList.add(new_char)

                else:
                    formatted_dict['fam_id'] = fam_id
                    if not formatted_dict['parent_0']:
                        formatted_dict['parent_0'] = self.meta_db.all()[0]['NULL_ID']
                    if not formatted_dict['parent_1']:
                        formatted_dict['parent_1'] = self.meta_db.all()[0]['NULL_ID']
                    
                    self.character_db.insert(formatted_dict)
                    new_char = Character(formatted_dict)
                    Tree.CharacterList.add(new_char)
                    self.addedChars.emit([new_char.getID()])
                
                new_char.setTreeID(fam_id)
                family_heads.append(new_char)

        new_family = Family(first_gen=family_heads, family_id=fam_id, family_type=fam_type, family_name=fam_name, pos=root_pt)
        Tree.MasterFamilies[fam_id] = new_family
        self.CURRENT_FAMILIES.add(fam_id)
        self.hideAddCharacter.emit(True)
        # if fam_name not in CharacterCreator.FAMILY_ITEMS:
        #     CharacterCreator.FAMILY_ITEMS.insert(-1, fam_name)

        # Connect signals
        new_family.setParent(self)
        new_family.edit_char.connect(self.parent().addCharacterEdit)
        new_family.add_descendant.connect(lambda x: self.parent().createCharacter(flags.CHAR_TYPE.DESCENDANT, x))
        new_family.remove_character.connect(self.removeCharacter)
        new_family.delete_fam.connect(self.deleteFamily)
        new_family.add_partner.connect(self.createPartnership)
        new_family.add_parent.connect(self.addParent)
        new_family.remove_partnership.connect(self.divorceProctor)

        self.parent().scene.addFamToScene(new_family)
        new_family.set_grid()
        new_family.build_tree()
        
        # Apply current flags
        if flags.FAMILY_FLAGS.CONNECT_PARTNERS in self.CURRENT_FAMILY_FLAGS:
            family_head = self.character_db.get(where('char_id') == family_heads[0].getID())
            self.previous_families.add(new_family.getID())
            if family_head['parent_0'] in Tree.CharacterList:
                self.CURRENT_FAMILIES.remove(new_family.getID())
            else:
                new_family.explodeFamily(True)
        
        if flags.FAMILY_FLAGS.DISPLAY_FAM_NAMES in self.CURRENT_FAMILY_FLAGS:
            new_family.setNameDisplay(False)
        else:
            new_family.setNameDisplay(True)
        
        if flags.FAMILY_FLAGS.INCLUDE_PARTNERS in self.CURRENT_FAMILY_FLAGS:
            new_family.includeFirstGen(True)
        else:
            new_family.includeFirstGen(False)

        self.familiesAdded.emit(flags.SELECTIONS_UPDATE.ADDED_FAM, [fam_entry])
        return True


    @qtc.pyqtSlot(uuid.UUID)
    def addParent(self, char_id):
        '''
        Creates a new parent character for the character passed in. Requires
        the user to select a parent character from the rest of the tree

        Args:
            char_id - the character id of the new child
        '''
        self.selection_window = ParentSelect()
        self.build_char = CharacterCreator(self)
        self.build_char.submitted.connect(lambda d: self.buildParent(d, char_id))
        self.selection_window.new_char.clicked.connect(self.build_char.show)
        self.selection_window.char_select.clicked.connect(lambda: print("In Construction!"))
        self.selection_window.show()


    @qtc.pyqtSlot(dict, uuid.UUID)
    def buildParent(self, parent_dict, child_id):
        '''
        Slot that does the heavy lifting of building a new parent character.
        Builds the new parent object and updates the child with its new parent

        Args:
            parent_dict - dictionary representation of new parent character
            child_id - id of the character that will be the child
        '''
        existing_dict = self.character_db.get(where('char_id') == child_id)
        parent_dict['fam_id'] = existing_dict['fam_id']
        parent_dict['parent_0'] = existing_dict['parent_0']
        parent_dict['parent_1'] = existing_dict['parent_1']
        kingdom_id = self.getKingdom(kingdom_name=parent_dict['kingdom'])
        formatted_dict = self.entry_formatter.char_entry(parent_dict, kingdom_id=kingdom_id)

        # update to-be child
        existing_dict['parent_0'] = formatted_dict['char_id']
        existing_dict['parent_1'] = None # WARNING: not sure if i like this...
        updated_dict = {**self.character_db.get(where('char_id') == child_id), **existing_dict}
        update = self.character_db.update(updated_dict, where('char_id') == child_id)
        new_char = Character(formatted_dict)

        for instance in Tree.CharacterList.search(updated_dict['char_id']):
            fam_id = instance.getTreeID()
            if fam_id == updated_dict['fam_id']:
                Tree.MasterFamilies[fam_id].addParent(new_char, updated_dict['char_id'])
            elif updated_dict['partnerships']:
                if fam_id == updated_dict['partnerships'][0]['rom_id']:
                    Tree.MasterFamilies[fam_id].addParent(new_char, updated_dict['char_id'])
            Tree.CharacterList.add(new_char)
            # MAKE CLONE
            new_char = Character(new_char.toDict())
    
        self.character_db.insert(formatted_dict)
        self.addedChars.emit([new_char.getID()])

        self.update_tree()
    

    @qtc.pyqtSlot(uuid.UUID)
    def createPartnership(self, char_id):
        '''
        Slot to establish a connection between two characters. Takes in one
        character's id and requests the user to select their partner

        Args:
            char_id: id of one of the characters involved in the partnership
        '''
        self.selection_window = PartnerSelect()
        self.selection_window.new_char.clicked.connect(lambda: self.parent().createCharacter(flags.CHAR_TYPE.PARTNER, char_id))
        self.selection_window.char_select.clicked.connect(lambda: self.matchMaker(char_id))
        self.selection_window.show()

    def matchMaker(self, char1_id, char_2=None):
        '''
        Method to join two characters in a partnership. Updates their database
        entries and creates an instance of each character in the other's family

        Args:
            char1_id - id of first character in new partnership
            char2 - optional parameter for the second character (user will be
                    prompted for a selection if none provided)
        '''
        if not char_2:
            # char_2 = self.requestCharacter("Please select a partner")
            char_2 = self.parent().requestCharacter("Please select a partner")
            if not isinstance(char_2, Character):
                return
        char_1 = Tree.CharacterList.search(char1_id)
        if not char_1:
            return
        char_1 = char_1[0]

        if char1_id == char_2.getID():
            print("Can't be your own partner!")
            return
        
        char1_record = self.character_db.get(where('char_id') == char1_id)
        char2_record = self.character_db.get(where('char_id') == char_2.getID())

        fam_1_ids = []
        for instance in Tree.CharacterList.search(char1_id):
            # print(instance.getName(), instance.getID(), instance.getTreeID())
            fam_1_ids.append(instance.getTreeID())

        fam_2_ids = []
        for instance in Tree.CharacterList.search(char_2.getID()):
            # print(instance.getName(), instance.getID(), instance.getTreeID())
            fam_2_ids.append(instance.getTreeID())

        rom_id = None
        if char1_record['partnerships']:
            if len(char1_record['partnerships']) == 1:
                if char1_record['partnerships'][0]['p_id'] == self.meta_db.all()[0]['NULL_ID']:
                    rom_id = char1_record['partnerships'][0]['rom_id']
                    self.character_db.update({'partnerships': []}, where('char_id') == char1_record['char_id'])
                else:
                    print("Replacing partners is not currently supported")
                    return
            else:
                print('Currently can only have one partner at a time.')
                return

        if char2_record['partnerships']:
            if len(char2_record['partnerships']) == 1:
                if char2_record['partnerships'][0]['p_id'] == self.meta_db.all()[0]['NULL_ID']:
                    if rom_id:
                        print("Can't currently combine two divorced families")
                        return
                    rom_id = char2_record['partnerships'][0]['rom_id']
                    self.character_db.update({'partnerships': []}, where('char_id') == char2_record['char_id'])
                else:
                    print("Replacing partners is not currently supported")
                    return
            else:
                print('Currently can only have one partner at a time.')
                return

        char_1_entry = self.entry_formatter.partnership_entry(char_1.getID(), rom_id)
        rom_id = char_1_entry['rom_id']
        char_2_entry = self.entry_formatter.partnership_entry(char_2.getID(), rom_id)

        for fam_id in fam_1_ids:
            try:
                mate = self.MasterFamilies[fam_id].addMate(char_2, rom_id, char_1)
                Tree.CharacterList.add(mate)
            except: #TODO: Clean up these exceptions
                pass
        for fam_id in fam_2_ids:
            try:
                mate = self.MasterFamilies[fam_id].addMate(char_1, rom_id, char_2)
                Tree.CharacterList.add(mate)
            except:
                pass
        
        char1_relationships = char1_record['partnerships'] + [char_1_entry]
        self.character_db.update({'partnerships': char1_relationships}, where('char_id') == char_1.getID())
        char2_relationships = char2_record['partnerships'] + [char_2_entry]
        self.character_db.update({'partnerships': char2_relationships }, where('char_id') == char_2.getID())
        self.update_tree()
    
    def spawnFamily(self, parent1_id, parent2_id, fam1_id, fam2_id, rom_id):
        ''' When a new offspring is spawned off of a partnership, a new family
        is created. This method prompts the user to choose a family name and
        updates the database accordingly
        '''
        parent1_fam = self.families_db.get(where('fam_id') == fam1_id)
        parent2_fam = self.families_db.get(where('fam_id') == fam2_id)

        if not parent1_fam or not parent2_fam:
            logging.debug('Not sure how to handle this situation yet...')
            return False
        if response := self.parent().selectFamilyName([parent1_fam['fam_name'], parent2_fam['fam_name'], 'Other']):
            update_parents = True
            if response == 'Other':
                new_name = self.parent().gatherFamName()
                update_parent = False
            elif response == parent1_fam['fam_name']:
                new_name = parent1_fam['fam_name']
                rom_id = fam1_id
                update_parents = fam1_id
            elif response == parent2_fam['fam_name']:
                new_name = parent2_fam['fam_name']
                rom_id = fam2_id
            
            if not new_name:
                return False
            if update_parents:
                parent1_dict = self.character_db.get(where('char_id') == parent1_id)
                parent2_dict = self.character_db.get(where('char_id') == parent2_id)
                
                # NOTE: assumes only one partnership
                parent1_dict['partnerships'][0]['rom_id'] = rom_id
                parent2_dict['partnerships'][0]['rom_id'] = rom_id

                self.families_db.update(parent1_dict, where('char_id') == parent1_id)
                self.families_db.update(parent2_dict, where('char_id') == parent2_id)

            else:
                formatted_entry = self.entry_formatter.family_entry(new_name, flags.FAM_TYPE.SUBSET, rom_id)
                self.families_db.insert(formatted_entry)
            return rom_id


    ##----------------- Removing characters/relationships ------------------##

    @qtc.pyqtSlot(uuid.UUID)
    def removeCharacter(self, char_id):
        '''
        Slot to remove all isntances of the character with the passed in 
        id from the tree and database

        Args:
            char_id - id of the character to be removed
        '''
        char_removal = True
        partner_removal = False
        first_gen = False
        char_instances = tuple(Tree.CharacterList.search(char_id))

        # find instance of blood family
        

        for instance in char_instances:
            # print(f'{instance.getTreeID()} --> {instance.getName()}')
            first_gen |= (instance is Tree.MasterFamilies[instance.getTreeID()].getFirstGen()[0])
            char_removed, partner_removed = Tree.MasterFamilies[instance.getTreeID()].deleteCharacter(char_id)
            if char_removed:
                Tree.CharacterList.remove(instance)
                del instance
            char_removal &= char_removed
            partner_removal |= partner_removed
        
        char_dict = self.character_db.get(where('char_id') == char_id)

        child = self.findChild(CharacterView, 'view{}'.format(char_id))
        if child is not None:
            child.close()

        if partner_removal:
            partnership = char_dict['partnerships']
            partner_id = partnership[0]['p_id']
            self.divorceProctor(char_id, partner_id)
        if char_removal:
            logger.info(f"Removed {char_dict['name']} from tree")
            self.tempStatusbarMsg.emit(f"Removed {char_dict['name']}", 2000)
            self.removedChars.emit([char_id])
            self.character_db.remove(where('char_id') == char_id)

        self.update_tree()
    
    @qtc.pyqtSlot(uuid.UUID)
    def deleteFamily(self, fam_id):
        '''
        Slot to completely delete a family. The user will be prompted for
        confirmation of delete

        Args:
            fam_id - id of the family to be deleted
        '''
        fam_entry = self.families_db.get(where('fam_id') == fam_id)
        fam_name = fam_entry['fam_name']
        # print(f"Deleting fam: {fam_id, fam_name}")
        # TODO: start here for fixing issue of character deleted even if aborted
        if not self.parent().promptDeleteFam(fam_name):
            return

        # fam_name = self.families_db.get(where('fam_id') == fam_id)['fam_name']
        self.tempStatusbarMsg.emit(f"Removed {fam_name}", 3000)
        if fam_id in self.CURRENT_FAMILIES:
            self.CURRENT_FAMILIES.remove(fam_id)
        fam = self.MasterFamilies[fam_id]
        # self.scene.removeFamFromScene(fam)
        self.parent().removeFamFromScene(fam)
        self.families_in_scene.remove(fam)
        for char in fam.getMembersAndPartners():
            if Tree.CharacterList.search(char):
                for instance in Tree.CharacterList.search(char):
                    if instance.getTreeID() == fam_id:
                        Tree.CharacterList.remove(instance)
                        del instance
        del fam
        del self.MasterFamilies[fam_id]
        self.families_db.remove(where('fam_id') == fam_id)
        self.familiesAdded.emit(flags.SELECTIONS_UPDATE.REMOVED_FAM, [fam_entry])
    
    @qtc.pyqtSlot(uuid.UUID)
    @qtc.pyqtSlot(uuid.UUID, uuid.UUID)
    def divorceProctor(self, char1_id, char2_id=None):
        '''
        Identifies partnership and removes all instances of each character except
        the one in their blood family

        Args:
            char1_id - id of the first character in the relationship
            char2_id - optional, will be found in the database if not provided 
        '''
        char_record = self.character_db.get(where('char_id') == char1_id)
        if char2_id:
            partner_record = self.character_db.get(where('char_id') == char2_id)
        else:
            rom_record = char_record['partnerships']
            if not rom_record:
                self.tempStatusbarMsg.emit(f"No partners to remove!", 2000)
                return
            if len(rom_record) == 1:
                partnership = rom_record[0]
                partner_record = self.character_db.get(where('char_id') == partnership['p_id'])
                if char_record['fam_id'] in Tree.MasterFamilies.keys():
                    Tree.MasterFamilies[char_record['fam_id']].removePartnership(char_record['char_id'], partner_record['char_id'])
                    char_instances = Tree.CharacterList.search(partner_record['char_id'])
                    for i in char_instances:
                        if i.getTreeID() == char_record['fam_id']:
                            Tree.CharacterList.remove(i)
                            break
                
                if partner_record['fam_id'] in Tree.MasterFamilies.keys():
                    Tree.MasterFamilies[partner_record['fam_id']].removePartnership(partner_record['char_id'], char_record['char_id'])
                    char_instances = Tree.CharacterList.search(char_record['char_id'])
                    for i in char_instances:
                        if i.getTreeID() == partner_record['fam_id']:
                            Tree.CharacterList.remove(i)
                            break
                
                if partnership['rom_id'] in Tree.MasterFamilies.keys():
                    Tree.MasterFamilies[partnership['rom_id']].splitFirstGen(char_record['char_id'], partner_record['char_id'])
                    char_instances = Tree.CharacterList.search(partner_record['char_id'])
                    for i in char_instances:
                        if i.getTreeID() == partnership['rom_id']:
                            Tree.CharacterList.remove(i)
                            break
            else:
                self.tempStatusbarMsg.emit(f"In construction", 2000)
                return
        
        fam_divorce = False
        for fam in Tree.MasterFamilies.values():
            if char1_id == fam.getFirstGen()[0] or char2_id == fam.getFirstGen()[0]:
                fam_divorce = True
                break
        if fam_divorce:
            char_partners = [char if char['p_id'] != partner_record['char_id'] 
                        else {'rom_id': char['rom_id'], 'p_id': self.meta_db.all()[0]['NULL_ID']} 
                        for char in char_record['partnerships']]
            partner_partners = [char if char['p_id'] != char_record['char_id'] 
                        else {'rom_id': char['rom_id'], 'p_id': self.meta_db.all()[0]['NULL_ID']} 
                        for char in partner_record['partnerships']]
        else:  
            char_partners = [char for char in char_record['partnerships'] 
                                if char['p_id'] != partner_record['char_id']]
            partner_partners = [char for char in partner_record['partnerships'] 
                                if char['p_id'] != char_record['char_id']]
        
        self.character_db.update({'partnerships': char_partners}, where('char_id') == char_record['char_id'])
        self.character_db.update({'partnerships': partner_partners}, where('char_id') == partner_record['char_id'])
        self.update_tree()


    ##-------------------- Getters ----------------##
    def getKingdom(self, kingdom_name=None, kingdom_id=None):
        if kingdom_name:
            kingdom_record = self.kingdoms_db.get(where('kingdom_name') == kingdom_name)
            if not kingdom_record:
                # print('PROBLEM: unrecognized kingdom, make new??')
                new_kingdom = self.entry_formatter.kingdom_entry(kingdom_name, kingdom_id)
                update = self.kingdoms_db.insert(new_kingdom)
                self.kingdomsAdded.emit(flags.SELECTIONS_UPDATE.ADDED_KINGDOM, [new_kingdom])
            else:
                return kingdom_record['kingdom_id']
        elif kingdom_id:
            kingdom_record = self.kingdoms_db.get(where('kingdom_id') == kingdom_id)
            if not kingdom_record:
                # print('PROBLEM: unrecognized kingdom, make new??')
                new_kingdom = self.entry_formatter.kingdom_entry(kingdom_name, kingdom_id)
                update = self.kingdoms_db.insert(new_kingdom)
                self.kingdomsAdded.emit(flags.SELECTIONS_UPDATE.ADDED_KINGDOM, [new_kingdom])
            else:
                return kingdom_record['kingdom_name']
        else:
            return self.kingdoms_db.get(where('kingdom_name') == 'None')

    def getFamily(self, fam_name=None, fam_id=None):
        if fam_name:
            fam_record = self.families_db.get(where('fam_name') == fam_name)
            if not fam_record:
                logging.warning('PROBLEM: unrecognized family, make new??')
            else:
                return fam_record['fam_id']
        elif fam_id:
            fam_record = self.families_db.get(where('fam_id') == fam_id)
            if not fam_record:
                logging.warning('PROBLEM: unrecognized family, make new??')
            else:
                return fam_record['fam_name']
        else:
            return self.families_db.get(where('fam_name') == 'None')
    
    

    # TODO: combine or just organize these two methods
    ##--------------------------- View Filtering --------------------------##
    def filterKingdoms(self, kingdom_record, filter_state):
        filtered_chars = self.character_db.search(where('kingdom_id') == kingdom_record['kingdom_id'])
        if filtered_chars:
            if filter_state:
                for char in filtered_chars:
                    for graphic_char in Tree.CharacterList.search(char['char_id']):
                        Tree.MasterFamilies[graphic_char.getTreeID()].filtered.remove(graphic_char)
                        graphic_char.setParent(Tree.MasterFamilies[graphic_char.getTreeID()])
                        graphic_char.setParentItem(Tree.MasterFamilies[graphic_char.getTreeID()])
            else:
                for char in filtered_chars:
                    for graphic_char in Tree.CharacterList.search(char['char_id']):
                        Tree.MasterFamilies[graphic_char.getTreeID()].filtered.add(graphic_char)
                        # self.scene.removeItem(graphic_char)
                        self.parent().scene.removeItem(graphic_char)
                        graphic_char.setParent(None)
                        graphic_char.setParentItem(None)
            # self.scene.update()
            # self.viewport().update()
            self.parent().updateView()

    @qtc.pyqtSlot(int, str)
    @qtc.pyqtSlot(int, int)
    def filterTree(self, flag_type, flag):
        if flag_type == flags.FAMILY_FLAGS.BASE:
            if flag == flags.FAMILY_FLAGS.DISPLAY_RULERS:
                if flags.FAMILY_FLAGS.DISPLAY_RULERS in self.CURRENT_FAMILY_FLAGS:
                    self.CURRENT_FAMILY_FLAGS.remove(flags.FAMILY_FLAGS.DISPLAY_RULERS)
                    print("Showing rulers")
                    for family in self.MasterFamilies.values():
                        for char in family.getMembersAndPartners():
                            char.setRulerDisplay(True)              

                else:
                    self.CURRENT_FAMILY_FLAGS.add(flags.FAMILY_FLAGS.DISPLAY_RULERS)
                    print("Hidding rulers")
                    for family in self.MasterFamilies.values():
                        for char in family.getMembersAndPartners():
                            char.setRulerDisplay(False)              
                # self.scene.update()
                self.parent().updateView()
            
            elif flag == flags.FAMILY_FLAGS.DISPLAY_FAM_NAMES:
                if flags.FAMILY_FLAGS.DISPLAY_FAM_NAMES in self.CURRENT_FAMILY_FLAGS:
                    self.CURRENT_FAMILY_FLAGS.remove(flags.FAMILY_FLAGS.DISPLAY_FAM_NAMES)
                    print("Showing family names")
                    for family in self.MasterFamilies.values():
                        family.setNameDisplay(True)
                            
                else:
                    self.CURRENT_FAMILY_FLAGS.add(flags.FAMILY_FLAGS.DISPLAY_FAM_NAMES)
                    print("Hiding family names")
                    for family in self.MasterFamilies.values():
                        family.setNameDisplay(False)
                # self.scene.update()
                self.parent().updateView()

            elif flag == flags.FAMILY_FLAGS.INCLUDE_PARTNERS:
                if flags.FAMILY_FLAGS.INCLUDE_PARTNERS in self.CURRENT_FAMILY_FLAGS:
                    self.CURRENT_FAMILY_FLAGS.remove(flags.FAMILY_FLAGS.INCLUDE_PARTNERS)
                    print("Hidding partners")
                    for family in self.MasterFamilies.values():
                        family.includeFirstGen(False)

                else:
                    self.CURRENT_FAMILY_FLAGS.add(flags.FAMILY_FLAGS.INCLUDE_PARTNERS)
                    print("Showing partners")
                    for family in self.MasterFamilies.values():
                        family.includeFirstGen(True)
                self.update_tree()

            elif flag == flags.FAMILY_FLAGS.CONNECT_PARTNERS:
                if flags.FAMILY_FLAGS.CONNECT_PARTNERS in self.CURRENT_FAMILY_FLAGS:
                    self.CURRENT_FAMILY_FLAGS.remove(flags.FAMILY_FLAGS.CONNECT_PARTNERS)
                    print('Separating families')
                    for fam_id, family in self.MasterFamilies.items():
                        if fam_id in self.previous_families:
                            if fam_id in self.CURRENT_FAMILIES:
                                family.explodeFamily(False)
                            self.CURRENT_FAMILIES.add(fam_id)
                    
                else:
                    self.CURRENT_FAMILY_FLAGS.add(flags.FAMILY_FLAGS.CONNECT_PARTNERS)
                    print('Connecting families')
                    self.previous_families = set(self.CURRENT_FAMILIES)
                    for fam_id, family in self.MasterFamilies.items():
                        # family_head = self.character_db.get(where('char_id') == family.getFirstGen()[0].getID())
                        # char_instances = Tree.CharacterList.search(family_head['char_id'])

                        # if (family_head['parent_0'] in Tree.CharacterList or family_head['parent_1'] in Tree.CharacterList) \
                        #     or family_head['parent_0'] != termination_id \
                        if family._term_type != flags.FAM_TYPE.NULL_TERM and fam_id in self.previous_families:
                            self.CURRENT_FAMILIES.remove(family.getID())
                        else:
                            family.explodeFamily(True)
                    if flags.FAMILY_FLAGS.INCLUDE_PARTNERS not in self.CURRENT_FAMILY_FLAGS:
                        self.requestFilterChange.emit(flags.FAMILY_FLAGS.BASE, flags.FAMILY_FLAGS.INCLUDE_PARTNERS)

                self.update_tree()

        elif flag_type == flags.TREE_ICON_DISPLAY.BASE:
            if flag == flags.TREE_ICON_DISPLAY.IMAGE:
                print('Showing as image')
                Tree.TREE_DISPLAY = flag
                for char in Tree.CharacterList:
                    char.setDisplayMode(flags.TREE_ICON_DISPLAY.IMAGE)              

            elif flag == flags.TREE_ICON_DISPLAY.NAME:
                print('Showing as name')
                Tree.TREE_DISPLAY = flag
                for char in Tree.CharacterList:
                    char.setDisplayMode(flags.TREE_ICON_DISPLAY.NAME)
            # self.scene.update()
            self.parent().updateView()
        
        elif flag_type == flags.GROUP_SELECTION_ITEM.FAMILY:
            family_record = self.families_db.get(where('fam_name') == flag)
            if family_record:
                family_id = family_record['fam_id']
                if family_id in self.CURRENT_FAMILIES:
                    self.CURRENT_FAMILIES.remove(family_id)
                    print(f'Removed family {flag}')
                elif flags.FAMILY_FLAGS.CONNECT_PARTNERS not in self.CURRENT_FAMILY_FLAGS:
                    self.CURRENT_FAMILIES.add(family_id)
                    print(f'Added family {flag}')
                self.update_tree()
                
        
        elif flag_type == flags.GROUP_SELECTION_ITEM.KINGDOM:
            kingdom_record = self.kingdoms_db.get(where('kingdom_name') == flag)
            if kingdom_record:
                kingdom_id = kingdom_record['kingdom_id']
                if kingdom_id in self.CURRENT_KINGDOMS:
                    self.CURRENT_KINGDOMS.remove(kingdom_id)
                    self.filterKingdoms(kingdom_record, False)
                    print(f'Removed kingdom {flag}')
                else:
                    self.CURRENT_KINGDOMS.add(kingdom_id)
                    self.filterKingdoms(kingdom_record, True)
                    print(f'Added kingdom {flag}')
            
        else:
            print("Unknown Flag Type!!")
        return
