
# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg

# 3rd party
import numpy as np
from tinydb import where

# Built-in Modules
import random
import types
import uuid

# User-defined Modules
from Tree.character import PictureLineEdit, PictureEditor
from Mechanics.storyTime import Time, DateLineEdit, DateValidator
from Mechanics.flags import EVENT_TYPE


## Embededded Objects

class EmbeddedGraphic(qtw.QGraphicsWidget):

    top_left_handle = 1
    top_right_handle = 2
    bottom_left_handle = 3
    bottom_right_handle = 4

    handle_size = 14
    handle_space = -4

    handle_cursors = {
        top_left_handle: qtc.Qt.SizeFDiagCursor,
        top_right_handle: qtc.Qt.SizeBDiagCursor,
        bottom_left_handle: qtc.Qt.SizeBDiagCursor,
        bottom_right_handle: qtc.Qt.SizeFDiagCursor
    }

    def __init__(self, start_pos, stamp, timestamp=False, parent=None):
        super(EmbeddedGraphic, self).__init__(parent)

        if isinstance(stamp, qtg.QImage):
            self.stamp = qtg.QPixmap.fromImage(stamp)
        else: # Assume to be image path
            self.stamp = qtg.QPixmap(stamp)


        if isinstance(start_pos, qtc.QRectF):
            rect = self.mapFromScene(start_pos).boundingRect()
            self.setPos(rect.x(), rect.y())
            rect.translate(-rect.x(), -rect.y())
            self.stamp_rect = rect
        else:
            if timestamp:
                start_pos = self.mapFromScene(start_pos)
            self.stamp_rect = qtc.QRectF(self.stamp.rect())
            self.setPos(start_pos.x() - self.stamp.width() / 2, start_pos.y() 
                                - self.stamp.height() / 2)
        
        self.handles_pen = qtg.QPen(qtg.QColor(0, 0, 0, 255), 1.0, qtc.Qt.SolidLine, qtc.Qt.RoundCap, qtc.Qt.RoundJoin)
        self.handles_brush = qtg.QBrush(qtg.QColor(255, 0, 0, 255))
        
        self.handles = {}
        self.show_handles = False
        self.handle_selected = None
        self.mouse_press_pos = None
        self.mouse_press_rect = None
        self.updateHandlesPos()
    
    def getID(self):
        return self._id

    def getGraphicalRect(self):
        return self.mapToScene(self.stamp_rect).boundingRect()
    
    def setStamp(self, img):
        self.prepareGeometryChange()
        current_pos = self.pos()
        self.stamp = qtg.QPixmap.fromImage(img)
        self.stamp_rect = qtc.QRectF(self.stamp.rect())
        self.setPos(current_pos)
        self.updateHandlesPos()
    
    def handleAt(self, point):
        for handle, b_rect, in self.handles.items():
            if b_rect.contains(point):
                return handle
        return None

    def hoverEnterEvent(self, mouseEvent):
        self.show_handles = True
        self.setCursor(qtc.Qt.OpenHandCursor)
        super(EmbeddedGraphic, self).hoverEnterEvent(mouseEvent)

    def hoverMoveEvent(self, moveEvent):
        # if self.isSelected():
        handle = self.handleAt(moveEvent.pos())
        if handle:
            self.setCursor(self.handle_cursors[handle])
        else:
            self.setCursor(qtc.Qt.OpenHandCursor)
        super(EmbeddedGraphic, self).hoverMoveEvent(moveEvent)

    def hoverLeaveEvent(self, moveEvent):
        self.show_handles = False
        # self.setCursor(qtc.Qt.OpenHandCursor)
        super(EmbeddedGraphic, self).hoverLeaveEvent(moveEvent)

    def mousePressEvent(self, mouseEvent):
        self.handle_selected = self.handleAt(mouseEvent.pos())
        if self.handle_selected:
            self.mouse_press_pos = mouseEvent.pos()
            self.mouse_press_rect = self.boundingRect()
        super(EmbeddedGraphic, self).mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        if self.handle_selected:
            self.interactiveResize(mouseEvent.pos())
        else:
            self.setCursor(qtc.Qt.ClosedHandCursor)
            super(EmbeddedGraphic, self).mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        super(EmbeddedGraphic, self).mouseReleaseEvent(mouseEvent)
        self.handle_selected = None
        self.mouse_press_pos = None
        self.mouse_press_rect = None
        self.update()

    def updateHandlesPos(self):
        size = self.handle_size
        b_rect = self.boundingRect()
        self.handles[self.top_left_handle] = qtc.QRectF(b_rect.left(), b_rect.top(), size, size)
        self.handles[self.top_right_handle] = qtc.QRectF(b_rect.right() - size, b_rect.top(), size, size)
        self.handles[self.bottom_left_handle] = qtc.QRectF(b_rect.left(), b_rect.bottom() - size, size, size)
        self.handles[self.bottom_right_handle] = qtc.QRectF(b_rect.right() - size, b_rect.bottom() - size, size, size)

    def interactiveResize(self, mouse_pos):
        offset = self.handle_size + self.handle_space
        bounding_rect = self.boundingRect()
        rect = self.stamp_rect
        diff = qtc.QPointF(0, 0)

        self.prepareGeometryChange()

        if self.handle_selected == self.top_left_handle:
            start_x = self.mouse_press_rect.left()
            start_y = self.mouse_press_rect.top()
            end_x = start_x + mouse_pos.x() - self.mouse_press_pos.x()
            end_y = start_y + mouse_pos.y() - self.mouse_press_pos.y()
            delta = min((end_x - start_x), (end_y - start_y))
            diff.setX(delta)
            diff.setY(delta)
            bounding_rect.setLeft(start_x + delta)
            bounding_rect.setTop(start_y + delta)
            rect.setLeft(bounding_rect.left() + offset)
            rect.setTop(bounding_rect.top() + offset)
            self.stamp_rect = rect

        elif self.handle_selected == self.top_right_handle:
            start_x = self.mouse_press_rect.right()
            start_y = self.mouse_press_rect.top()
            end_x = start_x + mouse_pos.x() - self.mouse_press_pos.x()
            end_y = start_y + mouse_pos.y() - self.mouse_press_pos.y()
            delta = min(abs((end_x - start_x)), (end_y - start_y))
            diff.setX(-delta)
            diff.setY(delta)
            bounding_rect.setRight(start_x - delta)
            bounding_rect.setTop(start_y + delta)
            rect.setRight(bounding_rect.right() - offset)
            rect.setTop(bounding_rect.top() + offset)
            self.stamp_rect = rect

        elif self.handle_selected == self.bottom_left_handle:
            start_x = self.mouse_press_rect.left()
            start_y = self.mouse_press_rect.bottom()
            end_x = start_x + mouse_pos.x() - self.mouse_press_pos.x()
            end_y = start_y + mouse_pos.y() - self.mouse_press_pos.y()
            delta = min((end_x - start_x), abs((end_y - start_y)))
            diff.setX(delta)
            diff.setY(-delta)
            bounding_rect.setLeft(start_x + delta)
            bounding_rect.setBottom(start_y - delta)
            rect.setLeft(bounding_rect.left() + offset)
            rect.setBottom(bounding_rect.bottom() - offset)
            self.stamp_rect = rect

        elif self.handle_selected == self.bottom_right_handle:
            start_x = self.mouse_press_rect.right()
            start_y = self.mouse_press_rect.bottom()
            end_x = start_x + mouse_pos.x() - self.mouse_press_pos.x()
            end_y = start_y + mouse_pos.y() - self.mouse_press_pos.y()
            delta = min((end_x - start_x), (end_y - start_y))
            diff.setX(delta)
            diff.setY(delta)
            bounding_rect.setRight(start_x + delta)
            bounding_rect.setBottom(start_y + delta)
            rect.setRight(bounding_rect.right() - offset)
            rect.setBottom(bounding_rect.bottom() - offset)
            self.stamp_rect = rect

        self.updateHandlesPos()
    
    def toggleEditing(self, state):
        self.editing = state
        if state:
            self.unsetCursor()
            self.setFlag(qtw.QGraphicsItem.ItemIsMovable, False) 
            self.setFlag(qtw.QGraphicsItem.ItemIsSelectable, False)
            self.setFlag(qtw.QGraphicsItem.ItemSendsGeometryChanges, False)
            self.setAcceptHoverEvents(False)
        if not self.editing:
            self.setFlag(qtw.QGraphicsItem.ItemIsMovable, True) 
            self.setFlag(qtw.QGraphicsItem.ItemIsSelectable, True)
            self.setFlag(qtw.QGraphicsItem.ItemSendsGeometryChanges, True)
            self.setCursor(qtc.Qt.OpenHandCursor)
            self.setAcceptHoverEvents(True)

    def boundingRect(self):
        offset = self.handle_size + self.handle_space
        return self.stamp_rect.adjusted(-offset, -offset, offset, offset)

    def shape(self):
        path = qtg.QPainterPath()
        path.addRect(self.stamp_rect)
        if self.isSelected() or self.show_handles:
            for shape in self.handles.values():
                path.addEllipse(shape)
        return path

    def paint(self, painter, option, widget=None):

        painter.drawPixmap(self.stamp_rect.toRect(), self.stamp)

        if self.isSelected() or self.show_handles:
            painter.setRenderHint(qtg.QPainter.Antialiasing)
            painter.setBrush(self.handles_brush)
            painter.setPen(self.handles_pen)
            for handle, rect in self.handles.items():
                if not self.handle_selected or handle == self.handle_selected:
                    painter.drawEllipse(rect)

    def __repr__(self):
        return self._id
    
    def __hash__(self):
        return hash(self._id)

    def __eq__(self, other):
        if isinstance(other, uuid.UUID):
            return self._id == other
        elif isinstance(other, EmbeddedGraphic):
            return self._id == other._id
        else:
            return False


