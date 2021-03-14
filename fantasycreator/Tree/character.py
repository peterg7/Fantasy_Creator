
# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

# Built-in Modules
import re
import uuid
import datetime

# User-defined Modules
from Mechanics.flags import TREE_ICON_DISPLAY, EVENT_TYPE
from Mechanics.storyTime import Time, DateLineEdit

# External resources
from resources import resources


# Create Character class
class Character(qtw.QGraphicsWidget):

    ICON_HEIGHT = 180
    ICON_WIDTH = 180

    CROWN_HEIGHT = 50
    RULER_PIC_PATH = ':/dflt-tree-images/crown.png'
    BUTTON_WIDTH = 35

    item_moved = qtc.pyqtSignal(qtc.QPointF)

    def __init__(self, char_dict=None, char_id=None, x_pos=0, y_pos=0, parent=None):
        super(Character, self).__init__(parent)
        self.setX(x_pos)
        self.setY(y_pos)
        self.setFlags(qtw.QGraphicsItem.ItemIsFocusable | 
                        qtw.QGraphicsItem.ItemIsSelectable | 
                        qtw.QGraphicsItem.ItemClipsToShape)
        # self.setFlag(qtw.QGraphicsItem.ItemSendsGeometryChanges)
        # self.setFlag(qtw.QGraphicsItem.ItemIsMovable)
        self.setCacheMode(qtw.QGraphicsItem.ItemCoordinateCache)
        self.setAcceptHoverEvents(True)
        self.setCursor(qtc.Qt.PointingHandCursor)
        self.setZValue(2)

        self.add_desc = qtw.QPushButton(
            '+',
            clicked=lambda: self.parent().add_descendant.emit(self.uniq_id)
        )
        # self.add_btn.setFixedSize(self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        self.add_desc.setStyleSheet("""
                        QPushButton { 
                            border-width: 3px;
                            border-color: green;
                            border-style: outset;
                            border-radius: 3px;
                            color: green;
                            font: bold 26px;
                            background-color: rgba(66, 245, 117, 40);
                        }
                        QPushButton:pressed { 
                            background-color: rgba(66, 245, 117, 70);
                            border-style: inset;
                        }""")

        self.del_desc = qtw.QPushButton(
            '-',
            clicked=lambda: self.parent().remove_character.emit(self.uniq_id)
        )
        # self.del_btn.setFixedSize(self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        self.del_desc.setStyleSheet("""
                        QPushButton { 
                            border-width: 3px;
                            border-color: red;
                            border-style: outset;
                            border-radius: 3px;
                            color: red;
                            font: bold 32px;
                            background-color: rgba(245, 66, 66, 40);
                        }
                        QPushButton:pressed { 
                            background-color: rgba(245, 66, 66, 70);
                            border-style: inset;
                        }""")
        
        self.add_partner = qtw.QPushButton(
            '+',
            clicked=lambda: self.parent().add_partner.emit(self.uniq_id)
        )
        # self.partner_btn.setFixedSize(self.BUTTON_HEIGHT, self.BUTTON_WIDTH)
        self.add_partner.setStyleSheet("""
                        QPushButton { 
                            border-width: 3px;
                            border-color: blue;
                            border-style: outset;
                            border-radius: 3px;
                            color: blue;
                            font: bold 26px;
                            background-color: rgba(66, 197, 245, 40);
                        }
                        QPushButton:pressed { 
                            background-color: rgba(66, 197, 245, 70);
                            border-style: inset;
                        }""")
        
        self.del_partner = qtw.QPushButton(
            '-',
            clicked=lambda: self.parent().remove_partnership[uuid.UUID].emit(self.uniq_id)
        )
        # self.partner_btn.setFixedSize(self.BUTTON_HEIGHT, self.BUTTON_WIDTH)
        self.del_partner.setStyleSheet("""
                        QPushButton { 
                            border-width: 3px;
                            border-color: yellow;
                            border-style: outset;
                            border-radius: 3px;
                            color: yellow;
                            font: bold 28px;
                            background-color: rgba(245, 218, 66, 40);
                        }
                        QPushButton:pressed { 
                            background-color: rgba(245, 218, 66, 70);
                            border-style: inset;
                        }""")

        self.add_desc_btn = qtw.QGraphicsProxyWidget(self)
        self.add_desc_btn.setWidget(self.add_desc)
        self.add_desc_btn.setToolTip("Add Descendant")
        self.add_desc_btn.setVisible(False)

        self.del_desc_btn = qtw.QGraphicsProxyWidget(self)
        self.del_desc_btn.setWidget(self.del_desc)
        self.del_desc_btn.setToolTip("Delete Character")
        self.del_desc_btn.setVisible(False)

        self.add_partner_btn = qtw.QGraphicsProxyWidget(self)
        self.add_partner_btn.setWidget(self.add_partner)
        self.add_partner_btn.setToolTip("Add Partner")
        self.add_partner_btn.setVisible(False)

        self.del_partner_btn = qtw.QGraphicsProxyWidget(self)
        self.del_partner_btn.setWidget(self.del_partner)
        self.del_partner_btn.setToolTip("Remove Partner")
        self.del_partner_btn.setVisible(False)

        # Character properties
        self.uniq_id = char_id 
        # self.clone_num = 0       
        self.tree_id = None
        self.name = ''
        self.parent_0 = None
        self.parent_1 = None
        self.tree_pos = None
        self.ruler = False
        self.picture_loc = ''

        self.display_font = qtg.QFont('Cochin')
        self.display_font.setPointSize(40)
        self.display_font.setWeight(qtg.QFont.DemiBold)

        self.ruler_display_flag = True
        self.current_display_mode = TREE_ICON_DISPLAY.IMAGE

        # self.pixmap = qtw.QGraphicsPixmapItem()
        self.pixmap = None
        self.img = None
        self.img_ruler_pixmap = None
        self.name_ruler_pixmap = None
        self.offset = (0, 0)

        if char_dict is not None:
            self.parseDict(char_dict)
    
    ## Auxiliary Methods ##

    # def removeSelf(self):
    #     self.parent().delete_character(self.uniq_id)
    #     self.parent().removed_character.emit(char_id)

    def parseDict(self, dictionary):
        self.uniq_id = dictionary.get('char_id', self.uniq_id)
        if not self.uniq_id:
            self.uniq_id = uuid.uuid4()
        # self.clone_num = dictionary.get('clone', self.clone_num)
        # self.clone_num += 1
        # self.romance_id = dictionary.get('romance_id', self.romance_id)
        self.tree_id = dictionary.get('tree_id', self.tree_id)
        self.name = dictionary.get('name', self.name)
        ruler_input = dictionary.get('ruler', self.ruler)
        self.parent_0 = dictionary.get('parent_0', self.parent_0)
        self.parent_1 = dictionary.get('parent_1', self.parent_1)
        self.tree_pos = dictionary.get('tree_pos', self.tree_pos)
        if img := dictionary.get('__IMG__', None):
            # print('Using img')
            if isinstance(img, qtg.QImage):
                self.pixmap = qtg.QPixmap.fromImage(img)
            else: # Assume instance of QPixmap
                self.pixmap = img

            self.current_pixmap = self.pixmap
            self.updatePixmapImage()
            self.img = img

        # else:
        #     picture_loc_input = dictionary.get('picture_path', self.picture_loc)
        #     if picture_loc_input != self.picture_loc:
        #         self.updatePixmapImage(picture_loc_input)
        if self.ruler != ruler_input:
            self.ruler = ruler_input
            if self.ruler_display_flag:
                self.showRuler(self.ruler)
        self.setToolTip(self.name)
        self.updateButtons()

    def toDict(self):
        char_dict = {}
        char_dict['char_id'] = self.uniq_id
        char_dict['tree_id'] = self.tree_id
        char_dict['name'] = self.name
        char_dict['ruler'] = self.ruler
        char_dict['parent_0'] = self.parent_0
        char_dict['parent_1'] = self.parent_1
        char_dict['picture_path'] = self.picture_loc
        char_dict['__IMG__'] = self.img
        return char_dict
    
    def clone(self):
        char = Character()
        char.parseDict(self.toDict())
        return char

    def setDisplayMode(self, display_mode):
        if display_mode == TREE_ICON_DISPLAY.IMAGE:
            self.current_display_mode = TREE_ICON_DISPLAY.IMAGE
            self.updatePixmapImage(self.picture_loc)

        elif display_mode == TREE_ICON_DISPLAY.NAME:
            self.current_display_mode = TREE_ICON_DISPLAY.NAME
            self.setNameDisplay()
        
        if self.ruler_display_flag:
            self.showRuler(self.ruler)
        self.updateButtons()
    
    def setNameDisplay(self):
        # size = qtc.QSize(self.pixmap.pixmap().width(), self.pixmap.pixmap().height())
        font_metric = qtg.QFontMetrics(self.display_font)
        text_width = font_metric.horizontalAdvance(self.name)

        size = qtc.QSize(text_width, self.ICON_HEIGHT/2)


        result_px = qtg.QPixmap(size)
        result_px.fill(qtc.Qt.transparent)
        painter = qtg.QPainter(result_px)
        bounding_rect = qtc.QRect(0, 0, text_width, self.ICON_HEIGHT/2)
        painter.setFont(self.display_font)
        painter.drawText(bounding_rect, qtc.Qt.AlignCenter, self.name)
        painter.end()
        # self.pixmap.setPixmap(result_px)
        # self.pixmap.setOffset(-text_width / 2, -self.ICON_HEIGHT / 4)
        # self.pixmap.setShapeMode(qtw.QGraphicsPixmapItem.BoundingRectShape)
        self.current_pixmap = result_px
        self.offset = (-text_width / 2, -self.ICON_HEIGHT / 4)
    

    def buildNameRulerPix(self):
        img = qtg.QImage(self.RULER_PIC_PATH)
        img.convertTo(qtg.QImage.Format_ARGB32_Premultiplied)
        crown_px = qtg.QPixmap.fromImage(img)

        crown_px = crown_px.scaledToHeight(self.CROWN_HEIGHT)
        crown_point = qtc.QPoint((self.pixmap.width()-crown_px.width())/2, 0)
        
        size = qtc.QSize(self.current_pixmap.width(), self.current_pixmap.height() + self.CROWN_HEIGHT)
        char_rect = qtc.QRect(0, self.CROWN_HEIGHT, self.current_pixmap.width(), self.current_pixmap.height())
        result_px = qtg.QPixmap(size)
        result_px.fill(qtc.Qt.transparent)
        painter = qtg.QPainter(result_px)
        painter.setRenderHint(qtg.QPainter.TextAntialiasing)
        painter.setRenderHint(qtg.QPainter.SmoothPixmapTransform)
        painter.drawPixmap(char_rect, self.current_pixmap)
        painter.drawPixmap(crown_point, crown_px)
        painter.end()
        self.name_ruler_pixmap = result_px

    def buildImgRulerPix(self):
        img = qtg.QImage(self.RULER_PIC_PATH)
        img.convertTo(qtg.QImage.Format_ARGB32_Premultiplied)
        crown_px = qtg.QPixmap.fromImage(img)

        crown_px = crown_px.scaledToHeight(self.CROWN_HEIGHT)
        crown_point = qtc.QPoint((self.pixmap.width()-crown_px.width())/2, 0)
        
        size = qtc.QSize(self.pixmap.width(), self.pixmap.height() + self.CROWN_HEIGHT)
        char_rect = qtc.QRect(0, self.CROWN_HEIGHT, self.pixmap.width(), self.pixmap.height())
        result_px = qtg.QPixmap(size)
        result_px.fill(qtc.Qt.transparent)
        painter = qtg.QPainter(result_px)
        painter.setRenderHint(qtg.QPainter.TextAntialiasing)
        painter.setRenderHint(qtg.QPainter.SmoothPixmapTransform)
        painter.drawPixmap(char_rect, self.pixmap)
        painter.drawPixmap(crown_point, crown_px)
        painter.end()
        self.img_ruler_pixmap = result_px

    def showRuler(self, ruler_state):
        if ruler_state:
            if self.current_display_mode == TREE_ICON_DISPLAY.IMAGE:
                if not self.img_ruler_pixmap:
                    self.buildImgRulerPix()
                self.prepareGeometryChange()
                self.current_pixmap = self.img_ruler_pixmap
                self.offset = (-self.current_pixmap.width() / 2, -self.current_pixmap.height() / 2 - self.CROWN_HEIGHT/2)

            elif self.current_display_mode == TREE_ICON_DISPLAY.NAME:
                self.setNameDisplay()
                if not self.name_ruler_pixmap:
                    self.buildNameRulerPix()
                self.prepareGeometryChange()
                self.current_pixmap = self.name_ruler_pixmap
                self.offset = (-self.current_pixmap.width() / 2, -self.current_pixmap.height() / 2 - self.CROWN_HEIGHT/2)

        elif self.current_display_mode == TREE_ICON_DISPLAY.IMAGE:
            self.updatePixmapImage()
        elif self.current_display_mode == TREE_ICON_DISPLAY.NAME:
            self.setNameDisplay()
    
    def setRulerDisplay(self, flag):
        self.ruler_display_flag = flag
        if self.ruler_display_flag:
            self.showRuler(self.ruler)
        else:
            self.current_pixmap = self.pixmap
            self.showRuler(False)
        self.updateButtons()
    
    def updatePixmapImage(self, pix=None):
        self.current_pixmap = self.pixmap
        self.offset = (-self.current_pixmap.width() / 2, -self.current_pixmap.height() / 2)
        
        
    def updateButtons(self):
        pix_height = self.current_pixmap.height()
        pix_width = self.current_pixmap.width()

        self.add_desc_btn.resize(pix_width + 70, self.BUTTON_WIDTH)
        self.del_desc_btn.resize(pix_width + 70, self.BUTTON_WIDTH)
        self.add_partner_btn.resize(self.BUTTON_WIDTH, pix_height)
        self.del_partner_btn.resize(self.BUTTON_WIDTH, pix_height)

        if self.ruler and self.ruler_display_flag:
            self.add_desc_btn.setPos(-pix_width/2 - self.BUTTON_WIDTH, 
                                        pix_height/2 - self.CROWN_HEIGHT/2)
            self.del_desc_btn.setPos(-pix_width/2 - self.BUTTON_WIDTH, 
                        -pix_height/2 - self.CROWN_HEIGHT/2 - self.BUTTON_WIDTH - 9)
            self.add_partner_btn.setPos(pix_width/2, -pix_height/2 - self.CROWN_HEIGHT/2)
            self.del_partner_btn.setPos(-pix_width/2 - self.BUTTON_WIDTH, 
                                        -pix_height/2 - self.CROWN_HEIGHT/2)
        else:
            self.add_desc_btn.setPos(-pix_width/2 - self.BUTTON_WIDTH, pix_height/2)
            self.del_desc_btn.setPos(-pix_width/2 - self.BUTTON_WIDTH, 
                                                -pix_height/2 - self.BUTTON_WIDTH - 9)
            self.add_partner_btn.setPos(pix_width/2, -pix_height/2)
            self.del_partner_btn.setPos(-pix_width/2 - self.BUTTON_WIDTH, -pix_height/2)
        


    ## Accessors and Mutators ##

    def setTreePos(self, pos):
        self.tree_pos = pos
    
    def setParentID(self, char_id, parent_index=0):
        if not parent_index:
            self.parent_0 = char_id
        else:
            self.parent_1 = char_id
    
    def setTreeID(self, tree_id):
        self.tree_id = tree_id

    # def setRomanceID(self, rom_id):
    #     self.romance_id = rom_id

    def getName(self):
        return self.name
    
    def setName(self, new_name):
        self.name = new_name

    def getID(self):
        return self.uniq_id
    
    # def getRomanceID(self):
    #     return self.romance_id
    def getTreeID(self):
        return self.tree_id

    def getWidth(self):
        return self.current_pixmap.width()
    
    def getHeight(self):
        return self.current_pixmap.height()
    
    def addXOffset(self, offset):
        self.setX(self.x() + offset)
    
    def addYOffset(self, offset):
        self.setY(self.y() + offset)
    
    ## Override paint methods ##

    def paint(self, painter, option, widget):
        # self.pixmap.paint(painter, option, widget)
        painter.drawPixmap(self.x() + self.offset[0], self.y() + self.offset[1], self.current_pixmap)

    def boundingRect(self):
        bounding_rect = self.current_pixmap.rect()
        bounding_rect.translate(self.offset[0], self.offset[1])
        bounding_rect.adjust(-35, -35, 35, 35)
        return qtc.QRectF(bounding_rect)
    
    def shape(self):
        path = qtg.QPainterPath()
        path.addRect(self.boundingRect())
        return path
    
    ## Override Built-In Slots ##


    def contextMenuEvent(self, event):
    # def launchContextMenu(self, event):
        menu = qtw.QMenu("Options")
        edit_act = menu.addAction("Edit...")
        add_part_act = menu.addAction("Add partner")
        rem_part_act = menu.addAction("Remove partner")
        add_parent_act = menu.addAction("Add parent")
        # rem_parent_act = menu.addAction("Add parent")
        add_desc_act = menu.addAction("Add descendant")
        rem_char_act = menu.addAction("Delete character")
        selected_act = menu.exec(event.screenPos())
        if selected_act == edit_act:
            self.parent().edit_char.emit(self.uniq_id)
        elif selected_act == add_part_act:
            self.parent().add_partner.emit(self.uniq_id)
        elif selected_act == rem_part_act:
            self.parent().remove_partnership[uuid.UUID].emit(self.uniq_id)
        elif selected_act == add_parent_act:
            self.parent().add_parent.emit(self.uniq_id)
        # elif selected_act == rem_parent_act:
        #     print('Removing parent- in construction')
        elif selected_act == add_desc_act:
            self.parent().add_descendant.emit(self.uniq_id)
        elif selected_act == rem_char_act:
            self.parent().remove_character.emit(self.uniq_id)
        event.accept()
        # super(Character, self).contextMenuEvent(event)
        self.setCursor(qtc.Qt.PointingHandCursor)
        


    def hoverEnterEvent(self, event):
        self.add_desc_btn.setVisible(True)
        self.del_desc_btn.setVisible(True)
        self.add_partner_btn.setVisible(True)
        self.del_partner_btn.setVisible(True)
        super(Character, self).hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        self.add_desc_btn.setVisible(False)
        self.del_desc_btn.setVisible(False)
        self.add_partner_btn.setVisible(False)
        self.del_partner_btn.setVisible(False)
        super(Character, self).hoverLeaveEvent(event)


    ## Operator Overloads ##

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.uniq_id
    
    def __hash__(self):
        return hash(self.uniq_id)

    def __eq__(self, other):
        if isinstance(other, uuid.UUID):
            return self.uniq_id == other
        elif isinstance(other, Character):
            return self.uniq_id == other.uniq_id
        else:
            return self is other


class CharacterView(qtw.QGraphicsWidget):

    closed = qtc.pyqtSignal()
    CURRENT_SPAWN = qtc.QPoint(20, 60)  #NOTE: Magic Number

    def __init__(self, char_dict, parent=None):
        super(CharacterView, self).__init__(parent)
        self.setAttribute(qtc.Qt.WA_DeleteOnClose)
        self.setFlags(qtw.QGraphicsItem.ItemIsMovable | qtw.QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setCursor(qtc.Qt.OpenHandCursor)
        
        self._char = char_dict
        self._id = self._char['char_id']
        self.setObjectName('view{}'.format(self._id))

        self.brush = qtg.QBrush(qtg.QColor('#c9cdd4')) # make dependent upon gender? kingdom?
        self.translucent_effect = qtw.QGraphicsOpacityEffect(self)
        self.translucent_effect.setOpacity(0.8)
        self.setGraphicsEffect(self.translucent_effect)
        self.translucent_effect.setEnabled(False)

        self.setSizePolicy(
            qtw.QSizePolicy.Preferred,
            qtw.QSizePolicy.Preferred
        )

        self.setScale(1.4)

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
        self.name_label.setWidget(CharacterViewLabel())
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

        self.family_label = qtw.QGraphicsProxyWidget(self)
        self.family_label.setWidget(CharacterViewLabel())
        self.family_label.widget().setStyleSheet(label_style)
        self.family_label.setAcceptHoverEvents(False)
        layout.addItem(self.family_label)


        self.sex_label = qtw.QGraphicsProxyWidget(self)
        self.sex_label.setWidget(CharacterViewLabel())
        self.sex_label.widget().setStyleSheet(label_style)
        self.sex_label.setAcceptHoverEvents(False)
        layout.addItem(self.sex_label)


        self.birth_label = qtw.QGraphicsProxyWidget(self)
        self.birth_label.setWidget(CharacterViewLabel())
        self.birth_label.widget().setStyleSheet(label_style)
        self.birth_label.setAcceptHoverEvents(False)
        layout.addItem(self.birth_label)

        self.death_label = qtw.QGraphicsProxyWidget(self)
        self.death_label.setWidget(CharacterViewLabel())
        self.death_label.widget().setStyleSheet(label_style)
        self.death_label.setAcceptHoverEvents(False)
        layout.addItem(self.death_label)

        self.race_label = qtw.QGraphicsProxyWidget(self)
        self.race_label.setWidget(CharacterViewLabel())
        self.race_label.widget().setStyleSheet(label_style)
        self.race_label.setAcceptHoverEvents(False)
        layout.addItem(self.race_label)


        self.kingdom_label = qtw.QGraphicsProxyWidget(self)
        self.kingdom_label.setWidget(CharacterViewLabel())
        self.kingdom_label.widget().setStyleSheet(label_style)
        self.kingdom_label.setAcceptHoverEvents(False)
        layout.addItem(self.kingdom_label)

        self.updateView()

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
        
    
    def getID(self):
        return self._id
    
    def updateView(self):
        if self._char['name']:
            label_string = self._char['name']
        else:
            label_string = 'Name: ...'
        self.name_label.widget().setText(label_string)

        if self._char['family']:
            label_string = f"<b>Family</b>: {self._char['family']}"
        else:
            label_string = 'Family: ...'
        self.family_label.widget().setText(label_string)
        
        if self._char['sex']:
            label_string = f"<b>Sex</b>: {self._char['sex']}"
        else:
            label_string = 'Sex: ...'
        self.sex_label.widget().setText(label_string)
        
        if self._char['birth']:
            # label_string = f"<b>Birth</b>: {'{0} • {1} • {2}'.format(*self._char['birth'])}"
            label_string = f"<b>Birth</b>: {str(self._char['birth'])}"
        else:
            label_string = 'Birth: ...'
        self.birth_label.widget().setText(label_string)

        if self._char['death']:
            # label_string = f"<b>Death</b>: {'{0} • {1} • {2}'.format(*self._char['death'])}"
            label_string = f"<b>Death</b>: {str(self._char['death'])}"
        else:
            label_string = 'Death: ...'
        self.death_label.widget().setText(label_string)

        if self._char['race']:
            label_string = f"<b>Race</b>: {self._char['race']}"
        else:
            label_string = 'Race: ...'
        self.race_label.widget().setText(label_string)

        if self._char['kingdom']:
            label_string = f"<b>Kingdom</b>: {self._char['kingdom']}"
        else:
            label_string = 'Kingdom: ...'
        self.kingdom_label.widget().setText(label_string)
    

    def check_selected(self):
        if self.isSelected():
            self.translucent_effect.setEnabled(False)
        else:
            self.translucent_effect.setEnabled(True)
    
    def sceneEventFilter(self, source, event):
        if event.type() != qtc.QEvent.GraphicsSceneHoverMove:
            # Intercept event
            return True
        return super(CharacterView, self).sceneEventFilter(source, event)

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
        super(CharacterView, self).closeEvent(event)
    
    def mousePressEvent(self, event):
        self.setCursor(qtc.Qt.ClosedHandCursor)
        event.accept()
        super(CharacterView, self).mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.setCursor(qtc.Qt.OpenHandCursor)
        event.accept()
        super(CharacterView, self).mouseReleaseEvent(event)
    

class CharacterViewLabel(qtw.QLabel):

    def __init__(self, parent=None):
        super(CharacterViewLabel, self).__init__(parent)
        self.setTextFormat(qtc.Qt.RichText)
        self.setFont(qtg.QFont('Baskerville', 26))
        self.setCursor(qtc.Qt.OpenHandCursor)
    


# Character creation form
class CharacterCreator(qtw.QDialog):

    submitted = qtc.pyqtSignal(dict)
    closed = qtc.pyqtSignal()

    DFLT_PROFILE_PATH = ':/dflt-tree-images/default_profile.png'
    UNKNOWN_MALE_PATH = ':/dflt-tree-images/unknown_male.png'
    UNKNOWN_FEMALE_PATH = ':/dflt-tree-images/unknown_female.png'

    SEX_ITEMS = ["Select Sex"]
    RACE_ITEMS = ["Select Race"]
    KINGDOM_ITEMS = ["Select Kingdom"]
    FAMILY_ITEMS = ["Select Family"]

    IMAGES_PATH = 'tmp/' # TODO: FIX THIS

    def __init__(self, parent=None, editingChar=None):
        super(CharacterCreator, self).__init__(parent)
        # self.setSizePolicy(
        #     qtw.QSizePolicy.Preferred,
        #     qtw.QSizePolicy.Preferred
        # )
        self.setAttribute(qtc.Qt.WA_DeleteOnClose)
        self.setModal(True) # CAUSES BUG 

        self.setMinimumSize(415, 500)
        self.setMaximumSize(415, 700)

        self.RULER_PIC = qtg.QPixmap(Character.RULER_PIC_PATH)
        self._id = 0

        layout = qtw.QFormLayout()

        # Create input widgets
        self.name = qtw.QLineEdit()
        self.name.setFont(qtg.QFont('Baskerville', 16))
        self.family_select = qtw.QComboBox()
        self.family_select.setFont(qtg.QFont('Baskerville', 16))
        self.sex_selection = qtw.QComboBox()
        self.sex_selection.setFont(qtg.QFont('Baskerville', 16))
        self.race_selection = qtw.QComboBox()
        self.race_selection.setFont(qtg.QFont('Baskerville', 16))
        self.birth_date = DateLineEdit()
        self.birth_date.setFont(qtg.QFont('Baskerville', 16))
        self.death_date = DateLineEdit()
        self.death_date.setFont(qtg.QFont('Baskerville', 16))
        self.kingdom_select = qtw.QComboBox()
        self.kingdom_select.setFont(qtg.QFont('Baskerville', 16))
        self.ruler = qtw.QCheckBox()
        self.ruler_picture = qtw.QLabel()
        self.picture_path = PictureLineEdit()
        self.picture_path.setFont(qtg.QFont('Baskerville', 16))
        self.picture = qtw.QLabel()

        # Modify widgets
        self.sex_selection.addItems(self.SEX_ITEMS)
        self.sex_selection.model().item(0).setEnabled(False)

        self.race_selection.addItems(self.RACE_ITEMS)
        self.race_selection.model().item(0).setEnabled(False)

        self.family_select.addItems(self.FAMILY_ITEMS)
        self.family_select.model().item(0).setEnabled(False)

        self.kingdom_select.addItems(self.KINGDOM_ITEMS)
        self.kingdom_select.model().item(0).setEnabled(False)


        self.on_ruler_change(self.ruler.checkState())

        # Connect signals
        self.sex_selection.currentTextChanged.connect(self.on_sex_change)
        self.race_selection.currentTextChanged.connect(self.on_race_change)
        self.family_select.currentTextChanged.connect(self.on_fam_change)
        self.kingdom_select.currentTextChanged.connect(self.on_kingdom_change)
        self.ruler.stateChanged.connect(self.on_ruler_change)
        self.picture_path.clicked.connect(self.getPic)

        self.submit_btn = qtw.QPushButton(
            'Submit',
            clicked=self.onSubmit
        )
        self.submit_btn.setDefault(True)
        self.submit_btn.setAutoDefault(True)
        self.submit_btn.setFont(qtg.QFont('Baskerville', 16))
        # self.submit_btn.setStyleSheet(
        #     """
        #     QPushButton{
        #         outline: none;
        #         font-family: 'Baskerville';
        #         font-size: 18px;
        #     }""")
        self.cancel_btn = qtw.QPushButton(
            'Cancel',
            clicked=self.close
        )
        self.cancel_btn.setDefault(False)
        self.cancel_btn.setAutoDefault(False)
        self.cancel_btn.setFont(qtg.QFont('Baskerville', 16))
        # self.cancel_btn.setStyleSheet(
        #     """
        #     QPushButton{
        #         outline: none;
        #         font-family: 'Baskerville';
        #         font-size: 18px;
        #     }""")
        
        
        # Define layout
        layout.addRow('Name', self.name)
        label = layout.labelForField(self.name)
        label.setFont(qtg.QFont('Baskerville', 16))
        layout.addRow('Sex', self.sex_selection)
        label = layout.labelForField(self.sex_selection)
        label.setFont(qtg.QFont('Baskerville', 16))
        layout.addRow('Birth Date', self.birth_date)
        label = layout.labelForField(self.birth_date)
        label.setFont(qtg.QFont('Baskerville', 16))
        layout.addRow('Death Date', self.death_date)
        label = layout.labelForField(self.death_date)
        label.setFont(qtg.QFont('Baskerville', 16))
        layout.addRow('Race', self.race_selection)
        label = layout.labelForField(self.race_selection)
        label.setFont(qtg.QFont('Baskerville', 16))
        layout.addRow('Family', self.family_select)
        label = layout.labelForField(self.family_select)
        label.setFont(qtg.QFont('Baskerville', 16))
        layout.addRow('Kingdom', self.kingdom_select)
        label = layout.labelForField(self.kingdom_select)
        label.setFont(qtg.QFont('Baskerville', 16))

        grid_layout = qtw.QGridLayout()
        # grid_layout.setColumnStretch(3, 1)
        # grid_layout.setHorizontalSpacing()
        # grid_layout.setColumnStretch(1, 2)
        # grid_layout.setColumnStretch(2, 2)
        grid_layout.setRowMinimumHeight(1, self.RULER_PIC.height())
        max_width = max(self.picture.width(), self.RULER_PIC.width())
        grid_layout.setColumnMinimumWidth(3, max_width)

        ruler_label = qtw.QLabel('Ruler')
        ruler_label.setFont(qtg.QFont('Baskerville', 16))
        grid_layout.addWidget(ruler_label, 1, 0)
        grid_layout.addWidget(self.ruler, 1, 1, 1, 1)
        grid_layout.addWidget(self.ruler_picture, 1, 3, 2, 1, qtc.Qt.AlignCenter)

        picture_label = qtw.QLabel('Picture')
        picture_label.setFont(qtg.QFont('Baskerville', 16))
        grid_layout.addWidget(picture_label, 4, 0)
        self.picture_path.setSizePolicy(qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Fixed)
        grid_layout.addWidget(self.picture_path, 4, 1, 1, 2)
        grid_layout.addWidget(self.picture, 4, 3, 2, 1, qtc.Qt.AlignCenter)

        layout.addRow(grid_layout)

        button_box = qtw.QHBoxLayout()
        button_box.addWidget(self.cancel_btn)
        button_box.addWidget(self.submit_btn)
        layout.addRow(button_box)

        layout.setLabelAlignment(qtc.Qt.AlignLeft)

        self.setLayout(layout)
        self.setFont(qtg.QFont('Baskerville', 18))
        if editingChar:
            self._char = editingChar
            self.setWindowTitle(self._char['name'])
            self.parseExistingChar()
        else:
            self._char = {}
            self.setWindowTitle('Create a new character')
        #self.setVisible(True)
    

    def parseExistingChar(self):
        self._id = self._char['char_id']
        self.name.setText(self._char['name'])
        self.family_select.setCurrentText(self._char['family'])
        self.sex_selection.setCurrentText(self._char['sex'].title())
        self.race_selection.setCurrentText(self._char['race'].title())
        if self._char['birth']:
            self.birth_date.setText(str(self._char['birth']))
        if self._char['death']:
            self.death_date.setText(str(self._char['death']))
        self.kingdom_select.setCurrentText(self._char['kingdom'])
        self.ruler.setChecked(self._char['ruler'])
        self.picture_path.setText(self._char['picture_path'])
        # self.picture.setPixmap(qtg.QPixmap(self._char['picture_path']))
        if img := self._char['__IMG__']:
            self.picture.setPixmap(qtg.QPixmap.fromImage(img))
        else:
            self.picture.setPixmap(qtg.QPixmap(self._char['picture_path']))

    
    # def closeEvent(self, event):
    #     self.closed.emit()
    #     super(CharacterCreator, self).closeEvent(event)
    @qtc.pyqtSlot()
    def getPic(self):
        filename, _ = qtw.QFileDialog.getOpenFileName(
            self,
            'Select an image to open...',
            qtc.QDir.homePath(),
            'Images (*.png *.jpeg *.jpg *.xpm)'
        )
        if filename:
            self.picture_dialog = PictureEditor(filename, EVENT_TYPE.CHAR, self)
            self.picture_dialog.submitted.connect(self.store_new_pic)
            self.picture_dialog.show()

    @qtc.pyqtSlot(str, qtg.QPixmap)
    def store_new_pic(self, filename, pix):
        self.picture_path.setText(filename)
        self.picture.setPixmap(pix)


    
    @qtc.pyqtSlot(str)
    def on_kingdom_change(self, text):
        if text == 'New...':
            text, ok = qtw.QInputDialog.getText(self, 'Define new kingdom', 'Enter kingdom:')
            if ok:
                self.kingdom_select.addItem(text)
                self.KINGDOM_ITEMS.insert(-1, text)
                self.kingdom_select.setCurrentText(text)
            else:
                self.kingdom_select.setCurrentIndex(0)
    
    @qtc.pyqtSlot(str)
    def on_fam_change(self, text):
        if text == 'New...':
            text, ok = qtw.QInputDialog.getText(self, 'New Family', 'Enter family name:')
            if ok:
                self.family_select.addItem(text)
                self.FAMILY_ITEMS.insert(-1, text)
                self.family_select.setCurrentText(text)
            else:
                self.family_select.setCurrentIndex(0)

    @qtc.pyqtSlot(str)
    def on_race_change(self, text):
        if text == 'Other...':
            text, ok = qtw.QInputDialog.getText(self, 'Define other race', 'Enter race:')
            if ok:
                self.race_selection.addItem(text)
                self.RACE_ITEMS.insert(-1, text)
                self.race_selection.setCurrentText(text)
            else:
                self.race_selection.setCurrentIndex(0)
    
    @qtc.pyqtSlot(str)
    def on_sex_change(self, text):
        if text == 'Other...':
            text, ok = qtw.QInputDialog.getText(self, 'Define other sex', 'Enter sex:')
            if ok:
                self.sex_selection.addItem(text)
                self.SEX_ITEMS.insert(len(self.SEX_ITEMS)-1, text)
                self.sex_selection.setCurrentText(text)
            else:
                self.sex_selection.setCurrentIndex(0)
    
    @qtc.pyqtSlot(int)
    def on_ruler_change(self, ruler):
        if ruler:
            self.ruler_picture.setPixmap(self.RULER_PIC)
        else:
            self.ruler_picture.clear()


    def onSubmit(self):
        self._char['name'] = self.name.text()
        selectedFamily = str(self.family_select.currentText())
        if selectedFamily == 'Select Family':
            selectedFamily = ''
        self._char['family'] = selectedFamily
        selectedSex = str(self.sex_selection.currentText())
        if selectedSex == 'Select Sex':
            selectedSex = ''
        self._char['sex'] = selectedSex
        birth, state = self.birth_date.getDate()
        if state:
            self._char['birth'] = birth
        else:
            self._char['birth'] = Time()
        death, state = self.death_date.getDate()
        if state:
            self._char['death'] = death
        else:
            self._char['death'] = Time() + Time(10, 10, 10)
        self._char['ruler'] = bool(self.ruler.checkState())
        selectedKingdom = str(self.kingdom_select.currentText())
        if selectedKingdom == 'Select Kingdom':
            selectedKingdom = ''
        self._char['kingdom'] = selectedKingdom 
        picture_path = self.picture_path.text()
        if not picture_path:
            if selectedSex == 'Male':
                picture_path = self.UNKNOWN_MALE_PATH
            elif selectedSex == 'Female':
                picture_path = self.UNKNOWN_FEMALE_PATH
            else:
                picture_path = self.DFLT_PROFILE_PATH
        self._char['picture_path'] = picture_path
        if self.picture.pixmap() and not self.picture.pixmap().isNull():
            self._char['__IMG__'] = self.picture.pixmap().toImage()
        else:
            self._char['__IMG__'] = qtg.QImage(picture_path)
        selectedRace = str(self.race_selection.currentText())
        if selectedRace == 'Select Race':
            selectedRace = ''
        self._char['race'] = selectedRace
        self.close()
        self.submitted.emit(self._char)
        
    
    def keyPressEvent(self, event):
        if event.key() == qtc.Qt.Key_Escape:
            self.close()
        super(CharacterCreator, self).keyPressEvent(event)


