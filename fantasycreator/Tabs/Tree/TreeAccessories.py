''' Holds methods to support the TreeGraphics module

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

# 3rd Party
from tinydb import where

# User-defined Modules
from flags import *
from treeGraphics import TreeView

# External resources
import resources

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