class GraphicCharacter(EmbeddedGraphic):

    def __init__(self, start_pos, char_id, stamp, timestamp=False, parent=None):
        super(GraphicCharacter, self).__init__(start_pos, stamp, timestamp, parent)
        
        if char_id:
            self.setID(char_id)
        # if center_anchor:
        #     self.moveBy(self.stamp_rect.width()/2, self.stamp_rect.height()/2)
    
    def setID(self, _id):
        self._id = _id
        self.setObjectName('graphicChar{}'.format(self._id))

    def contextMenuEvent(self, event):
        self.setCursor(qtc.Qt.PointingHandCursor)
        menu = qtw.QMenu("Options")
        # edit_act = menu.addAction("Edit...")
        edit_char_act = menu.addAction("Edit...")
        add_timestamp_act = menu.addAction("Add timestamp")
        view_act = menu.addAction("Character view")
        del_character_act = menu.addAction("Remove character")
        selected_act = menu.exec(event.screenPos())

        # if selected_act == edit_act:
        #     self.parent().edit_char.emit(self._id)
        if selected_act == add_timestamp_act:
            self.parent().timestamp_req.emit(self._id, self.mapToScene(self.stamp_rect.center()))
        elif selected_act == edit_char_act:
            self.parent().edit_char.emit(self._id)
        elif selected_act == view_act:
            self.parent().add_char_view.emit(self._id)
        elif selected_act == del_character_act:
            self.parent().remove_character(self._id)

        event.accept()
        self.unsetCursor()
        


