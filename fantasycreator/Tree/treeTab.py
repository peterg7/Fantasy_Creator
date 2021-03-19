''' Tab module that holds the tree graphics

Created by MainWindow at launch, this class connects signals from the tree
to other modules in the program as well as sets up the general graphics of this
tab such as toolbars, control panel, etc.

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
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg

# Built-in Modules
import logging

# User-defined Modules
from .treeGraphics import TreeView
from .tree import Tree
from fantasycreator.Data.characterLookup import LookUpTableView
from fantasycreator.Mechanics.controlPanel import ControlPanel

# Create Tree tab 
class TreeTab(qtw.QMainWindow):

    tree_loaded = qtc.pyqtSignal()

    def __init__(self, parent=None):
        super(TreeTab, self).__init__(parent)
        self.setWindowFlags(qtc.Qt.Widget)

        # Setup and layout
        self.layout = qtw.QHBoxLayout()
        self.splitter = qtw.QSplitter()

        self.treeview = TreeView(self)

        self.tableview = LookUpTableView(self)
        
        self.splitter.addWidget(self.treeview)
        self.splitter.addWidget(self.tableview)
        self.splitter.setOrientation(qtc.Qt.Vertical)
        self.splitter.setContentsMargins(25, 0, 0, 0)

        # self.setLayout(self.layout)

        self.setCentralWidget(self.splitter)
        self.tree_loaded.emit()
        # self.layout.addWidget(self.splitter)
        # self.setLayout(self.layout)


        ## Control Panel
        self.control_panel = ControlPanel(self)
        self.addDockWidget(qtc.Qt.RightDockWidgetArea, self.control_panel)
        self.control_panel.filtersChanged.connect(self.handleFilters)
        self.control_panel.selectionChanged.connect(self.handleFilters)
        self.control_panel.visibilityChanged.connect(self.handlePanelViz)
        # self.control_panel.topLevelChanged.connect(lambda x: self.handlePanelViz(not x))
        self.control_panel.dockLocationChanged.connect(self.handlePanelLoc)

        # Connect signals
        self.treeview.tree.familiesAdded.connect(self.control_panel.updateSelections)
        self.treeview.tree.familiesRemoved.connect(self.control_panel.updateSelections)
        self.treeview.tree.kingdomsAdded.connect(self.control_panel.updateSelections)
        self.treeview.tree.kingdomsRemoved.connect(self.control_panel.updateSelections)
        self.treeview.tree.requestFilterChange.connect(self.control_panel.updateFilters)

        # Create toolbar
        self.toolbar = qtw.QToolBar(self)
        self.toolbar.setIconSize(qtc.QSize(22, 22))
        self.toolbar.setSizePolicy(
            qtw.QSizePolicy.Expanding, 
            qtw.QSizePolicy.Preferred)
        self.addToolBar(qtc.Qt.TopToolBarArea, self.toolbar)

        self.toolbar.setFloatable(False)
        self.toolbar.setMovable(False)

        ## Toolbar
        self.toolbar.setToolButtonStyle(qtc.Qt.ToolButtonTextBesideIcon)
        startspacer = qtw.QLabel()
        startspacer.setFixedWidth(10)
        self.toolbar.addWidget(startspacer)

        # Add family creation action
        add_char_act = self.toolbar.addAction(
            qtg.QIcon(':/toolbar-icons/add_family_icon.png'),
            'Add Family'
        )
        add_char_act.triggered.connect(self.treeview.createFamily)
        
        self.add_add_separator = self.toolbar.addSeparator()

        # Add character creation action
        self.add_char_act = self.toolbar.addAction(
            qtg.QIcon(':/toolbar-icons/add_char_icon.png'),
            'Add Character'
        )
        self.add_char_act.triggered.connect(self.treeview.createCharacter)
        self.treeview.tree.hideAddCharacter.connect(self.setCharAddBtn)

        self.add_del_separator = self.toolbar.addSeparator()

        # Add character remove action
        self.del_char_act = self.toolbar.addAction(
            qtg.QIcon(':/toolbar-icons/remove_char_icon.png'), 
            'Remove Entry'
        )
        self.del_char_act.setShortcut(qtc.Qt.Key_Backspace)
        self.del_char_act.triggered.connect(lambda: logging.info('In Construction!'))

        self.add_del_separator.setVisible(False)
        self.del_char_act.setVisible(False)
        self.del_char_act.setEnabled(False)
        self.treeview.setCharDel.connect(self.setCharDeleteBtn)

        middlespacer = qtw.QLabel()
        middlespacer.setSizePolicy(
            qtw.QSizePolicy.Expanding, 
            qtw.QSizePolicy.Preferred
        )
        self.toolbar.addWidget(middlespacer)

        # Add control panel button
        self.panel_btn = qtw.QToolButton(self)
        panel_icon = qtg.QIcon()
        panel_icon.addPixmap(qtg.QPixmap(":/toolbar-icons/control_panel.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.panel_btn.setIcon(panel_icon)
        self.panel_btn.setToolTip('Show Control Panel')
        self.panel_act = self.toolbar.addWidget(self.panel_btn)
        self.panel_btn.pressed.connect(self.control_panel.show)
        self.panel_btn.setVisible(False)
        self.panel_btn.setEnabled(False)
    
        # Add pan button
        pan_btn = qtw.QToolButton(self)
        pan_icon = qtg.QIcon()
        pan_icon.addPixmap(qtg.QPixmap(":/toolbar-icons/pan_icon.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        pan_btn.setIcon(pan_icon)
        pan_btn.setCheckable(True)
        pan_btn.setToolTip('Pan')
        pan_act = self.toolbar.addWidget(pan_btn)
        pan_btn.toggled.connect(self.treeview.togglePanning)

        # Add view fit action
        fit_view_btn = qtw.QToolButton(self)
        view_icon = qtg.QIcon()
        view_icon.addPixmap(qtg.QPixmap(':/toolbar-icons/fit_view_icon.png'), qtg.QIcon.Normal, qtg.QIcon.Off)
        fit_view_btn.setIcon(view_icon)
        fit_view_btn.setToolTip('Fit View')
        fit_view_act = self.toolbar.addWidget(fit_view_btn)
        fit_view_btn.pressed.connect(self.treeview.fitWithBorder)

        # Setup Zoom Slider
        zoomicon = qtw.QLabel()
        zoomicon.setPixmap(qtg.QPixmap(':/toolbar-icons/zoom_icon.png').scaledToHeight(16))
        self.minZoom = TreeView.MIN_ZOOM
        self.maxZoom = TreeView.MAX_ZOOM
        self.zoomslider = qtw.QSlider()
        self.zoomslider.setRange(self.minZoom, self.maxZoom)
        self.zoomslider.setOrientation(qtc.Qt.Horizontal)
        self.zoomslider.setSizePolicy(
            qtw.QSizePolicy.Minimum,
            qtw.QSizePolicy.Preferred
        )
        self.zoomslider.setToolTip('Zoom')
        self.zoomslider.valueChanged.connect(self.treeview.zoomEvent)
        self.treeview.zoomChanged.connect(self.handleZoomChange)
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



    ## Auxiliary Functions ##

    def build_tree(self, db):
        self.treeview.connectDB(db)
        self.treeview.initTree()
        self.tableview.adjustView()
        self.tree_loaded.emit()
    ## Custom Slots ##

    @qtc.pyqtSlot(int, str)
    @qtc.pyqtSlot(int, int)
    def handleFilters(self, flag_type, flag):
        self.treeview.tree.filterTree(flag_type, flag)

    @qtc.pyqtSlot(int)
    def handleZoomChange(self, value):
        self.zoomslider.blockSignals(True)
        self.zoomslider.setValue(value)
        self.zoomslider.blockSignals(False)

    @qtc.pyqtSlot(bool)
    def handlePanelViz(self, viz_state):
        if viz_state:
            self.panel_act.setVisible(False)
            self.panel_act.setEnabled(False)
            if self.dockWidgetArea(self.control_panel) == qtc.Qt.RightDockWidgetArea:
                self.splitter.setContentsMargins(25, 0, 0, 0)
            elif self.dockWidgetArea(self.control_panel) == qtc.Qt.LeftDockWidgetArea:
                self.splitter.setContentsMargins(0, 0, 25, 0)
            else:
                self.splitter.setContentsMargins(25, 0, 25, 0)
        else:
            self.splitter.setContentsMargins(25, 0, 25, 0)
            self.panel_act.setVisible(True)
            self.panel_act.setEnabled(True)

    
    @qtc.pyqtSlot(qtc.Qt.DockWidgetArea)
    def handlePanelLoc(self, loc):
        if loc == qtc.Qt.RightDockWidgetArea and self.control_panel.isVisible():
            self.splitter.setContentsMargins(25, 0, 0, 0)
        elif loc == qtc.Qt.LeftDockWidgetArea and self.control_panel.isVisible():
            self.splitter.setContentsMargins(0, 0, 25, 0)
        else:
            self.splitter.setContentsMargins(25, 0, 25, 0)



    @qtc.pyqtSlot(bool)
    def setCharDeleteBtn(self, state):
        self.add_del_separator.setVisible(state)
        self.del_char_act.setVisible(state)
        self.del_char_act.setEnabled(state)

    @qtc.pyqtSlot(bool)
    def setCharAddBtn(self, state):
        self.add_add_separator.setVisible(state)
        self.add_char_act.setVisible(state)
        self.add_char_act.setEnabled(state)

    @qtc.pyqtSlot()
    def saveRequest(self):
        # print('Saving tree...')
        logging.debug('Saving tree...')
    
    @qtc.pyqtSlot()
    def preferenceUpdate(self):
        # print('Tree: Received preference notification...')
        logging.debug('Received preference notification...')
        self.tree.updatePreferences()