
# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg

# External resources
from fantasycreator.resources import resources


class PaintButtonLayout(qtw.QGridLayout):
    MIN_SIZE = 10
    def __init__(self, parent=None):
        super(PaintButtonLayout, self).__init__(parent)
        self.setVerticalSpacing(15)
        
    def setGeometry(self, oldRect):
        min_extent = max(PaintButtonLayout.MIN_SIZE * 2, oldRect.height())
        newRect = qtc.QRect(0, 0, min_extent, min_extent)
        newRect.moveCenter(oldRect.center())
        super(PaintButtonLayout, self).setGeometry(newRect)

class SideControlButton(qtw.QPushButton):
    def __init__(self, min_side_lenth, max_side_lenth, width_for_height=False, parent=None):
        super(SideControlButton, self).__init__(parent)
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Preferred, qtw.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        # if width_for_height:
        sizePolicy.setWidthForHeight(True)
            # sizePolicy.setHeightForWidth(True)
        # else:
        sizePolicy.setHeightForWidth(True)
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(qtc.QSize(min_side_lenth, min_side_lenth))
        self.setMaximumSize(qtc.QSize(max_side_lenth, max_side_lenth))
        self.setText("")

    def heightForWidth(self, width):
        return width
    def widthForHeight(self, height):
        return height