class PictureLineEdit(qtw.QLineEdit):

    clicked = qtc.pyqtSignal(bool)

    def __init__(self, parent=None):
        super(PictureLineEdit, self).__init__(parent)
    
    def mousePressEvent(self, event):
        self.clicked.emit(True)


class PictureEditor(qtw.QDialog):

    CHAR_IMAGE_HEIGHT = 180
    CHAR_IMAGE_WIDTH = 180
    LOC_IMAGE_WIDTH = 260
    LOC_IMAGE_HEIGHT = 200

    submitted = qtc.pyqtSignal(str, qtg.QPixmap)

    class ImageDisplay(qtw.QGraphicsView):
        def __init__(self, pix, min_zoom, max_zoom, zoom_init, increment=1, img_mode=EVENT_TYPE.CHAR, parent=None):
            super(PictureEditor.ImageDisplay, self).__init__(parent)
            self.setVerticalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
            self.setDragMode(qtw.QGraphicsView.ScrollHandDrag)
            rect = qtc.QRectF(pix.rect())
            self.scene = qtw.QGraphicsScene(self)
            self.scene.setSceneRect(rect)
            graphic_pix = self.scene.addPixmap(pix)
            self.setScene(self.scene)

            self.setSizePolicy(
                qtw.QSizePolicy.Fixed,
                qtw.QSizePolicy.Fixed)
            if img_mode == EVENT_TYPE.CHAR:
                self.setFixedSize(qtc.QSize(
                    PictureEditor.CHAR_IMAGE_WIDTH + 2,
                    PictureEditor.CHAR_IMAGE_HEIGHT + 2))
                self.fitInView(graphic_pix, qtc.Qt.KeepAspectRatioByExpanding)

            elif img_mode == EVENT_TYPE.LOC:
                self.setFixedSize(qtc.QSize(
                    PictureEditor.LOC_IMAGE_WIDTH + 2,
                    PictureEditor.LOC_IMAGE_HEIGHT + 2))
                # self.fitInView(graphic_pix, qtc.Qt.KeepAspectRatioByExpanding)

            # self.viewport().setSizePolicy(
            #     qtw.QSizePolicy.Fixed,
            #     qtw.QSizePolicy.Fixed)
            # self.viewport().setFixedSize(qtc.QSize(
            #     PictureEditor.IMAGE_WIDTH,
            #     PictureEditor.IMAGE_HEIGHT))


            self.centerOn(rect.center())

            self.max_zoom = max_zoom
            self.min_zoom = min_zoom
            self.increment = increment
            self.current_zoom = zoom_init

        
        def scaleImg(self, factor):
            center_pos = self.viewport().rect().center()
            zoomInFactor = 1.1
            zoomOutFactor = 1 / zoomInFactor
            self.setTransformationAnchor(qtw.QGraphicsView.NoAnchor)
            self.setResizeAnchor(qtw.QGraphicsView.NoAnchor)

            if factor > self.current_zoom:
                zoomFactor = zoomInFactor
                self.current_zoom += self.increment
            else:
                zoomFactor = zoomOutFactor
                self.current_zoom -= self.increment

            oldPos = self.mapToScene(center_pos)
            self.scale(zoomFactor, zoomFactor)
            newPos = self.mapToScene(center_pos)
            delta = newPos - oldPos
            self.translate(delta.x(), delta.y())


    def __init__(self, filename, img_mode=EVENT_TYPE.CHAR, parent=None):
        super(PictureEditor, self).__init__(parent)
        self.setWindowTitle("Adjust Image")

        if filename:
            self.filename = filename
            # self.current_pix = qtg.QPixmap(self.filename)
            self.current_pix = self.importPicture(self.filename, img_mode)
        else:
            self.close()

        layout = qtw.QVBoxLayout()
        
        self.img_view = PictureEditor.ImageDisplay(self.current_pix, 4, 20, 12, img_mode=img_mode, parent=self)
        layout.addWidget(self.img_view)

        self.scale_slider = qtw.QSlider()
        self.scale_slider.setSizePolicy(
            qtw.QSizePolicy.Minimum,
            qtw.QSizePolicy.Preferred)
        self.scale_slider.setOrientation(qtc.Qt.Horizontal)
        self.scale_slider.setMinimum(4)
        self.scale_slider.setMaximum(20)
        self.scale_slider.setTickInterval(1)
        self.scale_slider.setTickPosition(qtw.QSlider.TicksBelow)

        self.current_scale = 12
        self.scale_slider.setValue(self.current_scale)
        self.scale_slider.valueChanged.connect(self.img_view.scaleImg)
        layout.addWidget(self.scale_slider)

        button_layout = qtw.QHBoxLayout()
        self.cancel_btn = qtw.QPushButton(
            'Cancel',
            clicked=self.close
        )
        button_layout.addWidget(self.cancel_btn)
        self.submit_btn = qtw.QPushButton(
            'Accept',
            clicked=self.submit
        )
        button_layout.addWidget(self.submit_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    
    def importPicture(self, filename, img_mode):
        img = qtg.QImage(filename)
        # img.convertToColorSpace(qtg.QColorSpace(qtg.QColorSpace.SRgb)) # Not avaliable on 5.13
        if img_mode == EVENT_TYPE.CHAR:
            img = img.scaled(PictureEditor.CHAR_IMAGE_WIDTH, PictureEditor.CHAR_IMAGE_HEIGHT,
                                qtc.Qt.KeepAspectRatioByExpanding, qtc.Qt.SmoothTransformation)
        elif img_mode == EVENT_TYPE.LOC:
            img = img.scaled(PictureEditor.LOC_IMAGE_WIDTH, PictureEditor.LOC_IMAGE_HEIGHT,
                                qtc.Qt.KeepAspectRatioByExpanding)
        return qtg.QPixmap.fromImage(img)


    def submit(self):
        rect = self.img_view.viewport().rect()
        final_pix = qtg.QPixmap(rect.size())
        final_pix.fill(qtg.QColor(qtc.Qt.transparent))
        painter = qtg.QPainter(final_pix)
        painter.setRenderHint(qtg.QPainter.SmoothPixmapTransform)
        painter.setRenderHint(qtg.QPainter.Antialiasing)
        self.img_view.render(painter, qtc.QRectF(final_pix.rect()), rect)
        painter.end()
        self.submitted.emit(self.filename, final_pix)
        self.close()
    



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