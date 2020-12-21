

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

# 3rd Party
from tinydb import where

# User-defined Modules
from flags import *
from family import Family
from graphStruct import Graph
from hashList import HashList
from database import DataFormatter
from character import Character, CharacterView, CharacterCreator, UserLineInput, PictureEditor

# External resources
import resources

# create Tree view
class TreeView(qtw.QGraphicsView):

    # Custom signals
    addedChars = qtc.pyqtSignal(list)
    removedChars = qtc.pyqtSignal(list)
    updatedChars = qtc.pyqtSignal(list)
    temp_statusbar_msg = qtc.pyqtSignal(str, int)
    families_removed = qtc.pyqtSignal(int, list)
    families_added = qtc.pyqtSignal(int, list)
    scene_clicked = qtc.pyqtSignal(qtc.QPoint)
    requestFilterChange = qtc.pyqtSignal(int, int)

    zoomChanged = qtc.pyqtSignal(int)
    setCharDel = qtc.pyqtSignal(bool)


    MasterFamilies = {}
    CharacterList = HashList() # Stores all CHARACTER objects

    #TODO: FIX THESE -> need a better location 
    CURRENT_FAMILY_FLAGS = set()
    TREE_DISPLAY = TREE_ICON_DISPLAY.IMAGE
    CURRENT_FAMILIES = set()
    CURRENT_KINGDOMS = set()
    CENTER_ANCHOR = qtc.QPointF(5000, 150)
    DFLT_VIEW = qtc.QRectF(4000, 150, 5000, 1000)

    MIN_ZOOM = -8
    MAX_ZOOM = 8

    def __init__(self, parent=None, size=None):
        super(TreeView, self).__init__(parent)
        print('Initializing tree...')
        
        # Setup Scene
        self.scene = TreeScene(self)
        self.setScene(self.scene)
        self.setVerticalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
        self.centerOn(self.CENTER_ANCHOR)
        self.setResizeAnchor(qtw.QGraphicsView.AnchorViewCenter)
        self.setTransformationAnchor(qtw.QGraphicsView.NoAnchor)
        self.setRenderHints(qtg.QPainter.Antialiasing | qtg.QPainter.SmoothPixmapTransform)
        
        self.viewport().grabGesture(qtc.Qt.PinchGesture)
        self.viewport().setAttribute(qtc.Qt.WA_AcceptTouchEvents)

        # Local variables
        self.zoom_factor = 1
        self.current_factor = 1
        self.zoomStatus = 0
        self.zoom_tracker = 0 
        self.char_selection_timeout = 10000 # in ms
        self.char_views = []
        self._pan = False
        self._pan_act = False
        self.selecting_char = False
        self.selected_char = None
        self._mousePressed = False
        self.last_mouse = None
        self.previous_families = set()

 
    ## Auxiliary Methods ##

    def init_tree_view(self):
        print('Building tree...')
        self.assembleTrees()
        for fam_id, family in TreeView.MasterFamilies.items():
            family.setParent(self)
            family.edit_char.connect(self.add_character_edit)
            family.add_descendant.connect(lambda x: self.createCharacter(CHAR_TYPE.DESCENDANT, x))
            family.remove_character.connect(self.remove_character)
            family.add_partner.connect(self.createPartnership)
            family.remove_partnership.connect(self.divorceProctor)
            family.add_parent.connect(self.addParent)
            family.delete_fam.connect(self.delete_family)
            
            family.set_grid()
            family.build_tree()
            self.scene.add_family_to_scene(family)
            self.addedChars.emit([char.getID() for char in family.getAllMembers()])
            TreeView.CharacterList.add(*family.getMembersAndPartners())
        
        self.setTreeSpacing()
        self.scene.update()
        self.viewport().update()
    
    def init_char_dialogs(self):
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

        CharacterCreator.SEX_ITEMS.extend(x for x in sexes)
        CharacterCreator.SEX_ITEMS.append('Other...')
        CharacterCreator.RACE_ITEMS.extend(x for x in races)
        CharacterCreator.RACE_ITEMS.append('Other...')
        CharacterCreator.KINGDOM_ITEMS.extend(x for x in kingdoms)
        CharacterCreator.KINGDOM_ITEMS.append('New...')
        CharacterCreator.FAMILY_ITEMS.extend(x for x in families)


    def assembleTrees(self):
        for char_dict in self.character_db:
            graphic_char = Character(char_dict)

            rom_fam_ids = [x['rom_id'] for x in char_dict['partnerships']]
            blood_fam_id = char_dict['fam_id']

            # Create romance family
            for rom_fam_id in rom_fam_ids:
                if rom_fam_id and self.families_db.contains(where('fam_id') == rom_fam_id):
                    
                    if rom_fam_id not in TreeView.MasterFamilies.keys():
                        graphic_char.setTreeID(rom_fam_id)
                        TreeView.MasterFamilies[rom_fam_id] = Family([graphic_char], rom_fam_id)
                    
                    if graphic_char not in TreeView.MasterFamilies[rom_fam_id].getFirstGen():
                        root_char = TreeView.MasterFamilies[rom_fam_id].getRoot()
                        TreeView.MasterFamilies[rom_fam_id].setFirstGen(1, graphic_char, rom_fam_id)
                
            # Create blood family
            if blood_fam_id and self.families_db.contains(where('fam_id') == blood_fam_id):
                if blood_fam_id not in TreeView.MasterFamilies.keys(): #NOTE: Assume sorted order
                    graphic_char.setTreeID(blood_fam_id)
                    TreeView.MasterFamilies[blood_fam_id] = Family([graphic_char], blood_fam_id)


            if char_dict['parent_0'] == self.meta_db.all()[0]['NULL_ID'] or char_dict['parent_0'] == self.meta_db.all()[0]['TERM_ID']:
                continue

            if char_dict['parent_0']:
                TreeView.MasterFamilies[blood_fam_id].addChild(graphic_char, char_dict['parent_0'])

            if char_dict['parent_1']:
                TreeView.MasterFamilies[blood_fam_id].addChildRelationship(graphic_char, char_dict['parent_1'])

        for f_id, fam in TreeView.MasterFamilies.items():
            fam_record = self.families_db.get(where('fam_id') == f_id)
            if fam_record:
                fam.setName(fam_record['fam_name'])
                fam.setType(fam_record['fam_type'])

        self.connectFamilies()

        # for fam in TreeView.MasterFamilies.values():
        #     print(f'\nFam: {fam.getID()}')
        #     for char in fam.getMembersAndPartners():
        #         print(char, char.getTreeID())

        # self.treetab.build_tree(TreeView.MasterFamilies, self.database, self.size())
  
    
    def connectFamilies(self):
        couples_record = self.character_db.search((where('partnerships') != []))
        relationships = [x['partnerships'] for x in couples_record]
        relationships = [couple for couples in relationships for couple in couples]
        relationships.sort(key=lambda x: x['rom_id'])

        for rom_id, couple in groupby(relationships, key=lambda x:x['rom_id']):
            couple = tuple(couple)
            partner1 = couple[0]
            partner2 = couple[1]

            fam1_id = self.character_db.get(where('char_id') == partner2['p_id'])['fam_id']
            if fam1_id not in TreeView.MasterFamilies.keys():
                fam1_id = rom_id
            
            fam2_id = self.character_db.get(where('char_id') == partner1['p_id'])['fam_id']
            if fam1_id not in TreeView.MasterFamilies.keys():
                fam2_id = rom_id

            graphics_p1 = TreeView.MasterFamilies[fam1_id].getMember(partner2['p_id'])
            graphics_p2 = TreeView.MasterFamilies[fam2_id].getMember(partner1['p_id'])

            if rom_id in TreeView.MasterFamilies.keys():
                if graphics_p2.getData() in graphics_p1.getMates():
                    TreeView.MasterFamilies[fam1_id].addMate(graphics_p2.getData(), rom_id, graphics_p1.getData())
                else:
                    TreeView.MasterFamilies[fam2_id].addMate(graphics_p1.getData(), rom_id, graphics_p2.getData())
                continue

            # print(f'connecting {graphics_p1} and {graphics_p2} in {fam1_id}')
            TreeView.MasterFamilies[fam1_id].addMate(graphics_p2.getData(), rom_id, graphics_p1.getData())
            TreeView.MasterFamilies[fam2_id].addMate(graphics_p1.getData(), rom_id, graphics_p2.getData())



    def connect_db(self, database):
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
        fam_sizes = [(k, v.boundingRect()) for k,v in TreeView.MasterFamilies.items()]
        fam_sizes.sort(key=lambda x: x[1].width(), reverse=True)
        root_y = 0
        root_x = 0
        x_offset = 0
        count = 0
        for fam_id, size in fam_sizes:
            root_loc = qtc.QPoint(root_x, root_y)
            TreeView.MasterFamilies[fam_id].setPos(root_loc)
            x_offset = np.power(-1, count) * (abs(x_offset) + size.width()*(2/3))
            root_x = x_offset
            count += 1


    def updatePreferences(self):
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
            if val := pref_record.get('ruler_crown_size', None):
                if val != Character.CROWN_HEIGHT:
                #     for char in TreeView.CharacterList:
                #         if char.ruler:
                #             char.buildRulerPix()
                #             if FAMILY_FLAGS.DISPLAY_RULERS in TreeView.CURRENT_FAMILY_FLAGS:
                #                 char.showRuler(True)
                    Character.CROWN_HEIGHT = val         
            if val := pref_record.get('ruler_crown_img', None):
                pass
            if val := pref_record.get('char_img_width', None):
                PictureEditor.CHAR_IMAGE_WIDTH = val
            if val := pref_record.get('char_img_height', None):
                PictureEditor.CHAR_IMAGE_HEIGHT = val
            self.update_tree()



    def update_tree(self):
        self.scene.reset_scene()
        for fam_id, family in TreeView.MasterFamilies.items():
            if fam_id in TreeView.CURRENT_FAMILIES: #WARNING: not good place for constant
                family.set_grid()  
                family.build_tree()
                if family not in self.scene.current_families:
                    # family.initFirstGen()
                    family.setParent(self)
                    # self.addedChars.emit([char.getID() for char in family.getAllMembers()])
                    family.initFirstGen()
                    self.scene.add_family_to_scene(family)
            else:
                if family in self.scene.current_families:
                    # self.removedChars.emit([char.getID() for char in family.getAllMembers()])
                    self.scene.remove_family_from_scene(family) 
                    family.setParent(None)
        self.scene.update()
        self.viewport().update()
        # self.fitWithBorder()

        # for char in TreeView.CharacterList:
        #     print(char)


    
        

    
    def toggle_char_selecting(self):
        self.selecting_char = False
        self.temp_statusbar_msg.emit('', 100) # temporary way to clear message
    
    def toggle_panning(self, state):
        self._pan = state
        self._pan_act = state
        self._mousePressed = False
        if self._pan:
            self.viewport().setCursor(qtc.Qt.OpenHandCursor)
        else:
            self.viewport().unsetCursor()
    
    @qtc.pyqtSlot()
    def check_character_dlt_btn(self):
        if not self.char_views:
            self.setCharDel.emit(False)
            CharacterView.CURRENT_SPAWN = qtc.QPoint(20, 50) # NOTE: Magic Number
        else:
            self.setCharDel.emit(True)
    

    ## Custom Slots ##

    @qtc.pyqtSlot(list)
    def updateChars(self, char_list):
        for char_id in char_list:
            char_record = self.character_db.get(where('char_id') == char_id)
            char_occurences = TreeView.CharacterList.search(char_id)
            for char in char_occurences:
                char.parseDict(char_record)
                char_view = self.findChild(CharacterView, 'view{}'.format(char_id))
                if char_view:
                    char_view.updateView()


    @qtc.pyqtSlot(dict)
    def receiveCharacterUpdate(self, char_dict):
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
            char_occurences = TreeView.CharacterList.search(formatted_dict['char_id'])
            for char in char_occurences:
                char.parseDict(formatted_dict)
                char_view = self.findChild(CharacterView, 'view{}'.format(formatted_dict['char_id']))
                if char_view:
                    char_view.updateView()


    @qtc.pyqtSlot()
    def character_selected(self):
        if not self.selecting_char:
            if self.last_mouse == 'Single':
                if len(self.scene.selectedItems()) > 0: # at least one character selected
                    selected_item = self.scene.selectedItems()[0] # NOTE: only using "first" item
                    if isinstance(selected_item, Character):
                        self.add_character_view(selected_item.getID())

            elif self.last_mouse == 'Double':
                if len(self.scene.selectedItems()) > 0: # at least one character selected
                    selected_item = self.scene.selectedItems()[0] # NOTE: only using "first" item
                    if isinstance(selected_item, Character):
                        self.add_character_edit(selected_item.getID())
    
    # @qtc.pyqtSlot(dict, qtc.QPointF)
    def inspect_selection(self, point):
        self.toggle_char_selecting()
        if point:
            selection = self.itemAt(point)
            if not selection and self.scene.sceneRect().contains(point):
                selection = self.mapToScene(point)
            self.selected_char = selection


    def requestCharacter(self, msg_prompt): # Wait for user to select a character
        self.selecting_char = True
        self.selected_char = None
        print(msg_prompt)
        
        # AutoCloseMessageBox.showWithTimeout(3, msg_prompt)
        prompt = CustomMsgBox(msg_prompt)
        prompt.move(self.width()/2, 0)
        self.scene_clicked.connect(prompt.close)
        prompt.show()
        
        self.temp_statusbar_msg.emit(f'{msg_prompt}...', self.char_selection_timeout)
        loop = qtc.QEventLoop()
        self.scene_clicked.connect(loop.quit)
        self.scene_clicked.connect(self.inspect_selection)
        timer = qtc.QTimer()
        timer.singleShot(self.char_selection_timeout, loop.quit)
        loop.exec()
        return self.selected_char

        

    @qtc.pyqtSlot(dict, Character)
    @qtc.pyqtSlot(dict, uuid.UUID)
    def add_new_character(self, char_dict, char_type, parent=None):
        added_partner = False
        if char_type == CHAR_TYPE.DESCENDANT:
            if isinstance(parent, uuid.UUID):
                parent_id = parent

            # elif isinstance(parent, list): # assume to be selectionList
            #     existing_char = parent[0] # get first character
            elif isinstance(parent, Character):
                # parent_char = parent
                parent_id = parent.getID()
            elif not parent:
                parent = self.requestCharacter('Please select a parent')
                if isinstance(parent, Character):
                    parent_id = parent.getID()
                elif isinstance(parent, qtc.QPointF):
                    self.add_new_family([char_dict], fam_type=FAM_TYPE.NULL_TERM, root_pt=parent)
                    return # Parent selection timeout, empty list returned
                else:
                    return
            
            parent_dict = self.character_db.get(where('char_id') == parent_id)
            parent_char_instances = TreeView.CharacterList.search(parent_id)
            parent_ids = []
            for instance in parent_char_instances:
                parent_ids.append(instance.getTreeID())

            fam_id = parent_dict['fam_id']
            other_parent_dict = None
            other_parent_ids = []
            # Add to relationship families (if exists)
            if parent_dict['partnerships']:
                if len(parent_dict['partnerships']) > 1:
                    # Need to launch dialog to select which relationship to place the desc. (or discern based on selection)
                    # print("Currently Unsupported")
                    return
                else:
                    fam_id = parent_dict['partnerships'][0]['rom_id']
                    if parent_dict['partnerships'][0]['p_id'] != self.meta_db.all()[0]['NULL_ID']:
                        other_parent_dict = self.character_db.get(where('char_id') == parent_dict['partnerships'][0]['p_id'])
                        char_dict['parent_1'] = other_parent_dict['char_id']

                        other_parent_instances = TreeView.CharacterList.search(other_parent_dict['char_id'])
                        for instance in other_parent_instances:
                            other_parent_ids.append(instance.getTreeID())

            char_dict['fam_id'] = fam_id
            char_dict['parent_0'] = parent_dict['char_id']

            kingdom_id = self.get_kingdom(kingdom_name=char_dict['kingdom'])
            formatted_dict = self.entry_formatter.char_entry(char_dict, kingdom_id=kingdom_id)
            
            fam_record = self.families_db.get(where('fam_id') == fam_id)
            if not fam_record:
                first_gen = [parent_dict]
                if other_parent_dict:
                    first_gen.append(other_parent_dict)
                if not self.add_new_family(first_gen, fam_id=fam_id):
                    return
                # added_partner = True
                
            # if added_partner:
            #     new_char = TreeView.CharacterList.search(formatted_dict['char_id'])[0]
            # else:
            new_char = Character(formatted_dict)
            new_char.setParentID(formatted_dict['parent_0'])
            if other_parent_ids:
                formatted_dict['parent_1'] = other_parent_dict['char_id']
                new_char.setParentID(formatted_dict['parent_1'], 1)
            
            instance_ids = set(parent_ids + other_parent_ids)
            instance_ids.add(fam_id)
            for f_id in instance_ids:
                if other_parent_dict:
                    if f_id == other_parent_dict['fam_id']:
                        TreeView.MasterFamilies[f_id].addChild(new_char, other_parent_dict['char_id'])
                        TreeView.MasterFamilies[f_id].addChildRelationship(new_char, parent_dict['char_id'])
                    else:
                        TreeView.MasterFamilies[f_id].addChild(new_char, parent_dict['char_id'])
                        TreeView.MasterFamilies[f_id].addChildRelationship(new_char, other_parent_dict['char_id'])

                else:
                    TreeView.MasterFamilies[f_id].addChild(new_char, parent_dict['char_id'])
                    # TreeView.MasterFamilies[f_id].addChild(new_char,
                new_char.setTreeID(f_id)
                TreeView.CharacterList.add(new_char)
                # CREATE CLONE
                new_char = Character(new_char.toDict())
            

        elif char_type == CHAR_TYPE.PARTNER:
            if isinstance(parent, uuid.UUID):
                existing_char = TreeView.CharacterList.search(parent)[0]
            elif isinstance(parent, list): # assume to be selectionList
                existing_char = parent[0] # get first character
            elif isinstance(parent, Character):
                existing_char = parent
            elif not parent:
                partner = self.requestCharacter('Please select a partner')
                if isinstance(partner, Character):
                    existing_char = partner
                else:
                    return
            existing_dict = self.character_db.get(where('char_id') == existing_char.getID())
            
            fam_name = char_dict['family']
            kingdom_id = self.get_kingdom(kingdom_name=char_dict['kingdom'])
            formatted_dict = self.entry_formatter.char_entry(char_dict, kingdom_id=kingdom_id)
            
            rom_id = None
            if existing_dict['parent_0'] == self.meta_db.all()[0]['NULL_ID']:
                if not formatted_dict['parent_0']:
                    formatted_dict['parent_0'] = self.meta_db.all()[0]['NULL_ID']
                    rom_id = existing_dict['fam_id']

            romance_entry = self.entry_formatter.partnership_entry(existing_dict['char_id'], rom_id)
            formatted_dict['partnerships'] = [romance_entry]
            existing_dict['partnerships'].append({'rom_id': romance_entry['rom_id'], 'p_id': formatted_dict['char_id']})
            
            # NOTE: set family to NULL if not entered in CharacterCreator
            parent = None
            if not fam_name:
                create_fam_prompt = qtw.QMessageBox(qtw.QMessageBox.Question, "Create family?", 
                            "Would you like to create a family for the new partner?",
                            qtw.QMessageBox.Yes | qtw.QMessageBox.No, self)
                prompt_font = qtg.QFont('Didot', 20)
                create_fam_prompt.setFont(prompt_font)
                response = create_fam_prompt.exec()
                if response == qtw.QMessageBox.Yes:
                    self.add_new_family([formatted_dict, existing_dict], fam_type=FAM_TYPE.NULL_TERM)
                    added_partner = True
                else:
                    formatted_dict['fam_id'] = self.meta_db.all()[0]['NULL_ID']
                    formatted_dict['parent_0'] = self.meta_db.all()[0]['NULL_ID']
            else:
                fam_id = self.get_family(fam_name=fam_name)
                if fam_id:
                    formatted_dict['fam_id'] = fam_id
                    parent = self.requestCharacter('Please select a parent')
                    if not isinstance(parent, Character):
                        print("No parent selected!")
                        return
                    formatted_dict['parent_0'] = parent.getID()
                else:
                    self.add_new_family([formatted_dict, existing_dict], fam_name)
                    added_partner = True

            if added_partner:
                new_char = TreeView.CharacterList.search(formatted_dict['char_id'])[0]
                new_char_fam = self.character_db.get(where('char_id') == new_char.getID())
                new_char_fam = new_char_fam['fam_id']
            else:
                new_char = Character(formatted_dict)
                new_char_fam = formatted_dict['fam_id']
            # new_char.setTreeID(existing_dict['fam_id'])
            if parent:
                new_char.setParent(0, parent.getID())
            
            
            for instance in TreeView.CharacterList.search(existing_char.getID()):
                # if formatted_dict['fam_id'] not in TreeView.MasterFamilies.keys():
                fam_id = instance.getTreeID()
                if fam_id == existing_dict['fam_id']:
                    if not added_partner:
                        TreeView.MasterFamilies[fam_id].addMateNoClone(new_char, romance_entry['rom_id'], existing_char)
                    else:
                        # MAKE CLONE
                        new_char = TreeView.MasterFamilies[fam_id].addMate(new_char, romance_entry['rom_id'], existing_char)
                    # TreeView.MasterFamilies[fam_id].addMateNoClone(existing_char, romance_entry['rom_id'], new_char)
                    TreeView.CharacterList.add(new_char)

                elif fam_id == new_char_fam:
                    continue

                else:
                # instance_ids.append(instance.getTreeID())
                    mate = TreeView.MasterFamilies[fam_id].addMate(new_char, romance_entry['rom_id'], instance)
                    TreeView.CharacterList.add(mate)
                
            if FAMILY_FLAGS.INCLUDE_PARTNERS not in self.CURRENT_FAMILY_FLAGS:
                self.requestFilterChange.emit(FAMILY_FLAGS.BASE, FAMILY_FLAGS.INCLUDE_PARTNERS)
            else:
                self.CURRENT_FAMILY_FLAGS.remove(FAMILY_FLAGS.INCLUDE_PARTNERS)
                self.filter_tree(FAMILY_FLAGS.BASE, FAMILY_FLAGS.INCLUDE_PARTNERS)
        else:
            print('Unknown character type...')
            return

        # print()
        # for char in TreeView.CharacterList:
        #     print(char, char.getTreeID())

        # Apply current flags
        if FAMILY_FLAGS.DISPLAY_RULERS in self.CURRENT_FAMILY_FLAGS:
            for char in TreeView.CharacterList.search(formatted_dict['char_id']):
                char.setRulerDisplay(True)              
        else:
            for char in TreeView.CharacterList.search(formatted_dict['char_id']):
                char.setRulerDisplay(False)              


        if TreeView.TREE_DISPLAY == TREE_ICON_DISPLAY.IMAGE:
            for char in TreeView.CharacterList.search(formatted_dict['char_id']):
                char.setDisplayMode(TREE_ICON_DISPLAY.IMAGE)              

        elif TreeView.TREE_DISPLAY == TREE_ICON_DISPLAY.NAME:
            for char in TreeView.CharacterList.search(formatted_dict['char_id']):
                char.setDisplayMode(TREE_ICON_DISPLAY.NAME)
        self.scene.update()


        # enter character into db
        if not added_partner:
            self.character_db.insert(formatted_dict)
            self.addedChars.emit([new_char.getID()])
        # if char_type != CHAR_TYPE.PARTNER:
        self.update_tree()
    
    
    def add_new_family(self, first_gen, fam_name=None, fam_id=None, fam_type=FAM_TYPE.SUBSET, root_pt=None):    
        if not fam_name:
            if isinstance(first_gen[0], dict):
                fam_name = first_gen[0].get('family', None)
                if not fam_name:
                    # fam_name, ok = qtw.QInputDialog.getText(self, "New Family", "Enter a family name:")
                    fam_name, ok = UserLineInput.requestInput("New Family", "Enter a family name:", self)
                    if not ok:
                        return False
        if not root_pt:
            root_pt = self.mapToScene(self.viewport().rect().center())
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
                    TreeView.CharacterList.add(new_char)

                else:
                    formatted_dict['fam_id'] = fam_id
                    if not formatted_dict['parent_0']:
                        formatted_dict['parent_0'] = self.meta_db.all()[0]['NULL_ID']
                    
                    self.character_db.insert(formatted_dict)
                    new_char = Character(formatted_dict)
                    TreeView.CharacterList.add(new_char)
                    self.addedChars.emit([new_char.getID()])
                
                new_char.setTreeID(fam_id)                
                family_heads.append(new_char)
        
        # if fam_type == FAM_TYPE.NULL_TERM:
        #     family_heads[0].
               
        new_family = Family(first_gen=family_heads, family_id=fam_id, family_type=fam_type, family_name=fam_name, pos=root_pt)
        TreeView.MasterFamilies[fam_id] = new_family
        self.CURRENT_FAMILIES.add(fam_id)
        CharacterCreator.FAMILY_ITEMS.insert(-1, fam_name)

        # Connect signals
        new_family.setParent(self)
        new_family.edit_char.connect(self.add_character_edit)
        new_family.add_descendant.connect(lambda x: self.createCharacter(CHAR_TYPE.DESCENDANT, x))
        new_family.remove_character.connect(self.remove_character)
        new_family.delete_fam.connect(self.delete_family)
        new_family.add_partner.connect(self.createPartnership)
        new_family.add_parent.connect(self.addParent)
        new_family.remove_partnership.connect(self.divorceProctor)

        self.scene.add_family_to_scene(new_family)
        new_family.set_grid()
        new_family.build_tree()
        
        # Apply current flags
        if FAMILY_FLAGS.CONNECT_PARTNERS in self.CURRENT_FAMILY_FLAGS:
            family_head = self.character_db.get(where('char_id') == family_heads[0].getID())
            self.previous_families.add(new_family.getID())
            if family_head['parent_0'] in TreeView.CharacterList:
                self.CURRENT_FAMILIES.remove(new_family.getID())
            else:
                new_family.explodeFamily(True)
        
        if FAMILY_FLAGS.DISPLAY_FAM_NAMES in self.CURRENT_FAMILY_FLAGS:
            new_family.setNameDisplay(False)
        else:
            new_family.setNameDisplay(True)
        
        if FAMILY_FLAGS.INCLUDE_PARTNERS in self.CURRENT_FAMILY_FLAGS:
            new_family.includeFirstGen(True)
        else:
            new_family.includeFirstGen(False)

        self.families_added.emit(SELECTIONS_UPDATE.ADDED_FAM, [fam_entry])
        return True


    def get_kingdom(self, kingdom_name=None, kingdom_id=None):
        if kingdom_name:
            kingdom_record = self.kingdoms_db.get(where('kingdom_name') == kingdom_name)
            if not kingdom_record:
                print('PROBLEM: unrecognized kingdom, make new??')
            else:
                return kingdom_record['kingdom_id']
        elif kingdom_id:
            kingdom_record = self.kingdoms_db.get(where('kingdom_id') == kingdom_id)
            if not kingdom_record:
                print('PROBLEM: unrecognized kingdom, make new??')
            else:
                return kingdom_record['kingdom_name']
        else:
            return self.kingdoms_db.get(where('kingdom_name') == 'None')


    def get_family(self, fam_name=None, fam_id=None):
        if fam_name:
            fam_record = self.families_db.get(where('fam_name') == fam_name)
            if not fam_record:
                print('PROBLEM: unrecognized family, make new??')
            else:
                return fam_record['fam_id']
        elif fam_id:
            fam_record = self.families_db.get(where('fam_id') == fam_id)
            if not fam_record:
                print('PROBLEM: unrecognized family, make new??')
            else:
                return fam_record['fam_name']
        else:
            return self.families_db.get(where('fam_name') == 'None')
    

    @qtc.pyqtSlot()
    def createFamily(self, parent=None):
        # name, ok = qtw.QInputDialog.getText(self, "New Family", "Enter a family name:")
        name, ok = UserLineInput.requestInput("New Family", "Enter a family name:", self)
        if ok:
            CharacterCreator.FAMILY_ITEMS.append(name)
            self.new_char_dialog = CharacterCreator(self)
            self.new_char_dialog.family_select.setCurrentText(name)
            self.new_char_dialog.submitted.connect(lambda d: self.add_new_family([d], name, fam_type=FAM_TYPE.ENDPOINT))
            self.new_char_dialog.show()
        else:
            return

    @qtc.pyqtSlot(uuid.UUID)
    def createPartnership(self, char_id):
        self.selection_window = PartnerSelect()
        self.selection_window.new_char.clicked.connect(lambda: self.createCharacter(CHAR_TYPE.PARTNER, char_id))
        self.selection_window.char_select.clicked.connect(lambda: self.matchMaker(char_id))
        self.selection_window.show()


    def matchMaker(self, char_1_id, char_2=None):
        if not char_2:
            char_2 = self.requestCharacter("Please select a partner")
            if not isinstance(char_2, Character):
                return
        char_1 = TreeView.CharacterList.search(char_1_id)
        if not char_1:
            return
        char_1 = char_1[0]

        if char_1_id == char_2.getID():
            print("Can't be your own partner!")
            return
        
        char_1_record = self.character_db.get(where('char_id') == char_1_id)
        char_2_record = self.character_db.get(where('char_id') == char_2.getID())

        # if len(char_1_record['partnerships']) > 1:
        #     print()
        
        fam_1_ids = []
        for instance in TreeView.CharacterList.search(char_1_id):
            # print(instance.getName(), instance.getID(), instance.getTreeID())
            fam_1_ids.append(instance.getTreeID())

        fam_2_ids = []
        for instance in TreeView.CharacterList.search(char_2.getID()):
            # print(instance.getName(), instance.getID(), instance.getTreeID())
            fam_2_ids.append(instance.getTreeID())

        rom_id = None
        if char_1_record['partnerships']:
            if len(char_1_record['partnerships']) == 1:
                if char_1_record['partnerships'][0]['p_id'] == self.meta_db.all()[0]['NULL_ID']:
                    rom_id = char_1_record['partnerships'][0]['rom_id']
                    self.character_db.update({'partnerships': []}, where('char_id') == char_1_record['char_id'])
                else:
                    print("Replacing partners is not currently supported")
                    return
            else:
                print('Currently can only have one partner at a time.')
                return

        if char_2_record['partnerships']:
            if len(char_2_record['partnerships']) == 1:
                if char_2_record['partnerships'][0]['p_id'] == self.meta_db.all()[0]['NULL_ID']:
                    if rom_id:
                        print("Can't currently combine two divorced families")
                        return
                    rom_id = char_2_record['partnerships'][0]['rom_id']
                    self.character_db.update({'partnerships': []}, where('char_id') == char_2_record['char_id'])
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
                TreeView.CharacterList.add(mate)
            except:
                pass
        for fam_id in fam_2_ids:
            try:
                mate = self.MasterFamilies[fam_id].addMate(char_1, rom_id, char_2)
                TreeView.CharacterList.add(mate)
            except:
                pass
        
        char_1_relationships = char_1_record['partnerships'] + [char_1_entry]
        self.character_db.update({'partnerships': char_1_relationships}, where('char_id') == char_1.getID())
        char_2_relationships = char_2_record['partnerships'] + [char_2_entry]
        self.character_db.update({'partnerships': char_2_relationships }, where('char_id') == char_2.getID())
        self.update_tree()


    @qtc.pyqtSlot(uuid.UUID)
    @qtc.pyqtSlot(uuid.UUID, uuid.UUID)
    def divorceProctor(self, char1_id, char2_id=None):
        char_record = self.character_db.get(where('char_id') == char1_id)
        if char2_id:
            partner_record = self.character_db.get(where('char_id') == char2_id)
        else:
            rom_record = char_record['partnerships']
            if not rom_record:
                self.temp_statusbar_msg.emit(f"No partners to remove!", 2000)
                return
            if len(rom_record) == 1:
                partnership = rom_record[0]
                partner_record = self.character_db.get(where('char_id') == partnership['p_id'])
                if char_record['fam_id'] in TreeView.MasterFamilies.keys():
                    TreeView.MasterFamilies[char_record['fam_id']].removePartnership(char_record['char_id'], partner_record['char_id'])
                    char_instances = TreeView.CharacterList.search(partner_record['char_id'])
                    for i in char_instances:
                        if i.getTreeID() == char_record['fam_id']:
                            TreeView.CharacterList.remove(i)
                            break
                
                if partner_record['fam_id'] in TreeView.MasterFamilies.keys():
                    TreeView.MasterFamilies[partner_record['fam_id']].removePartnership(partner_record['char_id'], char_record['char_id'])
                    char_instances = TreeView.CharacterList.search(char_record['char_id'])
                    for i in char_instances:
                        if i.getTreeID() == partner_record['fam_id']:
                            TreeView.CharacterList.remove(i)
                            break
                
                if partnership['rom_id'] in TreeView.MasterFamilies.keys():
                    TreeView.MasterFamilies[partnership['rom_id']].splitFirstGen(char_record['char_id'], partner_record['char_id'])
                    char_instances = TreeView.CharacterList.search(partner_record['char_id'])
                    for i in char_instances:
                        if i.getTreeID() == partnership['rom_id']:
                            TreeView.CharacterList.remove(i)
                            break
            else:
                self.temp_statusbar_msg.emit(f"In construction", 2000)
                return
        
        fam_divorce = False
        for fam in TreeView.MasterFamilies.values():
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
        

    @qtc.pyqtSlot(uuid.UUID)
    def addParent(self, char_id):
        self.selection_window = ParentSelect()
        self.build_char = CharacterCreator(self)
        self.build_char.submitted.connect(lambda d: self.buildParent(d, char_id))
        self.selection_window.new_char.clicked.connect(self.build_char.show)
        self.selection_window.char_select.clicked.connect(lambda: print("In Construction!"))
        self.selection_window.show()

    @qtc.pyqtSlot(dict, uuid.UUID)
    def buildParent(self, parent_dict, child_id):
        existing_dict = self.character_db.get(where('char_id') == child_id)
        parent_dict['fam_id'] = existing_dict['fam_id']
        parent_dict['parent_0'] = existing_dict['parent_0']
        parent_dict['parent_1'] = existing_dict['parent_1']
        kingdom_id = self.get_kingdom(kingdom_name=parent_dict['kingdom'])
        formatted_dict = self.entry_formatter.char_entry(parent_dict, kingdom_id=kingdom_id)

        # update to-be child
        existing_dict['parent_0'] = formatted_dict['char_id']
        existing_dict['parent_1'] = None # WARNING: not sure if i like this...
        updated_dict = {**self.character_db.get(where('char_id') == child_id), **existing_dict}
        update = self.character_db.update(updated_dict, where('char_id') == child_id)
        new_char = Character(formatted_dict)

        for instance in TreeView.CharacterList.search(updated_dict['char_id']):
            fam_id = instance.getTreeID()
            if fam_id == updated_dict['fam_id']:
                TreeView.MasterFamilies[fam_id].addParent(new_char, updated_dict['char_id'])
            elif updated_dict['partnerships']:
                if fam_id == updated_dict['partnerships'][0]['rom_id']:
                    TreeView.MasterFamilies[fam_id].addParent(new_char, updated_dict['char_id'])
            TreeView.CharacterList.add(new_char)
            # MAKE CLONE
            new_char = Character(new_char.toDict())
    
        self.character_db.insert(formatted_dict)
        self.addedChars.emit([new_char.getID()])

        self.update_tree()
    

    @qtc.pyqtSlot()
    @qtc.pyqtSlot(uuid.UUID)
    def createCharacter(self, char_type=None, parent=None):
        # print(f'Creator called with {char_type}, {parent}')
        if not char_type:
            char_type = CharacterTypeSelect.requestType()
        if not char_type:
            return
        self.new_char_dialog = CharacterCreator(self)
        self.new_char_dialog.submitted.connect(lambda d: self.add_new_character(d, char_type, parent))
        self.new_char_dialog.show()
    
    @qtc.pyqtSlot()
    def delete_active_character(self):
        if self.scene.selectedItems():
            char = self.scene.selectedItems()[0]
            char_id = char.getID()
            
        elif self.char_views:
            char = self.char_views[-1]
            char_id = uuid.UUID(char.objectName()[4:])
        else: # No active character
            return
        fam_id = self.character_db.get(where('char_id') == char_id)['fam_id']
        if fam_id not in self.MasterFamilies.keys():
            fam_id = self.character_db.get(where('char_id') == char_id)['partnerships'][0]['rom_id']
        # TreeView.MasterFamilies[fam_id].delete_character(char_id)
        for _id, fam in TreeView.MasterFamilies.items():
            fam.delete_character(char_id)

    @qtc.pyqtSlot(uuid.UUID)
    def remove_character(self, char_id):
        char_removal = True
        partner_removal = False
        first_gen = False
        char_instances = tuple(TreeView.CharacterList.search(char_id))
        for instance in char_instances:
            # print(f'{instance.getTreeID()} --> {instance.getName()}')
            first_gen |= (instance is TreeView.MasterFamilies[instance.getTreeID()].getFirstGen()[0])
            char_removed, partner_removed = TreeView.MasterFamilies[instance.getTreeID()].delete_character(char_id)
            if char_removed:
                TreeView.CharacterList.remove(instance)
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
            print(f"Removed {char_dict['name']} from tree")
            self.temp_statusbar_msg.emit(f"Removed {char_dict['name']}", 2000)
            self.removedChars.emit([char_id])
            self.character_db.remove(where('char_id') == char_id)

        self.update_tree()
    
    @qtc.pyqtSlot(uuid.UUID)
    def delete_family(self, fam_id):
        fam_entry = self.families_db.get(where('fam_id') == fam_id)
        fam_name = fam_entry['fam_name']
        # print(f"Deleting fam: {fam_id, fam_name}")
        delete_fam_prompt = qtw.QMessageBox(qtw.QMessageBox.Warning, "Delete family?", 
                            (f"Are you sure you would like to delete the" 
                            f"{fam_name} family?"),
                            qtw.QMessageBox.No | qtw.QMessageBox.Yes, self)
        delete_fam_prompt.setInformativeText('This action can not be undone.')
        prompt_font = qtg.QFont('Didot', 20)
        delete_fam_prompt.setFont(prompt_font)
        response = delete_fam_prompt.exec()
        if response != qtw.QMessageBox.Yes:
            return

        # fam_name = self.families_db.get(where('fam_id') == fam_id)['fam_name']
        self.temp_statusbar_msg.emit(f"Removed {fam_name}", 3000)
        if fam_id in self.CURRENT_FAMILIES:
            self.CURRENT_FAMILIES.remove(fam_id)
        fam = self.MasterFamilies[fam_id]
        self.scene.remove_family_from_scene(fam)
        for char in fam.getMembersAndPartners():
            if TreeView.CharacterList.search(char):
                for instance in TreeView.CharacterList.search(char):
                    if instance.getTreeID() == fam_id:
                        TreeView.CharacterList.remove(instance)
                        del instance
        del fam
        del self.MasterFamilies[fam_id]
        self.families_db.remove(where('fam_id') == fam_id)
        self.families_added.emit(SELECTIONS_UPDATE.REMOVED_FAM, [fam_entry])
    
    @qtc.pyqtSlot(uuid.UUID)
    @qtc.pyqtSlot(Character)
    def add_character_view(self, char_id):
        if char_id is not None:
            char_view = self.findChild(CharacterView, 'view{}'.format(char_id))
            if char_view is None:
                char = self.character_db.get(where('char_id') == char_id)
                fam_record = self.families_db.get(where('fam_id') == char['fam_id'])

                if not fam_record:
                    if char['partnerships']:
                        fam_record = self.families_db.get(where('fam_id') == char['partnerships'][0]['rom_id'])
                    else:
                        fam_record = {'fam_name': ''} # NOTE: Temporary 
                char['family'] = fam_record['fam_name']
                kingdom_record = self.kingdoms_db.get(where('kingdom_id') == char['kingdom_id'])
                if not kingdom_record:
                    char['kingdom'] = ''
                else:
                    char['kingdom'] = kingdom_record['kingdom_name']

                popup_view = CharacterView(char)
                popup_view.setParent(self)
                self.scene.addItem(popup_view)
                popup_view.setPos(self.mapToScene(CharacterView.CURRENT_SPAWN)) # NOTE: Magic numbers!
                popup_view.setZValue(2)
                CharacterView.CURRENT_SPAWN += qtc.QPoint(10, 10)
                popup_view.closed.connect(lambda : self.char_views.remove(popup_view))
                popup_view.closed.connect(self.check_character_dlt_btn)
                popup_view.closed.connect(self.scene.clearSelection)
                self.char_views.append(popup_view)
                self.scene.selectionChanged.connect(popup_view.check_selected)
                self.check_character_dlt_btn()
            else:
                char_view.setSelected(True)
                
    @qtc.pyqtSlot(uuid.UUID)
    def add_character_edit(self, char_id):
        selected_char = self.character_db.get(where('char_id') == char_id)
        if selected_char:
            fam_record = self.families_db.get(where('fam_id') == selected_char['fam_id'])
            if not fam_record:
                fam_record = self.families_db.get(where('fam_id') == selected_char['partnerships'][0]['rom_id'])
            selected_char['family'] = fam_record['fam_name']
            kingdom_record = self.kingdoms_db.get(where('kingdom_id') == selected_char['kingdom_id'])
            if kingdom_record:
                selected_char['kingdom'] = kingdom_record['kingdom_name']
            else:
                selected_char['kingdom'] = ''
            self.edit_window = CharacterCreator(self, selected_char)
            self.edit_window.submitted.connect(self.receiveCharacterUpdate)
            # self.edit_window.submitted.connect(lambda d: self.updatedChars.emit([d['char_id']]))
            self.edit_window.show()


    def filterKingdoms(self, kingdom_record, filter_state):
        filtered_chars = self.character_db.search(where('kingdom_id') == kingdom_record['kingdom_id'])
        if filtered_chars:
            if filter_state:
                for char in filtered_chars:
                    for graphic_char in TreeView.CharacterList.search(char['char_id']):
                        TreeView.MasterFamilies[graphic_char.getTreeID()].filtered.remove(graphic_char)
                        graphic_char.setParent(TreeView.MasterFamilies[graphic_char.getTreeID()])
                        graphic_char.setParentItem(TreeView.MasterFamilies[graphic_char.getTreeID()])
            else:
                for char in filtered_chars:
                    for graphic_char in TreeView.CharacterList.search(char['char_id']):
                        TreeView.MasterFamilies[graphic_char.getTreeID()].filtered.add(graphic_char)
                        self.scene.removeItem(graphic_char)
                        graphic_char.setParent(None)
                        graphic_char.setParentItem(None)
            self.scene.update()
            self.viewport().update()


    ## Auxiliary Functions ##
    @qtc.pyqtSlot(int, str)
    @qtc.pyqtSlot(int, int)
    def filter_tree(self, flag_type, flag):
        if flag_type == FAMILY_FLAGS.BASE:
            if flag == FAMILY_FLAGS.DISPLAY_RULERS:
                if FAMILY_FLAGS.DISPLAY_RULERS in self.CURRENT_FAMILY_FLAGS:
                    self.CURRENT_FAMILY_FLAGS.remove(FAMILY_FLAGS.DISPLAY_RULERS)
                    print("Showing rulers")
                    for family in self.MasterFamilies.values():
                        for char in family.getMembersAndPartners():
                            char.setRulerDisplay(True)              

                else:
                    self.CURRENT_FAMILY_FLAGS.add(FAMILY_FLAGS.DISPLAY_RULERS)
                    print("Hidding rulers")
                    for family in self.MasterFamilies.values():
                        for char in family.getMembersAndPartners():
                            char.setRulerDisplay(False)              
                self.scene.update()
            
            elif flag == FAMILY_FLAGS.DISPLAY_FAM_NAMES:
                if FAMILY_FLAGS.DISPLAY_FAM_NAMES in self.CURRENT_FAMILY_FLAGS:
                    self.CURRENT_FAMILY_FLAGS.remove(FAMILY_FLAGS.DISPLAY_FAM_NAMES)
                    print("Showing family names")
                    for family in self.MasterFamilies.values():
                        family.setNameDisplay(True)
                            
                else:
                    self.CURRENT_FAMILY_FLAGS.add(FAMILY_FLAGS.DISPLAY_FAM_NAMES)
                    print("Hiding family names")
                    for family in self.MasterFamilies.values():
                        family.setNameDisplay(False)
                self.scene.update()

            elif flag == FAMILY_FLAGS.INCLUDE_PARTNERS:
                if FAMILY_FLAGS.INCLUDE_PARTNERS in self.CURRENT_FAMILY_FLAGS:
                    self.CURRENT_FAMILY_FLAGS.remove(FAMILY_FLAGS.INCLUDE_PARTNERS)
                    print("Hidding partners")
                    for family in self.MasterFamilies.values():
                        family.includeFirstGen(False)

                else:
                    self.CURRENT_FAMILY_FLAGS.add(FAMILY_FLAGS.INCLUDE_PARTNERS)
                    print("Showing partners")
                    for family in self.MasterFamilies.values():
                        family.includeFirstGen(True)
                self.update_tree()

            elif flag == FAMILY_FLAGS.CONNECT_PARTNERS:
                if FAMILY_FLAGS.CONNECT_PARTNERS in self.CURRENT_FAMILY_FLAGS:
                    self.CURRENT_FAMILY_FLAGS.remove(FAMILY_FLAGS.CONNECT_PARTNERS)
                    print('Separating families')
                    for fam_id, family in self.MasterFamilies.items():
                        if fam_id in self.previous_families:
                            if fam_id in self.CURRENT_FAMILIES:
                                family.explodeFamily(False)
                            self.CURRENT_FAMILIES.add(fam_id)
                    
                else:
                    self.CURRENT_FAMILY_FLAGS.add(FAMILY_FLAGS.CONNECT_PARTNERS)
                    print('Connecting families')
                    self.previous_families = set(self.CURRENT_FAMILIES)
                    # termination_id = self.meta_db.all()[0]['TERM_ID']
                    for fam_id, family in self.MasterFamilies.items():
                        # family_head = self.character_db.get(where('char_id') == family.getFirstGen()[0].getID())
                        # char_instances = TreeView.CharacterList.search(family_head['char_id'])

                        # if (family_head['parent_0'] in TreeView.CharacterList or family_head['parent_1'] in TreeView.CharacterList) \
                        #     or family_head['parent_0'] != termination_id \
                        if family._term_type != FAM_TYPE.ENDPOINT and fam_id in self.previous_families:
                            self.CURRENT_FAMILIES.remove(family.getID())
                        else:
                            family.explodeFamily(True)
                    if FAMILY_FLAGS.INCLUDE_PARTNERS not in self.CURRENT_FAMILY_FLAGS:
                        self.requestFilterChange.emit(FAMILY_FLAGS.BASE, FAMILY_FLAGS.INCLUDE_PARTNERS)

                self.update_tree()


        elif flag_type == TREE_ICON_DISPLAY.BASE:
            if flag == TREE_ICON_DISPLAY.IMAGE:
                print('Showing as image')
                TreeView.TREE_DISPLAY = flag
                for char in TreeView.CharacterList:
                    char.setDisplayMode(TREE_ICON_DISPLAY.IMAGE)              

            elif flag == TREE_ICON_DISPLAY.NAME:
                print('Showing as name')
                TreeView.TREE_DISPLAY = flag
                for char in TreeView.CharacterList:
                    char.setDisplayMode(TREE_ICON_DISPLAY.NAME)
            self.scene.update()
        
        elif flag_type == GROUP_SELECTION_ITEM.FAMILY:
            family_record = self.families_db.get(where('fam_name') == flag)
            if family_record:
                family_id = family_record['fam_id']
                if family_id in self.CURRENT_FAMILIES:
                    self.CURRENT_FAMILIES.remove(family_id)
                    print(f'Removed family {flag}')
                elif FAMILY_FLAGS.CONNECT_PARTNERS not in self.CURRENT_FAMILY_FLAGS:
                    self.CURRENT_FAMILIES.add(family_id)
                    print(f'Added family {flag}')
                self.update_tree()
                
        
        elif flag_type == GROUP_SELECTION_ITEM.KINGDOM:
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
    

    

    ## Override Built-In Event Slots ##

    def resizeEvent(self, event):                
        self.fitWithBorder()
        super(TreeView, self).resizeEvent(event)

    def fitWithBorder(self):
        boundingRect = qtc.QRectF()
        if len(self.scene.current_families):
            for fam in self.scene.current_families:
                boundingRect = boundingRect.united(fam.sceneBoundingRect())
            boundingRect.adjust(-TreeScene.BORDER_X, -TreeScene.BORDER_Y, 
                                    TreeScene.BORDER_X, TreeScene.BORDER_Y)
            if boundingRect.width() < self.DFLT_VIEW.width():
                rect = qtc.QRectF()
                rect.setSize(self.DFLT_VIEW.size())
                rect.moveCenter(boundingRect.center())
                boundingRect = rect
                
        else:
            boundingRect = self.DFLT_VIEW
        self.fitInView(boundingRect, qtc.Qt.KeepAspectRatio)
        
        self.zoom_tracker = 0
        self.zoomStatus = 0
        self.zoomChanged.emit(0)

    # def wheelEvent(self, event):                  
    #     if event.angleDelta().y() > 0:
    #         direction = self.zoomStatus + 1
    #     else:
    #         direction = self.zoomStatus - 1
    #     self.zoomEvent(direction, event.pos())

    def zoomEvent(self, factor, center_pos=None):
        slider_zoom = False
        if not center_pos:
            slider_zoom = True
            center_pos = self.viewport().rect().center()
        zoomInFactor = 1.1
        zoomOutFactor = 1 / zoomInFactor
        self.setTransformationAnchor(qtw.QGraphicsView.NoAnchor)
        self.setResizeAnchor(qtw.QGraphicsView.NoAnchor)

        if factor > self.zoomStatus:
            zoomFactor = zoomInFactor
            self.zoom_tracker += 1
        else:
            zoomFactor = zoomOutFactor
            self.zoom_tracker -= 1
        self.zoomStatus = factor
        

        if TreeView.MIN_ZOOM > self.zoom_tracker:
            self.zoom_tracker = TreeView.MIN_ZOOM
            return
        elif TreeView.MAX_ZOOM < self.zoom_tracker:
            self.zoom_tracker = TreeView.MAX_ZOOM
            return

        if not slider_zoom:
            self.zoomChanged.emit(self.zoom_tracker)

        oldPos = self.mapToScene(center_pos)
        self.scale(zoomFactor, zoomFactor)
        # self.scale(factor, factor)
        newPos = self.mapToScene(center_pos)
        delta = newPos - oldPos
        self.translate(delta.x(), delta.y())

        
    def mousePressEvent(self, event):
        if self.selecting_char and event.button() == qtc.Qt.LeftButton:
            self.scene_clicked.emit(event.pos())
            return
        
        self.last_mouse = 'Single'
        if event.button()  == qtc.Qt.LeftButton: 
            self._mousePressed = True
        
        if self._pan: 
            # self._pan = True
            # self._mousePressed = True
            self._panStartX = event.x()
            self._panStartY = event.y()
            self.viewport().setCursor(qtc.Qt.ClosedHandCursor)
            # event.accept()
        super(TreeView, self).mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self._mousePressed = False
        if self._pan: 
            self.viewport().setCursor(qtc.Qt.OpenHandCursor)

            # event.accept()
        if self.last_mouse == "Single":
            qtc.QTimer.singleShot(qtw.QApplication.instance().doubleClickInterval(), 
                            self.character_selected)
        super(TreeView, self).mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        self.last_mouse = 'Double'
        super(TreeView, self).mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        if self._mousePressed:
            self.last_mouse = 'Move'
            if self._pan:
                self.viewport().setCursor(qtc.Qt.ClosedHandCursor)
                self.horizontalScrollBar().setValue(
                    self.horizontalScrollBar().value() - (event.x() - self._panStartX))
                self.verticalScrollBar().setValue(
                    self.verticalScrollBar().value() - (event.y() - self._panStartY))
                self._panStartX = event.x()
                self._panStartY = event.y()
                event.accept()
        super(TreeView, self).mouseMoveEvent(event)

    ## Gestures

    def viewportEvent(self, event):
        if event.type() == qtc.QEvent.Gesture:
            return self.gestureEvent(event)
        elif event.type() == qtc.QEvent.GestureOverride:
            event.accept()
        return super(TreeView, self).viewportEvent(event)

 
    def gestureEvent(self, event):
        if swipe := event.gesture(qtc.Qt.PinchGesture):
            if swipe.totalScaleFactor() != 1:
                # print('Pinching!')
                flags = swipe.changeFlags()
                if flags & qtw.QPinchGesture.ScaleFactorChanged:
                    self.current_factor = swipe.totalScaleFactor()

                if swipe.state() == qtc.Qt.GestureFinished:
                    self.zoom_factor *= self.current_factor
                    self.current_factor = 1
                    return True
                
                scale_factor = self.zoom_factor * self.current_factor
                self.zoomEvent(scale_factor, swipe.centerPoint().toPoint())

        return True


    
    def keyPressEvent(self, event):
        if event.key() == qtc.Qt.Key_Escape:        # Escape key shortcuts
            if self.scene.selectedItems():
                item = self.scene.selectedItems()[0]
                if isinstance(item, Character):
                    child = self.findChild(CharacterView, 'view{}'.format(item.getID()))
                    if child is not None:
                        child.close()
                    self.scene.clearSelection()
                elif isinstance(item, CharacterView):
                    item.close()
            elif self.scene.focusItem():
                item = self.scene.focusItem()
                if isinstance(item, CharacterView):
                    item.close()
            elif self.char_views:
                view = self.char_views[-1]
                view.close()

        super(TreeView, self).keyPressEvent(event)
    

    
            

