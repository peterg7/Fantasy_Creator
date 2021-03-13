
# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtPrintSupport as qps

# Built-in Modules
import types

# 3rd Party
# from tinydb import where

# User-defined Modules
from mapBuilderGraphics import MapView
from mapBuilderUI import Ui_MapBuilderTab
from mapBuilderObjects import TimestampList
from animator import AnimatorControlBar
from storyTime import Time, TimeConstants

# Create Map Tab
class MapBuilderTab(qtw.QMainWindow, Ui_MapBuilderTab):

    map_loaded = qtc.pyqtSignal()

    COLORS = ['#fb803c', '#7c4002',
                '#fffc91', '#7f7e45',
                '#8481c4', '#4f4c8a',
                '#b92fc2', '#81067a',  
                '#0000fa', '#040079',
                '#0a7cf6', '#074a91', 
                '#0bf8ee', '#037e7b',
                #'#42eda9', '#007e03',
                '#08fb01', '#05403c',
                '#f70406', '#820300',
                '#c1c1c1', '#82817f',
                '#ffffff', '#000000']
    # '#dc137d', 
    # '#7e07f9', 
    #'#fffd00', 
    #'#868417',
    FONT_SIZES = [7, 8, 9, 10, 11, 12, 13, 14, 18, 24, 36, 48, 64, 72, 96, 144, 288]

    MODES = [
        'select', 'pan',
        'undo', 'img',
        'eraser', 'dropper',
        'pen', 'brush',
        'spray', 'text',
        'line', 'polyline',
        'rect',
        'ellipse'
    ]

    LOCATIONS = {
        'castle': ':/map-icons/castle-icon.png',
        'village': ':/map-icons/village-icon.png',
        'port': ':/map-icons/anchor.png',
        'otherLoc': ':/map-icons/misc-location.png',
        'camp': ':/map-icons/camp-icon.png'
    }


    def __init__(self, parent=None):
        super(MapBuilderTab, self).__init__(parent)
        self.setWindowFlags(qtc.Qt.Widget)
        self.setupUi(self)

        # Replace canvas placeholder from QtDesigner.
        self.mapview = MapView(self)
        self.mapview.viewport().setMouseTracking(True)

        old_view = self.mainLayout.replaceWidget(self.view, self.mapview)
        self.view.setParent(None)
        del self.view
        del old_view

        # Replace animator placeholder
        self.animator_controls = AnimatorControlBar(self)
        old_controls = self.middle_main_vertical_layout.replaceWidget(self.animateWidget,
                                                            self.animator_controls)
        self.animateWidget.setParent(None)
        del self.animateWidget
        del old_controls
        self.animator_controls.setEnabled(False)

        self.timestampList = TimestampList(self)
        old_list = self.timestamps_layout.replaceWidget(self.tempList, self.timestampList)
        self.tempList.setParent(None)
        del self.tempList
        del old_list

        self.map_loaded.emit()

        # Setup the mode buttons
        self.mode_group = qtw.QButtonGroup(self)
        self.mode_group.setExclusive(True)
        # self.mode_group = ButtonGroup(self)

        for mode in self.MODES:
            btn = getattr(self, '%sButton' % mode)
            # btn.pressed.connect(lambda mode=mode: self.mapview.set_mode(mode))
            btn.pressed.connect(lambda mode=mode: self.handleButtonPress(mode, 'drawing'))
            self.mode_group.addButton(btn)
        

        # NOT IMPLEMENTED BUTTONS:
        self.undoButton.setEnabled(False)
        self.imgButton.setEnabled(False)
        self.removeCharButton.setEnabled(False)


        self.MODES.append('location')

        # Setup embedded buttons
        for mode, stamp_path in self.LOCATIONS.items():
            btn = getattr(self, '%sButton' % mode)
            btn.pressed.connect(lambda mode=mode: self.handleButtonPress('location', mode))
            btn.pressed.connect(lambda stamp_path=stamp_path: self.mapview.set_current_stamp(stamp_path))
            self.mode_group.addButton(btn)
        
        self.existingLocButton.clicked.connect(lambda: self.handleButtonPress('location', 'existingLoc'))
        self.existingLocButton.clicked.connect(self.mapview.launchLocationSelect)
        self.mode_group.addButton(self.existingLocButton)

        self.MODES.append('character')
        
        self.addCharButton.clicked.connect(lambda : self.handleButtonPress('character', 'addChar'))
        self.addCharButton.clicked.connect(self.mapview.launchCharacterSelect)
        self.mode_group.addButton(self.addCharButton)

        self.selectButton.setChecked(True)
        self.current_button = self.selectButton

        self.CURSORS = {
            'eraser': qtg.QCursor(qtg.QPixmap(":/map-icons/eraser.png"), 0, 15),
            'dropper': qtg.QCursor(qtg.QPixmap(":/map-icons/pipette.png"), 0, 15),
            'pen': qtg.QCursor(qtg.QPixmap(":/map-icons/pencil.png"), 0, 15),
            'brush': qtg.QCursor(qtg.QPixmap(":/map-icons/paint-brush.png"), 0, 15),
            'spray': qtg.QCursor(qtg.QPixmap(":/map-icons/spray.png"), 0, 0),
            'text': qtc.Qt.IBeamCursor,
            'castle': qtg.QCursor(
                qtg.QPixmap(":/map-icons/castle-icon.png").scaledToHeight(50, qtc.Qt.SmoothTransformation), -1, -1),
            'village': qtg.QCursor(
                qtg.QPixmap(":/map-icons/village-icon.png").scaledToHeight(50, qtc.Qt.SmoothTransformation), -1, -1),
            'port': qtg.QCursor(
                qtg.QPixmap(":/map-icons/anchor.png").scaledToHeight(50, qtc.Qt.SmoothTransformation), -1, -1),
            'camp': qtg.QCursor(
                qtg.QPixmap(":/map-icons/camp-icon.png").scaledToHeight(50, qtc.Qt.SmoothTransformation), -1, -1),
            'existingLoc': qtg.QCursor(
                qtg.QPixmap(":/map-icons/known-location-icon.png").scaledToHeight(50, qtc.Qt.SmoothTransformation), -1, -1),
            'otherLoc': qtg.QCursor(
                qtg.QPixmap(":/map-icons/misc-location.png").scaledToHeight(50, qtc.Qt.SmoothTransformation), -1, -1),
            'addChar': qtg.QCursor(
                qtg.QPixmap(":/toolbar-icons/add_char_icon.png").scaledToHeight(50, qtc.Qt.SmoothTransformation), -1, -1),
            'select': qtc.Qt.ArrowCursor,
            'pan': qtc.Qt.OpenHandCursor
        }

        # Allow canvas to clear button selection
        self.mapview.scene.canvas.clear_mode.connect(self.handleButtonPress)

        # Setup the color selection buttons.
        self.primaryButton.pressed.connect(lambda: self.choose_color(self.set_primary_color))
        self.secondaryButton.pressed.connect(lambda: self.choose_color(self.set_secondary_color))

        # Initialize button colours.
        for n, hex in enumerate(self.COLORS, 1):
            btn = getattr(self, 'colorButton_%d' % n)
            btn.setStyleSheet('QPushButton { background-color: %s; }' % hex)
            btn.hex = hex  # For use in the event below

            def patch_mousePressEvent(self_, e):
                if e.button() == qtc.Qt.LeftButton:
                    self.set_primary_color(self_.hex)

                elif e.button() == qtc.Qt.RightButton:
                    self.set_secondary_color(self_.hex)

            btn.mousePressEvent = types.MethodType(patch_mousePressEvent, btn)

        # Setup animator
        year_index = TimeConstants.NAMED_ORDER['year']
        min_year, max_year = getattr(TimeConstants, f'TIME_{year_index}_RNG')
        self.animator_controls.initControls(min_year, max_year)
        self.mapview.visual_timestamp.connect(self.addTimestamp)
        self.animateButton.clicked.connect(lambda x: self.animator_controls.setActive(x))
        self.animator_controls.scene_change.connect(self.mapview.animationDirector)

        self.timestampList.removed_timestamp.connect(self.mapview.removeTimestamp)

        # Initialize animation timer.
        self.timer = qtc.QTimer()
        self.timer.timeout.connect(self.mapview.scene.canvas.on_timer)
        self.timer.setInterval(100)
        self.timer.start()

        # Setup to agree with Canvas
        self.set_primary_color('#000000')
        self.set_secondary_color('#ffffff')

        # Signals for canvas-initiated color changes (dropper)
        self.mapview.scene.canvas.primary_color_updated.connect(self.set_primary_color)
        self.mapview.scene.canvas.secondary_color_updated.connect(self.set_secondary_color)
        
        # Setup up existing locations filter
        self.show_known_locs.stateChanged.connect(self.mapview.scene_coordinator)

        # Setup the toolbar
        startspacer = qtw.QLabel()
        startspacer.setFixedWidth(10)
        self.mainToolbar.addWidget(startspacer)

        self.mainToolbar.addAction(self.actionNewImage)
        self.actionNewImage.triggered.connect(self.newMap)

        self.mainToolbar.addAction(self.actionOpenImage)
        self.actionOpenImage.triggered.connect(self.openImage)
        
        self.mainToolbar.addAction(self.actionExportImage)
        self.actionExportImage.triggered.connect(self.exportMap)

        self.mainToolbar.addAction(self.actionPrintImage)
        self.actionPrintImage.triggered.connect(self.printMap)

        self.mainToolbar.addAction(self.actionClearImage) # Confirm with user
        self.actionClearImage.triggered.connect(self.sweepMap)

        middlespacer_1 = qtw.QLabel()
        middlespacer_1.setSizePolicy(
            qtw.QSizePolicy.Expanding, 
            qtw.QSizePolicy.Preferred
        )
        self.mainToolbar.addWidget(middlespacer_1)

        self.fontselect = qtw.QFontComboBox()
        self.mainToolbar.addWidget(self.fontselect)
        self.fontselect.currentFontChanged.connect(lambda f: self.mapview.scene.canvas.set_config('font', f))
        self.fontselect.setCurrentFont(qtg.QFont('Baskerville'))

        self.fontsize = qtw.QComboBox()
        self.fontsize.addItems([str(s) for s in self.FONT_SIZES])
        self.fontsize.setCurrentText(str(36))
        self.fontsize.currentTextChanged.connect(lambda f: self.mapview.scene.canvas.set_config('fontsize', int(f)))
        self.mainToolbar.addWidget(self.fontsize)

        self.mainToolbar.addAction(self.actionBold)
        self.actionBold.triggered.connect(lambda s: self.mapview.scene.canvas.set_config('bold', s))
        self.mainToolbar.addAction(self.actionItalic)
        self.actionItalic.triggered.connect(lambda s: self.mapview.scene.canvas.set_config('italic', s))
        self.mainToolbar.addAction(self.actionUnderline)
        self.actionUnderline.triggered.connect(lambda s: self.mapview.scene.canvas.set_config('underline', s))

        self.mainToolbar.addSeparator()

        sizeicon = qtw.QLabel()
        sizeicon.setPixmap(qtg.QPixmap(':/map-icons/border-weight.png').scaledToHeight(18))
        self.mainToolbar.addWidget(sizeicon)
        self.sizeselect = qtw.QSlider()
        self.sizeselect.setRange(1,20)
        self.sizeselect.setOrientation(qtc.Qt.Horizontal)
        self.sizeselect.setSizePolicy(
            qtw.QSizePolicy.Minimum,
            qtw.QSizePolicy.Preferred
        )
        self.sizeselect.valueChanged.connect(lambda s: self.mapview.scene.canvas.set_config('size', s))
        self.mainToolbar.addWidget(self.sizeselect)


        middlespacer_2 = qtw.QLabel()
        middlespacer_2.setSizePolicy(
            qtw.QSizePolicy.Expanding, 
            qtw.QSizePolicy.Preferred
        )
        self.mainToolbar.addWidget(middlespacer_2)

        self.mainToolbar.addAction(self.actionPan)
        self.actionPan.triggered.connect(self.mapview.toggle_panning)
        # self.mainToolbar.addSeparator()
        self.mainToolbar.addAction(self.actionFitView)
        self.actionFitView.triggered.connect(self.mapview.fitWithBorder)
        # self.mainToolbar.addSeparator()

        zoomicon = qtw.QLabel()
        zoomicon.setPixmap(qtg.QPixmap(':/toolbar-icons/zoom_icon.png').scaledToHeight(16))
        self.minZoom = -14
        self.maxZoom = 14
        self.zoomslider = qtw.QSlider()
        self.zoomslider.setRange(self.minZoom, self.maxZoom)
        self.zoomslider.setOrientation(qtc.Qt.Horizontal)
        self.zoomslider.setSizePolicy(
            qtw.QSizePolicy.Minimum,
            qtw.QSizePolicy.Preferred
        )
        self.zoomslider.valueChanged.connect(self.mapview.zoomEvent)
        self.mapview.zoomChanged.connect(self.handleZoomChange)
        self.mainToolbar.addWidget(zoomicon)
        self.mainToolbar.addWidget(self.zoomslider)

        endspacer = qtw.QLabel()
        # endspacer.setSizePolicy(
        #     qtw.QSizePolicy.Fixed, 
        #     qtw.QSizePolicy.Preferred
        # )
        endspacer.setFixedWidth(10)
        self.mainToolbar.addWidget(endspacer)

        self.panButton.toggled.connect(self.mapview.toggle_panning)

        toolbutton_style = """
            QToolButton {
                font: 17px 'Baskerville';
            }
            QToolButton:pressed {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #dadbde, stop: 1 #f6f7fa);
            }
        """

        self.mainToolbar.setStyleSheet(toolbutton_style)
    
        self.show()
    

    def build_map(self, database):
        print('Building map...')
        self.mapview.connect_db(database)
        self.mapview.init_loc_dialogs()
        self.mapview.initTimestamps()
        self.mapview.fitWithBorder()
        self.show_known_locs.setChecked(True)
        self.animator_controls.active = True
        self.map_loaded.emit()

    @qtc.pyqtSlot(int)
    def handleZoomChange(self, value):
        self.zoomslider.blockSignals(True)
        self.zoomslider.setValue(value)
        self.zoomslider.blockSignals(False)
    
    @qtc.pyqtSlot(str, str)
    def handleButtonPress(self, mode, secondary):
        if mode in self.CURSORS:
            self.mapview.viewport().setCursor(self.CURSORS[mode])
        elif secondary in self.CURSORS:
            self.mapview.viewport().setCursor(self.CURSORS[secondary])
        else:
            self.mapview.viewport().setCursor(qtc.Qt.ArrowCursor)

        if secondary == 'reset':
            self.mapview.viewport().setCursor(qtc.Qt.ArrowCursor)
            self.selectButton.setChecked(True)

        self.mapview.set_mode(mode, secondary)

    

    @qtc.pyqtSlot(str, Time)
    def addTimestamp(self, char_name, time):
        entry = f'{char_name}\n  {str(time)}'
        self.timestampList.addItem(entry)


    def choose_color(self, callback):
        dlg = qtw.QColorDialog()
        if dlg.exec():
            callback( dlg.selectedColor().name() )
 
    @qtc.pyqtSlot(str)
    def set_primary_color(self, hex):
        self.mapview.set_primary_color(hex)
        self.primaryButton.setStyleSheet('QPushButton { background-color: %s; }' % hex)

    @qtc.pyqtSlot(str)
    def set_secondary_color(self, hex):
        self.mapview.set_secondary_color(hex)
        self.secondaryButton.setStyleSheet('QPushButton { background-color: %s; }' % hex)


    def openImage(self):

        filename, _ = qtw.QFileDialog.getOpenFileName(self, "Open file", 
                "PNG files (*.png) ;;JPEG files (*jpg) ;;All files (*.*)", 
                "PNG files (*.png)"
        )
        if filename:
            self.mapview.set_new_image(filename)
            
    def newMap(self):
        self.mapview.blank_slate()

    def sweepMap(self):
        self.mapview.sweep_canvas()

    def printMap(self):
        printer = qps.QPrinter()
        printer.setOutputFormat(printer.NativeFormat)

        dialog = qps.QPrintDialog(printer)
        if dialog.exec() == qtw.QDialog.Accepted:
            self.mapview.scene.clearSelection()
            self.mapview.fitWithBorder()

            painter = qtg.QPainter(printer)
            painter.setRenderHint(qtg.QPainter.Antialiasing)
            self.mapview.render(painter)
            painter.end()


    def exportMap(self):
        filename, _ = qtw.QFileDialog.getSaveFileName(
            self,
            "Select an export location...",
            qtc.QDir.currentPath(),
            'PDF Files (*.pdf) ;;All Files (*)',
            'PDF Files (*.pdf)'
        )
        if filename:
            self.mapview.scene.clearSelection()
            self.mapview.fitWithBorder()

            printer = qps.QPrinter()
            printer.setOutputFormat(qps.QPrinter.PdfFormat)
            printer.setPaperSize(qps.QPrinter.A4)
            printer.setOutputFileName(filename)
            printer.setPageOrientation(qtg.QPageLayout.Landscape)

            painter = qtg.QPainter(printer)
            painter.setRenderHint(qtg.QPainter.Antialiasing)
            self.mapview.render(painter)
            painter.end()
    
    @qtc.pyqtSlot()
    def saveRequest(self):
        print('Saving map...')
        self.mapview.saveMap()
        self.mapview.saveEmbedded()
        
    
    @qtc.pyqtSlot()
    def preferenceUpdate(self):
        print('Map: Received preference notification...')