class GraphicLocation(EmbeddedGraphic):

    def __init__(self, start_pos, mode, stamp, loc_id=None, parent=None):
        super(GraphicLocation, self).__init__(start_pos, stamp, False, parent)
        self.mode = mode
        self._id = loc_id
        if loc_id:
            self.setID(loc_id)

    def setID(self, _id):
        self._id = _id
        self.setObjectName('graphicLoc{}'.format(self._id))
    
    def contextMenuEvent(self, event):
        self.setCursor(qtc.Qt.PointingHandCursor)
        menu = qtw.QMenu("Options")
        # edit_act = menu.addAction("Edit...")
        edit_act = menu.addAction("Edit...")
        view_act = menu.addAction("Location view")
        del_loc_act = menu.addAction("Remove location")
        selected_act = menu.exec(event.screenPos())

        if selected_act == edit_act:
            self.parent().edit_location.emit(self._id)
        elif selected_act == view_act:
            self.parent().add_loc_view.emit(self._id)
        elif selected_act == del_loc_act:
            self.parent().remove_location(self._id)

        event.accept()
        self.unsetCursor()


class LocationView(qtw.QGraphicsWidget):

    closed = qtc.pyqtSignal()
    CURRENT_SPAWN = qtc.QPoint(20, 60)  #NOTE: Magic Number

    def __init__(self, location_dict, parent=None):
        super(LocationView, self).__init__(parent)
        self.setAttribute(qtc.Qt.WA_DeleteOnClose)
        self.setFlags(qtw.QGraphicsItem.ItemIsMovable | qtw.QGraphicsItem.ItemIsSelectable)
        # self.setAcceptHoverEvents(True)
        self.setCursor(qtc.Qt.OpenHandCursor)

        self._location = location_dict
        self._id = self._location['location_id']
        self.setObjectName('view{}'.format(self._id))

        self.setScale(1.4)

        self.brush = qtg.QBrush(qtg.QColor('#c9cdd4')) # pass as argument?
        self.translucent_effect = qtw.QGraphicsOpacityEffect(self)
        self.translucent_effect.setOpacity(0.8)
        self.setGraphicsEffect(self.translucent_effect)
        self.translucent_effect.setEnabled(False)

        self.setSizePolicy(
            qtw.QSizePolicy.Preferred,
            qtw.QSizePolicy.Preferred
        )

        self.setMinimumSize(qtc.QSizeF(225, 275))


        self.display_widgets = qtw.QGraphicsItemGroup(self)

        # Set layout
        layout = qtw.QGraphicsLinearLayout(qtc.Qt.Vertical)
        label_style = """ QLabel {
                    background-color: #e3ddcc;
                    border-radius: 5px;
                    border-color: gray;
                    padding: 4px;
                    font: 24px;
                }"""
        
        # Create and add label widgets
        self.name_label = qtw.QGraphicsProxyWidget(self)
        self.name_label.setWidget(LocationViewLabel())
        self.name_label.widget().setStyleSheet("""QLabel {
                    background-color: rgba(255, 255, 255, 0);
                    border-radius: 5px;
                    border-color: gray;
                    padding: 4px;
                    font: 34px 'Didot';
                }""")
        self.name_label.widget().setAlignment(qtc.Qt.AlignHCenter | qtc.Qt.AlignVCenter)
        self.name_label.setAcceptHoverEvents(False)
        layout.addItem(self.name_label)

        self.type_label = qtw.QGraphicsProxyWidget(self)
        self.type_label.setWidget(LocationViewLabel())
        self.type_label.widget().setStyleSheet(label_style)
        self.type_label.setAcceptHoverEvents(False)
        layout.addItem(self.type_label)

        self.details_label = qtw.QGraphicsProxyWidget(self)
        self.details_label.setWidget(LocationViewLabel())
        self.details_label.widget().setStyleSheet(label_style)
        self.details_label.setAcceptHoverEvents(False)
        layout.addItem(self.details_label)

    
        self.cancel_btn = qtw.QGraphicsProxyWidget(self)
        self.cancel_btn.setWidget(qtw.QPushButton(
            'Cancel',
            clicked=self.close
        ))
        self.cancel_btn.widget().setStyleSheet("""
                        QPushButton { 
                            border: 1px solid black;
                            border-style: outset;
                            border-radius: 2px;
                            color: black;
                            font: 24px;
                            font-family: Baskerville;
                        }
                        QPushButton:pressed { 
                            background-color: rgba(255, 255, 255, 70);
                            border-style: inset;
                        }""")
        layout.addItem(self.cancel_btn)
        layout.setSpacing(16)
        self.setLayout(layout)

        self.updateView()
        
    
    def getID(self):
        return self._id
    
    def updateView(self):
        name = self._location['location_name']
        if not name:
            name = 'Location: ...'
        self.name_label.widget().setText(name)

        _type = self._location['location_type']
        if _type:
            _type = f"<b>Type</b>: {_type}"
        else:
            _type = 'Type...'
        self.type_label.widget().setText(_type)

        details = self._location['location_details']
        if details:
            details = f"<b>Details</b>: {details}"
        else:
            details = 'Details: ...'
        self.details_label.widget().setText(details)
    

    def check_selected(self):
        if self.isSelected():
            self.translucent_effect.setEnabled(False)
        else:
            self.translucent_effect.setEnabled(True)
    

    ## Override drawing methods ##

    def paint(self, painter, option, widget):
        frame = qtc.QRectF(qtc.QPointF(0, 0), self.geometry().size())
        painter.setBrush(self.brush)
        painter.drawRoundedRect(frame, 10, 10)
    
    def shape(self):
        path = qtg.QPainterPath()
        path.addRect(self.boundingRect())
        return path

    ## Override Built-In Slots ##
    def closeEvent(self, event):
        self.closed.emit()
        super(LocationView, self).closeEvent(event)
    
    def mousePressEvent(self, event):
        self.setCursor(qtc.Qt.ClosedHandCursor)
        event.accept()
        super(LocationView, self).mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.setCursor(qtc.Qt.OpenHandCursor)
        event.accept()
        super(LocationView, self).mouseReleaseEvent(event)
    