# Create Tree scene 
class TreeScene(qtw.QGraphicsScene):
    
    LINE_WIDTH = 2.5
    SCENE_WIDTH = 8000
    SCENE_HEIGHT = 8000
    BORDER_X = 50
    BORDER_Y = 40

    # Custom signals
    add_descendants = qtc.pyqtSignal(uuid.UUID)
    remove_char = qtc.pyqtSignal(uuid.UUID)
    # edit_char = qtc.pyqtSignal(uuid.UUID)
    

    def __init__(self, parent=None):
        super(TreeScene, self).__init__(parent)
        bg_pix = qtg.QPixmap(':/background-images/scene_bg_2.png')
        bg_pix = bg_pix.scaled(self.SCENE_WIDTH, self.SCENE_HEIGHT, 
                                        qtc.Qt.KeepAspectRatioByExpanding)
        self.SCENE_WIDTH = bg_pix.width()
        self.SCENE_HEIGHT = bg_pix.height()
        self.setSceneRect(0, 0, self.SCENE_WIDTH, self.SCENE_HEIGHT)
        self.setItemIndexMethod(qtw.QGraphicsScene.NoIndex)
        self.current_families = []
        self.linePen = qtg.QPen(qtg.QColor('black'), self.LINE_WIDTH)
        self.bg = qtw.QGraphicsPixmapItem(bg_pix)
        self.bg.setPos(0, 0)
        self.addItem(self.bg)
        
    ## Custom Slots ##

    @qtc.pyqtSlot()
    def reset_scene(self):
        self.clearSelection()
        for fam in self.current_families:
            fam.reset_family()
        self.clearFocus()
    
    ## Auxiliary Methods ##
    
    def add_family_to_scene(self, fam):
        if fam not in self.current_families:
            # print(f'Adding {fam}')
            fam.setZValue(1)
            self.addItem(fam)
            self.current_families.append(fam)
            fam.installFilters()
        
    def remove_family_from_scene(self, fam):
        if fam in self.current_families:
            # print(f'Removing: {fam}')
            # fam.prepareGeometryChange()
            self.current_families.remove(fam)
            self.removeItem(fam)
    
    # def event(self, event):
    #     if event.type() == qtc.QEvent.Gesture:
    #         return self.gestureEvent(event)
    #     if event.type() == qtc.QEvent.GestureOverride:
    #         event.accept()
    #     return super(TreeScene, self).event(event)
 
    # def gestureEvent(self, event):
    #     if swipe := event.gesture(qtc.Qt.PanGesture):
    #         print('Panning!')
        
    #     elif swipe := event.gesture(qtc.Qt.PinchGesture):
    #         print('Pinching!')
        
    #     return True
            
        