class Ui_MapBuilderTab(object):

    PAINT_BUTTON_MIN_SIDE = 10
    PAINT_BUTTON_MAX_SIDE = 25

    DRAW_BUTTON_MIN_SIDE = 20
    DRAW_BUTTON_MAX_SIDE = 50

    LEFT_SIDEBAR_MIN_WIDTH = 95
    LEFT_SIDEBAR_MAX_WIDTH = 125
    LEFT_SIDEBAR_MIN_HEIGHT = 0
    LEFT_SIDEBAR_MAX_HEIGHT = 2000

    RIGHT_SIDEBAR_MIN_WIDTH = 140
    RIGHT_SIDEBAR_MAX_WIDTH = 165
    RIGHT_SIDEBAR_MIN_HEIGHT = 0
    RIGHT_SIDEBAR_MAX_HEIGHT = 2000

    def setupUi(self, MapBuilderTab):
        MapBuilderTab.setObjectName("MapBuilderTab")
        # MapBuilderTab.resize(706, 556)
        self.centralWidget = qtw.QWidget(MapBuilderTab)
        self.centralWidget.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)
        self.centralWidget.setObjectName("centralWidget")

        self.mainLayout = qtw.QHBoxLayout(self.centralWidget)
        self.mainLayout.setSizeConstraint(qtw.QLayout.SetDefaultConstraint)
        self.mainLayout.setSpacing(6)
        self.mainLayout.setObjectName("mainLayout")
        self.left_main_vertical_layout = qtw.QVBoxLayout()
        # self.left_main_vertical_layout.setAlignment(qtc.Qt.AlignHCenter)
        # self.left_main_vertical_layout.setSpacing(6)
        self.left_main_vertical_layout.setObjectName("left_main_vertical_layout")
        # self.sceneGroup = qtw.QWidget(self.centralWidget)
        
        self.sceneGroup = qtw.QGroupBox("Drawing")
        self.sceneGroup.setFont(qtg.QFont('Baskerville', 18))

        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Preferred, 
                                    qtw.QSizePolicy.Preferred)
        sizePolicy.setWidthForHeight(True)
        # sizePolicy.setHeightForWidth(True)
        # sizePolicy.setHorizontalStretch(0)
        # sizePolicy.setVerticalStretch(2)
        self.sceneGroup.setSizePolicy(sizePolicy)
        self.sceneGroup.setMinimumSize(Ui_MapBuilderTab.LEFT_SIDEBAR_MIN_WIDTH, 
                                        Ui_MapBuilderTab.LEFT_SIDEBAR_MIN_HEIGHT)
        self.sceneGroup.setMaximumSize(Ui_MapBuilderTab.LEFT_SIDEBAR_MAX_WIDTH, 
                                        Ui_MapBuilderTab.LEFT_SIDEBAR_MAX_HEIGHT)
        self.sceneGroup.setObjectName("sceneGroup")
        
        self.drawing_tools_layout = qtw.QGridLayout(self.sceneGroup)
        self.drawing_tools_layout.setAlignment(qtc.Qt.AlignHCenter)
        self.drawing_tools_layout.setContentsMargins(0, 0, 0, 0)
        # self.drawing_tools_layout.setSpacing(10)
        self.drawing_tools_layout.setVerticalSpacing(12)
        self.drawing_tools_layout.setHorizontalSpacing(8)
        self.drawing_tools_layout.setObjectName("drawing_tools_layout")
        self.rectButton = SideControlButton(Ui_MapBuilderTab.DRAW_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.DRAW_BUTTON_MAX_SIDE,
                                            False, self.sceneGroup)
        icon = qtg.QIcon()
        icon.addPixmap(qtg.QPixmap(":/map-icons/layer-shape.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.rectButton.setIcon(icon)
        self.rectButton.setCheckable(True)
        self.rectButton.setToolTip("Draw a rectangle")
        self.rectButton.setObjectName("rectButton")
        self.drawing_tools_layout.addWidget(self.rectButton, 6, 1, 1, 1)
        self.polylineButton = SideControlButton(Ui_MapBuilderTab.DRAW_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.DRAW_BUTTON_MAX_SIDE, 
                                            False, self.sceneGroup)
        icon1 = qtg.QIcon()
        icon1.addPixmap(qtg.QPixmap(":/map-icons/layer-shape-polyline.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.polylineButton.setIcon(icon1)
        self.polylineButton.setCheckable(True)
        self.polylineButton.setToolTip("Draw a poly-line")
        self.polylineButton.setObjectName("polylineButton")
        self.drawing_tools_layout.addWidget(self.polylineButton, 5, 1, 1, 1)

        self.eraserButton = SideControlButton(Ui_MapBuilderTab.DRAW_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.DRAW_BUTTON_MAX_SIDE, 
                                            False, self.sceneGroup)
        icon3 = qtg.QIcon()
        icon3.addPixmap(qtg.QPixmap(":/map-icons/eraser.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.eraserButton.setIcon(icon3)
        self.eraserButton.setCheckable(True)
        self.eraserButton.setToolTip("Erase")
        self.eraserButton.setObjectName("eraserButton")
        self.drawing_tools_layout.addWidget(self.eraserButton, 1, 1, 1, 1)

        self.dropperButton = SideControlButton(Ui_MapBuilderTab.DRAW_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.DRAW_BUTTON_MAX_SIDE, 
                                            False, self.sceneGroup)
        icon4 = qtg.QIcon()
        icon4.addPixmap(qtg.QPixmap(":/map-icons/pipette.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.dropperButton.setIcon(icon4)
        self.dropperButton.setCheckable(True)
        self.dropperButton.setToolTip("Select color")
        self.dropperButton.setObjectName("dropperButton")
        self.drawing_tools_layout.addWidget(self.dropperButton, 3, 1, 1, 1)

        self.brushButton = SideControlButton(Ui_MapBuilderTab.DRAW_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.DRAW_BUTTON_MAX_SIDE, 
                                            False, self.sceneGroup)
        icon5 = qtg.QIcon()
        icon5.addPixmap(qtg.QPixmap(":/map-icons/paint-brush.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.brushButton.setIcon(icon5)
        self.brushButton.setCheckable(True)
        self.brushButton.setToolTip("Paintbrush")
        self.brushButton.setObjectName("brushButton")
        self.drawing_tools_layout.addWidget(self.brushButton, 2, 1, 1, 1)

        self.penButton = SideControlButton(Ui_MapBuilderTab.DRAW_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.DRAW_BUTTON_MAX_SIDE, 
                                            False, self.sceneGroup)
        icon6 = qtg.QIcon()
        icon6.addPixmap(qtg.QPixmap(":/map-icons/pencil.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.penButton.setIcon(icon6)
        self.penButton.setCheckable(True)
        self.penButton.setToolTip("Pen")
        self.penButton.setObjectName("penButton")
        self.drawing_tools_layout.addWidget(self.penButton, 2, 0, 1, 1)

        self.textButton = SideControlButton(Ui_MapBuilderTab.DRAW_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.DRAW_BUTTON_MAX_SIDE, 
                                            False, self.sceneGroup)
        icon7 = qtg.QIcon()
        icon7.addPixmap(qtg.QPixmap(":/map-icons/edit.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.textButton.setIcon(icon7)
        self.textButton.setCheckable(True)
        self.textButton.setToolTip("Add a textbox")
        self.textButton.setObjectName("textButton")
        self.drawing_tools_layout.addWidget(self.textButton, 4, 0, 1, 1)
        # self.polygonButton = qtw.QPushButton(self.sceneGroup)
        # self.polygonButton.setMinimumSize(qtc.QSize(45, 45))
        # self.polygonButton.setMaximumSize(qtc.QSize(45, 45))
        # self.polygonButton.setText("")
        # icon11 = qtg.QIcon()
        # icon11.addPixmap(qtg.QPixmap(":/map-icons/layer-shape-polygon.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        # self.polygonButton.setIcon(icon11)
        # self.polygonButton.setCheckable(True)
        # self.polygonButton.setToolTip("Draw a polygon")
        # self.polygonButton.setObjectName("polygonButton")
        # self.drawing_tools_layout.addWidget(self.polygonButton, 5, 1, 1, 1)
        # self.roundrectButton = qtw.QPushButton(self.sceneGroup)
        # self.roundrectButton.setMinimumSize(qtc.QSize(45, 45))
        # self.roundrectButton.setMaximumSize(qtc.QSize(45, 45))
        # self.roundrectButton.setText("")
        # icon12 = qtg.QIcon()
        # icon12.addPixmap(qtg.QPixmap(":/map-icons/layer-shape-round.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        # self.roundrectButton.setIcon(icon12)
        # self.roundrectButton.setCheckable(True)
        # self.roundrectButton.setToolTip("Draw a rounded rectangle")
        # self.roundrectButton.setObjectName("roundrectButton")
        # self.drawing_tools_layout.addWidget(self.roundrectButton, 6, 1, 1, 1)
        self.ellipseButton = SideControlButton(Ui_MapBuilderTab.DRAW_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.DRAW_BUTTON_MAX_SIDE, 
                                            False, self.sceneGroup)
        icon10 = qtg.QIcon()
        icon10.addPixmap(qtg.QPixmap(":/map-icons/layer-shape-ellipse.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.ellipseButton.setIcon(icon10)
        self.ellipseButton.setCheckable(True)
        self.ellipseButton.setToolTip("Draw an ellipse")
        self.ellipseButton.setObjectName("ellipseButton")
        self.drawing_tools_layout.addWidget(self.ellipseButton, 6, 0, 1, 1)

        self.lineButton = SideControlButton(Ui_MapBuilderTab.DRAW_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.DRAW_BUTTON_MAX_SIDE, 
                                            False, self.sceneGroup)
        icon11 = qtg.QIcon()
        icon11.addPixmap(qtg.QPixmap(":/map-icons/layer-shape-line.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.lineButton.setIcon(icon11)
        self.lineButton.setCheckable(True)
        self.lineButton.setToolTip("Draw a line")
        self.lineButton.setObjectName("lineButton")
        self.drawing_tools_layout.addWidget(self.lineButton, 5, 0, 1, 1)

        self.sprayButton = SideControlButton(Ui_MapBuilderTab.DRAW_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.DRAW_BUTTON_MAX_SIDE, 
                                            False, self.sceneGroup)
        icon12 = qtg.QIcon()
        icon12.addPixmap(qtg.QPixmap(":/map-icons/spray.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.sprayButton.setIcon(icon12)
        self.sprayButton.setCheckable(True)
        self.sprayButton.setFlat(False)
        self.sprayButton.setToolTip("Spray paint!")
        self.sprayButton.setObjectName("sprayButton")
        self.drawing_tools_layout.addWidget(self.sprayButton, 3, 0, 1, 1)

        self.undoButton = SideControlButton(Ui_MapBuilderTab.DRAW_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.DRAW_BUTTON_MAX_SIDE, 
                                            False, self.sceneGroup)
        icon13 = qtg.QIcon()
        icon13.addPixmap(qtg.QPixmap(":/toolbar-icons/undo_icon.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.undoButton.setIcon(icon13)
        self.undoButton.setFlat(False)
        self.undoButton.setObjectName("undoButton")
        self.drawing_tools_layout.addWidget(self.undoButton, 1, 0, 1, 1)

        self.selectButton = SideControlButton(Ui_MapBuilderTab.DRAW_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.DRAW_BUTTON_MAX_SIDE, 
                                            False, self.sceneGroup)
        icon14 = qtg.QIcon()
        icon14.addPixmap(qtg.QPixmap(":/map-icons/selection-cursor.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.selectButton.setIcon(icon14)
        self.selectButton.setCheckable(True)
        self.selectButton.setFlat(False)
        self.selectButton.setToolTip("Select")
        self.selectButton.setObjectName("selectButton")
        self.drawing_tools_layout.addWidget(self.selectButton, 0, 0, 1, 1)

        self.panButton = SideControlButton(Ui_MapBuilderTab.DRAW_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.DRAW_BUTTON_MAX_SIDE, 
                                            False, self.sceneGroup)
        icon15 = qtg.QIcon()
        icon15.addPixmap(qtg.QPixmap(":/map-icons/open-hand-cursor.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.panButton.setIcon(icon15)
        self.panButton.setCheckable(True)
        self.panButton.setFlat(False)
        self.panButton.setToolTip("Pan")
        self.panButton.setObjectName("panButton")
        self.drawing_tools_layout.addWidget(self.panButton, 0, 1, 1, 1)

        self.imgButton = SideControlButton(Ui_MapBuilderTab.DRAW_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.DRAW_BUTTON_MAX_SIDE, 
                                            False, self.sceneGroup)
        icon16 = qtg.QIcon()
        icon16.addPixmap(qtg.QPixmap(":/map-icons/image-icon.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.imgButton.setIcon(icon16)
        self.imgButton.setCheckable(True)
        self.imgButton.setFlat(False)
        self.imgButton.setObjectName("imgButton")
        self.drawing_tools_layout.addWidget(self.imgButton, 4, 1, 1, 1)

        self.left_main_vertical_layout.addWidget(self.sceneGroup)
        # spacerItem = qtw.QSpacerItem(20, 10, qtw.QSizePolicy.Minimum, qtw.QSizePolicy.MinimumExpanding)
        # self.left_main_vertical_layout.addItem(spacerItem)
        # self.left_main_vertical_layout.addStretch(1)
        self.mainLayout.addLayout(self.left_main_vertical_layout)
        
        self.colors_layout = qtw.QVBoxLayout()
        # self.colors_layout.setSpacing(6)
        # self.colors_layout.setAlignment(qtc.Qt.AlignHCenter)
        self.colors_layout.setDirection(qtw.QBoxLayout.BottomToTop)
        self.colors_layout.setObjectName("colors_layout")

        self.colorswidget = qtw.QWidget(self.centralWidget)
        self.colorswidget.setContentsMargins(10, 0, 10, 0)
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Preferred, qtw.QSizePolicy.Preferred)
        sizePolicy.setWidthForHeight(True)
        sizePolicy.setHeightForWidth(True)
        self.colorswidget.setSizePolicy(sizePolicy)
        self.colorswidget.setMinimumSize(Ui_MapBuilderTab.LEFT_SIDEBAR_MIN_WIDTH, 
                                        Ui_MapBuilderTab.LEFT_SIDEBAR_MIN_HEIGHT)
        self.colorswidget.setMaximumSize(Ui_MapBuilderTab.LEFT_SIDEBAR_MAX_WIDTH, 
                                        Ui_MapBuilderTab.LEFT_SIDEBAR_MAX_HEIGHT)
        # self.colorswidget.setContentsMargins(11, 0, 0, 0)
        self.colorswidget.setObjectName("colorswidget")
        self.colorswidget_layout = qtw.QGridLayout(self.colorswidget)
        # self.colorswidget.setMinimumSize(50, 50)
        # self.colorswidget.setMaximumSize(120, 120)

        for i in range(8):
            self.colorswidget_layout.setRowStretch(i, 1)
            self.colorswidget_layout.setColumnStretch(i, 1)

        self.secondaryButton = SideControlButton(25, 55, False, self.colorswidget)
        self.secondaryButton.setObjectName("secondaryButton")
        self.colorswidget_layout.addWidget(self.secondaryButton, 3, 3, 4, 4)
        

        self.primaryButton = SideControlButton(25, 55, False, self.colorswidget)
        self.colorswidget_layout.addWidget(self.primaryButton, 1, 1, 4, 4)
        self.primaryButton.setObjectName("primaryButton")

        self.colors_layout.addWidget(self.colorswidget)#, qtc.Qt.AlignHCenter)
        self.widget_2 = qtw.QWidget(self.centralWidget)
        self.widget_2.setMinimumSize(Ui_MapBuilderTab.LEFT_SIDEBAR_MIN_WIDTH, 
                                    Ui_MapBuilderTab.LEFT_SIDEBAR_MIN_HEIGHT)
        self.widget_2.setMaximumSize(Ui_MapBuilderTab.LEFT_SIDEBAR_MAX_WIDTH, 
                                    Ui_MapBuilderTab.LEFT_SIDEBAR_MAX_HEIGHT)
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Preferred, 
                                        qtw.QSizePolicy.Preferred)
        self.widget_2.setSizePolicy(sizePolicy)
        self.widget_2.setObjectName("widget_2")


        self.colorbuttons_layout = qtw.QGridLayout(self.widget_2)
        self.colorbuttons_layout.setVerticalSpacing(15)
        self.colorbuttons_layout.setHorizontalSpacing(10)
        self.colorbuttons_layout.setObjectName("colorbuttons_layout")

        self.colorButton_11 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
                                            True, self.widget_2)
        self.colorButton_11.setObjectName("colorButton_11")
        self.colorbuttons_layout.addWidget(self.colorButton_11, 5, 0, 1, 1)

        self.colorButton_7 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
                                            True, self.widget_2)
        self.colorButton_7.setObjectName("colorButton_7")
        self.colorbuttons_layout.addWidget(self.colorButton_7, 3, 0, 1, 1)

        self.colorButton_9 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
                                            True, self.widget_2)
        self.colorButton_9.setObjectName("colorButton_9")
        self.colorbuttons_layout.addWidget(self.colorButton_9, 4, 0, 1, 1)

        self.colorButton_10 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
                                            True, self.widget_2)
        self.colorButton_10.setObjectName("colorButton_10")
        self.colorbuttons_layout.addWidget(self.colorButton_10, 4, 1, 1, 1)

        # self.colorButton_23 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
        #                                     Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
        #                                     True, self.widget_2)
        # self.colorButton_23.setObjectName("colorButton_23")
        # self.colorbuttons_layout.addWidget(self.colorButton_23, 11, 0, 1, 1)

        self.colorButton_18 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
                                            True, self.widget_2)
        self.colorButton_18.setObjectName("colorButton_18")
        self.colorbuttons_layout.addWidget(self.colorButton_18, 8, 1, 1, 1)

        self.colorButton_20 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
                                            True, self.widget_2)
        self.colorButton_20.setObjectName("colorButton_20")
        self.colorbuttons_layout.addWidget(self.colorButton_20, 9, 1, 1, 1)

        self.colorButton_6 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
                                            True, self.widget_2)
        self.colorButton_6.setObjectName("colorButton_6")
        self.colorbuttons_layout.addWidget(self.colorButton_6, 2, 1, 1, 1)

        self.colorButton_3 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
                                            True, self.widget_2)
        self.colorButton_3.setObjectName("colorButton_3")
        self.colorbuttons_layout.addWidget(self.colorButton_3, 1, 0, 1, 1)

        # self.colorButton_24 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
        #                                     Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
        #                                     True, self.widget_2)
        # self.colorButton_24.setObjectName("colorButton_24")
        # self.colorbuttons_layout.addWidget(self.colorButton_24, 11, 1, 1, 1)

        self.colorButton_17 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
                                            True, self.widget_2)
        self.colorButton_17.setObjectName("colorButton_17")
        self.colorbuttons_layout.addWidget(self.colorButton_17, 8, 0, 1, 1)

        self.colorButton_1 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
                                            True, self.widget_2)
        self.colorButton_1.setObjectName("colorButton_1")
        self.colorbuttons_layout.addWidget(self.colorButton_1, 0, 0, 1, 1)

        self.colorButton_8 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
                                            True, self.widget_2)
        self.colorButton_8.setObjectName("colorButton_8")
        self.colorbuttons_layout.addWidget(self.colorButton_8, 3, 1, 1, 1)

        self.colorButton_22 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
                                            True, self.widget_2)
        self.colorButton_22.setObjectName("colorButton_22")
        self.colorbuttons_layout.addWidget(self.colorButton_22, 10, 1, 1, 1)

        self.colorButton_15 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
                                            True, self.widget_2)
        self.colorButton_15.setObjectName("colorButton_15")
        self.colorbuttons_layout.addWidget(self.colorButton_15, 7, 0, 1, 1)

        self.colorButton_5 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
                                            True, self.widget_2)
        self.colorButton_5.setObjectName("colorButton_5")
        self.colorbuttons_layout.addWidget(self.colorButton_5, 2, 0, 1, 1)

        self.colorButton_2 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
                                            True, self.widget_2)
        self.colorButton_2.setObjectName("colorButton_2")
        self.colorbuttons_layout.addWidget(self.colorButton_2, 0, 1, 1, 1)

        self.colorButton_16 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
                                            True, self.widget_2)
        self.colorButton_16.setObjectName("colorButton_16")
        self.colorbuttons_layout.addWidget(self.colorButton_16, 7, 1, 1, 1)

        self.colorButton_14 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
                                            True, self.widget_2)
        self.colorButton_14.setObjectName("colorButton_14")
        self.colorbuttons_layout.addWidget(self.colorButton_14, 6, 1, 1, 1)

        self.colorButton_4 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
                                            True, self.widget_2)
        self.colorButton_4.setObjectName("colorButton_4")
        self.colorbuttons_layout.addWidget(self.colorButton_4, 1, 1, 1, 1)

        self.colorButton_21 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
                                            True, self.widget_2)
        self.colorButton_21.setObjectName("colorButton_21")
        self.colorbuttons_layout.addWidget(self.colorButton_21, 10, 0, 1, 1)

        self.colorButton_12 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
                                            True, self.widget_2)
        self.colorButton_12.setObjectName("colorButton_12")
        self.colorbuttons_layout.addWidget(self.colorButton_12, 5, 1, 1, 1)

        self.colorButton_19 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
                                            True, self.widget_2)
        self.colorButton_19.setObjectName("colorButton_19")
        self.colorbuttons_layout.addWidget(self.colorButton_19, 9, 0, 1, 1)

        self.colorButton_13 = SideControlButton(Ui_MapBuilderTab.PAINT_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.PAINT_BUTTON_MAX_SIDE, 
                                            True, self.widget_2)
        self.colorButton_13.setObjectName("colorButton_13")
        self.colorbuttons_layout.addWidget(self.colorButton_13, 6, 0, 1, 1)

        self.colors_layout.addWidget(self.widget_2)
        self.colors_layout.setStretch(0, 4)
        self.colors_layout.setStretch(1, 1)
        self.left_main_vertical_layout.addLayout(self.colors_layout)
        self.left_main_vertical_layout.insertStretch(1, 1)

        self.middle_main_vertical_layout = qtw.QVBoxLayout()
        self.middle_main_vertical_layout.setObjectName("middle_main_vertical_layout")

        self.view = qtw.QLabel(self.centralWidget)
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)
        self.view.setSizePolicy(sizePolicy)
        self.view.setObjectName('mapview')
        
        self.middle_main_vertical_layout.addWidget(self.view)

        self.animateWidget = qtw.QWidget(self.centralWidget)
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Preferred)
        self.animateWidget.setSizePolicy(sizePolicy)
        self.animateWidget.setMinimumSize(qtc.QSize(0, 84))
        self.animateWidget.setMaximumSize(qtc.QSize(16777215, 84))
        self.animateWidget.setObjectName("animateWidget")

        self.middle_main_vertical_layout.addWidget(self.animateWidget)
        self.mainLayout.addLayout(self.middle_main_vertical_layout)


        self.right_main_vertical_layout = qtw.QVBoxLayout()
        # self.right_main_vertical_layout.setAlignment(qtc.Qt.AlignHCenter)
        self.right_main_vertical_layout.setSpacing(6)
        self.right_main_vertical_layout.setObjectName("right_main_vertical_layout")

        self.embeddedGroup = qtw.QGroupBox("Embedded")
        self.embeddedGroup.setFont(qtg.QFont('Baskerville', 18))
        # self.embeddedGroup.setAlignment(qtc.Qt.AlignCenter)

        # sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Preferred)
        # sizePolicy.setHorizontalStretch(0)
        # # sizePolicy.setVerticalStretch(1)
        # self.embeddedGroup.setSizePolicy(sizePolicy)
        self.embeddedGroup.setMinimumSize(Ui_MapBuilderTab.RIGHT_SIDEBAR_MIN_WIDTH, 
                                        Ui_MapBuilderTab.RIGHT_SIDEBAR_MIN_HEIGHT)
        self.embeddedGroup.setMaximumSize(Ui_MapBuilderTab.RIGHT_SIDEBAR_MAX_WIDTH, 
                                        Ui_MapBuilderTab.RIGHT_SIDEBAR_MAX_HEIGHT)
        self.embeddedGroup.setObjectName("embeddedGroup")

        self.embedded_object_layout = qtw.QVBoxLayout(self.embeddedGroup)
        self.embedded_object_layout.setContentsMargins(0, 0, 0, 0)
        self.embedded_object_layout.setAlignment(qtc.Qt.AlignHCenter)
        # self.embedded_object_layout.setSpacing(10)
        self.embedded_object_layout.setObjectName("embedded_object_layout")

        self.charactersGroup = qtw.QGroupBox("Characters")
        self.charactersGroup.setFont(qtg.QFont('Baskerville', 15))
        self.characters_layout = qtw.QGridLayout(self.charactersGroup)
        self.characters_layout.setContentsMargins(0, 0, 0, 0)
        self.characters_layout.setVerticalSpacing(12)
        self.characters_layout.setHorizontalSpacing(6)
        self.characters_layout.setObjectName("characters_layout")

        self.addCharButton = SideControlButton(Ui_MapBuilderTab.DRAW_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.DRAW_BUTTON_MAX_SIDE,
                                            self.charactersGroup)
        self.addCharButton.setCheckable(True)
        self.addCharButton.setToolTip("Add a character")
        icon17 = qtg.QIcon()
        icon17.addPixmap(qtg.QPixmap(":/toolbar-icons/add_char_icon.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.addCharButton.setIcon(icon17)
        self.addCharButton.setIconSize(qtc.QSize(22, 22))
        self.addCharButton.setObjectName("addCharButton")
        self.characters_layout.addWidget(self.addCharButton, 0, 0, 1, 1)

        self.removeCharButton = SideControlButton(Ui_MapBuilderTab.DRAW_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.DRAW_BUTTON_MAX_SIDE,
                                            self.charactersGroup)
        self.removeCharButton.setCheckable(True)
        self.removeCharButton.setToolTip("Remove a character")
        icon18 = qtg.QIcon()
        icon18.addPixmap(qtg.QPixmap(":/toolbar-icons/remove_char_icon.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.removeCharButton.setIcon(icon18)
        self.removeCharButton.setIconSize(qtc.QSize(22, 22))
        self.removeCharButton.setObjectName("removeCharButton")
        self.characters_layout.addWidget(self.removeCharButton, 0, 1, 1, 1)

        self.embedded_object_layout.addWidget(self.charactersGroup)

        self.locationsGroup = qtw.QGroupBox("Locations")
        self.locationsGroup.setFont(qtg.QFont('Baskerville', 15))
        self.locations_layout = qtw.QGridLayout(self.locationsGroup)
        self.locations_layout.setVerticalSpacing(10)
        self.locations_layout.setHorizontalSpacing(6)
        self.locations_layout.setContentsMargins(0, 0, 0, 0)
        self.locations_layout.setObjectName("locations_layout")

        self.castleButton = SideControlButton(Ui_MapBuilderTab.DRAW_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.DRAW_BUTTON_MAX_SIDE,
                                            self.locationsGroup)
        self.castleButton.setCheckable(True)
        self.castleButton.setToolTip("Insert kingdom landmark")
        icon19 = qtg.QIcon()
        icon19.addPixmap(qtg.QPixmap(":/map-icons/castle-icon.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.castleButton.setIcon(icon19)
        self.castleButton.setIconSize(qtc.QSize(22, 22))
        self.castleButton.setObjectName("castleButton")
        self.locations_layout.addWidget(self.castleButton, 0, 0, 1, 1)

        self.villageButton = SideControlButton(Ui_MapBuilderTab.DRAW_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.DRAW_BUTTON_MAX_SIDE,
                                            self.locationsGroup)
        self.villageButton.setCheckable(True)
        self.villageButton.setToolTip("Insert village/town")
        icon20 = qtg.QIcon()
        icon20.addPixmap(qtg.QPixmap(":/map-icons/village-icon.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.villageButton.setIcon(icon20)
        self.villageButton.setIconSize(qtc.QSize(25, 25))
        self.villageButton.setObjectName("villageButton")
        self.locations_layout.addWidget(self.villageButton, 0, 1, 1, 1)

        self.portButton = SideControlButton(Ui_MapBuilderTab.DRAW_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.DRAW_BUTTON_MAX_SIDE,
                                            self.locationsGroup)
        self.portButton.setCheckable(True)
        self.portButton.setToolTip("Insert port/harbor")
        icon21 = qtg.QIcon()
        icon21.addPixmap(qtg.QPixmap(":/map-icons/anchor.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.portButton.setIcon(icon21)
        self.portButton.setIconSize(qtc.QSize(22, 22))
        self.portButton.setObjectName("portButton")
        self.locations_layout.addWidget(self.portButton, 1, 0, 1, 1)

        self.campButton = SideControlButton(Ui_MapBuilderTab.DRAW_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.DRAW_BUTTON_MAX_SIDE,
                                            self.locationsGroup)
        self.campButton.setCheckable(True)
        self.campButton.setToolTip("Insert camp/temporary location")
        icon22 = qtg.QIcon()
        icon22.addPixmap(qtg.QPixmap(":/map-icons/camp-icon.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.campButton.setIcon(icon22)
        self.campButton.setIconSize(qtc.QSize(25, 25))
        self.campButton.setObjectName("campButton")
        self.locations_layout.addWidget(self.campButton, 1, 1, 1, 1)

        self.otherLocButton = SideControlButton(Ui_MapBuilderTab.DRAW_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.DRAW_BUTTON_MAX_SIDE,
                                            self.locationsGroup)
        self.otherLocButton.setCheckable(True)
        self.otherLocButton.setToolTip("Insert other landmark")
        icon23 = qtg.QIcon()
        icon23.addPixmap(qtg.QPixmap(":/map-icons/misc-location.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.otherLocButton.setIcon(icon23)
        self.otherLocButton.setIconSize(qtc.QSize(25, 25))
        self.otherLocButton.setObjectName("otherLocButton")
        self.locations_layout.addWidget(self.otherLocButton, 2, 1, 1, 1)

        self.existingLocButton = SideControlButton(Ui_MapBuilderTab.DRAW_BUTTON_MIN_SIDE, 
                                            Ui_MapBuilderTab.DRAW_BUTTON_MAX_SIDE,
                                            self.locationsGroup)
        self.existingLocButton.setCheckable(True)
        self.existingLocButton.setToolTip("Insert existing location")
        icon24 = qtg.QIcon()
        icon24.addPixmap(qtg.QPixmap(":/map-icons/known-location-icon.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.existingLocButton.setIcon(icon24)
        self.existingLocButton.setIconSize(qtc.QSize(25, 25))
        self.existingLocButton.setObjectName("existingLocButton")
        self.locations_layout.addWidget(self.existingLocButton, 2, 0, 1, 1)

        self.embedded_object_layout.addWidget(self.locationsGroup)

        self.show_known_locs = qtw.QCheckBox('Show Existing\nLocations')
        self.show_known_locs.setFont(qtg.QFont('Baskerville', 15))
        self.show_known_locs.setContentsMargins(5, 5, 5, 5)
        self.embedded_object_layout.addWidget(self.show_known_locs)

        self.right_main_vertical_layout.addWidget(self.embeddedGroup)

        self.timestampGroup = qtw.QGroupBox('Time Stamps')
        self.timestampGroup.setMinimumSize(Ui_MapBuilderTab.RIGHT_SIDEBAR_MIN_WIDTH,
                                        Ui_MapBuilderTab.RIGHT_SIDEBAR_MIN_HEIGHT)
        self.timestampGroup.setMaximumSize(Ui_MapBuilderTab.RIGHT_SIDEBAR_MAX_WIDTH,
                                        Ui_MapBuilderTab.RIGHT_SIDEBAR_MAX_HEIGHT)
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Preferred, qtw.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(2.5)
        self.timestampGroup.setSizePolicy(sizePolicy)
        self.timestampGroup.setFont(qtg.QFont('Baskerville', 18))
        self.timestampGroup.setObjectName("timestampGroup")
        
        self.timestamps_layout = qtw.QVBoxLayout()
        self.timestamps_layout.setAlignment(qtc.Qt.AlignHCenter)
        self.timestamps_layout.setObjectName("timestamps_layout")

        self.tempList = qtw.QWidget(self.centralWidget)
        self.tempList.setSizePolicy(qtw.QSizePolicy.Preferred, qtw.QSizePolicy.Preferred)
        self.tempList.setMinimumSize(qtc.QSize(65, 100))
        self.tempList.setMaximumSize(qtc.QSize(175, 350))
        self.tempList.setObjectName("tempList")
        self.timestamps_layout.addWidget(self.tempList)
        self.timestampGroup.setLayout(self.timestamps_layout)

        self.right_main_vertical_layout.addWidget(self.timestampGroup)

        self.animateButton = qtw.QPushButton(self.timestampGroup)
        # sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.MinimumExpanding, qtw.QSizePolicy.MinimumExpanding)
        # sizePolicy.setHorizontalStretch(0)
        # sizePolicy.setVerticalStretch(0)
        # self.animateButton.setSizePolicy(sizePolicy)
        self.animateButton.setMinimumSize(qtc.QSize(65, 25))
        self.animateButton.setMaximumSize(qtc.QSize(125, 35))
        self.animateButton.setText("Animate Mode")
        self.animateButton.setFont(qtg.QFont('Baskerville', 16))
        self.animateButton.setCheckable(True)
        self.animateButton.setToolTip("Toggle animation mode")

        self.animateButton.setObjectName("animateButton")
        self.animateButton.setStyleSheet("""
                    QPushButton:!checked {
                        border-width: 2px;
                        border-radius: 5px;        
                        border-style: inset;
                        background-color: rgba(195, 195, 195, 20);
                    }
                    QPushButton:checked { 
                        border-width: 2px;
                        border-radius: 5px;
                        border-style: outset;
                        background-color: rgb(155, 155, 155);
                    }
        """)
        self.timestamps_layout.addWidget(self.animateButton)

        self.right_main_vertical_layout.insertStretch(1, 1)

        self.mainLayout.addLayout(self.right_main_vertical_layout)
        MapBuilderTab.setCentralWidget(self.centralWidget)
        
        self.mainToolbar = qtw.QToolBar(MapBuilderTab)
        self.mainToolbar.setIconSize(qtc.QSize(22, 22))
        self.mainToolbar.setFloatable(False)
        self.mainToolbar.setMovable(False)
        self.mainToolbar.setObjectName("mainToolbar")
        MapBuilderTab.addToolBar(qtc.Qt.TopToolBarArea, self.mainToolbar)



        self.actionOpenImage = qtw.QAction(MapBuilderTab)
        icon25 = qtg.QIcon()
        icon25.addPixmap(qtg.QPixmap(":/map-icons/blue-folder-open-image.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.actionOpenImage.setIcon(icon25)
        self.actionOpenImage.setToolTip("Open image")
        self.actionOpenImage.setObjectName("actionOpenImage")
        self.actionExportImage = qtw.QAction(MapBuilderTab)
        icon26 = qtg.QIcon()
        icon26.addPixmap(qtg.QPixmap(":/map-icons/export-pdf.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.actionExportImage.setIcon(icon26)
        self.actionExportImage.setToolTip("Export as PDF")
        self.actionExportImage.setObjectName("actionExportImage")
        self.actionPrintImage = qtw.QAction(MapBuilderTab)
        icon27 = qtg.QIcon()
        icon27.addPixmap(qtg.QPixmap(":/map-icons/printer.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.actionPrintImage.setIcon(icon27)
        self.actionPrintImage.setToolTip("Print map")
        self.actionPrintImage.setObjectName("actionPrintImage")

        self.actionNewImage = qtw.QAction(MapBuilderTab)
        icon28 = qtg.QIcon()
        icon28.addPixmap(qtg.QPixmap(":/map-icons/document-image.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.actionNewImage.setIcon(icon28)
        self.actionNewImage.setToolTip("Set blank canvas")
        self.actionNewImage.setObjectName("actionNewImage")

        self.actionClearImage = qtw.QAction(MapBuilderTab)
        icon29 = qtg.QIcon()
        icon29.addPixmap(qtg.QPixmap(":/map-icons/clear-sweep.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.actionClearImage.setIcon(icon29)
        self.actionClearImage.setToolTip("Erase objects/drawings")
        self.actionClearImage.setObjectName("actionClearImage")

        self.actionBold = qtw.QAction(MapBuilderTab)
        self.actionBold.setCheckable(True)
        icon30 = qtg.QIcon()
        icon30.addPixmap(qtg.QPixmap(":/map-icons/edit-bold.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.actionBold.setIcon(icon30)
        self.actionBold.setToolTip("Bold")
        self.actionBold.setObjectName("actionBold")
        self.actionItalic = qtw.QAction(MapBuilderTab)
        self.actionItalic.setCheckable(True)
        icon31 = qtg.QIcon()
        icon31.addPixmap(qtg.QPixmap(":/map-icons/edit-italic.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.actionItalic.setIcon(icon31)
        self.actionItalic.setToolTip("Italic")
        self.actionItalic.setObjectName("actionItalic")
        self.actionUnderline = qtw.QAction(MapBuilderTab)
        self.actionUnderline.setCheckable(True)
        icon32 = qtg.QIcon()
        icon32.addPixmap(qtg.QPixmap(":/map-icons/edit-underline.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.actionUnderline.setIcon(icon32)
        self.actionUnderline.setToolTip("Underline")
        self.actionUnderline.setObjectName("actionUnderline")

        self.actionPan = qtw.QAction(MapBuilderTab)
        self.actionPan.setCheckable(True)
        icon33 = qtg.QIcon()
        icon33.addPixmap(qtg.QPixmap(":/toolbar-icons/pan_icon.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.actionPan.setIcon(icon33)
        self.actionPan.setObjectName("actionPan")
        self.actionFitView = qtw.QAction(MapBuilderTab)
        icon34 = qtg.QIcon()
        icon34.addPixmap(qtg.QPixmap(":/toolbar-icons/fit_view_icon.png"))
        self.actionFitView.setIcon(icon34)
        self.actionFitView.setObjectName("actionFitView")
        # self.actionZoom = qtw.QAction(MapBuilderTab)
        

        # self.actionFillShapes = qtw.QAction(MapBuilderTab)
        # self.actionFillShapes.setCheckable(True)
        # icon22 = qtg.QIcon()
        # icon22.addPixmap(qtg.QPixmap(":/map-icons/paint-can-color.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        # self.actionFillShapes.setIcon(icon22)
        # self.actionFillShapes.setObjectName("actionFillShapes")
        # self.menuFIle.addAction(self.actionNewImage)
        # self.menuFIle.addAction(self.actionOpenImage)
        # self.menuFIle.addAction(self.actionExportImage)
        # self.menuEdit.addAction(self.actionCopy)
        # self.menuEdit.addSeparator()
        # self.menuEdit.addAction(self.actionClearImage)
        # self.menuImage.addAction(self.actionInvertColors)
        # self.menuImage.addSeparator()
        # self.menuImage.addAction(self.actionFlipHorizontal)
        # self.menuImage.addAction(self.actionFlipVertical)
        # self.menuBar.addAction(self.menuFIle.menuAction())
        # self.menuBar.addAction(self.menuEdit.menuAction())
        # self.menuBar.addAction(self.menuImage.menuAction())
        # self.menuBar.addAction(self.menuHelp.menuAction())
        # self.fileToolbar.addAction(self.actionNewImage)
        # self.fileToolbar.addAction(self.actionOpenImage)
        # self.fileToolbar.addAction(self.actionExportImage)

        

        self.retranslateUi(MapBuilderTab)
        qtc.QMetaObject.connectSlotsByName(MapBuilderTab)

    def retranslateUi(self, MapBuilderTab):
        _translate = qtc.QCoreApplication.translate
        MapBuilderTab.setWindowTitle(_translate("MapBuilderTab", "Piecasso"))
        # self.menuFIle.setTitle(_translate("MapBuilderTab", "FIle"))
        # self.menuEdit.setTitle(_translate("MapBuilderTab", "Edit"))
        # self.menuImage.setTitle(_translate("MapBuilderTab", "Image"))
        # self.menuHelp.setTitle(_translate("MapBuilderTab", "Help"))
        # self.fileToolbar.setWindowTitle(_translate("MapBuilderTab", "toolBar"))
        # self.drawingToolbar.setWindowTitle(_translate("MapBuilderTab", "toolBar"))
        self.mainToolbar.setWindowTitle(_translate("MapBuilderTab", "toolBar"))
        # self.actionCopy.setText(_translate("MapBuilderTab", "Copy"))
        # self.actionCopy.setShortcut(_translate("MapBuilderTab", "Ctrl+C"))
        # self.actionClearImage.setText(_translate("MapBuilderTab", "Clear Image"))
        # self.actionOpenImage.setText(_translate("MapBuilderTab", "Open Image..."))
        # self.actionExportImage.setText(_translate("MapBuilderTab", "Save Image As..."))
        # self.actionInvertColors.setText(_translate("MapBuilderTab", "Invert Colors"))
        # self.actionFlipHorizontal.setText(_translate("MapBuilderTab", "Flip Horizontal"))
        # self.actionFlipVertical.setText(_translate("MapBuilderTab", "Flip Vertical"))
        # self.actionNewImage.setText(_translate("MapBuilderTab", "New Image"))
        self.actionBold.setText(_translate("MapBuilderTab", "Bold"))
        self.actionBold.setShortcut(_translate("MapBuilderTab", "Ctrl+B"))
        self.actionItalic.setText(_translate("MapBuilderTab", "Italic"))
        self.actionItalic.setShortcut(_translate("MapBuilderTab", "Ctrl+I"))
        self.actionUnderline.setText(_translate("MapBuilderTab", "Underline"))
        # self.actionFillShapes.setText(_translate("MapBuilderTab", "Fill Shapes?"))