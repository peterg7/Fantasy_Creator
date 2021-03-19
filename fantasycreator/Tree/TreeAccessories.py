''' Holds methods to support the TreeGraphics and Character modules

Contains various message box templates used by the TreeGraphics module. 
Stored in this file simply for organizational purposes

Copyright (c) 2020 Peter C Gish

See the MIT License (MIT) for more information. You should have received a copy
of the MIT License along with this program. If not, see 
<https://www.mit.edu/~amini/LICENSE.md>.
'''
__author__ = "Peter C Gish"
__date__ = "3/13/21"
__maintainer__ = "Peter C Gish"
__version__ = "1.0.1"


# PyQt 
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

# Built-in Modules
import re
import logging

# 3rd Party
from tinydb import where

# User-defined Modules
# from .treeGraphics import TreeView
from .character import Character
from fantasycreator.Mechanics.flags import CHAR_TYPE
from fantasycreator.Dialogs.pictureEditor import PictureEditor, PictureLineEdit
from fantasycreator.Mechanics.flags import TREE_ICON_DISPLAY, EVENT_TYPE
from fantasycreator.Mechanics.storyTime import Time, DateLineEdit


# External resources
from fantasycreator.resources import resources

class PartnerSelect(qtw.QDialog):
    ''' Simple dialog window asking the user to pick from existing characters
    or create a new one as a partner. 
    '''

    # Custom signal
    selection_made = qtc.pyqtSignal(bool)
    
    def __init__(self, parent=None):
        ''' Constructor. Creates layout, sets fonts, and builds buttons
        to be used for display and collection of the user's response.

        Args:
            parent - optional parent widget
        '''
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
        self.setWindowTitle('Partner Creation Type')
    

class ParentSelect(qtw.QDialog):
    ''' Similar to PartnerSelect, this dialog window requests the type of character
    to be the parent. Either an existing object or to create a new one.
    '''

    # Custom signals
    selection_made = qtc.pyqtSignal(bool)
    
    def __init__(self, parent=None):
        ''' Constructor. Establishes layout, customizes appearance, and builds
        the input buttons.

        Args:
            parent - optional parent widget
        '''
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
    ''' Dialog window that is launched by the creation of a new Character from
    the toolbar. Prompts the user for the type of character they wish to create.
    Possess a static method to allow for non-instantiated execution of this window.
    '''

    def __init__(self, parent=None):
        ''' Constructor. Intializes the dialog, customizes it's appearance, and
        builds input buttons.

        Args:
            parent - optional parent widget
        '''
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
        ''' Callback method for user response
        '''
        self.selection = char_type
        self.done(0)
    
    @staticmethod
    def requestType():
        window = CharacterTypeSelect()
        window.exec_()
        return window.selection