class PartnerSelect(qtw.QDialog):

    selection_made = qtc.pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super(PartnerSelect, self).__init__(parent)
        layout = qtw.QGridLayout()
        font = qtg.QFont('Didot', 28)
        self.title = qtw.QLabel("Please choose who the new partner will be.")
        self.title.setFont(font)

        font = qtg.QFont('Didot', 20)
        self.new_char = qtw.QPushButton("New Character")
        self.new_char.setFont(font)
        self.new_char.clicked.connect(self.close)

        self.char_select = qtw.QPushButton("Select Existing")
        self.char_select.setFont(font)
        self.char_select.clicked.connect(self.close)

        layout.addWidget(self.title, 1, 0, 1, 3)
        layout.addWidget(self.new_char, 2, 0, 1, 1)
        layout.addWidget(self.char_select, 2, 2, 1, 1)
        self.setLayout(layout)
        self.setSizePolicy(qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Preferred)
        # self.setFixedSize(325, 100)
        self.setWindowTitle('Partner Creation Type')
    
class ParentSelect(qtw.QDialog):

    selection_made = qtc.pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super(ParentSelect, self).__init__(parent)
        layout = qtw.QGridLayout()
        font = qtg.QFont('Didot', 28)
        self.title = qtw.QLabel("Please choose who the new parent will be.")
        self.title.setFont(font)

        font = qtg.QFont('Didot', 20)
        self.new_char = qtw.QPushButton("New Character")
        self.new_char.setFont(font)
        self.new_char.clicked.connect(self.close)

        self.char_select = qtw.QPushButton("Select Existing")
        self.char_select.setFont(font)
        self.char_select.clicked.connect(self.close)

        layout.addWidget(self.title, 1, 0, 1, 3)
        layout.addWidget(self.new_char, 2, 0, 1, 1)
        layout.addWidget(self.char_select, 2, 2, 1, 1)
        self.setLayout(layout)
        self.setSizePolicy(qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Preferred)
        # self.setFixedSize(325, 100)
        self.setWindowTitle('Parent Creation Type')
    

