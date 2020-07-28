
# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

class DetachableTabWidget(qtw.QTabWidget):

    tab_loaded = qtc.pyqtSignal()

    def __init__(self, parent=None):
        super(DetachableTabWidget, self).__init__(parent)

        self.tabbar = self.TabBar(self)
        self.tabbar.onDetachTabSignal.connect(self.detachTab)
        self.tabbar.onMoveTabSignal.connect(self.moveTab)

        # Styling
        tabwidget_style = """
            QTabWidget::pane {
                /* The tab widget frame */
                border-top: 2px solid #C2C7CB;
            }
            QTabWidget::tab-bar {
                left: 5px; /* move to the right by 5px */
            }
        """
        tabbar_style = """
            QTabBar::tab {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #E1E1E1, stop: 0.4 #DDDDDD,
                                stop: 0.5 #D8D8D8, stop: 1.0 #D3D3D3);
                border: 2px solid #C4C4C3;
                border-bottom-color: #C2C7CB; /* same as the pane color */
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 8ex;
                padding: 8px;
            }

            QTabBar::tab:selected {
                border-color: #9B9B9B;
                border-bottom-color: #C2C7CB; /* same as pane color */
            }

            QTabBar::tab:!selected {
                margin-top: 4px; /* make non-selected tabs look smaller */
            }
        """

        self.setStyleSheet(tabwidget_style)
        self.tabbar.setStyleSheet(tabbar_style)
        # tab_font = self.tabbar.font()
        # tab_font.setPointSize(16)
        # tab_font = qtg.QFont('Hoefler Text', 18)
        tab_font = qtg.QFont('Cochin', 20, qtg.QFont.DemiBold)
        self.tabbar.setFont(tab_font)

        self.setTabBar(self.tabbar)

    def setMovable(self, movable):
        pass

    @qtc.pyqtSlot(int, int)
    def moveTab(self, fromIndex, toIndex):
        widget = self.widget(fromIndex)
        icon = self.tabIcon(fromIndex)
        text = self.tabText(fromIndex)

        self.removeTab(fromIndex)
        self.insertTab(toIndex, widget, icon, text)
        self.setCurrentIndex(toIndex)


    @qtc.pyqtSlot(int, qtc.QPoint)
    def detachTab(self, index, point):

        # Get the tab content
        name = self.tabText(index)
        icon = self.tabIcon(index)        
        if icon.isNull():
            icon = self.window().windowIcon()              
        contentWidget = self.widget(index)
        contentWidgetRect = contentWidget.frameGeometry()

        # Create a new detached tab window
        detachedTab = self.DetachedTab(contentWidget, self.parentWidget())
        detachedTab.setWindowModality(qtc.Qt.NonModal)
        detachedTab.setWindowTitle(name)
        detachedTab.setWindowIcon(icon)
        detachedTab.setObjectName(name)
        detachedTab.setGeometry(contentWidgetRect)
        detachedTab.onCloseSignal.connect(self.attachTab)
        detachedTab.move(point)
        detachedTab.show()


    @qtc.pyqtSlot(qtw.QWidget, type(''), qtg.QIcon)
    def attachTab(self, contentWidget, name, icon):

        # Make the content widget a child of this widget
        contentWidget.setParent(self)

        # Create an image from the given icon
        if not icon.isNull():
            tabIconPixmap = icon.pixmap(icon.availableSizes()[0])
            tabIconImage = tabIconPixmap.toImage()
        else:
            tabIconImage = None

        # Create an image of the main window icon
        if not icon.isNull():
            windowIconPixmap = self.window().windowIcon().pixmap(icon.availableSizes()[0])
            windowIconImage = windowIconPixmap.toImage()
        else:
            windowIconImage = None

        if name == 'Family Tree':
            index = 0
        elif name == 'Timeline':
            index = 1
        elif name == 'Map Builder':
            index = 2
        elif name == 'Character Scroll':
            index = 3
        if tabIconImage == windowIconImage:
            index = self.insertTab(index, contentWidget, name)
        else:
            index = self.insertTab(index, contentWidget, icon, name)

        if index > -1:
            self.setCurrentIndex(index)


    class DetachedTab(qtw.QDialog):

        onCloseSignal = qtc.pyqtSignal(qtw.QWidget, type(''), qtg.QIcon)

        def __init__(self, contentWidget, parent=None):
            qtw.QDialog.__init__(self, parent)

            layout = qtw.QVBoxLayout(self)            
            self.contentWidget = contentWidget            
            layout.addWidget(self.contentWidget)
            self.contentWidget.show()
            self.setWindowFlags(qtc.Qt.Window)

        def event(self, event):
            # If QEvent.NonClientAreaMouseButtonDblClick then
            # close the dialog
            if event.type() == 176:
                event.accept()
                self.close()

            return qtw.QDialog.event(self, event)


        def closeEvent(self, event):
            self.onCloseSignal.emit(self.contentWidget, self.objectName(), self.windowIcon())

    class TabBar(qtw.QTabBar):

        onDetachTabSignal = qtc.pyqtSignal(int, qtc.QPoint)
        onMoveTabSignal = qtc.pyqtSignal(int, int)

        def __init__(self, parent=None):
            qtw.QTabBar.__init__(self, parent)

            self.setAcceptDrops(True)
            self.setElideMode(qtc.Qt.ElideRight)
            self.setSelectionBehaviorOnRemove(qtw.QTabBar.SelectLeftTab)

            self.dragStartPos = qtc.QPoint()
            self.dragDropedPos = qtc.QPoint()
            self.mouseCursor = qtg.QCursor()
            self.dragInitiated = False


        def mouseDoubleClickEvent(self, event):
            event.accept()
            self.onDetachTabSignal.emit(self.tabAt(event.pos()), self.mouseCursor.pos())

        def mousePressEvent(self, event):
            if event.button() == qtc.Qt.LeftButton:
                self.dragStartPos = event.pos()

            self.dragDropedPos.setX(0)
            self.dragDropedPos.setY(0)

            self.dragInitiated = False

            qtw.QTabBar.mousePressEvent(self, event)

        def mouseMoveEvent(self, event):

            # Determine if the current movement is detected as a drag
            if not self.dragStartPos.isNull() and ((event.pos() - self.dragStartPos).manhattanLength() > qtw.QApplication.startDragDistance()*2):
                self.dragInitiated = True

            # If the current movement is a drag initiated by the left button
            if (((event.buttons() & qtc.Qt.LeftButton)) and self.dragInitiated): 

                # Stop the move event
                finishMoveEvent = qtg.QMouseEvent(qtc.QEvent.MouseMove, event.pos(), qtc.Qt.NoButton, qtc.Qt.NoButton, qtc.Qt.NoModifier)
                qtw.QTabBar.mouseMoveEvent(self, finishMoveEvent)

                # Convert the move event into a drag
                drag = qtg.QDrag(self)
                mimeData = qtc.QMimeData()
                mimeData.setData('action', b'application/tab-detach')
                drag.setMimeData(mimeData)

                #Create the appearance of dragging the tab content
                pixmap = self.parentWidget().grab()
                targetPixmap = qtg.QPixmap(pixmap.size())
                targetPixmap.fill(qtc.Qt.transparent)
                painter = qtg.QPainter(targetPixmap)
                painter.setOpacity(0.85)
                painter.drawPixmap(0, 0, pixmap)
                painter.end()
                drag.setPixmap(targetPixmap)

                # Initiate the drag
                dropAction = drag.exec_(qtc.Qt.MoveAction | qtc.Qt.CopyAction)

                # If the drag completed outside of the tab bar, detach the tab and move
                # the content to the current cursor position
                if dropAction == qtc.Qt.IgnoreAction:
                    event.accept()
                    self.onDetachTabSignal.emit(self.tabAt(self.dragStartPos), self.mouseCursor.pos())

                # Else if the drag completed inside the tab bar, move the selected tab to the new position
                elif dropAction == qtc.Qt.MoveAction:
                    if not self.dragDropedPos.isNull():
                        event.accept()
                        self.onMoveTabSignal.emit(self.tabAt(self.dragStartPos), self.tabAt(self.dragDropedPos))
            else:
                qtw.QTabBar.mouseMoveEvent(self, event)


        def dragEnterEvent(self, event):
            mimeData = event.mimeData()
            formats = mimeData.formats()

            if 'action' in formats and mimeData.data('action') == 'application/tab-detach':
                event.acceptProposedAction()

            qtw.QTabBar.dragMoveEvent(self, event)

        def dropEvent(self, event):
            self.dragDropedPos = event.pos()
            qtw.QTabBar.dropEvent(self, event)