class LocationViewLabel(qtw.QLabel):

    def __init__(self, parent=None):
        super(LocationViewLabel, self).__init__(parent)
        self.setTextFormat(qtc.Qt.RichText)
        self.setFont(qtg.QFont('Baskerville', 26))
        self.setCursor(qtc.Qt.OpenHandCursor)
        self.setWordWrap(True)
        self.setSizePolicy(
            qtw.QSizePolicy.Minimum,
            qtw.QSizePolicy.Preferred
        )
        # self.setMaximumWidth(200)


# Character creation form
class LocationCreator(qtw.QDialog):

    submitted = qtc.pyqtSignal(dict)
    closed = qtc.pyqtSignal()

    DFLT_LOC_PATH = ':/dflt-event-imges/unknown_event_loc.png'

    TYPE_ITEMS = ["Select Type"]

    def __init__(self, parent=None, editingLoc=None, windowTitle=None):
        super(LocationCreator, self).__init__(parent)
        self.setSizePolicy(
            qtw.QSizePolicy.Preferred,
            qtw.QSizePolicy.Preferred
        )
        self.setAttribute(qtc.Qt.WA_DeleteOnClose)
        self.setFont(qtg.QFont('Baskerville', 14))
        
        self.setModal(True) # CAUSES BUG 

        # self.setFixedSize(380, self.minimumHeight())

        self._id = 0

        main_layout = qtw.QVBoxLayout()
        fields_layout = qtw.QFormLayout()

        # Create input widgets
        self.name = qtw.QLineEdit()
        self.name.setFont(qtg.QFont('Baskerville', 16))
        self.type_select = qtw.QComboBox()
        self.type_select.setFont(qtg.QFont('Baskerville', 16))
        self.details = qtw.QTextEdit()
        self.details.setFont(qtg.QFont('Baskerville', 16))
        self.picture_path = PictureLineEdit()
        self.picture_path.setFont(qtg.QFont('Baskerville', 16))
        self.picture = qtw.QLabel(alignment=qtc.Qt.AlignCenter)

        # Modify widgets
        self.type_select.addItems(self.TYPE_ITEMS)
        self.type_select.model().item(0).setEnabled(False)

        self.details.setSizePolicy(
            qtw.QSizePolicy.Minimum,
            qtw.QSizePolicy.Minimum
        )   
        self.details.setFixedHeight(100)

        self.picture_path.setSizePolicy(
            qtw.QSizePolicy.Maximum,
            qtw.QSizePolicy.Preferred
        )

        # Connect signals
        self.type_select.currentTextChanged.connect(self.onTypeChange)
        self.picture_path.clicked.connect(self.getPic)


        self.submit_btn = qtw.QPushButton(
            'Submit',
            clicked=self.onSubmit
        )
        self.submit_btn.setDefault(True)
        self.submit_btn.setFont(qtg.QFont('Baskerville', 16))
        self.cancel_btn = qtw.QPushButton(
            'Cancel',
            clicked=self.close
        )
        self.cancel_btn.setAutoDefault(False)
        self.cancel_btn.setFont(qtg.QFont('Baskerville', 16))
        
        # Define layout
        fields_layout.addRow('Name', self.name)
        label = fields_layout.labelForField(self.name)
        label.setFont(qtg.QFont('Baskerville', 16))
        fields_layout.addRow('Type', self.type_select)
        label = fields_layout.labelForField(self.type_select)
        label.setFont(qtg.QFont('Baskerville', 16))
        fields_layout.addRow('Details', self.details)
        label = fields_layout.labelForField(self.details)
        label.setFont(qtg.QFont('Baskerville', 16))
        fields_layout.addRow('Picture', self.picture_path)
        label = fields_layout.labelForField(self.picture_path)
        label.setFont(qtg.QFont('Baskerville', 16))

        fields_layout.setLabelAlignment(qtc.Qt.AlignLeft)
        main_layout.addLayout(fields_layout)

        main_layout.addWidget(self.picture, qtc.Qt.AlignCenter)

        # picture_layout = qtw.QVBoxLayout()
        # picture_layout.setContentsMargins(0, 0, 0, 0)
            
        # picture_layout.addWidget(self.picture_path)
        # picture_layout.addWidget(self.picture, qtc.Qt.AlignCenter)

        # layout.addRow('Picture', picture_layout)

        button_box = qtw.QHBoxLayout()
        button_box.addWidget(self.cancel_btn)
        button_box.addWidget(self.submit_btn)
        main_layout.addLayout(button_box)

        self.setLayout(main_layout)

        self._location = editingLoc
        if self._location:
            self.parseExistingLoc()
        if not windowTitle:
            self.setWindowTitle(self._location['location_name'])
        else:
            self.setWindowTitle(windowTitle)
        #self.setVisible(True)
    

    def parseExistingLoc(self):
        self._id = self._location['location_id']
        self.name.setText(self._location['location_name'])
        self.type_select.setCurrentText(self._location['location_type'].title())
        self.picture_path.setText(self._location['picture_path'])
        if img := self._location['__IMG__']:
            self.picture.setPixmap(qtg.QPixmap.fromImage(img))
        else:
            self.picture.setPixmap(qtg.QPixmap(self._location['picture_path']))


    @qtc.pyqtSlot()
    def getPic(self):
        filename, _ = qtw.QFileDialog.getOpenFileName(
            self,
            'Select an image to open...',
            qtc.QDir.homePath(),
            'Images (*.png *.jpeg *.jpg *.xpm)'
        )
        if filename:
            self.picture_dialog = PictureEditor(filename, EVENT_TYPE.LOC, self)
            self.picture_dialog.submitted.connect(self.storeNewPic)
            self.picture_dialog.show()
            # self.picture_path.setText(filename)
            # self.picture.setPixmap(qtg.QPixmap(filename))
    @qtc.pyqtSlot(str, qtg.QPixmap)
    def storeNewPic(self, filename, pix):
        self.picture_path.setText(filename)
        self.picture.setPixmap(pix)
    
    @qtc.pyqtSlot(str)
    def onTypeChange(self, text):
        if text == 'New...':
            text, ok = qtw.QInputDialog.getText(self, 'Enter new location type', 'Enter type:')
            if ok:
                self.type_select.addItem(text)
                self.TYPE_ITEMS.insert(len(self.TYPE_ITEMS)-2, text)
                self.type_select.setCurrentText(text)
            else:
                self.type_select.setCurrentIndex(0)

    def onSubmit(self):
        name = self.name.text()
        if not name:
            name = 'Unnamed'
        self._location['location_name'] = name
        details = self.details.toPlainText()
        if not details:
            details = ''
        self._location['location_details'] = details
        selected_type = str(self.type_select.currentText())
        if selected_type == 'Select Type':
            selected_type = ''
        self._location['location_type'] = selected_type 
        picture_path = self.picture_path.text()
        if not picture_path:
            picture_path = self.DFLT_LOC_PATH
        self._location['picture_path'] = picture_path
        if self.picture.pixmap() and not self.picture.pixmap().isNull():
            self._location['__IMG__'] = self.picture.pixmap().toImage()
        else:
            self._location['__IMG__'] = qtg.QImage(picture_path)
        self.close()
        self.submitted.emit(self._location)
        
    
    def keyPressEvent(self, event):
        if event.key() == qtc.Qt.Key_Escape:
            self.close()
        super(LocationCreator, self).keyPressEvent(event)