class CharacterTypeSelect(qtw.QDialog):

    def __init__(self, parent=None):
        super(CharacterTypeSelect, self).__init__(parent)
        layout = qtw.QGridLayout()
        font = qtg.QFont('Didot', 24)
        self.title = qtw.QLabel("Please choose the character type.")
        self.title.setFont(font)

        font = qtg.QFont('Didot', 18)
        self.new_desc = qtw.QPushButton("New Descendant")
        self.new_desc.setFont(font)
        self.new_desc.pressed.connect(lambda: self.handleSelection(CHAR_TYPE.DESCENDANT))
        # self.new_desc.pressed.connect(self.close)

        self.new_part = qtw.QPushButton("New Partner")
        self.new_part.setFont(font)
        self.new_part.pressed.connect(lambda: self.handleSelection(CHAR_TYPE.PARTNER))
        # self.new_part.pressed.connect(self.close)

        layout.addWidget(self.title, 1, 0, 1, 3)
        layout.addWidget(self.new_desc, 2, 0, 1, 1)
        layout.addWidget(self.new_part, 2, 2, 1, 1)
        self.setLayout(layout)
        self.setSizePolicy(qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Preferred)
        self.setWindowTitle('New Character Type')

        self.selection = None
    
    def handleSelection(self, char_type):
        self.selection = char_type
        self.done(0)
    
    @staticmethod
    def requestType():
        window = CharacterTypeSelect()
        window.exec_()
        return window.selection




