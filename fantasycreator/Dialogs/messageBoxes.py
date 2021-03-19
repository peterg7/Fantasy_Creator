
# PyQt 
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

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

class AutoCloseMsgBox(qtw.QMessageBox):

    def __init__(self, parent=None):
        super(AutoCloseMsgBox, self).__init__(parent)
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
        w = AutoCloseMsgBox()
        w.timeout = timeout_secs
        w.setText(message)
        if window_title:
            w.setWindowTitle(window_title)
        if icon:
            w.setIcon(icon)
        if buttons:
            w.setStandardButtons(buttons)
        w.exec()