class CharacterSelect(qtw.QDialog):

    submitted = qtc.pyqtSignal(str)

    def __init__(self, char_list, parent=None):
        super(CharacterSelect, self).__init__(parent)

        self.setAttribute(qtc.Qt.WA_DeleteOnClose)
        self.setModal(True)
        self.setFont(qtg.QFont('Baskerville', 16))

        layout = qtw.QGridLayout()

        self.title_label = qtw.QLabel('Select a character:')
        self.title_label.setFont(qtg.QFont('Baskerville', 16))
        self.character_select = qtw.QListWidget(self)
        self.character_select.setFont(qtg.QFont('Baskerville', 18))
        self.character_select.setSizePolicy(
            qtw.QSizePolicy.Preferred,
            qtw.QSizePolicy.Fixed)
        self.character_select.setFixedHeight(200)

        self.character_select.addItems(char_list)

        self.cancel_btn = qtw.QPushButton(
            'Cancel',
            pressed=self.close )
        self.submit_btn = qtw.QPushButton(
            'Confirm',
            pressed=self.onSubmit )
        self.submit_btn.setDefault(True)

        layout.addWidget(self.title_label, 0, 0, 1, 1)
        layout.addWidget(self.character_select, 1, 0, 1, 3)
        layout.addWidget(self.cancel_btn, 2, 1, 1, 1)
        layout.addWidget(self.submit_btn, 2, 2, 1, 1)

        self.setLayout(layout)
        
    def onSubmit(self):
        self.submitted.emit(self.character_select.currentItem().text())
        self.close()


