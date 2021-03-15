# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc


class AboutWindow(qtw.QDialog):

    MESSAGE = """
    Bring your stories to life!
    Brought to you by Fantastical Studios.\n 
    JK it's me, Peter. 
    Happy 22nd Birthday! 
    I hope this can help you follow
    your dreams :). 
    """

    def __init__(self, parent=None):
        super(AboutWindow, self).__init__(parent)
        self.setSizePolicy(
            qtw.QSizePolicy.Fixed,
            qtw.QSizePolicy.Fixed
        )
        self.setMinimumSize(qtc.QSize(300, 250))
        self.setMaximumSize(qtc.QSize(300, 250))

        layout = qtw.QVBoxLayout()
        
        self.title_label = qtw.QLabel('Fantasy Creator')
        self.title_label.setFont(qtg.QFont('Baskerville', 26, italic=True))
        self.title_label.setAlignment(qtc.Qt.AlignCenter)
        
        self.about_msg = qtw.QLabel(self)
        self.about_msg.setSizePolicy(
            qtw.QSizePolicy.Expanding,
            qtw.QSizePolicy.Expanding
        )
        self.about_msg.setWordWrap(True)
        self.about_msg.setText(AboutWindow.MESSAGE)
        self.about_msg.setFont(qtg.QFont('Baskerville', 16))

        layout.addWidget(self.title_label, qtc.Qt.AlignCenter)
        layout.addWidget(self.about_msg)

        self.setLayout(layout)