class CharacterView(qtw.QGraphicsWidget):
    ''' Popup window that is launched when the user clicks on a character object.
    The popup is embedded in the main window and thus is not a dialog but a 
    graphics widget.
    '''

    # Custom signals and global variables
    closed = qtc.pyqtSignal()
    CURRENT_SPAWN = qtc.QPoint(20, 60)  #NOTE: Magic Number

    def __init__(self, char_dict, parent=None):
        ''' Constructor. Builds the layout, add necessary widgets, and customizes
        appearance.

        Args:
            char_dict - the character's information in dictionary form
            parent - optional parent widget
        '''
        super(CharacterView, self).__init__(parent)
        self.setAttribute(qtc.Qt.WA_DeleteOnClose)
        self.setFlags(qtw.QGraphicsItem.ItemIsMovable | qtw.QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setCursor(qtc.Qt.OpenHandCursor)
        
        self._char = char_dict
        self._id = self._char['char_id']
        self.setObjectName('view{}'.format(self._id))

        self.brush = qtg.QBrush(qtg.QColor('#c9cdd4')) # make dependent upon gender? kingdom?
        self.translucent_effect = qtw.QGraphicsOpacityEffect(self)
        self.translucent_effect.setOpacity(0.8)
        self.setGraphicsEffect(self.translucent_effect)
        self.translucent_effect.setEnabled(False)

        self.setSizePolicy(
            qtw.QSizePolicy.Preferred,
            qtw.QSizePolicy.Preferred
        )

        self.setScale(1.4)

        # Set layout
        layout = qtw.QGraphicsLinearLayout(qtc.Qt.Vertical)
        label_style = """ QLabel {
                    background-color: #e3ddcc;
                    border-radius: 5px;
                    border-color: gray;
                    padding: 4px;
                    font: 24px;
                }"""
        
        # Create and add label widgets
        self.name_label = qtw.QGraphicsProxyWidget(self)
        self.name_label.setWidget(CharacterViewLabel())
        self.name_label.widget().setStyleSheet("""QLabel {
                    background-color: rgba(255, 255, 255, 0);
                    border-radius: 5px;
                    border-color: gray;
                    padding: 4px;
                    font: 34px 'Didot';
                }""")
        self.name_label.widget().setAlignment(qtc.Qt.AlignHCenter | qtc.Qt.AlignVCenter)
        self.name_label.setAcceptHoverEvents(False)
        layout.addItem(self.name_label)

        self.family_label = qtw.QGraphicsProxyWidget(self)
        self.family_label.setWidget(CharacterViewLabel())
        self.family_label.widget().setStyleSheet(label_style)
        self.family_label.setAcceptHoverEvents(False)
        layout.addItem(self.family_label)

        self.sex_label = qtw.QGraphicsProxyWidget(self)
        self.sex_label.setWidget(CharacterViewLabel())
        self.sex_label.widget().setStyleSheet(label_style)
        self.sex_label.setAcceptHoverEvents(False)
        layout.addItem(self.sex_label)

        self.birth_label = qtw.QGraphicsProxyWidget(self)
        self.birth_label.setWidget(CharacterViewLabel())
        self.birth_label.widget().setStyleSheet(label_style)
        self.birth_label.setAcceptHoverEvents(False)
        layout.addItem(self.birth_label)

        self.death_label = qtw.QGraphicsProxyWidget(self)
        self.death_label.setWidget(CharacterViewLabel())
        self.death_label.widget().setStyleSheet(label_style)
        self.death_label.setAcceptHoverEvents(False)
        layout.addItem(self.death_label)

        self.race_label = qtw.QGraphicsProxyWidget(self)
        self.race_label.setWidget(CharacterViewLabel())
        self.race_label.widget().setStyleSheet(label_style)
        self.race_label.setAcceptHoverEvents(False)
        layout.addItem(self.race_label)

        self.kingdom_label = qtw.QGraphicsProxyWidget(self)
        self.kingdom_label.setWidget(CharacterViewLabel())
        self.kingdom_label.widget().setStyleSheet(label_style)
        self.kingdom_label.setAcceptHoverEvents(False)
        layout.addItem(self.kingdom_label)

        self.updateView()

        self.cancel_btn = qtw.QGraphicsProxyWidget(self)
        self.cancel_btn.setWidget(qtw.QPushButton(
            'Cancel',
            clicked=self.close
        ))
        self.cancel_btn.widget().setStyleSheet("""
                        QPushButton { 
                            border: 1px solid black;
                            border-style: outset;
                            border-radius: 2px;
                            color: black;
                            font: 24px;
                            font-family: Baskerville;
                        }
                        QPushButton:pressed { 
                            background-color: rgba(255, 255, 255, 70);
                            border-style: inset;
                        }""")
        layout.addItem(self.cancel_btn)
        layout.setSpacing(16)
        self.setLayout(layout)
        
    
    def getID(self):
        return self._id
    
    def updateView(self):
        ''' Accesses the stored character dictionary and reflects the stored
        information onto the view.
        '''
        if self._char['name']:
            label_string = self._char['name']
        else:
            label_string = 'Name: ...'
        self.name_label.widget().setText(label_string)

        if self._char['family']:
            label_string = f"<b>Family</b>: {self._char['family']}"
        else:
            label_string = 'Family: ...'
        self.family_label.widget().setText(label_string)
        
        if self._char['sex']:
            label_string = f"<b>Sex</b>: {self._char['sex']}"
        else:
            label_string = 'Sex: ...'
        self.sex_label.widget().setText(label_string)
        
        if self._char['birth']:
            label_string = f"<b>Birth</b>: {str(self._char['birth'])}"
        else:
            label_string = 'Birth: ...'
        self.birth_label.widget().setText(label_string)

        if self._char['death']:
            label_string = f"<b>Death</b>: {str(self._char['death'])}"
        else:
            label_string = 'Death: ...'
        self.death_label.widget().setText(label_string)

        if self._char['race']:
            label_string = f"<b>Race</b>: {self._char['race']}"
        else:
            label_string = 'Race: ...'
        self.race_label.widget().setText(label_string)

        if self._char['kingdom']:
            label_string = f"<b>Kingdom</b>: {self._char['kingdom']}"
        else:
            label_string = 'Kingdom: ...'
        self.kingdom_label.widget().setText(label_string)
    

    def check_selected(self):
        ''' Simple test method to see if this view is currently selected.
        '''
        if self.isSelected():
            self.translucent_effect.setEnabled(False)
        else:
            self.translucent_effect.setEnabled(True)
    
    def sceneEventFilter(self, source, event):
        if event.type() != qtc.QEvent.GraphicsSceneHoverMove:
            # Intercept event
            return True
        return super(CharacterView, self).sceneEventFilter(source, event)

    ## Override drawing methods ##

    def paint(self, painter, option, widget):
        frame = qtc.QRectF(qtc.QPointF(0, 0), self.geometry().size())
        painter.setBrush(self.brush)
        painter.drawRoundedRect(frame, 10, 10)
    
    def shape(self):
        path = qtg.QPainterPath()
        path.addRect(self.boundingRect())
        return path

    ## Override Built-In Slots ##
    def closeEvent(self, event):
        self.closed.emit()
        super(CharacterView, self).closeEvent(event)
    
    def mousePressEvent(self, event):
        self.setCursor(qtc.Qt.ClosedHandCursor)
        event.accept()
        super(CharacterView, self).mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.setCursor(qtc.Qt.OpenHandCursor)
        event.accept()
        super(CharacterView, self).mouseReleaseEvent(event)
    

class CharacterViewLabel(qtw.QLabel):
    ''' Custom label widget for appearance purposes
    '''
    def __init__(self, parent=None):
        super(CharacterViewLabel, self).__init__(parent)
        self.setTextFormat(qtc.Qt.RichText)
        self.setFont(qtg.QFont('Baskerville', 26))
        self.setCursor(qtc.Qt.OpenHandCursor)
    

class CharacterCreator(qtw.QDialog):
    ''' Dialog window to gather necessary information from the user regarding
    character creation. Provides input fields for all stored fields of a 
    character. Reused for editing a character by initially filled out the form
    with the existing data.
    '''

    # Custom signals
    submitted = qtc.pyqtSignal(dict)
    closed = qtc.pyqtSignal()

    # Global class variables
    DFLT_PROFILE_PATH = ':/dflt-tree-images/default_profile.png'
    UNKNOWN_MALE_PATH = ':/dflt-tree-images/unknown_male.png'
    UNKNOWN_FEMALE_PATH = ':/dflt-tree-images/unknown_female.png'

    SEX_ITEMS = ["Select Sex"]
    RACE_ITEMS = ["Select Race"]
    KINGDOM_ITEMS = ["Select Kingdom"]
    FAMILY_ITEMS = ["Select Family"]

    IMAGES_PATH = 'tmp/' # TODO: FIX THIS

    def __init__(self, parent=None, editing_char=None):
        ''' Constructor. Initializes the window and builds all component
        widgets. Determines if editing or creating. 

        Args:
            parent - optional parent widget
            editing_char - dictionary of the character to edit
        '''
        super(CharacterCreator, self).__init__(parent)

        self.setAttribute(qtc.Qt.WA_DeleteOnClose)
        self.setModal(True) # CAUSES BUG 

        self.setMinimumSize(415, 500)
        self.setMaximumSize(415, 700)

        self.RULER_PIC = qtg.QPixmap(Character.RULER_PIC_PATH)
        self._id = 0
        self.disabled_entries = []

        layout = qtw.QFormLayout()

        # Create input widgets
        self.name = qtw.QLineEdit()
        self.name.setFont(qtg.QFont('Baskerville', 16))
        self.family_select = qtw.QComboBox()
        self.family_select.setFont(qtg.QFont('Baskerville', 16))
        self.sex_selection = qtw.QComboBox()
        self.sex_selection.setFont(qtg.QFont('Baskerville', 16))
        self.race_selection = qtw.QComboBox()
        self.race_selection.setFont(qtg.QFont('Baskerville', 16))
        self.birth_date = DateLineEdit()
        self.birth_date.setFont(qtg.QFont('Baskerville', 16))
        self.death_date = DateLineEdit()
        self.death_date.setFont(qtg.QFont('Baskerville', 16))
        self.kingdom_select = qtw.QComboBox()
        self.kingdom_select.setFont(qtg.QFont('Baskerville', 16))
        self.ruler = qtw.QCheckBox()
        self.ruler_picture = qtw.QLabel()
        self.picture_path = PictureLineEdit()
        self.picture_path.setFont(qtg.QFont('Baskerville', 16))
        self.picture = qtw.QLabel()

        # Modify widgets
        self.sex_selection.addItems(self.SEX_ITEMS)
        self.sex_selection.model().item(0).setEnabled(False)

        self.race_selection.addItems(self.RACE_ITEMS)
        self.race_selection.model().item(0).setEnabled(False)

        self.family_select.addItems(self.FAMILY_ITEMS)
        self.family_select.model().item(0).setEnabled(False)

        self.kingdom_select.addItems(self.KINGDOM_ITEMS)
        self.kingdom_select.model().item(0).setEnabled(False)


        self.onRulerChange(self.ruler.checkState())

        # Connect signals
        self.sex_selection.currentTextChanged.connect(self.onSexChange)
        self.race_selection.currentTextChanged.connect(self.onRaceChange)
        self.family_select.currentTextChanged.connect(self.onFamChange)
        self.kingdom_select.currentTextChanged.connect(self.onKingdomChange)
        self.ruler.stateChanged.connect(self.onRulerChange)
        self.picture_path.clicked.connect(self.getPic)

        self.submit_btn = qtw.QPushButton(
            'Submit',
            clicked=self.onSubmit
        )
        self.submit_btn.setDefault(True)
        self.submit_btn.setAutoDefault(True)
        self.submit_btn.setFont(qtg.QFont('Baskerville', 16))
        # self.submit_btn.setStyleSheet(
        #     """
        #     QPushButton{
        #         outline: none;
        #         font-family: 'Baskerville';
        #         font-size: 18px;
        #     }""")
        self.cancel_btn = qtw.QPushButton(
            'Cancel',
            clicked=self.close
        )
        self.cancel_btn.setDefault(False)
        self.cancel_btn.setAutoDefault(False)
        self.cancel_btn.setFont(qtg.QFont('Baskerville', 16))
        # self.cancel_btn.setStyleSheet(
        #     """
        #     QPushButton{
        #         outline: none;
        #         font-family: 'Baskerville';
        #         font-size: 18px;
        #     }""")
        
        
        # Define layout
        layout.addRow('Name', self.name)
        label = layout.labelForField(self.name)
        label.setFont(qtg.QFont('Baskerville', 16))
        layout.addRow('Sex', self.sex_selection)
        label = layout.labelForField(self.sex_selection)
        label.setFont(qtg.QFont('Baskerville', 16))
        layout.addRow('Birth Date', self.birth_date)
        label = layout.labelForField(self.birth_date)
        label.setFont(qtg.QFont('Baskerville', 16))
        layout.addRow('Death Date', self.death_date)
        label = layout.labelForField(self.death_date)
        label.setFont(qtg.QFont('Baskerville', 16))
        layout.addRow('Race', self.race_selection)
        label = layout.labelForField(self.race_selection)
        label.setFont(qtg.QFont('Baskerville', 16))
        layout.addRow('Family', self.family_select)
        label = layout.labelForField(self.family_select)
        label.setFont(qtg.QFont('Baskerville', 16))
        layout.addRow('Kingdom', self.kingdom_select)
        label = layout.labelForField(self.kingdom_select)
        label.setFont(qtg.QFont('Baskerville', 16))

        grid_layout = qtw.QGridLayout()
        # grid_layout.setColumnStretch(3, 1)
        # grid_layout.setHorizontalSpacing()
        # grid_layout.setColumnStretch(1, 2)
        # grid_layout.setColumnStretch(2, 2)
        grid_layout.setRowMinimumHeight(1, self.RULER_PIC.height())
        max_width = max(self.picture.width(), self.RULER_PIC.width())
        grid_layout.setColumnMinimumWidth(3, max_width)

        ruler_label = qtw.QLabel('Ruler')
        ruler_label.setFont(qtg.QFont('Baskerville', 16))
        grid_layout.addWidget(ruler_label, 1, 0)
        grid_layout.addWidget(self.ruler, 1, 1, 1, 1)
        grid_layout.addWidget(self.ruler_picture, 1, 3, 2, 1, qtc.Qt.AlignCenter)

        picture_label = qtw.QLabel('Picture')
        picture_label.setFont(qtg.QFont('Baskerville', 16))
        grid_layout.addWidget(picture_label, 4, 0)
        self.picture_path.setSizePolicy(qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Fixed)
        grid_layout.addWidget(self.picture_path, 4, 1, 1, 2)
        grid_layout.addWidget(self.picture, 4, 3, 2, 1, qtc.Qt.AlignCenter)

        layout.addRow(grid_layout)

        button_box = qtw.QHBoxLayout()
        button_box.addWidget(self.cancel_btn)
        button_box.addWidget(self.submit_btn)
        layout.addRow(button_box)

        layout.setLabelAlignment(qtc.Qt.AlignLeft)

        self.setLayout(layout)
        self.setFont(qtg.QFont('Baskerville', 18))
        if editing_char:
            self._char = editing_char
            self.setWindowTitle(self._char['name'])
            self.parseExistingChar()
        else:
            self._char = {}
            self.setWindowTitle('Create a new character')
        #self.setVisible(True)
    
    def parseExistingChar(self):
        ''' Use the information stored in the passed in character dictionary to
        populate this windows labels.
        '''
        self._id = self._char['char_id']
        self.name.setText(self._char['name'])
        self.family_select.setCurrentText(self._char['family'])
        self.sex_selection.setCurrentText(self._char['sex'].title())
        self.race_selection.setCurrentText(self._char['race'].title())
        if self._char['birth']:
            self.birth_date.setText(str(self._char['birth']))
        if self._char['death']:
            self.death_date.setText(str(self._char['death']))
        self.kingdom_select.setCurrentText(self._char['kingdom'])
        self.ruler.setChecked(self._char['ruler'])
        self.picture_path.setText(self._char['picture_path'])
        # self.picture.setPixmap(qtg.QPixmap(self._char['picture_path']))
        if img := self._char['__IMG__']:
            self.picture.setPixmap(qtg.QPixmap.fromImage(img))
        else:
            self.picture.setPixmap(qtg.QPixmap(self._char['picture_path']))

    # def closeEvent(self, event):
    #     self.closed.emit()
    #     super(CharacterCreator, self).closeEvent(event)
    @qtc.pyqtSlot()
    def getPic(self):
        ''' Slot used to begin the picture acquisition process by prompting the
        user to choose an image stored on their computer. If a filename
        is captured, pass it on to the PictureEditor for the next step. 
        '''
        filename, _ = qtw.QFileDialog.getOpenFileName(
            self,
            'Select an image to open...',
            qtc.QDir.homePath(),
            'Images (*.png *.jpeg *.jpg *.xpm)'
        )
        if filename:
            self.picture_dialog = PictureEditor(filename, EVENT_TYPE.CHAR, self)
            self.picture_dialog.submitted.connect(self.storeNewPic)
            self.picture_dialog.show()

    @qtc.pyqtSlot(str, qtg.QPixmap)
    def storeNewPic(self, filename, pix):
        ''' Stores a newly selected picture in this object

        Args:
            filename - string filename of the new picture
            pix - pixmap storage of the user's image
        '''
        self.picture_path.setText(filename)
        self.picture.setPixmap(pix)
    
    @qtc.pyqtSlot(str)
    def onKingdomChange(self, text):
        ''' Simple callback to examine user's selection for kingdom. Prompts for
        a new option if necessary.

        Args: 
            text - the current text entry that has been selected
        '''
        if text == 'New...':
            text, ok = qtw.QInputDialog.getText(self, 'Define new kingdom', 'Enter kingdom:')
            if ok:
                self.kingdom_select.addItem(text)
                self.KINGDOM_ITEMS.insert(-1, text)
                self.kingdom_select.setCurrentText(text)
            else:
                self.kingdom_select.setCurrentIndex(0)
    
    @qtc.pyqtSlot(str)
    def onFamChange(self, text):
        ''' Simple callback to examine user's selection for family. Prompts for
        a new option if necessary.

        Args: 
            text - the current text entry that has been selected
        '''
        if text == 'New...':
            text, ok = qtw.QInputDialog.getText(self, 'New Family', 'Enter family name:')
            if ok:
                self.family_select.addItem(text)
                self.FAMILY_ITEMS.insert(-1, text)
                self.family_select.setCurrentText(text)
            else:
                self.family_select.setCurrentIndex(0)

    @qtc.pyqtSlot(str)
    def onRaceChange(self, text):
        ''' Simple callback to examine user's selection for race. Prompts for
        a new option if necessary.

        Args: 
            text - the current text entry that has been selected
        '''
        if text == 'Other...':
            text, ok = qtw.QInputDialog.getText(self, 'Define other race', 'Enter race:')
            if ok:
                self.race_selection.addItem(text)
                self.RACE_ITEMS.insert(-1, text)
                self.race_selection.setCurrentText(text)
            else:
                self.race_selection.setCurrentIndex(0)
    
    @qtc.pyqtSlot(str)
    def onSexChange(self, text):
        ''' Simple callback to examine user's selection for sex. Prompts for
        a new option if necessary.

        Args: 
            text - the current text entry that has been selected
        '''
        if text == 'Other...':
            text, ok = qtw.QInputDialog.getText(self, 'Define other sex', 'Enter sex:')
            if ok:
                self.sex_selection.addItem(text)
                self.SEX_ITEMS.insert(len(self.SEX_ITEMS)-1, text)
                self.sex_selection.setCurrentText(text)
            else:
                self.sex_selection.setCurrentIndex(0)
    
    @qtc.pyqtSlot(int)
    def onRulerChange(self, ruler):
        ''' Simple callback to examine state of ruler button. 

        Args: 
            ruler - the boolean state of the button
        '''
        if ruler:
            self.ruler_picture.setPixmap(self.RULER_PIC)
        else:
            self.ruler_picture.clear()
    
    def fixedFamEntry(self, fam_name):
        self.family_select.setCurrentText(fam_name)
        index = self.family_select.currentIndex()
        self.family_select.setEnabled(False)
        self.disabled_entries.append('family_select')

    def onSubmit(self):
        ''' Callback for the submit button on the dialog. Packages all stored
        information and return it via the `submit` signal.
        '''
        self._char['name'] = self.name.text()
        selectedFamily = str(self.family_select.currentText())
        if selectedFamily == 'Select Family':
            selectedFamily = ''
        self._char['family'] = selectedFamily
        selectedSex = str(self.sex_selection.currentText())
        if selectedSex == 'Select Sex':
            selectedSex = ''
        self._char['sex'] = selectedSex
        birth, state = self.birth_date.getDate()
        if state:
            self._char['birth'] = birth
        else:
            self._char['birth'] = Time()
        death, state = self.death_date.getDate()
        if state:
            self._char['death'] = death
        else:
            self._char['death'] = Time() + Time(10, 10, 10)
        self._char['ruler'] = bool(self.ruler.checkState())
        selectedKingdom = str(self.kingdom_select.currentText())
        if selectedKingdom == 'Select Kingdom':
            selectedKingdom = ''
        self._char['kingdom'] = selectedKingdom 
        picture_path = self.picture_path.text()
        if not picture_path:
            if selectedSex == 'Male':
                picture_path = self.UNKNOWN_MALE_PATH
            elif selectedSex == 'Female':
                picture_path = self.UNKNOWN_FEMALE_PATH
            else:
                picture_path = self.DFLT_PROFILE_PATH
        self._char['picture_path'] = picture_path
        if self.picture.pixmap() and not self.picture.pixmap().isNull():
            self._char['__IMG__'] = self.picture.pixmap().toImage()
        else:
            self._char['__IMG__'] = qtg.QImage(picture_path)
        selectedRace = str(self.race_selection.currentText())
        if selectedRace == 'Select Race':
            selectedRace = ''
        self._char['race'] = selectedRace
        self.closeDialog()
        self.submitted.emit(self._char)
        
    def keyPressEvent(self, event):
        if event.key() == qtc.Qt.Key_Escape:
            self.closeDialog()
        super(CharacterCreator, self).keyPressEvent(event)

    def closeDialog(self):
        for entry in self.disabled_entries:
            getattr(self, entry).setEnabled(True)
        self.close()