class LocationSelect(qtw.QDialog):

    submitted = qtc.pyqtSignal(str)

    def __init__(self, loc_list, parent=None):
        super(LocationSelect, self).__init__(parent)
        self.setAttribute(qtc.Qt.WA_DeleteOnClose)
        self.setModal(True)
        self.setFont(qtg.QFont('Baskerville', 16))

        layout = qtw.QGridLayout()

        self.title_label = qtw.QLabel('Select a location:')
        self.title_label.setFont(qtg.QFont('Baskerville', 16))
        self.location_select = qtw.QListWidget(self)
        self.location_select.setFont(qtg.QFont('Baskerville', 18))
        self.location_select.setSizePolicy(
            qtw.QSizePolicy.Preferred,
            qtw.QSizePolicy.Fixed)
        self.location_select.setFixedHeight(200)

        self.location_select.addItems(loc_list)

        self.cancel_btn = qtw.QPushButton(
            'Cancel',
            pressed=self.close )
        self.submit_btn = qtw.QPushButton(
            'Confirm',
            pressed=self.onSubmit )
        self.submit_btn.setDefault(True)

        layout.addWidget(self.title_label, 0, 0, 1, 1)
        layout.addWidget(self.location_select, 1, 0, 1, 3)
        layout.addWidget(self.cancel_btn, 2, 1, 1, 1)
        layout.addWidget(self.submit_btn, 2, 2, 1, 1)

        self.setLayout(layout)
        
    def onSubmit(self):
        self.submitted.emit(self.location_select.currentItem().text())
        self.close()

