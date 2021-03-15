''' Holds methods to support the TreeGraphics and Character modules

Contains various message box templates used by the TreeGraphics module. 
Stored in this file simple for organizational purposes

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

# 3rd Party
from tinydb import where

# User-defined Modules
# from .treeGraphics import TreeView
from .character import Character
from Mechanics.flags import CHAR_TYPE
from Dialogs.pictureEditor import PictureEditor, PictureLineEdit
from Mechanics.flags import TREE_ICON_DISPLAY, EVENT_TYPE
from Mechanics.storyTime import Time, DateLineEdit

# External resources
from resources import resources

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


class CharacterView(qtw.QGraphicsWidget):

    closed = qtc.pyqtSignal()
    CURRENT_SPAWN = qtc.QPoint(20, 60)  #NOTE: Magic Number

    def __init__(self, char_dict, parent=None):
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
            # label_string = f"<b>Birth</b>: {'{0} • {1} • {2}'.format(*self._char['birth'])}"
            label_string = f"<b>Birth</b>: {str(self._char['birth'])}"
        else:
            label_string = 'Birth: ...'
        self.birth_label.widget().setText(label_string)

        if self._char['death']:
            # label_string = f"<b>Death</b>: {'{0} • {1} • {2}'.format(*self._char['death'])}"
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

    def __init__(self, parent=None):
        super(CharacterViewLabel, self).__init__(parent)
        self.setTextFormat(qtc.Qt.RichText)
        self.setFont(qtg.QFont('Baskerville', 26))
        self.setCursor(qtc.Qt.OpenHandCursor)
    


# Character creation form
class CharacterCreator(qtw.QDialog):

    submitted = qtc.pyqtSignal(dict)
    closed = qtc.pyqtSignal()

    DFLT_PROFILE_PATH = ':/dflt-tree-images/default_profile.png'
    UNKNOWN_MALE_PATH = ':/dflt-tree-images/unknown_male.png'
    UNKNOWN_FEMALE_PATH = ':/dflt-tree-images/unknown_female.png'

    SEX_ITEMS = ["Select Sex"]
    RACE_ITEMS = ["Select Race"]
    KINGDOM_ITEMS = ["Select Kingdom"]
    FAMILY_ITEMS = ["Select Family"]

    IMAGES_PATH = 'tmp/' # TODO: FIX THIS

    def __init__(self, parent=None, editingChar=None):
        super(CharacterCreator, self).__init__(parent)
        # self.setSizePolicy(
        #     qtw.QSizePolicy.Preferred,
        #     qtw.QSizePolicy.Preferred
        # )
        self.setAttribute(qtc.Qt.WA_DeleteOnClose)
        self.setModal(True) # CAUSES BUG 

        self.setMinimumSize(415, 500)
        self.setMaximumSize(415, 700)

        self.RULER_PIC = qtg.QPixmap(Character.RULER_PIC_PATH)
        self._id = 0

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


        self.on_ruler_change(self.ruler.checkState())

        # Connect signals
        self.sex_selection.currentTextChanged.connect(self.on_sex_change)
        self.race_selection.currentTextChanged.connect(self.on_race_change)
        self.family_select.currentTextChanged.connect(self.on_fam_change)
        self.kingdom_select.currentTextChanged.connect(self.on_kingdom_change)
        self.ruler.stateChanged.connect(self.on_ruler_change)
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
        if editingChar:
            self._char = editingChar
            self.setWindowTitle(self._char['name'])
            self.parseExistingChar()
        else:
            self._char = {}
            self.setWindowTitle('Create a new character')
        #self.setVisible(True)
    

    def parseExistingChar(self):
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
        filename, _ = qtw.QFileDialog.getOpenFileName(
            self,
            'Select an image to open...',
            qtc.QDir.homePath(),
            'Images (*.png *.jpeg *.jpg *.xpm)'
        )
        if filename:
            self.picture_dialog = PictureEditor(filename, EVENT_TYPE.CHAR, self)
            self.picture_dialog.submitted.connect(self.store_new_pic)
            self.picture_dialog.show()

    @qtc.pyqtSlot(str, qtg.QPixmap)
    def store_new_pic(self, filename, pix):
        self.picture_path.setText(filename)
        self.picture.setPixmap(pix)


    
    @qtc.pyqtSlot(str)
    def on_kingdom_change(self, text):
        if text == 'New...':
            text, ok = qtw.QInputDialog.getText(self, 'Define new kingdom', 'Enter kingdom:')
            if ok:
                self.kingdom_select.addItem(text)
                self.KINGDOM_ITEMS.insert(-1, text)
                self.kingdom_select.setCurrentText(text)
            else:
                self.kingdom_select.setCurrentIndex(0)
    
    @qtc.pyqtSlot(str)
    def on_fam_change(self, text):
        if text == 'New...':
            text, ok = qtw.QInputDialog.getText(self, 'New Family', 'Enter family name:')
            if ok:
                self.family_select.addItem(text)
                self.FAMILY_ITEMS.insert(-1, text)
                self.family_select.setCurrentText(text)
            else:
                self.family_select.setCurrentIndex(0)

    @qtc.pyqtSlot(str)
    def on_race_change(self, text):
        if text == 'Other...':
            text, ok = qtw.QInputDialog.getText(self, 'Define other race', 'Enter race:')
            if ok:
                self.race_selection.addItem(text)
                self.RACE_ITEMS.insert(-1, text)
                self.race_selection.setCurrentText(text)
            else:
                self.race_selection.setCurrentIndex(0)
    
    @qtc.pyqtSlot(str)
    def on_sex_change(self, text):
        if text == 'Other...':
            text, ok = qtw.QInputDialog.getText(self, 'Define other sex', 'Enter sex:')
            if ok:
                self.sex_selection.addItem(text)
                self.SEX_ITEMS.insert(len(self.SEX_ITEMS)-1, text)
                self.sex_selection.setCurrentText(text)
            else:
                self.sex_selection.setCurrentIndex(0)
    
    @qtc.pyqtSlot(int)
    def on_ruler_change(self, ruler):
        if ruler:
            self.ruler_picture.setPixmap(self.RULER_PIC)
        else:
            self.ruler_picture.clear()


    def onSubmit(self):
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
        self.close()
        self.submitted.emit(self._char)
        
    
    def keyPressEvent(self, event):
        if event.key() == qtc.Qt.Key_Escape:
            self.close()
        super(CharacterCreator, self).keyPressEvent(event)



