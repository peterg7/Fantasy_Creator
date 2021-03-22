''' Controls the tree graphics. Handles user input & display of the tree

Module for graphics of the tree tab. Controls graphical aspects of the tree including
adding/removing characters to the scene, adding/removing families, requesting
user input, etc. 

Copyright (c) 2020 Peter C Gish

See the MIT License (MIT) for more information. You should have received a copy
of the MIT License along with this program. If not, see 
<https://www.mit.edu/~amini/LICENSE.md>.
'''
__author__ = "Peter C Gish"
__date__ = "3/14/21"
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
from .tree import Tree
from .treeAccessories import PartnerSelect, ParentSelect, CharacterTypeSelect, CharacterView, CharacterCreator
from .character import Character
from fantasycreator.Dialogs.messageBoxes import CustomMsgBox, AutoCloseMsgBox
from fantasycreator.Dialogs.lineInputs import UserLineInput, UserSelectInput
from fantasycreator.Dialogs.pictureEditor import PictureEditor
import fantasycreator.Mechanics.flags as flags
from fantasycreator.Data.hashList import HashList
from fantasycreator.Data.database import DataFormatter

# External resources
from fantasycreator.resources import resources


class TreeView(qtw.QGraphicsView):
    ''' Object that provides the viewport of the tree tab. Holds the scene
    object and enables interaction between graphical and non-graphical objects.
    Handles all mouse/keyboard events and any necessary dialog windows.
    '''
    # Custom signals
    tempStatusbarMsg = qtc.pyqtSignal(str, int)
    sceneClicked = qtc.pyqtSignal(qtc.QPoint)

    zoomChanged = qtc.pyqtSignal(int)
    setCharDel = qtc.pyqtSignal(bool)

    TREE_DISPLAY = flags.TREE_ICON_DISPLAY.IMAGE
    CENTER_ANCHOR = qtc.QPointF(5000, 150)
    DFLT_VIEW = qtc.QRectF(4000, 150, 5000, 1000)

    # Relative bounds for user zoom
    MIN_ZOOM = -8
    MAX_ZOOM = 8

    def __init__(self, parent=None, size=None):
        ''' Constructor - initialize TreeScene, set window settings, and establish 
        global constants

        Args:
            parent - widget for this object
            size - initial size of the graphics port
        '''

        super(TreeView, self).__init__(parent)
        logging.debug('Initializing tree...')

        self.tree = Tree(self)

        # Setup Scene
        self.scene = TreeScene(self)
        self.setScene(self.scene)
        self.setVerticalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
        self.centerOn(self.CENTER_ANCHOR)
        self.setResizeAnchor(qtw.QGraphicsView.AnchorViewCenter)
        self.setTransformationAnchor(qtw.QGraphicsView.NoAnchor)
        self.setRenderHints(qtg.QPainter.Antialiasing |
                            qtg.QPainter.SmoothPixmapTransform)

        # Scrollpad gestures
        self.viewport().grabGesture(qtc.Qt.PinchGesture)
        self.viewport().setAttribute(qtc.Qt.WA_AcceptTouchEvents)

        # Local variables
        self.zoom_factor = 1
        self.current_factor = 1
        self.zoomStatus = 0
        self.zoom_tracker = 0
        self.char_selection_timeout = 10000  # in ms
        self.char_views = []
        self._pan = False
        self._pan_act = False
        self.selecting_char = False
        self.selected_char = None
        self._mousePressed = False
        self.last_mouse = None

    ##----------------------- Initializaiton Methods ------------------------##

    def connectDB(self, database):
        ''' Connects to the global database and establishes necessary tables

        Args:
            database - instance of global database
        '''
        self.tree.connectDB(database)
        # Create tables
        self.character_db = database.table('characters')
        self.families_db = database.table('families')
        self.kingdoms_db = database.table('kingdoms')

    def initTree(self):
        self.tree.initTree()
        self.tree.initCharCombos()

    ##-------------------- Adding/Modifying Characters ---------------------##

    @qtc.pyqtSlot(Family)
    def addFamily(self, new_fam):
        ''' Simple slot to insert the passed in family to the scene

        Args:
            new_fam - new family object to add to the scene
        '''
        self.scene.addFamToScene(new_fam)

    @qtc.pyqtSlot(Family)
    def delFamily(self, target_fam):
        ''' Slot to remove a specific family from the scene

        Args:
            target_fam - desired family to be removed from the scene (not deleted)
        '''
        self.scene.removeFamFromScene(target_fam)

    @qtc.pyqtSlot(Character)
    def delCharacter(self, target_char):
        ''' Slot to remove a specific character from the scene

        Args:
            target_char - character to be removed from the scene (not deleted)
        '''
        self.scene.removeItem(target_char)

    @qtc.pyqtSlot()
    @qtc.pyqtSlot(int, uuid.UUID)
    def createCharacter(self, char_type=None, parent_id=None):
        ''' Initial method for building a character. Launches a CharacterCreator
        popup for the user to enter information. Passes the input to the 
        addNewCharacter method

        Args:
            char_type - the type of character beeing build (Normal/Partner)
            parent - the optional parent (or partner) of this new character
        '''
        if not char_type:
            char_type = CharacterTypeSelect.requestType()
        if not char_type:
            return

        # Determine default family for this new character
        fam_id = None
        fam_created = False
        fam_name = None
        if parent_id:
            if char_type != flags.CHAR_TYPE.PARTNER:
                parent_dict = self.character_db.get(where('char_id') == parent_id)
                partners = parent_dict.get('partnerships', None)
                if not partners:
                    fam_id = parent_dict['fam_id']
                elif len(partners) == 1:
                    fam_id = partners[0]['rom_id']
                else:
                    logging.error('Feature not implemented, need to select form multiple partners')
            else:
                create_new_fam = self.confirmNewFamily()
                if create_new_fam == qtw.QMessageBox.Yes:
                    fam_created = True
                    fam_name = self.gatherFamName()
                    
        self.new_char_dialog = CharacterCreator(self)

        self.new_char_dialog.submitted.connect(
                lambda d: self.tree.addNewCharacter(d, char_type, parent_id))

        if fam_id or fam_created:
            if not fam_name:
                fam_name = self.tree.getFamily(fam_id=fam_id)
            if fam_name not in CharacterCreator.FAMILY_ITEMS:
                CharacterCreator.FAMILY_ITEMS.insert(-1, fam_name)
                self.new_char_dialog.family_select.addItem(fam_name)
            self.new_char_dialog.fixedFamEntry(fam_name)
        self.new_char_dialog.show()

    def gatherFamName(self, first_gen=None, fam_id=None, fam_type=flags.FAM_TYPE.SUBSET, root_pt=None):
        ''' Method to prompt the user for a family name. Distributes the entered name
        to tree.py or internally depending on argument types

        Args:
            first_get - a list of dictionary representation of characters
            fam_id - uuid of this family
            fam_type - flag indicating the type of family this will be
            root_pt - graphical point indicating the initial location of this family
        '''
        name, ok = UserLineInput.requestInput(
            "New Family", "Enter a family name:", self)
        if not ok:
            return False
        if not first_gen:
            return name
        elif root_pt:
            self.tree.addNewFamily(first_gen, name, fam_type, root_pt)
            return

        root_pt = self.mapToScene(self.viewport().rect().center())
        self.tree.addNewFamily(first_gen, name, fam_id, root_pt)
    
    def confirmNewFamily(self):
        ''' Prompt the user with a message dialog to determine if a new family
        should be created for the newly created partner. Returns the user's response
        '''
        create_fam_prompt = qtw.QMessageBox(qtw.QMessageBox.Question, "Create family?",
                                            "Would you like to create a family for the new partner?",
                                            qtw.QMessageBox.Yes | qtw.QMessageBox.No, self)
        prompt_font = qtg.QFont('Didot', 20)
        create_fam_prompt.setFont(prompt_font)
        response = create_fam_prompt.exec()
        return response
    
    def selectFamilyName(self, options):
        ''' Launches a dialog window for the user to choose from a list of
        options and returns the result

        Args:
            options - list of string choices for the user to choose from
        '''
        selection, ok = UserSelectInput.requestInput(
            'Choose Family Name',
            'What would you like to call the newly formed family?',
            options,
            self)
        if not ok:
            return False
        return selection


    @qtc.pyqtSlot()
    @qtc.pyqtSlot(str)
    def createFamily(self, fam_name=None):
        ''' Slot that is called to build a new family object. Requests name of the
        new family and passes information to addNewFamily()

        Args:
            parent - optional parent used as the head of the family
        '''
        if not fam_name:
            fam_name = self.gatherFamName()
            if not fam_name:
                return
            # CharacterCreator.FAMILY_ITEMS.append(name)
            self.new_char_dialog = CharacterCreator(self)
            if fam_name not in CharacterCreator.FAMILY_ITEMS:
                CharacterCreator.FAMILY_ITEMS.insert(-1, fam_name)
                self.new_char_dialog.family_select.addItem(fam_name)
            self.new_char_dialog.fixedFamEntry(fam_name)
            root_pt = self.mapToScene(self.viewport().rect().center())
            self.new_char_dialog.submitted.connect(lambda d: self.tree.addNewFamily(
                first_gen=[d], fam_name=fam_name, fam_type=flags.FAM_TYPE.SINGLETON, root_pt=root_pt))
            self.new_char_dialog.show()
        else:
            return

    @qtc.pyqtSlot()
    def characterSelected(self):
        ''' Slot to determine if a character has been selected in the graphics port.
        Called everytime there is a mouse click
        '''
        if self.selecting_char:
            return

        # at least one character selected
        if self.last_mouse == 'Single' and len(self.scene.selectedItems()) > 0:
            # NOTE: only using "first" item
            selected_item = self.scene.selectedItems()[0]
            if isinstance(selected_item, Character):
                self.addCharacterView(selected_item.getID())

        # at least one character selected
        elif self.last_mouse == 'Double' and len(self.scene.selectedItems()) > 0:
            # NOTE: only using "first" item
            selected_item = self.scene.selectedItems()[0]
            if isinstance(selected_item, Character):
                self.addCharacterEdit(selected_item.getID())

    # @qtc.pyqtSlot(dict, qtc.QPointF)
    def inspectSelection(self, point):
        ''' Determines if the passed in point is contained within a character's
        bounding box
        '''
        self.toggleSelecting()
        if point:
            selection = self.itemAt(point)
            if not selection and self.scene.sceneRect().contains(point):
                selection = self.mapToScene(point)
            self.selected_char = selection

    def requestCharacter(self, msg_prompt):
        ''' Method used when the user must select a character. Waits 
        `char_selection_time` for user to make a selection
        '''
        self.selecting_char = True
        self.selected_char = None
        print(msg_prompt)

        # AutoCloseMessageBox.showWithTimeout(3, msg_prompt)
        prompt = CustomMsgBox(msg_prompt)
        prompt.move(self.width()/2, 0)
        self.sceneClicked.connect(prompt.close)
        prompt.show()

        self.tempStatusbarMsg.emit(
            f'{msg_prompt}...', self.char_selection_timeout)
        loop = qtc.QEventLoop()
        self.sceneClicked.connect(loop.quit)
        self.sceneClicked.connect(self.inspectSelection)
        timer = qtc.QTimer()
        timer.singleShot(self.char_selection_timeout, loop.quit)
        loop.exec()


    ##----------------- Removing characters/relationships ------------------##

    @qtc.pyqtSlot()
    def deleteActiveChar(self):
        ''' Slot that is used by the toolbar and keyboard shortcuts to delete
        the most recently active character
        '''
        if self.scene.selectedItems():
            char = self.scene.selectedItems()[0]
            char_id = char.getID()

        elif self.char_views:
            char = self.char_views[-1]
            char_id = uuid.UUID(char.objectName()[4:])
        else:  # No active character
            return
        fam_id = self.character_db.get(where('char_id') == char_id)['fam_id']
        if fam_id not in self.MasterFamilies.keys():
            fam_id = self.character_db.get(where('char_id') == char_id)[
                'partnerships'][0]['rom_id']
        # TreeView.MasterFamilies[fam_id].deleteCharacter(char_id)
        for _id, fam in TreeView.MasterFamilies.items():
            fam.deleteCharacter(char_id)

    def promptDeleteFam(self, fam_name):
        delete_fam_prompt = qtw.QMessageBox(qtw.QMessageBox.Warning, "Delete family?",
                                            (f"Are you sure you would like to delete the"
                                             f"{fam_name} family?"),
                                            qtw.QMessageBox.No | qtw.QMessageBox.Yes, self)
        delete_fam_prompt.setInformativeText('This action can not be undone.')
        prompt_font = qtg.QFont('Didot', 20)
        delete_fam_prompt.setFont(prompt_font)
        response = delete_fam_prompt.exec()
        return response == qtw.QMessageBox.Yes

    @qtc.pyqtSlot()
    def checkCharDeleteBtn(self):
        ''' Slot used by the toolbar to determine if the character delete button
        should be visible
        '''
        if not self.char_views:
            self.setCharDel.emit(False)
            CharacterView.CURRENT_SPAWN = qtc.QPoint(
                20, 50)  # NOTE: Magic Number
        else:
            self.setCharDel.emit(True)

    @qtc.pyqtSlot(uuid.UUID)
    @qtc.pyqtSlot(Character)
    def addCharacterView(self, char_id):
        '''Slot called when a character is selected. Creates a view object displaying
        basic information about the selected character

        Args:
            char_id - character id who has been selected and will be viewed
        '''
        if char_id is not None:
            char_view = self.findChild(CharacterView, 'view{}'.format(char_id))
            if char_view is None:
                char = self.character_db.get(where('char_id') == char_id)
                fam_record = self.families_db.get(
                    where('fam_id') == char['fam_id'])

                if not fam_record:
                    if char['partnerships']:
                        fam_record = self.families_db.get(
                            where('fam_id') == char['partnerships'][0]['rom_id'])
                    else:
                        fam_record = {'fam_name': ''}  # NOTE: Temporary
                char['family'] = fam_record['fam_name']
                kingdom_record = self.kingdoms_db.get(
                    where('kingdom_id') == char['kingdom_id'])
                if not kingdom_record:
                    char['kingdom'] = ''
                else:
                    char['kingdom'] = kingdom_record['kingdom_name']

                popup_view = CharacterView(char)
                popup_view.setParent(self)
                self.scene.addItem(popup_view)
                # NOTE: Magic numbers!
                popup_view.setPos(self.mapToScene(CharacterView.CURRENT_SPAWN))
                popup_view.setZValue(2)
                CharacterView.CURRENT_SPAWN += qtc.QPoint(10, 10)
                popup_view.closed.connect(
                    lambda: self.char_views.remove(popup_view))
                popup_view.closed.connect(self.checkCharDeleteBtn)
                popup_view.closed.connect(self.scene.clearSelection)
                self.char_views.append(popup_view)
                self.scene.selectionChanged.connect(popup_view.check_selected)
                self.checkCharDeleteBtn()
            else:
                char_view.setSelected(True)

    @qtc.pyqtSlot(uuid.UUID)
    def addCharacterEdit(self, char_id):
        ''' Slot called when a character is double clicked. Launches a popup window
        that allows the user to modify information about the character. Upon
        submission, the information is pased to receiveCharacterUpdate() for
        storage

        Args:
            char_id - id of the character to be edited.
        '''
        selected_char = self.character_db.get(where('char_id') == char_id)
        if selected_char:
            fam_record = self.families_db.get(
                where('fam_id') == selected_char['fam_id'])
            if not fam_record:
                fam_record = self.families_db.get(
                    where('fam_id') == selected_char['partnerships'][0]['rom_id'])
            selected_char['family'] = fam_record['fam_name']
            kingdom_record = self.kingdoms_db.get(
                where('kingdom_id') == selected_char['kingdom_id'])
            if kingdom_record:
                selected_char['kingdom'] = kingdom_record['kingdom_name']
            else:
                selected_char['kingdom'] = ''
            self.edit_window = CharacterCreator(self, selected_char)
            self.edit_window.submitted.connect(
                self.tree.receiveCharacterUpdate)
            # self.edit_window.submitted.connect(lambda d: self.updatedChars.emit([d['char_id']]))
            self.edit_window.show()

    @qtc.pyqtSlot()
    def updateView(self):
        self.scene.update()
        self.viewport().update()

    @qtc.pyqtSlot()
    def resetView(self):
        self.scene.resetScene()

    def toggleSelecting(self):
        self.selecting_char = False
        self.tempStatusbarMsg.emit('', 100)  # temporary way to clear message

    def togglePanning(self, state):
        self._pan = state
        self._pan_act = state
        self._mousePressed = False
        if self._pan:
            self.viewport().setCursor(qtc.Qt.OpenHandCursor)
        else:
            self.viewport().unsetCursor()

    ##-------------------- Override Built-In Event Slots --------------------##

    def resizeEvent(self, event):
        ''' Override method to capture a resize and adjust the size of the viewport
        accordingly
        '''
        self.fitWithBorder()
        super(TreeView, self).resizeEvent(event)

    def fitWithBorder(self):
        ''' Sizes the viewport with a border on all four sides
        '''
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

    # TODO: Detect mouse presence and default to wheel if discovered
    # def wheelEvent(self, event):
    #     if event.angleDelta().y() > 0:
    #         direction = self.zoomStatus + 1
    #     else:
    #         direction = self.zoomStatus - 1
    #     self.zoomEvent(direction, event.pos())

    def zoomEvent(self, factor, center_pos=None):
        ''' Performs the necessary calcultions and validation checks to execute
        a zoom transformation of the viewport

        Args:
            factor - the scale factor to be applied
            center_pos - the center position for the zoom (the scene's center
                            will be used if not provided)
        '''
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

    # Mouse Events

    def mousePressEvent(self, event):
        ''' Capture mouse preses and analyze them. Store the coordinates of the
        event in the case of panning

        Args: 
            event - mouseEvent that was cought by the system
        '''
        if self.selecting_char and event.button() == qtc.Qt.LeftButton:
            self.sceneClicked.emit(event.pos())
            return

        self.last_mouse = 'Single'
        if event.button() == qtc.Qt.LeftButton:
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
        ''' Capture mouse releases and reset stored mouse values. Launch a timer
        for an interval for double clicking
        '''
        self._mousePressed = False
        if self._pan:
            self.viewport().setCursor(qtc.Qt.OpenHandCursor)

            # event.accept()
        if self.last_mouse == "Single":
            qtc.QTimer.singleShot(qtw.QApplication.instance().doubleClickInterval(),
                                  self.characterSelected)
        super(TreeView, self).mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        ''' Store the double click and pass it along to the superclass
        '''
        self.last_mouse = 'Double'
        super(TreeView, self).mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        ''' Store state of mouse and execute panning if applicable
        '''
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

    # Gestures

    def viewportEvent(self, event):
        ''' Capture events that correspond with trackpad controls
        '''
        if event.type() == qtc.QEvent.Gesture:
            return self.gestureEvent(event)
        elif event.type() == qtc.QEvent.GestureOverride:
            event.accept()
        return super(TreeView, self).viewportEvent(event)

    def gestureEvent(self, event):
        ''' Capture gesture events for pinch (zoom) and utilize the existing
        zoomEvent function to translate the gesture to an action
        '''
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

    # Keyboard input

    def keyPressEvent(self, event):
        ''' Override keyboard input to the graphics port. Captures the escape
        key for closing CharacterViews or clearing selection

        Args:
            event - keyEvent caught by the system
        '''
        if event.key() == qtc.Qt.Key_Escape:        # Escape key shortcuts
            if self.scene.selectedItems():
                item = self.scene.selectedItems()[0]
                if isinstance(item, Character):
                    child = self.findChild(
                        CharacterView, 'view{}'.format(item.getID()))
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


class TreeScene(qtw.QGraphicsScene):
    '''
    Object that handles the graphical visualization of the tree. Qt couples a viewport
    with a scene in order to display and easily manipulate graphical objects. This
    object does very little besides provide an access point for graphical display.
    '''

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
        ''' Constructor for the tree scene. Establishes size, sets background
        and instantiates member variables

        Args:
            parent - optional parent widget
        '''
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
    def resetScene(self):
        ''' Restores the scene to how it was when the scene was created
        '''
        self.clearSelection()
        for fam in self.current_families:
            fam.reset_family()
        self.clearFocus()

    ## Auxiliary Methods ##

    def addFamToScene(self, fam):
        ''' Adds the provided family to the scene and installs scene filters
        for mouse events

        Args:
            fam - family object to be added to the scene
        '''
        if fam not in self.current_families:
            fam.setZValue(1)
            self.addItem(fam)
            self.current_families.append(fam)
            fam.installFilters()

    def removeFamFromScene(self, fam):
        ''' Removes the passed in family from the scene

        Args:
            fam - family to be removed from the scene
        '''
        if fam in self.current_families:
            self.current_families.remove(fam)
            self.removeItem(fam)
