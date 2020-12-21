# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

# Built-in Packages
from datetime import datetime
import smtplib


class BugReporter(qtw.QDialog):

    def __init__(self, parent=None):
        super(BugReporter, self).__init__(parent)
        self.setSizePolicy(
            qtw.QSizePolicy.Fixed,
            qtw.QSizePolicy.Fixed
        )
        self.setMinimumSize(qtc.QSize(400, 375))
        self.setMaximumSize(qtc.QSize(400, 375))

        layout = qtw.QGridLayout()
        self.bug_title = qtw.QLineEdit()
        self.bug_title.setPlaceholderText('Title')
        self.bug_title.setFont(qtg.QFont('Baskerville', 22))

        self.timestamp_label = qtw.QLabel(str(datetime.now().strftime('%c')))
        self.timestamp_label.setFont(qtg.QFont('Baskerville', 16))

        self.crash_button = qtw.QCheckBox('Causes a\nCrash?')

        self.description_entry = qtw.QTextEdit()
        self.description_entry.setPlaceholderText("Description")

        self.submit_button = qtw.QPushButton(
            'Submit', 
            pressed=self.onSubmit
        )
        self.cancel_button = qtw.QPushButton(
            'Cancel',
            pressed=self.close
        )

        layout.addWidget(self.bug_title, 0, 0, 2, 1)
        layout.addWidget(self.timestamp_label, 1, 0, 1, 1)
        layout.addWidget(self.crash_button, 1, 3, 1, 1)
        layout.addWidget(self.description_entry, 2, 0, 2, 4)
        layout.addWidget(self.cancel_button, 4, 2, 1, 1)
        layout.addWidget(self.submit_button, 4, 3, 1, 1)
        
        self.submit_button.setEnabled(False)
        self.bug_title.textChanged.connect(self.onTextChange)
        self.description_entry.textChanged.connect(self.onTextChange)

        self.setWindowTitle('Report a bug')
        self.setLayout(layout)

    def onTextChange(self):
        if self.bug_title.text() and self.description_entry.toPlainText():
            self.submit_button.setEnabled(True)
        else:
            self.submit_button.setEnabled(False)

    def onSubmit(self):
        message = self.bug_title.text() + '\n' + self.description_entry.toPlainText()
        print(message)
        self.sendReport()
        self.close()
    
    def sendReport(self):
        sender_addr = 'fantasycreatorbot@gmail.com'
        sender_pswd = 'GYjF@&-y%P5y'
        receiver_addr = 'pgish97@gmail.com'
        subject = f'Bug: {self.bug_title.text()}'
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(sender_addr, sender_pswd)
        message = f'''Subject:{self.bug_title.text()}\n
        {self.timestamp_label.text()}\t{'Crash' if self.crash_button.isChecked() else 'No Crash'}\n
        {self.description_entry.toPlainText()}'''
        server.sendmail(sender_addr, receiver_addr, message)
        server.close()

