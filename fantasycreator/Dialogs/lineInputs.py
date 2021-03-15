    
# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc


class UserLineInput(qtw.QDialog):
    
    # submitted = qtc.pyqtSignal()

    def __init__(self, window_title, prompt, parent=None):
        super(UserLineInput, self).__init__(parent)
        self.setWindowTitle(window_title)

        layout = qtw.QVBoxLayout()
        prompt_label = qtw.QLabel(prompt)
        prompt_label.setFont(qtg.QFont('Baskerville', 20))

        self.name_entry = qtw.QLineEdit(self)
        self.name_entry.setFont(qtg.QFont('Baskerville', 18))

        button_layout = qtw.QHBoxLayout()
        self.submit_btn = qtw.QPushButton(
            'Submit',
            clicked=self.handleInput
        )
        self.submit_btn.setDefault(True)
        self.submit_btn.setFont(qtg.QFont('Baskerville', 16))
        self.cancel_btn = qtw.QPushButton(
            'Cancel',
            clicked=self.cancelReq
        )
        self.cancel_btn.setAutoDefault(False)
        self.cancel_btn.setFont(qtg.QFont('Baskerville', 16))
        button_layout.addWidget(self.cancel_btn, qtc.Qt.AlignLeft)
        button_layout.addWidget(self.submit_btn, qtc.Qt.AlignRight)

        layout.addWidget(prompt_label)
        layout.addWidget(self.name_entry)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.input = None
        self.okay = True
    
    def cancelReq(self):
        self.okay = False
        self.done(0)
    
    def handleInput(self):
        self.input = self.name_entry.text()
        self.done(0)

    @staticmethod
    def requestInput(window_title, prompt, parent):
        window = UserLineInput(window_title, prompt, parent)
        window.exec_()
        return window.input, window.okay