class CustomMsgBox(qtw.QDialog):

    def __init__(self, msg, parent=None):
        super(CustomMsgBox, self).__init__(parent)
        self.setFocusPolicy(qtc.Qt.NoFocus)
        font = qtg.QFont('Didot', 28)
        layout = qtw.QHBoxLayout()
        self.title = qtw.QLabel(msg)
        self.title.setFont(font)
        
        layout.addWidget(self.title)
        self.setLayout(layout)

        # self.setStandardButtons(qtw.QMessageBox.NoButton)


class AutoCloseMessageBox(qtw.QMessageBox):

    def __init__(self, parent=None):
        super(AutoCloseMessageBox, self).__init__(parent)
        self.timeout = 0
        self.currentTime = 0
    
    def showEvent(self, event):
        self.currentTime = 0
        self.startTimer(1000)
    
    def timerEvent(self, *args, **kwargs):
        self.currentTime += 1
        if self.currentTime >= self.timeout:
            self.done(0)
    
    @staticmethod
    def showWithTimeout(timeout_secs, message, window_title=None, icon=None, buttons=qtw.QMessageBox.NoButton):
        w = AutoCloseMessageBox()
        w.timeout = timeout_secs
        w.setText(message)
        if window_title:
            w.setWindowTitle(window_title)
        if icon:
            w.setIcon(icon)
        if buttons:
            w.setStandardButtons(buttons)
        w.exec()