class TimestampCreator(qtw.QDialog):

    submitted = qtc.pyqtSignal(Time)

    def __init__(self, parent=None):
        super(TimestampCreator, self).__init__(parent)
        self.setWindowTitle('Create a Timestamp')
        self.setFont(qtg.QFont('Baskerville', 18))

        layout = qtw.QVBoxLayout()
        self.title_label = qtw.QLabel('Enter a date:')
        self.time_entry = DateLineEdit(self)

        buttons_layout = qtw.QHBoxLayout()
        self.cancel_btn = qtw.QPushButton(
            'Cancel',
            pressed=self.close )
        self.submit_btn = qtw.QPushButton(
            'Confirm',
            pressed=self.onSubmit )
        self.submit_btn.setDefault(True)

        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.submit_btn)

        layout.addWidget(self.title_label, qtc.Qt.AlignCenter)
        layout.addWidget(self.time_entry, qtc.Qt.AlignCenter)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def onSubmit(self):
        entry, valid = self.time_entry.getDate()
        if valid:
            self.submitted.emit(entry)
        self.close()


class TimestampList(qtw.QListWidget):

    removed_timestamp = qtc.pyqtSignal(str, Time)

    def __init__(self, parent=None):
        super(TimestampList, self).__init__(parent)
        self.setFont(qtg.QFont('Baskerville', 15))
        self.setVerticalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Preferred, qtw.QSizePolicy.Expanding)
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(qtc.QSize(65, 100))
        self.setMaximumSize(qtc.QSize(175, 350))
    
    def contextMenuEvent(self, event):
        self.setCursor(qtc.Qt.PointingHandCursor)
        menu = qtw.QMenu("Options")
        del_timestamp_act = menu.addAction("Delete timestamp")
        selected_act = menu.exec(event.globalPos())
        
        if selected_act == del_timestamp_act:
            self.removeAndEmitItem()
        event.accept()
        self.unsetCursor()

    def keyPressEvent(self, event):
        if event.key() == qtc.Qt.Key_Backspace:
            self.removeAndEmitItem()
        super(TimestampList, self).keyPressEvent(event)
    
    def removeAndEmitItem(self):
        item = self.currentItem()
        if item:
            self.takeItem(self.row(item))
            tmp = item.text().split('  ')
            name, time = (tmp[0][:-1], Time(tmp[1]))
            self.removed_timestamp.emit(name, time)
            del item
