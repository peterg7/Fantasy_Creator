
# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg

# User-defined Modules
from .timelineGraphics import TimelineView
from Data.characterLookup import LookUpTableView

# craete Timeline scene
class TimelineTab(qtw.QMainWindow):

    timeline_loaded = qtc.pyqtSignal()

    def __init__(self, parent=None):
        super(TimelineTab, self).__init__(parent)
        self.setWindowFlags(qtc.Qt.Widget)

        # Setup and layout
        self.layout = qtw.QVBoxLayout()
        self.splitter = qtw.QSplitter()
        
        self.timelineview = TimelineView(self)
        self.tableview = LookUpTableView(self)

        self.tableview.setSortingEnabled(True)
        self.tableview.setColumnHidden(0, True) # hide ID column
        self.tableview.setVisibleCol(True)
        self.tableview.setSizeAdjustPolicy(qtw.QAbstractScrollArea.AdjustToContents)

        self.splitter.addWidget(self.timelineview)
        self.splitter.addWidget(self.tableview)
        self.splitter.setOrientation(qtc.Qt.Vertical)
        self.splitter.setContentsMargins(25, 0, 25, 0)

        # self.setLayout(self.layout)
        
        self.setCentralWidget(self.splitter)
        self.timeline_loaded.emit()


        # Create toolbar
        self.toolbar = qtw.QToolBar(self)
        self.toolbar.setIconSize(qtc.QSize(22, 22))
        self.toolbar.setSizePolicy(
            qtw.QSizePolicy.Expanding, 
            qtw.QSizePolicy.Preferred)
        self.addToolBar(qtc.Qt.TopToolBarArea, self.toolbar)

        self.toolbar.setFloatable(False)
        self.toolbar.setMovable(False)    
        

        self.toolbar.setToolButtonStyle(qtc.Qt.ToolButtonTextBesideIcon)
        startspacer = qtw.QLabel()
        startspacer.setFixedWidth(10)
        self.toolbar.addWidget(startspacer)

        # Add Event creation action
        add_event_act = self.toolbar.addAction(
            qtg.QIcon(':/toolbar-icons/add_event_icon.png'),
            'Add Event'
        )
        add_event_act.triggered.connect(self.timelineview.build_event)

        self.add_del_separator = self.toolbar.addSeparator()

        # Add remove event action
        self.del_event_act = self.toolbar.addAction(
            qtg.QIcon(':/toolbar-icons/remove_event_icon.png'), 
            'Remove Entry'
        )
        self.del_event_act.setShortcut(qtc.Qt.Key_Backspace)
        self.del_event_act.triggered.connect(self.timelineview.deleteActiveEvent)

        self.add_del_separator.setVisible(False)
        self.del_event_act.setVisible(False)
        self.del_event_act.setEnabled(False)
        self.timelineview.setEventDel.connect(self.setEventDelButton)

        middlespacer = qtw.QLabel()
        middlespacer.setSizePolicy(
            qtw.QSizePolicy.Expanding, 
            qtw.QSizePolicy.Preferred
        )
        self.toolbar.addWidget(middlespacer)

        # Add pan button
        pan_btn = qtw.QToolButton(self)
        pan_icon = qtg.QIcon()
        pan_icon.addPixmap(qtg.QPixmap(":/toolbar-icons/pan_icon.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        pan_btn.setIcon(pan_icon)
        pan_btn.setCheckable(True)
        pan_btn.setToolTip('Pan')
        pan_act = self.toolbar.addWidget(pan_btn)
        pan_btn.toggled.connect(self.timelineview.toggle_panning)

        # Add view fit action
        fit_view_btn = qtw.QToolButton(self)
        view_icon = qtg.QIcon()
        view_icon.addPixmap(qtg.QPixmap(':/toolbar-icons/fit_view_icon.png'), qtg.QIcon.Normal, qtg.QIcon.Off)
        fit_view_btn.setIcon(view_icon)
        fit_view_btn.setToolTip('Fit View')
        fit_view_act = self.toolbar.addWidget(fit_view_btn)
        fit_view_btn.pressed.connect(self.timelineview.fitWithBorder)

        # Setup Zoom Slider
        zoomicon = qtw.QLabel()
        zoomicon.setPixmap(qtg.QPixmap(':/toolbar-icons/zoom_icon.png').scaledToHeight(16))
        self.minZoom = TimelineView.MIN_ZOOM
        self.maxZoom = TimelineView.MAX_ZOOM
        self.zoomslider = qtw.QSlider()
        self.zoomslider.setRange(self.minZoom, self.maxZoom)
        self.zoomslider.setOrientation(qtc.Qt.Horizontal)
        self.zoomslider.setSizePolicy(
            qtw.QSizePolicy.Minimum,
            qtw.QSizePolicy.Preferred
        )
        self.zoomslider.setToolTip('Zoom')
        self.zoomslider.valueChanged.connect(self.timelineview.zoomEvent)
        self.timelineview.zoomChanged.connect(self.handleZoomChange)
        self.toolbar.addWidget(zoomicon)
        self.toolbar.addWidget(self.zoomslider)

        endspacer = qtw.QLabel()
        endspacer.setFixedWidth(10)
        self.toolbar.addWidget(endspacer)

        toolbutton_style = """
            QToolButton {
                font: 17px 'Baskerville';
            }
            QToolButton:pressed {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #dadbde, stop: 1 #f6f7fa);
            }
        """

        self.toolbar.setStyleSheet(toolbutton_style)
        

    def build_timeline(self, db):
        self.timelineview.connect_db(db)
        self.timelineview.init_timeline_view()
        self.timelineview.init_event_dialogs()
        self.tableview.adjustView()
        self.timeline_loaded.emit()
    
    @qtc.pyqtSlot(int)
    def handleZoomChange(self, value):
        self.zoomslider.blockSignals(True)
        self.zoomslider.setValue(value)
        self.zoomslider.blockSignals(False)

    @qtc.pyqtSlot(bool)
    def setEventDelButton(self, state):
        if not state:
            self.add_del_separator.setVisible(False)
            self.del_event_act.setVisible(False)
            self.del_event_act.setEnabled(False)
        else:
            self.add_del_separator.setVisible(True)
            self.del_event_act.setVisible(True)
            self.del_event_act.setEnabled(True)
        # self.toolbar.adjustSize()

    # def resizeEvent(self, event):
    #     self.timelineview.viewport().update()
    #     super(TimelineTab, self).resizeEvent(event)
    
    @qtc.pyqtSlot()
    def saveRequest(self):
        print('Saving timeline...')
    
    @qtc.pyqtSlot()
    def preferenceUpdate(self):
        print('Timeline: Received preference notification...')
    