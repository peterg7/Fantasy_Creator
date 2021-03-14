
# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg

# Built-in Modules
import sys
import time

# External resources
from resources import resources

# Opening window
class WelcomeWindow(qtw.QDialog):

    new_book = qtc.pyqtSignal()
    open_existing = qtc.pyqtSignal(str)
    open_sample = qtc.pyqtSignal()
    closed = qtc.pyqtSignal()

    INIT_WIDTH = 960
    INIT_HEIGHT = 640

    def __init__(self, width, height, parent=None):
        super(WelcomeWindow, self).__init__(parent)
        
        self.setSizePolicy(
            qtw.QSizePolicy.Preferred,
            qtw.QSizePolicy.Preferred
        )
        # self.setModal(True)
        self.setWindowTitle('Welcome!')
        self.setFixedSize(WelcomeWindow.INIT_WIDTH, WelcomeWindow.INIT_HEIGHT)
        
        # self.background = qtg.QPixmap(':/background-images/welcome_background.png')
        self.background_movie = qtg.QMovie(':background-images/welcome_screen.gif')
        self.background_movie.setCacheMode(qtg.QMovie.CacheAll)
        self.background_movie.jumpToFrame(0)
        self.background_movie.setScaledSize(qtc.QSize(WelcomeWindow.INIT_WIDTH, WelcomeWindow.INIT_HEIGHT))
        # background_size = background_movie.currentImage().size()
        self.background_aspect = WelcomeWindow.INIT_WIDTH / WelcomeWindow.INIT_HEIGHT

        # self.background_label = qtw.QLabel()
        # self.background_label.setAlignment(qtc.Qt.AlignCenter)
        # self.resizeEvent()

        # self.background_label.setMovie(background_movie)
        self.background_movie.frameChanged.connect(self.paintNewFrame)
        self.background_movie.stateChanged.connect(self.loopMovie)
        self.background_movie.start()

        # self.background = self.background_label.grab()


        # Set up layout
        layout = qtw.QGridLayout()

        heading = qtw.QLabel('Fantasy Creator')
        heading.setAttribute(qtc.Qt.WA_TranslucentBackground)
        heading_font = qtg.QFont('Apple Chancery', 105, qtg.QFont.ExtraBold)
        heading.setFont(heading_font)
        heading.setAlignment(qtc.Qt.AlignCenter)
        heading.setStyleSheet("QLabel {color : #ffa217}")
        layout.addWidget(heading, 1, 1, 2, 6)

        options_font = qtg.QFont('Baskerville', 25)

        self.new_book_btn = qtw.QPushButton('New Book')
        self.new_book_btn.setFont(options_font)
        self.new_book_btn.clicked.connect(self.handleNewBook)
        layout.addWidget(self.new_book_btn, 3, 3, 1, 2)

        self.open_book_btn = qtw.QPushButton('Open Existing')
        self.open_book_btn.setFont(options_font)
        self.open_book_btn.clicked.connect(self.handleOpenBook)
        layout.addWidget(self.open_book_btn, 4, 3, 1, 2)

        self.open_sample_btn = qtw.QPushButton('Sample')
        self.open_sample_btn.setFont(options_font)
        self.open_sample_btn.clicked.connect(self.handleOpenSample)
        layout.addWidget(self.open_sample_btn, 5, 3, 1, 2)

        spacer = qtw.QSpacerItem(0, 0)
        layout.addItem(spacer, 7, 0, 1, 1)

        self.progress_bar = qtw.QProgressBar(self)
        self.progress_bar.setOrientation(qtc.Qt.Horizontal)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(8)
        self.current_progress = 0
        # self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar, 2, 2, 1, 4)


        self.cancel = qtw.QPushButton(
            'Exit',
            clicked=sys.exit
        )
        self.cancel.setFont(qtg.QFont('Baskerville', 18))
        layout.addWidget(self.cancel, 7, 7, 1, 1)

        for col in range(8):
            layout.setColumnStretch(col, 1)

        # layout.addWidget(self.background_label, 0, 0, 7, 7)
        self.setLayout(layout)
        self.progress_bar.setVisible(False)
        

    def launchApp(self, signal, args=None):
        self.progress_bar.setVisible(True)
        self.new_book_btn.setVisible(False)
        self.open_book_btn.setVisible(False)
        self.open_sample_btn.setVisible(False)
        self.cancel.setVisible(False)
        app = qtw.QApplication.instance()
        app.processEvents()
        if args:
            signal.emit(args)
        else:
            signal.emit()

    def incrementProgressBar(self):
        self.current_progress += 1
        self.progress_bar.setValue(self.current_progress)
        app = qtw.QApplication.instance()
        app.processEvents()
    

    def closeEvent(self, event):
        self.closed.emit()
        super(WelcomeWindow, self).closeEvent(event)    
    
    def handleOpenBook(self):
        filename, _ = qtw.QFileDialog.getOpenFileName(
            self,
            "Select a file to open...",
            qtc.QDir.currentPath(), # static method returning user's home path
            'JSON Files (*.json) ;;Text Files (*.txt) ;;All Files (*)',
            'JSON Files (*.json)'
        )
        if filename:
            self.launchApp(self.open_existing, filename)

    def handleNewBook(self):
        self.launchApp(self.new_book)

    def handleOpenSample(self):
        self.launchApp(self.open_sample)
    
    # def resizeEvent(self, event):
    #     bkgnd_img = self.background.scaled(self.size(), 
    #                     qtc.Qt.IgnoreAspectRatio, qtc.Qt.SmoothTransformation)
    #     palette = qtg.QPalette()
    #     palette.setBrush(qtg.QPalette.Window, qtg.QBrush(bkgnd_img))
    #     self.setPalette(palette)

    #     super(WelcomeWindow, self).resizeEvent(event)

    # def resizeEvent(self, event=None):
    #     rect = self.geometry()

    #     background_movie = self.background_label.movie()
    #     if background_movie:
    #         width = rect.height() * self.background_aspect
    #         if width <= rect.width():
    #             size = qtc.QSize(width, rect.height())
    #         else:
    #             height = rect.width() / self.background_aspect
    #             size = qtc.QSize(rect.width(), height)

    #         background_movie.setScaledSize(size)

    #         palette = qtg.QPalette()
    #         palette.setBrush(qtg.QPalette.Window, qtg.QBrush(self.background))
    #         self.setPalette(palette)

    #     super(WelcomeWindow, self).resizeEvent(event)
    
    def paintEvent(self, event):
        current_frame = self.background_movie.currentPixmap()
        frame_rect = current_frame.rect()

        frame_rect.moveCenter(self.rect().center())
        if frame_rect.intersects(event.rect()):
            painter = qtg.QPainter(self)
            painter.drawPixmap(
                frame_rect.left(),
                frame_rect.top(),
                current_frame)
    
    def paintNewFrame(self, frame_num):
        # print(frame_num, self.background_movie.state())
        # # if self.background_movie.state() == qtg.QMovie.NotRunning:
        # #     self.background_movie.start()
        self.repaint()
    
    def loopMovie(self, state):
        if state == qtg.QMovie.NotRunning:
            self.background_movie.start()
